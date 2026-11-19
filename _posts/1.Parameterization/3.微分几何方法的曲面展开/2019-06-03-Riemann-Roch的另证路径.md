---
layout: post
category: Parameterization
categories: ["Parameterization", "Parameterization-QuadRemeshing"]
title: "Riemann-Roch 的另证路径：线丛、层与上同调"
---

> 本文是《[Abel-Jacobi 与 Riemann-Roch 的证明]({% post_url 1.Parameterization/3.微分几何方法的曲面展开/2019-06-02-Abel-Jacobi与Riemann-Roch定理证明 %})》的姊妹篇。那一篇只用复分析语言（亚纯微分、留数、奇异积分、调和积分），刻意不引入线丛与上同调；本文单独承接这套现代语言，把同一条定理的**第二条证明路径**放在这里，供读者在两套语言之间来回对照。

## 0. 为什么单列成文

- **符号打架**：复分析路径写 $l(D)$、$i(D)$、$d(D)$；现代路径写 $h^0$、$h^1$、$\deg$。混在一节里读者要不停翻译，论证的「依据」反而被记号遮住。
- **依赖不同**：复分析路径依赖 Hodge 定理与奇异积分，自足、可逐行核对；现代路径依赖层与上同调，工具更重、但结论更强（可直接推广到高维复流形）。
- **原文条件**：现代路径的出处是伍鸿熙、吕以辇、陈志华《紧黎曼曲面引论》，其 PDF 为**无文字层扫描件**，无法逐字照录。故本文只给章节索引、思路提纲与对照表，**不做原文摘录、不标页码**。

## 1. 两条路径并列对照

| 栏目 | A1：复分析路径（《证明》一文的 §2） | A2：线丛与层论路径（本文） |
|---|---|---|
| 前提假设 | 紧致黎曼曲面 + Hodge 定理 | 紧致黎曼曲面 + 全纯线丛、层与上同调 |
| 核心工具 | 奇异积分；$S$、$T$ 互为转置 | 全纯线丛的上同调、Dolbeault 引理、Serre 对偶 |
| 关键一步 | $\dim\mathrm{Im}\,d=\dim m(D)-\dim i(D)$ | RR 被重写为指标公式 $\chi(\mathcal O(D))=\deg D+1-g$ |
| 难点 | 奇异积分的良定义、$S,T$ 矩阵互为转置 | 层上同调的构造与消没定理 |
| 结论强度 | 完整（含所有技术细节） | 完整，且可推广到高维复流形 |
| 可计算性 | 低（以存在性为主） | 中（给出 Hirzebruch–Riemann–Roch 的入口） |

**交汇点**：两条路径算的是同一个量 $\ell(D)-\ell(K-D)$。A1 用 $S/T$ 的秩把它算出来，A2 用 $h^0-h^1$ 的指标把它算出来；Serre 对偶在两边的形态完全一致。

## 2. 章节索引（伍鸿熙等《紧黎曼曲面引论》）

按原书章节顺序，A2 的完整链条分布如下（章节号可查，页码从略）：

| 章节 | 内容 | 在证明中的位置 |
|---|---|---|
| 第一章 §4 | 亚纯函数与亚纯微分 | 建立 $(\omega)$、留数、$K$ 的语言 |
| 第二章 §5 | 因子 | 除子群、线性等价、$l(D)$ |
| 第二章 §6 | RR 定理及初步应用 | 定理陈述与用复分析语言的证明 |
| 第三章 §7 | 全纯线丛 | 把 $D$ 换成 $\mathcal O(D)$ |
| 第三章 §8 | 层论 | 层、茎、正合列 |
| 第三章 §9 | 层上同调 | $H^0$、$H^1$ 与 Čech 计算 |
| 第三章 §11 | Hodge 定理和 Serre 对偶 | $H^1(M,\mathcal O(D))\cong H^0(M,\mathcal O(K-D))^{*}$ |
| 第三章 §12 | RR 定理证明 | $\chi(\mathcal O(D))=\deg D+1-g$ |
| 第五章 §19 | 应用 | Abel 定理与 Jacobi 反演的层论表述 |

## 3. A2 的思路提纲（逐步节点）

以下每步都写成「已知 → 依据 → 得到」，与《[证明注记与对照表]({% post_url 1.Parameterization/3.微分几何方法的曲面展开/2019-06-04-证明注记与对照表 %})》的节点格式一致。

**步 1（把除子变成线丛）**
已知：因子 $D=\sum n_i p_i$ 与开覆盖 $\{U_\alpha\}$，$D$ 在 $U_\alpha$ 上由亚纯函数 $f_\alpha$ 给出。依据：转移函数 $g_{\alpha\beta}=f_\beta/f_\alpha$ 在 $U_\alpha\cap U_\beta$ 上全纯且无零点，满足上循环条件 $g_{\alpha\beta}g_{\beta\gamma}g_{\gamma\alpha}=1$。得到：复线丛 $\mathcal O(D)$；且 $D\sim D'\iff\mathcal O(D)\cong\mathcal O(D')$。

**步 2（截面 = 被 $D$ 压住的亚纯函数）**
已知：$\mathcal O(D)$ 的局部全纯截面 $s_\alpha$ 满足 $s_\alpha=g_{\alpha\beta}s_\beta$。依据：把 $s_\alpha$ 与 $f_\alpha$ 相乘，得到 $U_\alpha$ 上的亚纯函数 $h=f_\alpha s_\alpha$，它在重叠处满足 $h_\alpha=h_\beta$。得到：$H^0(M,\mathcal O(D))\cong L(D)$，故 $\ell(D)=h^0(D)$。

**步 3（一阶上同调 = 被 $D$ 允许的亚纯微分）**
已知：Čech 1-上链 $\{c_{\alpha\beta}\}$ 模 1-上边界，或等价地用 Dolbeault 模型 $H^1(M,\mathcal O(D))\cong H^{0,1}_{\bar\partial}(M,\mathcal O(D))$。依据：两条模型给出同一个群。得到：$i(D)\cong H^1(M,\mathcal O(D))$，故 $\dim i(D)=h^1(D)$。

**步 4（Serre 对偶）**
已知：$M$ 紧致。依据：Serre 对偶定理。得到：$H^1(M,\mathcal O(D))\cong H^0(M,\mathcal O(K-D))^{*}$，于是 $h^1(D)=h^0(K-D)=\ell(K-D)$；这正是《证明》一文里 $i(D)\cong l(K-D)$ 的现代写法。

**步 5（指标 = 度数 + 1 − 亏格）**
已知：$\bar\partial_D:A^{0,0}(\mathcal O(D))\to A^{0,1}(\mathcal O(D))$ 是椭圆算子。依据：Dolbeault 引理把它的核与余核分别识别为 $H^0$ 与 $H^1$；其指标可由 Hodge 理论（或 Atiyah–Singer 指标定理）算得。得到：
$$
\chi(\mathcal O(D))=h^0(D)-h^1(D)=\deg D+1-g,
$$
把步 2、步 4 代入即得 $\ell(D)-\ell(K-D)=d(D)+1-g$。

**步 6（与 A1 对接）**
已知：A1 的结论 $\dim l(D)=\dim i(D)+d(D)+(1-g)$。依据：步 2–步 5 的翻译。得到：两式逐字对应，只需做一次记号替换。

## 4. 术语对照表

| 复分析路径（A1） | 现代路径（A2） | 说明 |
|---|---|---|
| $l(D)$ | $h^0(\mathcal O(D))$ | 极点被 $D$ 控制的亚纯函数空间 |
| $i(D)$ | $h^1(\mathcal O(D))$ | 极点受 $D$ 约束的亚纯微分空间 |
| $d(D)$ | $\deg\mathcal O(D)$ | 除子的次数 / 线丛的次数 |
| $K$ | 典范线丛（余切丛的行列式） | 全纯 $1$-形式的除子 |
| $P$（主除子群） | $\mathcal O(D)\cong\mathcal O$ | 线丛平凡 |
| $\mathrm{Pic}^0(M)$ | 次数为 $0$ 的线丛的模空间 | 零次除子模主除子 |
| Serre 对偶 $i(D)\cong l(K-D)$ | $H^1(\mathcal O(D))\cong H^0(\mathcal O(K-D))^{*}$ | 同一个事实的两种写法 |

## 5. 与两篇主文的关系

| 结论 | A1 里的位置 | A2 里的位置 |
|---|---|---|
| RR 公式 | 《证明》§2.6 情形 (1)–(3) | 本文步 5 |
| $d(K)=2g-2$ | 《证明》§2.7 推论 3.3.5 | 步 5 取 $D=K$ |
| 度数足够大时的维数 | 《证明》§2.7 定理 3.4.2 | 步 5 加消没定理 $h^1=0$ |
| Abel 定理 | 《证明》§4 | 第五章 §19 的层论表述 |
| Jacobi 反演 | 《证明》§5 | 第五章 §19 的层论表述 |

> 说明：本文只是把第二条路径的骨架摆出来，凡标「依据」处都是引用现成定理（Hodge 定理、Serre 对偶、Dolbeault 引理、指标定理），**不展开证明**；需要逐行核对细节时请回到《[Abel-Jacobi 与 Riemann-Roch 的证明]({% post_url 1.Parameterization/3.微分几何方法的曲面展开/2019-06-02-Abel-Jacobi与Riemann-Roch定理证明 %})》。
