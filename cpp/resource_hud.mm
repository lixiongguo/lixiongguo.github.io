#import "resource_hud.h"

#import <mach/mach.h>
#include <algorithm>
#include <sys/resource.h>
#include <sys/sysctl.h>
#include <vector>

namespace {

double timevalSeconds(const struct timeval &value) {
    return value.tv_sec + value.tv_usec / 1e6;
}

struct CoreTick {
    uint64_t idle;
    uint64_t total;
};

std::vector<CoreTick> readCores() {
    natural_t count = 0;
    processor_info_array_t info = nullptr;
    mach_msg_type_number_t infoCount = 0;
    std::vector<CoreTick> cores;
    if (host_processor_info(mach_host_self(), PROCESSOR_CPU_LOAD_INFO, &count, &info, &infoCount) != KERN_SUCCESS) {
        return cores;
    }
    auto *load = reinterpret_cast<processor_cpu_load_info_t>(info);
    cores.resize(count);
    for (natural_t i = 0; i < count; ++i) {
        uint64_t total = 0;
        for (int state = 0; state < CPU_STATE_MAX; ++state) total += load[i].cpu_ticks[state];
        cores[i] = {load[i].cpu_ticks[CPU_STATE_IDLE], total};
    }
    vm_deallocate(mach_task_self(), reinterpret_cast<vm_address_t>(info), infoCount * sizeof(integer_t));
    return cores;
}

double memoryUsedGB(double *totalGB) {
    uint64_t physical = 0;
    size_t length = sizeof(physical);
    sysctlbyname("hw.memsize", &physical, &length, nullptr, 0);
    *totalGB = physical / (1024.0 * 1024.0 * 1024.0);
    vm_statistics64_data_t vm{};
    mach_msg_type_number_t count = HOST_VM_INFO64_COUNT;
    vm_size_t page = 0;
    if (host_statistics64(mach_host_self(), HOST_VM_INFO64, reinterpret_cast<host_info64_t>(&vm), &count) != KERN_SUCCESS ||
        host_page_size(mach_host_self(), &page) != KERN_SUCCESS) {
        return 0;
    }
    const uint64_t available = (vm.free_count + vm.inactive_count + vm.speculative_count) * static_cast<uint64_t>(page);
    return std::max(0.0, (physical - available) / (1024.0 * 1024.0 * 1024.0));
}

double processRssMB() {
    mach_task_basic_info_data_t info;
    mach_msg_type_number_t count = MACH_TASK_BASIC_INFO_COUNT;
    if (task_info(mach_task_self(), MACH_TASK_BASIC_INFO, reinterpret_cast<task_info_t>(&info), &count) != KERN_SUCCESS) {
        return 0;
    }
    return info.resident_size / (1024.0 * 1024.0);
}

} // namespace

@implementation ResourceHud {
    NSTimer *timer;
    std::vector<CoreTick> previous;
    double previousProc;
    CFAbsoluteTime previousAt;
    std::vector<double> loads;
    double selfCores;
    double rssMB;
    double usedGB;
    double totalGB;
}

+ (void)attachToView:(NSView *)parent {
    ResourceHud *hud = [[ResourceHud alloc] initWithFrame:NSZeroRect];
    hud.translatesAutoresizingMaskIntoConstraints = NO;
    [parent addSubview:hud positioned:NSWindowAbove relativeTo:nil];
    [NSLayoutConstraint activateConstraints:@[
        [hud.topAnchor constraintEqualToAnchor:parent.topAnchor constant:12],
        [hud.trailingAnchor constraintEqualToAnchor:parent.trailingAnchor constant:-12],
        [hud.widthAnchor constraintEqualToConstant:220],
        [hud.heightAnchor constraintEqualToConstant:118],
    ]];
}

- (instancetype)initWithFrame:(NSRect)frame {
    self = [super initWithFrame:frame];
    if (!self) return nil;
    self.wantsLayer = YES;
    previousProc = -1;
    previousAt = 0;
    usedGB = 0;
    totalGB = 0;
    selfCores = 0;
    rssMB = 0;
    [self sample];
    timer = [NSTimer scheduledTimerWithTimeInterval:1.0 target:self selector:@selector(sample) userInfo:nil repeats:YES];
    return self;
}

- (NSView *)hitTest:(NSPoint)point {
    return nil;
}

- (void)viewWillMoveToWindow:(NSWindow *)newWindow {
    [super viewWillMoveToWindow:newWindow];
    if (!newWindow && timer) {
        [timer invalidate];
        timer = nil;
    }
}

- (void)sample {
    const std::vector<CoreTick> now = readCores();
    if (previous.size() == now.size()) {
        loads.resize(now.size());
        for (size_t i = 0; i < now.size(); ++i) {
            const uint64_t totalDelta = now[i].total - previous[i].total;
            const uint64_t idleDelta = now[i].idle - previous[i].idle;
            loads[i] = totalDelta == 0 ? 0 : std::max(0.0, std::min(1.0, 1.0 - static_cast<double>(idleDelta) / totalDelta));
        }
    }
    previous = now;

    struct rusage usage;
    const CFAbsoluteTime at = CFAbsoluteTimeGetCurrent();
    if (getrusage(RUSAGE_SELF, &usage) == 0) {
        const double proc = timevalSeconds(usage.ru_utime) + timevalSeconds(usage.ru_stime);
        if (previousProc >= 0 && at > previousAt) {
            selfCores = std::max(0.0, (proc - previousProc) / (at - previousAt));
        }
        previousProc = proc;
        previousAt = at;
    }
    rssMB = processRssMB();
    usedGB = memoryUsedGB(&totalGB);
    [self setNeedsDisplay:YES];
}

- (void)drawRect:(NSRect)dirtyRect {
    NSRect bounds = NSInsetRect(self.bounds, 0.5, 0.5);
    NSBezierPath *card = [NSBezierPath bezierPathWithRoundedRect:bounds xRadius:8 yRadius:8];
    [[NSColor colorWithCalibratedWhite:0.08 alpha:0.92] setFill];
    [card fill];
    [[NSColor colorWithCalibratedWhite:1 alpha:0.16] setStroke];
    [card stroke];

    const NSUInteger busy = std::count_if(loads.begin(), loads.end(), [](double load) { return load >= 0.5; });
    NSDictionary *titleAttr = @{
        NSFontAttributeName: [NSFont monospacedSystemFontOfSize:12 weight:NSFontWeightSemibold],
        NSForegroundColorAttributeName: [NSColor colorWithCalibratedRed:1 green:0.84 blue:0.68 alpha:1]
    };
    NSString *title = loads.empty()
        ? @"资源"
        : [NSString stringWithFormat:@"资源  %lu/%lu 核忙", busy, loads.size()];
    [title drawAtPoint:NSMakePoint(10, self.bounds.size.height - 22) withAttributes:titleAttr];

    const CGFloat left = 10;
    const CGFloat width = self.bounds.size.width - 20;
    const CGFloat barBottom = 46;
    const CGFloat barHeight = 36;
    const NSUInteger count = loads.empty() ? 1 : loads.size();
    const CGFloat gap = 3;
    const CGFloat barWidth = std::max(2.0, (width - gap * (count - 1)) / count);
    for (NSUInteger i = 0; i < loads.size(); ++i) {
        const CGFloat x = left + i * (barWidth + gap);
        NSRect track = NSMakeRect(x, barBottom, barWidth, barHeight);
        [[NSColor colorWithCalibratedWhite:0.18 alpha:1] setFill];
        [[NSBezierPath bezierPathWithRoundedRect:track xRadius:1.5 yRadius:1.5] fill];
        NSRect fill = track;
        fill.size.height = std::max(2.0, barHeight * loads[i]);
        [[NSColor colorWithCalibratedRed:0.91 green:0.49 blue:0.05 alpha:1] setFill];
        [[NSBezierPath bezierPathWithRoundedRect:fill xRadius:1.5 yRadius:1.5] fill];
    }

    NSDictionary *rowAttr = @{
        NSFontAttributeName: [NSFont monospacedSystemFontOfSize:11 weight:NSFontWeightRegular],
        NSForegroundColorAttributeName: [NSColor colorWithCalibratedWhite:0.85 alpha:1]
    };
    NSString *mem = [NSString stringWithFormat:@"内存 %.1f / %.1f GB", usedGB, totalGB];
    NSString *selfRow = [NSString stringWithFormat:@"本进程  %.1f 核   %.0f MB", selfCores, rssMB];
    [mem drawAtPoint:NSMakePoint(10, 24) withAttributes:rowAttr];
    [selfRow drawAtPoint:NSMakePoint(10, 8) withAttributes:rowAttr];
}

@end
