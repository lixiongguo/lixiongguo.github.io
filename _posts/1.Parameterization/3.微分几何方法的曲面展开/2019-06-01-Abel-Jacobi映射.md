---
layout: post
category: Parameterization
categories: ["Parameterization", "Parameterization-QuadRemeshing"]
title: "Abel-Jacobi映射"
---

顾险峰老师的计算共形理论将四边形网格化从"工程技巧"提升为可判定的数学问题。将曲面视为**黎曼曲面**，通过复分析工具实现全局参数化。**任何一个四边形网格都可以诱导出一个共形结构（conformal structure）**：

- 四边形网格的每个面可以映射为单位正方形 $[0,1] \times [0,1]$，面与面之间的转移函数是平移 + 旋转 $90^\circ$ 的整数倍
- 这种转移函数自然是全纯（复解析）的——因为平移和旋转都是共形变换
- 因此，四边形网格的图册（atlas）本身就是一个共形图册，曲面被赋予了共形结构

<img src="https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20260530062135832.png" alt="image-20260530062135832" style="zoom: 67%;" />

反过来，**给定一个共形结构，是否总能找到一个"好"的四边形网格？**答案是否定的——这是一个受全局拓扑约束的问题。

> 本文只陈述结论。Riemann-Roch、双线性关系、Abel 定理与 Jacobi 反演的完整证明（含逐步逻辑节点与两条证明路线对照）见《[Abel-Jacobi 与 Riemann-Roch 的证明]({% post_url 1.Parameterization/3.微分几何方法的曲面展开/2019-06-02-Abel-Jacobi与Riemann-Roch定理证明 %})》。

##### Poincaré–Hopf 定理（一般形式）

设 $V$ 为曲面 $M$ 上的光滑向量场，$p$ 为孤立奇点，$I(p)$ 为奇点指数（绕奇点一圈向量转过的圈数除以 $2\pi$），则：

$$
\sum_{p \in \text{奇点}} I(p) = \chi(M)
$$

##### 四边形网格的特化

对四边形网格引导场（cross field），价数为 $k$ 的顶点指数为 $I(v) = 1 - k/4$。设价数为 $k$ 的顶点数量为 $n_k$，代入得：

- 奇异点指数之和必须等于曲面的欧拉示性数：

$$
\sum_{k \neq 4} (4 - k) \, n_k = 4\chi(M)
$$

这是 **Poincaré-Hopf 定理** 的直接推论——四边形网格的指数可以定义为 $I(v) = 1 - k/4$。

理想四边形网格在普通 4-价顶点附近曲率为零，曲率集中在 extraordinary vertex 上。若顶点价数为 $n$，局部锥角为
$$
\Theta_v = n \cdot \frac{\pi}{2},  K_v = 2\pi - \Theta_v = \left(4 - n\right)\frac{\pi}{2}.
$$

这正是 Poincaré-Hopf 指数 $I(v) = 1 - n/4$ 的几何含义——奇异点 index 以 $\frac{1}{4}$ 为单位，来自 $2\pi$ 与 $\frac{\pi}{2}$ 对称性的比例关系。

然而Poincaré-Hopf 只是**必要条件**，不是充分条件。从共形结构到四边形网格 需要额外满足 **Abel 约束**。



## 除子与 Riemann-Roch 定理

紧黎曼面上不能存在非常数全纯函数（Liouville 定理），因此要研究**亚纯**对象——允许孤立零极点的函数与微分形式。除子（divisor）统一记录这些零极点的位置与阶数。

### 亚纯函数的除子

设 $f$ 为紧黎曼面 $S$ 上的亚纯函数。在点 $p$ 处用局部坐标 $z$，写 $f(z)=(z-p)^k u(z)$，$u(p)\neq 0$，则**阶数** $\operatorname{ord}_p(f)=k$：
- $k>0$：$k$ 阶零点；
- $k<0$：$|k|$ 阶极点；
- $k=0$：正则且非零。

**除子**（divisor）是形式线性组合

$$
(f)=\operatorname{div}(f)=\sum_{p\in S}\operatorname{ord}_p(f)\,p,
$$

亦可写为 $(f)=\sum_i m_i P_i-\sum_j n_j Q_j$（零点减极点）。主除子（principal divisor）总度数恒为零：

$$
\deg(f)=\sum_p \operatorname{ord}_p(f)=0.
$$

### 亚纯微分形式的除子

除子不仅属于函数，也属于**亚纯微分形式**。设 $\omega$ 为 $S$ 上的亚纯 $k$-形式（$k\ge 1$）。在局部坐标 $z$ 下写成

$$
\omega = f(z)\,(dz)^k,
$$

其中 $f$ 为亚纯函数，定义

$$
\operatorname{ord}_p(\omega):=\operatorname{ord}_p(f),
\qquad
(\omega)=\operatorname{div}(\omega)=\sum_{p\in S}\operatorname{ord}_p(\omega)\,p.
$$

**与函数除子的关系**：$k=0$ 时 $\omega$ 就是亚纯函数，定义一致。$k\ge 1$ 时 $\omega$ 在坐标变换 $z\mapsto w$ 下按 $(dz)^k=(w'(z)\,dz)^k$ 变换，但 $\operatorname{ord}_p(\omega)$ 与坐标选取无关——零极点阶数是不变量。

**直观**：在 $p$ 附近，$|\omega|$ 的行为像 $|z-p|^{\operatorname{ord}_p(\omega)}$；$\operatorname{ord}_p(\omega)>0$ 为零点，$<0$ 为极点。对 $k$-形式，零点/极点阶数按 $k$ 次幂体现在「体积元」$(dz)^k$ 的缩放中。

**典范除子 $K$**：取一个**非零全纯** $1$-形式 $\omega_0$（紧曲面亏格 $g\ge 1$ 时存在），其除子

$$
K:=(\omega_0)=\sum_p \operatorname{ord}_p(\omega_0)\,p
$$

称为**典范除子**；$\omega_0$ 无极点，故 $K$ 仅含零点，且 $\deg K=2g-2$。任意两个非零全纯 $1$-形式相差一个非零常数，除子相同，故 $K$ 由曲面共形结构唯一确定。

对亚纯 $k$-形式，若 $\omega=\omega_0^k$（$k$ 次幂）则 $(\omega)=k\,K$；一般亚纯 $k$-形式的除子度数满足 $\deg(\omega)=k(2g-2)$（在允许极点时，零点度数之和减极点度数之和）。

**主除子与线性等价**（微分形式视角）：亚纯函数 $h$ 诱导 $k$-形式 $h\,\omega_0^k$，其除子

$$
(h\,\omega_0^k)=(h)+kK.
$$

两个除子 $D,D'$ **线性等价**（记 $D\sim D'$），若 $D-D'=(h)$ 对某个亚纯函数 $h$。对 $k$-形式而言，给定目标除子 $D$，「是否存在亚纯 $k$-形式 $\omega$ 使 $(\omega)=D$」等价于「$D$ 是否与 $kK$ 线性等价」，即 $D-kK$ 是否为主除子——这一判定由 **Abel 定理** 给出；Riemann-Roch 管的是另一件事：在 $(\omega)\ge D$ 的宽松要求下解空间有几维。

### 四边形网格与亚纯四次微分的除子

设 $D_Q$ 为奇异点除子：价数为 $k$ 的顶点 $v$ 对应点 $p_v$，系数

$$
d_v = k-4
$$

（$5$-价为 $+1$ 零点，$3$-价为 $-1$ 极点），即 $D_Q=\sum_v d_v\,p_v$。四边形网格的存在性（在共形结构已定的前提下）与下述问题等价：**是否存在亚纯四次微分** $\omega$（即 $(dz)^4$，$K^4$ 的截面）使得

$$
(\omega)=D_Q .
$$

局部上，每个面视为单位正方形、取 $dz_f$；面与边、边与正则顶点之间的转移只差因子 $e^{\mathbf i n\pi/2}$（$n\in\mathbb Z$），故 $(dz)^4$ 在正则处全局拼接。在价数为 $k$ 的锥奇异点，局部坐标与等距展开 $w_v$ 的关系为

$$
z_v=w_v^{4/k},
$$

代入得 $\left(\tfrac{k}{4}\right)^4 z_v^{\,k-4}(dz_v)^4=\omega$，故 $\operatorname{ord}_v(\omega)=k-4$：**$3$-价为一阶极点，$5$-价为一阶零点**。

Gauss–Bonnet / Poincaré–Hopf 与除子度数是**同一件事**（用 $E=2F$ 与 $V-E+F=\chi$）：

$$
\deg D_Q=\sum_v (k_v-4)=2E-4V=-4\chi(M)=8g-8=\deg(4K),
$$

也就是说，四边形网格的除子度数自动等于四次微分的典范度数——**度数平衡是恒等式，不构成额外约束**。真正的约束来自 Abel 条件（见后文）；Riemann-Roch 回答的是另一个问题：给定极点上界时这样的微分有多少个，即 $\ell(4K-D_Q)$ 的维数。

### Riemann-Roch

对除子 $D$，令

$$
L(D)=\{\,f\in\mathcal M(S)\ :\ (f)+D\ge 0\,\}\cup\{0\},
\qquad
\ell(D)=\dim_{\mathbb C}L(D),
$$

即"极点上界由 $D$ 控制"的亚纯函数空间。Riemann-Roch：

$$
\ell(D) - \ell(K - D) = \deg(D) + 1 - g,
$$

其中 $K=(\omega_0)$ 为典范除子（某非零全纯 $1$-形式的除子），$g$ 为亏格；对偶项 $\ell(K-D)$ 来自 Serre 对偶 $H^1(D)\cong L(K-D)^{*}$。$k$-形式版本把 $K$ 换成 $kK$：$\ell(kK-D)>0$ 当且仅当存在亚纯 $k$-形式 $\omega$ 使 $(\omega)\ge D$（"至少满足"），其自由度即 $\ell(kK-D)$；若要**恰好** $(\omega)=D$，则须 $D\sim kK$，这一步的判定交给 Abel 定理。




## Abel定理与Abel-Jacobian映射

### 周期矩阵与 Jacobi 簇

设 $\{\zeta_1, \dots, \zeta_g\}$ 为全纯 1-形式的基，定义 $A$ 周期矩阵和 $B$ 周期矩阵：

$$
\mathbf{A}_{ij} = \int_{a_i} \zeta_j,
\mathbf{B}_{ij} = \int_{b_i} \zeta_j, i,j = 1,\dots,g
$$

周期矩阵（Riemann 矩阵）：

$$
\Pi = \mathbf{A}^{-1} \mathbf{B} \in \mathbb{C}^{g \times g}
$$

$\Pi$ 满足 Riemann 双线性关系：对称且 $\operatorname{Im}(\Pi) > 0$（正定）。

格 $\Gamma$ 由列向量生成：

$$
\Gamma = \{\mathbf{A} m + \mathbf{B} n \mid m, n \in \mathbb{Z}^g\}
$$

**Jacobi 簇**：$J(S) = \mathbb{C}^g / \Gamma$ 是 $g$ 维复环面。

四边形网格无缝化要求周期为整数：

$$
\int_{a_i} \zeta_j \in \mathbb{Z} + i\mathbb{Z},
\int_{b_i} \zeta_j \in \mathbb{Z} + i\mathbb{Z}
$$



在 $2g$ 个同调基底 $\{a_1, \ldots, a_g, b_1, \ldots, b_g\}$ 上对 1-form 积分，得到 $2g$ 个周期向量：

$$
\text{Period}(a_i) = \int_{a_i} \omega \in \mathbb{C}^g, \quad
\text{Period}(b_i) = \int_{b_i} \omega \in \mathbb{C}^g
$$

这些周期组成了曲面的**周期矩阵（Period Matrix）**。要让接缝两侧的参数坐标完美拼接，所有周期必须是**整数**（或至少是高斯整数 $\mathbb{Z} + i\mathbb{Z}$）。周期矩阵的整数化是四边形网格化的核心困难——它既是一个优化问题（如 MIQ 的混合整数规划），也有着深刻的复几何解释（周期矩阵的列张成了 $\mathbb{C}^g$ 中的格点 $\Gamma$）。

另外，设 $\{\varphi_1, \cdots, \varphi_g\}$ 为 $\Omega^1$（$\mathbb{C}$ 上全纯微分构成的线性空间）的正规基（canonical basis），满足

$$
\int_{a_i} \varphi_j = \delta_{ij}, \quad i, j = 1, \cdots, g,
$$

其中 $\delta_{ij}$ 为 Kronecker 符号。

对于每一条闭曲线 $\gamma$，沿 $\gamma$ 对各个全纯微分基积分，得到 $\mathbb{C}^g$ 中的向量

$$
\lambda_\gamma = \left(\int_{\gamma} \varphi_1, \cdots, \int_{\gamma} \varphi_g\right).
$$

$\mathbb{C}^g$ 中的 $g$ 维复格点 $\Gamma$ 定义为

$$
\Gamma = \left\{ \sum_{k=1}^g (s_k \lambda_{a_k} + t_k \lambda_{b_k}) : s_k, t_k \in \mathbb{Z} \right\}.
$$

雅可比簇 **Jacobian Variety $J(S)$** 定义在黎曼面 $S$ 上，是紧商空间

$$
J(S) = \mathbb{C}^g / \Gamma.
$$

### Abel–Jacobi 映射

**Abel–Jacobi 映射**是将**几何对象**（点、除子、代数圈）转化为**复环面上的点**的桥梁。以某个固定基点 $p_0 \in S$ 为原点，Abel-Jacobian 映射 $\mu : S \to J(S)$ 定义为：对任意 $p \in S$

$$
\mu(p) = \left( \int_{p_0}^p \varphi_1, \dots, \int_{p_0}^p \varphi_g \right) \pmod \Gamma,
$$

其中积分沿任意路径进行。

对除子 $D = \sum_i d_i p_i$，Abel-Jacobi 映射为

$$
\mu(D) = \sum_i d_i \,\mu(p_i).
$$

亚纯函数除子 $(f)$ 通过 Abel-Jacobian 映射后满足 **Abel-Jacobi 定理**：

$$
\mu((f)) = \sum_{p \in S} \nu_p(f) \mu(p) = 0.
$$

**Abel 定理**（19世纪）：除子 $D$ 是主除子（某个亚纯函数的零极点除子）当且仅当

$$
\deg D = 0 \quad\text{且}\quad \mu(D)\equiv 0 \pmod{\Gamma}.
$$

**$\deg D=0$ 这个前提不能省**——主除子度数恒为零。因此对四边形网格不能直接判定 $\mu(D_Q)$（$\deg D_Q=8g-8\neq 0$），须先减去四次微分的典范部分，得到 **Abel–Jacobi 条件**：

$$
\mu\big(D_Q-4(\omega_0)\big)\equiv 0 \pmod{\Gamma}.
$$

反方向（存在性）由 Abel 定理的逆定理给出：该条件成立 $\Rightarrow$ 存在亚纯函数 $f$ 使 $(f)=D_Q-4(\omega_0)$，取

$$
\omega=f\,\omega_0^{\,4},
$$

则 $(\omega)=(f)+4(\omega_0)=D_Q$，即得以 $D_Q$ 为除子的亚纯四次微分；若其轨道有限，就切出四边形网格。（三角网格同理，把 $4$ 换成 $6$，见下例。）

### 示例

环面上不存在 5,7-三角化，即不存在恰有两个异常顶点、价数分别为 5 和 7 的三角化。

![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20260605111848155.png)

证明思路：将 5,7-三角化 $\mathcal{T}$ 的每个面视为欧氏等边三角形，可构造共形结构 $\mathcal{A}$。在面 $f$、边 $e$、顶点 $v$ 上分别取局部坐标 $z_f, z_e, z_v$；对价数为 $k$ 的奇异顶点，局部坐标与等距嵌入 $w_v$ 的关系为

$$
z_v = w_v^{\frac{6}{k}}.
$$

面、边与正则顶点之间的转移映射的旋转分量为 $e^{i \frac{n\pi}{3}}$（$n \in \mathbb{Z}$）的形式。在局部坐标上定义全纯微分

$$
\omega = (dz_f)^6 = (dz_e)^6 = (dz_v)^6.
$$

$\omega$ 全局良定义，但在奇异顶点处需延拓。由上式得

$$
dw_v = \frac{k}{6} (z_v)^{\frac{k-6}{6}} dz_v, 
(dw_v)^6 = \left(\frac{k}{6}\right)^6 (z_v)^{k-6} (dz_v)^6.
$$

因此 $\omega=(dz)^6$ 是全局亚纯 $6$-形式，其除子 $(\omega)$ 在 $5$-价顶点 $q$ 为 $-1$ 阶极点、$7$-价顶点 $p$ 为 $+1$ 阶零点（因 $k-6$：$5\mapsto -1$，$7\mapsto +1$）。

取典范全纯 $1$-形式 $\omega_0$（$(\omega_0)=K$，无额外极点），构造亚纯函数

$$
f = \frac{\omega}{(\omega_0)^6},  (f) = (\omega) - 6(\omega_0) = p - q.
$$

由 Abel-Jacobi 定理，

$$
\mu((f)) = \mu(p) - \mu(q) = \int_{p_0}^p \omega_0 - \int_{p_0}^q \omega_0 = 0.
$$

这意味着在基本域内 $p$ 与 $q$ 必须重合，与 $p \neq q$ 矛盾。故环面上不存在 5,7-三角化。$\square$

该论证可以推广：对任意亏格，若奇异点除子 $D$ 不可解（$\mu\big(D-4(\omega_0)\big)\not\equiv 0 \pmod{\Gamma}$），则不存在以这些点为奇异点的四边形网格——即使 Poincaré-Hopf（度数）与 Riemann-Roch（维数）都已满足。

一个给定拓扑的曲面能否被四边形网格化？能——当且仅当存在一组满足 **Poincaré-Hopf + Abel-Jacobi** 条件的奇异点配置、其对应的亚纯 $n$-形式（四边形网格为四次微分 $(dz)^4$，三角网格为六次微分 $(dz)^6$）轨道有限，且它的所有周期可以同时整数化。