---
layout: post
title: "凸优化与 Lagrangian 对偶"
category: Parameterization
categories: ["Parameterization", "Parameterization-Appendix"]
mathjax: true
---

## 原问题与 Lagrangian

**原问题**最优值记
$$
p^* := \min_{\boldsymbol{x}\in\mathbb{R}^n}\Bigl\{f(\boldsymbol{x})\ :\ c_i(\boldsymbol{x})=0\ (i\in\mathcal{E}),\ c_i(\boldsymbol{x})\le 0\ (i\in\mathcal{I})\Bigr\}.
$$

引入 Lagrange 乘子 $\boldsymbol{\lambda}\in\mathbb{R}^m$（$m=\lvert\mathcal{E}\rvert+\lvert\mathcal{I}\rvert$，仅在 $\mathcal{I}$ 上要求非负），构造 **Lagrangian**
$$
\mathcal{L}(\boldsymbol{x},\boldsymbol{\lambda})
:= f(\boldsymbol{x}) + \sum_{i\in\mathcal{E}\cup\mathcal{I}}\lambda_i\,c_i(\boldsymbol{x}).
$$

### 对偶函数与对偶问题

定义**对偶函数**

$$
\theta(\boldsymbol{\lambda})
:= \inf_{\boldsymbol{x}\in\mathbb{R}^n}\;
\mathcal{L}(\boldsymbol{x},\boldsymbol{\lambda}),
\qquad \lambda_i\ge 0\ \ (i\in\mathcal{I}).
$$

**对偶问题 (dual)** 为
$$
d^* := \max_{\boldsymbol{\lambda}}\;
\theta(\boldsymbol{\lambda})
\quad\text{s.t.}\quad
\lambda_i\ge 0\ \ (i\in\mathcal{I}).
$$

**对偶问题恒为凸优化**——无论原问题是否凸。理由如下：固定 $\boldsymbol{x}$ 时，$\mathcal{L}(\boldsymbol{x},\boldsymbol{\lambda})=f(\boldsymbol{x})+\sum_i\lambda_ic_i(\boldsymbol{x})$ 对 $\boldsymbol{\lambda}$ **仿射**（系数为 $-c_i(\boldsymbol{x})$）。对偶函数
$$
\theta(\boldsymbol{\lambda})=\inf_{\boldsymbol{x}}\mathcal{L}(\boldsymbol{x},\boldsymbol{\lambda})
$$

是一族仿射函数的**逐点下确界**，故 $\theta$ 对 $\boldsymbol{\lambda}$ **凹**。对偶问题即在凸集 $\{\boldsymbol{\lambda}:\lambda_i\ge0,\ i\in\mathcal{I}\}$ 上**极大化凹函数**——等价于极小化凸函数 $-\theta$，属于标准凸优化。

| | **原问题 (primal)** | **对偶问题 (dual)** |
|--|---------------------|---------------------|
| 形式 | $\min f(\boldsymbol{x})$ s.t. $c_i=0\ (i\in\mathcal{E})$、$c_i\le0\ (i\in\mathcal{I})$ | $\max \theta(\boldsymbol{\lambda})$ s.t. $\lambda_i\ge0\ (i\in\mathcal{I})$ |
| 凸性 | 一般**非凸** | **恒凸** |

因此：原问题非凸时，对偶仍给出**凸**的松弛/下界问题（弱对偶 $d^*\le p^*$），但 $d^*$ 未必等于 $p^*$——间隙大小取决于原问题结构（Slater 等条件保证强对偶）。对偶的凸性不意味着「好算」：求 $\theta(\boldsymbol{\lambda})$ 本身可能需解一个（一般非凸的）内层极小化。

### 弱对偶

对任意**原问题可行** $\boldsymbol{x}$ 与任意满足 $\lambda_i\ge0\ (i\in\mathcal{I})$ 的 $\boldsymbol{\lambda}$，有

$$
\mathcal{L}(\boldsymbol{x},\boldsymbol{\lambda})
:= f(\boldsymbol{x}) - \underbrace{\sum_{i\in\mathcal{E}}\lambda_ic_i(\boldsymbol{x})}_{=0}
+ \underbrace{\sum_{i\in\mathcal{I}}\lambda_ic_i(\boldsymbol{x})}_{\le 0}
\;\le\; f(\boldsymbol{x}).
$$

故 $\theta(\boldsymbol{\lambda})\le f(\boldsymbol{x})$。对一切可行 $\boldsymbol{x}$ 取最小，得到**弱对偶 (weak duality)**：

$$
d^* \le p^*
$$

最小化原问题时，对偶最优值 $d^*$ 是原问题最优值 $p^*$ 的一个**下界**。一般非凸问题中，这个下界往往不紧。

**对偶间隙 (duality gap)** 定义为

$$
\mathrm{gap} := p^* - d^* \;\ge\; 0.
$$

若 $\mathrm{gap}=0$，即 $p^*=d^*$，称**强对偶 (strong duality)** 成立：原问题与对偶问题最优值一致。此时求解原问题等价于寻找使间隙为零的 $(\boldsymbol{x}^*,\boldsymbol{\lambda}^*)$；



### Slater 条件

**Slater 条件**：存在可行点 $\boldsymbol{\tilde{x}}$ 使 $c_i(\boldsymbol{\tilde{x}})=0\ (i\in\mathcal{E})$，且 $c_i(\boldsymbol{\tilde{x}})>0\ (i\in\mathcal{I})$（不等式严格成立）。仿射不等式可放宽为 $c_i(\boldsymbol{\tilde{x}})\ge 0$。直观：可行域在不等式意义下有相对内部；椭圆内、多边形内等通常易验证。

凸 + Slater 时，强对偶成立，且 KKT 条件也成为最优性的**充分**条件——那一步的代数形式见《KKT 条件与约束品性》。





## 附录：

### 经济学视角：$d^*$ 是「可证明的最优成本下界」

在资源约束优化里，可把原问题读作**生产者问题**：

$$
p^* = \min\;\text{成本（或损失）} f(\boldsymbol{x})
\quad\text{s.t.}\quad
\text{资源/技术约束 } c_i=0\ (i\in\mathcal{E}),\ c_i\ge 0\ (i\in\mathcal{I}).
$$

- **$\boldsymbol{x}$**：生产方案（投入、参数、映射坐标等）；
- **$c_i(\boldsymbol{x})\ge 0$**：第 $i$ 种资源的下限或规范（面积、能量、容量）；
- **$p^*$**：在约束下能实现的**最低可行成本**。

**对偶问题**换一个提问方式：不直接找最优方案，而是问——「若允许对违反约束施加**线性惩罚**（由 $\lambda_i\ge 0$ 定价），再让生产者自由选 $\boldsymbol{x}$ 使 Lagrangian 最小，惩罚定价 $\boldsymbol{\lambda}$ 最多能把成本**压到多低**？」

$$
d^* = \max_{\lambda_i\ge 0}
\;
\underbrace{\inf_{\boldsymbol{x}}\bigl(f(\boldsymbol{x})-\sum_i\lambda_ic_i(\boldsymbol{x})\bigr)}_{\text{给定价格后，生产者的最优反应}}.
$$

- **$\lambda_i$**：第 $i$ 条约束的**影子价格 (shadow price)**——约束每放松一单位，最优成本可下降多少（见后文互补松弛）；
- **$\theta(\boldsymbol{\lambda})$**：在价格 $\boldsymbol{\lambda}$ 下，生产者按 $\min_{\boldsymbol{x}}\mathcal{L}$ 反应后的**最低广义成本**；
- **$d^*$**：所有合理定价 $\lambda_i\ge 0$ 中，这个下界的**最大值**。

因此 $d^*\le p^*$ 有清晰的经济含义：

> **无论你怎么给约束标定惩罚价，按 Lagrangian 自由优化后得到的成本下界，都不可能超过真正受约束时的最优成本 $p^*$。**

- 若 $d^*<p^*$：**对偶间隙**表示「仅靠线性惩罚无法完全替代硬约束」——惩罚定价再精明，生产者的最优反应仍比真约束下更乐观，下界偏松。
- 若 $d^*=p^*$（强对偶）：存在价格 $\boldsymbol{\lambda}^*$，使「软约束 + 该定价」与「硬约束」给出相同最优值；$\lambda_i^*$ 即约束 $i$ 的**边际价值**——紧约束处 $\lambda_i^*>0$，松弛约束处 $\lambda_i^*=0$（多一单位资源已不值钱）。

**小例子（单资源）**：$\min x$ s.t. $x\ge 2$，写成 N&W 形式即 $c(x)=x-2\ge0$。真约束下 $p^*=2$。若用惩罚代替约束，$\mathcal{L}=x-\lambda(x-2)=(1-\lambda)x+2\lambda$：$\lambda\ne 1$ 时生产者可沿下降方向取 $x\to\pm\infty$ 使 $\mathcal{L}\to -\infty$，$\lambda= 1$ 时 $\mathcal{L}\equiv 2$。故 $d^*=\max_{\lambda\ge 0}\inf_x \mathcal{L}=2=p^*$：价格 $\lambda^*=1$ 恰为「每多生产一单位 $x$ 所增加的边际成本」，与约束的边际价值一致。

**与 LP 单纯形法**：最优表最后一行的**检验数**即对偶变量；它们既是 KKT 乘子，也是资源的影子价格——这是 $d^*\le p^*$ 在运筹学里每天被「算出来」的版本。





## 鞍点视角——为何 $d^*\le p^*$

本附录用「鞍点」解释弱对偶，并给出 $d^*\le p^*$ 的代数与几何两种读法。凸问题下 KKT 的充分性由同一套鞍点语言给出，见《KKT 条件与约束品性》附录。

把 Lagrangian 看成 $\boldsymbol{x}$ 与 $\boldsymbol{\lambda}$ 的**双变量函数**。原问题与对偶问题可写成两个**极值–极值**问题：

$$
\boxed{
p^* = \min_{\boldsymbol{x}\in\mathcal{F}}
\;\max_{\lambda_i\ge 0,\,i\in\mathcal{I}}\;
\mathcal{L}(\boldsymbol{x},\boldsymbol{\lambda})
}
\tag{P}
$$

$$
\boxed{
d^* = \max_{\lambda_i\ge 0,\,i\in\mathcal{I}}
\;\min_{\boldsymbol{x}\in\mathbb{R}^n}\;
\mathcal{L}(\boldsymbol{x},\boldsymbol{\lambda})
}
\tag{D}
$$

这里 $\mathcal{F}=\{\boldsymbol{x}: c_i=0\ (i\in\mathcal{E}),\ c_i\ge 0\ (i\in\mathcal{I})\}$ 为原可行域。对任意函数 $\mathcal{L}$，**minimax 不等式**恒成立：

$$
\max_{\lambda_i\ge 0}
\min_{\boldsymbol{x}}
\mathcal{L}(\boldsymbol{x},\boldsymbol{\lambda})
\;\le\;
\min_{\boldsymbol{x}\in\mathcal{F}}
\max_{\lambda_i\ge 0}
\mathcal{L}(\boldsymbol{x},\boldsymbol{\lambda}),
$$

即 $d^*\le p^*$。证明只需一行交换逻辑：设 $\boldsymbol{\lambda}$ 为对偶最优，$\boldsymbol{x}$ 为原可行，则

$$
d^* = \min_{\boldsymbol{x}'} \mathcal{L}(\boldsymbol{x}',\boldsymbol{\lambda})
\le \mathcal{L}(\boldsymbol{x},\boldsymbol{\lambda})
\le f(\boldsymbol{x}) \;\Rightarrow\; d^*\le p^*.
$$

**鞍点** $(\boldsymbol{x}^*,\boldsymbol{\lambda}^*)$ 满足：固定乘子时 $\mathcal{L}$ 对 $\boldsymbol{x}$ 极小，固定 $\boldsymbol{x}^*$ 时对乘子极大——即同时实现 (P) 与 (D) 的等号。此时

$$
\mathcal{L}(\boldsymbol{x}^*,\boldsymbol{\lambda}^*)
= p^* = d^*,
$$

**强对偶**等价于 Lagrangian 在最优处存在鞍点。凸 + Slater 保证这种鞍点存在；非凸问题则可能出现「内层 $\min_{\boldsymbol{x}}$ 与外层 $\max$ 换序」后值不相等，留下正的对偶间隙。

**几何直观（$n=1$，单不等式）**：想象 $\mathcal{L}(x,\lambda)$ 为曲面。原问题先在每个 $x$ 上对 $\lambda\ge 0$ 取**上包络**（惩罚违反约束），再对 $x$ 取最小——得到 $p^*$。对偶问题先对每个 $\lambda$ 在 $x$ 上取**下包络**，再对 $\lambda$ 取最大——得到 $d^*$。下包络的最高点不可能超过上包络的最低点，故 $d^*\le p^*$。

| 操作顺序 | 含义 | 结果 |
| :--- | :--- | :--- |
| $\min_x \max_\lambda \mathcal{L}$ | 先对每个位置选最狠惩罚，再选最优位置 | $p^*$（原问题） |
| $\max_\lambda \min_x \mathcal{L}$ | 先对每个惩罚系数找最省成本的 $x$，再选最有利的系数 | $d^*$（对偶问题） |
| 鞍点 | 两种顺序得到同一值 | $p^*=d^*$（强对偶） |