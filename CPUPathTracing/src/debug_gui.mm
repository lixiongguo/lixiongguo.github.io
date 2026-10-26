// Native debug window for the MIS scene. Uses AppKit, not SFML.
// Left / right images update as samples accumulate.
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
#include "renderer/normal_renderer.hpp"
#include "thread/thread_pool.hpp"

#import <Cocoa/Cocoa.h>
#import "../../cpp/resource_hud.h"

#include <atomic>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <mutex>
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

enum class ViewMode { Split, MisOn, MisOff, Normal };

const char *viewName(ViewMode mode) {
    switch (mode) {
    case ViewMode::Split: return "并排  MIS开 | MIS关";
    case ViewMode::MisOn: return "只看 MIS开";
    case ViewMode::MisOff: return "只看 MIS关";
    case ViewMode::Normal: return "法线";
    }
    return "";
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
    AppState(int w, int h)
        : ground({ 0, 0, 0 }, { 0, 1, 0 }, 50),
          diffuseBall({ 0, 1, 0 }, 1),
          mirrorBall({ -2.4f, 1, 1.5f }, 1),
          lightSphere({ 0, 4.5f, 0 }, 0.6),
          groundMat({ 1, 1, 1 }),
          red(RGB(200, 90, 90)),
          mirrorMat({ 1, 1, 1 }),
          lightMat(RGB(255, 255, 255)),
          area(lightSphere, glm::vec3(35, 35, 35), true),
          filmOn(w, h),
          filmOff(w, h),
          camOn(filmOn, { 0, 2.5f, -6 }, { 0, 1.5f, 0 }, 45),
          camOff(filmOff, { 0, 2.5f, -6 }, { 0, 1.5f, 0 }, 45),
          pathOn(camOn, scene),
          pathOff(camOff, scene),
          normals(camOn, scene) {
        scene.addShape(ground, &groundMat);
        scene.addShape(diffuseBall, &red);
        scene.addShape(mirrorBall, &mirrorMat);
        scene.addAreaLight(&area, &lightMat);
        scene.build();
        pathOn.setUseMis(true);
        pathOff.setUseMis(false);
    }

    void resize(int w, int h) {
        filmOn.setResolution(w, h);
        filmOff.setResolution(w, h);
        filmOn.clear();
        filmOff.clear();
        camOn.zoom(0);
        camOff.zoom(0);
        spp = 0;
    }

    void clearFilms() {
        filmOn.clear();
        filmOff.clear();
        spp = 0;
    }

    bool applyInput(float dt) {
        uint32_t keys = held.load();
        float tx = 0, ty = 0, z = 0;
        bool wantReset = false;
        bool wantSave = false;
        int newW = 0, newH = 0;
        ViewMode mode;
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
        }

        bool moved = false;
        auto both = [&](Direction dir) {
            camOn.move(dt, dir);
            camOff.move(dt, dir);
            moved = true;
        };
        if (keys & KeyW) both(Direction::Forward);
        if (keys & KeyS) both(Direction::Backward);
        if (keys & KeyA) both(Direction::Left);
        if (keys & KeyD) both(Direction::Right);
        if (keys & KeyUp) both(Direction::Up);
        if (keys & KeyDown) both(Direction::Down);
        if (tx != 0 || ty != 0) {
            camOn.turn({ tx, ty });
            camOff.turn({ tx, ty });
            moved = true;
        }
        if (z != 0) {
            camOn.zoom(z);
            camOff.zoom(z);
            moved = true;
        }
        if (newW > 0 && newH > 0) {
            resize(newW, newH);
            moved = false;
        } else if (moved || wantReset) {
            clearFilms();
        }
        if (wantSave) {
            const bool reinhard = mode != ViewMode::Normal;
            writePPM(filmOn, "build/gui/mis_on.ppm", reinhard);
            writePPM(filmOff, "build/gui/mis_off.ppm", reinhard);
            std::lock_guard<std::mutex> lock(inputMutex);
            note = "已保存 build/gui/mis_on.ppm 和 mis_off.ppm";
        }
        return mode != ViewMode::Normal;
    }

    void renderBatch() {
        using clock = std::chrono::steady_clock;
        const auto now = clock::now();
        float dt = std::chrono::duration<float>(now - lastTick).count();
        lastTick = now;
        if (dt > 0.2f) dt = 0.2f;

        const bool reinhard = applyInput(dt);
        ViewMode mode;
        int batch = 1;
        {
            std::lock_guard<std::mutex> lock(inputMutex);
            mode = view;
            batch = sppBatch;
        }

        auto accumulate = [&](auto &renderer, Film &film) {
            const size_t w = film.getWidth();
            const size_t h = film.getHeight();
            const int seed = spp;
            thread_pool.parallelFor(w, h, [&](size_t x, size_t y) {
                for (int i = 0; i < batch; ++i) {
                    film.addSample(x, y, renderer.renderPixel({ static_cast<int>(x), static_cast<int>(y), seed + i }));
                }
            });
            thread_pool.wait();
        };

        if (mode == ViewMode::Normal) {
            accumulate(normals, filmOn);
        } else if (mode == ViewMode::MisOn) {
            accumulate(pathOn, filmOn);
        } else if (mode == ViewMode::MisOff) {
            accumulate(pathOff, filmOff);
        } else {
            accumulate(pathOn, filmOn);
            accumulate(pathOff, filmOff);
        }
        spp += batch;

        std::vector<uint8_t> on, off;
        if (mode != ViewMode::MisOff) writeRGBA(filmOn, on, reinhard);
        if (mode == ViewMode::Split || mode == ViewMode::MisOff) writeRGBA(filmOff, off, true);

        std::string caption;
        {
            std::lock_guard<std::mutex> lock(inputMutex);
            caption = note;
        }
        std::lock_guard<std::mutex> lock(imageMutex);
        rgbaOn.swap(on);
        rgbaOff.swap(off);
        shownW = static_cast<int>(filmOn.getWidth());
        shownH = static_cast<int>(filmOn.getHeight());
        shownSpp = spp;
        shownView = mode;
        shownBatch = batch;
        shownNote = caption;
    }

    Plane ground;
    Sphere diffuseBall;
    Sphere mirrorBall;
    Sphere lightSphere;
    GroundMaterial groundMat;
    DiffuseMaterial red;
    SpecularMaterial mirrorMat;
    DiffuseMaterial lightMat;
    AreaLight area;
    Scene scene;
    Film filmOn;
    Film filmOff;
    Camera camOn;
    Camera camOff;
    PathTracingRenderer pathOn;
    PathTracingRenderer pathOff;
    NormalRenderer normals;

    std::atomic<bool> running { true };
    std::atomic<uint32_t> held { 0 };
    std::mutex inputMutex;
    float turnX = 0, turnY = 0, zoomDelta = 0;
    bool reset = false;
    bool save = false;
    int pendingW = 0, pendingH = 0;
    int sppBatch = 1;
    ViewMode view = ViewMode::Split;
    std::string note;
    int spp = 0;
    std::chrono::steady_clock::time_point lastTick = std::chrono::steady_clock::now();

    std::mutex imageMutex;
    std::vector<uint8_t> rgbaOn, rgbaOff;
    int shownW = 0, shownH = 0, shownSpp = 0, shownBatch = 1;
    ViewMode shownView = ViewMode::Split;
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
    NSImageView *leftView;
    NSImageView *rightView;
    NSTextField *leftCaption;
    NSTextField *rightCaption;
    NSTextField *status;
    NSStackView *images;
    BOOL scheduled;
}

- (instancetype)initWithState:(std::shared_ptr<AppState>)appState {
    self = [super initWithFrame:NSMakeRect(0, 0, 900, 520)];
    if (!self) return nil;
    state = std::move(appState);

    leftCaption = [self caption:@"MIS 开"];
    rightCaption = [self caption:@"MIS 关"];
    leftView = [self imageView];
    rightView = [self imageView];

    NSStackView *leftCol = [self column:leftCaption image:leftView];
    NSStackView *rightCol = [self column:rightCaption image:rightView];
    images = [[NSStackView alloc] init];
    images.orientation = NSUserInterfaceLayoutOrientationHorizontal;
    images.spacing = 12;
    images.distribution = NSStackViewDistributionFillEqually;
    [images addArrangedSubview:leftCol];
    [images addArrangedSubview:rightCol];

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
    [root addArrangedSubview:images];
    [root addArrangedSubview:status];
    [self addSubview:root];
    [ResourceHud attachToView:self];

    [NSLayoutConstraint activateConstraints:@[
        [root.leadingAnchor constraintEqualToAnchor:self.leadingAnchor],
        [root.trailingAnchor constraintEqualToAnchor:self.trailingAnchor],
        [root.topAnchor constraintEqualToAnchor:self.topAnchor],
        [root.bottomAnchor constraintEqualToAnchor:self.bottomAnchor],
        [leftView.heightAnchor constraintEqualToAnchor:leftView.widthAnchor multiplier:0.75],
        [leftView.widthAnchor constraintGreaterThanOrEqualToConstant:360],
    ]];
    return self;
}

- (NSTextField *)caption:(NSString *)text {
    NSTextField *label = [[NSTextField alloc] init];
    label.editable = NO;
    label.bezeled = NO;
    label.drawsBackground = NO;
    label.stringValue = text;
    label.font = [NSFont boldSystemFontOfSize:13];
    return label;
}

- (NSImageView *)imageView {
    NSImageView *view = [[NSImageView alloc] init];
    view.imageScaling = NSImageScaleProportionallyUpOrDown;
    view.imageAlignment = NSImageAlignCenter;
    view.wantsLayer = YES;
    view.layer.backgroundColor = NSColor.blackColor.CGColor;
    [view setContentHuggingPriority:NSLayoutPriorityDefaultLow forOrientation:NSLayoutConstraintOrientationVertical];
    return view;
}

- (NSStackView *)column:(NSTextField *)caption image:(NSImageView *)image {
    NSStackView *col = [[NSStackView alloc] init];
    col.orientation = NSUserInterfaceLayoutOrientationVertical;
    col.spacing = 4;
    col.alignment = NSLayoutAttributeLeading;
    [col addArrangedSubview:caption];
    [col addArrangedSubview:image];
    [image setContentHuggingPriority:NSLayoutPriorityDefaultLow forOrientation:NSLayoutConstraintOrientationHorizontal];
    return col;
}

- (BOOL)acceptsFirstResponder { return YES; }

- (NSView *)hitTest:(NSPoint)point {
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
            [view scheduleBatch];
        });
    });
}

- (void)refresh {
    std::vector<uint8_t> on, off;
    int w = 0, h = 0, spp = 0, batch = 1;
    ViewMode mode = ViewMode::Split;
    std::string note;
    {
        std::lock_guard<std::mutex> lock(state->imageMutex);
        on = state->rgbaOn;
        off = state->rgbaOff;
        w = state->shownW;
        h = state->shownH;
        spp = state->shownSpp;
        batch = state->shownBatch;
        mode = state->shownView;
        note = state->shownNote;
    }
    const bool showOff = mode == ViewMode::Split || mode == ViewMode::MisOff;
    const bool showOn = mode != ViewMode::MisOff;
    leftView.superview.hidden = !showOn;
    rightView.superview.hidden = !showOff;
    if (showOn) leftView.image = imageFromRGBA(on, w, h);
    if (showOff) rightView.image = imageFromRGBA(off, w, h);
    if (mode == ViewMode::MisOff) {
        leftCaption.stringValue = @"MIS 关";
    } else if (mode == ViewMode::Normal) {
        leftCaption.stringValue = @"法线";
    } else {
        leftCaption.stringValue = @"MIS 开";
    }
    rightCaption.stringValue = @"MIS 关";

    NSString *extra = note.empty() ? @"" : [NSString stringWithFormat:@"    %@", [NSString stringWithUTF8String:note.c_str()]];
    status.stringValue = [NSString stringWithFormat:
        @"spp %d    每轮 %d    %dx%d    %s%@\n拖拽旋转   WASD 移动   空格/Shift 升降   滚轮变焦   V 切换视图   1/2/3 分辨率   -/= 每轮采样   R 重置   P 保存   Esc 退出",
        spp, batch, w, h, viewName(mode), extra];
    self.window.title = [NSString stringWithFormat:@"路径追踪调试  spp %d", spp];
}

- (void)setHeld:(uint32_t)bit down:(BOOL)down {
    if (down) state->held.fetch_or(bit);
    else state->held.fetch_and(~bit);
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
        return;
    }
    if ([ch isEqualToString:@"r"] && !event.isARepeat) {
        std::lock_guard<std::mutex> lock(state->inputMutex);
        state->reset = true;
        return;
    }
    if ([ch isEqualToString:@"v"] && !event.isARepeat) {
        std::lock_guard<std::mutex> lock(state->inputMutex);
        state->view = static_cast<ViewMode>((static_cast<int>(state->view) + 1) % 4);
        state->reset = true;
        state->note.clear();
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
        return;
    }
    if ([ch isEqualToString:@"-"] || [ch isEqualToString:@"="]) {
        if (event.isARepeat) return;
        std::lock_guard<std::mutex> lock(state->inputMutex);
        if ([ch isEqualToString:@"-"]) state->sppBatch = std::max(1, state->sppBatch / 2);
        else state->sppBatch = std::min(8, state->sppBatch * 2);
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
}

- (void)scrollWheel:(NSEvent *)event {
    std::lock_guard<std::mutex> lock(state->inputMutex);
    state->zoomDelta += event.scrollingDeltaY * 0.15f;
}

- (void)windowWillClose:(NSNotification *)notification {
    state->running.store(false);
    [NSApp terminate:nil];
}

@end

int main(int argc, char **argv) {
    @autoreleasepool {
        auto state = std::make_shared<AppState>(360, 270);
        if (argc > 1 && std::string(argv[1]) == "--dump") {
            state->sppBatch = 2;
            state->renderBatch();
            writePPM(state->filmOn, "build/gui/mis_on.ppm", true);
            writePPM(state->filmOff, "build/gui/mis_off.ppm", true);
            return 0;
        }

        [NSApplication sharedApplication];
        [NSApp setActivationPolicy:NSApplicationActivationPolicyRegular];

        DebugView *view = [[DebugView alloc] initWithState:state];
        NSWindow *window = [[NSWindow alloc] initWithContentRect:NSMakeRect(0, 0, 980, 460)
            styleMask:NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable | NSWindowStyleMaskResizable
            backing:NSBackingStoreBuffered
            defer:NO];
        window.title = @"路径追踪调试";
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
