#pragma once
// 从 viewer.mm 抽出的平台无关核心：自由液面场景与模拟状态。
// macOS 的 viewer.mm 与跨平台的 viewer_glfw.cpp 共用本文件。

#include "fluidsim.h"
#include "vec.h"

#include <atomic>
#include <chrono>
#include <cmath>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

namespace {
float spherePhi(const Vec3f& position, const Vec3f& centre, float radius) {
    return dist(position, centre) - radius;
}

Vec3f boundaryCentre(0.5f, 0.5f, 0.5f);
float boundaryRadius = 0.35f;

float boundaryPhi(const Vec3f& position) {
    return -spherePhi(position, boundaryCentre, boundaryRadius);
}

float liquidPhi(const Vec3f& position) {
    return spherePhi(position, Vec3f(0.55f, 0.55f, 0.4f), 0.23f);
}

struct Snapshot {
    std::vector<Vec3f> particles;
    float radius = 0.02f;
    int resolution = 32;
    int frame = 0;
    float stepMs = 0;
    bool paused = false;
    bool ready = false;
};

struct SimState {
    explicit SimState(int resolution) { reset(resolution); }

    void reset(int resolution) {
        delete sim;
        sim = new FluidSim();
        res = resolution;
        sim->initialize(1.0f, res, res, res);
        sim->set_boundary(boundaryPhi);
        sim->set_liquid(liquidPhi);
        frame = 0;
    }

    void step() {
        const auto start = std::chrono::steady_clock::now();
        sim->advance(0.01f);
        const auto elapsed = std::chrono::steady_clock::now() - start;
        stepMs = std::chrono::duration<float, std::milli>(elapsed).count();
        frame += 1;
    }

    Snapshot capture(bool isPaused) const {
        Snapshot shot;
        shot.particles = sim->particles;
        shot.radius = sim->particle_radius;
        shot.resolution = res;
        shot.frame = frame;
        shot.stepMs = stepMs;
        shot.paused = isPaused;
        shot.ready = true;
        return shot;
    }

    ~SimState() { delete sim; }

    FluidSim* sim = nullptr;
    int res = 32;
    int frame = 0;
    float stepMs = 0;
    std::atomic<bool> running{true};
    std::atomic<bool> paused{false};
    std::mutex commandMutex;
    bool wantReset = false;
    int pendingResolution = 0;
    std::mutex snapshotMutex;
    Snapshot latest;
    float yaw = 0.9f;
    float pitch = 0.35f;
    float distance = 2.4f;
};

} // namespace
