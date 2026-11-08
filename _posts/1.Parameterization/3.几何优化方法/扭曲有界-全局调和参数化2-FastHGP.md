<!-- ---
layout: post
title: "快速局部单射调和映射 — FastHGP 子空间方法"
categories: ["Parameterization", "Parameterization-GeometricOptimization"]
mathjax: true
--- -->

> **论文**：Eden Fedida Hefetz, Edward Chien, Ofir Weber. *A Subspace Method for Fast Locally Injective Harmonic Mapping*. Computer Graphics Forum, 38(2), 2019.
> **前置**：Harmonic Global Parametrization (HGP) [BCW17]

## 1. 动机：HGP 的瓶颈与 FastHGP 的思路

HGP（Harmonic Global Parameterization）能在复杂拓扑上生成无缝、低扭曲的全局参数化，鲁棒性极好。但其代价也很高——内部依赖 MOSEK 求解二阶锥规划（SOCP），一次完整流程约需数十次大规模线性系统求解，不适合交互式应用。

FastHGP 的关键洞察：**HGP 中绝大部分自由度是冗余的**。调和解空间的维度仅与边界顶点数和锥点数成正比（与网格密度无关），且局部单射性和扭曲的信息主要集中在边界和锥点邻域。因此可以将优化从全顶点空间压缩到几十到几百维的子空间中，总成本约等于 1–2 次线性求解。

---

## 2. 两个关键观察（为什么子空间方法可行）

**Observation 1 — 局部单射性仅由边界/锥点邻域决定**

来自 HGP 的 Theorem 6.1：对 HGP 调和解，若边界和锥点邻域的所有三角形都是局部单射的，则整个映射自动局部单射。换句话说——**内部三角形的单射性"被管住了"**，我们无需逐面检查整个网格。

这个结论的直觉：调和映射在内部是"尽量平滑"的——如果边界上没有任何地方折叠，内部在调和内插下也不会折叠。唯一可能出问题的是锥点附近的局部极端扭曲，但那些区域的三角形数量也很有限。

**Observation 2 — 扭曲在边界上达到极值**

对局部单射调和映射，共形扭曲的上界总出现在边界三角形上。推广到带锥点多连通域，结论类似。

这意味着一件事：**最小化边界/锥点邻域三角形的扭曲，等价于最小化全局扭曲**。优化范围从 $O(|V|)$ 降到 $O(|\partial V| + |C|)$。

> 两个 Observation 结合，将变量空间和目标空间同时压缩到了同一低维区域——这是子空间方法可行的根基。

---

## 3. HGP 线性系统回顾

HGP 将曲面切开 seam 后映射到复平面，每顶点 $v_i$ 对应一个复变量 $z_i = f(v_i) \in \mathbb{C}$。齐次系统 $A_{\text{hgp}} z = 0$ 包含三类约束：

**旋转约束**（seam 边 $e_{ij} \in E_s$，即切割路径上的边）：
$$
z_j^a - z_i^a = e^{i\pi r_{ij}/2}\,(z_j^b - z_i^b)
$$

直观：切割后 seam 两侧的 UV 坐标可以通过一个 $k \cdot 90^\circ$ 旋转对齐。$r_{ij} \in \{0,1,2,3\}$ 来自 cross-field 的跨边 matching。

**内部调和**（$v_i$ 为内部顶点）：
$$
\sum_{v_j \in \mathcal{N}(v_i)} w_{ij}(z_i - z_j) = 0
$$

标准离散调和方程，$w_{ij}$ 取 cotangent 权重。正权重（如 intrinsic Delaunay 重剖分）可加强单射保证，但一般负 cot 权引起的少量局部翻转可用启发式修复。

**旋转调和**（seam 切割后产生多副本的顶点）：对 degree-$d$ 的 seam 顶点有 $d$ 个副本，需满足额外的旋转一致性条件（HGP 原文式 (3)，构造较繁琐）。

---

## 4. 调和解空间的维数

对亏格 0 曲面，$A_{\text{hgp}}$ 行满秩、列数多于行数，零空间非平凡。增广为方阵：

$$
A_{\text{aug}} = \begin{pmatrix} A_{\text{hgp}} \\ A_{\text{int}} \end{pmatrix}
$$

其中 $A_{\text{int}}$ 是插值条件矩阵，通过固定部分顶点的 UV 位置使增广矩阵满秩可逆。插值规则：

| 曲面类型 | 插值条件 |
|:---|:---|
| 球面（0 个边界） | 除 1 个锥点外，其余 $|C|-1$ 个锥点各固定一个副本位置 |
| 圆盘 / 多连通圆盘 | 每个 $\partial V$ 顶点 + 每个锥点各固定一个副本；若 $n>1$ 额外固定 $n-1$ 个 seam 边界顶点的第二副本 |

**定理 8**：$\dim N(A_{\text{hgp}}) = 2\,(|\partial V| + |C| + n - 1)$ 实维。

**直觉**：每个"自由"边界位置或锥点位置贡献一个复自由度。所有调和映射都可表示为这些插值向量 $c_{\text{int}}$ 的线性组合。这就是子空间——维度与网格密度完全脱钩，百万顶点网格可能只需几十个自由度。

---

## 5. KKT 系统：避免显式组装旋转调和

直接编码 HGP 式 (3) 的旋转调和行很繁琐。论文用一个巧妙的等价 KKT 公式化来绕过：

$$
\min_z \lVert Dz\rVert ^2 \quad \text{s.t.} \quad A_{\text{lin}} z = c_{\text{lin}}
$$

其中 $D$ 是面积加权梯度算子，$2D^T D$ 是标准 cotangent Laplacian；$A_{\text{lin}}$ 仅包含简单约束（旋转约束和插值条件）。对应的 KKT 条件：

$$
\begin{pmatrix} 2D^T D & A_{\text{lin}}^T \\ A_{\text{lin}} & 0 \end{pmatrix} \begin{pmatrix} z \\ \lambda \end{pmatrix} = \begin{pmatrix} 0 \\ c_{\text{lin}} \end{pmatrix}
$$

记 $K$ 为这拼块矩阵。**定理 6** 保证 $K$ 可逆，且 $K$ 的解 $z$ 自动满足完整 HGP 系统（含旋转调和）。因此：

- 通过求解 $K \cdot [z; \lambda] = [0; c_{\text{int}}]$ 得到调和解；
- $K$ 的可逆性直接证明了 $A_{\text{hgp}}$ 满秩；
- 实现时只需遍历三角形组装 $2D^T D$，无需手写旋转调和式 (3)。

---

## 6. 约化子空间构造

### 6.1 选择性求逆

完整计算 $K^{-1}$ 的代价与一次 LU 分解相同（大约是求解的 2–3 倍）。但 FastHGP 不需要所有逆矩阵元素——只需 $V_{cb}$（锥/边界相关顶点）对应的行。利用 **selected inversion** 技术，仅提取 $K^{-1}$ 在这些行的非零——代价约等价于 1 次 LU 分解。

收集 $V_{cb}$ 行的逆元素，构成**约化调和基矩阵** $H$：

$$
H \in \mathbb{C}^{|V_{cb}| \times (|\partial V| + |C| + n - 1)}
$$

$H$ 的每一列是一个基底映射，它们的线性组合张成整个 HGP 调和解空间。

### 6.2 虚拟顶点（Virtual Vertices）

对稠密边界的模型，$|\partial V|$ 本身也可能很大（如 1-2 千）。引入虚拟顶点降维：每隔 $k$ 个边界顶点取一个 **meta vertex**，其余顶点约束为相邻两个 meta 顶点的弧长加权凸组合：

$$
v_{\text{slave}} = (1-t)\,v_a + t\,v_b, \quad t = \frac{\text{arc}(v_a, v)}{\text{arc}(v_a, v_b)}
$$

这相当于把边界"降采样"到虚拟顶点的凸包约束中，子空间维数进一步降低。

---

## 7. ATP：在低维空间中求可行局部单射映射

子空间构造完成后，需要在系数 $c_{\text{int}}$（实现里常记为 meta 顶点与锥点上的复坐标 $c$）上，找一个使边界/锥点邻域三角形**局部单射**的初值，再交给 §8 的 Projected Newton 去压扭曲。**ATP**（**Alternating Tangential Projection**，交替切向投影）就是这一步：它不是一种新的展 UV 能量，也不是 HGP 里的 SOCP 求解器，而是 FastHGP 在 **Newton 之前**、专门为**带锥点**模型设计的**可行初值搜索**。

### 7.0 ATP 在整条管线中的位置

桌面 FastHGP 的主流程可概括为：

1. 组装 KKT 矩阵 $K$，用选择性求逆得到约化调和基，并构造约化 Jacobian $J_{fz}, J_{f\bar{z}}$（§5–§6）；
2. **有锥点** → 运行 ATP，得到子空间系数初值 $c$，并检查是否局部单射；
3. **无锥点、仅边界** → 跳过 ATP，用 Tutte 型嵌入（§7.3）；
4. 在 $T_{cb}$ 上对 $c$ 做 Projected Newton，最小化对称 Dirichlet（§8）；
5. 将 $c$ 回代为全网格 UV。

ATP 只负责第 2 步。若 ATP 失败（论文与实现中约一成左右情形），后续 Newton 往往无法可靠启动，需回退完整 HGP 的 SOCP。

### 7.1 局部凸化（Lipman frames）

以帧 $\zeta_i$（与 HGP 相同的 frame field，来自向量场或预计算 frames）定义每个锥/边界邻域三角形 $i$ 上的局部凸可行集 $B_i \subset \mathbb{C}^2$：

$$
\mathrm{Re}\!\left(\frac{f_z^i}{\zeta_i}\right) - |f_{\bar{z}}^i| \geq \sigma^2, \qquad
\mathrm{Re}\!\left(\frac{f_z^i}{\zeta_i}\right) \geq \frac{1}{k}|f_{\bar{z}}^i|
$$

其中 $f_z^i, f_{\bar{z}}^i$ 是面 $i$ 的 Wirtinger 导数，$\mathrm{Re}(f_z/\zeta)$ 控制沿 frame 方向的伸缩量，$|f_{\bar{z}}|$ 控制准共性（quasiconformality）程度。参数 $\sigma^2$（实现中常取 $\sigma^2 \approx 0.01$）防止退化压缩；$k$（常取 $0.9$）限制 $f_{\bar{z}}$ 相对 $f_z$ 的比例，与 Lipman 单射条件一致。

> **几何直觉**：$f_z$ 描述映射的保角伸缩，$f_{\bar{z}}$ 描述映射的「翻转」分量。在适当归一化下，$|f_{\bar{z}}| \leq \mathrm{Re}(f_z/\zeta)$ 对应 Jacobian 不反号（三角形不折叠）；再加 $\mathrm{Re}(f_z/\zeta) \geq \sigma^2$ 避免退化成零面积。

帧场 $\zeta_i$ 把 HGP 中面向全网格的 Lipman 约束**局部化、凸化**到每个三角形上，使 ATP 可以对每个面做独立的凸投影。

### 7.2 在什么空间里「交替」？

ATP 不在全网格 $2|V|$ 维 UV 上直接搜索，而在**两层变量**之间交替：

| 层次 | 变量 | 含义 |
|:---|:---|:---|
| **全局** | $c \in \mathbb{C}^{n}$ | 子空间里 meta 顶点 + 锥点的复系数；$n$ 为自由度个数 |
| **局部** | 每个 $T_{cb}$ 面上的 $(f_z^i, f_{\bar{z}}^i)$ | 由 $J_{fz} c,\; J_{f\bar{z}} c$ 线性得到，描述该面映射的复导数 |

二者通过约化 Jacobian 耦合：给定 $c$ 可算出所有面上的 $(f_z, f_{\bar{z}})$；反过来，指定各面上的目标导数后，可在加权最小二乘意义下反解最接近的调和映射 $c$。

**初始化**（完全共形、沿 frame 方向单位伸缩）：

$$
f_z^i = 1/\zeta_i, \qquad f_{\bar{z}}^i = 0
$$

**第一步（MAP）**：做一次**面积加权最小二乘**全局步（Maximum A Posteriori / 加权伪逆意义下的全局投影），把上述初值拉回到某个调和映射对应的 $(f_z, f_{\bar{z}})$ 上，并固定平移自由度（例如约束所有 cone 系数平均为零）。

**迭代（ATP 主体）**每轮包含：

1. **局部步（Local step）**  
   对每个三角形**独立**将当前的 $(f_z^i, f_{\bar{z}}^i)$ **正交投影**到凸集 $B_i$ 上。不同面之间在这一步互不相干，保证每面单独满足 Lipman 型不等式。

2. **全局步（Global step, ATP）**  
   记局部步结果为 $b_l$，当前全局映射导数为 $a_l$，残差 $n_i = a_l - b_l$。在**面积加权**的 $\lVert Jc - \cdot\rVert ^2$ 意义下，沿与 $n_i$ 相关的方向修正 $c$（实现上等价于用 $J$ 的加权伪逆作用在残差上，步长由 $n_i$ 与加权内积确定）。这一步把「各面各自可行」的局部目标**拼合**回**一个全局调和映射**。

3. **收敛检验**  
   当加权残差 $\lVert n_i\rVert _W < 10^{-4}$ 时停止；否则继续交替。最大迭代次数可达数百（实现中常设 500）。

> **为何叫「切向」投影？** 全局步不是在全空间中任意梯度下降，而是沿**残差在加权最小二乘解流形上的切向方向**修正 $c$，使 $Jc$ 逐步逼近局部可行点，同时保持「来自某个调和 $c$」的结构。

**成功判据**（实现与论文一致的精神）：收敛后检查每个面上是否 $|f_z| \geq |f_{\bar{z}}|$（无折叠的充分检验），且 $c$ 有限无 NaN。全部通过则 ATP 成功，进入 Newton；否则标记失败，Newton 可跳过或回退 HGP。

### 7.3 无锥多边界情形的简化

对 trivial holonomy 的多连通圆盘（**无锥点**），跳过 ATP，直接用 **Tutte 型嵌入**：主边界按弧长比例映射到圆，其余边界 meta 顶点在邻域凸包约束下解线性系统——经典方法 [GGT06]，**一次线性求解、无需迭代**。这与 ATP 的迭代投影形成对照：ATP 处理锥点带来的非平凡和乐与 Lipman 约束，无锥时初值问题已足够简单。

### 7.4 ATP 与 LSCM、HGP SOCP 的分工

| 方法 | 作用 | 典型场景 |
|:---|:---|:---|
| **HGP SOCP** | 全顶点、全局最优（在凸松弛意义下）的调和 + Lipman | 精度与鲁棒性优先，可接受 MOSEK 代价 |
| **ATP** | 低维、迭代的可行初值；严格调和 + 局部 Lipman 凸集 | FastHGP 桌面版，**有锥点** |
| **Tutte 嵌入** | 低维、非迭代的边界初值 | FastHGP 桌面版，**无锥点** |
| **LSCM** | 全网格共形线性初值，无子空间、无帧场凸约束 | 浏览器 WASM 简化版（`FastHGPSimple`）中**替代 ATP/Tutte**，仅作 warm start，再在对称 Dirichlet 上梯度下降 |

要点：**ATP 不是 LSCM 的升级版**。LSCM 在全体顶点上解一次线性最小二乘共形问题，不利用调和子空间，也不强制 Lipman 帧约束；WASM 选它是因为实现轻、无需 seam/锥点/KKT。桌面 FastHGP 则在**已降维的子空间**里，用 ATP **专门解决「有锥点时如何得到局部单射的调和初值」**——这是 LSCM 无法直接替代的。

本仓库中，ATP 的数值逻辑已迁入 `FastHGPNumerics`（对应 `reference_matlab` 中的 `ATPForInitialValue`、`localStep`、`globalStep_ATP` 等）；桌面 `FastHGP` 在 `mHasCones` 时调用，WASM 则不包含该路径。

---

## 8. Projected Newton：扭曲最小化

ATP 给出可行初值后，在 $T_{cb}$（锥/边界三角形）上最小化对称 Dirichlet 能量：

$$
E_{\text{iso}} = \frac{1}{2}\sum_{t \in T_{cb}} A_t \left(\sigma_1^2 + \sigma_1^{-2} + \sigma_2^2 + \sigma_2^{-2}\right)
$$

其中 $\sigma_1, \sigma_2$ 是三角形 Jacobian 的奇异值。对称 Dirichlet 能量同时惩罚"拉得太长"（$\sigma \gg 1$）和"压得太扁"（$\sigma \ll 1$），是衡量等距扭曲的经典度量。

**Projected Newton** 方法：

1. 计算每个三角形对 $(f_z^i, f_{\bar{z}}^i)$ 的 Hessian $Q_i$，复合约化 Jacobian 得全局 Hessian：$H = \sum_i \tilde{J}_i^T Q_i \tilde{J}_i$
2. 将 $Q_i$ 解析投影到 PSD（半正定）锥——保证全局 Hessian 正定，Newton 方向一定是下降方向
3. 双线搜索：先保证局部单射不丢失，再保证能量下降（Armijo 条件）

> **Why PSD 投影？** 对称 Dirichlet 在极值点附近 Hessian 可能不定，此时 Newton 步可能不是下降方向。PSD 投影是矩阵级的"安全兜底"——移除负特征值对应的方向，确保一步下去能量一定降低。

Observation 2 保证在 $T_{cb}$（而非全网格）上最小化 $E_{\text{iso}}$ 即可有效降低全局扭曲。

---

## 9. 与 HGP 的对比

| | HGP [BCW17] | FastHGP |
|:---|:---|:---|
| 调和约束 | 软约束（最小二乘松弛，允许偏离调和） | 硬约束（精确零空间，严格调和） |
| 优化变量 | 全部顶点 UV（$2|V|$ 维） | $c_{\text{int}}$（$2(|\partial V|+|C|+n-1)$ 维） |
| 核心求解器 | MOSEK SOCP（二阶锥规划，全局最优） | 1 次 LU 分解 + 选择性求逆 + ATP + Newton |
| 扭曲优化 | 无（SOCP 隐式控制） | 对称 Dirichlet + Projected Newton |
| 速度 | 基准 | ~10 倍快 |
| 鲁棒性 | 极高（含 homotopy 等启发式） | 略低（ATP 约 10-15% 不收敛，回退 HGP） |

实验数据：10 万三角形级模型约 1 秒完成；77 个测试模型中 66 个成功，11 个失败主要因 ATP 不收敛或求解器数值问题。

---

## 10. 理论要点小结

1. **子空间维数**：$2(|\partial V| + |C| + n - 1)$，与网格密度无关——百万面网格可能只需几十维
2. **两个观察**构成子空间方法的理论基础：单射性和扭曲都只在边界/锥点邻域需要控制
3. **KKT 公式化**避免了旋转调和约束的显式编码，同时用 $K$ 的可逆性证明了 $A_{\text{hgp}}$ 满秩
4. **选择性求逆**使子空间构造代价仅 ≈ 1 次 LU 分解，而非完整 $K^{-1}$
5. **ATP** 在低维 Jacobian + 局部凸可行集 $B_i$ 中求**局部单射的调和初值**（有锥点）；无锥时用 Tutte；**Projected Newton** 在同样低维空间中优化扭曲
6. 速度约 HGP 的 10 倍，代价是鲁棒性略降（ATP 偶有不收敛）；浏览器简化实现以 LSCM 代替 ATP/Tutte，仅保留对称 Dirichlet 精修
