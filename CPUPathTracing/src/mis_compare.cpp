// 自包含 MIS 对比程序：不依赖 SFML / OpenEXR / rapidobj。
// 直接用 renderPixel 采样并写出 PPM，分别渲染 MIS 开 / 关两张图。
#include "camera/camera.hpp"
#include "shape/sphere.hpp"
#include "shape/plane.hpp"
#include "shape/scene.hpp"
#include "util/rgb.hpp"
#include "material/diffuse_material.hpp"
#include "material/specular_material.hpp"
#include "material/ground_material.hpp"
#include "light/area_light.hpp"
#include "renderer/path_tracing_renderer.hpp"

#include <vector>
#include <fstream>
#include <cmath>
#include <iostream>

static void renderAndSave(PathTracingRenderer &renderer, int W, int H, int spp, const std::string &filename) {
    std::vector<glm::vec3> img(static_cast<size_t>(W) * H, glm::vec3(0));
    for (int y = 0; y < H; ++y) {
        for (int x = 0; x < W; ++x) {
            glm::vec3 c(0);
            for (int s = 0; s < spp; ++s) {
                // pixel_coord.z 用作不同样本的随机种子
                c += renderer.renderPixel({ x, y, s });
            }
            c /= static_cast<float>(spp);
            img[static_cast<size_t>(y) * W + x] = c;
        }
        if ((y + 1) % (H / 10 + 1) == 0) {
            std::cout << "  " << filename << " progress " << (y + 1) << "/" << H << std::endl;
        }
    }

    // Reinhard tonemap + gamma 2.2，写出二进制 PPM
    std::ofstream f(filename, std::ios::binary);
    f << "P6\n" << W << " " << H << "\n255\n";
    for (int y = 0; y < H; ++y) {
        for (int x = 0; x < W; ++x) {
            glm::vec3 c = img[static_cast<size_t>(y) * W + x];
            c = c / (1.0f + c);                          // Reinhard
            c = glm::pow(c, glm::vec3(1.0f / 2.2f));     // gamma
            uint8_t r = static_cast<uint8_t>(glm::clamp(c.r, 0.f, 1.f) * 255);
            uint8_t g = static_cast<uint8_t>(glm::clamp(c.g, 0.f, 1.f) * 255);
            uint8_t b = static_cast<uint8_t>(glm::clamp(c.b, 0.f, 1.f) * 255);
            f.write(reinterpret_cast<char *>(&r), 1);
            f.write(reinterpret_cast<char *>(&g), 1);
            f.write(reinterpret_cast<char *>(&b), 1);
        }
    }
    std::cout << "saved " << filename << std::endl;
}

int main() {
    const int W = 480, H = 360, spp = 64;

    Film film(W, H);
    Camera camera(film, { 0, 2.5f, -6 }, { 0, 1.5f, 0 }, 45);

    // ---- 极简场景：地面 + 漫反射球 + 镜面球 + 一盏小球面光源 ----
    Plane  ground      ({ 0, 0, 0 }, { 0, 1, 0 }, 50);
    Sphere diffuseBall ({ 0, 1, 0 }, 1);
    Sphere mirrorBall  ({ -2.4f, 1, 1.5f }, 1);
    Sphere lightSphere ({ 0, 4.5f, 0 }, 0.6);

    Scene scene;
    scene.addShape(ground, new GroundMaterial { { 1, 1, 1 } });
    scene.addShape(diffuseBall, new DiffuseMaterial { RGB(200, 90, 90) });
    scene.addShape(mirrorBall,  new SpecularMaterial { { 1, 1, 1 } });

    AreaLight areaLight(lightSphere, glm::vec3(35, 35, 35), /*double_side=*/true);
    scene.addAreaLight(&areaLight, new DiffuseMaterial { RGB(255, 255, 255) });

    scene.build();

    std::cout << "[MIS ON ] rendering..." << std::endl;
    PathTracingRenderer r_on(camera, scene);
    r_on.setUseMis(true);
    renderAndSave(r_on, W, H, spp, "mis_on.ppm");

    std::cout << "[MIS OFF] rendering (pure path tracing, NEE disabled)..." << std::endl;
    PathTracingRenderer r_off(camera, scene);
    r_off.setUseMis(false);
    renderAndSave(r_off, W, H, spp, "mis_off.ppm");

    return 0;
}
