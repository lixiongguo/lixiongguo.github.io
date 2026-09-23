---
layout: post
title: "FastHGP — 子空间方法加速的局部单射调和映射"
categories: ["Parameterization", "Parameterization-GeometricOptimization"]
mathjax: true
---

> **论文**：Eden Fedida Hefetz, Edward Chien, Ofir Weber. *A Subspace Method for Fast Locally Injective Harmonic Mapping*. Computer Graphics Forum (Eurographics), 38(2), 2019.
> **前置**：Harmonic Global Parametrization [BCW17]（见《全局调和参数化 — q-CCM 与 HGP》）
> **代码**：https://github.com/eden-fed/HGP

## 1. 动机与定位

无质量约束的线性方法（LSCM、CETM 等）代价只有一次稀疏线性求解，但没有单射保证、鲁棒性差；带保证的非凸方法（BDHM、[CLW16]、[SPSH*17]）鲁棒，但内部要解几十甚至上百个线性系统。

FastHGP 的目标是同时拿到两者：**鲁棒性接近非凸方法，代价接近线性方法**。

关键思路是把搜索限制在 **HGP 调和解空间** $\mathcal{N}(A_{\text{hgp}})$ 内（这是一个比共形映射更大的空间），但**不松弛调和约束**——和在 HGP 中使用 MOSEK 求解 SOCP（把调和条件写成二次误差项做软约束）不同，FastHGP 把调和方程作为**硬约束**精确满足，只在低维子空间里自由搜索。

$$
\text{总代价} \approx 1\text{–}2 \text{ 次线性求解}
$$

支撑这一切的是两个观察：

**Observation 1（单射性局部化）**：对任何调和解 $z$，判断其是否局部单射**只需考察边界与锥点邻域的三角形** [BCW17, Thm 6.1]。内部三角形的单射性"自动被管住"。

**Observation 2（扭曲取极值于边界）**：光滑局部单射调和映射的共形扭曲上界出现在圆盘域的边界上 [CW15]；该结论已推广到多连通域 [CW17]，并可推广到锥点（视为无穷小 puncturing）。

两者合并 ⇒ **单射性约束和扭曲能量都只需施加在 $T_{cb}$（含锥点或边界顶点的三角形）上**，变量数与目标项数同时与网格密度解耦。

---

## 2. HGP 线性系统回顾

曲面 $S=(V,E,T)$ 沿 seam graph $G_s=(V_s,E_s)$ 切开得到圆盘 $S_c$，逐片线性映射 $f:S_c\to\mathbb{R}^2$（用 $\mathbb{R}^2\cong\mathbb{C}$ 记 $z_i:=f(v_i)$）。无缝条件要求 seam 边两侧的像相差一个 $\pi/2$ 的整数倍旋转。记锥点集合 $C\subset V_s$，$S_c$ 的内部顶点 $\mathring V := V\setminus(V_s\cup\partial V)$。

$$
z_j^a-z_i^a=e^{\,\mathrm{i}\pi r_{ij}/2}\,(z_j^b-z_i^b),\qquad e_{ij}\in G_s
\tag{1}
$$

$$
\sum_{v_j\in N(v_i)} w_{ij}(z_i-z_j)=0,\qquad v_i\in\mathring V
\tag{2}
$$

$$
\sum_{v_j\in N^*(v_i^0)} w_{ij}(z_i^0-z_j)+\sum_{v_j\in N^*(v_i^1)} w_{ij}e^{\mathrm{i}\pi r/2}(z_i^1-z_j)=0,\qquad v_i\in V_s\setminus(C\cup\partial V)
\tag{3}
$$

- (1) 是 seam 边的**旋转约束**，$r_{ij}\in\{0,1,2,3\}$ 由 [MZ12] 附录 B 的线性系统定出；
- (2) 是内部顶点的**标准调和约束**，$w_{ij}$ 为 cotangent 权；
- (3) 是 seam 顶点的**旋转调和约束**（此处只写了 $G_s$ 中度数 2 的顶点；度数 $d$ 有 $d$ 个副本，方程繁琐），**实现时无需构造它**（见 §4）。

权重取 cotangent 而非 mean value coordinates，原因是收敛性与对称性；正权是局部单射的**充分**条件（可用 intrinsic Delaunay 重剖分保证），但实验中发现负 cot 权很少影响结果，偶尔出现的孤立翻转可用"把单顶点移到其 1-ring 核内"的启发式修复。

---

## 3. 系统维数与插值条件

(1)–(3) 行数少于列数，构成齐次系统 $A_{\text{hgp}}z=0$。记 $A_{\text{aug}}=\begin{pmatrix}A_{\text{hgp}}\\ A_{\text{int}}\end{pmatrix}$，其中 $A_{\text{int}}$ 是"补全"方阵的插值条件。

### 3.1 球面情形

**Lemma 3**：$S\cong S^2$ 时 seam graph $G_s$ 是**树**，$\chi(G_s)=|V_s|-|E_s|=1$。

- 列维数：$|\mathring V|+2|E_s|$（内部顶点各 1 个复变量，每个 seam 顶点 $\deg(v)$ 个副本）；
- 行维数：$|E_s|+|\mathring V|+(|V_s|-|C|)$；
- 差值：$|E_s|-|V_s|+|C|=|C|-1$。

**插值条件**：先取 $G_s$ 中度数为 1 的锥点（树必有叶子；假设无"非锥叶子"以免引入多余变量），对**其余 $|C|-1$ 个锥点**各固定其（某个副本的）位置。$A_{\text{int}}$ 的每行只有一个 1，其余为零。

> 求解 $A_{\text{aug}}z=\binom{0}{c_{\text{int}}}$ 即得 $\mathcal{N}(A_{\text{hgp}})$ 中的一个元素；$c_{\text{int}}$ 线性无关的取法给出线性无关的解——锥点位置是被"调和插值"出来的。

### 3.2 圆盘 / 多连通圆盘情形

**Lemma 4**：亏格 0、$n>0$ 个边界，$G_s$ 有 $m$ 个连通分量时为**森林**，$\chi(G_s)=m$。
**Lemma 5**：$|\partial V\cap V_s|=n+(m-1)$（证明见附录 A：把 $G_s\cup\partial S$ 当 1-skeleton 做 cell decomposition，逐个分量数交点）。

- 列维数：$|\mathring V|+|\partial V|+2|E_s|$（$\partial V\cap V_s$ 上顶点有 $\deg(v)+1$ 个变量）；
- 行维数：$|E_s|+|\mathring V|+(|V_s|-|C|-|\partial V\cap V_s|)$；
- 差值：$|\partial V|+|C|+n-1$。取 $n=0$ 与球面情形吻合。

插值条件：每个 $\partial V$ 顶点、每个锥点各固定一个（副本的）位置；若 $n>1$ 还需再指定 $n-1$ 个 $\partial V\cap V_s$ 顶点的**第二个副本**位置，且使剩余 $m$ 个 $\partial V\cap V_s$ 元素在 $G_s$ 的 $m$ 个分量间均匀分布。

---

## 4. KKT 公式化：不显式写旋转调和

直接编码 (3) 很繁琐。论文转成等价的**线性约束二次极小化**：

$$
\min_{z}\ \|Dz\|^2
\quad\text{s.t.}\quad
A_{\text{lin}}z=c_{\text{lin}},\qquad
A_{\text{lin}}=\begin{pmatrix}A_1\\ A_{\text{int}}\end{pmatrix},\
c_{\text{lin}}=\begin{pmatrix}0\\ c_{\text{int}}\end{pmatrix}
\tag{4}
$$

目标函数是各分量坐标的 Dirichlet 能量之和，其 Hessian $2D^tD$ 就是**一对标准 cotangent Laplacian**（对 $\mathrm{Re}(z_i)$、$\mathrm{Im}(z_i)$ 各一个），$D$ 是面积加权的（平方根）梯度算子。由于目标正半定、约束线性，**KKT 条件既必要又充分**：

$$
\underbrace{\begin{pmatrix}2D^tD & A_{\text{lin}}^t\\ A_{\text{lin}} & 0\end{pmatrix}}_{K}
\begin{pmatrix}z\\ \lambda\end{pmatrix}
=\begin{pmatrix}0\\ c_{\text{lin}}\end{pmatrix}
\tag{5}
$$

**Theorem 6**：$K$ 可逆，(4) 有唯一解。
*证明骨架*：设 $K\binom{z}{\lambda}=0$。由下块 $z\in\mathcal{N}(A_{\text{lin}})$；若 $z=0$ 则 $\lambda\in\mathcal{N}(A_{\text{lin}}^t)$ 非零，与 $A_{\text{lin}}$ 满秩（Prop 11，附录 B：利用各行稀疏性沿 $\partial S$ 与 $G_s$ 做链式消元）矛盾；若 $z\neq0$，左乘 $z^t$ 使第二项消失，得 $\|Dz\|^2=0$，即 $z\in\mathcal{N}(D)\cap\mathcal{N}(A_{\text{lin}})$——但 $\mathcal{N}(D)$ 只有常向量，而插值条件已排除非零常向量，矛盾。$\square$

**Proposition 7**：KKT 系统的解 $(z,\lambda)$ 中，$z$ 满足**增广 HGP 系统** $A_{\text{aug}}z=\binom{0}{c_{\text{int}}}$。
*证明骨架*：$K$ 的对应 $\mathring V$ 的行直接给出 (2)；对 $V_s\setminus(C\cup\partial V)$ 的行含 Lagrange 乘子，用 (1) 的 $2k$ 行线性组合消掉乘子后恰好得到 (3)。论文用 Figure 3/4 的度数 2 例子显式演示了 $x_i^0$ 与 $y_i^1$、$y_i^0$ 与 $x_i^1$ 配对消元。

**Theorem 8**：$A_{\text{aug}}$ 可逆，$A_{\text{hgp}}$ 满秩，

$$
\dim\mathcal{N}(A_{\text{hgp}})=2\bigl(|\partial V|+|C|+n-1\bigr)\quad\text{（实维）}
$$

且取 $c_{\text{int}}$ 为标准基即得 $\mathcal{N}(A_{\text{hgp}})$ 的一组基（因为此时解就是 $K^{-1}$ 的一列）。

> **为什么这个公式化很实用**：$K$ 的左上块 $2D^tD$ 只需遍历 $S_c$ 的三角形、把 3 个 cotangent 权累加进去即可（和构造标准 Laplacian 完全一样），(2)(3) 都**不需要**显式构造。

### KKT 在算法中的三重角色

KKT 系统 (5) 不是只在证明里出现的工具，而是整个算法的**唯一线性代数内核**：它既承担全部理论保证，又是**子空间构造**与**最终回代**这两处实际计算的入口。与"直接解 $A_{\text{aug}}z=\binom{0}{c_{\text{int}}}$"相比，优势正在于：$A_{\text{lin}}$ 只含最简单的旋转约束 (1) 与插值条件，$2D^tD$ 可像标准 Laplacian 一样组装，**繁琐的 (3) 被彻底绕开**。

**① 子空间构造（核心计算）**

Theorem 8 的最后一句直接给出构造方法：$c_{\text{int}}$ 取标准基单元时，解就是 $K^{-1}$ 的一列。于是

| 步骤 | 操作 | 依托的性质 |
| :--- | :--- | :--- |
| 1 | 令 $c_{\text{int}}$ 跑遍 $\mathbb{R}^{2(\vert\partial V\vert+\vert C\vert+n-1)}$ 的标准基 | $c_{\text{int}}\leftrightarrow z$ 是**线性双射**（$K$ 可逆，Theorem 6） |
| 2 | 只需保留 $z$ 在 $V_{cb}$ 上的分量 | Observation 1（单射性只看 $T_{cb}$） |
| 3 | 选择性求逆只取 $K^{-1}$ 左上块中 $V_{cb}$ 对应的行 | 每列求解一次，右端为单位向量，可批量并行提取 |
| 4 | 拼成约化调和基 $H$ | $H$ 的列张成 $\mathcal{N}(A_{\text{hgp}})$ 在 $V_{cb}$ 上的图像 |

**② 最终回代（收尾计算）**

ATP（§6）与 Projected Newton（§7）全程在系数 $c$ / 导数 $(f_z,f_{\bar z})$ 上工作，**不做任何 KKT 求解**。只有在拿到最优 $c_{\text{int}}^*$ 之后，才用**同一个分解**再解一次 (5) 得到全网格映射 $z^*$。因此 $\mathcal{N}(A_{\text{hgp}})$ 的完整基自始至终没有被构造——这就是"总代价 ≈ 1–2 次线性求解"的具体含义。

**③ 理论保证（附带收益）**

- **Theorem 6** 的证明全程在 $K$ 上做，顺带用到并证明 $A_{\text{lin}}$ 满秩（Prop 11）；
- **Proposition 7** 说明 (3) 可由 (1) 的行消去 Lagrange 乘子得到，即 (3) 落在 $A_{\text{aug}}$ 的行空间内；
- 于是 $K$ 可逆 $\Rightarrow A_{\text{aug}}$ 可逆 $\Rightarrow A_{\text{hgp}}$ 满秩 $\Rightarrow \dim\mathcal{N}(A_{\text{hgp}})=2(|\partial V|+|C|+n-1)$。

**$\lambda$ 到底做了什么？**

$\lambda$ 是 seam 两侧副本之间的"旋转耦合乘子"，算法本身**从不使用它的数值**。对第一块行 $2D^tDz+A_{\text{lin}}^t\lambda=0$ 按顶点类型分类即可看清：

| 顶点类型 | 是否出现在 $A_{\text{lin}}$ | 消 $\lambda$ 后的方程 |
| :--- | :--- | :--- |
| 内部顶点 $v\in\mathring V$ | 否（$A_1$ 只管 seam 端点，$A_{\text{int}}$ 只管锥点/边界） | 退化为纯调和 (2) |
| seam 非锥顶点 $V_s\setminus(C\cup\partial V)$ | 是（作为 seam 边端点） | 由 $x_i^0$ 配 $y_i^1$、$y_i^0$ 配 $x_i^1$ 相加消掉 $\lambda$，得旋转调和 (3)（度数 $k$ 需 $2k$ 行组合） |
| 锥点 / 边界顶点 | 是（被 $A_{\text{int}}$ 固定位置） | 位置被直接钉住，即"调和插值" |

> **一句话**：$K$ 把"调和"（目标函数最优）与"旋转 + 插值"（约束）缝进一个可逆矩阵；消掉 $\lambda$ 就恢复 (3)，而算法只需组装 $K$、分解一次、按需取 $K^{-1}$ 的少量元素。

---

## 5. 约化子空间构造

### 5.1 选择性求逆（selected inversion）

由 Theorem 9（[BCW17, Thm 6.1]，本文重述）只需跟踪**锥点与边界三角形** $T_{cb}$ 的顶点 $V_{cb}$ 的行为。因此：

1. 令 $c_{\text{int}}$ 跑标准基，用**选择性求逆** [KLS13, VCKS17]（PARDISO 实现）只算出 $K^{-1}$ 中 $V_{cb}$ 对应的**行**（而非完整 $K^{-1}$，也不是完整零空间基）；
2. 得到**约化调和基**

$$
H\in\mathbb{C}^{|V_{cb}|\times(|\partial V|+|C|+n-1)}
$$

其列表征 $\mathcal{N}(A_{\text{hgp}})$ 中限制在 $V_{cb}$ 上的图像。

论文称这是**选择性求逆在几何处理中的首次应用**。只做一次 LU 分解的代价，但比"LU + 多次回代取完整列再丢弃"快一个数量级；直接算零空间基（稀疏 LU、QR/SVD 正交基、[J*18] 的 LUQ 算法）实测都慢得多。

> 注意：$\mathcal{N}(A_{\text{hgp}})$ 的**完整基从未被显式构造**。优化结束后，用同一个分解求解 (5) 得到最终全网格映射 $z^*$。

### 5.2 边界虚拟顶点（virtual vertices）

对稠密边界的模型，$|\partial V|$ 本身可能很大（单位圆盘上 $O(|V|^{1/2})$），会让维数攀升。于是沿 $\partial S$ 每 $k$ 个顶点取一个**虚拟顶点**（$k$ 由用户指定），中间顶点约束为相邻两个虚拟顶点的弧长凸组合：

$$
v=(1-t)v_a+tv_b,\qquad t=\frac{\operatorname{arc}(v_a,v)}{\operatorname{arc}(v_a,v_b)}
$$

这给出 $\mathcal{N}(A_{\text{hgp}})$ 的一个更小子空间。仅在 $|\partial V|>1000$ 时启用（见 Table 2）；若网格不是 3-连通（例如存在 "ear" 三角形），虚拟顶点的选取需更小心（附录 E）。与 [LFJG17] 的 seam straightening 思路相近。

---

## 6. ATP：在低维子空间中找可行局部单射映射

子空间构造完成后，需要在系数 $c_{\text{int}}$ 上找**局部单射**的初值。用的是 [HCW17] 的 **Alternating Tangential Projections（ATP）**：在"线性子空间"与"凸子集"之间交替投影，且全局投影方向**垂直于上一次局部投影结果**（除第一步），收敛更快，交集非空时保证收敛到可行点。

### 6.1 两层空间

| 层次 | 空间 | 含义 |
| :--- | :--- | :--- |
| **全局** | $\operatorname{Im}\tilde J$ | 真正来自 HGP 调和解的 Jacobian 分量集合 |
| **局部** | $B=\prod_i B_i$，$B_i\subset\mathbb{C}^2$ | 每个三角形上由 frame 凸化的"可行导数"集合 |

矩阵与复合：

$$
\tilde J := J\circ H,\qquad
\tilde J:\mathbb{R}^{2(|\partial V|+|C|+n-1)}\to\mathbb{R}^{4|T_{cb}|}
$$

其中 $J$ 计算 $T_{cb}$ 上的 Jacobian 并分解为**相似/反相似部分** $f_z^i,f_{\bar z}^i$（Wirtinger 导数，基本就是 (4) 中限制在 $V_{cb}$ 的 $D$ 加上换基）。

**Lemma 10**：$\mathcal{N}(\tilde J)$ 维数为 2，由常值复向量构成（把插值约束指定的顶点全部共位，Jacobian 消失；证明见附录 C，用到 (1)(2) 诱导的 4-fold branched cover 上的调和 1-form 论证）。为消掉这个零空间，追加一行全 1，记作 $\tilde J_1$。

### 6.2 局部凸空间 $B_i$

用 frame $\zeta_i$（$|\zeta_i|=1$，来自 [BZK09] 的 frame field，与 HGP 一致——这样能"鼓励"正确的锥角与转角）定义：

$$
\mathrm{Re}\!\left(\frac{f_z^i}{\zeta_i}\right)-|f_{\bar z}^i|\ \ge\ \sigma^2
\tag{7}
$$

$$
\mathrm{Re}\!\left(\frac{f_z^i}{\zeta_i}\right)\ \ge\ \frac{1}{k}\,|f_{\bar z}^i|
\tag{8}
$$

$\sigma^2$ 是很小的正常数（防退化），$k$ 略小于 1。两式分别来自**小伸缩量（little dilatation）**与 Jacobian 较小奇异值的表达（[WMZ12]）：只要把 $|f_z|$ 换成 $f_z$ 在 frame 方向的分量（小于 $|f_z|$），就同时得到单射保证与"粗略对齐 frame"。投影时只改变 $\mathrm{Re}(f_z^i/\zeta_i)$ 与 $|f_{\bar z}^i|$，保持 $\mathrm{Im}(f_z^i/\zeta_i)$ 与 $\arg f_{\bar z}^i$ 不变；$B$ 上的投影即各 $B_i$ 上逐分量投影。$(x,y)$ 平面上的形状：两条直线 + 绿色可行区（论文 Figure 5 画在 $(\mathrm{Re}(f_z/\zeta),|f_{\bar z}|)$ 平面内）。

### 6.3 全局投影

**首次全局投影**（不做法向超平面限制）：求面积加权最小二乘 $\min_c\|W^{1/2}(\tilde Jc-p)\|^2$，正规方程为 $\tilde J^tW\tilde Jc=\tilde J^tWp$，但 $\tilde J^tW\tilde J$ 奇异（2 维解空间）。改用 $\tilde J_1$：

$$
c=(\tilde J_1^tW_1\tilde J_1)^{-1}\tilde J_1^tW_1\,p
\tag{9}
$$

其中 $W_1$ 的最后两个对角元取面积均值作权重，最后只取 $\tilde J_1c$ 的前面部分。

**后续切向全局投影**：把结果限制在超平面 $\mathcal{H}_l:=\{q:(a_l-b_l)^t(b_l-q)=0\}$（$a_l,b_l$ 分别是最近一次全局/局部投影结果）：

$$
c_{l+1}=c_l-\frac{n_l^tWn_l\ \bigl(\begin{smallmatrix}n_l\\0\end{smallmatrix}\bigr)^tW_1\tilde J_1\tilde M^{-1}\tilde J_1^tW_1}{\bigl(\begin{smallmatrix}n_l\\0\end{smallmatrix}\bigr)^t\tilde M^{-1}\tilde J_1^tW_1}
\tag{10}
$$

$\tilde M:=\tilde J_1^tW_1\tilde J_1$，$n_l:=a_l-b_l$。只需一次线性求解（$\tilde M^{-1}\tilde J_1^tW_1$ 可预计算）。

**初始化**：$f_z^i$ 由 frame field 给出，$f_{\bar z}^i=0$；先做一次 (9)，随后在局部投影与 (10) 间交替。**参数**：$k=0.9$，$\sigma^2=0.01$，终止判据 $\|W^{1/2}n_l\|<10^{-4}$（Table 1 显示迭代次数通常个位数，最多 24）。

### 6.4 无锥 + trivial holonomy：一次线性求解的替代

对**无锥点**的圆盘/多连通圆盘（trivial holonomy），不必用 ATP：直接用 [GGT06] 的经典结果——把一条边界放到凸集边界上，其余边界顶点要求落在其邻居的凸包内（用现有 cotangent 权），得到一个关于 $V_{cb}$ 变量的小型**稠密线性系统**（有虚拟顶点时更小）。结果**保证是子空间内的局部单射映射**。因此这一情形下算法是**理论上完全鲁棒**的（实验 16 个模型全部成功）。

---

## 7. Projected Newton：扭曲最小化

拿到局部单射初值后，在 $T_{cb}$ 上最小化面积加权的**对称 Dirichlet 能量**：

$$
E_{\text{iso}}=\frac12\bigl(\sigma_1^2+\sigma_1^{-2}+\sigma_2^2+\sigma_2^{-2}\bigr),
\qquad
E_{\text{total}}=\sum_{t\in T_{cb}}A_t\,E_{\text{iso}}
$$

（共形扭曲记 $k=|f_{\bar z}|/|f_z|$。）

$E_{\text{iso}}$ 非凸，Hessian 不定，朴素 Newton 不能用。做法沿用 [CW15]：

1. **逐三角形**计算关于 $(f_z^i,f_{\bar z}^i)$ 的 $4\times4$ 小 Hessian $Q_i$，**解析投影到 PSD 锥**（[CW15] 给闭式公式）；
2. 组装 $H=\sum_i\tilde J_i^tQ_i\tilde J_i$——因为每个 $Q_i$ 已 PSD，其和自然 PSD，Newton 方向必是下降方向；

> 注意这里的 Hessian 不是 $3\times3/6\times6$ 的逐元素矩阵，而是 $2(|\partial V|+|C|+n-1)$ 维的**子空间** Hessian（变量是 $c$）。

3. **两次线搜索**：一次保持局部单射（防翻转），一次保证能量下降（Armijo）。

Observation 2 保证：只在 $T_{cb}$ 上压能量，就能有效降低全网格扭曲——论文 Figure 7 显示 Newton 之后 $E_{\text{iso}}$ 与 $k$ 显著下降，且扭曲"聚集"在锥点与边界附近（这正好印证 Observation 2）。

---

## 8. 实验结果

实现：Autodesk Maya 2018 插件；子空间构造用 C++ + PARDISO 6.0 选择性求逆，ATP/PN 用 Matlab（经 Matlab engine 从 C++ 调用，非 GPU）。硬件 Xeon E5-1650 3.6 GHz / 32 GB。

**Group A（带锥点，61 个 sphere/disk，主要来自 [MPZ14] 基准，外加 250K 面 / 509 锥点的 "awakening" 做压力测试）**

| 模型 | 面数 | 锥点 | 子空间构造 | ATP | Newton | 总计 | HGP | 加速 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| retinal | 7,282 | 18 | 0.06 | 0.00 | 0.07 | 0.14 | 0.81 | ×6 |
| horse | 39,698 | 52 | 0.30 | 0.00 | 0.11 | 0.42 | 4.75 | ×11 |
| uu-memento100k | 99,932 | 107 | 0.98 | 0.02 | 0.13 | 1.13 | 11.00 | ×10 |
| awakening | 250,153 | 509 | 4.07 | 0.15 | 0.51 | 4.74 | Fail（>6 小时） | — |

结论：
- **总时间 ~ 1 秒量级**（10 万面），比 HGP 快一个数量级，比 [CLW16] 快 2–4 个数量级；
- **绝大多数时间花在子空间构造**上，ATP 与 PN 极快；
- 质量上 $E_{\text{iso}}$ 略优于 HGP，共形扭曲 $k$ 平均好约 3 倍（HGP 并不优化畸变）。

**Group B（无锥点，16 个亏格 0 / 多连通圆盘，与 [SPSH*17] 的 Composite Majorization 对比）**

| 模型 | 面数 | 边界顶点 | DOF | 子空间构造 | Newton | 总计 | CM |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| beetle_refined | 38,726 | 1,136 | 138 | 0.31 | 0.15 | 0.47 | 2.79 |
| bear | 296,409 | 557 | 557 | 2.17 | 0.91 | 3.08 | 20.07 |
| mannequin-devil_2m | 1,815,057 | 929 | 929 | 12.31 | 1.25 | 13.59 | 185.17 |

百万面级模型数秒完成；Figure 6 用多连通 car 模型对比 CETM [SSP08]——共形等价平坦度量无法在不切开网格的前提下浸入平面，因此 CETM 无法保持映射连续，而**空间变量**的调和映射天然连续。

**鲁棒性**

- 77 个模型中 **66 个成功**；
- 9 个出现 2–3 处局部翻转，源于形状很差的源网格三角形导致的**负 cotangent 权**，用"把单顶点移入其 1-ring 核"的启发式全部修复；
- 11 个失败：2 个源于 PARDISO 数值问题，9 个源于 **ATP 不收敛**——此时 $\mathcal{N}(A_{\text{hgp}})\cap B=\varnothing$，即 frame 凸化出的集合与调和空间不相交；
- 与 HGP 相比鲁棒性略低，因为 HGP 还有一堆启发式没被采用：调整 Laplacian 权重、失败时迭代更新 frame、homotopy frame fixing；且 HGP 把调和约束**软化为最小二乘**（相当于在稍大的双调和映射空间里搜索），进一步降低不可行概率。论文猜测：光滑情形下亏格 0 曲面总存在共形映射（[BGB08]），而共形映射也是调和的，所以**只调 frame 或许就足以提升鲁棒性**。

---

## 9. 与 HGP 的对比

| | HGP [BCW17] | **FastHGP** |
| :--- | :--- | :--- |
| 调和约束 | 软约束（二次误差项最小二乘松弛） | **硬约束**（精确落在 $\mathcal{N}(A_{\text{hgp}})$ 内） |
| 搜索空间 | 全顶点 UV，$2\|V\|$ 维 | $c_{\text{int}}$，$2(\|\partial V\|+\|C\|+n-1)$ 维（+ 虚拟顶点再降维） |
| 核心求解器 | MOSEK SOCP | 1 次 LU + **选择性求逆** → ATP → Projected Newton |
| 畸变优化 | 无（靠 SOCP 隐式控制） | $T_{cb}$ 上对称 Dirichlet + Projected Newton，$k$ 平均好 3 倍 |
| 代价 | 数十次以上线性求解 | $\approx 1$–$2$ 次线性求解 |
| 鲁棒性 | 极高（含多项启发式） | 略低；无锥情形**理论完全鲁棒**，有锥时 ATP 约 10–15% 失败，需回退 HGP |

**适用边界**：论文限定亏格 0（球面、圆盘、多连通圆盘）；高亏格的代数分析与实现在 future work 中。锥点位置与角度按 [FL16, CLW16, BCW17] 的做法视为**给定**输入。

---

## 10. 要点小结

1. **硬约束 vs 软约束**：FastHGP 在 HGP 的调和解空间内精确搜索，不松弛调和性，代价却被压到 1–2 次线性求解——这是"用了一个非线性方法的鲁棒性，付了线性方法的钱"。
2. **两个 Observation 是子空间方法的理论根基**：局部单射性只看 $T_{cb}$；共形扭曲上界出现在边界/锥点邻域。变量数与目标项数因此同时与网格密度解耦。
3. **KKT 公式化 (4)(5) 是关键工程技巧**：避免显式编码繁琐的旋转调和 (3)；$K$ 的可逆性（Theorem 6）反过来证明了 $A_{\text{hgp}}$ 满秩（Theorem 8）。它同时是子空间构造与最终回代的**唯一线性代数入口**（详见 §4 末节"KKT 在算法中的三重角色"）。
4. **系统维数**：$\dim\mathcal{N}(A_{\text{hgp}})=2(|\partial V|+|C|+n-1)$，只与锥点数、边界顶点数和边界分量数有关。
5. **选择性求逆是速度来源**：只取 $K^{-1}$ 中 $V_{cb}$ 的行，代价 ≈ 1 次 LU，比"分解 + 多次回代再丢弃"快一个数量级；完整零空间基自始至终不被构造。
6. **ATP 求可行初值，Projected Newton 压畸变**，二者都在同一个低维空间中工作；无锥 + trivial holonomy 时 ATP 被 [GGT06] 的一次线性求解取代，且带理论保证。
7. **主要残留问题**：ATP 的可行性（$\mathcal{N}(A_{\text{hgp}})\cap B$ 是否非空）依赖 frame 选择；负 cotangent 权导致的孤立翻转需启发式修补。

---

## 参考文献

1. **论文**：Hefetz E. F., Chien E., Weber O. *A Subspace Method for Fast Locally Injective Harmonic Mapping*. Computer Graphics Forum, 38(2), 2019.
2. Bright A., Chien E., Weber O. *Harmonic Global Parametrization with Rational Holonomy*. ACM TOG, 36(4), 2017. [BCW17]
3. Hefetz E. F., Chien E., Weber O. *Fast Planar Harmonic Deformations with Alternating Tangential Projections*. CGF, 36(5), 2017. [HCW17]
4. Chen R., Weber O. *GPU-accelerated Locally Injective Shape Deformation*. ACM TOG, 36(6), 2017. [CW17]
5. Chen R., Weber O. *Bounded Distortion Harmonic Mappings in the Plane*. ACM TOG, 34(4), 2015. [CW15]
6. Lipman Y. *Bounded Distortion Mapping Spaces for Triangular Meshes*. ACM TOG, 31(4), 2012. [Lip12]
7. Gortler S. J., Gotsman C., Thurston D. *Discrete One-Forms on Meshes and Applications to 3D Mesh Parameterization*. CAGD, 23(2), 2006. [GGT06]
8. Kuzmin A., Luisier M., Schenk O. *Fast Methods for Computing Selected Elements of the Green's Function...*. Euro-Par, 2013. [KLS13]；Verbosio F., et al. *Enhancing the Scalability of Selected Inversion Factorization Algorithms*. J. Comput. Sci., 2017. [VCKS17]
9. Bommes D., Zimmer H., Kobbelt L. *Mixed-integer Quadrangulation*. SIGGRAPH, 2009. [BZK09]
10. Shtengel A., Poranne R., Sorkine-Hornung O., Kovalsky S. Z., Lipman Y. *Geometric Optimization via Composite Majorization*. ACM TOG, 36(4), 2017. [SPSH*17]
11. Chien E., Levi Z., Weber O. *Bounded Distortion Parametrization in the Space of Metrics*. ACM TOG, 35(6), 2016. [CLW16]
12. Weber O., Myles A., Zorin D. *Computing Extremal Quasiconformal Maps*. CGF, 31(5), 2012. [WMZ12]
