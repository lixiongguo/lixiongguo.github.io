---
layout: post
title: "Heat Method：测地距离的热流算法"
category: Parameterization
categories: ["Parameterization", "Parameterization-BasicParameterization"]
mathjax: true
---

> 笔记整理自 Keenan Crane, Clarisse Weischedel, Max Wardetzky — [*Geodesics in Heat*](https://www.cs.cmu.edu/~kmcrane/Projects/HeatMethod/)（ACM TOG 2013 / SGP）。  
> 关键词：**测地距离**、**Eikonal 方程**、热扩散、Poisson 重建。

---

## 1. 要算什么？

在曲面（三角网格、点云、栅格等）上给定源集合 $\gamma$（一点、多点或曲线），求函数 $\phi:M\to\mathbb{R}$：

$$
\phi(x)=\mathrm{dist}_M(x,\gamma)
$$

即沿曲面行走的**最短测地距离**（不是 $\mathbb{R}^3$ 直线距离）。章鱼相邻两腕在空间里很近，沿表面可能很远——测地距离才反映「贴着壳走」的长度。

经典做法包括：精确多源最短路（MMP 等）、快速行进（Fast Marching）直接离散 **Eikonal** 等。Heat Method 走另一条路：用**两次稀疏线性求解**近似 $\phi$，矩阵可预分解，换源点时摊销极快。

---

## 2. Eikonal 方程：距离满足什么 PDE？

光滑情形下，到源的距离函数满足 **Eikonal 方程**：

$$
\lVert \nabla\phi\rVert =1,\qquad \phi\big|_{\gamma}=0
$$

（在可微处；脊线 / 割迹上梯度不可微。）

含义很直白：

- 距离沿「最陡上升」方向的变化率恒为 1；
- 等距线的法向就是 $\nabla\phi$，且单位长度。

数值上直接解 Eikonal 往往要迎风格式、因果更新（Fast Marching 一类），实现与并行都不轻松。Heat Method 的关键洞察是：

> **先只要梯度方向对，模长事后用 Poisson 补回单位长度。**

---

## 3. 热核与 Varadhan 公式（动机）

短时热扩散与测地距离有深刻联系。Varadhan 公式说：若 $u_t(x)$ 是从源扩散出的热核（或热方程解），则

$$
\phi(x)=\lim_{t\to 0}\sqrt{-4t\log u_t(x)}.
$$

直接拿近似热核套这个极限式，数值上很脆——$t$ 太小噪声大，$t$ 太大又偏离测地。Heat Method **不直接用该公式算距离**，而只用到一个更弱、更稳的事实：

对小的 $t$，热场 $u_t$ 的梯度方向近似平行于真实距离梯度 $\nabla\phi$（都指向「离源变远」的方向）。于是可以：

1. 用热扩散拿到方向场；  
2. 单位化；  
3. 再积分回标量距离。

---

## 4. 算法三步（连续版）

$$
\begin{aligned}
\text{I.}&\quad \text{积分热流 }\dot u=\Delta u\text{（固定时间 }t\text{）}\\
\text{II.}&\quad X=-\frac{\nabla u}{\lVert \nabla u\rVert }\\
\text{III.}&\quad \text{解 Poisson }\Delta\phi=\nabla\cdot X
\end{aligned}
$$

- **I**：从源「注热」并扩散一小段时间，得到标量场 $u$（源附近热、远处冷）。  
- **II**：热总是沿测地「下山」最快方向泄漏，$-\nabla u$ 指向离源更远；$X$ 是单位方向场，对应 Eikonal 里「$\nabla\phi$ 应有的方向」。  
- **III**：找标量 $\phi$，使其梯度在 $L^2$ 意义下尽量贴近 $X$。变分给出 $\Delta\phi=\nabla\cdot X$；解完后平移使源上 $\phi\approx 0$。

$t\to 0$ 时 $\phi$ 趋近真测地距离；$t$ 略大则得到更光滑的距离近似（某些应用反而需要这种正则化）。

与 [向量场分解](向量场分解.md) 的联系：第三步正是「已知目标梯度方向，用 Poisson / Hodge 投影恢复势函数」——这里目标梯度是单位场 $X$，势就是距离。

---

## 5. 离散实现要点

### 5.1 时间离散（一步 Backward Euler）

热方程一步隐式格式：

$$
(I - t\Delta)\,u_t = u_0
$$

$u_0$ 在源顶点为 1（或 Kronecker / 面源），其余为 0。只需解**一个**稀疏正定系统。

### 5.2 空间离散

三角网格上常用：

- **Cotangent Laplacian** $\Delta$（与调和映射、参数化同一套）；  
- 梯度 $\nabla u$：分片常 / 面元上由顶点值差分；  
- 散度 $\nabla\cdot X$：与 Tong 等离散 Div 同类组装。

点云、体素网格只需替换「梯度 / 内积 / Laplace」的离散定义，管线不变——这是方法通用性的来源。

### 5.3 时间步 $t$ 怎么选？

经验上取与平均边长相关的尺度，例如

$$
t = h^2
$$

（$h$ 为平均边长；论文有更细的推荐）。$t$ 过小：方向场噪声大；$t$ 过大：过度平滑，短切现象（shortcut）加重。实践中可预分解 $(I-tL)$ 与 $L$，换源只回代。

### 5.4 多源

多个源点 / 源曲线：把它们的初始热量一并置入 $u_0$，一次扩散即得多源距离场（到最近源的距离）。

---

## 6. 性质与对比（笔记）

| 方面 | Heat Method | Fast Marching / MMP 等 |
| :--- | :--- | :--- |
| 核心计算 | 2 次稀疏线性求解 | 迎风 / 波前传播或精确展开 |
| 换源摊销 | 矩阵预分解后回代很快 | 通常需重跑 |
| 精度 | 细网格下数值收敛到真距离；粗网格为光滑近似 | 可精确或半精确 |
| 实现 | Laplace + 梯度/散度，易接入现有几何库 | 专用数据结构较多 |
| 光滑性 | $t$ 可调，距离场更光滑、利于求导 | 精确距离在割迹处不可微 |

适用：蒙皮权、测地 Voronoi、几何处理里大量「到某集合的距离」、需要 $\nabla\phi$ 的应用等。需要**严格最短路径折线**时，仍用精确测地算法。

CGAL 等库已有 Heat Method 封装，便于对照实现。

---

## 7. 和参数化 / 展开的关系

基础曲面展开、切缝、度量设计里经常需要：

- 到边界 / 到特征曲线的距离；  
- 测地极坐标、指数映射的近似；  
- 以距离为高度的标量场做切割或约束。

Heat Method 提供**便宜、可微性较好**的距离场，可与调和映射、ARAP、最优传输等管线并行使用：先用热方法拿 $\phi$，再进入变分能量。不必每次都上精确 MMP。

---

## 8. 一句话收束

Eikonal 说「距离梯度模长为 1」；热扩散在短时给出「正确方向」；单位化后再 Poisson 重建标量——这就是 Crane 等人的 **Heat Method**：把难解的非线性 Eikonal，拆成**热扩散 + 线性 Poisson** 两步，在离散几何里既好实现又好加速。
