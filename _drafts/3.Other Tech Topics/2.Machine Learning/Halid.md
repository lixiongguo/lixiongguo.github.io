---
title: "Halide：算法与调度的分离"
date: 2026-07-14
categories: [技术分享, 图像处理]
tags: [Halide, DSL, 自动优化, 编译器]
---

## 一、Halide DSL：算法（Function）与调度（Schedule）分离

### 1.1 设计动机

传统图像处理管线中，算法逻辑与优化代码（循环展开、向量化、并行化、分块等）交织在一起，导致代码难以维护、移植和迭代。

例如一个简单的 3×3 模糊，手写 C++ 高性能版本可能是这样：

```cpp
// 算法与优化完全耦合 —— 分块、向量化、边界处理混在一起
for (int y_tile = 0; y_tile < height; y_tile += 32) {
  for (int x_tile = 0; x_tile < width; x_tile += 256) {
    // ...临时缓冲区分配...
    for (int y = y_tile; y < min(y_tile + 32 + 2, height); y++) {
      for (int x = x_tile; x < min(x_tile + 256, width); x += 8) {
        // ...SIMD 内联计算...
      }
    }
  }
}
```

算法意图（3×3 模糊）被淹没在 tiling、向量化、边界处理的细节中。更直观的对比：

| | C++ 手写优化版 | Halide 版 |
|:---|:---|:---|
| 3×3 模糊代码行数 | ~80 行 | ~15 行 |
| 更换 tiling 参数 | 重写 4 层循环结构 | 改一行 `tile()` |
| 移植到 GPU | 重写整个文件（CUDA/OpenCL） | 改 `Target` 参数 |
| 尝试不同优化策略 | 每种策略需单独实现 | 增删 schedule 指令即可 |

Halide 的核心思想是 **将"做什么"（算法）与"怎么做"（调度）彻底解耦**。

### 1.2 Function — 算法描述

Halide 使用纯函数式的方式描述图像处理管线：

```cpp
Halide::Func brighter;
Halide::Var x, y;
brighter(x, y) = input(x, y) * 1.5f;
```

每个 `Func` 表达一个无限大的、按坐标索引的纯函数。管线由一系列 `Func` 的组合构成，例如一个 3×3 模糊：

```cpp
Func blur_x, blur_y;
blur_x(x, y) = (input(x-1, y) + input(x, y) + input(x+1, y)) / 3;
blur_y(x, y) = (blur_x(x, y-1) + blur_x(x, y) + blur_x(x, y+1)) / 3;
```

此时没有指定任何执行顺序、存储策略或并行方式——只定义了**数学含义**。

### 1.3 Schedule — 调度指令

在定义完算法后，通过 schedule 指令单独描述如何执行：

```cpp
blur_y.vectorize(x, 8);           // 最内层 x 维度向量化（SIMD，宽度 8）
blur_x.compute_at(blur_y, y);     // blur_x 在 blur_y 的 y 层级计算（行级融合）
blur_y.parallel(y);               // y 维度多线程并行
```

这三行 schedule 分别对应**三个不同的优化维度**：SIMD（指令级并行）、fusion（减少内存带宽）、多线程（线程级并行）——但算法定义完全不变。

**调度指令对应生成的伪代码**：

```cpp
// blur_x.compute_at(blur_y, y) + blur_y.vectorize(x, 8) + blur_y.parallel(y)
parallel for y in 0..height:             // 多线程
  // blur_x 在此层计算，只分配一行的临时缓冲区
  for x in 0..width step 8:              // SIMD 向量化，步长=8
    blur_x[x:x+8] = (input[x-1:x+7] + input[x:x+8] + input[x+1:x+9]) / 3
  for x in 0..width step 8:
    blur_y[x:x+8] = (blur_x_row_above[x:x+8] + blur_x[x:x+8] + blur_x_row_below[x:x+8]) / 3
```

**对比**：如果用 `compute_root()`（非融合版本），则需要两次遍历全图，产生中间全尺寸缓冲区，内存带宽翻倍。

核心调度原语：

| 原语 | 含义 |
|:---|:---|
| `compute_root()` | 作为独立阶段计算并存储全量结果 |
| `compute_at(f, var)` | 在消费者 f 的 var 循环层级内联计算（fusion） |
| `store_at(f, var)` | 控制在哪个层级分配存储 |
| `vectorize(var, factor)` | SIMD 向量化 |
| `parallel(var)` | 多线程并行 |
| `unroll(var)` | 循环展开 |
| `split(var, outer, inner, factor)` | 循环拆分（用于 tiling） |
| `reorder(vars...)` | 重排循环嵌套顺序 |
| `tile(var, outer, inner, factor)` | split + reorder 的组合快捷方式 |

### 1.4 Update 定义与归约域

Halide 支持递归定义（update step），通过 `RDom`（归约域）表达：

```cpp
// 直方图计算
RDom r(0, width, 0, height);           // 归约域：遍历全图
histogram(clamp(input(r.x, r.y), 0, 255)) += 1;
```

以及多阶段更新的管线：

```cpp
// 膨胀操作
Func dilate;
dilate(x, y) = input(x, y);            // 初始定义
RDom kernel(-1, 3, -1, 3);             // 3×3 结构元素
dilate(clamp(x + kernel.x, 0, w-1),
       clamp(y + kernel.y, 0, h-1)) =
    max(dilate(x, y), input(x + kernel.x, y + kernel.y));
```

`RDom` 表达的是"在某个域上做归约/累积"，与传统循环有本质区别——它是声明式的，编译器可以自由重排归约顺序。

### 1.5 编译流程与后端

Halide 的完整编译管线：

```
Halide Algorithm + Schedule
        ↓
   IR Lowering (将 Func 表达式降级为循环 IR)
        ↓
   Loop Optimizations (应用 schedule：tiling, vectorize, unroll, ...)
        ↓
   Bounds Inference (自动推断中间缓冲区大小)
        ↓
   Code Generation (LLVM / C / OpenCL / Metal / CUDA / ...)
```

关键特性：
- **Bounds Inference**：无需手动指定中间缓冲区大小，编译器根据 schedule 和消费者索引自动推导
- **多后端**：同一份 Halide 代码可生成 LLVM IR（CPU）、PTX（CUDA）、SPIR-V（OpenCL）、Metal Shading Language
- **JIT 编译**：支持运行时即时编译，适合开发阶段快速迭代和自动调优场景

```cpp
// JIT 编译并运行
blur_y.compile_jit();
Buffer<uint8_t> result = blur_y.realize({width, height});

// AOT 编译为静态库
blur_y.compile_to_static_library("blur", {input}, "blur");
```

### 1.6 完整示例：一个可运行的 Halide 程序

以下是一个从读取图像到输出结果的完整管线（亮度提升 + 3×3 模糊）：

```cpp
#include "Halide.h"
#include "halide_image_io.h"
using namespace Halide;

int main(int argc, char **argv) {
    // 1. 加载输入图像
    Buffer<uint8_t> input = Tools::load_image("input.png");

    // 2. 定义算法：亮度提升 + 可分离 3×3 模糊
    Var x, y;
    Func brighter("brighter");
    brighter(x, y) = min(input(x, y) * 1.5f, 255.0f);  // 提亮并 clamp

    Func blur_x("blur_x"), blur_y("blur_y");
    blur_x(x, y) = (brighter(x-1, y) + brighter(x, y) + brighter(x+1, y)) / 3;
    blur_y(x, y) = (blur_x(x, y-1) + blur_x(x, y) + blur_x(x, y+1)) / 3;

    // 3. 定义调度（与算法完全分离）
    brighter.compute_root();                   // brighter 全图计算一次
    blur_x.compute_at(blur_y, y);              // blur_x 行级融合
    blur_y.vectorize(x, 8);                    // SIMD
    blur_y.parallel(y);                        // 多线程

    // 4. 编译并运行
    blur_y.compile_jit();
    Buffer<uint8_t> output = blur_y.realize({input.width(), input.height()});

    // 5. 保存结果
    Tools::save_image(output, "output.png");
    return 0;
}
```

编译运行：

```bash
# 需要 Halide 源码目录，编译时链接 libHalide
g++ example.cpp -I/path/to/Halide/include -L/path/to/Halide/bin -lHalide \
    -lpthread -ldl -o example
./example
```

### 1.7 分离的价值

- **可移植性**：同一套算法，只需改变 schedule 即可适配 x86/ARM/GPU/DSP
- **可探索性**：调度空间极大，可自动搜索最优组合。例如一个 5-stage 的管线，可能的 schedule 组合可达 $O(10^4)$ 量级——手工枚举不现实，这正是后续自动调度要解决的问题
- **可维护性**：算法逻辑清晰独立，优化不污染业务代码
- **渐进优化**：先写正确再写快，互不干扰

---

## 二、自动调度：从手写 Schedule 到自动搜索

手写 schedule 需要专家级调优经验，且每个平台都要重新调整。Halide 社区提出了两代自动调度器。

### 2.1 Mullapudi et al. (SIGGRAPH 2016) — 第一代 Auto-Scheduler

**论文**：*Automatically Scheduling Halide Image Processing Pipelines* (Mullapudi, Adams, Sharlet, Ragan-Kelley, Fatahalian)

核心思路：将 schedule 搜索建模为一个**分阶段决策问题**，使用贪心搜索 + 成本模型。

#### 工作流程

1. **内联分析**：对每个 `Func` 判断是否适合完全内联（inline）。简单、只被一次消费的 stage 倾向于内联，避免中间缓冲开销
2. **计算位置选择**：对于非内联的 stage，决定 `compute_root()` 还是 `compute_at()`，以及在哪一层计算
3. **存储位置选择**：决定中间结果的存储层级（与计算位置可不同，如 compute_at 但 store_root 用于重用）
4. **tiling 决策**：对计算密集型 stage 进行循环拆分与分块
5. **向量化与并行**：在最内层循环应用 `vectorize`，在外层循环应用 `parallel`

每一步使用一个**手工设计的成本函数**估算不同选择的内存占用、计算量和局部性收益，贪心选择最优。

#### 成本模型细节

手工成本函数主要考量：
- **计算冗余**：compute_at 可能导致重复计算（同一像素被多个 tile 覆盖），需权衡冗余 vs 带宽
- **工作集大小**：tiling 后每个 tile 的中间缓冲是否 fit L1/L2 cache
- **生产者-消费者局部性**：compute_at 越靠近消费者，临时缓冲区越小，局部性越好，但可能引入冗余计算

例如对于 blur 管线：
- `blur_x.compute_root()`：blur_x 全图存储，遍历两次全图 → 带宽大，无冗余
- `blur_x.compute_at(blur_y, y)`：blur_x 只存一行，blur_y 立即消费 → 带宽小，无冗余
- `blur_x.compute_at(blur_y, x)`：blur_x 只存一个向量宽度 → 但 blur_y 需要上下列，会重复计算 blur_x

#### 局限

- 成本模型是启发式的，不够精确
- 贪心搜索容易陷入局部最优
- 对 GPU 调度的支持有限

#### 从 V1 到 V2 的演进动因

Mullapudi 2016 的贪心方法存在根本性缺陷：

| 问题 | V1 的表现 | V2 的改进方向 |
|:---|:---|:---|
| 成本模型 | 手工启发式，平台相关 | 神经网络，从真实硬件数据学习 |
| 搜索策略 | 贪心，一步定终身 | Beam search，保留多条候选路径 |
| 泛化能力 | 仅覆盖常见 pattern | 随机程序采样，覆盖更广 |

核心洞察：**调度质量的预测本质上是数据驱动的问题**——与其手工建模，不如在目标硬件上实测并训练一个预测器。这就是 Adams et al. 的出发点。

### 2.2 Adams et al. (SIGGRAPH 2019 / ACM Trans. Graph. 2020) — Halide Autoscheduler V2

**论文**：
- *Learning to Optimize Halide with Tree Search and Random Programs* (Adams, Ma, Anderson, Baghdadi, Li, Gharbi, Steiner, Johnson, Fatahalian, Durand, 2019)
- 扩展版发表于 ACM TOG 2020

核心突破：**机器学习指导的 beam search + 大规模合成训练数据**。

#### 三大组件

##### (1) 程序采样器（Program Sampler）

自动生成大量随机的、语义正确的 Halide 管线作为训练数据。生成规则覆盖：
- 各种常见的 image processing pattern（点操作、stencil、reduction、pyramid、histogram）
- 不同规模的管线（2~20 个 Func）
- 不同的数据依赖拓扑结构

关键设计：采样器不仅生成算法，还**同时随机生成若干 schedule**，在每个 schedule 下**真实编译运行并测量时间**，构成 `(program, schedule) → runtime` 的训练对。这种合成数据的优势在于**零人工标注成本**，可无限扩展。

##### (2) 神经网络成本模型（Neural Cost Model）

结构：将 Halide 管线 + schedule 编码为**特征向量**（包含内存访问模式、循环结构、并行度等特征），输入一个全连接网络，预测该 schedule 下的**实际运行时间**。

**特征工程**（将程序结构转为数值向量）：

| 特征类别 | 具体内容 |
|:---|:---|
| 循环结构 | 嵌套深度、每层循环范围、步长 |
| 访存模式 | stride pattern、是否连续访存、对齐情况 |
| 计算密度 | 算术强度（FLOP/byte）、每像素操作数 |
| 并行特性 | 向量化宽度、并行线程数、同步点 |
| 内存占用 | 各 stage 分配大小、cache 级别命中估算 |
| 管线拓扑 | Func 依赖图的结构特征（深度、fan-out 等） |

这些特征将"程序文本"转化为**固定维度的实值向量**，使得同一网络可以为任意管线预测运行时间。

训练细节：
- 训练数据来自**真实硬件上运行**采样程序并测量时间
- 损失函数：`|log(predicted) - log(actual)|`（对数空间相对误差），对大程序和小程序同等重视
- 网络结构相对简单（全连接层），因为特征已经高度结构化

##### (3) Beam Search 调度搜索

对于给定的目标管线，在巨大的 schedule 空间中执行 beam search：
- 每一步选择一个调度决策（是否 inline、compute_at 位置、tile 参数等）
- 用神经网络成本模型评估每个候选 schedule 的预期运行时间
- 保留 top-K 候选继续展开（典型 K=32 或 64）
- 最终对候选进行**实际编译运行验证**，选出最快者

**为什么是 beam search 而非强化学习**：schedule 决策是序列化的（先决定 inline，再决定 compute_at，再决定 tiling），且每一步的决策空间有限（~几十个候选），beam search 比 RL 更简单高效。神经网络成本模型作为 oracle，指导每步的选择方向。

#### 效果

- 在 CPU 上达到手写专家 schedule 的 **~90-100%** 性能
- 在 GPU 上也有竞争力
- 搜索时间可接受（分钟级）

---

## 三、将现有图像处理库自动翻译为 Halide

**论文**：*Automatically Translating Image Processing Libraries to Halide* (Ma, Smith, Kamil, Ragan-Kelley)

### 3.1 问题

大量成熟的图像处理库（如 Adobe 的滤镜、OpenCV 算子、Photoshop 插件等）是用 C/C++ 手写的，算法与优化深度耦合。手动重写为 Halide 成本极高，且容易引入错误。

### 3.2 方法概述

提出一个 **C++ → Halide 的自动翻译系统**，输入为 C++ 图像处理函数的源代码，输出为等价的 Halide `Func` + 初步 schedule。

#### 核心挑战

1. **识别循环结构**：从嵌套 for 循环中恢复"按坐标索引的纯函数"语义
2. **区分算法与优化**：识别哪些操作是算法本质（如卷积核），哪些是优化手段（如 tiling）
3. **处理指针别名与副作用**：C++ 中常见 `in-place` 更新，需要转换为 Halide 的纯函数形式
4. **边界处理**：C++ 中通常有显式的边界条件判断，Halide 有内置的 `BoundaryConditions` 机制

### 3.3 技术路线

翻译系统基于 Clang/LLVM 工具链，在 AST 和 IR 两个层面进行分析：

1. **循环分析与归一化**
   - 对输入 C++ 代码做 polyhedral 分析，提取循环的迭代域和访存模式
   - 将 C 风格的 for 循环提升为 Halide 的 `RDom`（归约域）或纯坐标映射
   - 处理非完美嵌套循环、带 stride 的循环

2. **数据流恢复**
   - 通过 def-use 链追踪每个像素值的计算来源
   - 构建表达树（expression tree），映射到 Halide 的 `Expr` 体系
   - 将条件赋值（`if` 边界判断）转换为 Halide 的 `select()` / `clamp()`
   - 处理 C++ 中的类型转换、饱和运算等语义

3. **分离存储与计算**
   - 识别中间缓冲区的生命周期和使用范围
   - 将中间缓冲区映射为独立的 `Func` 或内联表达式
   - 推断数据依赖关系，生成初步的 `compute_at` / `store_at` 建议
   - 特别处理 in-place 更新：分析指针别名关系，判断是否可以安全重构

4. **Schedule 恢复**
   - 从原始 C++ 的 pragma / OpenMP 指令推断并行化
   - 从循环分块模式推断 tiling 参数
   - 生成与原始优化等价的 Halide schedule 作为起点

**系统流水线**：

```
C++ Source
    ↓
Clang AST → 识别图像处理模式（stencil / point-wise / reduction）
    ↓
Polyhedral Analysis → 提取迭代域、访存关系
    ↓
Dataflow Graph Construction → 构建 Halide Func 依赖图
    ↓
Expression Translation → C++ 表达式 → Halide Expr
    ↓
Schedule Extraction → 从原始优化恢复 schedule 指令
    ↓
Halide Code Generation
```

### 3.4 局限与前景

- 适用于**结构化的 stencil 管线**，对包含复杂控制流的算法（如连通域标记、动态规划）支持有限
- 无法处理 C++ 中通过函数指针/虚函数动态分发的算法变体
- 翻译后的 schedule 是原始优化的"忠实复刻"，而非重新搜索最优，可作为后续 auto-scheduler 的初始种子
- 为遗留代码向现代 DSL 迁移提供了实际可行的路径
- 未来方向：与 auto-scheduler 结合，将翻译出的初始 schedule 作为 beam search 的起点，进一步优化

---

## 四、业界应用与生态影响

### 4.1 实际部署案例

Halide 并非纯学术项目，已在多个重量级产品中部署：

| 产品/项目 | 应用场景 | 关键收益 |
|:---|:---|:---|
| **Google Pixel HDR+** | 多帧合成去噪、色调映射 | 毫秒级处理，低功耗 |
| **Google Photos** | 自动增强、风格化滤镜 | 跨 Android/iOS/Web 统一管线 |
| **Adobe Photoshop** | 部分滤镜后端（实验性） | 加速开发迭代 |
| **Instagram** | 实时滤镜处理 | 算法与优化独立演进 |
| **YouTube** | 视频缩略图处理 | 大规模批处理 |
| **MIT 的 fast-pipeline** | 通用图像管线编译器 | 学术界基准 |

### 4.2 对后续 DSL 的影响

Halide 的"分离关注点"设计范式深刻影响了后续系统：

- **TVM**（Apache）：将 Halide 的 schedule 概念扩展到深度学习算子编译，引入 tensorize 等新原语
- **Taichi**：将分离思想带到物理仿真和图形学领域，面向稀疏数据结构的 compute 与 data layout 分离
- **Gradient (MIT)**：将 Halide 的自动微分能力系统化，支持反向传播的 schedule
- **Darkroom (Stanford)**：将 Halide 理念扩展到硬件综合（FPGA），算法描述可直接生成 Verilog

---

## 五、快速上手

### 安装

```bash
# macOS
brew install halide

# 或从源码编译（推荐获取最新特性）
git clone https://github.com/halide/Halide.git
cd Halide
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j$(nproc)
```

### 学习路径

建议顺序：**CppCon 视频 → Tutorial 01–16 → `apps/` 实操 → CVPR notes / 博士论文深挖 → 自动调度论文**。

#### 1. 官方入口（优先）

| 资源 | 说明 |
|:---|:---|
| [Tutorials](https://halide-lang.org/tutorials) | lesson 01–16，语法与调度的主线教材；源码在仓库 `tutorials/` |
| [API 文档](https://halide-lang.org/docs) | `Func` / `Var` / schedule 原语查手册 |
| [CppCon 2020 演讲](https://halide-lang.org/)（Videos） | 语言全貌，比论文好上手 |
| 专家调度实录（同页第二条视频） | 同一算法的手写 schedule 过程 |
| GitHub [`apps/`](https://github.com/halide/Halide/tree/main/apps) | 真实管线示例（相机、滤波等） |
| GitHub `test/` | 语言边角用例；能查行为，但非教学向、偏 cryptic |
| Python 绑定 | `pip install halide`；说明见仓库 [`doc/Python.md`](https://github.com/halide/Halide/blob/main/doc/Python.md) |
| 提问渠道 | [GitHub Discussions](https://github.com/halide/Halide/discussions)（首选）；`halide-dev` 邮件列表；SO `#halide` |

#### 2. 课程讲义

- **CVPR 2015 Halide course notes**（官网 [Course Notes](https://halide-lang.org/)）— 图像处理语境下的系统导论
- **MIT 6.815 / 6.865** Frédo Durand 计算摄影课中的 Halide 导论

#### 3. 论文阅读顺序

**核心三篇**（设计哲学 → 自动调度 → ML 成本模型）：

1. *Halide: A Language and Compiler for Optimizing Parallelism, Locality, and Recomputation in Image Processing Pipelines*（PLDI 2013）
2. *Automatically Scheduling Halide Image Processing Pipelines*（SIGGRAPH 2016）
3. *Learning to Optimize Halide with Tree Search and Random Programs*（SIGGRAPH 2019）

**补充阅读**：

| 文献 | 用途 |
|:---|:---|
| SIGGRAPH 2012 *Decoupling Algorithms from Schedules...* | 调度模型雏形，比 PLDI 更偏动机 |
| CACM Research Highlights（同上工作综述版） | 比 PLDI 原文更易读 |
| Ragan-Kelley **MIT 博士论文**（2014） | 设计与实现最全 |
| *Differentiable Programming...*（SIGGRAPH 2018） | Differentiable Halide / 自动微分，与本文后半相关 |

官网列出的论文页也会提醒：语法会演进，**正确写法以 Tutorial 为准**，论文只用来理解思想。

#### 4. 工业 / 后端文档

- **Qualcomm Halide for HVX** 用户指南：Hexagon、Generator、AOT 很细
- 仓库 [`doc/`](https://github.com/halide/Halide/tree/main/doc)：Hexagon、WebAssembly、Vulkan / WebGPU、RunGen、CMake 集成等

#### 5. 中文 / 二手笔记

- AutoKernel：[Introduction to Halide](https://autokernel-docs-en.readthedocs.io/en/latest/tutorials/halide/halide_intro.html) — 入门概述
- 各类个人论文清单/笔记 — 当索引用；语法仍以官方 Tutorial 为准

#### 6. 实践

用 Halide 重写一个熟悉的图像处理算法（如 bilateral filter），对比手写 C++ / OpenCV 的性能与 schedule 改动成本；再试 `autoscheduler` 与手写 schedule 的差距。

---


## 总结

| 维度 | 要点 |
|:---|:---|
| **DSL 设计** | Function（算法）与 Schedule（调度）分离，一次编写、多平台部署 |
| **自动调度 V1** | 贪心搜索 + 手工成本模型，快速但不够精确 |
| **自动调度 V2** | 神经网络成本模型 + beam search，接近专家水平 |
| **自动翻译** | 将 C++ 图像处理代码自动转为 Halide，降低迁移成本 |

Halide 的设计哲学——**分离关注点**——启发了后续大量 DSL（如 TVM、Taichi 等），在编译器和编程语言领域影响深远。
