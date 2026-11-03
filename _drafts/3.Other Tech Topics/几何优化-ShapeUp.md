---
layout: post
title: "Shape-Up"
date: 2026-06-17
category: Parameterization
categories: ["Parameterization", "Parameterization-GeometricOptimization"]
---

## 概述

Bouaziz、Deuss、Schwartzburg、Weise、Pauly 在 SGP 2012 提出 [**Shape-Up: Shaping Discrete Geometry with Projections**](https://doi.org/10.1111/j.1467-8659.2012.03171.x)（CGF 31(5), 1657–1667），用**形状约束 + 投影**统一大量几何处理任务。

核心只有两个概念：

| 概念 | 作用 |
| :--- | :--- |
| **Shape Proximity（形状邻近函数）** | 度量当前顶点与“满足约束的目标形状”之间的加权平方距离 |
| **Shape Projection（形状投影算子）** | 在局部步把顶点（或差分坐标）投影到约束流形上，得到目标形状 |

二者配合 **Local/Global 交替优化**：局部步各约束独立、可并行；全局步解**固定稀疏线性系统**融合冲突。无需手写梯度，换约束只需换投影算子。

后续延伸：**ShapeOp** 库（建筑/设计）、**Projective Dynamics**（物理仿真，SIGGRAPH 2014）、**Anderson 加速**（Wang et al. 2018）均建立在此框架上。

---

## 优化问题

顶点位置矩阵 $\mathbf{Q}\in\mathbb{R}^{n\times d}$（$d=2$ 或 $3$）。对第 $i$ 个形状约束：

- $\mathbf{A}_i\in\mathbb{R}^{k_i\times n}$：选取相关顶点并做线性变换（常用**差分坐标**，见下）；
- $\mathcal{C}_i$：可行目标形状集合（平面、圆、固定点等）；
- $\mathbf{P}_i\in\mathbb{R}^{k_i\times d}$：辅助变量，表示 $\mathbf{A}_i\mathbf{Q}$ 在 $\mathcal{C}_i$ 上的**最近投影**。

**形状邻近函数**即

$$
\frac{w_i}{2}\,\|\mathbf{A}_i\mathbf{Q}-\mathbf{P}_i\|_F^2,
$$

$w_i$ 为权重。指示函数 $\sigma_i(\mathbf{P}_i)=0$ 当 $\mathbf{P}_i\in\mathcal{C}_i$，否则 $+\infty$。

总目标：

$$
\boxed{\;
\min_{\mathbf{Q},\{\mathbf{P}_i\}}\;
\sum_i \frac{w_i}{2}\|\mathbf{A}_i\mathbf{Q}-\mathbf{P}_i\|_F^2 + \sigma_i(\mathbf{P}_i)
\;}
$$

Laplacian 公平性可视为 $\mathcal{C}_i=\{\mathbf{0}\}$、$\mathbf{A}_i$ 为 Laplacian 一行的特例。

---

## Local / Global 迭代

```
输入: 初始顶点 Q, 约束集合 {Ci, Ai, wi}
重复直到收敛:
  【Local】固定 Q，对每个 i 并行:
         Pi ← Proj_{Ci}(Ai Q)    // 形状投影算子
  【Global】固定 {Pi}，解线性系统:
         (Σ wi AiᵀAi) Q = Σ wi Aiᵀ Pi
```

全局步等价于对所有邻近项的**加权最小二乘**：

$$
\boxed{\;
\left(\sum_i w_i\,\mathbf{A}_i^{\mathsf T}\mathbf{A}_i\right)\mathbf{Q}
= \sum_i w_i\,\mathbf{A}_i^{\mathsf T}\mathbf{P}_i
\;}
$$

**性质**：

- 系统矩阵 $\sum w_i\mathbf{A}_i^{\mathsf T}\mathbf{A}_i$ **与迭代无关** → 可 Cholesky 预分解，每步仅换右端项；
- Local / Global 每步都**不增**目标值 → 保证收敛到局部极小；
- 通常 **5–20 次**迭代即得可用近似解（块坐标下降，收敛为次线性）。

与 **ARAP / SLIM** 的 local/global 同族：ARAP 的 local 是逐三角 SVD 求最佳旋转，global 解 cot-Laplacian；Shape-Up **抽象出“投影 + 二次距离”**，约束可任意组合。

---

## 差分坐标：加速收敛的关键

若 $\mathbf{A}_i=\mathbf{B}_i=\mathbf{I}$，仅约束绝对位置，信息传播慢（类似 Jacobi）。

Shape-Up 推荐 $\mathbf{A}_i=\mathbf{B}_i$ 为**差分坐标矩阵**（减均值、边向量、Laplacian 行等），消去全局平移/刚性分量，使局部投影更快影响全局。Projective Dynamics 明确引用：*“Using differential coordinates greatly improves the convergence speed”* [Bouaziz et al. 2012]。

这与 **Liu et al. 2008** 参数化 local/global、**Sorkine–Laplacian** 编辑一脉相承。

---

## 常见形状投影算子

投影 $\mathrm{Proj}_{\mathcal{C}_i}(\mathbf{A}_i\mathbf{Q})$ 多为**最小二乘拟合初等几何体**（常可用 SVD / 闭式解）：

| 约束 | 可行集 $\mathcal{C}_i$ | 投影含义 |
| :--- | :--- | :--- |
| **位置** | 固定点 $\mathbf{q}^*$ | $\mathbf{P}_i=\mathbf{q}^*$ |
| **平面性** | 四边形/多边形共面 | 顶点投影到最佳拟合平面 |
| **共圆（circular）** | 面顶点在圆上 | 拟合外接圆后投影到圆周 |
| **相似 / 刚性 one-ring** | 局部相似或刚体 | 去中心化 + SVD 求 $R,s$（ARAP local 步） |
| **边长** | $\|\mathbf{e}\|=L$ | 缩放到目标长度 |
| **Laplacian** | $\delta=0$ | $\mathbf{P}_i=\mathbf{0}$ |
| **共形参数化** | 保角关系 | 与 LSCM 等能量结合的投影形式 |

**组合即应用**：平面四边形网格 = 每面平面约束 + 可选公平项；圆网格 = 共圆约束；形变 = 相似 one-ring + 手柄位置约束。

---

## 论文中的应用示例

1. **平面 / 圆多边形网格**：直接优化顶点满足面约束，无需先自由变形再投影。
2. **形状空间探索（shape space exploration）**：在约束流形上插值或滑动参数。
3. **网格质量改善**：拉普拉斯 + 边长 / 角度类约束。
4. **保形形变**：共形邻近项 + 位置约束（对比非共形形变，少剪切、保纹理细节）。
5. **共形参数化**：与 LSCM 等相比，local/global 框架下可注入更多约束且保持无翻转倾向（论文 2D 对比实验）。

---

## 与 Local/Global 家族的关系

```
Shape-Up (2012)          几何约束、投影算子组合
    ↓
Projective Dynamics (2014)  + 质量矩阵 / 惯性项 → 隐式积分
    ↓
ShapeOp                    建筑形态找形、交互设计
    ↓
Anderson Acceleration (2018)  固定点视角加速 local/global
```

| 方法 | Local 步 | Global 步 | 典型用途 |
| :--- | :--- | :--- | :--- |
| **Shape-Up** | 通用 $\mathrm{Proj}_{\mathcal{C}_i}$ | $\mathbf{A}_i^{\mathsf T}\mathbf{A}_i$ 预分解 | 平面/圆网格、约束建模 |
| **ARAP** | 逐面最佳旋转 $R$ | 调和 / Laplacian 系统 | 网格形变、参数化 |
| **SLIM** | 加权旋转 + 特殊 $W$ | 重加权 Laplacian | 无翻转映射 |
| **ProjDyn** | 弹性约束投影 | $(\mathbf{M}/h^2+\sum w_i\mathbf{A}_i^{\mathsf T}\mathbf{A}_i)\mathbf{Q}=\cdots$ | 物理仿真 |

Shape-Up 的抽象更强：**非物理、纯几何**；ProjDyn 把同一结构加上 $\mathbf{M}/h^2$ 与动量项。

---

## 实现与扩展

- **ShapeOp**：开源 C++ 库，封装 local/global + 隐式积分（见 Bouaziz et al. 2014）。
- **Deng et al. 2015** *Interactive Design Exploration for Constrained Meshes*：在 Shape-Up 约束流形上交互探索。
- **加速**：Wang et al. 将每轮 local/global 视为固定点 $G(\mathbf{Q})$，用 **Anderson acceleration** 减少迭代次数（每步代价略增）。

对仅需快速原型的情况，也可在 `TinyAD` 中写能量求牛顿步；Shape-Up 的优势是**约束即投影、无需求导**。

---

## 算法设计要点（小结）

1. 把约束写成 $\|\mathbf{A}_i\mathbf{Q}-\mathbf{P}_i\|^2$，$\mathbf{P}_i$ 在 local 步闭式更新。
2. 用**差分坐标**选 $\mathbf{A}_i$，少迭代、更稳。
3. 预分解 $\mathbf{A}^{\mathsf T}\mathbf{A}$，global 步对 $x,y,z$ 三分量并行回代。
4. 冲突约束通过 global 步**最小二乘折中**；权重 $w_i$ 调节软硬。
5. 新应用 = 设计 $\mathcal{C}_i$ + $\mathrm{Proj}$，不必改求解器骨架。

---

## 参考文献

1. S. Bouaziz, M. Deuss, Y. Schwartzburg, T. Weise, M. Pauly. **Shape-Up: Shaping Discrete Geometry with Projections**. *Computer Graphics Forum* 31(5), SGP 2012. [DOI: 10.1111/j.1467-8659.2012.03171.x](https://doi.org/10.1111/j.1467-8659.2012.03171.x)
2. S. Bouaziz, S. Martin, T. Liu, L. Kavan, M. Pauly. **Projective Dynamics**. *ACM Trans. Graph.* 33(4), SIGGRAPH 2014.
3. T. Liu, S. Bouaziz, L. Kavan. **A Local/Global Approach to Mesh Parameterization**. CGF 2008.（ARAP / local-global 参数化）
4. Y. Wang et al. **Anderson Acceleration for Geometry Optimization and Physics Simulation**. SIGGRAPH 2018.
5. B. Deng et al. **Interactive Design Exploration for Constrained Meshes**. *Computer-Aided Design* 61, 2015.
