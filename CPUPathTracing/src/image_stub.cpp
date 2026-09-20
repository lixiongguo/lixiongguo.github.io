// 零依赖的 Image 桩：仅用于链接，本对比程序不调用 Film::save / Image 读写。
#include "image/image.hpp"
#include <fstream>

Image::Image(const std::filesystem::path &) {}

void Image::save(const std::filesystem::path &) const {
    // 未使用：本程序自行写出 PPM
}

void Image::savePPM(const std::filesystem::path &) const {}

void Image::saveEXR(const std::filesystem::path &) const {}
