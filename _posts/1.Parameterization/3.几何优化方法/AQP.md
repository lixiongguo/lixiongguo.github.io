---
layout: post
title: "1阶优化方法-SLIM和AQP"
category: Parameterization
categories: ["Parameterization", "Parameterization-GeometricOptimization"]
mathjax: true
---

## 概述

AQP（Accelerated Quadratic Proxy）针对大规模几何能量优化中的**病态性**与**收敛慢**问题，提出一种纯一阶加速算法。核心做法：

| 步骤       | 内容                                                         |
| :--------- | :----------------------------------------------------------- |
| **分解**   | $f = h + g$，$h(x)=\frac{1}{2}x^T H x$ 为 Laplacian 主导的严格凸二次项 |
| **预条件** | 每步在 Nesterov 外推点 $y_n$ 处，用 $h$ 作二次代理，解固定稀疏 KKT 系统 |
| **加速**   | 结合 Nesterov 动量，$\theta$ 由条件数 $\kappa(Q)$ 决定，实践中可取固定值 |

与 L-BFGS 相比，AQP 不存储多步历史、不需求 Hessian，只用到**前两步**的迭代结果；实验上迭代次数常少一个数量级以上。对 ARAP 能量，无加速版退化为 [Liu et al. 2008] 的 local/global 算法。

与 [SLIM](几何优化-SLIM.md) 的关系：二者都利用**二次代理**思想，但路线不同——SLIM 为 flip-preventing 能量设计**矩阵加权**代理 + 受限线搜索；AQP 将 Laplacian 二次项**全局**并入预条件，再叠加 Nesterov 加速，更适合 ARAP、ISO、CONF 等经典能量。

---

## 1. 问题设定

几何处理（变形、参数化、网格编辑）统一写成带线性约束的最小化：

$$
\min_{x \in \mathbb{R}^{dn}} f(x) \quad \text{s.t.} \quad Ax = b
$$

$x = \mathrm{vec}(X)$ 为 $d$ 维顶点矩阵 $X \in \mathbb{R}^{d \times n}$ 的列堆叠，$A$ 编码固定边界等位置约束。

**AQP 的关键分解**：

$$
f(x) = h(x) + g(x), \qquad h(x) = \frac{1}{2} x^T H x
$$

$H = L \otimes I_d$（Kronecker 积：Laplacian 对每个坐标分量独立作用，详见 §3.6），在 $\ker A$ 上严格正定；$g(x)$ 吸收全部非线性部分。

等价可分离形式：

$$
f(x) = \sum_{i=1}^m f_i(R_i x)
$$

$R_i$ 为极稀疏差分/Jacobian 选择矩阵，$f_i$ 为局部能量。**困难**：$f_i$ 常非凸；Newton 每步需变 Hessian，大规模不可行；L-BFGS 有改善但仍慢。

一阶迭代仅依赖两步历史：

$$
x_n = \mathcal{A}_\theta(x_{n-1}, x_{n-2})
$$

---

## 2. 两个关键观察

**观察 1 — Laplacian 主导病态**

几何能量的病态性很大程度上来自能量中的 **Laplacian-like 项**。取 Hessian 为 Laplacian 的凸二次代理，可显著压低条件数；且 $H$ 稀疏、**与迭代无关**，预处理 LU/Cholesky 一次，每步仅回代。

**观察 2 — 加速与预条件相互支持**

最优加速参数 $\theta$ 理论上应随 $\kappa(Q)$ 设定（§5.3）。二次代理使 $\kappa(Q)$ 近乎**与网格规模无关**，故 $\theta$ 可用几乎**普适的固定 $\eta$**（实验中 $\eta=100$ 或 $1000$），无需针对每种能量、每种网格精细调参。

---

## 3. 能量分解：如何把 $f$ 拆成 $h + g$

AQP 的前提是：几何能量在形式上**天然含有一个 Laplacian 二次项**，其余非线性部分可以整体归入 $g$。分解不是随意凑的，而是利用逐元素 Jacobian $T_j(x)$ 的 Frobenius 恒等式。

### 3.1 分解原则

几乎所有逐元素能量可写为

$$
f(x) = \sum_j E(T_j)\,|t_j|, \qquad \mathrm{vec}(T_j(x)) = J_j x
$$

其中 $T_j \in \mathbb{R}^{d \times d}$ 为第 $j$ 个单元（三角形/四面体）的 Jacobian，$|t_j|$ 为面积/体积权重。

**关键恒等式**——离散 Dirichlet 能量与 Laplacian 二次型等价：

$$
\frac{1}{2}x^T H x = \frac{1}{2}\sum_j \|T_j\|_F^2\,|t_j| = \frac{1}{2}\sum_{j,k} \sigma_k(T_j)^2\,|t_j|
$$

其中 $H = L \otimes I_d$，$L$ 为 cotan Laplacian。因此：**凡是在 $E(T)$ 中出现 $\|T\|_F^2$ 或等价二次项的能量，都可以把该项抽出来放进 $h(x)=\frac{1}{2}x^T H x$，余下部分放进 $g(x)$**。

分解后梯度为

$$
\nabla f(x) = Hx + \nabla g(x) = \sum_j J_j^T \,\mathrm{vec}(\nabla E(T_j))\,|t_j|
$$

AQP 每步在 $y_n$ 处线性化 $g$（保留 $h$ 的二次结构），故只需能计算 $\nabla f$ 和 $f$ 本身，不必显式写出 $g$ 的闭式。

### 3.2 ARAP：核范数项

局部 ARAP 能量 $\mathcal{D}_{\text{ARAP}}(T) = \|T - R(T)\|_F^2$。展开：

$$
\|T - R\|_F^2 = \|T\|_F^2 + \|R\|_F^2 - 2\,\mathrm{tr}(T^T R) = \|T\|_F^2 + d - 2\|T\|_*
$$

（$R$ 为正交矩阵，$\|R\|_F^2 = d$；$\mathrm{tr}(T^T R) = \|T\|_*$ 为核范数。）对全网求和：

$$
f_{\text{ARAP}}(x) = \underbrace{\frac{1}{2}x^T H x}_{h(x)} \;-\; \underbrace{\sum_j \|T_j\|_* |t_j|}_{g(x)} \;+\; c_0
$$

$h$ 是 Laplacian 二次项；$g$ 中的 $-\|T\|_*$ 是非光滑非线性项（SVD 奇异值之和）。**无加速版 AQP（QP）对 ARAP 恰好退化为 local/global**：KKT 步等价于 global 步，$\nabla g$ 中的旋转投影隐含在 $\nabla f_{\text{ARAP}}$ 的计算里。

### 3.3 ISO：逆 Jacobian 项

等距畸变 $\mathcal{D}_{\text{ISO}}(T) = \|T^{-1}\|_F^2$。利用 $\|T\|_F^2$ 恒等式：

$$
f_{\text{ISO}}(x) = \frac{1}{2}x^T H x + \frac{1}{2}\sum_j \|T_j^{-1}\|_F^2 |t_j|
$$

二次项进入 $h$，$\|T^{-1}\|_F^2$ 全部留在 $g$。ISO 在极小附近病态严重，正是 AQP 预条件发挥最大作用的场景之一（论文 Fig. 1：105 次迭代 vs L-BFGS 2300 次）。

### 3.4 CONF（$d=2$）：共形比项

二维共形畸变可写为

$$
f_{\text{CONF}}(x) = \frac{1}{2}x^T H x + \frac{1}{2}\sum_j \left(\frac{1}{\sigma_d(T_j)^2} - 1\right)\|T_j\|_F^2 |t_j|
$$

同样把 $\frac{1}{2}\|T\|_F^2$ 归入 $h$，含最小奇异值 $\sigma_d$ 的非线性因子留在 $g$。CONF 分解仅对三角网格成立（$d=2$）。

### 3.5 汇总

| 能量                | $h(x)=\frac{1}{2}x^T Hx$ 来源     | $g(x)$ 中的非线性部分                  |
| :------------------ | :-------------------------------- | :------------------------------------- |
| Dirichlet           | 全部                              | 无                                     |
| ARAP                | $\frac{1}{2}\sum \|T\|_F^2 |t_j|$ | $-\sum \|T\|_* |t_j|$                  |
| Symmetric Dirichlet | $\frac{1}{2}\sum \|T\|_F^2 |t_j|$ | $\frac{1}{2}\sum \|T^{-1}\|_F^2 |t_j|$ |
| ISO                 | 同上                              | $\frac{1}{2}\sum \|T^{-1}\|_F^2 |t_j|$ |
| MIPS                | 无（或需其他处理）                | 全部在 $g$                             |
| CONF ($d=2$)        | $\frac{1}{2}\sum \|T\|_F^2 |t_j|$ | 共形比 $(\sigma_1/\sigma_2)^2$ 相关项  |

### 3.6 Kronecker 积：$H = L \otimes I_d$ 的含义与实现

AQP 全文反复出现 $H = L \otimes I_d$。这里的 $\otimes$ 是**Kronecker 积**（张量积），不是 Kronecker 符号 $\delta_{ij}$。它把"对每个顶点做 Laplacian"与"对每个坐标分量独立处理"精确地编码进一个 $dn \times dn$ 矩阵。

#### 3.6.1 定义与 $\mathrm{vec}$ 恒等式

对 $A \in \mathbb{R}^{m \times n}$、$B \in \mathbb{R}^{p \times q}$，Kronecker 积 $A \otimes B \in \mathbb{R}^{mp \times nq}$ 是把 $B$ 的每个元素 $a_{ij}$ 替换为 $a_{ij} B$ 得到的分块矩阵。AQP 中最常用的是**右乘单位阵**的形式：

$$
H = L \otimes I_d, \qquad L \in \mathbb{R}^{n \times n},\; I_d \in \mathbb{R}^{d \times d}
$$

顶点位置矩阵 $X = [\mathbf{x}_1, \ldots, \mathbf{x}_n] \in \mathbb{R}^{d \times n}$ 按**列堆叠**为 $x = \mathrm{vec}(X) \in \mathbb{R}^{dn}$：

$$
x = \mathrm{vec}(X) = \begin{pmatrix} x_1 \\ x_2 \\ \vdots \\ x_d \end{pmatrix},
\quad x_\alpha = (X_{\alpha,1}, \ldots, X_{\alpha,n})^T \in \mathbb{R}^n,\; \alpha = 1,\ldots,d
$$

即先放所有顶点的第 1 坐标，再放所有顶点的第 2 坐标，依此类推（$d=2$ 时为先全体 $u$，再全体 $v$）。

**核心恒等式**（Kronecker 积与 $\mathrm{vec}$ 的交换律）：

$$
\boxed{\;(L \otimes I_d)\,\mathrm{vec}(X) = \mathrm{vec}(LX)\;}
$$

$L$ 左乘 $X$ 的每一**行**（每个坐标分量上的 $n$ 维向量），等价于 $H$ 左乘堆叠向量 $x$。几何上：$L$ 是离散 Laplacian（cotan 权），$LX$ 对每个坐标分别做调和/扩散，**$u$ 与 $v$（或 $x,y,z$）之间在 $h(x)=\frac{1}{2}x^T H x$ 中不耦合**。

二次型展开：

$$
\frac{1}{2}x^T (L \otimes I_d)\, x
= \frac{1}{2}\,\mathrm{tr}(X^T L X)
= \frac{1}{2}\sum_{\alpha=1}^{d} x_\alpha^T L x_\alpha
$$

这正是离散 **Dirichlet 能量** $\frac{1}{2}\int \|\nabla u\|^2 + \|\nabla v\|^2 \, dA$ 在三角网格上的标准二次型。

#### 3.6.2 二维示例：$L \otimes I_2$ 的分块结构

$d=2$ 时，$x = (u^T, v^T)^T$，$u,v \in \mathbb{R}^n$。Kronecker 积给出**块对角**结构：

$$
L \otimes I_2 =
\begin{pmatrix}
L & 0 \\
0 & L
\end{pmatrix}
$$

$H$ 是 $2n \times 2n$，但两块完全相同且**不交叉**——解 KKT 系统时，若右端项也按 $(u\text{-块}, v\text{-块})$ 分块，则等价于对**同一个** $L$ 求解两次 $n$ 维系统。实现中不必显式构造 $2n \times 2n$ 稠密矩阵；保持两个 $n$ 维 Laplacian 求解器即可。

#### 3.6.3 从面梯度算子到 $H$

逐面组装时，每个三角形 $T$ 有面积权 $A_T$ 与梯度算子 $G_T$（将顶点坐标映到该面 Jacobian 的 $\mathrm{vec}$）。Dirichlet 项贡献：

$$
H = \sum_T (A_T \otimes I_d)\, G_T^T G_T
$$

因 $(A_T \otimes I_d)\,\mathrm{vec}(X) = \mathrm{vec}(A_T X)$（标量 $A_T$ 对 $X$ 每行同乘），且 $G_T$ 本身已按坐标分块，求和后仍满足 $H = L \otimes I_d$ 的 Kronecker 形式，其中 $L$ 为 cotan Laplacian。这与 LSCM/调和参数化里见到的 $L$ 是同一对象。

#### 3.6.4 对 AQP 算法的实际好处

| 性质           | 含义                                                         |
| :------------- | :----------------------------------------------------------- |
| **稀疏性**     | $L$ 每行 $O(1)$ 非零 → $H$ 每行 $O(d)$ 非零，$dn$ 维仍稀疏   |
| **常数性**     | $H$ 不随迭代变化 → KKT 左端可**一次** Cholesky/LU，每步回代  |
| **分坐标解耦** | $d$ 个独立的 $L x_\alpha = b_\alpha$，可并行                 |
| **条件数**     | $\kappa(H) \approx \kappa(L)$（块重复 $d$ 次不改变条件数）；$\kappa(L) \sim \delta^{-2}$，预条件后 $\kappa(Q)$ 可近常数 |

带约束 $Ax=b$ 时，若约束是"固定某些顶点的某些坐标"（Dirichlet 边界），约束矩阵 $A$ 在 Kronecker 布局下同样稀疏；$K^T H K$ 仍可利用 $L$ 的结构。一般位置约束下需对完整 $dn$ 维系统预分解，但 $H$ 的 Kronecker 来源仍保证组装简洁。

#### 3.6.5 与未使用 Kronecker 形式的对比

若把 $u,v$ 交错排列为 $(u_1,v_1,u_2,v_2,\ldots)$，Laplacian 二次项对应的 $H$ **不再**是块对角，$u_i$ 与 $v_i$ 会混在同一 $2\times 2$ 块里——但那是变量顺序问题，能量本身仍不耦合 $u$ 与 $v$。AQP 与 libigl 等实现采用 $\mathrm{vec}$ 列堆叠 + $L \otimes I_d$，是为了：

1. 与 $\sum_T \|T_j\|_F^2 |t_j|$ 的推导一致；
2. 一次预分解 $L$，$d$ 个坐标共享；
3. 与 $\nabla f$ 的按坐标累加实现自然对齐。

**小结**：$L \otimes I_d$ 不是抽象记号，而是说"Dirichlet / Laplacian 能量对每个坐标分量施加相同的离散二阶算子"。AQP 把这部分抽进 $h(x)$，正是利用其**稀疏、常系数、Kronecker 可分离**来做固定预条件。

$L$ 在网格尺寸 $\delta$ 上条件数约 $\delta^{-2}$；把 Dirichlet 二次项从 $H+G$ 中剥离到 $H$ 侧作预条件，可将有效条件数 $\kappa(Q)$ 大幅压低（Fig. 3b）。

---

## 4. 凸二次代理


对逐元素能量 $\mathcal{D}(J)$，构造凸二次代理 $\mathcal{P}^{R_f^k}(J)$，满足三条性质（与 SLIM 中 ARAP 代理相同，见 [几何优化-SLIM](几何优化-SLIM.md) §2.1、§4）：

| 性质                   | 公式                                                         | 含义             |
| :--------------------- | :----------------------------------------------------------- | :--------------- |
| **Majorizer**          | $\mathcal{P}^{R_f^k}(J) \geq \mathcal{D}(J),\; \forall J$    | 代理是上界       |
| **Matching gradients** | $\nabla_J \mathcal{P}^{R_f^k}(J_f^k) = \nabla_J \mathcal{D}(J_f^k)$ | 当前点梯度一致   |
| **Closest minimizer**  | $\arg\min_J \mathcal{P}^{R_f^k}(J) = \mathrm{Proj}_{\mathcal{D}}(J_f^k)$ | 极小点为最近投影 |

**全局层面**，AQP 将能量写为 $f = h + g$，其中 $h(x)=\frac{1}{2}x^T H x$。加速步得到外推点 $y_n$ 后，**不**在 $y_n$ 处对完整 $f$ 做 Newton，而是对 $g$ 线性化、对 $h$ 保留二次型，求搜索方向 $p_n$：

$$
\min_p \; h(y_n + p) + g(y_n) + \nabla g(y_n)^T p \quad \text{s.t.} \quad Ap = 0
\tag{★}
$$

以下从 (★) 经 Lagrange 乘子法推出 KKT 线性系统。

### 4.1 从代理子问题到 KKT 系统

**Step 1 — 展开 $h$，化为标准二次规划**

$h(y_n+p) = \frac{1}{2}(y_n+p)^T H (y_n+p)$。对 $p$ 求最小化时，与 $p$ 无关的常数项 $\frac{1}{2}y_n^T H y_n$ 可丢弃：

$$
h(y_n+p) + g(y_n) + \nabla g(y_n)^T p
= \frac{1}{2}p^T H p + \underbrace{\bigl(H y_n + \nabla g(y_n)\bigr)^T}_{\nabla f(y_n)^T} p + \text{const.}
$$

其中用到 $f=h+g$ 故 $\nabla f(y_n) = H y_n + \nabla g(y_n)$。于是 (★) 等价于

$$
\min_p \; \frac{1}{2}p^T H p + \nabla f(y_n)^T p \quad \text{s.t.} \quad Ap = 0
\tag{QP}
$$

**Step 2 — 为何约束是 $Ap=0$**

原问题要求 $Ax=b$。当前 $y_n$ 一般**不**严格满足约束（$y_n$ 来自外推，不是可行点），但搜索沿 $p$ 方向：$x = y_n + tp$。要最终回到可行域，需 $A(y_n+tp)=b$；对任意 $t$ 的一阶要求即 $Ap=0$（切于可行仿射子空间 $\{x: Ax=b\}$）。

**Step 3 — 构造 Lagrangian**

引入乘子 $\lambda \in \mathbb{R}^{m}$（$A$ 为 $m\times dn$）：

$$
\mathcal{L}(p,\lambda) = \frac{1}{2}p^T H p + \nabla f(y_n)^T p + \lambda^T (Ap)
$$

**Step 4 — KKT 一阶条件**

对 $p$、$\lambda$ 求驻点：

$$
\frac{\partial \mathcal{L}}{\partial p} = H p + \nabla f(y_n) + A^T \lambda = 0
\qquad\Longrightarrow\qquad
H p_n + A^T \lambda = -\nabla f(y_n)
$$

$$
\frac{\partial \mathcal{L}}{\partial \lambda} = Ap = 0
\qquad\Longrightarrow\qquad
A p_n = 0
$$

**Step 5 — 块矩阵形式**

写成线性系统（即论文式 (7)）：

$$
\boxed{
\begin{bmatrix} H & A^T \\ A & 0 \end{bmatrix}
\begin{bmatrix} p_n \\ \lambda \end{bmatrix} =
\begin{bmatrix} -\nabla f(y_n) \\ 0 \end{bmatrix}
}
$$

**可解性**：$H$ 在 $\ker A$ 上严格正定（$h$ 在约束子空间上凸），$A$ 行满秩时上述鞍点系统有唯一解 $p_n$——即 (QP) 的最优搜索方向。

**与 Newton 的对比**：若在 $y_n$ 处对**完整** $f$ 做二次近似，KKT 左端为 $\nabla^2 f(y_n)$，每步随 $y_n$ 变化。AQP 用**固定** $H$ 替代 $\nabla^2 h$，右端仍用真实梯度 $\nabla f(y_n)$，从而左端可预分解。

**与 proximal gradient 的对比**：近端步对应 $\min_p \frac{1}{2}p^T H p + \nabla f(y_n)^T p + \frac{1}{2t}\|p\|^2$，KKT 左端变为 $H + \frac{1}{t}I$，依赖步长 $t$，无法一次预分解。

左端矩阵**恒定**，预处理 LU/Cholesky 一次，每步回代。

---

## 5. 加速机制：为什么外推 $y_n$ 再求方向

AQP 不是"先预条件、再随便加个 Nesterov"，**加速步与代理步在理论上耦合**：预条件压低 $\kappa(Q)$，使加速系数 $\theta$ 可普适选取；加速又进一步把收敛率从 $\rho$ 压到 $1-\sqrt{1-\rho}$。

### 5.1 三步迭代的角色

每轮迭代做三件事，顺序不能乱：

| 步骤       | 公式                                       | 作用                      |
| :--------- | :----------------------------------------- | :------------------------ |
| **加速**   | $y_n = (1+\theta)x_{n-1} - \theta x_{n-2}$ | 用动量外推到"超前点"      |
| **代理**   | 在 $y_n$ 处解 KKT 得 $p_n$                 | Laplacian 预条件搜索方向  |
| **线搜索** | $x_n = y_n + t\,p_n$                       | 在原始能量 $f$ 上充分下降 |

**关键**：代理步作用在 $y_n$ 上，而非 $x_{n-1}$。若对 $x_{n-1}$ 直接做代理最小化，动量无法生效，整体退化为普通预条件梯度下降（QP，$\theta=0$）。

### 5.2 误差递推与 Nesterov 系数

在局部极小 $x^*$ 附近，将 $f$ 二阶展开并忽略高阶余项：

$$
f(x) \approx \underbrace{\tfrac{1}{2}x^T H x}_{h(x)} + \underbrace{\tfrac{1}{2}x^T G x + a^T x + d}_{g(x)}
$$

$G = \nabla^2 g(x^*)$。记 $e_n = x_n - x^*$，约束子空间上的误差满足递推（Lemma 1）：

$$
K^T e_n = M\bigl[(1+\theta) K^T e_{n-1} - \theta K^T e_{n-2}\bigr], \qquad M = I - tQ
$$

$$
Q = (K^T H K)^{-1}(K^T (H+G) K)
$$

这是 **Chebyshev / Nesterov 型二阶递推**：不仅用上一迭代，还用上上一迭代，通过 $\theta$ 调节两者权重。

**Lemma 2**：对同一迭代矩阵 $M$（谱半径 $\rho < 1$），$\theta=0$ 时收敛率 $\rho$；取 $\theta_{\text{acc}} = \frac{2}{\rho}(1-\sqrt{1-\rho}) - 1$ 时收敛率 $1-\sqrt{1-\rho}$（最优）。

**Lemma 3**：取线搜索步长 $t = \lambda_1^{-1}$（$Q$ 的最大特征值），则 $\rho = 1 - \kappa^{-1}$，$\kappa = \kappa(Q)$。代入得

$$
\theta = \frac{1 - \sqrt{\kappa^{-1}}}{1 + \sqrt{\kappa^{-1}}}
$$

**Theorem 1**：取 $\eta = \kappa(Q)$ 时，$\|e_n\| \leq c(1-\sqrt{\kappa^{-1}})^n$。

### 5.3 为何 $\theta$ 可以"普适"

标准 Nesterov 要求 $\theta$ 随问题条件数精细调整。AQP 的观察是：

1. 几何能量的病态主要来自 Laplacian 项 → 抽出到 $H$ 作预条件（§3）；
2. $\kappa(Q)$ 因此随网格规模增长缓慢（Fig. 3b）；
3. 实践中取固定 $\eta = 100$ 或 $1000$ 即可。

**加速与预条件相互支持**：没有 Laplacian 代理（AGD，$H=I$），$\kappa(Q)$ 随网格急剧恶化；没有加速（QP，$\theta=0$），预条件 alone 仍比 L-BFGS 快，但不及完整 AQP（Fig. 3a）。

### 5.4 直观理解

把优化轨迹想象成在狭长山谷里下山：

- **无预条件（GD/AGD）**：山谷极窄（高 $\kappa$），每步只能挪一小步；
- **有预条件（QP）**：把山谷"拉宽"，每步能走更远，但仍沿锯齿形路径震荡；
- **预条件 + 加速（AQP）**：在拉宽的山谷里，外推点 $y_n$ 沿动量方向超前，在超前点处用 Laplacian 代理算方向，减少锯齿、更快贴近谷底。

---

## 6. 算法

### 6.1 主循环

```
输入: 可行初值 x, 参数 η > 0
初始化: x_{-1} = x_0 = x
        θ = (1 - √(1/η)) / (1 + √(1/η))

重复直到收敛:
  【加速】y_n = (1 + θ) x_{n-1} - θ x_{n-2}

  【代理步】解 KKT 系统求 p_n:
      [ H   A^T ] [ p_n ]   [ -∇f(y_n) ]
      [ A    0  ] [  λ   ] = [    0     ]

  【线搜索】x_n = y_n + t p_n,  0 < t ≤ 1
            ISO/CONF 用 [Smith & Schaefer 2015] barrier 限制 t，防翻转
```

**终止**：$\|\nabla f\| < \varepsilon$ 或能量变化足够小。

**实验**（Fig. 1）：2D ISO 变形，AQP 约 105 次迭代、0.11 s；L-BFGS 约 2300 次（极端案例可达 ×200 加速）。

### 6.2 与 Local/Global、Proximal 的关系

| 方法                  | 关系                                               |
| :-------------------- | :------------------------------------------------- |
| **QP（$\theta=0$）**  | 对 ARAP 退化为 [Liu et al. 2008] global/local      |
| **Proximal Gradient** | 系统 $(H + \frac{1}{t}I)$ 依赖步长 $t$，无法预分解 |
| **AQP**               | 固定 $H$，每步只求解一次 KKT，叠加 Nesterov 加速   |

Proximal 一般形式 $x_{k+1} = \mathrm{prox}_{\alpha F}(x_k - \alpha \nabla G(x_k))$，$f=F+G$。AQP 中 $F=h$，$G=g$；$h$ 的 proximal 步即上述 KKT 求解，但 $H$ 不含 $1/t$ 项。





## 8. 总结

AQP 将几何优化拆为 **Laplacian 二次项 + 非线性余项**，在 Nesterov 外推点上用固定稀疏 KKT 作预条件步，再辅以回溯（及可选翻转 barrier）线搜索。纯一阶、只用前两轮结果、无需真实 Hessian——迭代次数近乎与网格分辨率无关，适合大规模管线。

---

## 参考文献

- Kovalsky S. Z., Galun M., Lipman Y. *Accelerated Quadratic Proxy for Geometric Optimization*. SIGGRAPH 2016.
- Nesterov Y. *A method for solving the convex programming problem with convergence rate $O(1/k^2)$*. 1983.
- Liu T., et al. *A local/global approach to mesh parameterization*. CGF 2008.
- Smith J., Schaefer S. *Bijective parameterization with free boundaries*. SIGGRAPH 2015.
- Rabinovich M., et al. *Scalable Locally Injective Mappings*. SIGGRAPH 2017.（矩阵加权代理，见本站 [SLIM](几何优化-SLIM.md)）
