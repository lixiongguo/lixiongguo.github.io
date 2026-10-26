// Native viewer for the Batty free-surface solver. Same scene as the old web demo.
#include "fluidsim.h"
#include "vec.h"

#import <Cocoa/Cocoa.h>

#include <atomic>
#include <chrono>
#include <cmath>
#include <mutex>
#include <string>
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

void simLoop(const std::shared_ptr<SimState>& state, void (^onFrame)(void)) {
    {
        std::lock_guard<std::mutex> lock(state->snapshotMutex);
        state->latest = state->capture(state->paused.load());
    }
    dispatch_async(dispatch_get_main_queue(), onFrame);
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
        dispatch_async(dispatch_get_main_queue(), onFrame);
        if (!state->running.load()) break;
        if (isPaused) [NSThread sleepForTimeInterval:0.05];
    }
}

} // namespace

@interface FluidView : NSView <NSWindowDelegate>
- (instancetype)initWithState:(std::shared_ptr<SimState>)state;
@end

@implementation FluidView {
    std::shared_ptr<SimState> state;
    NSTextField* status;
    BOOL loopStarted;
}

- (instancetype)initWithState:(std::shared_ptr<SimState>)simState {
    self = [super initWithFrame:NSMakeRect(0, 0, 900, 700)];
    if (!self) return nil;
    state = std::move(simState);
    status = [[NSTextField alloc] init];
    status.editable = NO;
    status.bezeled = NO;
    status.drawsBackground = NO;
    status.textColor = [NSColor colorWithCalibratedRed:0.62 green:0.78 blue:1 alpha:1];
    status.font = [NSFont monospacedSystemFontOfSize:12 weight:NSFontWeightRegular];
    status.stringValue = @"正在初始化 32³ 网格…";
    status.translatesAutoresizingMaskIntoConstraints = NO;
    [self addSubview:status];
    [NSLayoutConstraint activateConstraints:@[
        [status.leadingAnchor constraintEqualToAnchor:self.leadingAnchor constant:16],
        [status.bottomAnchor constraintEqualToAnchor:self.bottomAnchor constant:-12],
    ]];
    return self;
}

- (BOOL)acceptsFirstResponder { return YES; }

- (void)viewDidMoveToWindow {
    [super viewDidMoveToWindow];
    if (!self.window || loopStarted) return;
    [self.window makeFirstResponder:self];
    loopStarted = YES;
    std::shared_ptr<SimState> kept = state;
    __weak FluidView* weakSelf = self;
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        simLoop(kept, ^{
            FluidView* view = weakSelf;
            if (!view || !kept->running.load()) return;
            [view setNeedsDisplay:YES];
            [view refreshStatus];
        });
    });
}

- (void)refreshStatus {
    Snapshot shot;
    {
        std::lock_guard<std::mutex> lock(state->snapshotMutex);
        shot = state->latest;
    }
    if (!shot.ready) return;
    status.stringValue = [NSString stringWithFormat:
        @"%d³    %d 粒子    第 %d 帧    %.0f ms    %@    拖拽旋转  滚轮缩放  空格暂停  R 重置  1/2/3 分辨率  Esc 退出",
        shot.resolution,
        (int)shot.particles.size(),
        shot.frame,
        shot.stepMs,
        shot.paused ? @"暂停" : @"播放"];
    self.window.title = [NSString stringWithFormat:@"流体模拟  %d³  帧 %d", shot.resolution, shot.frame];
}

- (void)drawRect:(NSRect)dirtyRect {
    [[NSColor colorWithCalibratedRed:0.024 green:0.043 blue:0.078 alpha:1] setFill];
    NSRectFill(self.bounds);

    Snapshot shot;
    {
        std::lock_guard<std::mutex> lock(state->snapshotMutex);
        shot = state->latest;
    }
    if (!shot.ready) return;

    const Vec3f target = boundaryCentre;
    const float yaw = state->yaw;
    const float pitch = state->pitch;
    const Vec3f eye = target + Vec3f(
        state->distance * cosf(pitch) * sinf(yaw),
        state->distance * sinf(pitch),
        state->distance * cosf(pitch) * cosf(yaw));
    const Vec3f forward = normalized(target - eye);
    const Vec3f worldUp(0, 1, 0);
    Vec3f right = cross(forward, worldUp);
    if (mag(right) < 1e-4f) right = Vec3f(1, 0, 0);
    right = normalized(right);
    const Vec3f up = cross(right, forward);
    const float focal = (float)std::min(self.bounds.size.width, self.bounds.size.height) * 0.9f;
    const float originX = (float)NSMidX(self.bounds);
    const float originY = (float)NSMidY(self.bounds) + 10;

    CGContextRef ctx = [[NSGraphicsContext currentContext] CGContext];
    CGContextSetFillColorWithColor(ctx, [[NSColor colorWithCalibratedRed:0.37 green:0.78 blue:1 alpha:0.9] CGColor]);
    const float minRadius = 1.6f;
    for (const Vec3f& particle : shot.particles) {
        const Vec3f rel = particle - eye;
        const float depth = dot(rel, forward);
        if (depth < 0.05f) continue;
        const float sx = originX + dot(rel, right) / depth * focal;
        const float sy = originY + dot(rel, up) / depth * focal;
        float radius = shot.radius / depth * focal;
        if (radius < minRadius) radius = minRadius;
        CGContextFillEllipseInRect(ctx, CGRectMake(sx - radius, sy - radius, radius * 2, radius * 2));
    }
}

- (void)mouseDragged:(NSEvent*)event {
    state->yaw += event.deltaX * 0.01f;
    state->pitch -= event.deltaY * 0.01f;
    if (state->pitch > 1.2f) state->pitch = 1.2f;
    if (state->pitch < -1.2f) state->pitch = -1.2f;
    [self setNeedsDisplay:YES];
}

- (void)scrollWheel:(NSEvent*)event {
    state->distance -= event.scrollingDeltaY * 0.01f;
    if (state->distance < 0.8f) state->distance = 0.8f;
    if (state->distance > 6.f) state->distance = 6.f;
    [self setNeedsDisplay:YES];
}

- (void)keyDown:(NSEvent*)event {
    NSString* ch = event.charactersIgnoringModifiers.lowercaseString;
    if (event.keyCode == 49 && !event.isARepeat) {
        state->paused.store(!state->paused.load());
        return;
    }
    if ([ch isEqualToString:@"r"] && !event.isARepeat) {
        std::lock_guard<std::mutex> lock(state->commandMutex);
        state->wantReset = true;
        return;
    }
    if (!event.isARepeat && ([ch isEqualToString:@"1"] || [ch isEqualToString:@"2"] || [ch isEqualToString:@"3"])) {
        int resolution = 32;
        if ([ch isEqualToString:@"1"]) resolution = 24;
        if ([ch isEqualToString:@"3"]) resolution = 48;
        std::lock_guard<std::mutex> lock(state->commandMutex);
        state->pendingResolution = resolution;
        return;
    }
    if (event.keyCode == 53 || ((event.modifierFlags & NSEventModifierFlagCommand) && [ch isEqualToString:@"q"])) {
        state->running.store(false);
        [NSApp terminate:nil];
    }
}

- (void)windowWillClose:(NSNotification*)notification {
    state->running.store(false);
    [NSApp terminate:nil];
}

@end

int main() {
    @autoreleasepool {
        auto state = std::make_shared<SimState>(32);
        [NSApplication sharedApplication];
        [NSApp setActivationPolicy:NSApplicationActivationPolicyRegular];

        FluidView* view = [[FluidView alloc] initWithState:state];
        NSWindow* window = [[NSWindow alloc] initWithContentRect:NSMakeRect(0, 0, 960, 720)
            styleMask:NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable | NSWindowStyleMaskResizable
            backing:NSBackingStoreBuffered
            defer:NO];
        window.title = @"流体模拟";
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
