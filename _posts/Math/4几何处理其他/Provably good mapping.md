---
layout: post
title: "Provably Good Planar Mappings — 可证明的平面映射"
category: Parameterization
categories: ["Parameterization", "Parameterization-GeometricOptimization"]
mathjax: true
---

> **论文**：Roi Poranne, Yaron Lipman. [*Provably Good Planar Mappings*](https://doi.org/10.1145/2601097.2601123). ACM Transactions on Graphics (SIGGRAPH), 33(4), 2014.

## 概述

平面映射与变形是图形学中的核心问题（图像变形、角色动画、配准、形状分析等）。**Provably Good Planar Mappings** 提出一套框架：在通用光滑函数基上构造映射，使"好"的性质——**无折叠（单射）、光滑、低畸变**——不仅在配准点上成立，而且可**证明**在整个定义域上成立。

变形即映射 $f:\Omega \to \mathbb{R}^2$；**Jacobian** $J_f$ 描述局部线性近似，**畸变**度量映射质量。本文路线：在 **meshless** 光滑基（B-Spline、TPS、Gaussian）上，于**配准点（collocation points）**施加**凸约束**，再用连续性模把离散保证**传播到全域**——桥接 mesh 方法的可控性与 meshless 的光滑性。

---

## 1. 动机：mesh 与 meshless 的鸿沟

用户拖动**手柄** $\{(\mathbf{p}_i,\mathbf{q}_i)\}$ 驱动区域 $\Omega\subset\mathbb{R}^2$ 的变形，要求：光滑、无 fold-over、畸变不超过阈值 $K$。常见路线各有短板：

| 方法类型 | 优势 | 不足 |
| :--- | :--- | :--- |
| **Mesh-based**（三角网格、ARAP、SLIM、[Lipman 2012 投影](https://doi.org/10.1145/2185520.2185604) 等） | 可控制单射 / 畸变 | 要足够光滑需极密单元，慢；交互变形易出现尖点 |
| **Meshless**（B-Spline、TPS、Gaussian、MVC 等） | 构造上天然光滑 | 难避免折叠，难控制畸变；MVC 等仅在有限点证明单射 |

本文目标：**meshless 的光滑基 + 可证明的全局单射与畸变界**。

---

## 2. 线性变形空间

选取有限组基函数 $\mathcal{F}=\{\varphi_k\}_{k=1}^n$，$\varphi_k:\Omega\to\mathbb{R}$。平面映射写为

$$
f(\mathbf{x}) = \begin{pmatrix} u(\mathbf{x}) \\ v(\mathbf{x}) \end{pmatrix}
= \sum_{k=1}^{n} \mathbf{c}_k\,\varphi_k(\mathbf{x}),
\qquad \mathbf{c}_k\in\mathbb{R}^2,
\tag{1}
$$

系数矩阵 $\mathbf{C}=[\mathbf{c}_1,\ldots,\mathbf{c}_n]\in\mathbb{R}^{2\times n}$ 为优化变量。基函数光滑 ⇒ $f$ 光滑；但**不**加约束时，$\mathbf{C}$ 任意取值会产生任意 fold-over 与畸变。

**关键**：$J_f(\mathbf{x})$ 对 $\mathbf{C}$ **仿射**（梯度 $\nabla u,\nabla v$ 为 $\mathbf{C}$ 的线性函数），故可在配准点上把奇异值约束写成 **SOCP / SDP** 可解的凸集——这是与 [Lipman 2012](https://doi.org/10.1145/2185520.2185604) 网格投影一脉相承、但搬到 meshless 系数空间的核心。

### 2.1 三类实验基函数

| 基 | 形式（示意） | 特点 |
| :--- | :--- | :--- |
| **B-Spline** | 张量积三次均匀 B 样条 | 局部支撑、交互常用 |
| **TPS** | $\varphi(\lVert \mathbf{x}-\mathbf{x}_k\rVert )=r^2\log r$ | 插值型、整体光滑 |
| **Gaussian** | $\exp(-\lVert \mathbf{x}-\mathbf{x}_k\rVert ^2/(2s^2))$ | 形状感知（shape-aware）径向基 |

论文 Table 1 给出各基 $\nabla\varphi$ 的**梯度连续性模** $\omega_{\nabla\varphi}(t)$（见 §5），用于全域传播分析。

---

## 3. 畸变度量：Jacobian 奇异值

在 $\mathbf{x}$ 处，$f=(u,v)^T$ 的 Jacobian

$$
J_f(\mathbf{x}) = \begin{pmatrix} \partial_x u & \partial_y u \\ \partial_x v & \partial_y v \end{pmatrix}.
$$

奇异值 $\Sigma(\mathbf{x})\ge\sigma(\mathbf{x})\ge 0$ 度量两主方向的拉伸。$D(\mathbf{f},\mathbf{x})=D(\Sigma,\sigma)$，$D=1$ 为无畸变。

**等距畸变**（长度保持）：

$$
D_{\text{iso}}(\mathbf{x}) = \max\bigl\{\Sigma(\mathbf{x}),\; 1/\sigma(\mathbf{x})\bigr\}.
\tag{2}
$$

$D_{\text{iso}}=1$ $\Leftrightarrow$ $\Sigma=\sigma=1$（局部刚体）。

**共形畸变**（角度保持）：

$$
D_{\text{conf}}(\mathbf{x}) = \Sigma(\mathbf{x}) / \sigma(\mathbf{x}).
\tag{3}
$$

$D_{\text{conf}}=1$ $\Leftrightarrow$ $\Sigma=\sigma$（局部相似变换）。

### 3.1 相似 / 反相似分解（式 (19)(20)）

记 $I\in\mathbb{R}^{2\times 2}$ 为**逆时针旋转 $\pi/2$** 的矩阵。定义 Jacobian 的**相似部分**与**反相似部分**（对系数 $\mathbf{C}$ **线性**）：

$$
\mathbf{J}_S f(\mathbf{x})
= \frac{\nabla u(\mathbf{x}) + I\,\nabla v(\mathbf{x})}{2},
\qquad
\mathbf{J}_A f(\mathbf{x})
= \frac{\nabla u(\mathbf{x}) - I\,\nabla v(\mathbf{x})}{2}.
\tag{19}
$$

（此处 $\nabla u,\nabla v\in\mathbb{R}^2$ 为列向量。）奇异值可写为（[Lehto & Virtanen 1973]）

$$
\Sigma(\mathbf{x}) = \bigl\lVert \mathbf{J}_S f(\mathbf{x})\bigr\rVert  + \bigl\lVert \mathbf{J}_A f(\mathbf{x})\bigr\rVert ,
\qquad
\sigma(\mathbf{x})
= \Bigl|\bigl\lVert \mathbf{J}_S f(\mathbf{x})\bigr\rVert  - \bigl\lVert \mathbf{J}_A f(\mathbf{x})\bigr\rVert \Bigr|.
\tag{20}
$$

等距界 (10) 即 $\lVert \mathbf{J}_S\rVert +\lVert \mathbf{J}_A\rVert \le K$ 且 $\lVert \mathbf{J}_S\rVert -\lVert \mathbf{J}_A\rVert \ge K^{-1}$；后者非凸，§7 用 **frame** 凸化。该分解也是 **Lemma 2**（附录 B）与 SOCP 约束 (21)–(28) 的基础。

---

## 4. 配准点、填充距离与连续性模

### 4.1 配准点上的约束

在配准点集 $\mathcal{Z}=\{\mathbf{z}_j\}_{j=1}^m\subset\Omega$ 上要求

$$
D(f;\mathbf{z}_j) \le K,\qquad \sigma(\mathbf{z}_j) > 0.
\tag{4}
$$

直接在整个 $\Omega$ 上施加无穷多条约束不可行；理论保证：若 $\mathcal{Z}$ **足够密**，且 (4) 在 $\mathcal{Z}$ 上成立，则对**所有** $\mathbf{x}\in\Omega$ 可界定畸变与单射性。

**填充距离（fill distance）** 量化密度：

$$
h(\mathcal{Z},\Omega) = \max_{\mathbf{x}\in\Omega}\;\min_{\mathbf{z}\in\mathcal{Z}} \lVert \mathbf{x}-\mathbf{z}\rVert .
\tag{5}
$$

即 $\Omega$ 中离配准点**最远**的点到最近配准点的距离。$h$ 越小，离散采样越密。

### 4.2 连续性模（式 (6)(7)）

标量函数 $g:\mathbb{R}^2\to\mathbb{R}$ 具有连续性模 $\omega$（**$\omega$-连续**），若

$$
|g(\mathbf{x}) - g(\mathbf{y})| \leq \omega(\lVert \mathbf{x} - \mathbf{y}\rVert ), \quad \forall \mathbf{x}, \mathbf{y} \in \Omega,
\tag{6}
$$

其中 $\omega:\mathbb{R}^+\to\mathbb{R}^+$ 连续、严格单调且 $\omega(0)=0$。向量值映射 $\mathbf{g}:\mathbb{R}^2\to\mathbb{R}^2$ 同理：

$$
\lVert \mathbf{g}(\mathbf{x}) - \mathbf{g}(\mathbf{y})\rVert  \leq \omega(\lVert \mathbf{x} - \mathbf{y}\rVert ), \quad \forall \mathbf{x}, \mathbf{y} \in \Omega.
\tag{7}
$$

### 4.3 奇异值的连续性模（Lemma 2 与式 (8)(9)）

**Lemma 2**：若 $\nabla u,\nabla v$ 均为 $\omega$-连续，则奇异值函数 $\Sigma,\sigma$ 为 **$2\omega$-连续**（证明见论文附录 B）。

对式 (1) 的映射，先界 $\nabla u$。记 $\omega_{\nabla f_i}$ 为基梯度 $\nabla f_i$ 的连续性模，$\omega_{\nabla\mathcal{F}}(t)\ge \omega_{\nabla f_i}(t)$ 对所有 $f_i\in\mathcal{F}$ 成立；矩阵**最大范数**

$$
\lVert \!\rVert \mathbf{C}\lVert \!\rVert  = \max_{\ell\in\{1,2\}} \sum_{i=1}^{n} \bigl|c_i^{(\ell)}\bigr|.
$$

则

$$
\lVert \nabla u(\mathbf{x}) - \nabla u(\mathbf{y})\rVert 
\leq \sum_{i=1}^{n} \bigl|c_i^{(u)}\bigr|\,\lVert \nabla f_i(\mathbf{x}) - \nabla f_i(\mathbf{y})\rVert 
\leq \lVert \!\rVert \mathbf{C}\lVert \!\rVert \,\omega_{\nabla\mathcal{F}}(\lVert \mathbf{x}-\mathbf{y}\rVert ),
\tag{8}
$$

故 $\omega_{\nabla u}=\omega_{\nabla v}=\lVert \!\rVert \mathbf{C}\lVert \!\rVert \,\omega_{\nabla\mathcal{F}}$。由 Lemma 2，奇异值函数的连续性模为

$$
\omega_{\Sigma,\sigma} = 2\,\lVert \!\rVert \mathbf{C}\lVert \!\rVert \,\omega_{\nabla\mathcal{F}}.
\tag{9}
$$

**Table 1**（论文）给出各基的 $\omega_{\nabla\mathcal{F}}$：

| 基 $f_i$ | $\omega_{\nabla\mathcal{F}}(t)$ |
| :--- | :--- |
| 三次均匀 B-Spline | $\dfrac{4}{3\Delta^2}\,t$，$\Delta$ 为网格间距 |
| TPS $\tfrac{1}{2}\lVert \mathbf{x}-\mathbf{x}_i\rVert ^2\log\lVert \mathbf{x}-\mathbf{x}_i\rVert ^2$ | $t\bigl(5.8 + 5|\log t|\bigr)$（局部，$\lVert \mathbf{x}-\mathbf{y}\rVert \lesssim 0.29$） |
| Gaussian $\exp\!\bigl(-\lVert \mathbf{x}-\mathbf{x}_i\rVert ^2/(2s^2)\bigr)$ | $t/s^2$ |

---

## 5. 全局畸变界：Lemma 1 与三种策略

**Lemma 1**：设 $\Sigma,\sigma$ 为 $\omega$-连续，$\mathbf{z}\in\mathcal{Z}$ 为配准点。则对任意 $\mathbf{x}\in\Omega$，

$$
\sigma(\mathbf{z}) - \omega(\lVert \mathbf{x}-\mathbf{z}\rVert )
\;\le\; \sigma(\mathbf{x}) \;\le\; \Sigma(\mathbf{x}) \;\le\;
\Sigma(\mathbf{z}) + \omega(\lVert \mathbf{x}-\mathbf{z}\rVert ).
$$

取 $\lVert \mathbf{x}-\mathbf{z}\rVert \le h(\mathcal{Z},\Omega)$ 即得全域界。

### 5.1 等距界（式 (10)(11)）

设在所有 $\mathbf{z}\in\mathcal{Z}$ 上 $D_{\text{iso}}(\mathbf{z})\le K$，等价于

$$
\Sigma(\mathbf{z}) \leq K, \qquad \sigma(\mathbf{z}) \geq \frac{1}{K}.
\tag{10}
$$

记 $h=h(\mathcal{Z},\Omega)$，$\omega=\omega_{\Sigma,\sigma}$（由 (9) 计算）。则对任意 $\mathbf{x}\in\Omega$，

$$
D_{\text{iso}}(\mathbf{x}) \leq \max\left\{ K + \omega(h),\; \frac{1}{K^{-1} - \omega(h)} \right\},
\qquad\text{需 } K^{-1} > \omega(h).
\tag{11}
$$

当 $K^{-1}>\omega(h)$ 时 $\sigma(\mathbf{x})>0$，映射局部单射。

### 5.2 共形界（式 (12)(13)）

配准点上的共形约束为

$$
\Sigma(\mathbf{z}) \leq K\,\sigma(\mathbf{z}), \qquad \sigma(\mathbf{z}) \geq \delta > 0,
\tag{12}
$$

其中 $\delta$ 防止 $\sigma\to 0$ 失去单射。则

$$
D_{\text{conf}}(\mathbf{x}) \leq K\,\frac{\delta + \omega(h)}{\delta - \omega(h)},
\qquad
\sigma(\mathbf{x}) \geq \delta - \omega(h),
\qquad \delta > \omega(h).
\tag{13}
$$

### 5.3 三种畸变控制策略（式 (14)–(17)）

记目标**全域**畸变上界为 $K_{\max}$（论文记号 $K_{\max}>K$）。

| 策略 | 已知 | 求 |
| :--- | :--- | :--- |
| **1. 认证** | $\mathcal{Z}$、配准点界 $K$ | $K_{\max}$：由 (11)(13) 直接代入 $h,\omega$ |
| **2. 加密网格** | $K$、目标 $K_{\max}$ | 所需填充距离 $h$ |
| **3. 反推约束** | $\mathcal{Z}$（故已知 $h$）、目标 $K_{\max}$ | 配准点上应施加的 $K$ |

**策略 2**——反解 (11)(13)（$\omega^{-1}$ 单调递增）：

$$
h_{\text{iso}} \leq \omega^{-1}\!\left(
\min\left\{
K_{\max} - K,\;
\frac{1}{K} - \frac{1}{K_{\max}}
\right\}
\right),
\tag{14}
$$

$$
h_{\text{conf}} \leq \omega^{-1}\!\left(
\frac{\delta K_{\max} - K}{K_{\max} + K}
\right).
\tag{15}
$$

共形情形下 (15) 还要求 $h_{\text{conf}}<\omega^{-1}(\delta)$，从而由 (13) 保证 $\sigma(\mathbf{x})>0$。

**策略 3**——给定 $h$，反推配准点应施加的界：

$$
K_{\text{iso}} \leq \min\left\{
K_{\max} - \omega(h),\;
\frac{1}{\dfrac{1}{K_{\max}} + \omega(h)}
\right\},
\tag{16}
$$

$$
K_{\text{conf}} \leq K_{\max}\,\frac{\delta - \omega(h)}{\delta + \omega(h)},
\qquad \delta_{\text{conf}} > \omega(h).
\tag{17}
$$

式 (11)(13) 与 (14)–(17) 把**离散配准点界 $K$**、**密度 $h$**、**基的光滑性 $\omega$** 三者联系起来——这就是 **provably** 的含义：交互时只在稀疏 active set 上解 SOCP，后处理可用更密网格**认证**全域界。

交互阶段用粗网格（如 $200\times 200$ 配准点）实时求解；用户满意后切换到策略 2，用 $3000$–$6000$ 点网格**证明**单射与畸变界（论文实验）。

---

## 6. 单射性：从配准点到全域

**局部单射**：$\det J_f(\mathbf{x})>0$。因 $\sigma(\mathbf{x})>0 \Rightarrow \det J_f\ge 0$ 且 $\det J_f$ 连续，在连通域上符号不变；故**只需** $\sigma(\mathbf{x})>0$ 处处成立，并在每连通分量上**一点**验证 $\det J_f>0$。

**全局单射**（单连通 $\Omega$）：若 $f$ 局部单射且 $f|_{\partial\Omega}$ 单射，则 $f$ 在 $\Omega$ 上单射（proper map 论证）。

由 (11)：当 $K^{-1}>\omega(h)$ 时，$\sigma(\mathbf{x})\ge K^{-1}-\omega(h)>0$，结合 (4) 在配准点成立 ⇒ **全域无 fold-over**。共形界 (13) 中 $\delta>\omega_{\text{co}}(h)$ 起同样作用。

---

## 7. 配准点上的凸约束与 SOCP（式 (18)–(28)）

§4 将连续问题 (1)(2) 离散为在配准点集 $\mathcal{Z}$ 上施加约束。论文 §5 的优化子问题为

$$
\min_{\mathbf{C}}\; E_{\mathrm{pos}}(f) + \lambda E_{\mathrm{reg}}(f)
\quad\text{s.t.}\quad
D(f;\mathbf{z}) \le K,\;\forall \mathbf{z}\in\mathcal{Z},
\qquad
f = \sum_{i=1}^{n} \mathbf{c}_i f_i.
\tag{18}
$$

其中 $D=D_{\text{iso}}$ 或 $D_{\text{conf}}$，$K\ge 1$ 为用户畸变界。对正确的 $K$ 与 $\mathcal{Z}$（§5 策略 2/3），可证 $f$ 在全域满足 $K_{\max}$ 界。下文把 active 配准点 $\mathbf{z}_i$ 上的畸变约束写成 **SOCP**。

### 7.1 等距约束的锥形式（式 (21)–(26)）

由 (10) 与 (19)(20)，等距约束等价于

$$
\bigl\lVert \mathbf{J}_S f(\mathbf{z}_i)\bigr\rVert  + \bigl\lVert \mathbf{J}_A f(\mathbf{z}_i)\bigr\rVert  \le K,
\tag{21}
$$

$$
\bigl\lVert \mathbf{J}_S f(\mathbf{z}_i)\bigr\rVert  - \bigl\lVert \mathbf{J}_A f(\mathbf{z}_i)\bigr\rVert  \ge \frac{1}{K}.
\tag{22}
$$

**(21)** 化为标准二阶锥：引入辅助变量 $t_i,s_i$，

$$
\bigl\lVert \mathbf{J}_S f(\mathbf{z}_i)\bigr\rVert  \le t_i,
\qquad
\bigl\lVert \mathbf{J}_A f(\mathbf{z}_i)\bigr\rVert  \le s_i,
\qquad
t_i + s_i \le K.
\tag{23}
$$

**(22)** 含**锥的补集** $\lVert \mathbf{J}_S\rVert \ge r_i$，非凸。引入辅助 $r_i$ 后写为

$$
\bigl\lVert \mathbf{J}_S f(\mathbf{z}_i)\bigr\rVert  \ge r_i,
\tag{24}
$$

沿用 [Lipman 2012] 的 **frame**：取单位向量 $\mathbf{d}_i$，用半空间

$$
\mathbf{J}_S f(\mathbf{z}_i)^\top \mathbf{d}_i \ge r_i
\tag{25}
$$

凸化内接于 (24) 的锥补（见论文插图：$\mathbf{d}_i$ 张成的半平面落在锥补内）。将 (22) 替换为

$$
\mathbf{J}_S f(\mathbf{z}_i)^\top \mathbf{d}_i - s_i \ge \frac{1}{K}.
\tag{26}
$$

（此处 $r_i$ 冗余。）该约束同时迫使 $\det J_f>0$。

每步 SOCP 后，为让下一半平面尽可能远离当前 $\mathbf{J}_S$，更新

$$
\mathbf{d}_i = \frac{\mathbf{J}_S f(\mathbf{z}_i)}{\bigl\lVert \mathbf{J}_S f(\mathbf{z}_i)\bigr\rVert }.
\tag{27}
$$

**初始化**：交互从静止姿态开始，各点 Jacobian 为恒等，取 $\mathbf{d}_i=(1,0)^\top$ 即可使平凡解可行；软手柄能量 (29) 保证 SOCP 始终有解。

### 7.2 共形约束（式 (28)）

共形情形用 frame 形式（与 Lipman 2012 同型，记号与本文一致）：

$$
\bigl\lVert \mathbf{J}_A f(\mathbf{z}_i)\bigr\rVert 
\le \frac{K-1}{K+1}\,\mathbf{J}_S f(\mathbf{z}_i)^\top \mathbf{d}_i,
\tag{28a}
$$

$$
\bigl\lVert \mathbf{J}_A f(\mathbf{z}_i)\bigr\rVert 
\le \mathbf{J}_S f(\mathbf{z}_i)^\top \mathbf{d}_i - \delta.
\tag{28b}
$$

### 7.3 位置能量 $E_{\mathrm{pos}}$（式 (29)(30)）

优化问题 (18) 的第一项是**位置能量** $E_{\mathrm{pos}}(f)$，使映射在**手柄点** $\{\mathbf{p}_\ell\}_{\ell=1}^{n_\ell}$ 上接近目标位置 $\{\mathbf{q}_\ell\}_{\ell=1}^{n_\ell}$。代入式 (1)：

$$
E_{\mathrm{pos}}(f)
= \sum_{\ell=1}^{n_\ell} \bigl\lVert f(\mathbf{p}_\ell) - \mathbf{q}_\ell\bigr\rVert _2
= \sum_{\ell=1}^{n_\ell} \left\lVert 
\sum_{i=1}^{n} \mathbf{c}_i\,\varphi_i(\mathbf{p}_\ell) - \mathbf{q}_\ell
\right\rVert _2.
\tag{29}
$$

这是对每个手柄的**欧氏距离**求和（$\mathbb{R}^2$ 上的 $\ell_2$ 范数再对 $\ell$ 求和），**不是**坐标分量上的 $\ell_1$ 范数。

**为何用 (29) 而非常见的二次能量** $\sum_\ell \lVert f(\mathbf{p}_\ell)-\mathbf{q}_\ell\rVert _2^2$？

| 能量 | 形式 | 与 SOCP 的关系 |
| :--- | :--- | :--- |
| **式 (29)** | $\sum_\ell \lVert \cdot\rVert _2$ | 引入辅助变量 $r_\ell$ 后，$\lVert f(\mathbf{p}_\ell)-\mathbf{q}_\ell\rVert _2\le r_\ell$ 是**标准二阶锥约束** |
| **二次** | $\sum_\ell \lVert \cdot\rVert _2^2$ | 对 $\mathbf{C}$ 是**纯二次**目标（QP）；也可放进 SOCP（旋转锥 / 等价二次项），但不如 (29) 与畸变锥约束**同型** |

最小化 (29) 等价于

$$
\min_{\mathbf{C},\,\{r_\ell\}} \;\sum_{\ell=1}^{n_\ell} r_\ell
\quad\text{s.t.}\quad
\left\lVert 
\sum_{i=1}^{n} \mathbf{c}_i\,\varphi_i(\mathbf{p}_\ell) - \mathbf{q}_\ell
\right\rVert _2 \le r_\ell,\;\forall \ell.
\tag{30}
$$

这是**线性目标 + 二阶锥约束** → 与 §7 中畸变约束一起构成**同一个 SOCP**。交互时手柄过紧、畸变界 $K$ 过小会导致 (30) 与畸变锥冲突——软约束 (29) 允许 SOCP **始终可行**（手柄暂时"拖不动"），优于硬等式 $f(\mathbf{p}_\ell)=\mathbf{q}_\ell$。

**硬约束变体**：若要求 $f(\mathbf{p}_\ell)=\mathbf{q}_\ell$ 精确成立，对线性基这是 $\mathbf{C}$ 上的**线性等式**（每个手柄 2 个方程），可与 SOCP 不等式约束联立；交互中更常用软能量 (29)。

---

## 8. 优化问题与 Active Set 算法

原无限维问题 (1)(2) 在 §7 离散为 **(18)**。交互实现中，每轮只在 **active set** $\bar{\mathcal{Z}}\subseteq\mathcal{Z}$ 上施加畸变锥 (23)(26) 或 (28)，而非全体配准点。正则项 $E_{\mathrm{reg}}$ 取双调和与 ARAP 的凸组合（论文默认）：

$$
E_{\mathrm{reg}}(f) = E_{\mathrm{bh}}(f) + \lambda\, E_{\mathrm{arap}}(f).
$$

### 8.1 双调和能量 $E_{\mathrm{bh}}$（式 (31)）

**双调和能量**惩罚 Hessian 的 Frobenius 范数，使映射尽量**光滑**（类似薄板样条 / 双调和插值的平面版）：

$$
E_{\mathrm{bh}}(f) = E_{\mathrm{bh}}(u,v)
= \iint_{\Omega} \bigl(\lVert H_u(\mathbf{x})\rVert _F^2 + \lVert H_v(\mathbf{x})\rVert _F^2\bigr)\, dA,
\tag{31}
$$

其中 $H_u,H_v$ 为 $u,v$ 的 Hessian。对式 (1)，$u=\sum_i c_i^{(u)}\varphi_i$，故

$$
H_u = \sum_{i=1}^{n} c_i^{(u)}\, H_{\varphi_i},\qquad
H_v = \sum_{i=1}^{n} c_i^{(v)}\, H_{\varphi_i},
$$

$H_{\varphi_i}$ 可**预计算**（与 $\mathbf{C}$ 无关）。代入 (31) 后，被积函数对 $\mathbf{c}_i=(c_i^{(u)},c_i^{(v)})$ 是**二次型**；用数值求积（配准网格或高斯积分点）离散为

$$
E_{\mathrm{bh}}(f) \approx \mathbf{c}^\top A_{\mathrm{bh}}\,\mathbf{c},
$$

$\mathbf{c}$ 为所有系数拉成的向量，$A_{\mathrm{bh}}\succeq 0$。**纯二次、凸**，与 SOCP 目标线性项可合并为 SOCP 的二次锥部分或单独作为 QP 子项。

### 8.2 ARAP 能量 $E_{\mathrm{arap}}$ 与 frame 二次化（式 (32)(33)）

**ARAP（As-Rigid-As-Possible）** 在预采样点 $\{\mathbf{r}_s\}_{s=1}^{n_s}$ 上要求 Jacobian 接近**旋转矩阵**：

$$
E_{\mathrm{arap}}(f)
= \sum_{s=1}^{n_s} \bigl\lVert J_f(\mathbf{r}_s) - Q(\mathbf{r}_s)\bigr\rVert _F^2,
\tag{32}
$$

其中 $Q(\mathbf{r}_s)\in SO(2)$ 为 $J_f(\mathbf{r}_s)$ 的**最近旋转**（极分解去剪切部分）。因 $Q$ 依赖 $J_f$ 而 $J_f$ 又依赖 $\mathbf{C}$，(32) 对 $\mathbf{C}$ **非凸**；经典做法为 [Liu et al. 2008] / [Sorkine & Alexa 2007] 的 **local-global** 交替：

1. **Local**：固定 $J_f$，更新 $Q_s\leftarrow \mathrm{polar}(J_f(\mathbf{r}_s))$；
2. **Global**：固定 $\{Q_s\}$，对 $\mathbf{C}$ 解**二次**最小二乘。

在 Provably Good 框架中，$Q_s$ 用与畸变约束相同的 **frame** $\mathbf{d}_s$ 构造（论文式 (27) 在采样点 $\mathbf{r}_s$ 上更新），使 (32) 在每一步 SOCP 内化为**对 $\mathbf{C}$ 的二次泛函**：

$$
E_{\mathrm{arap}}(f)
= \sum_{s=1}^{n_s} \bigl\lVert J_f(\mathbf{r}_s) - F_s\bigr\rVert _F^2,
\tag{33}
$$

其中 $F_s\in\mathbb{R}^{2\times 2}$ 由 frame $\mathbf{d}_s$ 确定的**固定**目标矩阵（相似 + 反相似模板的线性组合，与 §3.1 的 $J_s,J_a$ 分解一致）。展开：

$$
J_f(\mathbf{r}_s)=\sum_{i=1}^{n}\mathbf{c}_i\,\nabla\varphi_i(\mathbf{r}_s)^\top
\quad\text{（按列堆叠梯度）},
\qquad
\lVert J_f-F_s\rVert _F^2 = \mathrm{tr}\bigl((J_f-F_s)^\top(J_f-F_s)\bigr),
$$

对 $\mathbf{C}$ 为 $\lVert \mathbf{C} G_s - F_s\rVert _F^2$ 型二次项（$G_s$ 为基梯度在 $\mathbf{r}_s$ 的矩阵）。故 **(33) 在固定 frame 下是凸二次能量**，可写入 SOCP 的二次目标或与双调和项共用 $A_{\mathrm{reg}}$。

| 能量 | 对 $\mathbf{C}$ | 作用 |
| :--- | :--- | :--- |
| $E_{\mathrm{bh}}$ (31) | 二次、凸 | 整体光滑、抑制振荡 |
| $E_{\mathrm{arap}}$ (32) | 非凸（若 $Q$ 自由） | 局部刚体、保形感 |
| $E_{\mathrm{arap}}$ (33) | 二次（frame 固定） | 嵌入 SOCP 迭代，与 Lipman 2012 一脉 |

$\lambda$ 权衡光滑（双调和）与局部刚性（ARAP）；交互变形常取较小 $\lambda$，以手柄 (29) 与畸变界 $K$ 为主。

### 8.3 Active Set 更新（交互关键）

配准点布在均匀矩形网格上。每步：

1. 计算所有 $\mathbf{z}\in\mathcal{Z}$ 的 $D(f;\mathbf{z})$；
2. 找畸变的**局部极大**；若 $D(\mathbf{z})>K_{\text{on}}$（如 $K_{\text{on}}=0.1+0.9K$），将 $\mathbf{z}$ 加入 $\bar{\mathcal{Z}}$；
3. 若 $D(\mathbf{z})<K_{\text{off}}$（如 $0.5+0.5K$），从 $\bar{\mathcal{Z}}$ 移除；
4. 保留少量均匀分布的**常驻**配准点以防手柄快速移动时约束突变。

实践中每步仅激活少量孤立点（图 3A–3C：杆弯曲时激活点防止塌陷；去掉约束则出现奇点）。对 active 点解 SOCP（MOSEK 等内点法），复杂度随 $|\bar{\mathcal{Z}}|$ 近线性（论文图 7）。

### 8.4 Algorithm 1：Provably Good Planar Mapping（论文流程）

下面把论文 Algorithm 1 用本文记号重写（$Z'$ 对应 active set，$Z''$ 对应常驻点；阈值采用 $K_{\text{high}},K_{\text{low}}$）。

```text
Algorithm 1  Provably good planar mapping

Input:
  Positional constraints {p_l}_{l=1}^{n_l}, {q_l}_{l=1}^{n_l}
  Basis functions ϕ_i ∈ 𝓕
  Collocation grid Z = {z_j}_{j=1}^{m}
  Distortion type (isometric / conformal) and bound K ≥ 1

Output:
  Deformation f

Initialization:
  if first step then
    Precompute ϕ_i(z), ∇ϕ_i(z),  ∀z∈Z, ∀i
    Set frame directions d_j ← (1, 0), ∀z_j∈Z
    Initialize empty active set Z' ← ∅
    Initialize persistent set Z'' by farthest-point sampling
  end if

Active-set update:
  Evaluate distortion D(z),  ∀z∈Z
  Find local maxima set Z_max of D(z)
  for each z ∈ Z_max with D(z) > K_high do
    Insert z into Z'
  end for
  for each z ∈ Z' with D(z) < K_low do
    Remove z from Z'
  end for

Optimization:
  Solve (18) (SOCP) for coefficients c on points Z' ∪ Z'':
    - Isometric case: constraints (23) + (26)
    - Conformal case: constraints (28a)(28b)
    - Energies: (30), (31), and/or (33)

Postprocessing:
  Compute f from c and basis 𝓕
  Update frames d_j using (27)

Return:
  Deformation f
```

与 §8.3 的关系：$Z'$ 是随畸变峰值动态变化的约束点集，$Z''$ 是防止快速拖拽时约束退化的常驻点集；两者并集进入同一个 SOCP。

---

## 9. 算例与对比

### 9.1 椭圆投影式子问题（与 KKT 笔记的联系）

把点 $\mathbf{p}$ 投影到椭圆 $\{(x_1/a)^2+(x_2/b)^2\le 1\}$ 可视为 $\min \frac12\lVert \mathbf{x}-\mathbf{p}\rVert ^2$ s.t. 凸不等式——见 [凸优化与 KKT 条件](../6.附录-数值计算与最优化/2019-07-14-凸优化与KKT条件.md) 例 3。Provably Good 框架把类似**凸约束**搬到每个配准点的 Jacobian 上，再传播到全域。

### 9.2 论文实验摘要

| 实验 | 设置 | 现象 |
| :--- | :--- | :--- |
| **B-Spline 杆**（图 5） | $6\times 6$ 均匀三次 B 样条，$E_{\mathrm{bh}}+\lambda E_{\mathrm{arap}}$ | 无约束时出现两个奇点；$K=2,3,4$ 时策略 3 用 $3000$ 网格认证全域畸变 |
| **TPS 方块**（图 8） | 25 基、中间两点旋转 | 无约束子方块 fold-over 消失；$K=5$ 需 $\approx 6000$ 点认证 |
| **鸟图**（图 9） | meshless ARAP ± 畸变约束 | Photoshop ARAP 在手柄处尖点折叠；光滑基无约束仍 fold；加约束后双射 |
| **圆盘**（图 10） | vs Schüller 2013、Lipman 2012 | 网格法保证单射但不够光滑；本文同样 $D_{\text{iso}}\le 5$ 且更光滑 |
| **Shape-aware Gaussian**（图 11） | 40 个高斯、$K=3$ | vs Schüller：手柄处无尖点 |

---

## 10. 小结

| 概念 | 作用 |
| :--- | :--- |
| 线性空间 (1) | B-Spline / TPS / Gaussian；$J_f$ 对系数仿射 |
| 配准点 $\mathcal{Z}$、active set $\bar{\mathcal{Z}}$ | 稀疏凸约束；交互时可变 |
| 奇异值 $\Sigma,\sigma$；(19)(20) | $D_{\text{iso}}, D_{\text{conf}}$；$\mathbf{J}_S,\mathbf{J}_A$ 分解 |
| 连续性模 (6)(7)、(8)(9) | Lemma 2：梯度模 → 奇异值 $2\omega$ |
| 填充距离 $h$ (5)、全域界 (11)(13) | Lemma 1：离散 → 全域 |
| 策略 (14)–(17) | 认证 / 加密 $h$ / 反推 $K$ |
| SOCP (18)(23)(26)、frame (25)(27) | Lipman 2012 凸化搬到 meshless |
| 共形锥 (28a)(28b) | 共形 active 约束 |
| $E_{\mathrm{pos}}$ (29)(30) | 手柄：$\sum\lVert \cdot\rVert _2$ + 辅助 $r_\ell$，与畸变锥同型 |
| $E_{\mathrm{bh}}, E_{\mathrm{arap}}$ (31)(33) | 正则：双调和二次 + frame 二次化 ARAP |
| 策略 1–3 | 认证 / 加密 / 反推 $K$ |

**局限**：基需已知 $\omega_{\nabla\varphi}$；非凸域可用欧氏距离版分析；3D 推广见 Lipman 后续工作（有界畸变调和映射、3D 单射映射等）。

**相关笔记**：[MLS / 梯度域变形](几何变形.md)、[AKAP 平面变形](AKAF.md)、[AQP](../../1.Parameterization/2.几何优化方法/2018-01-03-加速二次代理-AQP.md)、[SLIM](../../1.Parameterization/2.几何优化方法/2018-01-02-可扩展局部单射映射-SLIM.md)、[TinyAD](几何优化-TinyAD.md)（可微能量原型）、[凸优化与 KKT](../6.附录-数值计算与最优化/2019-07-14-凸优化与KKT条件.md)。

---

## 参考文献

- Poranne R., Lipman Y. *Provably good planar mappings*. SIGGRAPH 2014. [DOI](https://doi.org/10.1145/2601097.2601123)
- Lipman Y. *Bounded distortion harmonic mappings in the plane*. SIGGRAPH 2015. [DOI](https://doi.org/10.1145/2766989)
- Lipman Y. *Bounded distortion mapping spaces for triangular meshes*. SIGGRAPH 2012. [DOI](https://doi.org/10.1145/2185520.2185604)
- Schüller C., et al. *Locally injective mappings*. SGP 2013.
- Solomon J., et al. *As-Killing-As-Possible vector fields for planar deformation*. SIGGRAPH 2011.
- Liu S., et al. *A local-global approach to mesh parameterization*. SIGGRAPH 2008.
- Sorkine O., Alexa M. *As-rigid-as-possible surface modeling*. SGP 2007.
