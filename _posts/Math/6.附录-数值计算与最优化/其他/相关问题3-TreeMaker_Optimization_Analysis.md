# TreeMaker 优化问题与约束条件分析

本文基于 TreeMaker 5.x 源码、项目内置帮助文档，以及 Robert J. Lang / Demaine 等公开资料，整理 TreeMaker 中“折纸设计优化”的约束条件、优化目标和最终数学问题。

## 结论摘要

TreeMaker 的核心设计问题是：给定一个代表目标折纸基底的树图，寻找纸面上叶节点对应顶点的位置，并使折叠基底相对于原始纸张尽可能大。

最核心的优化问题可写为：

```text
maximize    m
variables   m, v_i for every terminal/leaf node i
subject to  v_i in P
            ||v_i - v_j|| >= m * l_ij, for every pair of leaf nodes i, j
            plus user-imposed equalities/inequalities
```

其中：

- `m` 是 scale，即一单位树边长度对应纸张边长的比例。
- `v_i = (x_i, y_i)` 是叶节点在纸面中的对应顶点。
- `P` 是纸张区域；源码中通常是 `[0, w] x [0, h]`。
- `l_ij` 是树图中两个叶节点之间路径的树长度，包含边长和可能的 strain。

源码实现中，最大化问题通过最小化负值来求解：

```text
minimize -m
```

TreeMaker 实际有三类优化器：

1. `tmScaleOptimizer`：最大化整体 scale，是最基本、最核心的优化。
2. `tmEdgeOptimizer`：在 scale 固定时，最大化选中边的共同 strain，用于放大/拉长选中的 flap。
3. `tmStrainOptimizer`：在 scale 固定时，最小化加权平方 strain，用于在额外全局条件下尽量小地扭曲边长。

从圆填充的角度看，TreeMaker 并不是单纯把若干圆塞进正方形，而是把目标模型先抽象成带边长的树。叶节点对应 flap 的尖端和纸面圆心，树上内部边对应连接 flap 的 river 区域；任意两叶节点之间的树路径长度，转化为纸面上这两个顶点必须保持的最小距离。也就是说，圆填充只是 TreeMaker 优化问题的几何直觉，源码中真正求解的是更一般的 tree embedding / circle-river packing 问题。

## 圆填充与 TreeMaker 约束的关系

`2022-05-03-圆填充与折纸.md` 中提到的 circle packing，可以看成 TreeMaker 核心路径约束的一个特例。

若目标树为 `T=(V,E)`，边长为 `l(e)`，两个叶节点 `i,j` 之间的树路径距离为：

```text
d_T(i,j) = sum l(e), for e on the tree path from i to j
```

TreeMaker 的基本距离约束是：

```text
||p_i - p_j|| >= s * d_T(i,j)
```

当树是 star tree，或者每个 flap 简化成一个以叶节点为圆心的圆时，`d_T(i,j)` 就退化成两个圆半径之和：

```text
||p_i - p_j|| >= s * (r_i + r_j)
```

这就是普通圆不相交约束。更一般的树含有内部边，此时 `d_T(i,j)` 还包含中间 river 的长度贡献：

```text
d_T(i,j) = r_i + r_j + sum internal river lengths
```

因此 TreeMaker 的路径约束同时表达了三件事：

- flap 圆不能重叠；
- 中间 river 需要足够宽/长的纸带空间；
- 纸面中圆和 river 的相邻关系应与目标树结构一致。

需要注意的是，数学笔记中常把约束平方化写成：

```text
||p_i - p_j||^2 - s^2 * d_T(i,j)^2 >= 0
```

这是等价的理论写法，可以避免根号。但 TreeMaker 5 源码中的 `PathFn1` 实际使用的是未平方形式：

```text
s * d_T(i,j) - ||p_i - p_j|| <= 0
```

这两种写法表达同一个可行域；差别只在数值实现和梯度形式。

## “有多少约束条件”的口径

这个问题需要区分三种口径。

第一，运行时某个具体模型的约束实例数量不是固定值，取决于树图的叶节点数量、可移动节点/边数量，以及用户添加了多少条件。以基本 scale 优化为例，若有 `N` 个叶节点，则至少有：

- 纸张边界约束：每个叶节点 `0 <= x_i <= w`、`0 <= y_i <= h`，等价于 `4N` 个边界不等式；源码中由变量上下界 `SetBounds()` 表示。
- 叶路径距离约束：每对叶节点一个，即 `N(N - 1) / 2` 个路径不等式；若某条路径被用户强制为 active path，则普通路径不等式会跳过，改由 active path 等式承担。
- scale 附加下界：源码额外加入 `m >= 0.1 * current_scale`，避免 scale 在优化中塌缩。
- 用户条件产生的额外约束：固定节点、对称、共线、角度固定/量化、固定边长、相同 strain 等。

第二，源码层面低层数学约束函数共有 26 个 `tmDifferentiableFn` 子类，定义在 `tmModel/tmOptimizers/tmConstraintFns.h` / `.cpp`。它们是优化器真正加入 NLCO 的标量函数。

第三，从用户/模型层面看，`tmCondition` 条件类共有 13 个具体子类，定义在 `tmModel/tmTreeClasses/tmCondition*.h/.cpp`。这些条件是用户可理解的高层约束，一个 `tmCondition` 可能生成一个或多个低层数学约束。

## 源码中的 26 个低层约束函数

TreeMaker 的 NLCO 约定是：

- 等式约束：`f(u) = 0`
- 不等式约束：`f(u) <= 0`
- 变量上下界：由 `SetBounds(bl, bu)` 单独传给求解器

26 个低层约束函数如下。

| 编号 | 约束函数 | 含义 |
|---:|---|---|
| 1 | `OneVarFn` | 单变量线性约束，例如固定坐标或固定 strain |
| 2 | `TwoVarFn` | 双变量线性约束，例如两个 strain 相等 |
| 3 | `PathFn1` | scale 可变、两端节点都可动的路径距离约束 |
| 4 | `PathFn2` | scale 可变、一端节点固定的路径距离约束 |
| 5 | `PathAngleFn1` | 两端节点都可动时，路径角度固定 |
| 6 | `PathAngleFn2` | 一端节点固定时，路径角度固定 |
| 7 | `StrainPathFn1` | 共同 strain、两端节点都可动的路径距离约束 |
| 8 | `StrainPathFn2` | 共同 strain、一端节点固定的路径距离约束 |
| 9 | `StrainPathFn3` | 共同 strain、两端节点都固定的路径距离约束 |
| 10 | `StickToEdgeFn` | 节点位于纸张任意边界上 |
| 11 | `StickToLineFn` | 节点位于给定直线上，常用于对称轴 |
| 12 | `PairFn1A` | 两个可动节点关于直线镜像对称的第一个线性等式 |
| 13 | `PairFn1B` | 两个可动节点关于直线镜像对称的第二个线性等式 |
| 14 | `PairFn2A` | 一个可动节点与一个固定节点镜像对称的第一个线性等式 |
| 15 | `PairFn2B` | 一个可动节点与一个固定节点镜像对称的第二个线性等式 |
| 16 | `CollinearFn1` | 三个可动节点共线 |
| 17 | `CollinearFn2` | 两个可动节点和一个固定节点共线 |
| 18 | `CollinearFn3` | 一个可动节点和两个固定节点共线 |
| 19 | `BoundaryFn` | 点位于一条参考直线指定一侧；源码中定义但未发现常规条件调用 |
| 20 | `QuantizeAngleFn1` | 两端节点可动时，路径角度量化为指定角度步长 |
| 21 | `QuantizeAngleFn2` | 一端节点固定时，路径角度量化为指定角度步长 |
| 22 | `LocalizeFn` | 节点限制在给定圆邻域内；源码中定义但未发现常规条件调用 |
| 23 | `MultiStrainPathFn1` | 多个独立 strain、两端节点都可动的路径距离约束 |
| 24 | `MultiStrainPathFn2` | 多个独立 strain、一端节点固定的路径距离约束 |
| 25 | `MultiStrainPathFn3` | 多个独立 strain、两端节点都固定的路径距离约束 |
| 26 | `CornerFn` | 节点坐标位于纸张角点坐标，即 `x in {0,w}` 或 `y in {0,h}` |

其中 `PairFn1A/B`、`PairFn2A/B`、`CornerFn` 通常成对加入，因为一个几何条件需要多个标量方程完全表达。

## 用户可见的 13 类条件

源码把高层 `tmCondition` 和低层数学 constraint 明确区分：`tmCondition` 是施加在树和树部件上的条件，低层 constraint 则是优化器操作的标量函数。

13 个具体 `tmCondition` 类如下。

| 条件类 | 用户语义 | 主要生成的低层约束 |
|---|---|---|
| `tmConditionNodeFixed` | 节点坐标固定 | `OneVarFn` |
| `tmConditionNodeCombo` | 节点组合约束：到对称线、到纸边、到角点等 | `StickToLineFn`、`StickToEdgeFn`、`CornerFn` |
| `tmConditionNodeSymmetric` | 单节点在对称轴上 | `StickToLineFn` |
| `tmConditionNodeOnEdge` | 节点在纸边上 | `StickToEdgeFn` |
| `tmConditionNodeOnCorner` | 节点在纸角上 | `CornerFn` 两个 |
| `tmConditionNodesPaired` | 两节点关于对称线成对 | `PairFn1A/B` 或 `PairFn2A/B` |
| `tmConditionNodesCollinear` | 三节点共线 | `CollinearFn1/2/3` |
| `tmConditionPathActive` | 路径强制 active，即距离约束取等号 | `PathFn1`、`StrainPathFn*`、`MultiStrainPathFn*` |
| `tmConditionPathAngleFixed` | 路径 active 且角度固定 | `PathAngleFn1/2`，并继承 active path 约束 |
| `tmConditionPathAngleQuant` | 路径 active 且角度量化 | `QuantizeAngleFn1/2`，并继承 active path 约束 |
| `tmConditionPathCombo` | 路径组合条件：active、角度固定、角度量化 | 上述路径条件的组合 |
| `tmConditionEdgeLengthFixed` | 边长固定，即 strain 为 0 | `OneVarFn` |
| `tmConditionEdgesSameStrain` | 两条边 strain 相同 | `TwoVarFn` |

## 三类优化器的具体问题

### 1. Scale Optimization

源码入口：`tmModel/tmOptimizers/tmScaleOptimizer.cpp`

决策变量：

```text
u[0]       = scale m
u[1+2i]    = leaf node i 的 x 坐标
u[2+2i]    = leaf node i 的 y 坐标
```

目标函数：

```text
minimize -u[0]
```

也就是最大化 scale。

约束：

```text
0 <= m <= 2
0 <= x_i <= w
0 <= y_i <= h
m >= 0.1 * current_scale
m * l_ij - ||v_i - v_j|| <= 0, for every leaf path i,j
plus user conditions
```

其中路径约束在源码中由 `PathFn1` 实现：

```text
f(u) = m * l_ij - sqrt((x_i - x_j)^2 + (y_i - y_j)^2) <= 0
```

这正是 TreeMaker 帮助文档和论文中描述的“纸面两点距离至少等于树路径缩放长度”。

### 2. Edge Optimization

源码入口：`tmModel/tmOptimizers/tmEdgeOptimizer.cpp`

用途：在整体 scale 固定的情况下，对选中可拉伸边施加同一个 strain `sigma`，并最大化它。用户界面中对应 Scale Selection。

决策变量：

```text
u[0]       = selected stretchy edges 的共同 strain sigma
u[1+2i]    = movable node i 的 x 坐标
u[2+2i]    = movable node i 的 y 坐标
```

目标函数：

```text
minimize -sigma
```

约束：

```text
-0.999 <= sigma <= 10
0 <= x_i <= w
0 <= y_i <= h
l_fix + sigma * l_var - ||v_i - v_j|| <= 0
plus user conditions
```

源码中按路径两端是否可动选择 `StrainPathFn1/2/3`。

### 3. Strain Optimization

源码入口：`tmModel/tmOptimizers/tmStrainOptimizer.cpp`

用途：在整体 scale 固定时，为多个可拉伸边分配各自 strain，使额外条件能够满足，同时尽量少改变原始边长。常用于对称、角度等条件导致原始树不可行时。

决策变量：

```text
u[2i]          = movable node i 的 x 坐标
u[2i+1]        = movable node i 的 y 坐标
u[edgeOffset+k] = stretchy edge k 的 strain sigma_k
```

目标函数：

```text
minimize sum_k stiffness_k * sigma_k^2
```

源码注释称为 weighted mean square edge strain；实现中是未除以数量的加权平方和，不影响最优点。

约束：

```text
0 <= x_i <= w
0 <= y_i <= h
-0.999 <= sigma_k <= 2
l_fix + sum_k sigma_k * l_k - ||v_i - v_j|| <= 0
plus user conditions
```

源码中按路径两端是否可动选择 `MultiStrainPathFn1/2/3`。

## 最终优化问题

如果只问 TreeMaker 折纸设计的核心最终问题，即 TreeMaker 首先要解决的“树图到高效纸面布局”问题，它就是 scale optimization：

```text
Given:
  tree graph T
  leaf node set L
  paper rectangle P = [0,w] x [0,h]
  tree path length l_ij for every i,j in L

Find:
  scale m
  paper coordinates v_i = (x_i, y_i) for every leaf node i

Maximize:
  m

Subject to:
  0 <= x_i <= w
  0 <= y_i <= h
  ||v_i - v_j|| >= m * l_ij, for every pair i,j in L
  plus optional user conditions:
    fixed node coordinates
    node on edge/corner/line
    mirror symmetry
    node collinearity
    active path equality
    fixed or quantized path angle
    fixed edge length
    equal edge strain
```

TreeMaker 的 C++ 实现把它转成标准最小化形式：

```text
minimize:
  -m

subject to:
  m * l_ij - ||v_i - v_j|| <= 0
  bounds and user-generated equalities/inequalities
```

这是一个非线性约束优化问题。非线性主要来自欧氏距离、共线、纸边/角点多项式、角度量化、以及 strain 路径长度等约束。

## Active Constraints 到 Crease Pattern

优化输出并不直接等于完整折痕图。Scale optimization 的直接输出主要是：

```text
leaf node positions p_i
scale s
active paths
```

当某个叶路径满足：

```text
||p_i - p_j|| = s * d_T(i,j)
```

它就是 active constraint；在 TreeMaker 的折纸解释中，这条 leaf path 也叫 active path。几何上，它表示两个叶节点之间的纸面距离刚好被树路径长度“用满”：对应的 flap 圆和中间 river 处在相切或紧接状态。

这些 active paths 的重要性不只是数值优化意义上的“约束取等号”。它们会成为后续 crease pattern 构造中的轴向骨架，即 axial paths / axial creases。TreeMaker 后续还要根据这些骨架：

- 构造 active polygons；
- 在多边形区域中填入 crease molecules；
- 生成 axial、ridge、hinge、gusset、pseudohinge 等结构性折痕；
- 计算 facet ordering；
- 给出 mountain / valley / unfolded 折痕赋值。

所以，圆填充优化解决的是“纸张资源和关键顶点放在哪里”；完整折痕图还依赖后续的几何构造、层序计算和局部平坦可折条件。Kawasaki 定理和 Maekawa 定理属于这些局部可折约束/检验的一部分，但它们不是 `tmScaleOptimizer` 中直接求解的 NLCO 约束。

## 求解器

抽象接口在 `tmModel/tmNLCO/tmNLCO.h`：

- `SetObjective()`
- `AddLinearEquality()`
- `AddNonlinearEquality()`
- `AddLinearInequality()`
- `AddNonlinearInequality()`
- `SetBounds()`
- `Minimize()`

当前源码默认启用：

```text
#define tmUSE_ALM
```

即 `tmNLCO_alm`，Augmented Lagrangian Multiplier 增广拉格朗日方法。源码也保留 CFSQP、RFSQP、wnlib 等适配层，但默认没有启用。

这里可以补充一个历史时间线：

- 早期 TreeMaker 使用 Lang 自己实现的 ALM，速度较慢，但能处理基本非线性约束优化。
- TreeMaker 4.0 使用 André Tits 等人的 FSQP/CFSQP，速度大幅提升，也更强调可行迭代，对 circle/river packing 的几何解释更稳定。
- TreeMaker 5 又回到自写 ALM，主要是因为硬件速度提升后 ALM 已经足够快，同时自写代码便于开源发布。

因此，TreeMaker 5 当前源码默认 ALM，并不表示 ALM 在理论上总优于 FSQP；这是速度、许可证、可发布性和维护成本共同作用的工程选择。

## 复杂性补充

圆填充笔记中提到的复杂性也能解释为什么 TreeMaker 通常只承诺局部最优，而不是全局最优。

Demaine、Fekete、Lang 在 *Circle Packing for Origami Design Is Hard* 中证明，三角形、矩形和正方形纸张上的 circle/river origami design 是 NP-hard。直观原因是：这个问题不仅要放置几何对象，还要同时满足尺度比例、非重叠约束和树拓扑相邻关系。

TreeMaker 的实际流程可分成两步：

1. 优化步骤：求叶节点顶点位置和最大 scale。
2. 构造步骤：根据 active paths / active polygons 构造 crease pattern，并计算山谷赋值和层序。

困难主要集中在第一步的 packing / nonlinear optimization。第二步在 tree method 给出的额外结构下可以用专门的几何算法处理。由于第一步是非凸问题，不同初始节点布局可能得到不同的局部最优；这也解释了 TreeMaker 文档中建议用户拖动节点、改变初始构型后重新优化的原因。

## 资料依据

源码依据：

- `tmModel/tmOptimizers/tmScaleOptimizer.cpp`
- `tmModel/tmOptimizers/tmEdgeOptimizer.cpp`
- `tmModel/tmOptimizers/tmStrainOptimizer.cpp`
- `tmModel/tmOptimizers/tmConstraintFns.h`
- `tmModel/tmOptimizers/tmConstraintFns.cpp`
- `tmModel/tmTreeClasses/tmCondition.cpp`
- `tmModel/tmTreeClasses/tmCondition*.cpp`
- `tmModel/tmNLCO/tmNLCO.h`
- `tmModel/tmNLCO/README.txt`
- `help/overview.htm`

外部资料：

- Robert J. Lang, TreeMaker official page: https://langorigami.com/article/treemaker
- Robert J. Lang, TreeMaker 4 documentation / theory chapter: https://langorigami.com/wp-content/uploads/2015/09/TreeMkr40.pdf
- Robert J. Lang, Origami Design Secrets algorithms chapter: https://langorigami.com/wp-content/uploads/2015/09/ODS1e_Algorithms.pdf
- Erik D. Demaine, Martin L. Demaine, Robert J. Lang, "Facet Ordering and Crease Assignment in Uniaxial Bases": https://erikdemaine.org/papers/TreeMaker_OSME2006/paper.pdf
- Erik D. Demaine, Sandor P. Fekete, Robert J. Lang, "Circle Packing for Origami Design Is Hard": https://ar5iv.labs.arxiv.org/html/1008.1224
- 本地笔记：`2022-05-03-圆填充与折纸.md`

