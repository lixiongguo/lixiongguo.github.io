---
layout: post
title: "四边形网格化 — 变形 Frame Field"
category: Parameterization
categories: ["Parameterization", "Parameterization-QuadRemeshing"]
mathjax: true
---

> **论文**：Daniele Panozzo, Enrico Puppo, Marco Tarini, Olga Sorkine-Hornung. [*Frame Fields: Anisotropic and Non-Orthogonal Cross Fields*](https://doi.org/10.1145/2601097.2601179). ACM Transactions on Graphics (SIGGRAPH), 33(4), 2014.

## 概述

**Frame field** 是 **cross field** 的推广：在每个切平面上给出一组四个方向 $\langle \mathbf{v}, \mathbf{w}, -\mathbf{v}, -\mathbf{w}\rangle$，但 $\mathbf{v}$ 与 $\mathbf{w}$ **不必正交、不必等长**，可编码各向异性、缩放与剪切。它表示切丛上光滑变化的线性变换。

本文核心思路与主流 `cross field → seamless parameterization → quad mesh` 不同：

> 不在原曲面上硬把 frame field 投影成 cross field，而是**变形曲面本身**，使 frame field 在变形域中成为 cross field，再做规则四边形网格化，最后映回原曲面。

| 对比项 | 主流 cross field 路线 | 变形 Frame Field |
| :--- | :--- | :--- |
| 几何 | 原曲面固定 | 允许辅助变形 |
| 方向场 | 直接设计 cross | 设计更一般的 frame |
| 拓扑 | 显式处理奇异点、matching | 变形后借用标准 MIQ |
| 输出 | 无缝参数化 / 规则 quad | 服从设计场的各向异性 quad |

---

## 1. 方法总览（Figure 1）

![image-20250923104719017](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250923104719017.png)

论文 Figure 1 的五步流程（从左到右）：

| 阶段 | 内容 | 性质 |
| :--- | :--- | :--- |
| **① 稀疏约束** | 用户在输入曲面上放置绿色约束块 | 指定局部方向、尺度、剪切 |
| **② 稠密 frame field** | 由约束插值得到全场"毛发"状 frame | **非均匀、各向异性、非正交** |
| **③ 曲面变形** | 将曲面形变，使 frame 在变形域中变为 cross | frame → cross 的"扭曲"被吸收进几何 |
| **④ 均匀四边形化** | 在变形曲面上生成黄色规则 quad 网格 | **均匀、各向同性、正交** |
| **⑤ 逆变形** | 将 quad 映回原曲面（热力图表示单元面积） | **非均匀、各向异性、非正交**，服从原 frame |

论文原话：*Given a sparse set of constraints … we interpolate a dense, non-uniform, anisotropic and non-orthogonal frame field. We then deform the surface to warp this frame field into a cross field … Finally, we deform the resulting quad mesh back onto the original surface.*

最终网格**不追求最规则**，而追求**最服从用户给定的方向与尺寸设计**。

---

## 2. 为何从 frame field 出发

**Cross field** 与四边形局部结构天然对应（两组正交、四重对称方向），但设计意图往往是更一般的方向框架：

- 两方向不必正交；
- 长度可不等（各向异性）；
- 可含明显剪切（skew）。

这类结构用 **frame field** 表达更自然，却不能直接用于标准 quad meshing。

关键洞见（Lemma 3.1）：任意 frame 可唯一分解为 **cross + SPD 线性映射**——不是丢掉 frame，而是把它解释为"某个 cross 经局部变形后的像"。于是问题变为：**找一个几何变形，使该 frame 在新几何里成为 cross field**。

---

## 3. Frame 与 Cross 的对应关系（Lemma 3.1）

**Lemma 3.1.** 设 $f_p = \langle \mathbf{v}, \mathbf{w}, -\mathbf{v}, -\mathbf{w}\rangle$ 为切平面 $\mathbf{T}_p\mathcal{S}$ 上的 frame。则存在唯一的 cross

$$
\mathbf{x} = \langle \mathbf{u}, \mathbf{u}^\perp, -\mathbf{u}, -\mathbf{u}^\perp\rangle
$$

与唯一的 **SPD** 线性映射 $\mathbf{W}$，使得

$$
f_p = \mathbf{W}\mathbf{x} = \langle \mathbf{W}\mathbf{u}, \mathbf{W}\mathbf{u}^\perp, -\mathbf{W}\mathbf{u}, -\mathbf{W}\mathbf{u}^\perp\rangle
$$

**几何含义**：

| 对象 | 含义 |
| :--- | :--- |
| $\mathbf{x}$ | 理想的正交、四重对称方向结构 |
| $\mathbf{W}$ | 局部拉伸、缩放、剪切 |
| $f_p = \mathbf{W}\mathbf{x}$ | frame 是 cross 经 $\mathbf{W}$ 作用后的结果 |

**Definition 3.2**：frame field $\mathcal{F}$ 称为连续/光滑，若其分解得到的 cross 场 $\mathcal{X}$ 与 SPD 张量场 $\mathbf{W}$ **分别**连续/光滑。论文通过分别优化光滑 cross 与光滑 $\mathbf{W}$ 来生成光滑 frame field。

### 3.1 离散表示

在三角网格 $M$ 上，frame field **逐三角形常值**（piecewise constant）。三角形 $t$ 上的 frame $f_t$ 用 Lemma 3.1 的两部分表示：

- **Cross 部分** $\mathbf{x}_t$：相对三角形局部正交基 $\mathbf{B}_t$ 的一个角度（模 $\pi/2$ 等价类），同 [Ray et al. 2008]；
- **SPD 部分** $\mathbf{W}_t$：相对同一基 $\mathbf{B}_t$ 的 $2\times 2$ SPD 矩阵。

每个三角形基 $\mathbf{B}_t$ 不同，且除特殊情形外无法全局选一致光滑基（hairy ball theorem）——比较相邻三角形上的 frame 必须先**换到同一参考系**。

---

## 4. 平滑 cross field 与换基（Figure 3 配图）

<img src="https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20260701213147667.png" alt="image-20260701213147667" style="zoom:50%;" />

离散 **cross field** 称为 smooth，若它最小化 [Ray et al. 2008] 的平滑能量（其 Eq. 16），即相邻 cross 在统一参考系下差异小。

设共享边的两三角形 $t_1, t_2$，局部基为 $\mathbf{B}_1, \mathbf{B}_2$，对应 frame $f_1=\{\mathbf{x}_1, \mathbf{W}_1\}$、$f_2=\{\mathbf{x}_2, \mathbf{W}_2\}$。

**Cross 部分的换基**为旋转

$$
\mathbf{R}_{12} = \mathbf{B}_1 \mathbf{B}_2^{-1}
$$

（图中大弧线箭头）。**SPD 部分**用同一 $\mathbf{R}_{12}$ 传输：若 $\mathbf{W}_2 = \mathbf{U}_2 \mathbf{P}_2 \mathbf{U}_2^T$（极分解），则在 $\mathbf{B}_1$ 参考系下

$$
\mathbf{W}_2^{\text{(在 }\mathbf{B}_1\text{ 下)}} = \mathbf{R}_{12}\, \mathbf{W}_2\, \mathbf{R}_{12}^T
$$

之后才能在同一参考系下比较 $\mathbf{x}_1$ 与 $\mathbf{x}_2$、$\mathbf{W}_1$ 与传输后的 $\mathbf{W}_2$，计算平滑能量。这与 [向量场介绍](../../1.Parameterization/4.全局参数化与四边形网格化/2017-08-01-向量场介绍.md) 中 quarter-turn matching 的精神一致：先消除基底差异，再比较方向。

---

## 5. Frame field 插值（稀疏约束 → 稠密场）

论文 Section 5，对应流程图阶段 ②。给定稀疏约束 $\hat{f}_1,\ldots,\hat{f}_k$（在三角形 $t_1,\ldots,t_k$ 上）：

1. 对每个约束做 Lemma 3.1 分解，得 cross 约束 $\hat{\mathbf{x}}_j$ 与 SPD 约束 $\hat{\mathbf{W}}_j$；
2. **Cross 部分**：用 [Bommes et al. 2009]（MIQ）求满足约束的平滑离散 cross field $\mathcal{X}$；
3. **$\mathbf{W}$ 部分**：系数不能直接在各自局部基下做普通 Laplacian 插值（基不一致）。构造面基 **离散 Laplacian $\mathbf{L}^B$**（编码相邻面基之间的旋转），求解

$$
\mathbf{L}^B (\mathbf{w}_1^T, \ldots, \mathbf{w}_n^T)^T = 0, \qquad \mathbf{w}_j = \hat{\mathbf{w}}_j,\; j \in \mathcal{C}
\tag{4}
$$

其中 $\mathbf{w}_i \in \mathbb{R}^3$ 打包对称矩阵 $\mathbf{W}_i$ 的三个独立系数，$\mathcal{C}$ 为约束面集。**Lemma 5.1**：若所有约束 $\hat{\mathbf{W}}_j$ 为 SPD，则插值结果 $\mathbf{W}_i$ 仍为 SPD。

Frame field 诱导的度量 $g_{\mathcal{F}} = \mathbf{W}^{-T}\mathbf{W}^{-1}$。变形的目标是让该度量在变形域中接近欧氏度量，等价于把 frame **扭成** cross。

---

## 6. 几何变形能量（Figure 5 / 式 (5)）

三角形 $t$ 上，$\mathbf{W}_t$ 把 cross $\mathbf{x}_t$ 变为 frame $f_t$，故**理想局部变形**为 $\mathbf{W}_t^{-1}$：把当前 frame "拉直"为 cross。闭网格上无法每个三角形精确达到理想形变，故最小化 ARAP 型能量：

$$
\mathcal{E}(\mathbf{p}') = \sum_{t \in \mathcal{M}} \min_{\mathbf{Q}_t \in SO(3)} A_t \left\lVert  \mathbf{J}_t(\mathbf{p}') - \mathbf{Q}_t \tilde{\mathbf{W}}_t^{-1} \right\rVert _F^2
\tag{5}
$$

| 符号 | 含义 |
| :--- | :--- |
| $\mathbf{p}'$ | 变形后顶点位置（优化变量） |
| $\mathbf{J}_t(\mathbf{p}')$ | 三角形 $t$ 的变形 Jacobian（$3\times 3$，嵌入 $\mathbb{R}^3$） |
| $\tilde{\mathbf{W}}_t$ | $\mathbf{W}_t$ 在全局 3D 坐标系下的 $3\times 3$ 版本 |
| $\mathbf{Q}_t \in SO(3)$ | 局部最优旋转，吸收刚体转动自由度 |
| $A_t$ | 三角形面积权重 |

思想对比：

- **传统**：固定几何，优化方向场；
- **本文**：固定 frame 设计意图，**优化几何**，使 $\mathbf{J}_t \approx \mathbf{Q}_t \tilde{\mathbf{W}}_t^{-1}$。

论文在 $\mathbb{R}^3$ 中做嵌入（而非 Nash 定理所需的高维嵌入），实践中足够将各向异性度量近似为欧氏度量。

---



## 7. 数值求解：BCD 交替优化

式 (5) 与 [Sorkine & Alexa 2007; Liu et al. 2008] 的 ARAP 能量同型，用 **Block Coordinate Descent** 交替：

1. **固定 $\mathbf{Q}$，优化 $\mathbf{p}'$** → 解稀疏线性系统；
2. **固定 $\mathbf{p}'$，优化 $\mathbf{Q}$** → 各三角形局部 Procrustes（SVD）。

固定 $\mathbf{Q}$ 时，能量对 $\mathbf{p}'$ 的梯度为（式 (6)(7)）：

$$
\nabla \mathcal{E}(\mathbf{p}') = -4(\mathbf{L}\mathbf{p}' - \mathbf{b})
$$

$$
\mathbf{b}_i = \sum_{j \in \mathcal{N}(i)} \frac{1}{2}\Bigl(
\cot\theta_{ij}\, \mathbf{Q}_{t(i,j)} \tilde{\mathbf{W}}_{t(i,j)}^{-1}
+ \cot\theta_{ji}\, \mathbf{Q}_{t(j,i)} \tilde{\mathbf{W}}_{t(j,i)}^{-1}
\Bigr)(p_j - p_i)
$$

$\mathbf{L}$ 为标准 cotan Laplacian；$t(i,j)$ 为半边 $(p_j-p_i)$ 左侧的三角形；$\theta_{ij}$ 为该三角形中与此半边相对的角。令 $\nabla\mathcal{E}=0$ 即 $\mathbf{L}\mathbf{p}'=\mathbf{b}$——与 [AQP](AQP.md) 中 QP 步的 Laplacian 结构同源。

**初始化**：$\mathbf{p}'$ 取原网格顶点；$\mathbf{Q}$ 取接近单位阵的小随机旋转（帮助零曲率区域避免坏局部极小）。变形中自交（如 Figure 1 耳朵）可接受，无需特殊处理。

---

## 8. Frame-field 对齐四边形化（Section 7）

变形后 frame field **未必精确**为 cross field（问题过约束）。后续步骤：

1. **提取 cross**：对每个变形三角形 $t'$，用变形 Jacobian $\mathbf{J}_t$ 得变形后 frame $f_{t'} = \mathbf{J}_t f_t$，再极分解取最近 cross；
2. **平滑 cross field**：在变形网格上用 MIQ [Bommes et al. 2009] 平滑并参数化；若 frame 来自约束插值，**约束在变形域上保持**；
3. **均匀 remesh**：用 [Ebke et al. 2013] 在变形曲面生成均匀 quad 网格；
4. **逆变形**：连通性不变，用重心坐标将 quad 顶点映回原曲面 → 得到服从**原 frame field** 的各向异性网格。

**奇异点**：变形后 MIQ 可能出现新奇异点，对应原场上**密度过渡**所需拓扑（Figure 5 Cigar 例子：两端尺度比 10:1）。

与 **Anisotropic MIQ** [Bommes et al. 2009] 对比：后者在 cross field 拓扑固定后用梯度缩放单元，**不能**为尺度突变引入新奇异点；本文通过先变形几何，把自适应细分问题转化为变形域上的均匀细分问题。

---

## 9. 与主流路线的对比

### 9.1 相同点

- 四边形网格化离不开方向场；
- 希望边沿局部主方向排列。

### 9.2 核心区别

| | 变形 Frame Field | MIQ / QuadCover 等 |
| :--- | :--- | :--- |
| 策略 | **改几何**使问题变简单 | **在原几何上**建模拓扑与参数化 |
| 中间对象 | 变形域 | 参数域 / branch cover |
| 输出 | 各向异性 quad mesh | 无缝 UV / 规则 quad layout |

### 9.3 适用场景

**更适合本文**：

- 用户有明确方向/尺度/剪切设计；
- 允许辅助几何变形；
- 关注网格是否跟随设计场，而非原曲面无缝参数化。

**更适合 MIQ 路线**：

- 需系统控制奇异点与 matching；
- 几何不能动；
- 需要 seamless parameterization。





## 参考文献

- Panozzo D., Puppo E., Tarini M., Sorkine-Hornung O. *Frame Fields: Anisotropic and Non-Orthogonal Cross Fields*. SIGGRAPH 2014.
- Bommes M., et al. *Mixed-integer quadrangulation*. SIGGRAPH 2009.（MIQ）
- Ray N., et al. *Periodic global parameterization*. SIGGRAPH 2008.（cross field 平滑能量）
- Ebke M., et al. *QEx*. SIGGRAPH 2013.（均匀 quad remesh）
- Sorkine O., Alexa M. *As-rigid-as-possible surface modeling*. SGP 2007.
- Jiang Y., et al. *Frame field generation through metric customization*. SIGGRAPH 2015.
