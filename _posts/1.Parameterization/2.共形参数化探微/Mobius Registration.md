---
layout: post
title: "Möbius Registration"
date: 2026-06-17
category: Parameterization
categories: ["Parameterization", "Parameterization-ConformalMapping"]
---

## 问题：球面共形参数化不唯一

单连通化（genus-0）闭曲面的**球面共形参数化** $f:S^2\to M$ 由单值化定理保证存在，但仅确定到 **Möbius 变换** $S^2\to S^2$。两张曲面 $M_1,M_2$ 之间的"自然"映射

$$
f_2 \circ f_1^{-1} : S^2 \to S^2
$$

因此依赖如何选取各自的参数化——类比刚体配准中需指定平移与旋转。

Baden、Crane、Kazhdan 在 SGP 2018 的 [*Möbius Registration*](https://www.cs.cmu.edu/~kmcrane/Projects/MobiusRegistration/paper.pdf) 给出**快速、无需 landmark** 的流程：

1. 分别计算球面共形参数化（任意现有算法，如 CMCF）；
2. **中心化**（canonical inversion）：消去 Möbius 反演自由度，压低面积畸变；
3. **旋转对齐**：在 SO(3) 上最大化两共形因子场的相关。

开源实现：[mkazhdan/MoebiusRegistration](https://github.com/mkazhdan/MoebiusRegistration)（含 `SphereMap`、`MobiusCenter`、`MobiusAlign`）。

---

## 数学背景：反演与质心

### 球面反演

对 $c\in B^3$（开单位球），定义

$$
\eta_c(x)=\frac{(1-|c|^2)x + c}{|x+c|^2} + c,
$$

将 $S^2$ 映到 $S^2$。所有保定向的 $S^2\to S^2$ 共形映射可表为**偶数次**反演（含旋转）；中心化只考虑**单次反演**（旋转视为待对齐的剩余自由度）。

### 共形因子与质心

参数化 $f:S^2\to M$ 下，目标曲面面积元 $dA=\lambda\, dA_{S^2}$，$\lambda:S^2\to\mathbb{R}_{>0}$ 为**共形因子**。定义加权质心

$$
\mu_0 = \int_{S^2} \lambda(x)\, x\, dA_{S^2} = \int_{S^2} x\, dA.
$$

对反演 $\eta_c$，新参数化 $f\circ\eta_c^{-1}$ 的质心为

$$
\mu(c)=\int_{S^2} \eta_c(x)\, dA(x).
$$

**目标**：找 $c\in B^3$ 使 $\mu(c)=0$，即最小化能量

$$
E(c)=\tfrac{1}{2}\lVert \mu(c)\rVert ^2.
$$

### 梯度与唯一性

在 $c=0$ 处，Jacobian 有闭式

$$
J_\mu\big|_{c=0}=2\int_{S^2} (I - x x^{\mathsf T})\, dA,
$$

梯度 $\nabla_c E = J_\mu^{\mathsf T}\mu$。沿 $\nabla$ 下降**全局收敛**到唯一极小点：$J_\mu$ 满秩，且 $c\to\partial B^3$ 时 $E\to\frac{1}{2}(\int dA)^2$。这与 Springborn 的质心中心化、Bern–Eppstein 的拟凸规划等不同，但保证更简单、实现更轻。

---

## 算法 1：Möbius 中心化（离散）

输入：三角网格球面参数化，顶点 $V\subset S^2$，三角形 $\mathcal{T}$，原曲面面积权 $A(\tau)$。

```
重复直到 |μ| ≤ ε:
  μ ← Σ_{τ∈T} C(τ) A(τ)          // 三角形质心 C(τ) 归一化到单位球
  Jμ ← 2 Σ_{τ} A(τ) (I - C(τ)C(τ)ᵀ)
  c ← -Jμ⁻¹ μ                    // Gauss-Newton 一步（Jμ 对称）
  对每个顶点 v: v ← η_c(v)       // 应用反演
```

**要点**：

- 无需显式计算 $\lambda$；面积权 $A(\tau)$ 已编码共形缩放；
- 假设 $|v|=1$；非单位球需先归一化；
- 大模型可用线搜索（$c\leftarrow\alpha c$，$\alpha\in(0,1)$）。

**应用（单曲面）**：

- 稳定 CMCF 等迭代，防止顶点坍缩到一点（图 2）；
- 球面 orbifold 参数化：覆盖空间参数化后中心化，恢复对称性；
- 降低 conformal surface flow 中的面积漂移。

---

## 算法 2：旋转对齐（两曲面配准）

中心化后，两曲面球面参数化的共形因子 $\lambda_1,\lambda_2$ 在低阶上已对齐。剩余 **SO(3)** 自由度通过**最大化相关**确定：

### 步骤

1. **栅格化**：将 $(V,\mathcal{T})$ 的共形因子投影到等距矩形网格（equirectangular）；按球面单元面积积分，避免 aliasing（大 $\lambda$ 区域可能只占极小球面补丁）。
2. **低通滤波**：抑制采样噪声。
3. **谱相关**：
   - 对两函数做**快速球谐变换**（SHT）；
   - 各频带内系数交叉相乘，得到旋转谐波域的相关系数；
   - **快速 Wigner-$D$ 逆变换**在 Euler 角网格上求相关峰值 → 最优旋转 $R\in SO(3)$。
4. 带宽 $2\times$ 带限带宽的 Euler 网格以鲁棒检测极大值。

### 为何不用整个 Möbius 群的 FFT？

Möbius 群**非紧**、**6 维**，无法直接套用紧群 FFT。先中心化将问题降到 **3 维旋转**，才可用成熟的 SO(3) 谐波分析（Kostelec–Rockmore 等）。

---

## 广义中心化（可选）

将质心定义推广到函数空间 $\mathcal{F}\subset W^{1,2}(M)$：$\mu_0(\omega)$ 为体积形式 $\omega$ 在 $\mathcal{F}$ 上的 $L^2$ 投影。取 $\mathcal{F}$ 为**低阶球谐函数**时，中心化运动不再限于 Möbius，可在**角度畸变与面积畸变**之间折中（图 5：degree 1 仅反演，更高阶引入非共形修正）。

---

## 实验与鲁棒性

| 场景 | 结果 |
| :--- | :--- |
| 近等距 genus-0 曲面 | 无 landmark 的稠密对应；完美等距时恢复等距 |
| 粗糙对齐 + 最近点投影 | 映射不连续、非单射，仍可推断正确同调配准方向 |
| 反射对称检测 | 对一侧加反射可得 orientation-reversing 配准 |
| 旋转对称形状 | 仅确定到对称群（固有问题，非算法缺陷） |

**局限**：Möbius 变换**刚性**强——大非等距形变时只能作初始化，需后续非共形配准（如 ACAP、functional map 精化）。论文定位：**快速可靠的 initializer**，而非最终非刚性解。

---

## 工具链（MoebiusRegistration 仓库）

| 可执行文件 | 功能 |
| :--- | :--- |
| `SphereMap` | CMCF 球面参数化 + 中心化 + 等距网格输出 `.sgrid` |
| `MobiusCenter` | 对已参数化网格做反演中心化 |
| `MobiusAlign` | 两球面参数化旋转对齐，输出变换后源网格 |

PLY 需含 `x,y,z`（原坐标）与 `px,py,pz`（球面参数位置）。

---

## 与其他方法对比

| 方法 | 特点 |
| :--- | :--- |
| **Landmark / 三点采样** (LF09, LPD13) | 需特征点或大量采样 |
| **Hass–Koehl** (HK15) | 非凸度量畸变能量，更精细但更贵；中心化可替换其初始化 |
| **Li–Hartley** (LH07) | 球谐描述子，无点对点对应 |
| **Optimal Möbius Search** (Le16) | 圆盘拓扑，BnB 全局最优 Möbius |
| **Mobius Voting** (Lipman–Funkhouser 09) | 基于投票的曲面对应 |

---

## 与博客其他章节的关系

- **复平面代数**：见 `Complex_mobius_Transform`（$\mathbb{D}$ 自同构 ↔ 球面反演）。
- **球面参数化算法**：CMCF [KSBC12]、离散调和映射 [GY03] 等产生输入 $f$。
- **映射拓扑**：`surfaceHomologyInfercne` 处理更高 genus 的同调配准；本文仅限 genus-0 共形情形。
- **全局参数化**：球面 orbifold [AKL17] 与中心化结合可强制对称性。

---

## 参考文献

1. A. Baden, K. Crane, M. Kazhdan. **Möbius Registration**. *Computer Graphics Forum* 37(5), SGP 2018.
2. M. Kazhdan, J. Solomon, M. Ben-Chen. **Conformalized Mean Curvature Flow**. SIGGRAPH Asia 2012.
3. M. Springborn. **A variational principle for domino tilings**. 2005.
4. P. Kostelec, D. Rockmore. **FFTs on the Rotation Group**. J. Comput. Phys. 2008.
5. H. Le, A. V. Bronstein, M. M. Bronstein. **Conformal Surface Alignment With Optimal Mobius Search**. 2016.
