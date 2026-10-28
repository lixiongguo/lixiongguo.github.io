// Native window for the caustic lens scene. Uses AppKit, not SFML.
#include "camera/camera.hpp"
#include "shape/plane.hpp"
#include "shape/model.hpp"
#include "shape/scene.hpp"
#include "material/diffuse_material.hpp"
#include "material/dielectric_material.hpp"
#include "renderer/path_tracing_renderer.hpp"
#include "renderer/normal_renderer.hpp"
#include "thread/thread_pool.hpp"
#include "util/frame.hpp"
#include "util/rng.hpp"

#import <Cocoa/Cocoa.h>
#import "../../cpp/resource_hud.h"

#include <algorithm>
#include <cctype>
#include <array>
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <mutex>
#include <sstream>
#include <stdexcept>
#include <string>

namespace {

enum KeyBit : uint32_t {
    KeyW = 1u << 0,
    KeyA = 1u << 1,
    KeyS = 1u << 2,
    KeyD = 1u << 3,
    KeyUp = 1u << 4,
    KeyDown = 1u << 5,
};

enum class ViewMode { Render, Normal };

const char *viewName(ViewMode mode, bool clay) {
    if (clay) return "白模";
    return mode == ViewMode::Normal ? "法线" : "焦散";
}

struct Json {
    enum class Type { Null, Num, Str, Bool, Arr, Obj };
    Type type = Type::Null;
    double num = 0;
    bool boolean = false;
    std::string str;
    std::vector<Json> arr;
    std::vector<std::pair<std::string, Json>> obj;

    const Json *find(const std::string &key) const {
        for (const auto &entry : obj) {
            if (entry.first == key) return &entry.second;
        }
        return nullptr;
    }
    const Json &need(const std::string &key) const {
        const Json *value = find(key);
        if (!value) throw std::runtime_error("场景 JSON 缺少 " + key);
        return *value;
    }
    glm::vec3 vec3(const std::string &key) const {
        const Json &value = need(key);
        if (value.arr.size() != 3) throw std::runtime_error(key + " 需要 3 个数");
        return { static_cast<float>(value.arr[0].num), static_cast<float>(value.arr[1].num), static_cast<float>(value.arr[2].num) };
    }
    glm::vec3 vec3Or(const std::string &key, const glm::vec3 &fallback) const {
        return find(key) ? vec3(key) : fallback;
    }
    float number(const std::string &key) const { return static_cast<float>(need(key).num); }
    float numberOr(const std::string &key, float fallback) const {
        const Json *value = find(key);
        return value ? static_cast<float>(value->num) : fallback;
    }
    int integerOr(const std::string &key, int fallback) const {
        const Json *value = find(key);
        return value ? static_cast<int>(value->num) : fallback;
    }
    const std::string &text(const std::string &key) const { return need(key).str; }
};

struct JsonParser {
    explicit JsonParser(const std::string &text) : text(text) {}

    Json parse() {
        Json value = parseValue();
        skip();
        if (i != text.size()) throw std::runtime_error("场景 JSON 后面还有多余内容");
        return value;
    }

    void skip() {
        while (i < text.size() && std::isspace(static_cast<unsigned char>(text[i]))) ++i;
    }
    char peek() { skip(); return i < text.size() ? text[i] : 0; }
    char get() { skip(); if (i >= text.size()) throw std::runtime_error("场景 JSON 意外结束"); return text[i++]; }

    Json parseValue() {
        const char c = peek();
        if (c == '{') return parseObject();
        if (c == '[') return parseArray();
        if (c == '"') return parseString();
        if (c == 't' || c == 'f') return parseBool();
        if (c == '-' || std::isdigit(static_cast<unsigned char>(c))) return parseNumber();
        throw std::runtime_error("场景 JSON 有无法识别的值");
    }
    Json parseObject() {
        get();
        Json value;
        value.type = Json::Type::Obj;
        if (peek() == '}') { get(); return value; }
        while (true) {
            Json key = parseString();
            if (get() != ':') throw std::runtime_error("场景 JSON 对象缺少冒号");
            value.obj.emplace_back(key.str, parseValue());
            const char next = get();
            if (next == '}') return value;
            if (next != ',') throw std::runtime_error("场景 JSON 对象缺少逗号");
        }
    }
    Json parseArray() {
        get();
        Json value;
        value.type = Json::Type::Arr;
        if (peek() == ']') { get(); return value; }
        while (true) {
            value.arr.push_back(parseValue());
            const char next = get();
            if (next == ']') return value;
            if (next != ',') throw std::runtime_error("场景 JSON 数组缺少逗号");
        }
    }
    Json parseString() {
        if (get() != '"') throw std::runtime_error("场景 JSON 缺少字符串");
        Json value;
        value.type = Json::Type::Str;
        while (i < text.size() && text[i] != '"') {
            if (text[i] == '\\') {
                ++i;
                if (i >= text.size()) break;
            }
            value.str.push_back(text[i++]);
        }
        if (i >= text.size() || text[i] != '"') throw std::runtime_error("场景 JSON 字符串没有结束");
        ++i;
        return value;
    }
    Json parseNumber() {
        skip();
        const size_t begin = i;
        if (text[i] == '-') ++i;
        while (i < text.size() && (std::isdigit(static_cast<unsigned char>(text[i])) || text[i] == '.' || text[i] == 'e' || text[i] == 'E' || text[i] == '+' || text[i] == '-')) ++i;
        Json value;
        value.type = Json::Type::Num;
        value.num = std::stod(text.substr(begin, i - begin));
        return value;
    }
    Json parseBool() {
        Json value;
        value.type = Json::Type::Bool;
        if (text.compare(i, 4, "true") == 0) { value.boolean = true; i += 4; return value; }
        if (text.compare(i, 5, "false") == 0) { value.boolean = false; i += 5; return value; }
        throw std::runtime_error("场景 JSON 布尔值无效");
    }

    const std::string &text;
    size_t i = 0;
};

struct SceneDesc {
    std::string note;
    glm::vec3 eye { 0.f };
    glm::vec3 target { 0.f, 0.f, -1.f };
    float fov = 45.f;
    std::filesystem::path meshPath;
    int triMax = 0;
    glm::vec3 meshScale { 1.f };
    glm::vec3 meshRotate { 0.f };
    glm::vec3 meshTranslate { 0.f };
    float eta = 1.55f;
    float rough = 0.f;
    glm::vec3 glassAlbedo { 0.98f };
    glm::vec3 beamDir { 0.f, 0.f, -1.f };
    glm::vec3 beamOrigin { 0.f, 0.f, 0.25f };
    glm::vec2 beamHalf { 0.49f };
    int beamRays = 256;
    glm::vec3 beamPoint { 0.f, 0.f, 0.55f };
    glm::vec3 beamNormal { 0.f, 0.f, -1.f };
    float beamRadius = 0.52f;
    glm::vec3 beamAlbedo { 1.f, 0.97f, 0.88f };
    glm::vec3 wallPoint { 0.f, 0.f, -6.f };
    glm::vec3 wallNormal { 0.f, 0.f, 1.f };
    float wallRadius = 2.4f;
    glm::vec3 wallAlbedo { 0.74f };
    float mapHalf = 1.4f;
    int bins = 256;
};

glm::vec3 shadeWhite(const Camera &camera, const Scene &scene, const glm::ivec2 &pixel, const glm::vec3 &towardLight) {
    auto hit = scene.intersect(camera.generateRay(pixel));
    if (!hit.has_value()) return { 0.17f, 0.18f, 0.19f };
    const glm::vec3 normal = glm::normalize(hit->normal);
    const float shade = 0.28f + 0.72f * std::abs(glm::dot(normal, glm::normalize(towardLight)));
    return { shade, shade, shade };
}

std::vector<Triangle> loadObjTriangles(const std::filesystem::path &filename, size_t maxTriangles) {
    std::ifstream in(filename);
    std::vector<glm::vec3> verts;
    std::vector<std::array<int, 3>> faces;
    std::string line;
    while (std::getline(in, line)) {
        if (line.size() < 3 || line[0] == '#') continue;
        if (line[0] == 'v' && line[1] == ' ') {
            float x = 0, y = 0, z = 0;
            if (std::sscanf(line.c_str() + 2, "%f %f %f", &x, &y, &z) == 3) {
                verts.emplace_back(x, y, z);
            }
        } else if (line[0] == 'f' && line[1] == ' ') {
            std::istringstream tokens(line.substr(2));
            std::vector<int> idx;
            std::string token;
            while (tokens >> token) {
                const int slash = static_cast<int>(token.find('/'));
                const int raw = std::stoi(slash == static_cast<int>(std::string::npos) ? token : token.substr(0, slash));
                int id = raw > 0 ? raw - 1 : static_cast<int>(verts.size()) + raw;
                if (id >= 0) idx.push_back(id);
            }
            for (size_t k = 1; k + 1 < idx.size(); ++k) {
                faces.push_back({ idx[0], idx[k], idx[k + 1] });
            }
        }
    }
    size_t step = 1;
    if (maxTriangles > 0 && faces.size() > maxTriangles) {
        step = (faces.size() + maxTriangles - 1) / maxTriangles;
    }
    std::vector<Triangle> triangles;
    triangles.reserve(faces.size() / step + 1);
    for (size_t i = 0; i < faces.size(); i += step) {
        const auto &face = faces[i];
        if (face[0] < 0 || face[1] < 0 || face[2] < 0) continue;
        if (static_cast<size_t>(face[0]) >= verts.size() ||
            static_cast<size_t>(face[1]) >= verts.size() ||
            static_cast<size_t>(face[2]) >= verts.size()) continue;
        triangles.emplace_back(verts[face[0]], verts[face[1]], verts[face[2]]);
    }
    return triangles;
}

glm::vec3 tonemap(glm::vec3 c, bool reinhard) {
    c = glm::max(c, glm::vec3(0));
    if (reinhard) {
        c = c / (glm::vec3(1) + c);
    }
    return glm::pow(c, glm::vec3(1.f / 2.2f));
}

void writeRGBA(const Film &film, std::vector<uint8_t> &out, bool reinhard) {
    const size_t w = film.getWidth();
    const size_t h = film.getHeight();
    out.resize(w * h * 4);
    for (size_t y = 0; y < h; ++y) {
        for (size_t x = 0; x < w; ++x) {
            auto pixel = film.getPixel(x, y);
            glm::vec3 c(0);
            if (pixel.sample_count > 0) {
                c = pixel.color / static_cast<float>(pixel.sample_count);
            }
            c = tonemap(c, reinhard);
            const size_t i = (y * w + x) * 4;
            out[i + 0] = static_cast<uint8_t>(glm::clamp(c.r, 0.f, 1.f) * 255);
            out[i + 1] = static_cast<uint8_t>(glm::clamp(c.g, 0.f, 1.f) * 255);
            out[i + 2] = static_cast<uint8_t>(glm::clamp(c.b, 0.f, 1.f) * 255);
            out[i + 3] = 255;
        }
    }
}

void writePPM(const Film &film, const std::filesystem::path &path, bool reinhard) {
    std::filesystem::create_directories(path.parent_path());
    std::ofstream f(path, std::ios::binary);
    const size_t w = film.getWidth();
    const size_t h = film.getHeight();
    f << "P6\n" << w << " " << h << "\n255\n";
    for (size_t y = 0; y < h; ++y) {
        for (size_t x = 0; x < w; ++x) {
            auto pixel = film.getPixel(x, y);
            glm::vec3 c(0);
            if (pixel.sample_count > 0) {
                c = pixel.color / static_cast<float>(pixel.sample_count);
            }
            c = tonemap(c, reinhard);
            uint8_t rgb[3] = {
                static_cast<uint8_t>(glm::clamp(c.r, 0.f, 1.f) * 255),
                static_cast<uint8_t>(glm::clamp(c.g, 0.f, 1.f) * 255),
                static_cast<uint8_t>(glm::clamp(c.b, 0.f, 1.f) * 255),
            };
            f.write(reinterpret_cast<char *>(rgb), 3);
        }
    }
}

struct AppState {
    AppState(int w, int h, const SceneDesc &desc, std::vector<Triangle> triangles)
        : lens(std::make_unique<Model>(std::move(triangles))),
          beam(desc.beamPoint, desc.beamNormal, desc.beamRadius),
          wall(desc.wallPoint, desc.wallNormal, desc.wallRadius),
          glass(desc.eta, desc.glassAlbedo, desc.rough, desc.rough),
          wallMat(desc.wallAlbedo),
          beamMat(desc.beamAlbedo),
          film(w, h),
          camera(film, desc.eye, desc.target, desc.fov),
          path(camera, scene),
          normals(camera, scene),
          beamDirection(glm::normalize(desc.beamDir)),
          beamOrigin(desc.beamOrigin),
          beamHalf(desc.beamHalf),
          beamRays(std::max(8, desc.beamRays)),
          mapHalf(std::max(1e-3f, desc.mapHalf)),
          causticBins(std::max(8, desc.bins)),
          wallAlbedo(desc.wallAlbedo),
          beamMatAlbedo(desc.beamAlbedo),
          meshScale(desc.meshScale),
          meshRotate(desc.meshRotate),
          meshTranslate(desc.meshTranslate),
          ior(desc.eta),
          triMax(std::max(0, desc.triMax)),
          currentModel(desc.meshPath.filename().string()) {
        mountLens();
        note = desc.note.empty() ? currentModel : desc.note;
    }

    void mountLens() {
        scene.clearShapes();
        scene.addShape(*lens, &glass, meshTranslate, meshScale, meshRotate);
        scene.addShape(beam, &beamMat);
        scene.addShape(wall, &wallMat);
        scene.build();
        caustic.clear();
        causticReady = false;
        clearFilm();
    }

    void consumePendingModel() {
        if (!meshDirty.load()) return;
        std::string name;
        {
            std::lock_guard<std::mutex> lock(inputMutex);
            name = pendingModel;
            meshDirty.store(false);
        }
        if (name.empty() || name == currentModel) return;
        auto triangles = loadObjTriangles(modelsDir / name, static_cast<size_t>(triMax));
        if (triangles.empty()) {
            std::lock_guard<std::mutex> lock(inputMutex);
            note = "打不开 " + name;
            return;
        }
        scene.clearShapes();
        lens = std::make_unique<Model>(std::move(triangles));
        mountLens();
        currentModel = name;
        std::lock_guard<std::mutex> lock(inputMutex);
        note = name;
    }

    void resize(int w, int h) {
        film.setResolution(w, h);
        film.clear();
        camera.zoom(0);
        spp = 0;
    }

    void clearFilm() {
        film.clear();
        spp = 0;
    }

    bool receiverBin(const glm::vec3 &point, int &bx, int &by) const {
        const glm::vec3 rel = point - wall.point;
        const float u = (glm::dot(rel, wall.x_axis) + mapHalf) / (2.f * mapHalf);
        const float v = (glm::dot(rel, wall.z_axis) + mapHalf) / (2.f * mapHalf);
        if (u < 0.f || v < 0.f || u >= 1.f || v >= 1.f) return false;
        bx = glm::clamp(static_cast<int>(u * causticBins), 0, causticBins - 1);
        by = glm::clamp(static_cast<int>(v * causticBins), 0, causticBins - 1);
        return true;
    }

    glm::vec3 causticAt(const glm::vec3 &point) const {
        if (caustic.empty()) return {};
        int x = 0, y = 0;
        if (!receiverBin(point, x, y)) return {};
        return glm::vec3(caustic[static_cast<size_t>(y * causticBins + x)]);
    }

    glm::vec3 shadeCaustic(const glm::ivec2 &pixel) const {
        auto hit = scene.intersect(camera.generateRay(pixel));
        if (!hit.has_value()) return { 0.03f, 0.032f, 0.036f };
        if (hit->material == &wallMat) {
            const glm::vec3 pattern = causticAt(hit->hit_point);
            return wallAlbedo * (0.16f + 5.f * pattern);
        }
        if (hit->material == &beamMat) return { 2.2f, 2.1f, 1.7f };
        const glm::vec3 normal = glm::normalize(hit->normal);
        const float shade = 0.22f + 0.78f * std::abs(glm::dot(normal, glm::vec3(0.f, 0.f, 1.f)));
        return { shade, shade, shade };
    }

    bool buildCaustic() {
        if (meshDirty.load()) return false;
        const int rays = beamRays;
        const glm::vec3 axisU = glm::normalize(glm::cross(
            std::abs(beamDirection.y) < 0.9f ? glm::vec3(0.f, 1.f, 0.f) : glm::vec3(1.f, 0.f, 0.f),
            beamDirection));
        const glm::vec3 axisV = glm::normalize(glm::cross(beamDirection, axisU));
        struct ExitRay { glm::vec3 origin; glm::vec3 direction; bool valid; };
        std::vector<ExitRay> exits(static_cast<size_t>(rays) * rays);
        thread_pool.parallelFor(rays, rays, [&](size_t ix, size_t iy) {
            const float u = -beamHalf.x + 2.f * beamHalf.x * (static_cast<float>(ix) + 0.5f) / rays;
            const float v = -beamHalf.y + 2.f * beamHalf.y * (static_cast<float>(iy) + 0.5f) / rays;
            Ray ray { beamOrigin + axisU * u + axisV * v, beamDirection };
            for (int bounce = 0; bounce < 6; ++bounce) {
                auto hit = scene.intersect(ray);
                if (!hit.has_value() || hit->material != &glass) {
                    if (bounce > 0) exits[iy * rays + ix] = { ray.origin, ray.direction, true };
                    return;
                }
                const glm::vec3 outward = glm::normalize(hit->normal);
                const bool front = glm::dot(ray.direction, outward) < 0.f;
                const glm::vec3 n = front ? outward : -outward;
                const float eta = front ? (1.f / ior) : ior;
                const float cosI = glm::clamp(glm::dot(-ray.direction, n), 0.f, 1.f);
                const float sin2T = eta * eta * (1.f - cosI * cosI);
                if (sin2T > 1.f) return;
                const glm::vec3 next = glm::normalize(eta * ray.direction + (eta * cosI - std::sqrt(1.f - sin2T)) * n);
                ray.origin = hit->hit_point;
                ray.direction = next;
            }
        }, false);
        thread_pool.wait();
        if (meshDirty.load()) return false;

        std::vector<int> bins(static_cast<size_t>(causticBins) * causticBins, 0);
        int hitCount = 0;
        for (const auto &exit : exits) {
            if (!exit.valid) continue;
            const float nd = glm::dot(exit.direction, wall.normal);
            if (std::abs(nd) < 1e-6f) continue;
            const float t = glm::dot(wall.point - exit.origin, wall.normal) / nd;
            if (t <= 0.f) continue;
            int bx = 0, by = 0;
            if (!receiverBin(exit.origin + t * exit.direction, bx, by)) continue;
            bins[static_cast<size_t>(by * causticBins + bx)] += 1;
            hitCount += 1;
        }
        int peak = 1;
        caustic.assign(bins.size(), 0.f);
        for (size_t i = 0; i < bins.size(); ++i) peak = std::max(peak, bins[i]);
        for (size_t i = 0; i < bins.size(); ++i) caustic[i] = static_cast<float>(bins[i]) / static_cast<float>(peak);
        causticReady = true;
        std::lock_guard<std::mutex> lock(inputMutex);
        note = "焦散命中 " + std::to_string(hitCount) + "/" + std::to_string(rays * rays);
        return true;
    }

    bool applyInput(float dt) {
        uint32_t keys = held.load();
        float tx = 0, ty = 0, z = 0;
        bool wantReset = false;
        bool wantSave = false;
        int newW = 0, newH = 0;
        ViewMode mode = ViewMode::Render;
        bool clay = false;
        {
            std::lock_guard<std::mutex> lock(inputMutex);
            tx = turnX;
            ty = turnY;
            z = zoomDelta;
            turnX = turnY = zoomDelta = 0;
            wantReset = reset;
            wantSave = save;
            reset = save = false;
            newW = pendingW;
            newH = pendingH;
            pendingW = pendingH = 0;
            mode = view;
            clay = whiteModel;
        }

        bool moved = false;
        dt *= 0.8f;
        if (keys & KeyW) { camera.move(dt, Direction::Forward); moved = true; }
        if (keys & KeyS) { camera.move(dt, Direction::Backward); moved = true; }
        if (keys & KeyA) { camera.move(dt, Direction::Left); moved = true; }
        if (keys & KeyD) { camera.move(dt, Direction::Right); moved = true; }
        if (keys & KeyUp) { camera.move(dt, Direction::Up); moved = true; }
        if (keys & KeyDown) { camera.move(dt, Direction::Down); moved = true; }
        if (tx != 0 || ty != 0) {
            camera.turn({ tx, ty });
            moved = true;
        }
        if (z != 0) {
            camera.zoom(z);
            moved = true;
        }
        if (newW > 0 && newH > 0) {
            resize(newW, newH);
            moved = false;
        } else if (moved || wantReset) {
            clearFilm();
        }
        if (wantSave) {
            writePPM(film, "build/gui/lens.ppm", !clay && mode != ViewMode::Normal);
            std::lock_guard<std::mutex> lock(inputMutex);
            note = "已保存 build/gui/lens.ppm";
        }
        return !clay && mode != ViewMode::Normal;
    }

    void renderBatch() {
        using clock = std::chrono::steady_clock;
        const auto now = clock::now();
        float dt = std::chrono::duration<float>(now - lastTick).count();
        lastTick = now;
        if (dt > 0.2f) dt = 0.2f;
        consumePendingModel();

        const int epoch = inputEpoch.load();
        const int clayEpochAtStart = clayEpoch.load();
        const bool reinhard = applyInput(dt);
        ViewMode mode;
        bool clay = false;
        int batch = 1;
        {
            std::lock_guard<std::mutex> lock(inputMutex);
            mode = view;
            clay = whiteModel;
            batch = sppBatch;
        }
        if (clay) batch = 1;
        if (!clay && mode != ViewMode::Normal && !causticReady && !buildCaustic()) {
            awake.store(true);
            return;
        }

        const size_t w = film.getWidth();
        const size_t h = film.getHeight();
        const int seed = spp;
        std::atomic<bool> abandoned { false };
        thread_pool.parallelFor(w, h, [&](size_t x, size_t y) {
            if (abandoned.load(std::memory_order_relaxed) || meshDirty.load()) return;
            if (clayEpoch.load(std::memory_order_relaxed) != clayEpochAtStart) {
                abandoned.store(true, std::memory_order_relaxed);
                return;
            }
            for (int i = 0; i < batch; ++i) {
                const glm::ivec3 pixel { static_cast<int>(x), static_cast<int>(y), seed + i };
                glm::vec3 color;
                if (clay) color = shadeWhite(camera, scene, { pixel.x, pixel.y }, -beamDirection);
                else if (mode == ViewMode::Normal) color = normals.renderPixel(pixel);
                else color = shadeCaustic({ pixel.x, pixel.y });
                film.addSample(x, y, color);
            }
        });
        thread_pool.wait();
        if (abandoned.load(std::memory_order_relaxed)) {
            awake.store(true);
            return;
        }
        spp += batch;
        if (clay && held.load() == 0 && inputEpoch.load() == epoch) awake.store(false);

        std::vector<uint8_t> pixels;
        writeRGBA(film, pixels, reinhard);

        std::string caption;
        {
            std::lock_guard<std::mutex> lock(inputMutex);
            caption = note;
        }
        std::lock_guard<std::mutex> lock(imageMutex);
        rgba.swap(pixels);
        shownW = static_cast<int>(film.getWidth());
        shownH = static_cast<int>(film.getHeight());
        shownSpp = spp;
        shownView = mode;
        shownClay = clay;
        shownBatch = batch;
        shownNote = caption;
    }

    std::unique_ptr<Model> lens;
    std::filesystem::path modelsDir;
    std::vector<std::string> modelNames;
    std::string currentModel;
    std::string pendingModel;
    std::atomic<bool> meshDirty { false };
    glm::vec3 meshScale { 1.f };
    glm::vec3 meshRotate { 0.f };
    glm::vec3 meshTranslate { 0.f };
    float ior = 1.55f;
    int triMax = 0;
    Plane beam;
    Plane wall;
    DielectricMaterial glass;
    DiffuseMaterial wallMat;
    DiffuseMaterial beamMat;
    Scene scene;
    Film film;
    Camera camera;
    PathTracingRenderer path;
    NormalRenderer normals;
    glm::vec3 beamDirection { 0.f, 0.f, -1.f };
    glm::vec3 beamOrigin { 0.f };
    glm::vec2 beamHalf { 0.49f };
    int beamRays = 256;
    float mapHalf = 1.4f;
    int causticBins = 256;
    glm::vec3 wallAlbedo { 0.74f };
    glm::vec3 beamMatAlbedo { 1.f, 0.97f, 0.88f };
    std::vector<float> caustic;
    bool causticReady = false;

    std::atomic<bool> running { true };
    std::atomic<bool> awake { true };
    std::atomic<int> inputEpoch { 0 };
    std::atomic<int> clayEpoch { 0 };
    std::atomic<uint32_t> held { 0 };
    std::mutex inputMutex;
    float turnX = 0, turnY = 0, zoomDelta = 0;
    bool reset = false;
    bool save = false;
    int pendingW = 0, pendingH = 0;
    int sppBatch = 1;
    bool whiteModel = false;
    ViewMode view = ViewMode::Render;
    std::string note;
    int spp = 0;
    std::chrono::steady_clock::time_point lastTick = std::chrono::steady_clock::now();

    std::mutex imageMutex;
    std::vector<uint8_t> rgba;
    int shownW = 0, shownH = 0, shownSpp = 0, shownBatch = 1;
    ViewMode shownView = ViewMode::Render;
    bool shownClay = false;
    std::string shownNote;
};

NSImage *imageFromRGBA(const std::vector<uint8_t> &rgba, int w, int h) {
    if (w <= 0 || h <= 0 || rgba.size() < static_cast<size_t>(w) * h * 4) return nil;
    // First scanline is the top row, matching the film and the PPM writer.
    NSBitmapImageRep *rep = [[NSBitmapImageRep alloc]
        initWithBitmapDataPlanes:NULL
        pixelsWide:w
        pixelsHigh:h
        bitsPerSample:8
        samplesPerPixel:4
        hasAlpha:YES
        isPlanar:NO
        colorSpaceName:NSCalibratedRGBColorSpace
        bitmapFormat:0
        bytesPerRow:w * 4
        bitsPerPixel:32];
    if (!rep) return nil;
    memcpy(rep.bitmapData, rgba.data(), static_cast<size_t>(w) * h * 4);
    NSImage *image = [[NSImage alloc] initWithSize:NSMakeSize(w, h)];
    [image addRepresentation:rep];
    return image;
}

} // namespace

@interface DebugView : NSView <NSWindowDelegate>
- (instancetype)initWithState:(std::shared_ptr<AppState>)state;
@end

@implementation DebugView {
    std::shared_ptr<AppState> state;
    NSImageView *imageView;
    NSTextField *caption;
    NSTextField *status;
    NSSwitch *claySwitch;
    NSPopUpButton *modelPopup;
    BOOL scheduled;
}

- (instancetype)initWithState:(std::shared_ptr<AppState>)appState {
    self = [super initWithFrame:NSMakeRect(0, 0, 640, 560)];
    if (!self) return nil;
    state = std::move(appState);

    caption = [self makeCaption:@"焦散"];
    imageView = [self makeImageView];
    NSStackView *column = [self column:caption image:imageView];

    NSTextField *modelLabel = [self makeCaption:@"模型"];
    modelLabel.font = [NSFont systemFontOfSize:13];
    modelPopup = [[NSPopUpButton alloc] initWithFrame:NSZeroRect pullsDown:NO];
    for (const auto &name : state->modelNames) {
        [modelPopup addItemWithTitle:[NSString stringWithUTF8String:name.c_str()]];
    }
    if (state->modelNames.empty()) {
        [modelPopup addItemWithTitle:[NSString stringWithUTF8String:state->currentModel.c_str()]];
    }
    [modelPopup selectItemWithTitle:[NSString stringWithUTF8String:state->currentModel.c_str()]];
    modelPopup.target = self;
    modelPopup.action = @selector(modelChanged:);
    [modelPopup setContentCompressionResistancePriority:NSLayoutPriorityDefaultLow forOrientation:NSLayoutConstraintOrientationHorizontal];
    NSStackView *modelRow = [[NSStackView alloc] init];
    modelRow.orientation = NSUserInterfaceLayoutOrientationHorizontal;
    modelRow.spacing = 8;
    modelRow.alignment = NSLayoutAttributeCenterY;
    [modelRow addArrangedSubview:modelLabel];
    [modelRow addArrangedSubview:modelPopup];

    NSTextField *clayLabel = [self makeCaption:@"白模"];
    clayLabel.font = [NSFont systemFontOfSize:13];
    claySwitch = [[NSSwitch alloc] init];
    claySwitch.target = self;
    claySwitch.action = @selector(claySwitchChanged:);
    claySwitch.state = NSControlStateValueOff;
    NSStackView *clayRow = [[NSStackView alloc] init];
    clayRow.orientation = NSUserInterfaceLayoutOrientationHorizontal;
    clayRow.spacing = 8;
    clayRow.alignment = NSLayoutAttributeCenterY;
    [clayRow addArrangedSubview:clayLabel];
    [clayRow addArrangedSubview:claySwitch];

    status = [[NSTextField alloc] init];
    status.editable = NO;
    status.bezeled = NO;
    status.drawsBackground = NO;
    status.textColor = [NSColor secondaryLabelColor];
    status.font = [NSFont monospacedSystemFontOfSize:12 weight:NSFontWeightRegular];
    status.maximumNumberOfLines = 2;
    status.stringValue = @"正在渲染第一帧…";

    NSStackView *root = [[NSStackView alloc] init];
    root.orientation = NSUserInterfaceLayoutOrientationVertical;
    root.spacing = 8;
    root.edgeInsets = NSEdgeInsetsMake(12, 12, 12, 12);
    root.translatesAutoresizingMaskIntoConstraints = NO;
    [root addArrangedSubview:modelRow];
    [root addArrangedSubview:clayRow];
    [root addArrangedSubview:column];
    [root addArrangedSubview:status];
    [self addSubview:root];
    [ResourceHud attachToView:self];

    [NSLayoutConstraint activateConstraints:@[
        [root.leadingAnchor constraintEqualToAnchor:self.leadingAnchor],
        [root.trailingAnchor constraintEqualToAnchor:self.trailingAnchor],
        [root.topAnchor constraintEqualToAnchor:self.topAnchor],
        [root.bottomAnchor constraintEqualToAnchor:self.bottomAnchor],
        [imageView.heightAnchor constraintEqualToAnchor:imageView.widthAnchor multiplier:0.75],
        [imageView.widthAnchor constraintGreaterThanOrEqualToConstant:480],
    ]];
    return self;
}

- (NSTextField *)makeCaption:(NSString *)text {
    NSTextField *label = [[NSTextField alloc] init];
    label.editable = NO;
    label.bezeled = NO;
    label.drawsBackground = NO;
    label.stringValue = text;
    label.font = [NSFont boldSystemFontOfSize:13];
    return label;
}

- (NSImageView *)makeImageView {
    NSImageView *view = [[NSImageView alloc] init];
    view.imageScaling = NSImageScaleProportionallyUpOrDown;
    view.imageAlignment = NSImageAlignCenter;
    view.wantsLayer = YES;
    view.layer.backgroundColor = NSColor.blackColor.CGColor;
    [view setContentHuggingPriority:NSLayoutPriorityDefaultLow forOrientation:NSLayoutConstraintOrientationVertical];
    return view;
}

- (NSStackView *)column:(NSTextField *)title image:(NSImageView *)image {
    NSStackView *col = [[NSStackView alloc] init];
    col.orientation = NSUserInterfaceLayoutOrientationVertical;
    col.spacing = 4;
    col.alignment = NSLayoutAttributeLeading;
    [col addArrangedSubview:title];
    [col addArrangedSubview:image];
    [image setContentHuggingPriority:NSLayoutPriorityDefaultLow forOrientation:NSLayoutConstraintOrientationHorizontal];
    return col;
}

- (BOOL)acceptsFirstResponder { return YES; }

- (NSView *)hitTest:(NSPoint)point {
    NSView *hit = [super hitTest:point];
    for (NSView *walk = hit; walk && walk != self; walk = walk.superview) {
        if (walk == claySwitch || walk == modelPopup) return hit;
    }
    return NSPointInRect(point, self.bounds) ? self : nil;
}

- (void)viewDidMoveToWindow {
    [super viewDidMoveToWindow];
    if (self.window) {
        [self.window makeFirstResponder:self];
        [self scheduleBatch];
    }
}

- (void)scheduleBatch {
    if (scheduled || !state || !state->running.load()) return;
    scheduled = YES;
    std::shared_ptr<AppState> kept = state;
    __weak DebugView *weakSelf = self;
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        if (!kept->running.load()) return;
        kept->renderBatch();
        dispatch_async(dispatch_get_main_queue(), ^{
            DebugView *view = weakSelf;
            if (!view) return;
            view->scheduled = NO;
            if (!kept->running.load()) return;
            [view refresh];
            if (kept->awake.load() && kept->running.load()) [view scheduleBatch];
        });
    });
}

- (void)refresh {
    std::vector<uint8_t> pixels;
    int w = 0, h = 0, spp = 0, batch = 1;
    ViewMode mode = ViewMode::Render;
    bool clay = false;
    std::string note;
    {
        std::lock_guard<std::mutex> lock(state->imageMutex);
        pixels = state->rgba;
        w = state->shownW;
        h = state->shownH;
        spp = state->shownSpp;
        batch = state->shownBatch;
        mode = state->shownView;
        clay = state->shownClay;
        note = state->shownNote;
    }
    imageView.image = imageFromRGBA(pixels, w, h);
    caption.stringValue = clay ? @"白模" : (mode == ViewMode::Normal ? @"法线" : @"焦散");

    NSString *extra = note.empty() ? @"" : [NSString stringWithFormat:@"    %@", [NSString stringWithUTF8String:note.c_str()]];
    status.stringValue = [NSString stringWithFormat:
        @"spp %d    每轮 %d    %dx%d    %s%@\n拖拽旋转   WASD 移动   空格/Shift 升降   滚轮变焦   白模开关只看几何   V 法线   1/2/3 分辨率   -/= 每轮采样   R 重置   P 保存   Esc 退出",
        spp, batch, w, h, viewName(mode, clay), extra];
    self.window.title = [NSString stringWithFormat:@"焦散透镜  spp %d", spp];
}

- (void)wake {
    state->inputEpoch.fetch_add(1);
    state->awake.store(true);
    [self scheduleBatch];
}

- (void)modelChanged:(NSPopUpButton *)sender {
    NSString *title = sender.titleOfSelectedItem;
    if (!title) return;
    {
        std::lock_guard<std::mutex> lock(state->inputMutex);
        state->pendingModel = title.UTF8String;
        state->note = std::string("正在读取 ") + title.UTF8String;
    }
    state->meshDirty.store(true);
    state->clayEpoch.fetch_add(1);
    [self wake];
}

- (void)claySwitchChanged:(NSSwitch *)sender {
    {
        std::lock_guard<std::mutex> lock(state->inputMutex);
        state->whiteModel = sender.state == NSControlStateValueOn;
        state->reset = true;
        state->note = state->whiteModel ? "白模：只显示几何，不追踪光线" : "平行光沿 -Z，墙上是焦散";
    }
    state->clayEpoch.fetch_add(1);
    [self wake];
}
- (void)setHeld:(uint32_t)bit down:(BOOL)down {
    if (down) state->held.fetch_or(bit);
    else state->held.fetch_and(~bit);
    if (down) [self wake];
}

- (void)keyDown:(NSEvent *)event {
    if (event.modifierFlags & NSEventModifierFlagCommand) {
        NSString *ch = event.charactersIgnoringModifiers.lowercaseString;
        if ([ch isEqualToString:@"q"]) {
            state->running.store(false);
            [NSApp terminate:nil];
        }
        return;
    }
    NSString *ch = event.charactersIgnoringModifiers.lowercaseString;
    if ([ch isEqualToString:@"w"]) { [self setHeld:KeyW down:YES]; return; }
    if ([ch isEqualToString:@"a"]) { [self setHeld:KeyA down:YES]; return; }
    if ([ch isEqualToString:@"s"]) { [self setHeld:KeyS down:YES]; return; }
    if ([ch isEqualToString:@"d"]) { [self setHeld:KeyD down:YES]; return; }
    if ([ch isEqualToString:@"p"] && !event.isARepeat) {
        std::lock_guard<std::mutex> lock(state->inputMutex);
        state->save = true;
        [self wake];
        return;
    }
    if ([ch isEqualToString:@"r"] && !event.isARepeat) {
        std::lock_guard<std::mutex> lock(state->inputMutex);
        state->reset = true;
        [self wake];
        return;
    }
    if ([ch isEqualToString:@"v"] && !event.isARepeat) {
        std::lock_guard<std::mutex> lock(state->inputMutex);
        state->view = state->view == ViewMode::Render ? ViewMode::Normal : ViewMode::Render;
        state->reset = true;
        state->note.clear();
        [self wake];
        return;
    }
    if ([ch isEqualToString:@"1"] || [ch isEqualToString:@"2"] || [ch isEqualToString:@"3"]) {
        if (event.isARepeat) return;
        int w = 360, h = 270;
        if ([ch isEqualToString:@"2"]) { w = 480; h = 360; }
        if ([ch isEqualToString:@"3"]) { w = 640; h = 480; }
        std::lock_guard<std::mutex> lock(state->inputMutex);
        state->pendingW = w;
        state->pendingH = h;
        state->note.clear();
        [self wake];
        return;
    }
    if ([ch isEqualToString:@"-"] || [ch isEqualToString:@"="]) {
        if (event.isARepeat) return;
        std::lock_guard<std::mutex> lock(state->inputMutex);
        if ([ch isEqualToString:@"-"]) state->sppBatch = std::max(1, state->sppBatch / 2);
        else state->sppBatch = std::min(8, state->sppBatch * 2);
        [self wake];
        return;
    }
    switch (event.keyCode) {
    case 49: [self setHeld:KeyUp down:YES]; break;          // space
    case 56: case 60: [self setHeld:KeyDown down:YES]; break; // shift
    case 126: [self setHeld:KeyUp down:YES]; break;
    case 125: [self setHeld:KeyDown down:YES]; break;
    case 53:
        state->running.store(false);
        [NSApp terminate:nil];
        break;
    default: break;
    }
}

- (void)keyUp:(NSEvent *)event {
    NSString *ch = event.charactersIgnoringModifiers.lowercaseString;
    if ([ch isEqualToString:@"w"]) [self setHeld:KeyW down:NO];
    else if ([ch isEqualToString:@"a"]) [self setHeld:KeyA down:NO];
    else if ([ch isEqualToString:@"s"]) [self setHeld:KeyS down:NO];
    else if ([ch isEqualToString:@"d"]) [self setHeld:KeyD down:NO];
    else if (event.keyCode == 49 || event.keyCode == 126) [self setHeld:KeyUp down:NO];
    else if (event.keyCode == 56 || event.keyCode == 60 || event.keyCode == 125) [self setHeld:KeyDown down:NO];
}

- (void)mouseDragged:(NSEvent *)event {
    std::lock_guard<std::mutex> lock(state->inputMutex);
    state->turnX += event.deltaX;
    state->turnY += event.deltaY;
    [self wake];
}

- (void)scrollWheel:(NSEvent *)event {
    std::lock_guard<std::mutex> lock(state->inputMutex);
    state->zoomDelta += event.scrollingDeltaY * 0.15f;
    [self wake];
}

- (void)windowWillClose:(NSNotification *)notification {
    state->running.store(false);
    [NSApp terminate:nil];
}

@end

std::filesystem::path findModelsDir(const std::filesystem::path &scenePath) {
    const std::filesystem::path candidates[] = {
        "Models",
        "CPUPathTracing/Models",
        scenePath.parent_path().parent_path().parent_path() / "Models",
    };
    for (const auto &path : candidates) {
        if (std::filesystem::is_directory(path)) return path;
    }
    return {};
}

std::vector<std::string> listObjModels(const std::filesystem::path &directory) {
    std::vector<std::string> names;
    if (directory.empty()) return names;
    for (const auto &entry : std::filesystem::directory_iterator(directory)) {
        if (!entry.is_regular_file()) continue;
        if (entry.path().extension() != ".obj") continue;
        names.push_back(entry.path().filename().string());
    }
    std::sort(names.begin(), names.end());
    return names;
}

std::filesystem::path findSceneJson() {
    const std::filesystem::path candidates[] = {
        "renderer/Scenes/caustics-lens.json",
        "CPUPathTracing/renderer/Scenes/caustics-lens.json",
        "../CPUPathTracing/renderer/Scenes/caustics-lens.json",
    };
    for (const auto &path : candidates) {
        if (std::filesystem::exists(path)) return path;
    }
    return {};
}

std::filesystem::path resolveMesh(const std::filesystem::path &scenePath, const std::filesystem::path &meshPath) {
    if (meshPath.is_absolute() && std::filesystem::exists(meshPath)) return meshPath;
    if (std::filesystem::exists(meshPath)) return meshPath;
    const std::filesystem::path beside = scenePath.parent_path() / meshPath;
    if (std::filesystem::exists(beside)) return beside;
    const std::filesystem::path fromProject = scenePath.parent_path().parent_path().parent_path() / meshPath;
    if (std::filesystem::exists(fromProject)) return fromProject;
    return {};
}

SceneDesc loadSceneDesc(const std::filesystem::path &path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("打不开场景 " + path.string());
    std::stringstream buffer;
    buffer << in.rdbuf();
    const Json root = JsonParser(buffer.str()).parse();
    SceneDesc desc;
    if (const Json *note = root.find("note")) desc.note = note->str;
    const Json &camera = root.need("camera");
    desc.eye = camera.vec3("eye");
    desc.target = camera.vec3("target");
    desc.fov = camera.number("fovDeg");
    const Json &beam = root.need("beam");
    desc.beamDir = beam.vec3("direction");
    desc.beamOrigin = beam.vec3("origin");
    const Json &half = beam.need("halfExtent");
    if (half.arr.size() != 2) throw std::runtime_error("beam.halfExtent 需要 2 个数");
    desc.beamHalf = { static_cast<float>(half.arr[0].num), static_cast<float>(half.arr[1].num) };
    desc.beamRays = beam.integerOr("rays", 256);
    const Json &marker = beam.need("marker");
    desc.beamPoint = marker.vec3("point");
    desc.beamNormal = marker.vec3("normal");
    desc.beamRadius = marker.number("radius");
    desc.beamAlbedo = marker.vec3Or("albedo", desc.beamAlbedo);
    const Json &receiver = root.need("receiver");
    desc.wallPoint = receiver.vec3("point");
    desc.wallNormal = receiver.vec3("normal");
    desc.wallRadius = receiver.number("radius");
    desc.wallAlbedo = receiver.vec3Or("albedo", desc.wallAlbedo);
    desc.mapHalf = receiver.numberOr("mapHalf", desc.mapHalf);
    desc.bins = receiver.integerOr("bins", desc.bins);
    const Json &meshes = root.need("meshes");
    if (meshes.arr.empty()) throw std::runtime_error("场景 JSON 没有网格");
    const Json &mesh = meshes.arr[0];
    desc.meshPath = resolveMesh(path, mesh.text("path"));
    if (desc.meshPath.empty()) throw std::runtime_error("找不到网格 " + mesh.text("path"));
    desc.triMax = mesh.integerOr("triMax", 0);
    if (const Json *material = mesh.find("material")) {
        desc.eta = material->numberOr("eta", desc.eta);
        desc.rough = material->numberOr("rough", desc.rough);
        desc.glassAlbedo = material->vec3Or("albedo", desc.glassAlbedo);
    }
    if (const Json *transform = mesh.find("transform")) {
        desc.meshScale = transform->vec3Or("scale", desc.meshScale);
        desc.meshRotate = transform->vec3Or("rotateDeg", desc.meshRotate);
        desc.meshTranslate = transform->vec3Or("translate", desc.meshTranslate);
    }
    if (glm::dot(desc.beamDir, desc.beamDir) < 1e-8f) throw std::runtime_error("beam.direction 不能是零向量");
    return desc;
}

int main(int argc, char **argv) {
    @autoreleasepool {
        const bool dump = argc > 1 && std::string(argv[1]) == "--dump";
        std::filesystem::path scenePath;
        if (!dump && argc > 1) scenePath = argv[1];
        if (scenePath.empty()) scenePath = findSceneJson();
        if (scenePath.empty()) {
            std::cerr << "找不到场景 JSON renderer/Scenes/caustics-lens.json\n";
            return 1;
        }
        SceneDesc desc;
        try {
            desc = loadSceneDesc(scenePath);
        } catch (const std::exception &error) {
            std::cerr << error.what() << "\n";
            return 1;
        }
        auto triangles = loadObjTriangles(desc.meshPath, static_cast<size_t>(std::max(0, desc.triMax)));
        if (triangles.empty()) {
            std::cerr << "透镜网格没有三角形：" << desc.meshPath << "\n";
            return 1;
        }
        std::cerr << "场景 " << scenePath << "\n网格 " << desc.meshPath << "  " << triangles.size() << " 面\n";
        auto state = std::make_shared<AppState>(360, 270, desc, std::move(triangles));
        state->modelsDir = findModelsDir(scenePath);
        state->modelNames = listObjModels(state->modelsDir);
        if (dump) {
            state->sppBatch = 1;
            state->renderBatch();
            writePPM(state->film, "build/gui/lens.ppm", true);
            return 0;
        }

        [NSApplication sharedApplication];
        [NSApp setActivationPolicy:NSApplicationActivationPolicyRegular];

        DebugView *view = [[DebugView alloc] initWithState:state];
        NSWindow *window = [[NSWindow alloc] initWithContentRect:NSMakeRect(0, 0, 720, 640)
            styleMask:NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable | NSWindowStyleMaskResizable
            backing:NSBackingStoreBuffered
            defer:NO];
        window.title = @"焦散透镜";
        window.contentView = view;
        window.releasedWhenClosed = NO;
        window.delegate = view;
        [window center];
        [window makeKeyAndOrderFront:nil];
        [NSApp activate];
        [NSApp run];
    }
    return 0;
}
