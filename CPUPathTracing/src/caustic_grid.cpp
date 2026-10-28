// One-shot 10x10 caustic contact sheet for output-Kushiro0.2.obj.
// Rows are lens orientation and which face the beam hits. Columns are
// distance from the lens center along the beam.
#include "shape/model.hpp"
#include "thread/thread_pool.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

namespace {

struct MeshData {
    std::vector<glm::vec3> verts;
    std::vector<std::array<int, 3>> faces;
    glm::vec3 center { 0.f };
    float flatZ = 0.f;
};

MeshData loadObj(const std::filesystem::path &path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("打不开 " + path.string());
    MeshData mesh;
    glm::vec3 lo(1e9f), hi(-1e9f);
    std::string line;
    while (std::getline(in, line)) {
        if (line.size() < 3 || line[0] == '#') continue;
        if (line[0] == 'v' && line[1] == ' ') {
            float x = 0, y = 0, z = 0;
            if (std::sscanf(line.c_str() + 2, "%f %f %f", &x, &y, &z) == 3) {
                mesh.verts.emplace_back(x, y, z);
                lo = glm::min(lo, mesh.verts.back());
                hi = glm::max(hi, mesh.verts.back());
            }
        } else if (line[0] == 'f' && line[1] == ' ') {
            int id[3] = {};
            if (std::sscanf(line.c_str() + 2, "%d %d %d", &id[0], &id[1], &id[2]) == 3) {
                mesh.faces.push_back({ id[0] - 1, id[1] - 1, id[2] - 1 });
            }
        }
    }
    mesh.center = (lo + hi) * 0.5f;
    mesh.flatZ = lo.z;
    std::cerr << "网格 " << mesh.verts.size() << " 顶点 " << mesh.faces.size() << " 面\n";
    return mesh;
}

struct Config {
    const char *name;
    glm::mat3 linear;
    glm::vec3 light;
    bool skipFlat;
};

bool transmit(const glm::vec3 &incident, const glm::vec3 &outward, float ior, glm::vec3 &out) {
    const bool front = glm::dot(incident, outward) < 0.f;
    const glm::vec3 n = front ? outward : -outward;
    const float eta = front ? (1.f / ior) : ior;
    const float cosI = glm::clamp(glm::dot(-incident, n), 0.f, 1.f);
    const float sin2T = eta * eta * (1.f - cosI * cosI);
    if (sin2T > 1.f) return false;
    out = glm::normalize(eta * incident + (eta * cosI - std::sqrt(1.f - sin2T)) * n);
    return true;
}

glm::mat3 rot180X() {
    return glm::mat3(1, 0, 0, 0, -1, 0, 0, 0, -1);
}
glm::mat3 rot180Y() {
    return glm::mat3(-1, 0, 0, 0, 1, 0, 0, 0, -1);
}
glm::mat3 flipZ() {
    return glm::mat3(1, 0, 0, 0, 1, 0, 0, 0, -1);
}

void writePGM(const std::filesystem::path &path, const std::vector<int> &bins, int n) {
    std::vector<int> sorted = bins;
    std::sort(sorted.begin(), sorted.end());
    const int pivot = std::max(1, sorted[sorted.size() * 99 / 100]);
    std::ofstream out(path, std::ios::binary);
    out << "P5\n" << n << " " << n << "\n255\n";
    for (int count : bins) out.put(static_cast<char>(std::min(255, count * 255 / pivot)));
}

} // namespace

int main(int argc, char **argv) {
    const std::filesystem::path obj = argc > 1
        ? argv[1]
        : "Models/output-Kushiro0.2.obj";
    const std::filesystem::path outDir = "build/gui/caustic-grid";
    std::filesystem::create_directories(outDir);

    const MeshData mesh = loadObj(obj);
    const glm::vec3 lightNeg(0.f, 0.f, -1.f);
    const glm::vec3 lightPos(0.f, 0.f, 1.f);
    const Config configs[] = {
        { "原网格 光-Z 先打曲面", glm::mat3(1.f), lightNeg, false },
        { "原网格 光+Z 先打平面", glm::mat3(1.f), lightPos, false },
        { "Z翻转 光-Z", flipZ(), lightNeg, false },
        { "Z翻转 光+Z", flipZ(), lightPos, false },
        { "绕X转180 光-Z", rot180X(), lightNeg, false },
        { "绕X转180 光+Z", rot180X(), lightPos, false },
        { "绕Y转180 光-Z", rot180Y(), lightNeg, false },
        { "绕Y转180 光+Z", rot180Y(), lightPos, false },
        { "只在曲面折射 光-Z", glm::mat3(1.f), lightNeg, true },
        { "只在曲面折射 光+Z", glm::mat3(1.f), lightPos, true },
    };
    const float distances[] = { 1.f, 1.5f, 2.f, 3.f, 4.f, 6.f, 8.f, 12.f, 16.f, 24.f };
    constexpr int kRays = 80;
    constexpr int kBins = 128;
    constexpr float kMapHalf = 1.6f;
    constexpr float kIor = 1.55f;

    std::ofstream index(outDir / "index.txt");
    index << "列距离";
    for (float distance : distances) index << "\t" << distance;
    index << "\n";

    for (int row = 0; row < 10; ++row) {
        const Config &config = configs[row];
        std::vector<Triangle> triangles;
        triangles.reserve(mesh.faces.size());
        for (const auto &face : mesh.faces) {
            glm::vec3 p[3];
            bool flat = true;
            for (int k = 0; k < 3; ++k) {
                p[k] = config.linear * (mesh.verts[face[k]] - mesh.center);
                if (mesh.verts[face[k]].z > mesh.flatZ + 0.02f) flat = false;
            }
            if (config.skipFlat && flat) continue;
            triangles.emplace_back(p[0], p[1], p[2]);
        }
        Model model(triangles);
        const glm::vec3 dir = glm::normalize(config.light);
        const glm::vec3 axisU = glm::normalize(glm::cross(
            std::abs(dir.y) < 0.9f ? glm::vec3(0, 1, 0) : glm::vec3(1, 0, 0), dir));
        const glm::vec3 axisV = glm::normalize(glm::cross(dir, axisU));
        const float margin = 0.35f;
        struct Exit { glm::vec3 origin; glm::vec3 direction; bool ok; };
        std::vector<Exit> exits(static_cast<size_t>(kRays) * kRays);
        thread_pool.parallelFor(kRays, kRays, [&](size_t ix, size_t iy) {
            const float u = -0.49f + 0.98f * (static_cast<float>(ix) + 0.5f) / kRays;
            const float v = -0.49f + 0.98f * (static_cast<float>(iy) + 0.5f) / kRays;
            Ray ray { -dir * margin + axisU * u + axisV * v, dir };
            for (int bounce = 0; bounce < 6; ++bounce) {
                auto hit = model.intersect(ray, 1e-4f, std::numeric_limits<float>::infinity());
                if (!hit.has_value()) {
                    if (bounce > 0) exits[iy * kRays + ix] = { ray.origin, ray.direction, true };
                    return;
                }
                glm::vec3 next;
                if (!transmit(ray.direction, glm::normalize(hit->normal), kIor, next)) return;
                ray.origin = hit->hit_point;
                ray.direction = next;
            }
        }, false);
        thread_pool.wait();
        int exited = 0;
        for (const auto &exit : exits) if (exit.ok) exited += 1;
        std::cerr << "行 " << row << " " << config.name << " 出射 " << exited << "\n";
        index << config.name;
        for (int col = 0; col < 10; ++col) {
            const float distance = distances[col];
            const glm::vec3 planePoint = dir * distance;
            std::vector<int> bins(static_cast<size_t>(kBins) * kBins, 0);
            int landed = 0;
            for (const auto &exit : exits) {
                if (!exit.ok) continue;
                const float nd = glm::dot(exit.direction, dir);
                if (nd < 1e-4f) continue;
                const float t = glm::dot(planePoint - exit.origin, dir) / nd;
                if (t <= 0.f) continue;
                const glm::vec3 p = exit.origin + t * exit.direction;
                const float su = (glm::dot(p, axisU) + kMapHalf) / (2.f * kMapHalf);
                const float sv = (glm::dot(p, axisV) + kMapHalf) / (2.f * kMapHalf);
                if (su < 0.f || sv < 0.f || su >= 1.f || sv >= 1.f) continue;
                bins[static_cast<size_t>(static_cast<int>(sv * kBins) * kBins + static_cast<int>(su * kBins))] += 1;
                landed += 1;
            }
            char file[64];
            std::snprintf(file, sizeof(file), "r%02d_c%02d.pgm", row, col);
            writePGM(outDir / file, bins, kBins);
            index << "\t" << landed;
        }
        index << "\n";
    }
    std::cerr << "格子图已写入 " << outDir << "\n";
    return 0;
}
