---
layout: post
title: "复平面上的 Möbius 变换"
date: 2026-06-17
category: Parameterization
categories: ["Parameterization", "Parameterization-ConformalMapping"]
---

## 为何在共形参数化中反复出现 Möbius 变换？

黎曼映射定理保证：单连通真子集 $U \subsetneq \mathbb{C}$ 与单位圆盘 $\mathbb{D}$ 之间存在共形映射。但映射**不唯一**——任意两个这样的映射只差一个 $\mathbb{D}\to\mathbb{D}$ 的共形自同构，即 **Möbius 变换**。因此：

- 圆盘参数化、上半平面参数化在求得一个解之后，仍需选定规范（fix 3 个边界点，或最小化面积畸变，或做 Möbius 配准）；
- 球面参数化 $f:S^2\to M$ 同样只确定到 $S^2\to S^2$ 的 Möbius 群；
- 双曲圆盘上的共形映射唯一性模 $PSL(2,\mathbb{R})$，本质仍是 Möbius 变换。

`2016-07-14-共形映射介绍` 已给出入门形式；本文系统整理**复平面视角**下的代数、几何与离散实现要点，为 `Mobius Registration` 及各类 disk/sphere 参数化后处理打底。

---

## 一般形式与矩阵表示

**Möbius 变换**（分式线性变换）是 $\hat{\mathbb{C}}=\mathbb{C}\cup\{\infty\}$ 上形如

$$
\boxed{\; f(z)=\frac{az+b}{cz+d},\qquad ad-bc\neq 0 \;}
$$

的映射。可用 $2\times 2$ 复矩阵表示：

$$
M=\begin{pmatrix}a&b\\c&d\end{pmatrix},\quad
f(z)=\frac{a z+b}{c z+d}.
$$

矩阵整体乘以非零复数不改变映射；商群为 $PSL(2,\mathbb{C})=SL(2,\mathbb{C})/\{\pm I\}$。

**复合**：$f\circ g$ 对应矩阵乘法（注意顺序：先 $g$ 后 $f$ 则矩阵为 $M_f M_g$）。

**逆映射**：

$$
f^{-1}(w)=\frac{d w - b}{-c w + a}.
$$

---

## 几何性质（共形几何的"原子操作"）

1. **保角**：圆周角不变；等价于全纯且 $f'\neq 0$。
2. **保圆**：圆与直线（视为过 $\infty$ 的圆）映为圆/直线。
3. **保交比**（cross ratio）：对四个互异点 $z_1,z_2,z_3,z_4$，

$$
(z_1,z_2;z_3,z_4)=\frac{(z_1-z_3)(z_2-z_4)}{(z_1-z_4)(z_2-z_3)}
$$

在 Möbius 变换下不变。交比是共形不变量的基本生成元。

4. **三对点定变换**：给定 $z_1,z_2,z_3$ 映到 $w_1,w_2,w_3$，存在唯一 Möbius 变换；常用公式通过交比直接写出。

---

## 单位圆盘 $\mathbb{D}$ 的自同构

将 $\mathbb{D}$ 映到自身的保定向共形映射恰为

$$
\boxed{\;\varphi_a(z)=e^{i\theta}\,\frac{z-a}{1-\bar{a}\,z},\qquad |a|<1,\;\theta\in\mathbb{R}\;}
$$

**三个实自由度**：反演中心 $a$（2 维）+ 旋转 $\theta$（1 维）。这是黎曼映射"模 Möbius"唯一性的具体体现。

特例：

| 参数 | 效果 |
| :--- | :--- |
| $a=0$ | 纯旋转 $z\mapsto e^{i\theta}z$ |
| $\theta=0$, $a\in\mathbb{D}$ | **圆盘反演**（hyperbolic translation），将 $a$ 映到 $0$ |
| $a\to 1/\bar{a}$（在边界外） | 关于单位圆的反射组合 |

**Schwarz 引理推论**：$\mathbb{D}\to\mathbb{D}$ 的全纯自映射若固定 $0$，则 $|f(z)|\le |z|$，等号当且仅当 $f$ 为旋转。

---

## 上半平面 $\mathbb{H}$ 与双曲几何

上半平面 $\mathbb{H}=\{z:\mathrm{Im}\,z>0\}$ 的自同构群为 $PSL(2,\mathbb{R})$，同样由

$$
z\mapsto \frac{az+b}{cz+d},\quad a,b,c,d\in\mathbb{R},\; ad-bc>0
$$

给出。$\mathbb{H}$ 与 $\mathbb{D}$ 通过 Cayley 变换互相对应：

$$
\mathcal{C}(z)=\frac{z-i}{z+i}:\mathbb{H}\to\mathbb{D},\qquad
\mathcal{C}^{-1}(w)=i\,\frac{1+w}{1-w}.
$$

带边界的曲面共形展平到 $\mathbb{H}$ 或 $\mathbb{D}$ 后，"还差一个"的正是上述自同构——混合整数全局参数化、圆盘切割等算法中，周期/接缝数据常在此等价类内变化。

---

## 球面 $S^2$ 与立体投影

球面与 $\hat{\mathbb{C}}$ 通过**立体投影**（stereographic projection）共形等价。取北极 $N=(0,0,1)$ 投影到平面 $z=0$：

$$
\pi(x,y,z)=\frac{x+iy}{1-z},\qquad
\pi^{-1}(w)=\frac{2\,\mathrm{Re}\,w}{|w|^2+1},\;\frac{2\,\mathrm{Im}\,w}{|w|^2+1},\;\frac{|w|^2-1}{|w|^2+1}.
$$

$S^2\to S^2$ 的 Möbius 变换（保定向共形自同构）在 $\mathbb{R}^3$ 中可分解为**偶数次球面反演**；不含旋转时，单次反演

$$
\eta_c(x)=\frac{(1-|c|^2)x + c}{|x+c|^2} + c,\qquad c\in B^3
$$

将 $S^2$ 映到自身（`Mobius Registration` 的中心化算法即基于此）。

**Lorentz 模型**：嵌入 $S^2\subset\mathbb{R}^3$ 为 $x^2+y^2+z^2=1$，齐次坐标 $(x,y,z,t)$ 配合 Lorentz 内积 $p^{\mathsf T}E p=x^2+y^2+z^2-t^2$，Möbius 变换对应保持 $E$ 的线性变换（Lorentz 群）。Springborn 的中心化能量在双曲空间上 geodesically convex，是另一套常用实现。

---

## 与共形参数化算法的衔接

### 圆盘参数化后处理

求得 $f:M\to\mathbb{D}$ 后，常再乘 $\varphi_\omega\circ\psi$ 以：

- **固定三点**边界数据（消除 Möbius 自由度）；
- **最小化面积畸变**或**平衡顶点分布**（CDCP 等构造算法中的 $\psi_\omega$）；
- **对齐语义特征**（与另一张盘的映射配准）。

### 球面参数化

genus-0 闭曲面：$f:S^2\to M$。数值迭代（CMCF、Dirichlet 能量最小化等）可能**漂移**到面积高度集中的 Möbius 等价类；中心化反演把共形因子 $\lambda$ 的"质心"移到原点，抑制 drift（见 `Mobius Registration`）。

### 双曲圆盘（拓扑圆盘）

Le et al. 的 **Optimal Möbius Search** 在 $\mathbb{D}\to\mathbb{D}$ 上用分支定界**全局最优**搜索对齐变换，避免局部极小——与本文代数形式直接对应。

---

## 离散实现要点

1. **复数运算**：顶点坐标 $z_i\in\mathbb{C}$，Möbius 作用为 $z_i'=(a z_i+b)/(c z_i+d)$；注意 $c\neq 0$ 时分母可能接近零（接近极点）。
2. **球面反演**：在 $\mathbb{R}^3$ 中对单位球顶点直接做 $\eta_c$，无需显式共形因子；Gauss–Newton 可用对称 Jacobian $J_\mu$ 加速。
3. **组合**：先中心化（反演），再旋转（SO(3) FFT 相关）；旋转在复平面上为 $z\mapsto e^{i\theta}z$ 或 $3\times 3$ 正交矩阵作用在球面坐标上。
4. **验证**：检查交比、单位圆边界映射、或 $\lambda$ 质心是否为零。

---

## 参考文献

1. T. Needham, *Visual Complex Analysis* — 直观几何。
2. J. B. Conway, *Functions of One Complex Variable* — 标准定理与 $\mathbb{D}$ 自同构。
3. M. Springborn, *A variational principle for domino tilings* (2005) 及后续关于 Möbius 中心化的工作。
4. M. Bern, D. Eppstein, *Optimal Möbius Transformations for Information-Centric Operations on Mesh Models* (WADS 2001).
5. H. Le, A. V. Bronstein, M. M. Bronstein, *Conformal Surface Alignment With Optimal Mobius Search* (2016).

可视化推荐：[Möbius Transformations Revealed](https://www-users.cse.umn.edu/~arnold/moebius/).
