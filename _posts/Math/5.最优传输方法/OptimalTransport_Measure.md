---
layout: post
title: "从蓝噪声 OT 到结构化测度逼近 — BNOT 与 OTA"
category: Parameterization
categories: ["Parameterization", "Parameterization-OptimalTransport"]
mathjax: true
---

| 顺序 | 论文 | 角色 |
| :--- | :--- | :--- |
| **①** | Fernando de Goes, Katherine Breeden, Victor Ostromoukhov, Mathieu Desbrun. [*Blue Noise through Optimal Transport*](https://doi.org/10.1145/2366145.2366190). ACM TOG 31(6), SIGGRAPH Asia 2012. | **等权**点集 / 蓝噪声 stippling：容量约束 + 半离散 $W_2$ / Power 图 |
| **②** | Frédéric de Gournay, Jonas Kahn, Léo Lebrat, Pierre Weiss. [*Optimal Transport Approximation of 2-Dimensional Measures*](https://doi.org/10.1137/18M1193736). SIAM J. Imaging Sci. 12(4), 2019. ([arXiv:1804.08356](https://arxiv.org/abs/1804.08356)) | 把 ① 推广为**结构化测度族** $\mathcal{M}$ 上的 $W_2$ 逼近（可变权、曲线、线段…） |

下文分别简称 **BNOT**（①）与 **OTA**（②）。逻辑链是：

1.  BNOT 把「连续密度 → 等权点」写成半离散 OT / Power 图，并弄清容量约束与站点–重心更新；
2.  对照 Lloyd / CVT：为何必须进 Power 图、Lloyd 更新在 BNOT 中的角色（§3）；
3.  OTA：同一 OT 内核嵌入交替投影梯度（$\psi$/$\mathbf{w}$/$\mathbf{x}$/$\Pi$），扩展可容许测度与数值稳定性（正则 Newton、Green 积分）。

给定紧域 $\Omega\subset\mathbb{R}^2$ 上的目标密度 $\rho$（测度 $\mu$），统一目标可写成

$$
\min_{\nu\in\mathcal{M}} D(\nu,\mu),
\tag{1}
$$

取 $D=W_2$（二次 Wasserstein），$\Omega=[0,1]^2$。$\mathcal{M}$ 从「$n$ 个等权 Dirac」（BNOT）扩到：

| 特例 | $\mathcal{M}$ | 与经典方法的关系 |
| :--- | :--- | :--- |
| **等权点集 / 蓝噪声** | 权重固定为 $1/n$ | **BNOT** [de Goes et al. 2012] |
| **Stippling（可变权）** | $n$ 个 Dirac，可变权重 | Lloyd、CCVT；OTA 的 $\mathcal{M}_{a,n}$ |
| **曲线测度** | 弧长参数化、有界曲率/速度/加速度 | Curvling、路径规划、喷嘴轨迹 |
| **线段测度** | 分段线性约束 | Dashing 风格渲染 |

**OTA 主要贡献**：(i) 交替极小化 + 变度量投影梯度；(ii) 稳定化正则 Newton 解半离散 OT 对偶并给全局收敛；(iii) Green 公式加速 Laguerre 积分；(iv) 曲线空间投影（运动学 + 几何约束）；(v) 与静电 halftoning、Lloyd、BNOT 的系统对照。

**前置**：[最优传输介绍](2018-05-01-最优传输介绍.md)、[半离散 OT（凸几何）](2020-05-01-基于凸几何的半离散最优传输.md)。透镜侧应用见 [最优传输计算焦散透镜](2020-12-12-最优传输计算焦散透镜.md)。

---

## 1. 问题与可容许测度族（共同设定）

$\mu$ 有密度 $\rho:\Omega\to\mathbb{R}_+$，$\int_\Omega \rho=1$。希望 $\nu\in\mathcal{M}$ 在 $W_2$ 意义下最接近 $\mu$，且 $\mathcal{M}$ 编码所需结构。

**有限支撑（点）**：

$$
\mathcal{M}_{f,n}=\left\{\nu(\mathbf{x})=\frac{1}{n}\sum_{i=1}^{n}\delta_{\mathbf{x}[i]},\;\mathbf{x}\in\Omega^n\right\},
\tag{2}
$$

$$
\mathcal{M}_{a,n}=\left\{\nu(\mathbf{x},\mathbf{w})=\sum_{i=1}^{n}\mathbf{w}[i]\,\delta_{\mathbf{x}[i]},\;\mathbf{x}\in\Omega^n,\;\mathbf{w}\in\Delta_{n-1}\right\},
\tag{3}
$$

$\Delta_{n-1}$ 为标准单纯形。解 (1) 且 $\mathcal{M}=\mathcal{M}_{a,n}$ 即**可变权重的量化**；$\mathcal{M}_{f,n}$ 为等权 stippling。

**曲线 / 线段**：$\mathcal{M}$ 为弧长参数化曲线、或固定长度/曲率的离散曲线的 pushforward 测度（§8）。

### 1.2 半离散 $W_2$ 距离

对 $\nu\in\mathcal{M}_{a,n}$，Monge 型传输计划 $T:\Omega\to\{\mathbf{x}[1],\ldots,\mathbf{x}[n]\}$ 满足 $\mu(T^{-1}(\mathbf{x}[i]))=\mathbf{w}[i]$。则

$$
W_2^2(\mu,\nu)=\inf_{T\in\mathcal{T}(\mathbf{x},\mathbf{w})}\int_\Omega \lVert x-T(x)\rVert _2^2\,\mathrm{d}\mu(x).
\tag{4}
$$

最优 $T^*$ 描述如何把连续质量 $\mu$ 搬到离散支撑上——这是半离散 OT 的核心。

在结构化测度族 $\mathcal{M}$ 上，OTA 的核心问题为

$$
\inf_{\nu\in\mathcal{M}} W_2^2(\nu,\mu).
\tag{5}
$$

### 1.3 相关工作与应用背景

问题 (1) 最早由 [Chauffert et al. 2017] 以**卷积核距离**形式提出；OTA 用 $W_2$ 重述并大幅扩展。同一框架覆盖：

| 领域 | 典型 $\mathcal{M}$ | 文献线索 |
| :--- | :--- | :--- |
| 金融 | 离散支撑 | Pages & Wilbertz 2012 |
| 计算机图形 | 点 / 曲线 / 线段 | stippling、stroke-based rendering |
| 采样理论 | 有界速度/加速度轨迹 | MRI 压缩采样 [Boyer et al. 2016] |
| 设施选址 / 网络 | 空间分布网络 | Gastner & Newman 2006 |
| 3D 打印 / 雕刻 | 连续喷嘴/激光轨迹 | Chen et al. 2017 |

**曲线逼近**在 NPR、TSP art、线雕 3D 打印中常见，但以往多无显式优化表述；OTA 将 curvling 纳入 (5)。

---

## 2. Blue Noise through Optimal Transport（de Goes et al. 2012）

> **论文**：Fernando de Goes, Katherine Breeden, Victor Ostromoukhov, Mathieu Desbrun. [*Blue Noise through Optimal Transport*](https://doi.org/10.1145/2366145.2366190). ACM TOG 31(6), SIGGRAPH Asia 2012.  
> **项目页**：[geometry.caltech.edu/BlueNoise](https://geometry.caltech.edu/BlueNoise/) · PDF：[Caltech](https://www.geometry.caltech.edu/pubs/dGBOD12.pdf)

本节是后文一般框架最直接的前驱：两边都在做「用半离散 $W_2$ / Power 图把连续密度 $\rho$ 凝聚成点集」。

给定域 $\mathcal{D}$ 与正密度 $\rho$（墨水分布），蓝噪声采样把连续墨水**凝聚**成 $n$ 个 Dirac。de Goes 用三条要求刻画：

| 要求 | 含义 |
| :--- | :--- |
| **A. 均匀采样（容量）** | 每点承载等量墨水：$m_i=\int_{V_i}\rho=m\equiv\frac{1}{n}\int_{\mathcal{D}}\rho$ |
| **B. 最优传输** | 把 $\rho$ 搬到点集的总代价最小 |
| **C. 局部不规则** | 避免六角晶格 / Moire 伪影 |

传输代价（对任意剖分 $\mathcal{V}=\{V_i\}$）为

$$
E(X,\mathcal{V})=\sum_{i}\int_{V_i}\rho(x)\,\lVert x-x_i\rVert _2^2\,\mathrm{d}x.
\tag{27a}
$$

[Aurenhammer et al. 1998] 证明：在容量约束下极小化 $E$ 的最优剖分必为 **Power 图**（权重 Voronoi / Laguerre）。

因此不必在全体剖分中搜索，可限制到加权点集 $(X,W)$ 的 Power 单元 $V_i^w$。

这与 OTA 把半离散 $W_2$ 写成 Laguerre 图上的对偶问题完全同构。

### 2.2 变分形式

带 Lagrange 乘子的约束极小化可化为对标量泛函求驻点：

$$
F(X,W)=E(X,W)-\sum_{i} w_i\bigl(m_i-m\bigr).
\tag{27b}
$$

关键性质（与后文 OTA 对偶 / 梯度公式同构）：

- **固定 $X$，对 $W$**：Hessian $=-\Delta_{w,\rho}$（加权 Laplacian）→ **凹极大化**；Newton 解稀疏 Poisson 系统即可精确满足容量约束（残差可达 $10^{-12}$）。这对应后文 OTA 的 $\psi$-step（对偶变量与 Power 权重一一对应）。
- **固定 $W$，对 $X$**：

$$
\nabla_{x_i}F=2\,m_i\,(x_i-b_i),\qquad
b_i=\frac{1}{m_i}\int_{V_i^w}x\,\rho(x)\,\mathrm{d}x.
\tag{27c}
$$

临界点要求 $x_i=b_i$，即 **centroidal Power diagram**。这正是后文 OTA 梯度 (23)–(24) 的等权版本（$\mathbf{w}[i]=m_i=1/n$）。

数值上交替执行：对 $W$ 做 Newton 投影到容量可行集；对 $X$ 做带线搜索的梯度下降。与经典 Lloyd / CVT 的对照见下一节。

---

### BNOT 与 Lloyd / CVT 的对比

蓝噪声生成中大量迭代法依赖 **Voronoi 图 + Lloyd 松弛** [Lloyd 1982]：把站点移到各自 Voronoi 单元的密度重心，极小化量化 RMS（即经典 **CVT** 能量）[McCool & Fiume 1992; Du et al. 1999]。

BNOT 把同一几何问题改写成**带容量约束的半离散 OT**，并在 **Power 图**上优化——与 Lloyd 的差异可按原文归纳为下表。

原文 §1.2：**充分收敛的 Lloyd 往往过规整**，实践中只好早停；Balzer et al. [2009] 的 **CCVT** 给每个站点加等容量约束以抑伪影，但容量被**离散量化**，复杂度近二次，难上大规模。随后 Chen et al. [2012]、Xu et al. [2011] 在 Voronoi / Delaunay 空间用面积方差作惩罚，只能**近似**容量——把「空间各向同性」与「等容量」捆进同一无约束目标，必然折中。

BNOT 的关键一步（原文 §2.3）：在容量约束下极小化传输代价 $E$ 时，最优剖分**不是**一般 Voronoi，而是 Power 图。

多出的权重 $w_i$ 正好用来**精确**满足 $m_i=m$，从而可在「容量可行集」上专心优化各向同性，而不必与约束做权衡。实践中最优权重并不均匀（原文 Fig. 2），这也从侧面说明：若强制 $w_i$ 全等（即退回 Voronoi），容量一般不可同时精确满足。

## 整体循环（原文 Algorithm）：

反复「$W$：Newton 投影到等容量」→「$X$：带线搜索的梯度步（可含一次 Lloyd 式重心移动）」→ 必要时对过规整邻域抖动。

这与后文 OTA 的「$\psi$-step → $\mathbf{x}$-step」同构；

---

## 4. OTA：离散化与总算法框架（de Gournay et al. 2019）

### 4.1 用原子测度逼近一般 $\mathcal{M}$

无穷维问题 (5) 用一族原子测度空间逼近：

$$
\mathcal{M}_n=\{\nu(\mathbf{x},\mathbf{w}):\mathbf{x}\in\mathbf{X}_n,\;\mathbf{w}\in\mathbf{W}_n\}\subseteq\mathcal{M}_{a,n},
\tag{6}
$$

$$
\nu(\mathbf{x},\mathbf{w})=\sum_{i=1}^{n}\mathbf{w}[i]\,\delta_{\mathbf{x}[i]}.
\tag{7}
$$

$\mathbf{X}_n\subseteq\Omega^n$ 编码点之间的几何关系（如曲线邻接、速度界），$\mathbf{W}_n\subseteq\Delta_{n-1}$ 编码权重约束。离散化问题为

$$
\inf_{\nu\in\mathcal{M}_n} W_2^2(\nu,\mu),
\tag{8}
$$

在 [Gournay et al. 2018] 中证明：对适当构造的 $(\mathcal{M}_n)$，离散解 $(\nu_n^*)$ 沿子列弱收敛到 (5) 的全局极小元。

**例**：$\mathcal{M}$ 为 $1$-Lipschitz 曲线 pushforward 的测度，可用相邻点间距 $\le 1/n$ 的 $n$ 个 Dirac 逼近，$O(1/n)$ 的 $W_2$ 误差。

离散问题写为

$$
\min_{\mathbf{x}\in\mathbf{X},\,\mathbf{w}\in\mathbf{W}} F(\mathbf{x},\mathbf{w}),
\tag{9}
$$

$$
F(\mathbf{x},\mathbf{w})=\tfrac{1}{2}W_2^2(\nu(\mathbf{x},\mathbf{w}),\mu).
\tag{10}
$$

### 4.2 Algorithm 1：交替投影梯度

**变度量投影**（OTA 论文 §2.2）：

$$
\Pi^{\Sigma_k}_{\mathbf{X}}(\mathbf{x}_0)
:=\arg\min_{\mathbf{x}\in\mathbf{X}}\lVert \mathbf{x}-\mathbf{x}_0\rVert ^2_{\Sigma_k},
\qquad
\lVert \mathbf{x}-\mathbf{x}_0\rVert ^2_{\Sigma_k}
=\langle\Sigma_k(\mathbf{x}-\mathbf{x}_0),(\mathbf{x}-\mathbf{x}_0)\rangle.
$$

$\mathbf{X}$ 非凸时 $\Pi$ 为**点集值**映射，故 $\mathbf{x}$-步写 $\mathbf{x}_{k+1}\in\Pi(\cdots)$ 而非 $=$。

```
Algorithm 1  交替投影梯度（最小化 (1) / (9)）

Oracle: 给定 (x, w)，通过 ψ-step 计算 F(x,w)、∇_x F
输入:  初始 x₀, 目标测度 μ, 迭代次数 N_it
输出:  (x̂, ŵ) 近似 (9) 的解

for k = 0, …, N_it−1:
  w-step:  w_{k+1} ← argmin_{w∈W} F(x_k, w)              ▷ 解析
  选正定矩阵 Σ_k、步长 s_k
  x-step:  y_{k+1} ← x_k − s_k Σ_k^{-1} ∇_x F(x_k, w_{k+1})
  Π-step:  x_{k+1} ∈ Π^{Σ_k}_X(y_{k+1})
end for
x̂ ← x_{N_it},  ŵ ← w_{N_it}
```

**无约束 stippling / halftoning** 时 $\Pi$-步平凡：$\mathbf{x}_{k+1}=\mathbf{y}_{k+1}$。

**五大实现难点**：

| 步骤 | 问题 |
| :--- | :--- |
| $\psi$ | 如何高效计算 $F$？ |
| $\mathbf{w}$ | 如何解 $\arg\min_{\mathbf{w}\in\mathbf{W}}F$？ |
| $\mathbf{x}$ | 如何算 $\nabla_{\mathbf{x}}F$ 与度量 $\Sigma_k$？ |
| $\Pi$ | 如何实现曲线空间投影？ |
| 加速 | 多尺度、warm start 等 |

---

## 5. $\psi$-step：半离散最优传输

### 5.1 假设与 Laguerre 图

**Assumption 1**：$\Omega$ 为紧凸多面体（通常 $[0,1]^2$）；$\mu$ 绝对连续；$\nu$ 为 $n$ 个原子的离散测度。

**Theorem 1**：在 Assumption 1 下，(4) 的最优传输计划 $T^*$ 在 $\mu$-a.e. 意义下唯一。

**Laguerre 单元**（Power 图）：给定点位置 $\mathbf{x}$ 与权重 $\boldsymbol{\psi}\in\mathbb{R}^n$，

$$
\mathcal{L}_i(\boldsymbol{\psi},\mathbf{x})
=\Bigl\{x\in\Omega:\forall j\neq i,\;
\lVert x-\mathbf{x}[i]\rVert ^2-\boldsymbol{\psi}[i]\le \lVert x-\mathbf{x}[j]\rVert ^2-\boldsymbol{\psi}[j]\Bigr\}.
\tag{11}
$$

$\boldsymbol{\psi}=\mathbf{0}$ 时退化为 Voronoi 图。平面 Laguerre 图可在 $O(n\log n)$ 内计算（CGAL）。

**Theorem 2**：存在 $\boldsymbol{\psi}^*\in\mathbb{R}^n$ 使最优传输满足

$$
(T^*)^{-1}(\mathbf{x}[i])=\mathcal{L}_i(\boldsymbol{\psi}^*,\mathbf{x}).
\tag{12}
$$

即每个站点的质量恰好来自其 Laguerre 单元

### 5.2 对偶问题

无穷维 (4) 化为有限维**凹**极大化：

$$
W_2(\mu,\nu)=\max_{\boldsymbol{\psi}\in\mathbb{R}^n} g(\boldsymbol{\psi},\mathbf{x},\mathbf{w}),
\tag{13}
$$

$$
g(\boldsymbol{\psi},\mathbf{x},\mathbf{w})
=\sum_{i=1}^{n}\int_{\mathcal{L}_i(\boldsymbol{\psi},\mathbf{x})}
\bigl(\lVert \mathbf{x}[i]-x\rVert ^2-\boldsymbol{\psi}[i]\bigr)\,\mathrm{d}\mu(x)
+\sum_{i=1}^{n}\boldsymbol{\psi}[i]\,\mathbf{w}[i].
\tag{14}
$$

**Proposition 1**（$g$ 的光滑性）：

- $g$ 对 $\boldsymbol{\psi}$ **凹**，梯度 Lipschitz；
- 梯度：

$$
\frac{\partial g}{\partial\boldsymbol{\psi}_i}=\mathbf{w}[i]-\mu(\mathcal{L}_i(\boldsymbol{\psi},\mathbf{x})).
\tag{15}
$$

- 若 $\rho\in C^1$，则 $g$ 几乎处处二阶可微；$i\neq j$ 时

$$
\frac{\partial^2 g}{\partial\boldsymbol{\psi}_i\partial\boldsymbol{\psi}_j}
=\int_{\partial\mathcal{L}_i\cap\partial\mathcal{L}_j}\frac{\mathrm{d}\mu(x)}{\lVert \mathbf{x}[i]-\mathbf{x}[j]\rVert },
\tag{16}
$$

对角元由闭包关系

$$
\sum_{j=1}^{n}\frac{\partial^2 g}{\partial\boldsymbol{\psi}_i\partial\boldsymbol{\psi}_j}=0
\tag{17}
$$

确定。Hessian 结构与 [Levy et al. 2015] 半离散 OT 笔记一致：相邻 Laguerre 面共享时非零。

由 Gershgorin 圆盘定理，Hessian 最小特征值有下界 $-n\eta\lVert \rho\rVert _\infty\mathrm{diam}(\Omega)$，其中 $\eta=1/\min_{i\neq j}\lVert \mathbf{x}[i]-\mathbf{x}[j]\rVert $。

**二阶可微性的证明要点**：若某 Laguerre 单元测度为零，则其为线段或点。在一般位置假设下，点 $x$ 满足至少 3 个等式

$$
\lVert x-\mathbf{x}[i]\rVert ^2-\boldsymbol{\psi}[i]=\lVert x-\mathbf{x}[j_k]\rVert ^2-\boldsymbol{\psi}[j_k],
\tag{18}
$$

使 $\mathcal{L}_i$ 退化为单点；满足 (18) 的 $\boldsymbol{\psi}$ 集合余维 $\ge 1$，故几乎处处二阶可微。

**Lipschitz 梯度界**（命题 1 证明）：Laguerre 边界随 $\boldsymbol{\psi}$ 线性移动，速率 $\le\eta$。对单位方向 $\Delta$，

$$
\bigl|\mu(\mathcal{L}_i(\boldsymbol{\psi}+t\Delta,\mathbf{x}))-\mu(\mathcal{L}_i(\boldsymbol{\psi},\mathbf{x}))\bigr|
\le t(n-1)\lVert \rho\rVert _\infty\eta\,\mathrm{diam}(\Omega),
$$

求和得 $\lVert \nabla_{\boldsymbol{\psi}}g(\boldsymbol{\psi}+t\Delta)-\nabla_{\boldsymbol{\psi}}g(\boldsymbol{\psi})\rVert _2\le t n^{3/2}\lVert \rho\rVert _\infty\eta\,\mathrm{diam}(\Omega)$（偏悲观）。

**Proposition 2**：若 $\min\rho>0$ 且站点两两不同，(13) 的极大化子在加常数意义下唯一；极大点附近 $g$ 强凹。

**一阶 vs 二阶方法的困境** [Kitagawa et al.; Levy]：一阶法依赖梯度 Lipschitz 常数；二阶法依赖 $g$ 的 Hölder 正则性，且要求 Laguerre 单元质量不消失。故早期迭代宜一阶 + 好初值，接近最优解后切换二阶。LM / trust-region 的全局 $C^2$ 假设此处不满足。

### 5.3 正则化 Newton 法（稳定化）

先前方法 [Aurenhammer et al. 1998; de Goes et al. 2012; Levy et al.] 的收敛常依赖梯度 Lipschitz 常数，而该常数在点共线、密度不均匀时可**任意大**。

**Remark 1（高 Lipschitz 常数）**：$\mu$ 为 $\Omega=[0,1]^2$ 上均匀测度，$n$ 个点等距竖直排列 $\mathbf{x}[i]=(\tfrac12,\tfrac{1+2i}{2n})$。Hessian 为 1D Neumann Laplacian 的倍数，最大特征值 $\sim 4n$，Lipschitz 常数随 $n$ 爆炸——**曲线逼近密度时典型**。

OTA 采用**正则化 Newton**（类似 Levenberg–Marquardt，但正则参数自动选取）：

$$
\boldsymbol{\psi}_{k+1}=\boldsymbol{\psi}_k-t_k\bigl(A(\boldsymbol{\psi}_k)+\lVert \nabla_{\boldsymbol{\psi}}g(\boldsymbol{\psi}_k)\rVert _2\,\mathrm{Id}\bigr)^{-1}\nabla_{\boldsymbol{\psi}}g(\boldsymbol{\psi}_k),
\tag{19}
$$

$$
A(\boldsymbol{\psi})=
\begin{cases}
\nabla^2_{\boldsymbol{\psi}} g(\boldsymbol{\psi}) & \text{若 Hessian 在 }\boldsymbol{\psi}\text{ 有定义},\\
0 & \text{否则}.
\end{cases}
\tag{20}
$$

在**零均值**子空间上求解以保证唯一性。**Proposition 3**：Wolfe 线搜索下 (19) **全局收敛**到 (13) 的唯一极大点，且局部**二次收敛**——此前结果多为局部收敛 [Levy et al.]。

**设计 rationale**：去掉 $\lVert \nabla g\rVert \mathrm{Id}$ 则为纯 Newton；加入后，远离最优解时 $\lVert \nabla g\rVert $ 大 → 接近梯度下降；接近最优时 $\lVert \nabla g\rVert \to 0$ → 接近阻尼 Newton。

实践上可结合 [Merigot 2011] 的多尺度初始化；亦可用标准 LM $\boldsymbol{\psi}_{k+1}=\boldsymbol{\psi}_k-(A+c_k\mathrm{Id})^{-1}\nabla g$，$c_k$ 由 Wolfe 准则调节，收敛率相近。

### 5.4 Green 公式加速积分

计算 (14)(16) 需对 Laguerre 单元积分。策略：

1. 在规则网格上用双线性/双三次插值离散 $\rho$；
2. 用 **Green 公式**把体积分化为沿 Laguerre 边界的多项式线积分；
3. **预计算**边上各阶矩，之后每次 $\psi$-step 仅做线性组合。

对笛卡尔网格，Laguerre 单元与网格交可解析求交，复杂度从 $O(n_{\text{pixels}})$ 降至约 $O(\sqrt{n_{\text{pixels}}})$，使 $10^5$ 级点集在分钟量级可行。这是 OTA 相对 ibnot（BNOT 实现）的主要加速来源之一。

---

## 6. $\mathbf{w}$-step 与 $\mathbf{x}$-step

### 6.1 最优权重

子问题

$$
\mathbf{w}^*=\arg\min_{\mathbf{w}\in\mathbf{W}} F(\mathbf{x},\mathbf{w}).
\tag{21}
$$

#### 6.1.1 完全约束 $\mathbf{w}$

$\mathbf{W}=\{\mathbf{w}_0\}$（singleton，如等权 $1/n$）：$\mathbf{w}^*=\mathbf{w}_0$。

#### 6.1.2 单纯形上无约束极小化

$\mathbf{W}=\Delta_{n-1}$：**Proposition 4** 给出闭式解

$$
\mathbf{w}^*[i]=\mu(\mathcal{L}_i(\mathbf{0},\mathbf{x})),
\tag{22}
$$

即权重等于 **Voronoi 单元**（$\boldsymbol{\psi}=0$ 的 Laguerre 单元）内的 $\mu$-质量。

**证明要点**：在 (14) 中 $\boldsymbol{\psi}$ 是质量约束

$$
\mu\bigl(T^{-1}(\mathbf{x}[i])\bigr)=\mathbf{w}[i]
$$

的 Lagrange 乘子；对 $\mathbf{w}$ 极小化时该约束被移除，故可取 $\boldsymbol{\psi}=\mathbf{0}$。

### 6.2 站点梯度与变度量

设 $\boldsymbol{\psi}^*$ 为 (13) 的极大izer。**Proposition 5**：在 $\rho\in C^0\cap W^{1,1}$、$\mathbf{w}>0$、站点分离时，$F$ 对 $\mathbf{x}$ 为 $C^2$，且

$$
\frac{\partial F(\mathbf{x},\mathbf{w})}{\partial\mathbf{x}[i]}
=\mathbf{w}[i]\,\bigl(\mathbf{x}[i]-\mathbf{b}[i]\bigr),
\tag{23}
$$

其中 $\mathbf{b}[i]$ 为第 $i$ 个 Laguerre 单元的 $\mu$-重心：

$$
\mathbf{b}[i]=\frac{\int_{\mathcal{L}_i(\boldsymbol{\psi}^*,\mathbf{x})} x\,\mathrm{d}\mu(x)}
{\int_{\mathcal{L}_i(\boldsymbol{\psi}^*,\mathbf{x})}\mathrm{d}\mu(x)}.
\tag{24}
$$

**度量矩阵**（Algorithm 1 中 $\Sigma_k$）：

$$
\Sigma_k=\mathrm{diag}\bigl(\mu(\mathcal{L}_i(\boldsymbol{\psi}^*_k,\mathbf{x}_k))\bigr)_{1\le i\le n}.
\tag{25}
$$

**为何这样选？**

1. **Lloyd 算法**：无约束时 $\mathbf{x}_{k+1}=\mathbf{b}(\mathbf{x}_k)$——站点移向各自 Laguerre 单元重心。
2. **交替方向**：固定传输计划（Laguerre 剖分）后，移重心是固定剖分下最优位置。
3. **局部 1-Lipschitz**：临界点处 $\mathbf{x}\mapsto\mathbf{b}(\mathbf{x})$ 局部 1-Lipschitz [Du et al. 2010]，支持步长 $s_k=1$。
4. **拟 Newton**：$\Sigma_k$ 近似 $F$ 对 $\mathbf{x}$ 的 Hessian 对角 [Lebrat et al. / de Gournay et al. 2018]——$\Sigma_k$ 第 $i$ 对角元等于 $H_{\mathbf{x}\mathbf{x}}[F]$ 第 $i$ 行系数之和。

保证收敛的保守选取：$s_k$ 满足 **Wolfe 条件**。鉴于上述性质，实践取 $s_k=1$，无需线搜索即收敛良好（附录 A 给出局部理论支撑）。

---



## 8. 曲线空间投影（$\Pi$-step）

Stippling 无约束时 $\Pi$ 平凡。对 **curvling / 路径规划**，$\mathbf{X}$ 描述离散曲线上的运动学或几何约束。

### 8.1 离散曲线算子

离散曲线 $\mathbf{x}=(\mathbf{x}[1],\ldots,\mathbf{x}[n])\in\Omega^n$。**一阶差分**算子（开/闭曲线）：

$$
A_1^a:\mathbf{x}\mapsto
\begin{pmatrix}\mathbf{x}[2]-\mathbf{x}[1]\\ \vdots\\ \mathbf{x}[n]-\mathbf{x}[n-1]\\ \mathbf{x}[1]-\mathbf{x}[n]\end{pmatrix},
\qquad
A_1^b:\mathbf{x}\mapsto
\begin{pmatrix}\mathbf{x}[2]-\mathbf{x}[1]\\ \mathbf{x}[3]-\mathbf{x}[2]\\ \vdots\\ \mathbf{x}[n]-\mathbf{x}[n-1]\end{pmatrix}.
$$

下文 $A_1$ 泛指二者之一。**二阶差分**可取 $A_2=A_1^{\mathsf T}A_1$。

#### 运动学约束（凸）

有界**速度**与**加速度**（车辆模型）：

$$
\lVert (A_1\mathbf{x})[i]\rVert _2\le\alpha_1,\quad\forall i,
\tag{29}
$$

$$
\lVert (A_2\mathbf{x})[i]\rVert _2\le\alpha_2,\quad\forall i.
\tag{30}
$$

$$
\mathbf{X}=\{\mathbf{x}\in\Omega^n:\lVert A_1\mathbf{x}\rVert _{\infty,2}\le\alpha_1,\;\lVert A_2\mathbf{x}\rVert _{\infty,2}\le\alpha_2\}.
\tag{31}
$$

$\lVert \mathbf{y}\rVert _{\infty,p}=\sup_i\lVert \mathbf{y}[i]\rVert _p$。集合 (31) **凸**。

#### 几何约束（非凸）

连续情形：弧长参数曲线 $s:[0,T]\to\mathbb{R}^2$，$\lVert \dot{s}\rVert =1$，长度 $T$，曲率 $\kappa(t)=\lVert \ddot{s}(t)\rVert $。

**弧长均匀参数化**（离散）：

$$
\lVert (A_1\mathbf{x})[i]\rVert _2=\alpha_1,\quad\forall i.
\tag{32}
$$

曲线总长 $(n-1)\alpha_1$。

**有界曲率**：

$$
\lVert (A_2\mathbf{x})[i]\rVert _2\le\alpha_2,\quad\forall i.
\tag{33}
$$

在 (32) 成立时，对 $2\le i\le n-1$ 有推导

$$
\lVert (A_2\mathbf{x})[i]\rVert _2^2
=2\alpha_1^2\bigl(1-\cos\theta_i\bigr),
$$

其中 $\theta_i=\angle(\mathbf{x}[i]-\mathbf{x}[i-1],\,\mathbf{x}[i+1]-\mathbf{x}[i])$。故 (32)+(33) 蕴含

$$
|\theta_i|\le\arccos\!\Bigl(1-\frac{\alpha_2^2}{2\alpha_1^2}\Bigr).
\tag{34}
$$

固定长度 + 有界曲率：

$$
\mathbf{X}=\{\mathbf{x}\in\Omega^n:\lVert (A_1\mathbf{x})[i]\rVert _2=\alpha_1,\;\lVert A_2\mathbf{x}\rVert _{\infty,2}\le\alpha_2\}.
\tag{35}
$$

(35) **非凸**——可曲线缩短（投影变短更光滑）或曲线延长（加小环，Fig. 4）。

#### 线性附加约束

闭曲线、过指定点、指定均值等：

$$
B\mathbf{x}=\mathbf{b},
\qquad B\in\mathbb{R}^{p\times 2n},\;\mathbf{b}\in\mathbb{R}^p.
\tag{36}
$$

**统一形式**：

$$
\mathbf{X}=\{\mathbf{x}:A_i\mathbf{x}\in\mathbf{Y}_i,\;1\le i\le m,\;B\mathbf{x}=\mathbf{b}\}.
\tag{37}
$$

例如有界速度 (29) 对应

$$
\mathbf{Y}_1=\{\mathbf{y}\in\mathbb{R}^{n\times 2}:\lVert \mathbf{y}[i]\rVert _2\le\alpha_1,\;\forall i\}.
\tag{38}
$$

权重常取 $\mathbf{W}=\{1/n\}$ 或 $\Delta_{n-1}$。

### 8.2 ADMM 投影

**欧氏投影**（Algorithm 1 的 $\Pi$-步在无变度量时，或 ADMM 子问题）：

$$
\Pi_{\mathbf{X}}(\mathbf{z})
=\arg\min_{\substack{A_k\mathbf{x}\in\mathbf{Y}_k\\ B\mathbf{x}=\mathbf{b}}}
\tfrac{1}{2}\lVert \mathbf{x}-\mathbf{z}\rVert _2^2.
\tag{39}
$$

$\mathbf{X}$ 凸时解唯一；非凸时可能多解，算法求 (39) 的临界点。

**ADMM 分裂**：预条件 $\gamma_i>0$，堆叠

$$
A=\begin{pmatrix}\gamma_1 A_1\\ \vdots\\ \gamma_m A_m\end{pmatrix},\quad
\mathbf{y}=\begin{pmatrix}\mathbf{y}_1\\ \vdots\\ \mathbf{y}_m\end{pmatrix},\quad
\mathbf{Y}=\gamma_1\mathbf{Y}_1\times\cdots\times\gamma_m\mathbf{Y}_m.
\tag{40–41}
$$

(39) 等价于

$$
\min_{\substack{B\mathbf{x}=\mathbf{b}\\ A\mathbf{x}=\mathbf{y}\\ \mathbf{y}\in\mathbf{Y}}}
\tfrac{1}{2}\lVert \mathbf{x}-\mathbf{z}\rVert _2^2
=\min_{A\mathbf{x}=\mathbf{y}} f_1(\mathbf{x})+f_2(\mathbf{y}),
\tag{42}
$$

其中 $f_1(\mathbf{x})=\tfrac12\lVert \mathbf{x}-\mathbf{z}\rVert _2^2+\iota_{\mathbf{L}}(\mathbf{x})$，$\mathbf{L}=\{\mathbf{x}:B\mathbf{x}=\mathbf{b}\}$；$f_2(\mathbf{y})=\iota_{\mathbf{Y}}(\mathbf{y})$，

$$
\iota_{\mathbf{Y}}(\mathbf{y})=
\begin{cases}0 & \mathbf{y}\in\mathbf{Y},\\ +\infty & \text{否则}.\end{cases}
\tag{43}
$$

**Algorithm 2**（通用 ADMM）：交替更新 $\mathbf{y}$、$\mathbf{x}$、对偶 $\boldsymbol{\lambda}$，罚参数 $\beta>0$。

**Algorithm 3**（专用于 (39)）：

```
输入: 待投影 z, 初值 (x₀, λ₀), 矩阵 A,B, 投影 Π_Y, β>0
while 未收敛:
  y_{k+1} ← Π_Y(A x_k + λ_k)
  解线性系统:
    [ β A^T A + I   B^T ] [ x_{k+1} ]   [ β A^T(y_{k+1}−λ_k) + z ]
    [     B          0  ] [   μ     ] = [              b              ]
  λ_{k+1} ← λ_k + A x_{k+1} − y_{k+1}
```

$\mathbf{x}$-步用**共轭梯度**求解。$\mathbf{y}$-步为逐约束欧氏投影（球约束、等长约束等）。

- **凸 (31)**：ADMM 线性收敛 [Giselsson & Boyd]。
- **非凸 (35)**：理论开放 [Li & Pong]，实践中收敛到临界点。

**参数选取**：$\gamma_i=\lVert A_i\rVert _2$（谱范数）经验稳定；$\beta$ 手动调一次后固定。

### 8.3 投影算例（Fig. 4）

将猫轮廓（红）投影到蓝约束曲线集：中图——更短长度 + 有界曲率（简化变光滑）；右图——更长长度 + 有界曲率（加环保持形状）。

### 8.4 多分辨率实现

曲线优化时**不全点同时优化**：先在降采样曲线上解 (9)，再二分上采样中点作 warm start。实现用**二进尺度**：相邻采样间插中点；分辨率间权重除以 2。



## 附录 ：

### Algorithm 1 的收敛性

**Theorem 3** [Nesterov]：设 $\mathbf{X}\subset\mathbb{R}^n$ 闭凸，$\Sigma_k=\Sigma\succ 0$ 常数，$F\in C^1$ 且

$$
\forall(\mathbf{x}_1,\mathbf{x}_2),\quad
\lVert \nabla F(\mathbf{x}_1)-\nabla F(\mathbf{x}_2)\rVert _{\Sigma^{-1}}
\le L\lVert \mathbf{x}_1-\mathbf{x}_2\rVert _{\Sigma},
\tag{46}
$$

且 $\mathbf{X}$ 紧或 $F$ 强制。则步长 $s_k=1/L$ 时 Algorithm 1 收敛到 $F$ 的临界点。

**应用限制**：定理要求 $\Sigma_k$ 常数 → 权重 $\mathbf{w}$ 需预先固定。由 (23)，$\nabla_{\mathbf{x}}F$ 的 Lipschitz 常数含 $\min_{i\neq j}\lVert \mathbf{x}[i]-\mathbf{x}[j]\rVert ^{-1}$，**不能**对 $\mathbf{x}$ 一致有界 → 仅有**局部**理论。

**无 $\Pi$-步**（$\mathbf{X}=\Omega^n$）：临界点处梯度 1-Lipschitz（centroidal tessellation）[Du et al. Prop. 6.3]，故 $s_k=1$、$\Sigma_k$ 如 (25) 时可在 $\mathbf{x}^*$ 邻域内证明收敛。邻域大小依赖最优 Laguerre 剖分几何；数值上数百次随机初始化均收敛到视觉良好的驻点。



## 参考文献

- de Gournay F., Kahn J., Lebrat L., Weiss P. *Optimal transport approximation of 2-dimensional measures*. SIAM J. Imaging Sci., 12(4), 2019. [DOI](https://doi.org/10.1137/18M1193736) · [arXiv:1804.08356](https://arxiv.org/abs/1804.08356)
- de Goes F., Breeden K., Ostromoukhov V., Desbrun M. *Blue noise through optimal transport*. ACM TOG (SIGGRAPH Asia), 31(6), 2012. [DOI](https://doi.org/10.1145/2366145.2366190) · [项目页](https://geometry.caltech.edu/BlueNoise/)
- de Goes F., Cohen-Steiner D., Alliez P., Desbrun M. *An optimal transport approach to robust reconstruction and simplification of 2d shapes*. CGF, 30(5), 2011.- Aurenhammer F., Hoffmann M., Aronov B. *Minkowski-type theorems and least-squares clustering*. Algorithmica, 1998.
- Lévy B., Schwindt C., Steele E. *Laguerre–Minkowski diagrams and applications*. 2015.
- Merigot Q., Mérigot J. *A multiscale approach to optimal transport*. Computer Graphics Forum, 2018.
- Balzer M., Deussen O., et al. *Capacity-constrained point distributions*. CGF, 2009.
- Gournay F., et al. *A projection method on measures sets*. Constructive Approximation, 45(1), 2017. [Chauffert et al. — 卷积距离版 (1)]
- Boyer C., Chauffert N., Ciuciu P., Kahn J., Weiss P. *On the generation of sampling schemes for MRI*. SIAM J. Imaging Sci., 9(4), 2016.
- de Gournay F., Kahn J., Lebrat L. *Differentiation and regularity of semi-discrete optimal transport*. arXiv:1803.00827, 2018. [式 (23) 梯度来源]
- Du Q., Faber V., Gunzburger M. *Centroidal Voronoi tessellations*. SIAM Review, 41(4), 1999.
- Kitagawa J., Mérigot Q., Thibert B. *A Newton algorithm for semi-discrete optimal transport*. arXiv:1603.05579, 2016.
- Merigot Q. *A multiscale approach to optimal transport*. CGF, 30(5), 2011.
- Polyak R. A. *Regularized Newton method for unconstrained convex optimization*. Math. Program., 120(1), 2009.
- Schmaltz C., Gwosdek P., Bruhn A., Weickert J. *Electrostatic halftoning*. CGF, 29, 2010.

**相关笔记**：[最优传输介绍](2018-05-01-最优传输介绍.md) · [Monge/Kantorovich](2018-06-01-Monge问题与Kantorivch问题.md) · [半离散 OT](2020-05-01-基于凸几何的半离散最优传输.md) · [多尺度半离散 OT](2020-05-02-多尺度半离散最优传输.md) · [最优传输计算焦散透镜](2020-12-12-最优传输计算焦散透镜.md) · [Sinkhorn](2020-05-12-Sinkhorn算法与DSB.md)
