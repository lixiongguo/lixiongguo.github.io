---
layout: post
title: "二次代价与Brenier定理"
category: Parameterization
categories: ["Parameterization", "Parameterization-OptimalTransport"]
---

针对最重要的**二次代价函数** $c(x,y) = \frac{1}{2}\lVert x - y\rVert ^2$，Brenier 给出了最优传输映射的显式结构：

 **Brenier 定理**：对于绝对连续的 $\mu$（$\mu \ll \mathcal{L}^d$），二次代价下的最优传输映射 $T$ 存在且唯一，且可表示为某个凸函数 $\phi$ 的梯度：

$$
 T(x) = \nabla \phi(x), \quad \phi \text{ 是凸函数}
$$

 这个凸函数 $\phi$ 称为 **Brenier 势（Brenier Potential）**。

令 $\phi$ 为 Brenier 势（凸函数），则最优传输映射为

$$
T(x) = \nabla \phi(x).
$$

而 Kantorovich 势对 $(\phi_K, \psi_K)$ 可取为

$$
\phi_K(x) = \phi(x) - \frac{1}{2}\lVert x\rVert ^2, 
\psi_K(y) = \phi^*(y) - \frac{1}{2}\lVert y\rVert ^2,
$$

其中 $\phi^*$ 是 $\phi$ 的凸共轭（Legendre-Fenchel 变换）。由于

$$
c(x,y) = \frac{1}{2}\lVert x-y\rVert ^2 = \frac{1}{2}\lVert x\rVert ^2 - \langle x, y \rangle + \frac{1}{2}\lVert y\rVert ^2,
$$

在最优传输对上 $\phi(x) + \phi^*(y) = \langle x, y \rangle$，从而

$$
\phi_K(x) + \psi_K(y) = -\langle x, y \rangle = -c(x,y) + \frac{1}{2}\lVert x\rVert ^2 + \frac{1}{2}\lVert y\rVert ^2.
$$

（符号取决于对偶形式约定；与正文 $\phi(x)+\psi(y)\leq c(x,y)$ 的约定差一个 $\frac{1}{2}\lVert x\rVert ^2+\frac{1}{2}\lVert y\rVert ^2$ 的平移。）

**注**：在二次代价下，若 $\phi$ 是 Brenier 势，则其凸共轭 $\phi^*$ 就是对应的 Kantorovich 势 $\psi$，且在最优传输对上满足

$$
\phi(x) + \phi^*(y) = \langle x, y \rangle.
$$



## Monge-Ampère 方程

推前条件 $T_{\#}\mu = \nu$ 在 $T = \nabla \phi$ 下可写为：

$$
\nu(\nabla\phi(x)) \cdot \det(D^2\phi(x)) = \mu(x)
$$

这个非线性二阶偏微分方程就是 **Monge–Ampère 方程**，它是最优传输理论和保面积参数化的核心方程。

综上，二次代价下的最优传输问题可归结为, 存在唯一的凸函数 $\phi$（Brenier 势），使得：

 - $T = \nabla \phi$ 是唯一的最优传输映射
 - $\phi$ 满足 Monge-Ampère 方程 $\det(D^2\phi) \cdot \nu(\nabla\phi) = \mu$
 - $\phi^*$（$\phi$ 的凸共轭）是 Kantorovich 对偶问题的解

![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250928212316955.png)

*由 $c(x,y)=\frac{1}{2}\lVert x-y\rVert ^2$ 展开，Kantorovich 势取 $\tilde\phi(x)=\phi(x)-\frac{1}{2}\lVert x\rVert ^2$、$\tilde\psi(y)=\phi^*(y)-\frac{1}{2}\lVert y\rVert ^2$，满足 $\tilde\phi(x)+\tilde\psi(y)=\langle x,y\rangle$ 于最优对上。

![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250928212149743.png)

**最终公式（二次代价下）**：用源空间 Kantorovich 势 $\phi_K$ 表示传输映射

$$
\boxed{T(x) = x + \nabla \phi_K(x)}
$$

其中 $\phi_K(x) = \phi(x) - \frac{1}{2}\lVert x\rVert ^2$ 是定义在源空间上的 Kantorovich 势。这与 $T(x)=\nabla\phi(x)$ 等价，因为 $\nabla\phi(x) = x + \nabla\phi_K(x)$。



## 扭曲条件（Twist Condition）

对于更一般的代价函数 $c(x,y)$，Brenier 结论的推广需要所谓的**扭曲条件**：

 **定义（Twist Condition）**：代价函数 $c$ 满足扭曲条件，若映射：
$$
 y \mapsto \nabla_x c(x,y)
$$
 对每个固定的 $x$ 是单射。

这也意味着在最优传输中，$\nabla_x c(x,y)$ 唯一确定了 $y$，从而保证了传输映射 $T$ 的存在性：

$$
T(x) = \arg\min_y \left[ c(x,y) - \psi(y) \right] \quad \text{或等价地} \quad T(x) = \nabla c(x, \cdot)^{-1}(\nabla \phi(x))
$$

*图：一般代价下，Kantorovich 势与传输映射满足*
$$
\boxed{\nabla_x \phi(x) = -\nabla_x c(x, T(x))}
$$

其中 $\phi$ 是 Kantorovich 势（源空间侧）。

*图：**例子**——若 $c(x,y)=\frac{1}{2}\lVert x-y\rVert ^2$，则 $\nabla_x c = x-y$，代入得*

$$
\nabla \phi(x) = -(x - T(x)) \quad \Longrightarrow \quad T(x) = x + \nabla \phi(x),
$$

与 Brenier 一节中 $T(x)=x+\nabla\phi_K(x)$ 一致（此时 $\phi_K = \phi - \frac{1}{2}\lVert x\rVert ^2$）。

---



**概念小结**：$c$-变换与 $c$-上微分构成最优传输对偶理论的两根支柱——

| 概念                                    | 作用                                             | 二次代价下的对应                  |
| :-------------------------------------- | :----------------------------------------------- | :-------------------------------- |
| **$c$-变换** $\psi^c(x)$            | 由卖出价 $\psi$ 确定买入价；化简对偶为单势函数 | Legendre-Fenchel 共轭             |
| **$c$-上微分** $\partial^c \psi(x)$ | 确定 $x$ 应运往哪些 $y$；刻画最优配对        | 凸函数次微分 $\partial \phi(x)$ |
| **$c$-循环单调性**                    | 最优计划的充要条件                               | 单调映射的图                      |

Kantorovich 势可视作"价格函数"——类似于物理中"力是势能的负梯度"，**传输方向由 $c$-上微分（或 Brenier 势的梯度）决定**：

$$
x \xrightarrow{\;T\;} y \in \partial^c \psi(x),  T(x) = \nabla \phi(x) \;\text{（二次代价）}.
$$

