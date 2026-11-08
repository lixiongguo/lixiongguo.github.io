---
layout: post
title: "Monge问题与Kantorivch问题"
category: Parameterization
categories: ["Parameterization", "Parameterization-OptimalTransport"]
---

最优传输问题源于法国数学家 **Gaspard Monge** 于 1781 年提出的"**堆土问题**"：如何将一堆土以最小总代价搬运到指定位置，形成目标土堆。其核心是寻找一个将源分布映射到目标分布的最优方案。20 世纪 40 年代，**Kantorovich** 将问题松弛为联合分布上的线性规划，奠定了最优传输的现代数学基础，并因此获得 1975 年诺贝尔经济学奖。如今，最优传输广泛应用于计算机图形学、图像处理、机器学习、经济均衡分析等领域。

## Monge问题与Kantorivch问题

**Monge 问题（原始形式）**：给定两个概率测度 $\mu$（定义在 $X$ 上）和 $\nu$（定义在 $Y$ 上），以及代价函数 $c(x,y)$（表示将单位质量从 $x$ 运到 $y$ 所需的代价），求映射 $T: X \to Y$ 使得：
$$
 \min_{T} \int_X c(x, T(x)) \, d\mu(x) \quad \text{s.t.} \quad T_{\#}\mu = \nu
$$

其中 $T_{\#}\mu = \nu$ 是**推前（push-forward）条件**，即对任意可测集 $B \subseteq Y$：
$$
 \nu(B) = \mu(T^{-1}(B))
$$

Monge 问题的本质困难在于：$T$ 必须是**映射**（每个 $x$ 只能映射到唯一一个 $y$），这意味着质量不允许分裂。这导致问题**非凸且可能无解**。

 **Kantorovich 问题**：将映射要求放宽为**传输计划（transport plan）** $\pi$——一个定义在乘积空间 $X \times Y$ 上的联合概率测度。$\pi(x,y)$ 表示从 $x$ 运往 $y$ 的质量份额：

$$
 \min_{\pi \in \Pi(\mu,\nu)} \int_{X \times Y} c(x,y) \, d\pi(x,y)
$$

 其中 $\Pi(\mu,\nu)$ 是所有边缘分布分别为 $\mu$ 和 $\nu$ 的联合概率测度的集合：
$$
\Pi(\mu,\nu) = \left\{ \pi \mid \pi_x = \mu,\; \pi_y = \nu \right\}
$$

### Kantorovich 对偶(DP)

线性规划自然引出对偶问题。对偶变量的经济解释为"价格函数"——$\phi(x)$ 是在 $x$ 处买入的价格，$\psi(y)$ 是在 $y$ 处卖出的价格。无套利条件要求 $\phi(x) + \psi(y) \leq c(x,y)$（否则可在 $x$ 买入、在 $y$ 卖出套利）。

 **对偶问题（Kantorovich Duality）**：

$$
\min_{\pi \in \Pi(\mu,\nu)} \int c \, d\pi \;=\; \sup_{(\phi,\psi)} \left\{ \int_X \phi \, d\mu + \int_Y \psi \, d\nu \;\mid\; \phi(x) + \psi(y) \leq c(x,y) \right\}
$$

其中满足不等式约束的函数对 $(\phi,\psi)$ 称为 （Kantorovich Potential）,$\psi$ 可通过 $c$-变换由 $\phi$ 确定。

**Kantorovich 势**也称为"**影子价格**"：在最优传输的经济解释中，$\phi(x)$ 代表产地 $x$ 的资源"出厂价"，$\psi(y)$ 代表消费地 $y$ 的"收货价"。约束 $\phi(x) + \psi(y) \leq c(x,y)$ 意味着买入价与卖出价之差不高于运输成本，若差价高于运费，商人可倒卖牟利。当等号成立时，价格场 $(\phi,\psi)$ 达到均衡，此时对偶目标 $\int \phi d\mu + \int \psi d\nu$ 达到最大的社会总剩余，而最优传输计划正是由这些均衡价格导出的资源配置。

## $c$-变换与Legredre变换

 **定义（$c$-变换）**：给定函数 $\psi: Y \to \mathbb{R}$，其 $c$-变换定义为：

$$
 \psi^c(x) = \inf_{y \in Y} \left[ c(x,y) - \psi(y) \right]
$$

 类似地，$\phi$ 的 $c$-变换为：
$$
\phi^c(y) = \inf_{x \in X} \left[ c(x,y) - \phi(x) \right]
$$

对固定的 $x$ $y \mapsto c(x,y) - \psi(y)$ 的下确界

**$c$-凹性（$c$-concavity）**：若 $c$ 连续，则 $\psi^c$ 是 **$c$-凹函数**——即 $-\psi^c$ 是 $c$-凸函数。直观地说，$c$-变换把任意函数"投影"到满足对偶结构的 $c$-凹函数类中。

原始对偶需要在所有函数对 $(\phi, \psi)$ 中搜索。利用 $c$-变换，**问题可化为仅含一个势函数**：

$$
\min_{\pi \in \Pi(\mu,\nu)} \int c \, d\pi
= \sup_{\psi: Y \to \mathbb{R}} \left\{ \int_X \psi^c \, d\mu + \int_Y \psi \, d\nu \right\}
$$

等价地，也可只用 $\phi: X \to \mathbb{R}$ 表述：

$$
= \sup_{\phi: X \to \mathbb{R}} \left\{ \int_X \phi \, d\mu + \int_Y \phi^c \, d\nu \right\}.
$$

**证明思路**：给定任意可行对 $(\phi, \psi)$ 满足 $\phi(x)+\psi(y)\leq c(x,y)$，令 $\tilde\psi = \psi$、$\tilde\phi = \phi^c$，则 $(\tilde\phi, \tilde\psi)$ 仍可行且目标值不变或更大（因为 $\phi \leq \phi^{cc}$）。因此最优解总可取为 **$c$-共轭对** $(\phi, \phi^c)$ 或 $(\psi^c, \psi)$。

在最优解处，Kantorovich 势满足 **$c$-共轭关系** $\phi = \psi^c$、$\psi = \phi^c$（差一个常数不影响目标值）。

#### 二次代价下的 $c$-变换

当代价 $c(x,y) = \frac{1}{2}\lVert x-y\rVert ^2 = \frac{1}{2}\lVert x\rVert ^2 + \frac{1}{2}\lVert y\rVert ^2 - \langle x, y \rangle$ 时，

$$
\psi^c(x) = \frac{1}{2}\lVert x\rVert ^2 + \inf_{y \in Y} \left\{ \frac{1}{2}\lVert y\rVert ^2 - \psi(y) - \langle x, y \rangle \right\}.
$$

若令凸函数 $\bar\psi(y) = \frac{1}{2}\lVert y\rVert ^2 - \psi(y)$，则

$$
\psi^c(x) = \frac{1}{2}\lVert x\rVert ^2 - \psi^*(x),
$$

其中 $\psi^*$ 是经典的 Legendre-Fenchel  变换。

#### 内积代价与 Legendre 变换

**定义（Legendre-Fenchel 变换）**：对函数 $f: \mathbb{R}^d \to \mathbb{R} \cup \{+\infty\}$，其凸共轭 $f^*$ 定义为
$$
f^*(y) = \sup_{x \in \mathbb{R}^d} \left[ \langle x, y \rangle - f(x) \right].
$$

若 $f$ 为凸下半连续函数，则 $f^{**} = f$，即 Legendre 变换是对合。

当代价函数为内积 $c(x,y) = \langle x, y \rangle$ 时，$c$-变换退化为 Legendre 变换的负号版本：

$$
\psi^c(x) = \inf_{y} \left[ \langle x, y \rangle - \psi(y) \right], \qquad 
\phi^*(y) = \sup_{x} \left[ \langle x, y \rangle - \phi(x) \right],
$$

即 $\phi^* = (-\phi)^c$。此时 $c$-上微分还原为次微分 $\partial^c \phi(y) = \partial \phi^*(y)$，约束 $\phi(x) + \psi(y) \leq \langle x, y \rangle$ 等价于 Fenchel 不等式 $\psi(y) \leq \phi^*(y)$，最优解处 $\psi = \phi^*$。

二次代价可通过展开化为内积形式：
$$
c(x,y) = \frac{1}{2}\lVert x-y\rVert ^2 = \frac{1}{2}\lVert x\rVert ^2 - \langle x, y \rangle + \frac{1}{2}\lVert y\rVert ^2.
$$

**Voronoi 与 Delaunay 作为 Legendre 对偶**：给定带权点 $(x_i, w_i)$，power 距离为 $\lVert x - x_i\rVert ^2 - w_i = \lVert x\rVert ^2 - 2\langle x, x_i \rangle + \lVert x_i\rVert ^2 - w_i$。令 $\varphi_i = \tfrac{1}{2}(\lVert x_i\rVert ^2 - w_i)$，定义分段线性凸函数
$$
f(x) = \max_i \left[ \langle x, x_i \rangle - \varphi_i \right],
$$

则 power 图（加权 Voronoï）即为 $f$ 的次微分区域划分，而 regular 三角剖分（加权 Delaunay）为升维点 $(x_i, \varphi_i)$ 的下凸包。两者通过 Legendre-Fenchel 对偶互为对偶——与半离散最优传输中 Brenier 势通过 Legendre 变换导出 power 图的结构完全一致。

<img src="https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20260606120106524.png" alt="image-20260606120106524" style="zoom:50%;" />

## $c$-上微分（$c$-superdifferential）

$c$-变换刻画了"价格"之间的对偶关系；**$c$-上微分**则刻画在最优解处"谁与谁配对运输"——它是次微分（subdifferential）概念在一般代价下的推广。

给定函数 $\psi: Y \to \mathbb{R}$（Kantorovich 对偶中 $Y$ 侧的势），点 $x \in X$ 处的 **$c$-上微分** 定义为：

$$
\partial^c \psi(x) := \left\{ y \in Y \;\middle|\; \psi^c(x) + \psi(y) = c(x, y) \right\}.
$$

等价地，$y \in \partial^c \psi(x)$ 当且仅当 $y$ 达到 $c$-变换中的下确界：

$$
\psi^c(x) = c(x, y) - \psi(y) = \inf_{y' \in Y} \left[ c(x, y') - \psi(y') \right].
$$

对称地，对 $c$-凹函数 $\psi: X \to \mathbb{R}$，定义

$$
\partial^c \psi(y) := \left\{ x \in X \;\middle|\; \psi(x) + \psi^c(y) = c(x, y) \right\}.
$$

$\partial^c \psi(x)$ 是使不等式 $\psi^c(x) + \psi(y) \leq c(x,y)$ **取等号**的所有目标点 $y$。

#### 与最优传输映射的关系

若 Kantorovich 势 $\psi$ 达到对偶问题的上确界，且 Monge 映射 $T$ 存在，则对 $\mu$-几乎处处的 $x$ 有

$$
T(x) \in \partial^c \psi(x).
$$

在 **twist 条件**（$y \mapsto \nabla_x c(x,y)$ 对每个 $x$ 单射）下，$\partial^c \psi(x)$ 至多含一个点，从而 $T(x) = \nabla_x c(x, y)\big|_{y = T(x)}$ 唯一确定——这正是扭曲条件一节中公式

$$
T(x) = \arg\min_y \left[ c(x,y) - \psi(y) \right]
$$

的集合版本。

#### 二次代价：$c$-上微分 = 凸函数次微分

当 $c(x,y) = \frac{1}{2}\lVert x-y\rVert ^2$ 且 $\phi = \psi^c$ 为 Brenier 凸势时，条件 $\psi^c(x) + \psi(y) = c(x,y)$ 化为

$$
\phi(x) + \psi(y) = \frac{1}{2}\lVert x\rVert ^2 + \frac{1}{2}\lVert y\rVert ^2 - \langle x, y \rangle.
$$

令 $\bar\phi(x) = \phi(x) - \frac{1}{2}\lVert x\rVert ^2$、$\bar\psi(y) = \frac{1}{2}\lVert y\rVert ^2 - \psi(y)$（均为凸函数），则取等号等价于

$$
\bar\phi(x) + \bar\psi(y) = \langle x, y \rangle,
$$

即 $y \in \partial \bar\phi(x)$（$\bar\phi$ 的次微分）且 $x \in \partial \bar\psi(y)$。因此

$$
\partial^c \psi(x) = \partial \bar\phi(x),  T(x) = \nabla \bar\phi(x) = \nabla \phi(x)
$$

在 $\bar\phi$ 可微的点处退化为梯度映射。不可微点处，次微分是多值的，对应质量分裂的 Kantorovich 计划。



#### 半离散情形：Laguerre 单元

在半离散 OT 中，目标测度 $\nu = \sum_j \lambda_j \delta_{y_j}$，势函数 $\psi(y_j) = \psi_j$ 为有限维权重。此时

$$
\psi^c(x) = \min_j \left[ c(x, y_j) - \psi_j \right],
$$

而

$$
\partial^c \psi(x) = \arg\min_j \left[ c(x, y_j) - \psi_j \right]
$$

给出每个 $x$ 应被送往的目标点。对二次代价 $c(x,y) = \frac{1}{2}\lVert x-y\rVert ^2$，使下确界取到的 $j$ 构成 **Laguerre / Power 单元**：

$$
L_j(\psi) = \left\{ x \;\middle|\; \lVert x - y_j\rVert ^2 - \psi_j \leq \lVert x - y_k\rVert ^2 - \psi_k,\; \forall k \right\}.
$$

这正是半离散 OT 把连续域分割为加权 Voronoi 单元的几何来源——每个 cell 内所有点共享同一个 $c$-上微分（同一目标原子 $y_j$）。

#### $W_1$ 代价下的特化

当代价 $c(x,y) = \lVert x - y\rVert $ 时，$c$-变换给出

$$
\psi^c(x) = \inf_{y \in Y} \left[ \lVert x - y\rVert  - \psi(y) \right].
$$

此时 $\psi^c$ 自动 **1-Lipschitz**：对任意 $x, x'$，

$$
|\psi^c(x) - \psi^c(x')| \leq \lVert x - x'\rVert 
$$

（三角不等式直接推出）。Kantorovich-Rubinstein 对偶正是把一般对偶化简为单个 1-Lipschitz 函数 $f = -\psi^c$ 的情形——这也是 WGAN 中 critic 必须满足 Lipschitz 约束的来源。

---

## WGAN 与最优传输

WGAN（Arjovsky et al. 2017）是 Kantorovich 对偶在机器学习中最为人熟知的应用。原始 GAN 用 JS 散度度量分布距离，但两分布支撑不交时 JS 散度为常数 $\log 2$，梯度消失导致训练崩溃。WGAN 用 **Wasserstein-1 距离**替代 JS 散度：

$$
\boxed{W_1(P_r, P_g) = \min_{\pi \in \Pi(P_r,P_g)} \int \lVert x-y\rVert  \, d\pi(x,y)}
$$

### Kantorovich-Rubinstein 对偶形式

以上原始问题涉及高维耦合变量 $\pi$，难以直接计算。利用 Kantorovich 对偶（See §Kantorovich 对偶），当代价 $c(x,y) = \lVert x-y\rVert $ 时：

$$
\boxed{W_1(P_r, P_g) = \sup_{\lVert f\rVert _L \leq 1} \Big[ \mathbb{E}_{x\sim P_r}[f(x)] - \mathbb{E}_{x\sim P_g}[f(x)] \Big]}
$$

其中 $\lVert f\rVert _L \leq 1$ 表示 $f$ 是 1-Lipschitz 函数：$|f(x)-f(y)| \leq \lVert x-y\rVert $。推导来自一般对偶的化简——约束 $\phi(x)+\psi(y) \leq \lVert x-y\rVert $ 在 $W_1$ 代价下退化为 $\phi = -f,\; \psi = f$，且 $f$ 自动 1-Lipschitz。

WGAN 中的 **critic**（或 discriminator）$f_w$ 正是 Kantorovich 势在 KR 对偶中的化身：$f$ 最大化 $\mathbb{E}_{P_r}[f] - \mathbb{E}_{P_g}[f]$，其梯度指导生成器的更新方向。

### WGAN 与原始 GAN 的区别

| 维度 | 原始 GAN | WGAN |
|:---|:---|:---|
| 判别器 | 概率（sigmoid） | 标量分数（无激活） |
| 分布度量 | JS 散度 | $W_1$（Earth Mover's Distance） |
| Lipschitz | 无约束 | Weight Clip / Gradient Penalty / Spectral Norm |
| 梯度行为 | 支撑不交时消失 | 平滑、始终有意义 |
| 训练稳定性 | 差，易模式坍塌 | 显著改善 |

### 与最优传输理论的对应

| 最优传输 | WGAN |
|:---|:---|
| Monge 问题 | 生成器 $G: z \mapsto x$（决定性的推前映射） |
| Kantorovich 问题 | $W_1(P_r, P_g)$（Earth Mover's Distance） |
| Kantorovich 对偶 | $W_1 = \sup_{\lVert f\rVert _L \leq 1} \mathbb{E}_{P_r}[f] - \mathbb{E}_{P_g}[f]$ |
| Kantorovich 势 $\phi,\psi$ | Critic $f$ |
| 代价 $c(x,y)=\lVert x-y\rVert $ | 1-Wasserstein 距离的度量 |
| 1-Lipschitz 约束 | Weight Clip / Gradient Penalty / Spectral Norm |

> 生成器 $G(z)$ 天然是一个 **Monge 映射**——将低维噪声分布推前为数据分布。WGAN 用 Kantorovich 松弛度量该映射质量，用 critic 梯度改进映射。这是最优传输理论在深度学习中最直接的应用实例。
