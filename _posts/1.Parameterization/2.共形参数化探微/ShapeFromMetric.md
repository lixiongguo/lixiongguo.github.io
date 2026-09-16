---
layout: post
title: "Shape from Metric：从度量还原形状"
date: 2026-09-16
category: Parameterization
categories: ["Parameterization", "Parameterization-ConformalMapping"]
mathjax: true
---

> A. Chern, F. Knöppel, U. Pinkall, P. Schröder. **Shape from Metric**. *ACM Trans. Graph.* 37(4), SIGGRAPH 2018.
> 输入**只有**网格组合与边长（一个内蕴度量），输出 $\mathbb R^3$ 中的近似**等距浸入**。工具链：单位四元数（旋量）表示三角形朝向 $\to$ 四元数平行移动编码拓扑 $\to$ 非线性 Dirac 方程 $\to$ 变分极小化。

## 0. 一句话

曲面参数化研究"$\mathbb R^3$ 曲面 $\to$ 平面"的共形/等距展开，本文做的是**反向**的对偶问题：只给度量（边长），在**指定的正则同伦类**里把它"实现"成 $\mathbb R^3$ 中的形状。这既不是 Shape from Shading 也不是 Shape from X，这里的 metric 就是内蕴度量本身。它与本博客的单值化/Ricci 流（度量变形到常曲率）互补——那里是"改度量求良好坐标"，这里是"度量已定，求形状"。

## 1. 问题：只给度量，求形状

### 1.1 输入与输出

- **输入**：可定向三角网格的**组合结构** $\mathcal T$ + **边长** $\{l_{ij}\}_{(i,j)\in E}$。即只有 $(M,g)$ 的离散版本，没有任何 $\mathbb R^3$ 位置信息，且该度量**未必可嵌入**（可能是抽象度量：整体曲率、拓扑、边长冲突都可能使其在 $\mathbb R^3$ 中无解）。
- **输出**：一个到 $\mathbb R^3$ 的**近似等距浸入** $f:M\to\mathbb R^3$，满足
  $$
  f^*g_{\mathbb R^3}\approx g,
  $$
  允许自交（immersion 而非 embedding），只要求局部不退化——这正是[曲面度量](../7.离散微分几何/3.曲面度量.md)一节里的浸入/嵌入之别。

### 1.2 为什么难：三个层次

**（a）可积性**。等距浸入不是逐点条件，而是要同时满足 **Gauss–Codazzi 方程组**。给定 $I$（度量）后，第二基本型分解为
$$
I\!I = H\,I + I\!I_0,\qquad I\!I_0 \text{ 为关于 } I \text{ 的无迹部分},
$$
Gauss 方程把曲率与 $H$、$I\!I_0$ 的点态模长绑定（忽略教材约定中的常数因子）：
$$
K = H^2 - \mathrm{const}\cdot |I\!I_0|_I^2
\quad\Longrightarrow\quad
|I\!I_0|^2 \propto H^2 - K_g .
$$
所以：给定度量后想指定 $H$，就**必须**让 $H^2\ge K_g$ 处处成立；$I\!I_0$ 的大小被锁死，只剩一个"相位"自由度。全局上还有硬障碍，例如 Hilbert 定理：完备常负曲率曲面不能 $C^2$ 等距嵌入 $\mathbb R^3$。

**（b）非唯一性（Bonnet）**。等温坐标下 $I\!I_0$ 就是 **Hopf 微分** $Q$（一个 $(2,0)$ 型二次微分）。Codazzi 只约束 $Q$ 的相位：

- $H\equiv$ 常数（CMC）时 Codazzi 退化为 $\bar\partial Q=0$，即 $Q$ **全纯**；而 $e^{i\theta}Q$ 对任意实常数 $\theta$ 仍全纯 $\Rightarrow$ **单参数等距形变族**（Bonnet / 相关族）。这就是"悬链面 $\leftrightarrow$ 正螺面可以连续等距弯折"的来源。
- $H$ 非常数时相位由一阶 Codazzi 方程决定，一般只给**离散**解。

结论：**度量 + $H$（或等价地"平均曲率半密度"）才决定形状**（Bonnet 定理版的"曲面基本定理"）。只给度量是欠定问题，解集可能是一族，也可能有镜像/翻转等多个分支。

**（c）解空间的拓扑**。浸入空间按**正则同伦类**分连通分量，而正则同伦类不只有"翻转"这一种：

$$
\#\{\text{Imm}(M,\mathbb R^3)\text{ 的正则同伦类}\}=2^{2p},\qquad p=\text{亏格}.
$$

- 球面 $p=0$：只有 **1** 类——与 Smale 的球面外翻定理一致（所有浸入都正则同伦）；
- 环面 $p=1$：**4** 类；
- 亏格 $p$ 的曲面：$2^{2p}$ 类（本质是 $H^1(M;\mathbb Z_2)=\mathbb Z_2^{2p}$）。

所以朴素做法（"把边长残差 $\sum(|v_i-v_j|^2-l_{ij}^2)^2$ 直接丢进非线性最小二乘"）会在**错误的同伦类**里收敛，或者给出退化、翻转、"看起来完全不像"的解——实现中确实如此（见 §5.3）。

### 1.3 于是目标变成

> 在**指定的正则同伦类**中，找一个度量误差最小的浸入。

"指定同伦类"这件事必须在离散层面可计算、可控制，这就是本文离散理论的核心贡献。

## 2. 连续理论：把浸入写成旋量的 Dirac 方程

### 2.1 为什么是四元数

$\mathbb R^3$ 与四元数虚部同构：$\mathbb R^3\cong\mathrm{Im}\,\mathbb H$，三个虚单位 $i,j,k$ 给出三个方向的 $90^\circ$ 旋转，单位四元数 $q\in S^3$ 通过共轭作用 $\bar q(\cdot)q$ 双重覆盖 $SO(3)$（$q\sim-q$）。于是"曲面的朝向（法向/Gauss 映射）"和"复结构 $J$（切平面上的 $90^\circ$ 旋转）"可以装进**同一个代数**里运算，这正是四元数全纯几何/旋量曲面论的起点（本博客[Möbius 共形变形](../3.几何优化方法/Mobius共形变形.md)中也用四元数表示 3D Möbius 变换）。

### 2.2 spin 丛与 spin pairing：浸入由旋量重建

设 $M$ 为黎曼面，$L\to M$ 为其上的 **spin 丛**（一个四元数线丛），$\psi\in\Gamma(L)$ 为处处非零的**旋量（spinor）**。定义 spin pairing $(\cdot,\cdot)$，则浸入的微分可以由旋量"算出来"：

$$
\boxed{\;df=(\psi,\psi)\ \in\ \Gamma\big(\mathrm{Conf}(TM,\mathbb R^3)\big)\;}
\qquad\Longrightarrow\qquad
|df|^2=|(\psi,\psi)|^2=|\psi|^4 .
$$

即

- $(\psi,\psi)$ 是一个 $\mathbb R^3$ 值的 1-形式，且自动落在**共形 1-形式**中（每个切向量被送到 $\mathbb R^3$，且保持角度）；
- 诱导度量 $=$ 旋量模长的四次方：$|df|^2=|\psi|^4$，共形因子 $e^{2u}=|\psi|^2$；
- 法向由复结构给出：$J\psi=-\psi N$，$N:M\to S^2$ 即 Gauss 映射（对照[高斯曲率与高斯映射](../7.离散微分几何/1.高斯曲率与高斯映射.md)）。

也就是说：**形状 = 旋量模长 + 相位**，度量信息全部编码在 $|\psi|^4$ 里。

### 2.3 非线性 Dirac 方程与平均曲率半密度

上面积分 $df=(\psi,\psi)$ 得到单值浸入，要求 $(\psi,\psi)$ 是**闭** 1-形式。这个可积条件可以等价地写成一个方程：

$$
\boxed{\ \bar\partial\psi+\tfrac12\,H\,J\psi\,(\psi,\psi)=0\ }
\qquad\Longleftrightarrow\qquad
\boxed{\ D\psi=0\ }
$$

其中 $\bar\partial$ 是 spin 丛上的 Dirac 结构（四元数全纯结构），$H$ 是所得浸入（在万有覆盖上带平移周期）关于诱导度量的平均曲率。等价地写成 $D=\bar\partial+U\eta$，其中

$$
U=\tfrac12\,H\,|df|=\tfrac12\,H\,|\psi|^2
$$

就是 **Dirac 势 / 平均曲率半密度（mean curvature half-density）**，$\eta=J\psi(\psi,\cdot)/|\psi|^2$。

按 $\psi,\eta\psi$ 分解可得到最有信息量的一式：

$$
\bar\partial\psi=\alpha\,\psi+(U+VJ)\,\eta\,\psi .
$$

- $U$：平均曲率半密度（"形状"）。$H$ 与 $|df|$ 在共形缩放下的变换互相抵消，所以 $U$ 是**与参数化选取无关**的量——这就是"半密度"的含义；
- $V=0$：恰是形状算子 $dN$ 关于共形度规自伴的条件；
- $\alpha=0$：旋量的全纯性条件。特别地 $H\equiv 0$（极小曲面）时非线性 Dirac 方程退化为 $\bar\partial\psi=0$，即 $\psi$ **全纯**——这正是 Weierstrass 表示的旋量版（对照[极小曲面与 Circle Patterns](相关问题-极小曲面.md)）。

因此在旋量语言里：**"指定平均曲率"就是指定复半密度 $U+VJ$ 中的实部** $U=\tfrac12H|df|$；而 $\psi\mapsto\lambda\psi$（$\lambda\in\mathbb C^\times$）带来的实缩放与旋转，正是 Bonnet/相关族那部分自由度的来源。

### 2.4 等距版本

给定度量 $g$，等距浸入等价于在**硬约束**

$$
|\psi|^4=g
$$

下求解/极小化（此时 $df=(\psi,\psi)$ 自动给出等距）。这带来了本文算法的关键结构转变：

| 视角 | 变量 | 度量 $g$ 的角色 | 难点 |
| :--- | :--- | :--- | :--- |
| 直接法 | 顶点位置 $v_i$ | 残差 $\sum(|v_i-v_j|-l_{ij})^2$ | 非凸、易落错同伦类、退化 |
| 本文（旋量法） | 旋量场 $\psi$（每面单位四元数） | **约束** $|\psi|^4=g$（四次！） | 流形上的优化（$\int|\psi|^4=1$ 归一化） |

"非线性 Dirichlet 能量"的**非线性**就在这里：度量对旋量是四次型（$|\psi|^4$），约束流形是 $L^4$ 球面，而不是常见的线性最小二乘。

## 3. 后续工作：旋量泛函族与约束 Willmore

同组作者在后续工作（*Finding Conformal and Isometric Immersions of Surfaces*, arXiv:1901.09432；Springer Proc. Math. Stat. 349, 2021）把这个框架写成一族变分泛函，对非负耦合常数 $\epsilon=(\epsilon_1,\epsilon_2,\epsilon_3)$：

$$
E_\epsilon(\psi)=
\epsilon_1\!\!\int_M\frac{\langle *\bar\partial\psi\wedge\bar\partial\psi\rangle}{|\psi|^2}
+(\epsilon_2-\epsilon_1)\!\!\int_M\frac{\langle *\bar\partial\psi\wedge\psi(\psi,\psi)\rangle^{2}}{|\psi|^{4}}
+(\epsilon_3-\epsilon_1)\!\!\int_M\frac{\langle *\bar\partial\psi\wedge J\psi(\psi,\psi)\rangle^{2}}{|\psi|^{4}}
$$

（转录自原文 §2；幂次与半密度约定以原文为准，这里只需抓住"三项分别对应 Dirac 残差、$U$ 项、$V$ 项"。）

性质与几何含义：

- **共形不变**，且对 $\psi$ 的常数缩放不变 $\Rightarrow$ 可归一化到 $\int_M|\psi|^4=1$（再次出现 $L^4$ 球面）；
- 前两项在 $L^2$ 意义下度量"非线性 Dirac 方程 $\bar\partial\psi=\alpha\psi+(U+VJ)\eta\psi$ 失效的程度"；
- 最后一项 **$=\int_M H^2|\psi|^4=\int_M H^2\,dA$，正是 Willmore 泛函**；$\epsilon_3>0$ 相当于把 Willmore 当正则项，$\epsilon_3\to0$ 的极限预期给出**约束 Willmore 曲面**（固定共形类 + 正则同伦类下的 Willmore 极小元）；
- 等距版本：约束 $|\psi|^4=g$，当 $\epsilon_3=0,\ \epsilon_1,\epsilon_2>0$ 时泛函最小值 $0$，且由满足 $df=(\psi,\psi)$ 的**等距浸入**达到；
- 闭曲面要加周期项 $\sum_\gamma\big|\int_\gamma(\psi,\psi)\big|^2$（$\gamma$ 取 $H_1(M,\mathbb Z)$ 的一组基），把 1-形式 $(\psi,\psi)$ 的"恰当性"惩罚掉，否则只能得到万有覆盖上带平移周期的浸入。

**同伦类怎么被旋量"记住"**：映射 $f\mapsto L_f$ 给出
$$
\{\text{正则同伦类}\}\ \longleftrightarrow\ \{\text{spin 丛同构类}\},
$$
而 spin 丛的平方根 $E$（$E^2\cong K$）在 $\mathrm{Pic}$ 的半格点上取值，共 $2^{2p}$ 个——与 §1.2(c) 的 $2^{2p}$ 完全对上。这就是"要把拓扑编码进旋量"的数学原因。

## 4. 论文的离散理论

论文的定位是：**为 $\mathbb R^3$ 中的曲面浸入建立一个离散理论**，该理论在**细分与微小扰动下**精确刻画离散浸入（consistency + stability），并且**正确地复现浸入空间的拓扑**（即正则同伦类 = 连通分量）。三根支柱：

### 4.1 边长定形，朝向定形变

三角形形状由三边完全决定（余弦定理），所以对一个"只给度量"的网格，**每面在平面内的形状已经固定**，未知量只剩：

1. 每个三角形被放到 $\mathbb R^3$ 的什么**朝向**；
2. 顶点被放到哪里（即整体怎么"折"起来）。

### 4.2 每面一个单位四元数 + 四元数平行移动

- 每个三角形 $f$ 附带一个**单位四元数** $q_f\in S^3$，代表该面的朝向（它的旋转/旋量相位）；
- 相邻面之间的传递由**四元数平行移动**给出（沿对偶图传播，含二面角旋转）。
- 这与[离散联络与协变导数](../4.全局参数化与四边形网格化/离散联络与协变导数.md)中的"沿路径的平行移动/holonomy"是同一套语言：绕顶点或绕闭环传播一圈的**holonomy**（"和乐"）就是曲率/绕数的离散体现。

### 4.3 拓扑：holonomy 编码正则同伦类

关键一句（论文摘要原意）：用单位四元数表示三角形朝向，并**在其平行移动中编码浸入的拓扑**。离散 Gauss 映射的绕数（缠绕数）就藏在 holonomy 里：

- 有了它，算法不会在"翻转/自交类型"之间乱跳——**同伦类是算法的输入/不变量，而不是碰运气的结果**；
- 这也解释了为什么该离散理论在细分与扰动下稳定：它复现的是浸入空间的**拓扑**（连通分量），而不只是逐点近似。

### 4.4 与 Spin Transformations 的关系

Crane–Pinkall–Schröder 的 *Spin Transformations of Discrete Surfaces*（SIGGRAPH 2011）给出离散**四元数 Dirac 算子**与共形变形的可积条件；本文沿用同一套旋量语言，但把目标从"共形形变（给定曲率目标）"换成"给定度量，求等距实现"，因此不能只解一个线性系统，必须转为**变分 + 非线性约束**。

## 5. 非线性 Dirichlet 能量与求解

论文的方法学（摘要原话）：*Minimizing a non-linear Dirichlet energy optimally finds extrinsic geometry for the given intrinsic geometry and ensures low metric approximation error.*

即：内蕴几何（边长）已给，用能量极小化去"最优地挑"外蕴几何（在 $\mathbb R^3$ 中的摆放与弯曲方式）。

### 5.1 变量与能量骨架

- 变量：每面的旋量（单位四元数，$\|\psi\|=1$）+ 顶点位置（由旋量积分/重建得到）；
- 能量：度量约束 $|\psi|^4=g$ 的违反量 + Willmore/弯曲型正则（对应 §3 泛函族中 $\epsilon_1,\epsilon_2,\epsilon_3$ 的配比），以及保证闭形式恰当的周期项；
- 归一化：$\psi$ 的常数缩放是零方向，必须钉住（如 $\int|\psi|^4=1$），否则能量被整体缩放吃掉（"越缩越小/越大"的退化）。

### 5.2 迭代结构（实现视角）

论文附带 Houdini 实现与视频；第三方 MATLAB 复现（`liuzhenye1997/shape_from_metric`，含 `BunnyFromMetric.m` 等）把该算法落实为如下交替迭代（**具体公式以原文为准**，此处只取骨架）：

```
初始化：从边长构造每面旋量 ψ（单位四元数）
重复：
  1) 由邻面旋量与平行移动（含二面角）构造残差 / 局部量；
  2) 局部步：把局部量投影回约束流形（单位球面投影，即极分解式归一化）；
  3) 全局步：半隐式梯度流 (M + dt·L)ψ⁺ = M(ψ − dt·g)，稀疏 LDLᵀ，
             符号分解只做一次，后续仅数值回代；
  4) 泊松重建：由 ψ 积分出顶点位置（解一次泊松方程）；
  5) 由当前浸入回拉更新 ψ（保持等距一致性）；
  6) 误差评估：边长相对误差（L2 / 最大相对误差）
直到收敛
```

几个要点与坑：

- **局部-全局（local–global）结构**：局部步只管"回约束流形"（近似闭式），全局步只是一个稀疏线性求解——这是它能处理几万面网格的原因；
- **步长与权重调度**：步长需随迭代衰减；弯曲（Willmore 型）项在后期要降权甚至关闭，否则高频振荡不收敛；
- **泊松重建 vs 直接优化位置**：由旋量积分位置（泊松）比直接对 3 自由度位置做非线性优化稳定得多——旋量承担了全部非线性，位置只是线性后处理；
- **对称/旋转歧义**：解只确定到 $\mathbb R^3$ 的刚体运动（以及可能的镜像），评估误差前需先对齐（实现里的 `fix_rotation`）；
- **重建的是"浸入"**：结果允许自交（例如把兔子按度量重新"吹"起来时会出现穿插），这是问题的定义使然。

### 5.3 非唯一性与初始化（很现实的一课）

度量给全了，解仍可能不唯一（镜像、翻转、不同分支）。第三方复现给出的实验数据非常说明问题：

| 初始化策略 | 得到"正确解"的比例 |
| :--- | :--- |
| 只知边长，参考对角线取平均值，八面体任意 | ~33% |
| 参考对角线取真实值，八面体任意 | ~40% |
| 参考对角线取平均值，且**初始解为凸** | ~99.7% |
| 参考对角线取真实值，且**初始解为凸** | ~100% |

也就是说：**正确率几乎完全由初始化（尤其是初始解是否凸）决定**，而不是由能量/求解器决定。这与本文理论（正则同伦类 + 非唯一性）完全吻合，也是"只给度量"的问题在实践中最需要留意的部分。

## 6. 应用与可加约束

论文演示的方向：

- **数学可视化**：把抽象/非欧度量实现在 $\mathbb R^3$ 里（例如均匀边长的环面——4 个正则同伦类的不同"打结"方式、双曲三角剖分曲面等）；
- **艺术导向的等距形变**：给定目标度量做等距（保长度）形变，模拟**高膜刚度薄膜材料**（membrane stiffness）的行为——薄的片材想实现某个内部度量，于是自己在空间里弯折、起皱；
- **可加入外部数据**：指定平均曲率（对应指定半密度）、边界条件（带边界网格）、对称性约束；
- **工程上**：论文提供 Houdini 代码资源 + 视频，适合作为交互式设计工具。

## 7. 与其他方法对比

| 方法 | 思路 | 局限 |
| :--- | :--- | :--- |
| **直接边长残差优化** | $\min\sum(|v_i-v_j|-l_{ij})^2$ | 非凸、落错同伦类、退化、需好初值 |
| **Nash–Kuiper $C^1$ 嵌入** | 存在性定理 | 只保证 $C^1$，无实用算法 |
| **球面/平面特例解析法** | 逐三角形"球线相交"求解 | 只在特殊约束下有闭式，数值退化需处理 |
| **约束 Willmore 流 / 共形流** | 固定共形类下极小 Willmore | 不直接控制度量（是"近共形"而非"近等距"） |
| **本文** | 旋量表示 + 同伦类编码 + 非线性 Dirichlet 能量 | 非线性非凸、依赖初始化、只求近似等距 |

## 8. 与博客其他章节的关系

- [曲面度量](../7.离散微分几何/3.曲面度量.md)：immersion/embedding、regular homotopy（Smale 球面外翻）、Bonnet 定理与 Gauss–Codazzi 的完整推导——本文的连续前提都在这里；
- [共形等价理论介绍](../7.离散微分几何/4.共形等价理论介绍.md)：共形结构、等温坐标、共形因子——旋量模长 $|\psi|^2$ 就是共形因子；
- [高斯曲率与高斯映射](../7.离散微分几何/1.高斯曲率与高斯映射.md)：法向 $N$（本文里 $J\psi=-\psi N$）与角盈；
- [离散联络与协变导数](../4.全局参数化与四边形网格化/离散联络与协变导数.md)：平行移动、holonomy、离散联络——四元数平行移动的离散几何原型；
- [Möbius 共形变形](../3.几何优化方法/Mobius共形变形.md)：四元数表示 3D 相似/Möbius 变换，以及 spin transformations 的定位对照；
- [Ricci 流与参数化](2016-11-05-Ricci流与参数化.md)、[BFF 与 VSC](2023-01-01-BFF与VSC.md)：度量被**演化**（求常曲率/求边界） vs 度量被**给定**（求形状）；
- [Möbius Registration](Mobius%20Registration.md)：球面参数化 + 中心化 + 对齐，同样是"共形自由度未被钉死"的典型问题；
- [极小曲面与 Circle Patterns](相关问题-极小曲面.md)：Willmore/极小曲面与离散可积系统——本文 $\epsilon_3$ 项把二者接起来；
- [线性方程组 $Ax=b$](../6.附录-数值计算与最优化/2016-06-11-线性方程组Ax=b.md)：全局步的半隐式格式与稀疏 LDLᵀ 复用。

## 9. 参考文献

1. A. Chern, F. Knöppel, U. Pinkall, P. Schröder. **Shape from Metric**. *ACM Trans. Graph.* 37(4), 63:1–63:17, SIGGRAPH 2018. [DOI: 10.1145/3197517.3201276](https://doi.org/10.1145/3197517.3201276)｜[项目主页（含 PDF / 视频 / Houdini 代码）](https://cseweb.ucsd.edu/~alchern/projects/ShapeFromMetric/)
2. A. Chern, F. Knöppel, F. Pedit, U. Pinkall, P. Schröder. **Finding Conformal and Isometric Immersions of Surfaces**. arXiv:1901.09432；*Minimal Surfaces: Integrable Systems and Visualisation*, Springer Proc. Math. Stat. 349, 13–33, 2021. [DOI: 10.1007/978-3-030-68541-6_2](https://doi.org/10.1007/978-3-030-68541-6_2)
3. K. Crane, U. Pinkall, P. Schröder. **Spin Transformations of Discrete Surfaces**. *ACM Trans. Graph.* 30(4), SIGGRAPH 2011. [PDF](https://multires.caltech.edu/pubs/SpinXForm.pdf)
4. G. Kamberov, P. Norman, F. Pedit, U. Pinkall. **Quaternions, Spinors, and Surfaces**. *Contemporary Mathematics* 299, AMS, 2002. [AMS](https://bookstore.ams.org/conm-299/)
5. G. Kamberov, F. Pedit, U. Pinkall. **Bonnet pairs and isothermic surfaces**. *Duke Math. J.* 92, 1998.
6. S. Smale. **A classification of immersions of the two-sphere**. *Trans. AMS* 90, 1958（正则同伦类理论起点）；M. Hirsch / A. Phillips 的一般化。
7. B. Springborn, P. Schröder, U. Pinkall. **Conformal equivalence of triangle meshes**（离散共形结构/顶点缩放）. *ACM Trans. Graph.* 27(3), SIGGRAPH 2008.
8. E. Kuwert, R. Schätzle. **The Willmore functional**（$\epsilon_3\to0$ 的约束 Willmore 背景）.
9. 第三方复现：`liuzhenye1997/shape_from_metric`（MATLAB，含 `BunnyFromMetric.m`、`isometry_*` 系列，可对照论文附录取向）
