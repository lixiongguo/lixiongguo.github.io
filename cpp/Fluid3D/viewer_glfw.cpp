// Cross-platform viewer for the Batty free-surface solver: GLFW + OpenGL + Dear ImGui.
// Shares the scene/simulation state with the macOS AppKit viewer through viewer_core.hpp.
#include "viewer_core.hpp"

#include <GLFW/glfw3.h>
#include <GL/gl.h>

#include "imgui.h"
#include "imgui_impl_glfw.h"
#include "imgui_impl_opengl3.h"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

namespace {

const int kFrameWidth = 720;
const int kFrameHeight = 540;

const char *kChineseFontPaths[] = {
    "/mnt/c/Windows/Fonts/msyh.ttc",
    "/mnt/c/Windows/Fonts/msyh.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
};

struct Viewer {
    std::shared_ptr<SimState> state;
    std::vector<uint8_t> pixels;
    GLuint texture = 0;
    bool rotating = false;
    bool wantClose = false;
};

Viewer &viewer() {
    static Viewer instance;
    return instance;
}

void fillCircle(std::vector<uint8_t> &pixels, float cx, float cy, float radius) {
    const int x0 = std::max(0, static_cast<int>(cx - radius));
    const int x1 = std::min(kFrameWidth - 1, static_cast<int>(cx + radius + 1));
    const int y0 = std::max(0, static_cast<int>(cy - radius));
    const int y1 = std::min(kFrameHeight - 1, static_cast<int>(cy + radius + 1));
    const float r2 = radius * radius;
    for (int y = y0; y <= y1; ++y) {
        const float dy = static_cast<float>(y) - cy;
        for (int x = x0; x <= x1; ++x) {
            const float dx = static_cast<float>(x) - cx;
            if (dx * dx + dy * dy > r2) continue;
            const size_t offset = (static_cast<size_t>(y) * kFrameWidth + x) * 4;
            pixels[offset + 0] = 94;
            pixels[offset + 1] = 199;
            pixels[offset + 2] = 255;
            pixels[offset + 3] = 255;
        }
    }
}

// Software rasterisation of the particle cloud, matching the AppKit drawRect.
void drawSnapshot(const Snapshot &shot, const SimState &state) {
    Viewer &v = viewer();
    std::vector<uint8_t> &pixels = v.pixels;
    pixels.assign(static_cast<size_t>(kFrameWidth) * kFrameHeight * 4, 0);
    for (size_t i = 0; i < pixels.size(); i += 4) {
        pixels[i + 0] = 6;
        pixels[i + 1] = 11;
        pixels[i + 2] = 20;
        pixels[i + 3] = 255;
    }
    if (!shot.ready) return;

    const Vec3f target = boundaryCentre;
    const float yaw = state.yaw;
    const float pitch = state.pitch;
    const Vec3f eye = target + Vec3f(
        state.distance * cosf(pitch) * sinf(yaw),
        state.distance * sinf(pitch),
        state.distance * cosf(pitch) * cosf(yaw));
    const Vec3f forward = normalized(target - eye);
    const Vec3f worldUp(0, 1, 0);
    Vec3f right = cross(forward, worldUp);
    if (mag(right) < 1e-4f) right = Vec3f(1, 0, 0);
    right = normalized(right);
    const Vec3f up = cross(right, forward);
    const float focal = static_cast<float>(std::min(kFrameWidth, kFrameHeight)) * 0.9f;
    const float originX = kFrameWidth * 0.5f;
    const float originY = kFrameHeight * 0.5f + 10.f;
    const float minRadius = 1.6f;

    for (const Vec3f &particle : shot.particles) {
        const Vec3f rel = particle - eye;
        const float depth = dot(rel, forward);
        if (depth < 0.05f) continue;
        const float sx = originX + dot(rel, right) / depth * focal;
        const float syScreen = originY + dot(rel, up) / depth * focal;
        // Texture row 0 is the top row, the screen Y axis points up.
        const float sy = static_cast<float>(kFrameHeight - 1) - syScreen;
        float radius = shot.radius / depth * focal;
        if (radius < minRadius) radius = minRadius;
        fillCircle(pixels, sx, sy, radius);
    }
}

void uploadTexture() {
    Viewer &v = viewer();
    if (v.texture == 0) {
        glGenTextures(1, &v.texture);
        glBindTexture(GL_TEXTURE_2D, v.texture);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, kFrameWidth, kFrameHeight, 0, GL_RGBA, GL_UNSIGNED_BYTE,
                     v.pixels.data());
        return;
    }
    glBindTexture(GL_TEXTURE_2D, v.texture);
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, kFrameWidth, kFrameHeight, GL_RGBA, GL_UNSIGNED_BYTE, v.pixels.data());
}

void simLoop(std::shared_ptr<SimState> state) {
    {
        std::lock_guard<std::mutex> lock(state->snapshotMutex);
        state->latest = state->capture(state->paused.load());
    }
    while (state->running.load()) {
        int nextResolution = 0;
        bool reset = false;
        {
            std::lock_guard<std::mutex> lock(state->commandMutex);
            reset = state->wantReset;
            nextResolution = state->pendingResolution;
            state->wantReset = false;
            state->pendingResolution = 0;
        }
        if (nextResolution > 0) state->reset(nextResolution);
        else if (reset) state->reset(state->res);

        const bool isPaused = state->paused.load();
        if (!isPaused) state->step();
        {
            std::lock_guard<std::mutex> lock(state->snapshotMutex);
            state->latest = state->capture(isPaused);
        }
        if (isPaused) std::this_thread::sleep_for(std::chrono::milliseconds(50));
        else std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
}

std::string statusText() {
    Viewer &v = viewer();
    Snapshot shot;
    {
        std::lock_guard<std::mutex> lock(v.state->snapshotMutex);
        shot = v.state->latest;
    }
    char buffer[256];
    if (!shot.ready) {
        std::snprintf(buffer, sizeof(buffer), "正在初始化 %d³ 网格…", v.state->res);
        return std::string(buffer);
    }
    std::snprintf(buffer, sizeof(buffer),
                  "%d³    %d 粒子    第 %d 帧    %.0f ms    %s    拖拽旋转  滚轮缩放  空格暂停  R 重置  1/2/3 分辨率  Esc 退出",
                  shot.resolution, static_cast<int>(shot.particles.size()), shot.frame, shot.stepMs,
                  shot.paused ? "暂停" : "播放");
    return std::string(buffer);
}

std::string titleText() {
    Viewer &v = viewer();
    Snapshot shot;
    {
        std::lock_guard<std::mutex> lock(v.state->snapshotMutex);
        shot = v.state->latest;
    }
    char buffer[128];
    std::snprintf(buffer, sizeof(buffer), "流体模拟  %d³  帧 %d", shot.resolution, shot.frame);
    return std::string(buffer);
}

void requestReset() {
    Viewer &v = viewer();
    std::lock_guard<std::mutex> lock(v.state->commandMutex);
    v.state->wantReset = true;
}

void requestResolution(int resolution) {
    Viewer &v = viewer();
    std::lock_guard<std::mutex> lock(v.state->commandMutex);
    v.state->pendingResolution = resolution;
}

void keyCallback(GLFWwindow *window, int key, int scancode, int action, int mods) {
    (void)scancode;
    (void)mods;
    if (action == GLFW_REPEAT) return;
    if (ImGui::GetIO().WantCaptureKeyboard) return;
    if (action != GLFW_PRESS) return;
    Viewer &v = viewer();
    switch (key) {
    case GLFW_KEY_SPACE:
        v.state->paused.store(!v.state->paused.load());
        return;
    case GLFW_KEY_R: requestReset(); return;
    case GLFW_KEY_1: requestResolution(24); return;
    case GLFW_KEY_2: requestResolution(32); return;
    case GLFW_KEY_3: requestResolution(48); return;
    case GLFW_KEY_ESCAPE:
        v.state->running.store(false);
        v.wantClose = true;
        glfwSetWindowShouldClose(window, GLFW_TRUE);
        return;
    default: break;
    }
}

void scrollCallback(GLFWwindow *window, double xOffset, double yOffset) {
    (void)window;
    (void)xOffset;
    if (ImGui::GetIO().WantCaptureMouse) return;
    Viewer &v = viewer();
    v.state->distance -= static_cast<float>(yOffset) * 0.01f;
    if (v.state->distance < 0.8f) v.state->distance = 0.8f;
    if (v.state->distance > 6.f) v.state->distance = 6.f;
}

void closeCallback(GLFWwindow *window) {
    (void)window;
    viewer().state->running.store(false);
    viewer().wantClose = true;
}

void buildUi() {
    Viewer &v = viewer();
    const ImGuiIO &io = ImGui::GetIO();
    ImGui::SetNextWindowPos(ImVec2(0, 0));
    ImGui::SetNextWindowSize(io.DisplaySize);
    ImGui::Begin("流体模拟", nullptr,
                 ImGuiWindowFlags_NoTitleBar | ImGuiWindowFlags_NoResize |
                     ImGuiWindowFlags_NoMove | ImGuiWindowFlags_NoCollapse |
                     ImGuiWindowFlags_NoBringToFrontOnFocus);

    ImGui::Text("%s", statusText().c_str());
    ImGui::Separator();

    const float avail = ImGui::GetContentRegionAvail().x;
    const float aspect = static_cast<float>(kFrameHeight) / static_cast<float>(kFrameWidth);
    float width = avail;
    float height = width * aspect;
    const float maxHeight = ImGui::GetContentRegionAvail().y;
    if (height > maxHeight && maxHeight > 0) {
        height = maxHeight;
        width = height / aspect;
    }
    ImGui::SetCursorPosX((ImGui::GetWindowSize().x - width) * 0.5f);
    ImGui::Image(reinterpret_cast<ImTextureID>(static_cast<intptr_t>(v.texture)), ImVec2(width, height));

    if (ImGui::IsItemHovered() && ImGui::IsMouseClicked(ImGuiMouseButton_Left)) v.rotating = true;
    if (ImGui::IsMouseReleased(ImGuiMouseButton_Left)) v.rotating = false;
    if (v.rotating && ImGui::IsMouseDown(ImGuiMouseButton_Left)) {
        if (io.MouseDelta.x != 0.f || io.MouseDelta.y != 0.f) {
            v.state->yaw += io.MouseDelta.x * 0.01f;
            v.state->pitch -= io.MouseDelta.y * 0.01f;
            if (v.state->pitch > 1.2f) v.state->pitch = 1.2f;
            if (v.state->pitch < -1.2f) v.state->pitch = -1.2f;
        }
    }

    ImGui::End();
}

int runWindow() {
    Viewer &v = viewer();
    if (!glfwInit()) {
        std::cerr << "glfwInit 失败\n";
        return 1;
    }
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 0);
    GLFWwindow *window = glfwCreateWindow(960, 760, "流体模拟", nullptr, nullptr);
    if (!window) {
        std::cerr << "glfwCreateWindow 失败\n";
        glfwTerminate();
        return 1;
    }
    glfwMakeContextCurrent(window);
    glfwSwapInterval(1);
    glfwSetWindowUserPointer(window, &v);
    glfwSetKeyCallback(window, keyCallback);
    glfwSetScrollCallback(window, scrollCallback);
    glfwSetWindowCloseCallback(window, closeCallback);

    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO &io = ImGui::GetIO();
    io.IniFilename = nullptr; // 不在工程目录里写 imgui.ini
    bool fontLoaded = false;
    for (const char *path : kChineseFontPaths) {
        if (io.Fonts->AddFontFromFileTTF(path, 16.f, nullptr, io.Fonts->GetGlyphRangesChineseFull()) != nullptr) {
            fontLoaded = true;
            break;
        }
    }
    if (!fontLoaded) io.Fonts->AddFontDefault();
    ImGui::StyleColorsDark();
    ImGui_ImplGlfw_InitForOpenGL(window, true);
    ImGui_ImplOpenGL3_Init("#version 130");

    v.pixels.assign(static_cast<size_t>(kFrameWidth) * kFrameHeight * 4, 0);
    std::thread worker(simLoop, v.state);

    while (!glfwWindowShouldClose(window)) {
        glfwPollEvents();
        {
            Snapshot shot;
            {
                std::lock_guard<std::mutex> lock(v.state->snapshotMutex);
                shot = v.state->latest;
            }
            drawSnapshot(shot, *v.state);
        }
        uploadTexture();

        ImGui_ImplOpenGL3_NewFrame();
        ImGui_ImplGlfw_NewFrame();
        ImGui::NewFrame();
        buildUi();
        ImGui::Render();

        int displayW = 0;
        int displayH = 0;
        glfwGetFramebufferSize(window, &displayW, &displayH);
        glViewport(0, 0, displayW, displayH);
        glClearColor(0.02f, 0.04f, 0.07f, 1.f);
        glClear(GL_COLOR_BUFFER_BIT);
        ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
        glfwSwapBuffers(window);

        const std::string title = titleText();
        glfwSetWindowTitle(window, title.c_str());
    }

    v.state->running.store(false);
    worker.join();

    if (v.texture != 0) glDeleteTextures(1, &v.texture);
    ImGui_ImplOpenGL3_Shutdown();
    ImGui_ImplGlfw_Shutdown();
    ImGui::DestroyContext();
    glfwDestroyWindow(window);
    glfwTerminate();
    return 0;
}

} // namespace

int main() {
    viewer().state = std::make_shared<SimState>(32);
    return runWindow();
}
