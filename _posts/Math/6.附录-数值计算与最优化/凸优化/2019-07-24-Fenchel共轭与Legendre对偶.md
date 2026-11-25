---
layout: post
title: "Fenchel 共轭与 Legendre 对偶"
category: Parameterization
categories: ["Parameterization", "Parameterization-Appendix"]
mathjax: true
---

**凸共轭**（Fenchel 共轭）与它的特例 **Legendre 变换**，以及由它导出的 Fenchel 对偶、Moreau 分解与包络恒等式，是下面要处理的对象。

## 1. 定义

设 $f:\mathbb{R}^n\to\mathbb{R}\cup\{+\infty\}$ 不恒为 $+\infty$。其**凸共轭**（Fenchel 共轭）为

$$
f^*(\boldsymbol{y}):=\sup_{\boldsymbol{x}\in\mathbb{R}^n}\Bigl\{\langle\boldsymbol{x},\boldsymbol{y}\rangle-f(\boldsymbol{x})\Bigr\}.
$$

要点三条：

- $f^*$ 恒为**闭凸**函数（一族仿射函数 $\boldsymbol{y}\mapsto\langle\boldsymbol{x},\boldsymbol{y}\rangle-f(\boldsymbol{x})$ 的逐点上确界），与 $f$ 是否凸无关；
- $f$ 可以取 $+\infty$（用于编码约束），此时 $\sup$ 只在 $\operatorname{dom}f$ 上取；
- 记 $f^{**}:=(f^*)^*$，则恒有 $f^{**}\le f$，且 **Fenchel–Moreau 定理**给出 $f^{**}=f$ 当且仅当 $f$ 闭且凸。

## 2. Fenchel–Young 不等式

对任意 $\boldsymbol{x},\boldsymbol{y}$，

$$
f(\boldsymbol{x})+f^*(\boldsymbol{y})\ \ge\ \langle\boldsymbol{x},\boldsymbol{y}\rangle,
$$

且**等号成立当且仅当** $\boldsymbol{y}\in\partial f(\boldsymbol{x})$（$f$ 可微时即 $\boldsymbol{y}=\nabla f(\boldsymbol{x})$）。

这条不等式是整个对偶理论的起点：它把「$f$ 的上境图」与「$f^*$ 的上境图」用一张双曲抛物面隔开，两侧相切的位置就是次梯度。由它立刻得到

$$
f(\boldsymbol{x})=\sup_{\boldsymbol{y}}\Bigl\{\langle\boldsymbol{x},\boldsymbol{y}\rangle-f^*(\boldsymbol{y})\Bigr\}
=f^{**}(\boldsymbol{x}),
$$

即「$f$ 是其共轭的共轭」——闭凸函数可以由它的支撑超平面完全描述。

## 3. Legendre 对偶：共轭的古典形式

当 $f$ **严格凸、可微**且 $\nabla f$ 是 $\mathbb{R}^n\to\mathbb{R}^n$ 的双射时，$f^*$ 的 $\sup$ 由一阶条件唯一确定：

$$
\boldsymbol{y}=\nabla f(\boldsymbol{x})
\quad\Longrightarrow\quad
f^*(\boldsymbol{y})=\langle\nabla f^{-1}(\boldsymbol{y}),\boldsymbol{y}\rangle-f\bigl(\nabla f^{-1}(\boldsymbol{y})\bigr),
\qquad
\nabla f^*=(\nabla f)^{-1}.
$$

这就是经典的 **Legendre 变换**（也写作 $f^*(\boldsymbol{p})=\boldsymbol{p}\cdot\boldsymbol{x}-f(\boldsymbol{x})$，$\boldsymbol{p}=\nabla f$）。它只要求光滑严格凸，不要求 $f$ 有界或无约束以外的结构；一旦 $\nabla f$ 不满足满射（例如定义域有界、函数非光滑），Legendre 形式失效，必须回到 $\sup$ 定义——**这是凸共轭相对 Legendre 变换的推广之处**。

**例（二次型）**：$f(\boldsymbol{x})=\tfrac12\boldsymbol{x}^T\boldsymbol{Q}\boldsymbol{x}+\boldsymbol{b}^T\boldsymbol{x}+c$，$\boldsymbol{Q}\succ0$。由 $\boldsymbol{y}=\boldsymbol{Q}\boldsymbol{x}+\boldsymbol{b}$ 得 $\boldsymbol{x}=\boldsymbol{Q}^{-1}(\boldsymbol{y}-\boldsymbol{b})$，故

$$
f^*(\boldsymbol{y})=\tfrac12(\boldsymbol{y}-\boldsymbol{b})^T\boldsymbol{Q}^{-1}(\boldsymbol{y}-\boldsymbol{b})-c .
$$

特别地 $f=\tfrac12\lVert\cdot\rVert^2$ 时 $f^*=\tfrac12\lVert\cdot\rVert^2$（自共轭）。

## 4. 常见函数的共轭

| $f(\boldsymbol{x})$ | $f^*(\boldsymbol{y})$ | 备注 |
| :--- | :--- | :--- |
| $\tfrac12\lVert \boldsymbol{x}\rVert_2^2$ | $\tfrac12\lVert \boldsymbol{y}\rVert_2^2$ | 自共轭 |
| $\tfrac12\boldsymbol{x}^T\boldsymbol{Q}\boldsymbol{x}$，$\boldsymbol{Q}\succ0$ | $\tfrac12\boldsymbol{y}^T\boldsymbol{Q}^{-1}\boldsymbol{y}$ | Legendre |
| $\lVert \boldsymbol{x}\rVert$（任意范数） | $I_{B_*}(\boldsymbol{y})$，$B_*=\{\lVert \boldsymbol{y}\rVert_*\le1\}$ | 共轭 = 对偶单位球的指示函数 |
| $\lVert \boldsymbol{x}\rVert_1$ | $I_{\{\lVert \boldsymbol{y}\rVert_\infty\le1\}}$ | 软阈值/投影对偶的根据 |
| $\lVert \boldsymbol{x}\rVert_2$ | $I_{\{\lVert \boldsymbol{y}\rVert_2\le1\}}$ | |
| $I_C(\boldsymbol{x})$（$C$ 凸） | $\sigma_C(\boldsymbol{y})=\sup_{\boldsymbol{x}\in C}\langle\boldsymbol{x},\boldsymbol{y}\rangle$ | 指示函数 ↔ 支撑函数 |
| $\sigma_C(\boldsymbol{x})$ | $I_C(\boldsymbol{y})$ | 自反 |
| $-\log x$（$x>0$） | $-1-\log(-y)$（$y<0$） | 障碍项的共轭 |
| $e^{x}$ | $y\log y-y$（$y>0$） | 指数族的标准例 |
| $I_{\{\boldsymbol{A}\boldsymbol{x}=\boldsymbol{b}\}}$ | $\langle\boldsymbol{A}^{-T}\boldsymbol{b},\boldsymbol{y}\rangle$（在 $\boldsymbol{A}^T$ 的像上） | 等式约束的对偶化 |

从表里可以读出两条通用规律：**指示函数与支撑函数互为共轭**，**范数与对偶单位球的指示函数互为共轭**。近端算法里"软阈值 = 原向量减去投影""约束的对偶变量落在某个支撑函数的 prox 里"这些现象，都源自这两条。

## 5. Fenchel 对偶

共轭最重要的用途是把复合问题对偶化。考虑

$$
p^*:=\min_{\boldsymbol{x}}\ \bigl\{f(\boldsymbol{x})+g(\boldsymbol{A}\boldsymbol{x})\bigr\},
\qquad
d^*:=\max_{\boldsymbol{y}}\ \bigl\{-f^*(-\boldsymbol{A}^T\boldsymbol{y})-g^*(\boldsymbol{y})\bigr\}.
$$

**推导**：由 Fenchel–Young，对任意 $\boldsymbol{y}$ 有 $g(\boldsymbol{A}\boldsymbol{x})\ge\langle\boldsymbol{A}\boldsymbol{x},\boldsymbol{y}\rangle-g^*(\boldsymbol{y})$，代入目标得

$$
f(\boldsymbol{x})+g(\boldsymbol{A}\boldsymbol{x})
\ \ge\ f(\boldsymbol{x})+\langle\boldsymbol{x},\boldsymbol{A}^T\boldsymbol{y}\rangle-g^*(\boldsymbol{y}),
$$

对 $\boldsymbol{x}$ 取下确界即得 $d^*\le p^*$；再对 $\boldsymbol{y}$ 取上确界即 (弱) Fenchel 对偶。若 $f,g$ 闭凸且存在满足 $\boldsymbol{A}\operatorname{ri}(\operatorname{dom}f)\cap\operatorname{ri}(\operatorname{dom}g)\neq\varnothing$ 的约束品性，则**强对偶** $p^*=d^*$。

**与 Lagrangian 对偶的关系**：取 $g=I_{\{\boldsymbol{b}\}}$（只允许 $\boldsymbol{A}\boldsymbol{x}=\boldsymbol{b}$），则 $g^*(\boldsymbol{y})=\langle\boldsymbol{b},\boldsymbol{y}\rangle$，上面对偶即

$$
d^*=\max_{\boldsymbol{y}}\Bigl\{-f^*(-\boldsymbol{A}^T\boldsymbol{y})-\langle\boldsymbol{b},\boldsymbol{y}\rangle\Bigr\}
=\max_{\boldsymbol{y}}\ \inf_{\boldsymbol{x}}\Bigl\{f(\boldsymbol{x})-\langle\boldsymbol{y},\boldsymbol{A}\boldsymbol{x}-\boldsymbol{b}\rangle\Bigr\},
$$

这正是对偶函数 $\theta(\boldsymbol{y}):=\inf_{\boldsymbol{x}}\mathcal{L}(\boldsymbol{x},\boldsymbol{y})$ 的共轭写法：**对偶函数就是「$f$ 的共轭在 $-\boldsymbol{A}^T\boldsymbol{y}$ 处取值」**。线性约束下这套推导没有约束曲率项，比一般非线性 KKT 干净得多。

## 6. 与近端算子、投影的关系

### 6.1 Moreau 分解

$\operatorname{prox}$ 与共轭函数 $g^*$ 之间有一条恒等式，它同时解释三件事：软阈值为什么是「原向量减去投影」、$\operatorname{prox}$ 与投影的对偶关系、以及怎么算共轭函数的 prox。

**定理（Moreau 分解）**：对任意 $\boldsymbol{v}$ 与 $\gamma>0$，

$$
\boldsymbol{v}=\operatorname{prox}_{\gamma g}(\boldsymbol{v})+\gamma\,\operatorname{prox}_{\gamma^{-1}g^{*}}\!\Bigl(\frac{\boldsymbol{v}}{\gamma}\Bigr),
$$

即 $\operatorname{prox}_{\gamma g}(\boldsymbol{v})=\boldsymbol{v}-\gamma\,\operatorname{prox}_{\gamma^{-1}g^*}(\boldsymbol{v}/\gamma)$，其中 $g^*(\boldsymbol{y})=\sup_{\boldsymbol{x}}\{\langle\boldsymbol{x},\boldsymbol{y}\rangle-g(\boldsymbol{x})\}$。

**证明**：用 $\frac{1}{2\gamma}\lVert \boldsymbol{x}-\boldsymbol{v}\rVert^2=\sup_{\boldsymbol{y}}\{\langle\boldsymbol{x}-\boldsymbol{v},\boldsymbol{y}\rangle-\frac{\gamma}{2}\lVert \boldsymbol{y}\rVert^2\}$ 与 Fenchel 对偶（凸–凹的极小极大可交换）：

$$
\begin{aligned}
\min_{\boldsymbol{x}}\Bigl\{g(\boldsymbol{x})+\frac{1}{2\gamma}\lVert \boldsymbol{x}-\boldsymbol{v}\rVert^2\Bigr\}
&=\min_{\boldsymbol{x}}\sup_{\boldsymbol{y}}\Bigl\{g(\boldsymbol{x})+\langle\boldsymbol{x},\boldsymbol{y}\rangle-\langle\boldsymbol{v},\boldsymbol{y}\rangle-\frac{\gamma}{2}\lVert \boldsymbol{y}\rVert^2\Bigr\}\\
&=\sup_{\boldsymbol{y}}\Bigl\{-g^*(-\boldsymbol{y})-\langle\boldsymbol{v},\boldsymbol{y}\rangle-\frac{\gamma}{2}\lVert \boldsymbol{y}\rVert^2\Bigr\}.
\end{aligned}
$$

令 $\boldsymbol{z}=-\boldsymbol{y}$，内层是

$$
\arg\min_{\boldsymbol{z}}\Bigl\{g^*(\boldsymbol{z})+\frac{\gamma}{2}\Bigl\lVert \boldsymbol{z}-\frac{\boldsymbol{v}}{\gamma}\Bigr\rVert^2\Bigr\}
=\operatorname{prox}_{\gamma^{-1}g^*}\Bigl(\frac{\boldsymbol{v}}{\gamma}\Bigr)=:\boldsymbol{z}^{*} .
$$

原问题与对偶的最优点由内层 $\sup$ 的驻点条件联系：$\boldsymbol{y}=(\boldsymbol{x}-\boldsymbol{v})/\gamma$，故 $\boldsymbol{z}^{*}=(\boldsymbol{v}-\boldsymbol{x}^{*})/\gamma$，即 $\boldsymbol{x}^{*}=\boldsymbol{v}-\gamma\boldsymbol{z}^{*}$，证毕。

### 6.2 三个特例

**特例 1：软阈值 = 减去投影。** 取 $\gamma=1$、$g=\lVert \cdot\rVert_1$，则 $g^*=I_{\{\lVert \boldsymbol{y}\rVert_\infty\le1\}}$，$\operatorname{prox}_{I_{B_\infty}}=\Pi_{B_\infty}$（逐坐标截断到 $[-1,1]$）：

$$
\boldsymbol{v}=S_{1}(\boldsymbol{v})+\Pi_{B_\infty}(\boldsymbol{v}).
$$

即**硬阈值（保留大幅值坐标）= 原向量减去软阈值结果**。三维数值例：$\boldsymbol{v}=(3,\,-1,\,0.5)$，

$$
S_1(\boldsymbol{v})=(2,0,0),\qquad \Pi_{B_\infty}(\boldsymbol{v})=(1,-1,0.5),\qquad (2,0,0)+(1,-1,0.5)=(3,-1,0.5).
$$

**特例 2：包络的共轭恒等式。** 由上面的对偶表达式也可读出

$$
e_{\gamma g}(\boldsymbol{v})+e_{\gamma^{-1}g^*}\!\Bigl(\frac{\boldsymbol{v}}{\gamma}\Bigr)=\frac{\lVert \boldsymbol{v}\rVert^2}{2\gamma},
$$

其中 $e_{\gamma g}$ 是 Moreau 包络。以 $\boldsymbol{v}=(3,-1,0.5)$、$\gamma=1$、$g=\lVert \cdot\rVert_1$ 验证（逐坐标，$\boldsymbol{p}=S_1(\boldsymbol{v})=(2,0,0)$）：$e_g(\boldsymbol{v})=\bigl(2+\frac12\cdot1^2\bigr)+\bigl(0+\frac12\cdot1^2\bigr)+\bigl(0+\frac12\cdot0.5^2\bigr)=3.125$；$g^*=I_{B_\infty}$，$e_{g^*}(\boldsymbol{v})=\frac12\bigl[(1-3)^2+(-1+1)^2+(0.5-0.5)^2\bigr]=2$。两者和为 $5.125=\lVert \boldsymbol{v}\rVert^2/2$。

**特例 3：支撑函数的 prox。** 取 $g=I_C$、$\gamma=1$，则 $g^*=\sigma_C$（$C$ 的支撑函数），Moreau 分解读作

$$
\Pi_C(\boldsymbol{v})+\operatorname{prox}_{\sigma_C}(\boldsymbol{v})=\boldsymbol{v}.
$$

对偶问题里的对偶变量常常正好落在「某个凸集的支撑函数」的 prox 里，这时它只需要一次投影：$\operatorname{prox}_{\sigma_C}(\boldsymbol{v})=\boldsymbol{v}-\Pi_C(\boldsymbol{v})$。

**用法**：需要 $\operatorname{prox}_{g^*}$ 却只有 $\operatorname{prox}_g$ 的闭式解时（或反过来），用 Moreau 分解在两者之间转换；$\gamma$ 也可以吸收进 $g$ 的尺度。这是对偶算法里最常见的恒等式。

### 6.3 平滑的对偶表述

Moreau 包络

$$
e_{\gamma g}(\boldsymbol{v}):=\min_{\boldsymbol{x}}\Bigl\{g(\boldsymbol{x})+\frac{1}{2\gamma}\lVert \boldsymbol{x}-\boldsymbol{v}\rVert^2\Bigr\}
$$

满足 $\nabla e_{\gamma g}(\boldsymbol{v})=\bigl(\boldsymbol{v}-\operatorname{prox}_{\gamma g}(\boldsymbol{v})\bigr)/\gamma$，且梯度 $(1/\gamma)$-Lipschitz。它的共轭有闭式：

$$
\bigl(e_{\gamma g}\bigr)^*(\boldsymbol{y})=g^*(\boldsymbol{y})+\frac{\gamma}{2}\lVert \boldsymbol{y}\rVert^2,
$$

即**对原函数做 Moreau 平滑，等价于对共轭做二次正则**。

### 6.4 例：增广拉格朗日 = 对偶侧的 Moreau 平滑

等式约束问题 $\min f(\boldsymbol{x})$ s.t. $\boldsymbol{A}\boldsymbol{x}=\boldsymbol{b}$ 的对偶函数

$$
\theta(\boldsymbol{\lambda})=\inf_{\boldsymbol{x}}\bigl\{f(\boldsymbol{x})-\boldsymbol{\lambda}^T(\boldsymbol{A}\boldsymbol{x}-\boldsymbol{b})\bigr\}
$$

未必可微：$\inf$ 与微分不可交换时，$\theta$ 在 $\boldsymbol{\lambda}^{*}$ 附近可能只有次梯度，更谈不上梯度 Lipschitz。修补方式是给目标加二次罚项，而这件事在对偶侧可以精确说出来。记 $\boldsymbol{c}=\boldsymbol{A}\boldsymbol{x}-\boldsymbol{b}$，对任意 $\boldsymbol{\lambda}$：

$$
-\boldsymbol{\lambda}^T\boldsymbol{c}+\frac{\mu}{2}\lVert \boldsymbol{c}\rVert_2^2
=\max_{\boldsymbol{\nu}}\Bigl\{-\boldsymbol{\nu}^T\boldsymbol{c}-\frac{1}{2\mu}\lVert \boldsymbol{\nu}-\boldsymbol{\lambda}\rVert_2^2\Bigr\},
\qquad\text{极大点}\ \ \boldsymbol{\nu}=\boldsymbol{\lambda}-\mu\boldsymbol{c}.
$$

右端是「线性项 + 以 $\boldsymbol{\lambda}$ 为锚点的二次回拉」，极大点正是增广拉格朗日内层驻点的有效乘子。代回 $\inf_{\boldsymbol{x}}$ 并交换 $\inf$ 与 $\max$（凸–凹，Slater 下成立）：

$$
\theta_\mu(\boldsymbol{\lambda}):=\inf_{\boldsymbol{x}}\Bigl\{f(\boldsymbol{x})-\boldsymbol{\lambda}^T\boldsymbol{c}+\frac{\mu}{2}\lVert \boldsymbol{c}\rVert_2^2\Bigr\}
=\max_{\boldsymbol{\nu}}\Bigl\{\theta(\boldsymbol{\nu})-\frac{1}{2\mu}\lVert \boldsymbol{\nu}-\boldsymbol{\lambda}\rVert_2^2\Bigr\}
=-e_{\mu^{-1}(-\theta)}(\boldsymbol{\lambda}),
$$

末式即 §6.3 的凸包络换成凹函数（$\theta$ 凹，故 $-\theta$ 凸），平滑参数为 $\mu$。

于是罚项的作用一目了然：**它在对偶侧给 $\theta$ 加一个以当前 $\boldsymbol{\lambda}$ 为锚点的二次正则**；原侧与之对应的是 $\mu\boldsymbol{A}^T\boldsymbol{A}$ 带来的强凸化。三条结论随之而来：

- **极大值不变**：$\max\theta_\mu=\max\theta$，极大点同为 $\boldsymbol{\lambda}^{*}$。加罚项不改变对偶最优值，只把不可微的 $\theta$ 换成光滑的 $\theta_\mu$。
- **梯度有闭式**：由包络的梯度公式，$\nabla\theta_\mu(\boldsymbol{\lambda})=-\bigl(\boldsymbol{A}\boldsymbol{x}^{*}(\boldsymbol{\lambda})-\boldsymbol{b}\bigr)$，$\boldsymbol{x}^{*}$ 为内层解；$\nabla\theta_\mu$ 是 $(1/\mu)$-Lipschitz 的。
- **乘子步就是在 $\theta_\mu$ 上爬**：乘子步 $\boldsymbol{\lambda}^{k+1}=\boldsymbol{\lambda}^{k}-\mu(\boldsymbol{A}\boldsymbol{x}^{k+1}-\boldsymbol{b})$ 可写成

$$
\boldsymbol{\lambda}^{k+1}=\boldsymbol{\lambda}^{k}+\mu\,\nabla\theta_\mu\bigl(\boldsymbol{\lambda}^{k}\bigr),
$$

即固定步长 $\mu$ 的梯度上升，作用在光滑后的 $\theta_\mu$ 上。$1/\mu$ 恰是梯度 Lipschitz 常数，步长正好取在稳定界 $1/L$ 上——这就是乘子步不需要线搜索、也没有可调超参数的原因。

再由极大点与梯度的关系 $\boldsymbol{\nu}^{*}(\boldsymbol{\lambda})=\boldsymbol{\lambda}+\mu\nabla\theta_\mu(\boldsymbol{\lambda})$、$\nabla\theta_\mu(\boldsymbol{\lambda})=\nabla\theta(\boldsymbol{\nu}^{*})$，乘子步等价于

$$
\boldsymbol{\lambda}^{k+1}=\arg\max_{\boldsymbol{\lambda}}\Bigl\{\theta(\boldsymbol{\lambda})-\frac{1}{2\mu}\bigl\lVert \boldsymbol{\lambda}-\boldsymbol{\lambda}^{k}\bigr\rVert_2^2\Bigr\},
$$

即**对偶函数上的邻近点法**：每步不追 $\theta$ 的精确极大点，而追「加上回拉二次项后」的极大点，回拉系数是 $1/\mu$。

与二次罚函数对照，差别只在**回拉的锚点**：罚函数把 $\boldsymbol{\lambda}$ 拉向 $\boldsymbol{0}$（对 $\boldsymbol{\lambda}$ 本身做二次正则，消去后得 $f+\frac{\mu}{2}\lVert\boldsymbol{c}\rVert_2^2$，乘子只能隐式表达为 $-\mu\boldsymbol{c}$），增广拉格朗日把 $\boldsymbol{\lambda}$ 拉向 $\boldsymbol{\lambda}^{k}$（只对偏差做正则，乘子保持显式）。

**一维验证**：$\min\frac12x^2$ s.t. $x-1=0$ 时 $\theta(\lambda)=-\frac12\lambda^2+\lambda$。增广拉格朗日的内层条件 $\partial_x\bigl[\frac12x^2-\lambda(x-1)+\frac{\mu}{2}(x-1)^2\bigr]=0$ 给出 $x=(\mu+\lambda)/(1+\mu)$、$c=x-1=(\lambda-1)/(1+\mu)$，故

$$
\lambda^{+}=\lambda-\mu c=\frac{\lambda+\mu}{1+\mu};
$$

邻近点法的一阶条件 $1-\lambda-\dfrac{\lambda-\lambda^{k}}{\mu}=0$ 给出

$$
\lambda^{+}=\frac{\lambda^{k}+\mu}{1+\mu}.
$$

两式相同，故 $1/\mu$ 同时是回拉系数与邻近项系数。
