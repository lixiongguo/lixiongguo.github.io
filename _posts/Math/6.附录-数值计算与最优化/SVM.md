---
layout: post
title: "支持向量机 (SVM) 与凸优化"
category: Parameterization
categories: ["Parameterization", "Parameterization-Appendix"]
mathjax: true
---

支持向量机 (Support Vector Machine, SVM) 是经典的**二分类**线性判别器：在特征空间中寻找**最大间隔 (maximum margin)** 超平面。其训练问题可写为**凸二次规划 (QP)**；通过 **Lagrange 对偶**得到仅含对偶变量 $\alpha_i$ 的有限维问题，稀疏解对应**支持向量**。对偶 QP 常用 **SMO (Sequential Minimal Optimization)** 等坐标下降法求解——每步只优化两个 $\alpha$，子问题有闭式解。

本篇与《凸优化与KKT条件》《QP与SOCP》衔接：SVM 是约束 QP + 对偶理论 + KKT 互补松弛的标准课堂例；**核技巧**使同一套对偶 QP / SMO 在非线性边界上仍保持凸性与有限维对偶。

---

## 1. 几何直观

给定训练集 $\{(\boldsymbol{x}_i,y_i)\}_{i=1}^{m}$，$\boldsymbol{x}_i\in\mathbb{R}^n$，标签 $y_i\in\{+1,-1\}$。

**线性可分**时，存在超平面 $\boldsymbol{w}^T\boldsymbol{x}+b=0$ 使 $y_i(\boldsymbol{w}^T\boldsymbol{x}_i+b)>0$。归一化 $\|\boldsymbol{w}\|=1$ 后，样本 $i$ 到超平面的**函数间隔**为 $y_i(\boldsymbol{w}^T\boldsymbol{x}_i+b)$；**几何间隔**为 $y_i(\boldsymbol{w}^T\boldsymbol{x}_i+b)/\|\boldsymbol{w}\|$。

SVM 选择**最大几何间隔**的分离超平面。间隔最大的超平面由**距其最近的若干点**唯一确定——这些点称为**支持向量 (support vectors)**，对应约束在最优处**活跃**。

```
        ●  y=+1
    ●       ○  y=-1
  ●   |   ○
      |←δ→|   最大间隔 δ = 2/‖w‖
    ●   |   ○
        ○
```

---

## 2. 原始问题 (Primal)

### 2.1 硬间隔（线性可分）

要求所有样本正确分类且函数间隔至少为 $1$：

$$
\begin{aligned}
\min_{\boldsymbol{w},\,b}\quad & \frac{1}{2}\|\boldsymbol{w}\|^2 \\
\text{s.t.}\quad & y_i(\boldsymbol{w}^T\boldsymbol{x}_i+b)\ge 1,\quad i=1,\ldots,m.
\end{aligned}
\tag{P-hard}
$$

目标 $\frac{1}{2}\|\boldsymbol{w}\|^2$ 凸；约束对 $(\boldsymbol{w},b)$ **仿射**（$y_i\boldsymbol{w}^T\boldsymbol{x}_i+y_i b\ge 1$）。可行域非空时 (P-hard) 为**严格凸 QP**，最优解唯一。

等价地，最大化几何间隔 $\displaystyle\frac{2}{\|\boldsymbol{w}\|}$ 与最小化 $\|\boldsymbol{w}\|^2$ 同一解（差单调变换）。

### 2.2 为什么需要软间隔？

硬间隔 (P-hard) 隐含一个强假设：**存在**超平面使所有样本满足 $y_i(\boldsymbol{w}^T\boldsymbol{x}_i+b)\ge 1$。实际中这一假设常常不成立，或成立但**不该**被强行满足。软间隔正是为下列情形引入的。

#### （1）线性不可分：硬间隔问题无解

二维例子：绝大多数 $+$ 在左下，$-$ 在右上，但混入一个**异类点**。

```
    ○  y=-1
  ○   ○
    ●  ← 孤立的 y=+1，任何直线都无法同时分开
  ●   ●
●
```

此时 (P-hard) 的约束集**为空**，QP **不可行**——不存在任何 $(\boldsymbol{w},b)$ 满足全部 $m$ 条不等式。优化器无法给出分类器。

软间隔把 $y_i(\boldsymbol{w}^T\boldsymbol{x}_i+b)\ge 1$ 放松为 $y_i(\boldsymbol{w}^T\boldsymbol{x}_i+b)\ge 1-\xi_i$，$\xi_i\ge 0$。取足够大的 $\xi_i$ 总可使约束可行（例如 $\boldsymbol{w}=\boldsymbol{0},b=0,\xi_i=1$），**(P-soft) 恒有可行解**。不可分数据从「无解」变为「在惩罚下求最优折中」。

#### （2）噪声与离群点：硬间隔对异常点过敏

即使数据**近似**可分，标签错误或测量噪声会使少数点远离本类簇。硬间隔要求**每一个**点都在间隔正确一侧，分离超平面会被这些点「拽」向极端位置：

- $\|\boldsymbol{w}\|$ 变大 → 几何间隔变**窄**（在其余点上）；
- 决策边界过度迁就离群点 → **泛化变差**。

软间隔允许对「难以满足」的样本付出 $\xi_i>0$ 的代价，在目标里用 $C\sum_i\xi_i$ 惩罚。等价于告诉模型：**少数违背间隔的样本可以接受，但不要太多、不要太狠**——间隔仍由**多数可靠样本**（支持向量）主导，离群点往往对应 $\alpha_i=C$、$\xi_i>0$，而不是绑架整条边界。

#### （3）$C$ 的含义：间隔宽度 vs 训练误差

(P-soft) 目标

$$
\underbrace{\frac{1}{2}\|\boldsymbol{w}\|^2}_{\text{希望间隔大（}\|\boldsymbol{w}\|\text{ 小）}}
\;+\;
\underbrace{C\sum_{i=1}^{m}\xi_i}_{\text{希望违背间隔的总量小}}.
$$

| $C$ | 行为 |
| :--- | :--- |
| **$C$ 很大** | 强烈惩罚 $\xi_i$ → 逼近硬间隔；间隔窄也要尽量分对每一个点；对噪声敏感 |
| **$C$ 很小** | 允许较多、较大的 $\xi_i$ → 更宽间隔、更多训练误分类/间隔内样本；边界更「平滑」、更抗噪 |
| **$C\to\infty$** | (P-soft) $\to$ (P-hard)（在可行时） |

因此 $C$ 不是随便的超参：它实现 **最大间隔** 与 **拟合训练标签** 之间的显式权衡，类似正则化强度。交叉验证选 $C$ 是标准做法。

#### （4）与 hinge 损失同一逻辑

可证 (P-soft) 等价于**无约束**形式（对 $\boldsymbol{w},b$）：

$$
\min_{\boldsymbol{w},b}\;
\frac{1}{2}\|\boldsymbol{w}\|^2
+ C\sum_{i=1}^{m}
\max\bigl(0,\; 1-y_i(\boldsymbol{w}^T\boldsymbol{x}_i+b)\bigr).
$$

右边求和项即 **hinge loss**：$y_i(\boldsymbol{w}^T\boldsymbol{x}_i+b)\ge 1$ 时损失为 $0$；在间隔内或错分则线性增长。软间隔不是「拍脑袋加松弛」，而是把「允许错分」写进**凸损失**，与最大间隔原则在同一框架里统一。

#### （5）核 SVM 里仍然需要

即使用 RBF 等核把数据映射到高维并**理论上**可分，实践中仍几乎总用软间隔：

- 有限精度、重复样本、标签噪声使「精确可分」无意义；
- 无限维特征下硬间隔可能**过拟合**（间隔在训练集上极大但测试差）；
- 对偶中 $0\le\alpha_i\le C$ 的上界正是软间隔的印记：$\alpha_i=C$ 的样本是「被 $C$ 截断」的难例。

**小结**：硬间隔追求「全体样本、精确、宽间隔」；真实数据往往不可分、有噪声、需控泛化。软间隔用 $\xi_i$ 度量违背程度、用 $C$ 控制惩罚，使问题**恒可行**、**抗离群**、**可调泛化**，并自然导出 hinge 损失与对偶中的 $\alpha_i\le C$。

### 2.3 软间隔原始问题

在 (P-hard) 上引入松弛变量 $\xi_i\ge 0$：

$$
\begin{aligned}
\min_{\boldsymbol{w},\,b,\,\boldsymbol{\xi}}\quad
& \frac{1}{2}\|\boldsymbol{w}\|^2 + C\sum_{i=1}^{m}\xi_i \\
\text{s.t.}\quad
& y_i(\boldsymbol{w}^T\boldsymbol{x}_i+b)\ge 1-\xi_i,\quad i=1,\ldots,m, \\
& \xi_i\ge 0,\quad i=1,\ldots,m.
\end{aligned}
\tag{P-soft}
$$

- $\xi_i=0$：样本在间隔外侧或边界上（正确分类且间隔 $\ge 1$）；
- $0<\xi_i<1$：正确分类但在间隔内；
- $\xi_i\ge 1$：被误分类。

(P-soft) 仍是凸 QP（$m$ 个不等式 + $m$ 个非负约束）。**硬间隔**为 $C\to\infty$ 的极限（在 (P-hard) 可行时）。

### 2.4 判别函数

最优 $(\boldsymbol{w}^*,b^*)$ 给出分类器

$$
f(\boldsymbol{x})=\mathrm{sign}\bigl(\boldsymbol{w}^{*T}\boldsymbol{x}+b^*\bigr).
$$

对偶求解后，$\boldsymbol{w}^*$ 常写为支持向量的线性组合（见 §4）。

---

## 3. Lagrangian 与对偶问题

以下以 **(P-soft)** 为准；(P-hard) 即去掉 $\xi_i$ 与上界 $C$（$\alpha_i\ge 0$ 无上界）。

### 3.1 Lagrangian

对不等式 $1-\xi_i-y_i(\boldsymbol{w}^T\boldsymbol{x}_i+b)\le 0$ 乘子 $\alpha_i\ge 0$；对 $\xi_i\ge 0$ 乘子 $\mu_i\ge 0$：

$$
\begin{aligned}
\mathcal{L}(\boldsymbol{w},b,\boldsymbol{\xi},\boldsymbol{\alpha},\boldsymbol{\mu})
= &\;\frac{1}{2}\|\boldsymbol{w}\|^2 + C\sum_i\xi_i \\
&+ \sum_{i=1}^{m}\alpha_i\bigl(1-\xi_i-y_i(\boldsymbol{w}^T\boldsymbol{x}_i+b)\bigr)
- \sum_{i=1}^{m}\mu_i\xi_i.
\end{aligned}
$$

### 3.2 对偶函数 $\theta$

对 $(\boldsymbol{w},b,\boldsymbol{\xi})$ 取极小（《凸优化与KKT条件》§对偶理论）：

$$
\frac{\partial\mathcal{L}}{\partial\boldsymbol{w}}=\boldsymbol{0}
\;\Rightarrow\;
\boldsymbol{w}=\sum_{i=1}^{m}\alpha_i y_i\boldsymbol{x}_i.
$$

$$
\frac{\partial\mathcal{L}}{\partial b}=0
\;\Rightarrow\;
\sum_{i=1}^{m}\alpha_i y_i=0.
$$

$$
\frac{\partial\mathcal{L}}{\partial\xi_i}=0
\;\Rightarrow\;
C-\alpha_i-\mu_i=0
\;\Rightarrow\;
0\le\alpha_i\le C
\quad(\mu_i=C-\alpha_i\ge 0).
$$

代入 $\mathcal{L}$，交叉项消去，得

$$
\theta(\boldsymbol{\alpha})
= \sum_{i=1}^{m}\alpha_i
- \frac{1}{2}\sum_{i,j=1}^{m}\alpha_i\alpha_j y_i y_j\,\boldsymbol{x}_i^T\boldsymbol{x}_j,
\qquad
\boldsymbol{\alpha}\in\mathbb{R}^m.
$$

**对偶问题** $\max_{\boldsymbol{\alpha}}\theta(\boldsymbol{\alpha})$ 在约束下为

$$
\begin{aligned}
\max_{\boldsymbol{\alpha}}\quad
& \sum_{i=1}^{m}\alpha_i
- \frac{1}{2}\sum_{i,j=1}^{m}\alpha_i\alpha_j y_i y_j\,\boldsymbol{x}_i^T\boldsymbol{x}_j \\
\text{s.t.}\quad
& \sum_{i=1}^{m}\alpha_i y_i = 0, \\
& 0\le\alpha_i\le C,\quad i=1,\ldots,m.
\end{aligned}
\tag{D-soft}
$$

**硬间隔** (P-hard) 对偶：同上，但 $0\le\alpha_i$（无 $C$ 上界）。

| 原始 | 对偶 |
| :--- | :--- |
| $\boldsymbol{w}\in\mathbb{R}^n$，$b\in\mathbb{R}$，$\boldsymbol{\xi}\in\mathbb{R}^m$ | $\boldsymbol{\alpha}\in\mathbb{R}^m$ |
| $m$ 个间隔约束 + $m$ 个 $\xi_i\ge 0$ | 1 个等式 $\sum\alpha_i y_i=0$ + 盒约束 $[0,C]$ |
| 二次目标 + 线性约束 | **纯二次目标** + 线性约束 |

(P-soft) 满足 Slater（例如取 $\boldsymbol{w}=\boldsymbol{0},b=0,\xi_i=1$ 在 $C$ 足够大时），故 **强对偶** $p^*=d^*$，KKT 充要。

### 3.3 KKT 与互补松弛

记 $f_i(\boldsymbol{x})=\boldsymbol{w}^T\boldsymbol{x}+b$。最优时：

| 条件 | 含义 |
| :--- | :--- |
| $\boldsymbol{w}=\sum_i\alpha_i y_i\boldsymbol{x}_i$ | 平稳性 |
| $\sum_i\alpha_i y_i=0$ | 平稳性 |
| $y_i f_i(\boldsymbol{x}_i)\ge 1-\xi_i$，$\xi_i\ge 0$ | 原始可行 |
| $0\le\alpha_i\le C$ | 对偶可行 |
| $\alpha_i(1-\xi_i-y_i f_i(\boldsymbol{x}_i))=0$ | 间隔约束互补 |
| $\mu_i\xi_i=0$，$\mu_i=C-\alpha_i$ | 松弛互补 |

**支持向量**的三种情形（软间隔）：

| $\alpha_i$ | 样本角色 |
| :--- | :--- |
| $\alpha_i=0$ | 非支持向量，约束松弛 |
| $0<\alpha_i<C$ | 在**间隔边界**上，$y_i f_i(\boldsymbol{x}_i)=1$ |
| $\alpha_i=C$ | **边界外**或误分类，$y_i f_i(\boldsymbol{x}_i)\le 1$ |

由 $0<\alpha_i<C$ 的样本可算阈值

$$
b^*=y_i-\boldsymbol{w}^{*T}\boldsymbol{x}_i
\quad\text{（对任一此类 }i\text{ 取平均更稳）}.
$$

---

## 4. 核技巧 (Kernel Trick)

线性 SVM 的决策边界是 $\boldsymbol{w}^T\boldsymbol{x}+b=0$——**仿射超平面**。许多数据在原始坐标下**线性不可分**，却在某个更高维（甚至无穷维）特征空间里可被超平面分开。**核技巧**的做法是：在对偶与判别函数里只出现内积 $\langle\phi(\boldsymbol{x}_i),\phi(\boldsymbol{x}_j)\rangle$，用核函数 $K(\boldsymbol{x}_i,\boldsymbol{x}_j)$ 替代，从而**隐式**使用非线性映射 $\phi$，而无需构造 $\phi(\boldsymbol{x})$ 的坐标。

### 4.1 动机：原始空间线性不可分

**XOR**（二维、四类点）是经典反例：

| $\boldsymbol{x}$ | $y$ |
| :--- | :---: |
| $(0,0),\,(1,1)$ | $+1$ |
| $(0,1),\,(1,0)$ | $-1$ |

任意直线 $w_1 x_1+w_2 x_2+b=0$ 都无法把两类分开。但若引入 $\phi(x_1,x_2)=(x_1^2,\,\sqrt{2}\,x_1 x_2,\,x_2^2)$，则

$$
\phi(\boldsymbol{x})^T\phi(\boldsymbol{z})
= (x_1 z_1 + x_2 z_2)^2
= (\boldsymbol{x}^T\boldsymbol{z})^2,
$$

在 $\phi$-空间中存在**线性**分离超平面（对应原始空间的二次曲线）。核技巧让我们直接算 $(\boldsymbol{x}^T\boldsymbol{z})^2$，不必写出 $\phi$ 的三维坐标。

```
  x₂
  1   -  +     线性 SVM：找不到直线
  0   +  -     核 SVM：边界可为曲线（RBF）或二次曲面（多项式核）
      0──1  x₁
```

### 4.2 特征映射、核函数与 Gram 矩阵

设 $\phi:\mathbb{R}^n\to\mathcal{H}$ 为（可能无穷维）**特征映射**，$\mathcal{H}$ 为 Hilbert 空间。定义**核函数**

$$
K(\boldsymbol{x},\boldsymbol{z}) = \langle\phi(\boldsymbol{x}),\,\phi(\boldsymbol{z})\rangle_{\mathcal{H}}.
$$

**核化原始问题**：将 (P-soft) 中 $\boldsymbol{w}^T\boldsymbol{x}_i$ 理解为 $\langle\boldsymbol{w},\phi(\boldsymbol{x}_i)\rangle$，$\boldsymbol{w}\in\mathcal{H}$，约束变为 $y_i(\langle\boldsymbol{w},\phi(\boldsymbol{x}_i)\rangle+b)\ge 1-\xi_i$。表示定理给出最优 $\boldsymbol{w}^*=\sum_i \alpha_i^* y_i \phi(\boldsymbol{x}_i)$——仍落在训练点张成的子空间里。

**核化对偶 (D-soft)**：把 $\boldsymbol{x}_i^T\boldsymbol{x}_j$ 换为 $K(\boldsymbol{x}_i,\boldsymbol{x}_j)$：

$$
\begin{aligned}
\max_{\boldsymbol{\alpha}}\quad
& \sum_{i=1}^{m}\alpha_i
- \frac{1}{2}\sum_{i,j=1}^{m}\alpha_i\alpha_j y_i y_j\,K(\boldsymbol{x}_i,\boldsymbol{x}_j) \\
\text{s.t.}\quad
& \sum_{i=1}^{m}\alpha_i y_i = 0,\quad 0\le\alpha_i\le C.
\end{aligned}
\tag{D-kernel}
$$

记 **Gram 矩阵** $\boldsymbol{G}$，$G_{ij}=K(\boldsymbol{x}_i,\boldsymbol{x}_j)$；**对偶 Hessian** $Q_{ij}=y_i y_j G_{ij}$。问题仍是 $m$ 维**凸 QP**（$Q\succeq 0$ 当 $G\succeq 0$），SMO / 内点法结构不变。

**判别函数**（仅依赖核值）：

$$
f(\boldsymbol{x})
=\mathrm{sign}\!\left(
\sum_{i=1}^{m}\alpha_i^* y_i\,K(\boldsymbol{x}_i,\boldsymbol{x}) + b^*
\right).
$$

$\alpha_i^*>0$ 的样本仍是**支持向量**；预测是支持向量处核函数的**线性组合**——非线性边界，但系数 $\alpha_i^*$ 来自同一凸对偶。

### 4.3 有效核：Mercer 条件与正定性

并非任意 $K(\cdot,\cdot)$ 都对应某个 $\phi$。**Mercer 定理**（实用形式）：对称 $K$ 在任意有限点集 $\{\boldsymbol{x}_i\}_{i=1}^m$ 上生成的 Gram 矩阵 $\boldsymbol{G}$ **半正定**（$G\succeq 0$），当且仅当 $K$ 为某 $\mathcal{H}$ 中的合法内积核。因此训练前可检查：随机子集上 $\boldsymbol{G}$ 的特征值非负。

| 要求 | 含义 |
| :--- | :--- |
| $G\succeq 0$ | 对偶目标 $-\frac{1}{2}\boldsymbol{\alpha}^T Q\boldsymbol{\alpha}+\mathbf{1}^T\boldsymbol{\alpha}$ 在约束下仍有界、凸 |
| $K$ 对称 | $K(\boldsymbol{x},\boldsymbol{z})=K(\boldsymbol{z},\boldsymbol{x})$ |
| 违反 PSD | 对偶可能无界或数值不稳定；实践中勿随意组合核 |

**核的运算封闭性**（构造新核）：合法核的加、非负线性组合、直积、对固定映射的复合 $K(\psi(\boldsymbol{x}),\psi(\boldsymbol{z}))$ 仍为合法核——便于多通道特征拼接。

### 4.4 常用核及其在 SVM 中的角色

| 核 | 公式 | 典型场景 | 超参数 |
| :--- | :--- | :--- | :--- |
| **线性** | $K(\boldsymbol{x},\boldsymbol{z})=\boldsymbol{x}^T\boldsymbol{z}$ | 高维稀疏文本、维数 $n\gg m$；基线 | 无 |
| **多项式** | $K=(\gamma\,\boldsymbol{x}^T\boldsymbol{z}+r)^d$ | 低维、需显式交互项（如 XOR 型） | $\gamma,r,d$ |
| **RBF / 高斯** | $K=\exp(-\gamma\|\boldsymbol{x}-\boldsymbol{z}\|^2)$ | 通用非线性、光滑边界 | $\gamma>0$ |
| **Sigmoid** | $K=\tanh(\kappa\,\boldsymbol{x}^T\boldsymbol{z}+r)$ | 历史用法；**未必** PSD，需验证 | $\kappa,r$ |

**线性核**：$\phi$ 为恒等映射，(D-kernel) 退化为 (D-soft)。$n$ 很大时不必存 $m\times m$ 全矩阵，可按列流式算 $\boldsymbol{x}_i^T\boldsymbol{x}_j$。

**多项式核**：次数 $d$ 控制边界复杂度；$d$ 过大易过拟合。$\gamma$ 缩放内积，影响基函数尺度。

**RBF 核**：$\phi$ 为无穷维；$K(\boldsymbol{x}_i,\boldsymbol{x})\to 0$ 当 $\|\boldsymbol{x}-\boldsymbol{x}_i\|\to\infty$，决策函数由**邻近**支持向量局部决定。$\gamma$ 大 → 单点影响范围窄、边界曲折（易过拟合）；$\gamma$ 小 → 影响弥散、边界平滑（欠拟合）。与 (P-soft) 的 $C$ **联合**调参：$C$ 管间隔与误分，$\gamma$ 管非线性程度。

### 4.5 为何在对偶上用核，而非原始空间？

| | 原始空间显式 $\phi$ | 对偶 + 核 |
| :--- | :--- | :--- |
| 变量 | $\boldsymbol{w}\in\mathcal{H}$ 可能无穷维 | $\boldsymbol{\alpha}\in\mathbb{R}^m$，恒 $m$ 维 |
| 计算 | 需存 $\phi(\boldsymbol{x})$ 坐标 | 只算 $m\times m$ 的 $K_{ij}$ |
| 优化 | 一般 QP 维数随 $\dim\mathcal{H}$ 爆炸 | SMO 每步 $\mathcal{O}(m)$，与 $\dim\mathcal{H}$ 无关 |
| 表示 | $\boldsymbol{w}^*$ 难显式写出 | $\boldsymbol{w}^*=\sum_i\alpha_i^*y_i\phi(\boldsymbol{x}_i)$ 只需核求值 |

这正是《凸优化问题举例》§硬间隔 SVM 对偶「$d\gg N$ 时解对偶更好」的核化推广：**特征维可以无穷，对偶维数仍是样本数 $m$**。

### 4.6 核矩阵在 SMO 中的用法

§5 的 SMO 公式中，凡出现 $Q_{ij}=y_i y_j\boldsymbol{x}_i^T\boldsymbol{x}_j$ 处，一律改为 $Q_{ij}=y_i y_j K_{ij}$：

- **初始化**：预计算 $\boldsymbol{G}$（$\mathcal{O}(m^2 n)$ 对 RBF/线性）或**按列懒加载**；
- **两变量更新**：$Q_{ii},Q_{jj},Q_{ij}$ 与 $E_i-E_j$ 仅依赖核行/列；
- **预测**：$\sum_i \alpha_i y_i K(\boldsymbol{x}_i,\boldsymbol{x})+b$，非支持向量项 $\alpha_i=0$ 可跳过。

内存 $\mathcal{O}(m^2)$ 是核 SVM 的主要瓶颈；$m>10^4$ 时常用**线性核**、**Nyström / 随机傅里叶特征**近似、或**线性 SVM 的原始形式**（LIBLINEAR）规避全 Gram 矩阵。

### 4.7 调参与模型选择

核 SVM 的有效自由度来自 $(C,\text{核参数})$：

1. **网格搜索 / 交叉验证**：在验证集上选使准确率或 AUC 最大的 $(C,\gamma)$ 等；
2. **$C$–$\gamma$ 耦合**：大 $\gamma$（复杂边界）常配较小 $C$ 以防过拟合；小 $\gamma$ 可试较大 $C$；
3. **尺度**：RBF 对特征尺度敏感，常先**标准化**各维至零均值单位方差。

问题仍是**凸**的：给定 $(C,\gamma)$，(D-kernel) 全局最优唯一；非凸性仅来自离散的超参搜索，不在 QP 本身。

### 4.8 小结

核技巧不改变 SVM 的**凸 QP + 强对偶 + 支持向量稀疏**结构，只把内积换为 $K$，使最大间隔原则在隐式特征空间 $\mathcal{H}$ 中成立。实现链：**选核 → 构造 $G$ → 解 (D-kernel)（SMO / QP）→ 用核线性组合预测**；§5 SMO 无需修改逻辑，仅将内积替换为 $K_{ij}$。

---

## 5. SMO 算法

(D-soft) 是 $m$ 维**盒约束 QP**，Hessian $Q_{ij}=y_i y_j K_{ij}$（$K_{ij}=K(\boldsymbol{x}_i,\boldsymbol{x}_j)$，线性核时 $K_{ij}=\boldsymbol{x}_i^T\boldsymbol{x}_j$）半正定。通用内点法每步 $\mathcal{O}(m^3)$，$m$ 为万级时偏慢。**SMO**（Sequential Minimal Optimization，Platt 1998）把 (D-kernel) 拆成一系列**极小**子问题：每步只动 **2 个** $\alpha$，在保持 $\sum_k\alpha_k y_k=0$ 与 $[0,C]$ 的前提下解析更新，无需通用 QP 求解器。思想来自 Osuna 等（1997）的**分解法**：固定其余变量，低维子 QP 有闭式解。

### 5.1 为何恰好两个变量？

对偶 (D-kernel) 除盒约束 $0\le\alpha_i\le C$ 外，还有**一条等式** $\sum_i\alpha_i y_i=0$。

| 每步优化变量数 | 等式 + 盒约束 | 子问题 |
| :--- | :--- | :--- |
| **1 个** | 改 $\alpha_j$ 后一般破坏 $\sum\alpha_i y_i=0$ | 需在一条线上投影，无简洁闭式 |
| **2 个** | $\alpha_i y_i+\alpha_j y_j=\zeta$ 将二者绑在仿射直线上；沿直线做**一维**二次极值 | **有解析解** + clip |
| $\ge 3$ 个 | 子问题维数升高 | 需小型 QP，失去 SMO 的轻量优势 |

因此 SMO 选 **2** 为「能保等式、又能手算」的最小工作集大小。

### 5.2 两变量子问题：从等式到单变量二次

固定 $i\neq j$，记其余 $\alpha_k$ 不变，

$$
\zeta = -\sum_{k\neq i,j}\alpha_k y_k
\quad\Longrightarrow\quad
\alpha_i y_i + \alpha_j y_j = \zeta,
\qquad
\alpha_i = y_i(\zeta - y_j\alpha_j).
$$

将 $\alpha_i$ 代入对偶目标 $\theta(\boldsymbol{\alpha})$（§3.2，核矩阵 $Q_{uv}=y_u y_v K_{uv}$），得仅关于 $\alpha_j$ 的**凹二次函数**（因 $Q\succeq 0$）。记当前 $\alpha_j$ 为 $\alpha_j^{\mathrm{old}}$，沿可行方向对 $\alpha_j$ 求极大，得**未 clip 更新**（Platt / LIBSVM 标准式）：

$$
\eta = Q_{ii} + Q_{jj} - 2Q_{ij},
$$

$$
\alpha_j^{\mathrm{new,unc}}
= \alpha_j^{\mathrm{old}} + y_j\,\frac{E_i - E_j}{\eta},
\quad y_i\neq y_j;
$$

$$
\alpha_j^{\mathrm{new,unc}}
= \alpha_j^{\mathrm{old}} + \frac{E_i - E_j}{\eta},
\quad y_i = y_j.
$$

其中 **预测误差**（未取 $\mathrm{sign}$）

$$
E_k = f(\boldsymbol{x}_k) - y_k,
\qquad
f(\boldsymbol{x})=\sum_{t=1}^{m}\alpha_t y_t K(\boldsymbol{x}_t,\boldsymbol{x})+b.
$$

$\eta>0$ 时子问题严格凹，上式即牛顿步；$\eta\le 0$ 时跳过该对 $(i,j)$（核非 PSD 或数值退化）。

**盒约束 clip**：$\alpha_j^{\mathrm{new}}=\mathrm{clip}(\alpha_j^{\mathrm{new,unc}},\,L,\,H)$，$[L,H]\subseteq[0,C]$ 由 $\alpha_i$ 同步落在 $[0,C]$ 推出：

| 标签关系 | $L$ | $H$ |
| :--- | :--- | :--- |
| $y_i\neq y_j$ | $\max(0,\;\alpha_j^{\mathrm{old}}-\alpha_i^{\mathrm{old}})$ | $\min(C,\;C+\alpha_j^{\mathrm{old}}-\alpha_i^{\mathrm{old}})$ |
| $y_i=y_j$ | $\max(0,\;\alpha_i^{\mathrm{old}}+\alpha_j^{\mathrm{old}}-C)$ | $\min(C,\;\alpha_i^{\mathrm{old}}+\alpha_j^{\mathrm{old}})$ |

若 $L=H$，该对无法进展，换 $(i,j)$。由等式得

$$
\alpha_i^{\mathrm{new}}
= \alpha_i^{\mathrm{old}} + y_i y_j\bigl(\alpha_j^{\mathrm{old}}-\alpha_j^{\mathrm{new}}\bigr).
$$

若 $|\alpha_j^{\mathrm{new}}-\alpha_j^{\mathrm{old}}|<\varepsilon$（容差，常 $10^{-3}$），视为无进展，不更新 $b,E$。

**直观**：$E_i-E_j$ 衡量两样本相对间隔违背；$|E_i-E_j|$ 大则一步对偶目标增量大——这是启发式 2 的依据。

### 5.3 KKT 条件与 SMO 的终止准则

最优 $(\boldsymbol{\alpha}^*,b^*)$ 满足 §3.3 的 KKT。实现中用容差 $\varepsilon$ 做**近似 KKT**（LIBSVM 风格）：

| $\alpha_i$ 区域 | 要求（近似） | 违反时含义 |
| :--- | :--- | :--- |
| $\alpha_i=0$ | $E_i \ge -\varepsilon$ | 样本在间隔外仍「太错」→ 应增大 $\alpha_i$ |
| $0<\alpha_i<C$ | $\lvert E_i\rvert \le \varepsilon$ | 边界样本未在 $y_i f=1$ 上 |
| $\alpha_i=C$ | $E_i \le \varepsilon$ | 难例 / 误分类仍不满足 hinge |

**外循环**：优先检查 $\alpha_i\in(0,C)$ 的**自由支持向量**；若无违反，再扫 $\alpha_i=0$ 与 $\alpha_i=C$。全部满足则停止。SMO 不保证每步下降界，但实践中对凸 QP 极稳。

### 5.4 工作集选择：启发式 1 与 2

每轮选 **工作集** $\{i,j\}$：

**启发式 1（选 $i$）**

1. 扫描 $\alpha_i\in(0,C)$，取**第一个**违反 KKT 的 $i$；
2. 若无，扫描全体 $i$，取第一个违反者；
3. 若仍无，算法终止。

**启发式 2（选 $j$）**

在固定 $i$ 后，在 $j\neq i$ 中使 $|E_i-E_j|$ **最大**——期望单步对偶增量最大。若该 $j$ 导致 $\eta\le 0$ 或 $L=H$，则：

- 先随机试若干 $j$；
- 仍失败则**任意** $j\neq i$ 再试一轮。

**Shrinking（收缩，Joachims）**：当外循环多轮无进展时，将长期 $\alpha_i=0$ 且 $E_i\ge -\varepsilon$（或 $\alpha_i=C$ 且 $E_i\le\varepsilon$）的样本**暂时冻结**，缩小每步扫描范围；最终**展开 (unshrink)** 再全量验 KKT，防止误删潜在支持向量。大规模 LIBSVM 默认启用。

### 5.5 阈值 $b$ 与误差向量 $E$ 的更新

更新 $\alpha_i,\alpha_j$ 后，$f(\boldsymbol{x}_k)$ 对**所有** $k$ 仿射变化。记 $\Delta\alpha_i,\Delta\alpha_j$，则对任意 $k$，

$$
\Delta E_k
= y_i\,\Delta\alpha_i\,K_{ik} + y_j\,\Delta\alpha_j\,K_{jk}.
$$

**$E$ 的维护**：不必重算全表；用上式对 $k=1,\ldots,m$ 做 $\mathcal{O}(m)$ 递推（或只维护违反集合）。核列缓存时 $K_{ik},K_{jk}$ 已就绪。

**$b$ 的更新**（Platt）：若 $0<\alpha_i^{\mathrm{new}}<C$，由 $y_i f(\boldsymbol{x}_i)=1$ 得

$$
b_1 = b - E_i^{\mathrm{new}} - y_i(\alpha_i^{\mathrm{new}}-\alpha_i^{\mathrm{old}})Q_{ii} - y_j(\alpha_j^{\mathrm{new}}-\alpha_j^{\mathrm{old}})Q_{ij}.
$$

若 $0<\alpha_j^{\mathrm{new}}<C$，同理得 $b_2$（下标 $i,j$ 对调）。二者皆有效则 $b=(b_1+b_2)/2$；仅一侧在 $(0,C)$ 则取该侧；**都在边界**（$0$ 或 $C$）时保留旧 $b$ 或取平均（实现细节各库略异）。

### 5.6 算法流程（完整伪代码）

```
输入: {(x_i, y_i)}_{i=1}^m, C, 核 K, 容差 ε
预计算或懒加载 G_ij = K(x_i, x_j);  Q_ij = y_i y_j G_ij
初始化: α ← 0, b ← 0, E_i ← -y_i
numChanged ← 0;  examineAll ← true

while numChanged > 0 或 examineAll:
    numChanged ← 0
    if examineAll:
        for i = 1..m:  numChanged += tryPair(i)   // 启发式 1 全扫
    else:
        for i 满足 α_i ∈ (0,C):  numChanged += tryPair(i)  // 只扫自由 SV
    examineAll ← (numChanged = 0)

函数 tryPair(i):
    if α_i 未违反 KKT (容差 ε): return 0
    j ← argmax_{k≠i} |E_i - E_k|          // 启发式 2；失败则随机/穷举
    计算 η = Q_ii + Q_jj - 2 Q_ij
    if η ≤ 0: return 0
    按 y_i,y_j 算 L, H;  if L = H: return 0
    α_j^new ← clip(α_j^old + (y_j 或 1)·(E_i-E_j)/η, L, H)  // 见 §5.2
    if |α_j^new - α_j^old| < ε: return 0
    α_i^new ← α_i^old + y_i y_j (α_j^old - α_j^new)
    更新 b（§5.5）
    for k = 1..m:  E_k ← E_k + y_i Δα_i K_ik + y_j Δα_j K_jk
    return 1

// 可选: shrinking 冻结长期不活跃 i；结束前 unshrink 全验 KKT
返回 α, b
预测: sign( Σ_i α_i y_i K(x_i, x) + b )
```

### 5.7 与通用 QP、坐标下降的关系

| 方法 | 每步工作集 | 子问题 | 典型场景 |
| :--- | :--- | :--- | :--- |
| **SMO** | 2 个 $\alpha$ | 解析 + clip | 核 SVM，$m\sim 10^3$–$10^5$ |
| **内点法** (Mosek, ECOS) | 全体变量 | 牛顿解 KKT | 中小 $m$、需高精度 |
| **OSQP** 等 ADMM | 全体或稀疏结构 | 迭代 | 线性核、稀疏特征 |
| **坐标下降** | 1 个 $\alpha$ | 一维搜索 | 需投影到 $\sum\alpha_i y_i=0$；SMO 可看作**约束感知**的 2 坐标块下降 |

SMO 的优势在于**利用 SVM 对偶的等式结构**：2 变量足以在仿射子空间上闭式极大化，且 $E_k$、$Q$ 的更新极规律。劣势是**无多项式时间保证**（最坏情形迭代次数无界），但凸 QP 上几乎总收敛到 $\varepsilon$-KKT。

### 5.8 复杂度与实现要点

| 主题 | 说明 |
| :--- | :--- |
| **每步时间** | 更新 2 个 $\alpha$ + $\mathcal{O}(m)$ 刷新 $E$；选 $j$ 启发式 2 为 $\mathcal{O}(m)$ |
| **总迭代** | 实践常 $10^2$–$10^6$ 步，与 $m$、$C$、核、数据可分性相关；无通用上界 |
| **内存** | 全核矩阵 $\mathcal{O}(m^2)$；**列缓存**只存活跃列，$\mathcal{O}(m\cdot|\mathrm{cache}|)$ |
| **数值** | $\eta\le 0$ 跳过；特征标准化；$C$ 过大时 $\alpha$ 触边界多，收敛变慢 |
| **多类** | **一对一**（$K$ 个二分类 SVM）或 **一对多**；每类独立跑 SMO |
| **替代** | 小 $m$ 可直接 OSQP 解 (D-kernel)；线性核大规模用 **LIBLINEAR**（原始坐标下降） |

**LIBSVM**（C.-C. Chang & C.-J. Lin）是 SMO 最广泛实现：$C$-SVM、$\nu$-SVM、回归 SVR 共用同一套两变量更新与启发式；读其 `svm.cpp` 即 Platt SMO 的工程化版本。

### 5.9 小步推演（与 §6 衔接）

对 §6 两点硬间隔例：$Q_{11}=0,Q_{22}=4,Q_{12}=0$，$\alpha_1=\alpha_2=0$ 时 $E_1=-1,E_2=+1$。取 $i=1,j=2$，$y_i\neq y_j$，$\eta=4$，

$$
\alpha_2^{\mathrm{new,unc}} = 0 + (-1)\cdot\frac{E_1-E_2}{4} = 0 + (-1)\cdot\frac{-2}{4} = \frac{1}{2},
$$

clip 到 $[0,\infty)$ 仍为 $1/2$；由 $\alpha_1-\alpha_2=0$ 得 $\alpha_1=1/2$。一步即达最优 $\boldsymbol{\alpha}^*=(1/2,1/2)^T$，说明在极小问题上 SMO 可**一步收敛**；一般数据需多轮工作集更新。

---

## 6. 小例（硬间隔）

$\boldsymbol{x}_1=(0,0),y_1=+1$；$\boldsymbol{x}_2=(2,0),y_2=-1$。线性可分，间隔边界为 $x_1=1$。

(P-hard) 一解为 $\boldsymbol{w}^*=(-1,0)^T$，$b^*=1$：$y_1(\boldsymbol{w}^{*T}\boldsymbol{x}_1+b^*)=1$，$y_2(\boldsymbol{w}^{*T}\boldsymbol{x}_2+b^*)=1$，两点均在间隔边界上，均为支持向量。

对偶：$\max\;\alpha_1+\alpha_2-2\alpha_2^2$（$Q_{11}=0,\,Q_{22}=4,\,Q_{12}=0$）s.t. $\alpha_1-\alpha_2=0$，$\alpha_i\ge 0$。令 $\alpha_1=\alpha_2=\alpha$ 得 $\max\;2\alpha-2\alpha^2$，最优 $\alpha^*=1/2$，$d^*=1/2=p^*$。还原 $\boldsymbol{w}^*=\sum_i\alpha_i y_i\boldsymbol{x}_i=(-1,0)^T$。

**SMO 视角**：从 $\boldsymbol{\alpha}=\boldsymbol{0}$ 出发，§5.9 已算一步 SMO 即得 $\boldsymbol{\alpha}^*=(1/2,1/2)^T$；多类、软间隔时需多轮工作集更新与 clip。

---

## 7. 与其它篇章的关系

| 篇章 | 联系 |
| :--- | :--- |
| 《凸优化与KKT条件》 | Lagrangian、对偶、KKT、互补松弛 |
| 《QP与SOCP》 | (P-soft) 为凸 QP；内点法 / 活动集法可替代 SMO |
| 《线性规划》 | 无约束方向上的对偶间隙、活跃集直觉 |
| 《凸优化问题举例》 | 硬间隔 SVM 对偶；核化后 $d\to\infty$ 时对偶仍 $m$ 维 |
| MILP | 非凸扩展（特征选择整数）不在本篇 |

---

## 本篇小结

SVM 训练是**凸 QP**：原始 (P-soft) 最小化 $\|\boldsymbol{w}\|^2$ 与松弛惩罚；对偶 (D-soft) 为 $m$ 维二次目标 + 一线性等式 + 盒约束。**强对偶**下支持向量对应 $\alpha_i>0$。**核技巧**将内积换为 $K_{ij}$，在同一对偶 QP 上得到非线性边界。**SMO** 每步在二维工作集上解析极大化对偶、用 $E_k$ 与启发式选点维护 KKT，是 LIBSVM 等工具的核心求解器。
