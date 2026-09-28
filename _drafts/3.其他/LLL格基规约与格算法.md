---
layout: post
title: "LLL 格基规约与格算法"
category: Parameterization
categories: ["Parameterization", "Parameterization-Appendix"]
---

本文自 [带约束最优化]({%- assign p = site.posts | where: "title", "带约束最优化" | first -%}{{ p.url | relative_url }}) 的「整数规划与混合整数规划」一节拆出，系统介绍 **LLL 格基规约**及其在整数规划、密码分析中的角色，并详述 Lenstra–Kannan、Fincke–Pohst、Coppersmith 等格算法。

---

### 格基规约 (LLL) 与整数规划

**LLL 算法**（Lenstra–Lenstra–Lovász, 1982）作用于 $n$ 维格 (lattice)

$$
\mathcal{L}(\boldsymbol{B})=\Big\{\sum_{i=1}^n z_i\boldsymbol{b}_i \;\Big|\; z_i\in\mathbb{Z}\Big\},
\qquad \boldsymbol{B}=[\boldsymbol{b}_1,\ldots,\boldsymbol{b}_n]\in\mathbb{R}^{n\times n}
$$

在多项式时间内输出**近似短基 (reduced basis)**：新基向量在 Gram–Schmidt 正交化意义下"几乎正交"，且长度不超过最短非零格向量若干倍（因子为 $2^{O(n)}$ 量级）。LLL 的**原始设计目标**是**同步丢番图逼近 (simultaneous Diophantine approximation)**：给定有理向量，求整数系数使线性组合尽可能小——这是格算法的基础子程序，但本身**不是**通用整数规划求解器。

#### 哪条算法才是「LLL 用于整数规划」？

文献中常把多种格方法并列，需区分**问题类型**：

| 算法 / 问题 | 代表文献 | 与 ILP 的关系 |
|-------------|----------|---------------|
| **同步丢番图逼近** | LLL (1982) | LLL 的**原生应用**；Lenstra IP 在降维步骤中调用 LLL 求短组合，属**子程序** |
| **Lenstra 固定维数 IP** | Lenstra (1983), *Math. Oper. Res.* | **通用 ILP 的精确算法**：$n$ 固定时，对 $\min \boldsymbol{c}^T\boldsymbol{x}$ s.t. $\boldsymbol{A}\boldsymbol{x}\le\boldsymbol{b}$, $\boldsymbol{x}\in\mathbb{Z}^n$ 多项式时间可解 |
| **Kannan 改进** | Kannan (1987), *Math. Oper. Res.* | 在 Lenstra 框架上改进维数依赖与球分割 (sphere partition)，仍是**固定维数 ILP** 的主线延续 |
| **Fincke–Pohst** | Fincke & Pohst (1985) | 在格上**精确枚举短向量 / 最近向量 (CVP/SVP)**；用于格密码、低维格完全求解，**不是**一般 ILP 的标准框架 |
| **Coppersmith 小根法** | Coppersmith (1996) 等 | 对模多项式求**小整数根**（RSA 密码分析）；构造特殊格后做 LLL，问题类与 (9) 不同 |

**结论**：若问「LLL 用于**整数规划 (ILP/MILP)** 的具体算法」，答案是 **Lenstra (1983) 固定维数整数规划算法**，后续理论改进以 **Kannan (1987)** 为代表。**丢番图逼近**是 LLL 能力与 Lenstra 算法内部的**工具**，不是与 Lenstra 并列的另一套 IP 求解器。**Fincke–Pohst** 与 **Coppersmith** 解决的是格上其他经典问题（最短/最近向量、小多项式根），与通用 ILP 主线路相关但通常不称为「整数规划算法」本身。

#### Lenstra 固定维数 IP 算法概要

考虑标准形式 ILP（最大化化为最小化同理）：

$$
\min_{\boldsymbol{x}\in\mathbb{Z}^n}\;\boldsymbol{c}^T\boldsymbol{x}
\quad\text{s.t.}\quad
\boldsymbol{A}\boldsymbol{x}\le\boldsymbol{b}
$$

**核心结论**：当整数变量维数 $n$ **固定**时，(9) 可在**关于输入规模（约束数、系数位数）的多项式时间**内精确求解；时间复杂度中 $n$ 出现在指数上（Kannan 后续改进了该指数）。

**Lenstra (1983) 三步结构**：

1. **椭球法 / 线性规划**：多项式时间判定 $\{\boldsymbol{x}\in\mathbb{R}^n\mid\boldsymbol{A}\boldsymbol{x}\le\boldsymbol{b}\}$ 是否非空，并估计可行多面体在目标方向上的"厚度"；
2. **递归降维 (recursive projection)**：在最优值附近选取仿射超平面 $\{\boldsymbol{x}\mid\boldsymbol{a}^T\boldsymbol{x}=\beta\}$，在维数 $n-1$ 的子问题上递归；$\beta$ 只需在有限个由**短格向量长度**决定的临界层中枚举；
3. **LLL 短基**：对由 $\boldsymbol{A}$ 行向量张成的格（或其变体）运行 LLL，得到近似正交基，使超平面切片厚度 $\le 2^{O(n)}$ 倍最短基长——从而每层只需枚举 $O(1)$ 个整数候选（$n$ 固定时）。

因此 LLL 在 IP 中的角色是 **Lenstra–Kannan 固定维数框架的内核子程序**，而非像 Gurobi 那样直接处理数万 0–1 变量的通用引擎。

#### 与背包 / 子集和

**子集和** $\sum_i w_i x_i = W$，$x_i\in\{0,1\}$ 是典型 ILP。LLL 可在**密码分析**中攻破基于子集和的单向背包（Merkle–Hellman 等），其本质是：在由权重向量张成的格上，最短向量对应于"权重和接近目标"的 0–1 组合。这与 (9) 的格观点一致，也说明**格结构清晰时**，规约比盲目分支更有效。

#### 实践定位（与分支定界对比）

| 维度 | 分支定界 / Branch-and-Cut | Lenstra–Kannan（LLL 子程序） |
|------|---------------------------|------------------|
| 变量维数 $n$ | 可上万（依赖结构） | 理论多项式仅当 $n$ **固定**；$n\gtrsim 10$ 已不实用 |
| 约束规模 | 稀疏 MILP 工业标准 | 适合**低维**全整数子问题 |
| 最优性 | 全局最优 | 全局最优（固定 $n$ 时） |
| 典型场景 | 通用 MIP/MIQP | 理论复杂度、密码分析、少量整数变量的精确子问题 |

工业 MIP 求解器**不以 LLL 为主循环**；但在以下情形仍值得了解：

- **预处理 / 界收紧**：对某些全幺模或格结构约束，短基可导出有效不等式；
- **几何子问题**：整数变量极少（如局部接缝 $(j,k)\in\mathbb{Z}^2$、单条边跳变枚举）时，直接枚举或交替法已足够，LLL 属"理论备选"而非首选；
- **与割平面互补**：Gomory 割从表像导出；格割 (lattice cut) 族在研究中偶与 LLL 结合，但尚未进入主流求解器默认路径。

#### 小结

LLL 格规约**可以**用于整数规划——其严格意义是作为 **Lenstra (1983) / Kannan (1987) 固定维数 ILP 算法**的短基子程序；丢番图逼近是 LLL 的原生能力，Fincke–Pohst、Coppersmith 则属其他格问题。子集和密码分析等场景则直接利用格最短向量结构。对参数化中的 MIQP（成百上千条边的 $p_e\in\mathbb{Z}$），**交替优化与坐标下降**仍是工程首选；LLL 路线更适合作为理解"整数性为何有时可驯服"的理论补充，而非替代 Branch-and-Cut。各格算法的定义、步骤与相互关系见下文。

---

## 格算法详述

本节系统介绍格 (lattice) 的基本概念、经典计算问题，以及 LLL、丢番图逼近、Lenstra–Kannan 整数规划、Fincke–Pohst、Coppersmith 等算法各自**解决什么问题、输入输出是什么、彼此如何调用**。

---

### A.1 格的定义与几何直观

$n$ 维格是 $\mathbb{R}^n$ 中一组线性无关基向量 $\boldsymbol{b}_1,\ldots,\boldsymbol{b}_n$ 的**全体整系数线性组合**：

$$
\mathcal{L}(\boldsymbol{B})
=\Big\{\boldsymbol{B}\boldsymbol{z}\;\Big|\;\boldsymbol{z}\in\mathbb{Z}^n\Big\},
\qquad
\boldsymbol{B}=[\boldsymbol{b}_1,\ldots,\boldsymbol{b}_n]\in\mathbb{R}^{n\times n}
$$

$\boldsymbol{B}$ 称为**基 (basis)**；同一格有无穷多组基（幺模整数变换 $\boldsymbol{U}\in GL(n,\mathbb{Z})$：$\mathcal{L}(\boldsymbol{B})=\mathcal{L}(\boldsymbol{BU})$）。

**基本域 (fundamental parallelepiped)**：$\mathcal{P}=\{\sum_i t_i\boldsymbol{b}_i\mid t_i\in[0,1)\}$。**协体积 (covolume)** $\det(\mathcal{L})=|\det\boldsymbol{B}|$ 等于 $\mathcal{P}$ 的 $n$ 维体积。

**对偶格 (dual lattice)**：

$$
\mathcal{L}^*=\{\boldsymbol{y}\in\mathbb{R}^n\mid \boldsymbol{y}^T\boldsymbol{x}\in\mathbb{Z},\;\forall\boldsymbol{x}\in\mathcal{L}\}
$$

对偶格在 Fourier 分析、格密码与某些割平面理论中出现。

**Minkowski 定理（直观版）**：任意对称凸体，若体积 $> 2^n\det(\mathcal{L})$，则内部必含非零格点。这保证"短向量存在"，但**找到**短向量是困难的——格算法的核心即在此。

---

### A.2 格上的经典计算问题

| 问题 | 英文 | 输入 | 输出 | 难度 |
|------|------|------|------|------|
| **最短向量** | SVP | 基 $\boldsymbol{B}$ | 非零 $\boldsymbol{v}\in\mathcal{L}$ 使 $\|\boldsymbol{v}\|$ 最小 | NP-hard（精确）；LLL 给近似 |
| **最近向量** | CVP | 基 $\boldsymbol{B}$，目标 $\boldsymbol{t}\in\mathbb{R}^n$ | $\boldsymbol{v}\in\mathcal{L}$ 使 $\|\boldsymbol{t}-\boldsymbol{v}\|$ 最小 | NP-hard（精确） |
| **$\gamma$-最短向量** | $\gamma$-SVP | 基 $\boldsymbol{B}$，近似因子 $\gamma$ | 非零 $\boldsymbol{v}$ 使 $\|\boldsymbol{v}\|\le\gamma\cdot\lambda_1$ | LLL 实现 $\gamma=2^{O(n)}$ |
| **同步丢番图逼近** | Simult. Diophantine approx. | 有理向量 $\boldsymbol{\alpha}\in\mathbb{Q}^k$，容差 $\varepsilon$ | 整数 $\boldsymbol{q}\ne 0$ 使 $\|q\boldsymbol{\alpha}-\lfloor q\boldsymbol{\alpha}\rceil\|_\infty\le\varepsilon$ | LLL 多项式时间（$\varepsilon$ 依赖输入） |

**与整数规划的关系**：ILP 可行域是凸多面体与 $\mathbb{Z}^n$ 的交；当维数低时，可将"找整数点"转化为格上**短向量**或**薄切片中的格点枚举**——这正是 Lenstra 算法的几何来源。

---

### A.3 LLL 格基规约算法

**目标**：给定基 $\boldsymbol{B}$，在多项式时间内输出**规约基 (reduced basis)** $\boldsymbol{B}'$，使基向量"近似正交且逐渐变短"，从而 SVP/CVP 的贪心近似更可靠。

#### Gram–Schmidt 正交化

对 $\boldsymbol{b}_1,\ldots,\boldsymbol{b}_n$ 计算：

$$
\boldsymbol{b}_j^*=\boldsymbol{b}_j-\sum_{i=1}^{j-1}\mu_{ji}\boldsymbol{b}_i^*,
\qquad
\mu_{ji}=\frac{\boldsymbol{b}_j^T\boldsymbol{b}_i^*}{\|\boldsymbol{b}_i^*\|^2}
$$

$\boldsymbol{b}_j^*$ 为第 $j$ 个方向上的正交分量；$\mu_{ji}$ 为投影系数。

#### Lovász 条件（规模规约 + 交换）

LLL 基满足：

1. **尺寸规约 (size reduction)**：$|\mu_{ji}|\le\frac{1}{2}$（$j>i$），通过整数行变换 $\boldsymbol{b}_j\leftarrow\boldsymbol{b}_j-\lfloor\mu_{ji}\rceil\boldsymbol{b}_i$ 实现；
2. **Lovász 交换**：若 $\|\boldsymbol{b}_j^*\|^2\ge (\delta-\mu_{j,j-1}^2)\|\boldsymbol{b}_{j-1}^*\|^2$ 不成立（常取 $\delta=3/4$），则交换 $\boldsymbol{b}_{j-1}$ 与 $\boldsymbol{b}_j$ 并回退 $j$。

**输出性质**（$n$ 维格）：

- 第一基向量满足 $\|\boldsymbol{b}_1\|\le 2^{(n-1)/2}\lambda_1$（$\lambda_1$ 为最短向量长度）；
- 运行时间 $O(n^5\log^3 B)$（$B$ 为系数上界），**关于维数 $n$ 是多项式的**。

#### 作为同步丢番图逼近算法

给定 $\boldsymbol{\alpha}=(\alpha_1,\ldots,\alpha_{k-1})\in\mathbb{Q}^{k-1}$，构造 $(k+1)$ 维格，基向量形如 $(1,0,\ldots,0)$、$(\alpha_1,1,0,\ldots,0)$、$\ldots$、$(\alpha_{k-1},0,\ldots,1)$，并缩放最后一维以控制精度。LLL 输出的**第一个短向量**给出整数 $q$ 与小误差向量，使 $q\alpha_i$ 接近整数——这是 LLL 论文的原始动机，也是 Lenstra IP 中"枚举薄层"的量化依据。

---

### A.4 Babai 最近平面法（CVP 近似）

**输入**：LLL 规约后的基 $\boldsymbol{B}'$，目标 $\boldsymbol{t}$。  
**步骤**：从最高维到最低维，依次将 $\boldsymbol{t}$ 在 Gram–Schmidt 方向上**四舍五入到最近整数系数**，得到 $\boldsymbol{v}\in\mathcal{L}$。  
**保证**：若基为 LLL 规约，则 $\|\boldsymbol{t}-\boldsymbol{v}\|\le 2^{n/2}\cdot\mathrm{dist}(\boldsymbol{t},\mathcal{L})$。  
**定位**：多项式时间 **CVP 近似**；与 Fincke–Pohst 的**精确**枚举形成"快但不准 / 慢但精确"的两极。

---

### A.5 Lenstra 固定维数整数规划算法 (1983)

**问题**：(9) 式，$\boldsymbol{x}\in\mathbb{Z}^n$，$m$ 个线性不等式，系数有理数、位数多项式有界。

**定理**：固定 $n$ 时，存在算法在 $\mathrm{poly}(m,\log\|\boldsymbol{A}\|,\log\|\boldsymbol{b}\|,\log\|\boldsymbol{c}\|)$ 时间内判定可行性并求最优解。

#### 几何直觉

设 $P=\{\boldsymbol{x}\in\mathbb{R}^n\mid\boldsymbol{A}\boldsymbol{x}\le\boldsymbol{b}\}$ 为有界多面体（无界时可先加框约束）。在目标 $\boldsymbol{c}$ 方向上，最优整数解落在厚度有限的"最优带"内。算法在带内选取超平面 $\boldsymbol{c}^T\boldsymbol{x}=z$，将问题投影到 $n-1$ 维仿射子空间；关键是如何只枚举**有限个** $z$，使得不会漏掉最优整数点。

#### 算法骨架（递归）

```
Lenstra-IP(n, A, b, c):
  1. 用椭球法判定 P 是否为空；若空则返回不可行
  2. 计算 P 在 c 方向上的下界 z_lo 与上界 z_hi（LP + 舍入）
  3. 对由 A 的行张成的格（或 Parallelepiped 相关格）运行 LLL，得短基，估计切片厚度 τ
  4. 在 [z_lo, z_hi] 中，以步长 ~τ 枚举 z；对每个 z：
       在 {x | Ax≤b, c^T x = z} 上递归调用 Lenstra-IP(n-1, ...)
  5. n=1 时为一维整数区间上的直接枚举
```

**LLL 的作用**：短基给出厚度 $\tau=2^{O(n)}\lambda_1$ 的上界，使第 4 步每层候选数为 $O(1)$（$n$ 固定），总分支数为输入规模的**多项式**。

**局限**：时间形如 $\tau(n)\cdot\mathrm{poly}(m,\log)$，其中 $\tau(n)$ 对 $n$ 为**指数**；$n\ge 10$ 时几乎不可用。工业 MILP **不**实现此算法。

---

### A.6 Kannan 改进 (1987)

Kannan 在 Lenstra 框架上改进了两处：

1. **球分割 (sphere partition)**：用格覆盖与 Minkowski 凸体定理更精细地划分搜索区域，减少递归树分支因子；
2. **对偶格与短向量界**：改进维数 $n$ 在指数上的常数，从 $2^{O(n^2)}$ 量级降至 $2^{O(n\log n)}$ 量级（渐近意义下）。

**定位**：与 Lenstra **同一问题类**（固定维数 ILP）的**理论加速**；仍属"维数固定、输入规模多项式"的精确算法族。文献中常合称 **Lenstra–Kannan 算法**。

---

### A.7 Fincke–Pohst 枚举算法 (1985)

**问题**：在格 $\mathcal{L}(\boldsymbol{B})$ 上**精确**求解 SVP 或 CVP（在目标 $\boldsymbol{t}$ 附近找最近格点）。

#### 思想：球面收缩 (sphere shrinking)

维护半径 $R$，在球 $\{\boldsymbol{x}\in\mathbb{R}^n\mid\|\boldsymbol{x}-\boldsymbol{t}\|\le R\}$ 内**枚举**所有格点；从 $R$ 较大开始，找到向量后缩小 $R$。枚举利用 Gram–Schmidt 坐标剪枝（Schnorr–Euchner 实现是经典优化）。

**复杂度**：最坏情况指数 $2^{O(n)}$，但**低维**（$n\le 20$ 量级）常比 LLL 近似更可靠；格密码攻击、低维子集和完全求解中常用。

**与 ILP 的关系**：**不是**把一般 $\boldsymbol{A}\boldsymbol{x}\le\boldsymbol{b}$ 直接化为 Fincke–Pohst 的标准输入；但若已将 ILP 化简为"在已知有界区域内找最短/最近格点"（如子集和格），则 Fincke–Pohst 是精确求解器，而 LLL+Babai 只是近似。

| | LLL + Babai | Fincke–Pohst |
|--|-------------|--------------|
| 时间 | $n$ 的多项式 | $2^{O(n)}$ 最坏 |
| 结果 | 近似最短/最近 | **精确**最短/最近 |
| 典型 $n$ | 任意（大 $n$ 也可跑） | 小（$\lesssim 20$） |

---

### A.8 Coppersmith 小根法 (1996) 与 Howgrave–Graham

**问题**：给定整系数多项式 $f(x)$、模数 $N$（常为大合数），求**小**整数根 $|x|<X$，使得 $f(x)\equiv 0\pmod N$。

#### 格构造（一元情形，简化）

设 $f(x)=\sum_j a_j x^j$，$\deg f=d$。选取整数 $m,t$，构造 $d(m+1)$ 维格，基向量对应多项式 $g_{i,j}(x)=x^j N^{m-i} f(x)^i$ 在 $x=0$ 处的系数向量（适当缩放使范数反映"小根"条件）。

#### Howgrave–Graham 引理

若格中向量 $\boldsymbol{v}$ 的欧氏范数 $<\,N^m/\sqrt{\dim}$，则 $x_0$ 同时是 $f(x)\equiv 0\pmod{N^m}$ 与 $f(x)=0$ 在 $\mathbb{Z}$ 上的根——从而得到模 $N$ 的小根。

**步骤**：对构造的格运行 **LLL**，取第一个足够短的基向量，解一元方程。

**与 ILP 的关系**：问题类是**多项式同余小根**，不是线性不等式系统 (9)。在密码分析（RSA 低指数、部分密钥泄露）中极重要；与背包 ILP 同属"格技巧"家族，但**不**归入 Lenstra IP 主线。

**推广**：多变量、不同模、求近似根等均有 Coppersmith 型变体；核心仍是**特殊格 + LLL 短向量**。

---

### A.9 子集和格：各算法如何落地

**子集和**：给定权重 $w_1,\ldots,w_k$、目标和 $W$，求 $x_i\in\{0,1\}$ 使 $\sum w_i x_i=W$。

经典格构造（维度 $k+1$）：

$$
\boldsymbol{b}_0=(W, w_1,\ldots,w_k),\quad
\boldsymbol{b}_i=(0,\ldots,\underbrace{1}_{i\text{位}},\ldots,0),\; i=1,\ldots,k
$$

（具体缩放因子依攻击模型而变。）短向量 $(W-\sum w_i x_i,\,x_1,\ldots,x_k)$ 对应 0–1 解。

| 目标 | 选用算法 |
|------|----------|
| 快速启发式攻击 | LLL → 取 $\boldsymbol{b}_1$，舍入 $x_i$ |
| 低维精确解 | Fincke–Pohst 枚举 |
| 一般线性不等式 ILP、$n$ 固定 | Lenstra–Kannan |
| 模多项式小根 | Coppersmith + Howgrave–Graham |

---

### A.10 算法依赖关系总览

```
                    ┌─────────────────────────┐
                    │  格 L(B)  +  经典问题    │
                    │  SVP / CVP / 丢番图逼近   │
                    └───────────┬─────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
        ┌───────────┐    ┌─────────────┐   ┌──────────────┐
        │ LLL (1982)│    │ Fincke-Pohst│   │ 特殊格构造    │
        │ 短基规约   │    │ 精确枚举 SVP│   │ (子集和/Copper)│
        └─────┬─────┘    │    / CVP    │   └──────┬───────┘
              │          └─────────────┘          │
              ├──────────► Babai CVP 近似           │
              │                                     │
              ├──────────► 丢番图逼近（原生输出）    │
              │                                     │
              ▼                                     ▼
        ┌─────────────────┐                  ┌─────────────┐
        │ Lenstra IP(1983)│                  │ Coppersmith │
        │  + Kannan(1987) │                  │  小根法      │
        │ 固定维数 ILP    │                  └─────────────┘
        └─────────────────┘

并行工业路线（非格主循环）: Branch-and-Bound / Branch-and-Cut → Gurobi, CPLEX
```

---

### A.11 复杂度与选用指南

| 算法 | 问题 | 时间（典型表述） | 精确性 | 何时考虑 |
|------|------|------------------|--------|----------|
| LLL | 短基 / 丢番图逼近 | $\mathrm{poly}(n,\log B)$ | 近似 SVP 因子 $2^{O(n)}$ | 格预处理、密码、Lenstra 子程序 |
| Babai | CVP | $\mathrm{poly}(n,\log B)$ | 近似，因子 $2^{O(n)}$ | 规约基上的快速最近点 |
| Lenstra–Kannan | 固定 $n$ 的 ILP | 输入 $\mathrm{poly}$，$n$ 在指数 | **精确** | 理论、极低维全整数子问题 |
| Fincke–Pohst | SVP/CVP | $2^{O(n)}\cdot\mathrm{poly}(\log B)$ | **精确** | $n\lesssim 20$ 的格完全求解 |
| Coppersmith | 模多项式小根 | $\mathrm{poly}(\log N)$（依赖 $X$） | 条件精确 | 密码分析、特殊代数结构 |
| Branch-and-Cut | 通用 MILP/MIQP | 指数最坏 | **精确** | 工业规模、参数化外通用求解 |

**与 MIQP 应用的衔接**：cross field 问题 (6) 的整数维是**边数级**（可达 $10^4$），且目标可分离——**交替优化 (7)(8)** 利用结构，复杂度每轮近线性；Lenstra–Kannan 的维数指数爆炸使其不适用。格算法在此文中的价值主要是**理解整数性与几何结构**，而非替代 MIQ 专用启发式。详见 [带约束最优化]({%- assign p = site.posts | where: "title", "带约束最优化" | first -%}{{ p.url | relative_url }}) 中的 MIQ 交叉场小节。

---
