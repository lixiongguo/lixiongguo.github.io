---
layout: post
category: Parameterization
categories: ["Parameterization", "Parameterization-QuadRemeshing"]
title: "Abel-Jacobi 与 Riemann-Roch 的证明"
---

## 2. Riemann-Roch 公式（定理 3.3.1）

### 2.1 陈述

> **定理 3.3.1 (Riemann-Roch 公式).** 设 $M$ 为紧致黎曼曲面，其亏格为 $g$。则对任何因子 $D$，有
> $$
> \dim l(D)=\dim i(D)+(1-g)+d(D).
> $$
> 这里的维数都是指复维数。

> **根据 Hodge 定理的推论, 曲面 $M$ 上总存在典范因子, 因此 Riemann-Roch 公式也可以改写为**
> $$
> \dim l(D)-\dim l(K-D)=d(D)+(1-g).
> $$

### 2.2 预备：奇异积分

> **首先作一些准备工作. 设 $\omega$ 为紧致黎曼曲面 $M$ 上的亚纯微分, 我们假设 $\omega$ 的所有留数均为零. 设 $p_1,p_2,\cdots,p_k$ 为 $\omega$ 的所有极点, 在 $p_i$ 附近取局部坐标邻域 $B_i$, 使得当 $i\neq j$ 时 $B_i\cap B_j=\varnothing$. 由于**
> $$
> \int_{\partial B_i}\omega=2\pi\sqrt{-1}\,\mathrm{Res}_{p_i}(\omega)=0,
> $$
> **$\omega$ 在 $B_i-\{p_i\}$ 内为恰当形式, 即存在 $B_i-\{p_i\}$ 内的光滑函数 $g_i$, 使得 $\omega=dg_i$. 通过使用光滑截断函数以及零延拓, 在 $M-\{p_1,p_2,\cdots,p_k\}$ 上就得到光滑函数 $g$, 使得在每个 $p_i$ 附近均有 $\omega=dg$. 此时 $\omega-dg$ 可以看成 $M$ 上的光滑微分形式. 任给 $M$ 上闭形式 $\eta$, 定义奇异积分 $\int_M\omega\wedge\eta$ 为**
> $$
> \int_M\omega\wedge\eta=\int_M(\omega-dg)\wedge\eta.
> $$

> **奇异积分具有下列性质:**
> - **奇异积分的定义是恰当的.**（……若另有 $g'$，则 $g-g'=c_i$ 于 $p_i$ 附近，于是两个积分之差为 $\int_M d(g'-g)\wedge\eta=\sum_i c_i\int_{\partial B_i}\eta=0$。）
> - **当 $\eta$ 为恰当形式时, 奇异积分 $\int_M\omega\wedge\eta=0$.** 事实上，若 $\eta=df$，则
> $$
> \int_M\omega\wedge\eta=\int_M(\omega-dg)\wedge df=-\int_M d\left(f(\omega-dg)\right)=0,
> $$
> 上式最后用到了 Stokes 积分公式.
> - **$\omega=dg,\ g\in\mathcal M(M)\iff\int_M\omega\wedge\eta=0,\ \forall$ 闭形式 $\eta$.**

### 2.3 引理 3.3.2：规范化亚纯微分

> **引理 3.3.2.** 设 $M$ 为紧致黎曼曲面, $n\ge 1$ 为正整数. 任取 $p\in M$, $B$ 为 $p$ 附近的坐标邻域, $z$ 为 $B$ 上的坐标函数, $z(p)=0$. 则存在 $M$ 上的亚纯微分 $\omega$, 使得 $\omega$ 以 $p$ 为惟一极点, 且在 $p$ 附近有
> $$
> \omega=d\left(\frac{1}{z^n}\right)+\omega_h,
> $$
> 其中 $\omega_h$ 是 $p$ 附近的全纯微分, 并且奇异积分
> $$
> \int_M\omega\wedge\bar\phi_i=0,\qquad i=1,2,\cdots,g,
> $$
> 其中 $\{\phi_1,\phi_2,\cdots,\phi_g\}$ 是前节最后定义的 $H$ 的一组基.

> **证明.** 根据前节推论 3.2.5, 存在亚纯微分 $\omega_1$, 满足除奇异积分为零以外的所有条件. 根据前节最后的一段说明, 映射
> $$
> \phi:H\to\mathbb C^g,\qquad \varphi\mapsto\left(\int_M\varphi\wedge\bar\phi_1,\ \int_M\varphi\wedge\bar\phi_2,\ \cdots,\ \int_M\varphi\wedge\bar\phi_g\right)
> $$
> 是线性同构, 因此存在全纯微分 $\varphi$, 使得 $\int_M\varphi\wedge\bar\phi_i=\int_M\omega_1\wedge\bar\phi_i$，$i=1,2,\cdots,g$. 令 $\omega=\omega_1-\varphi$, 则 $\omega$ 为满足引理要求的亚纯微分. $\square$

> **注.** 不难看出, 上述引理中的亚纯微分 $\omega$ 是惟一的.

### 2.4 空间 $m(D)$ 与引理 3.3.3

> **现在, 我们假设 $D=\sum_{i=1}^{m}n_i\cdot p_i$ 为紧致黎曼曲面 $M$ 上的一个有效因子, $n_i>0$, $i=1,2,\cdots,m$. 根据刚才的引理, 存在 $M$ 上的亚纯微分 $\tau^1_{p_i},\tau^2_{p_i},\cdots,\tau^{n_i}_{p_i}$, $1\le i\le m$, 使得在 $p_i$ 附近的坐标邻域 $B_i$ 内, $\tau^k_{p_i}=d\left(\frac{1}{z^k}\right)+\eta^k_i$, 其中 $\eta^k_i$ 为 $B_i$ 内的全纯微分, 且 $\int_M\tau^k_{p_i}\wedge\bar\phi_j=0$, $\forall j=1,2,\cdots,g$, $1\le k\le n_i$. 显然, $\{\tau^1_{p_i},\tau^2_{p_i},\cdots,\tau^{n_i}_{p_i}\}_{i=1}^{m}$ 是 $M$ 上线性无关的亚纯微分, 记它们张成的复向量空间为 $m(D)$, 则**
> $$
> \dim m(D)=\sum_{i=1}^{m}n_i=d(D).
> $$

> **引理 3.3.3.** 设 $D$ 是如上所述的因子, $m(D)$ 如上定义. 则
> (i) $\forall f\in l(D)$, $df\in m(D)$;
> (ii) 设 $\tau\in m(D)$, 则 $\tau=df,\ f\in l(D)\iff\int_M\tau\wedge\phi_i=0,\ i=1,2,\cdots,g$.

> **证明.** (i) 设 $D=\sum_{i=1}^{m}n_i\cdot p_i$, $f\in l(D)$, 则 $\nu_{p_i}(f)+n_i\ge 0$, $i=1,2,\cdots,m$. 根据 $\tau^k_{p_i}$ 的构造, 存在 $\lambda^k_i\in\mathbb C$, 使得 $df-\sum_{i,k}\lambda^k_i\tau^k_{p_i}$ 是 $M$ 上无极点的亚纯微分, 即 $df-\sum_{i,k}\lambda^k_i\tau^k_{p_i}\in H$. 又因为
> $$
> \int_M\left(df-\sum_{i,k}\lambda^k_i\tau^k_{p_i}\right)\wedge\bar\phi_j=0,\qquad j=1,2,\cdots,g,
> $$
> 故 $df-\sum_{i,k}\lambda^k_i\tau^k_{p_i}=0$, 即 $df\in\mathrm{span}\{\tau^k_{p_i}\}=m(D)$.
>
> (ii) 「$\Rightarrow$」的部分在定义奇异积分时已经说明过. 下面设 $\tau\in m(D)$, 且 $\int_M\tau\wedge\phi_i=0$, $i=1,2,\cdots,g$. 于是 $\int_M\tau\wedge\phi=0$, $\forall\phi\in H^1$. 根据奇异积分的几个性质, 存在亚纯函数 $f$, 使得 $\tau=df$. 由 $m(D)$ 的定义容易看出, $f\in l(D)$. $\square$

> **根据这个引理我们知道, 外微分算子 $d$ 诱导了线性映射 $d:l(D)\to m(D)$, 并且它的像 $d(l(D))$ 在 $m(D)$ 中满足 $g$ 个线性约束条件, 因此**
> $$
> \dim d(l(D))\ge \dim m(D)-g.
> $$
> **显然, $\mathrm{Ker}\,d=\mathbb C$, 从而有**
> $$
> \dim l(D)=\dim\mathrm{Ker}\,d+\dim\mathrm{Im}\,d\ge 1+d(D)-g.
> $$
> **这是 Riemann 所获得的不等式, 它给出了 $\dim l(D)$ 的一个下界估计.**

### 2.5 引理 3.3.4：两个互为转置的算子

> **为了得到进一步的 Riemann-Roch 公式, 我们必须决定 $\mathrm{Im}\,d$ 的维数. 为此, 设 $\{\tau^1_{p_i},\cdots,\tau^{n_i}_{p_i}\}_{i=1}^{m}$ 是 $m(D)$ 的如上构造的基. 任取 $\phi\in H$, 我们来计算 $\int_M\tau^k_{p_i}\wedge\phi$.**（……在 $p_i$ 附近取坐标 $z$，$z(p_i)=0$，存在 $M-\{p_i\}$ 上的光滑函数 $g$，使 $g=\frac{1}{z^k}+f$、$\tau^k_{p_i}=dg$，于是）
> $$
> \int_M\tau^k_{p_i}\wedge\phi=\int_M(\tau^k_{p_i}-dg)\wedge\phi=\int_{M-B_i}(\tau^k_{p_i}-dg)\wedge\phi=-\int_{M-B_i}dg\wedge\phi=\int_{\partial B_i}g\phi=\int_{\partial B_i}\frac{1}{z^k}\phi.
> $$
> **如果在 $B_i$ 内 $\phi$ 有局部展开 $\phi=\left(\sum_j a^j_i z^j\right)dz$, 则由上式得**
> $$
> \int_M\tau^k_{p_i}\wedge\phi=2\pi\sqrt{-1}\cdot a^{k-1}_i,\qquad k=1,2,\cdots,n_i.
> $$

> **定义线性算子**
> $$
> S:m(D)\to H,\qquad \tau\mapsto\frac{1}{2\pi\sqrt{-1}}\sum_{j=1}^{g}\left(\int_M\tau\wedge\phi_j\right)\cdot\phi_j,
> $$
> **以及**
> $$
> T:H\to m(D),\qquad \phi\mapsto\sum_{i=1}^{m}\sum_{k=1}^{n_i}a_{i,k-1}\cdot\tau^k_{p_i},
> $$
> **其中, $a_{i,k}$ 是 $\phi$ 在 $p_i$ 的坐标邻域 $B_i$ 中展开的系数: $\phi=\left(\sum_k a_{i,k}z^k\right)dz$.**

> **引理 3.3.4.** 设线性映射 $S,T$ 定义如上, 则
> (i) $\mathrm{Ker}\,S=\mathrm{Im}\,d$;
> (ii) $\mathrm{Ker}\,T=i(D)$;
> (iii) $\dim\mathrm{Im}\,S=\dim\mathrm{Im}\,T$.

> **证明.** (i) $\tau\in\mathrm{Ker}\,S\iff\int_M\tau\wedge\phi_j=0$, $j=1,2,\cdots,g\iff\tau\in\mathrm{Im}\,d$.
>
> (ii) 回忆 $i(D)$ 的定义: $i(D)=\{\omega\mid(\omega)-D\ge 0\}$. 因此, $\omega\in i(D)\iff\omega\in H$, 且如果在 $p_i$ 附近 $\omega=\left(\sum_k a_{i,k}z^k\right)dz$, 则 $a_{i,k}=0$, $k\le n_i-1$. $\iff\omega\in\mathrm{Ker}\,T$.
>
> (iii) 我们在 $m(D)$ 的基 $\{\tau^k_{p_i}\}$ 和 $H$ 的基 $\{\phi_j\}$ 下分别计算线性算子 $S,T$ 的矩阵表示. 在 $B_i$ 内, $\phi_j$ 有局部展开 $\phi_j=\left(\sum_k a_{i,jk}z^k\right)dz$. 因此有
> $$
> S(\tau^k_{p_i})=\frac{1}{2\pi\sqrt{-1}}\sum_{j=1}^{g}\left(\int_M\tau^k_{p_i}\wedge\phi_j\right)\phi_j=\sum_{j=1}^{g}a_{i,j(k-1)}\phi_j,
> $$
> $$
> T(\phi_j)=\sum_{i=1}^{m}\sum_{k=1}^{n_i}a_{i,j(k-1)}\tau^k_{p_i}.
> $$
> 从而在这两组基下, 线性映射 $S,T$ 的矩阵互为转置, 特别地, $\dim\mathrm{Im}\,S=\dim\mathrm{Im}\,T$. $\square$

### 2.6 定理 3.3.1 的证明

> **有了上面这些准备, 我们现在可以给出 Riemann-Roch 公式的证明了. 分几种情况考虑.**

**情形 (1)：$D$ 为有效因子.**

> **如果 $D=0$, 则显然 $l(D)=\mathbb C$, $i(D)=H$, 从而 $\dim l(D)=1=\dim i(D)+(1-g)+d(D)$.**
>
> **如果 $D\ge 0$, 且 $d(D)>0$, 则由刚才的引理, 有**
> $$
> \begin{aligned}
> \dim l(D)&=\dim\mathrm{Ker}\,d+\dim\mathrm{Im}\,d\\
> &=1+\dim\mathrm{Ker}\,S\\
> &=1+\left(\dim m(D)-\dim\mathrm{Im}\,S\right)\\
> &=1+d(D)-\dim\mathrm{Im}\,T\\
> &=1+d(D)-\left(\dim H-\dim\mathrm{Ker}\,T\right)\\
> &=1+d(D)-\left(g-\dim i(D)\right)\\
> &=\dim i(D)+d(D)+(1-g).
> \end{aligned}
> $$
> **这说明 Riemann-Roch 公式对有效因子成立.**

**情形 (2)：$K-D$ 为有效因子.**

> **这时, 由 (1), 有**
> $$
> \dim l(K-D)=\dim i(K-D)+d(K-D)+(1-g).
> $$
> **用 $\dim l(K-D)=\dim i(D)$、$\dim i(K-D)=\dim l(D)$ 以及 $d(K)=2g-2$ 代入上式即得**
> $$
> \dim l(D)=\dim i(D)+d(D)+(1-g).
> $$

**情形 (3)：一般因子.**

> **最后, 设 $D$ 是 $M$ 上的一个一般的因子. 如果 $l(D)\neq\{0\}$, 则存在 $f_0\in l(D)$, 使得 $(f_0)+D\ge 0$. 令 $D_0=(f_0)+D$, 则 $D_0$ 为有效因子, 从而 Riemann-Roch 公式对 $D_0$ 成立, 因此 Riemann-Roch 公式对因子 $D$ 也成立;**
>
> **如果 $i(D)\neq\{0\}$, 则存在 $\omega_0\in i(D)$, 使得 $(\omega_0)-D\ge 0$. 令 $D_1=(\omega_0)-D$, 则 $D_1$ 为有效因子, 根据 (2), Riemann-Roch 公式对因子 $D$ 也成立;**
>
> **最后我们假设 $l(D)=i(D)=\{0\}$, 我们要证明此时必有 $d(D)=g-1$. 事实上, 把 $D$ 写成 $D=D_1-D_2$, 其中 $D_1,D_2$ 为有效因子, $D_1,D_2$ 无公共点. 根据本章第一节的习题, 有**
> $$
> \dim l(D_1)\le\dim l(D_1-D_2)+d(D_2)=d(D_2),
> $$
> **对有效因子 $D_1$ 用 Riemann-Roch 公式, 有**
> $$
> d(D_2)\ge\dim i(D_1)+d(D_1)+(1-g)\ge d(D_1)+(1-g),
> $$
> **这就得到下面的估计**
> $$
> d(D)=d(D_1)-d(D_2)\le g-1.
> $$
> **另一方面, 对于因子 $K-D$ 也有这个估计, 即 $d(K-D)\le g-1$, 从而**
> $$
> d(D)\ge d(K)-(g-1)=2g-2-(g-1)=g-1.
> $$
> **这说明 $d(D)=g-1$, 因而 Riemann-Roch 公式对 $D$ 也成立. $\square$**

### 2.7 推论 3.3.5 与定理 3.4.2

> **推论 3.3.5.** 设 $K$ 为 $M$ 上的典范因子, 则 $d(K)=2g-2$. 特别地, 亏格为 $1$ 的曲面上存在处处非零的全纯微分.

> **证明.** 如果 $g=0$, 则 $M$ 与黎曼球面 $S$ 同构 (习题). 取 $\omega=dz$, $z$ 为 $\mathbb C$ 上的复坐标. 则 $K=(\omega)=-2\infty$, 因此 $d(K)=-2=2g-2$.
>
> 如果 $g\ge 1$, 则存在非零全纯微分 $\omega\in H$. 此时 $K=(\omega)\ge 0$. 并且
> $$
> l(K)\cong i(0)=H,\qquad i(K)\cong l(0)=\mathbb C.
> $$
> 因此有
> $$
> g=\dim H=\dim l(K)=\dim i(K)+d(K)+(1-g)=1+d(K)+(1-g).
> $$
> **这说明 $d(K)=2g-2$. $\square$**

> **定理 3.4.2.** 设 $M$ 为紧致黎曼曲面, $D$ 为 $M$ 上的因子. 则
> (i) 当 $d(D)\ge 2g-1$ 时, $\dim l(D)=d(D)+(1-g)$;
> (ii) 当 $d(D)=g+n,\ n>0$ 时, $\dim l(D)\ge 1+n$；$g=0$ 时等号成立.

> **证明.** (i) 当 $d(D)\ge 2g-1$ 时, $d(K-D)=d(K)-d(D)=2g-2-d(D)<0$, 从而 $i(D)\cong l(K-D)=\{0\}$. 由 Riemann-Roch 公式, $\dim l(D)=\dim i(D)+d(D)+(1-g)=d(D)+(1-g)$.
>
> (ii) 当 $d(D)=g+n$, $n>0$ 时, 由 Riemann-Roch 公式, $\dim l(D)=\dim i(D)+d(D)+(1-g)\ge d(D)+(1-g)=g+n+(1-g)=1+n$. 当 $g=0$ 时, 由 (i) 知 $\dim l(D)=d(D)+(1-g)=1+n$. $\square$

## 3. 双线性关系（定理 3.5.4）

### 3.1 相交数与基本多边形

> **设 $\gamma,\tau$ 为 $M$ 上两条闭曲线, 若它们只交于有限个横截点, 则**
> $$
> \int_\sigma\omega_\tau
> $$
> **总是整数, 称为这两条曲线 $\sigma$ 和 $\tau$ 的相交数.**（……）**亏格为 $g$ 的闭曲面上总存在绕过给定点的 $2g$ 条闭曲线 $\sigma_1,\sigma_2,\cdots,\sigma_{2g}$, 使得这些闭曲线交于一个公共点, 且它们之间的相交数满足: $\sigma_i$ 与 $\sigma_{g+i}$ 的相交数为 $1$, $\sigma_{g+i}$ 与 $\sigma_i$ 的相交数为 $-1$, 其它的相交数均为 $0$.**

> **命题 3.5.1.** 设 $\omega$ 为黎曼曲面 $M$ 上的闭 $1$-形式, 如果对任意闭曲线 $\sigma$, 均有 $\int_\sigma\omega=0$, 则 $\omega$ 为恰当形式.

> **证明.** 固定 $p_0\in M$, 定义函数 $f:M\to\mathbb C$ 如下: $f(p)=\int_{\sigma_{p_0p}}\omega$, 其中 $\sigma_{p_0p}$ 是连接 $p$ 和 $p_0$ 的曲线. 由于 $\omega$ 在闭曲线上的积分为零, 因此 $f$ 的定义与连接 $p$ 和 $p_0$ 的曲线的选取无关. 显然有 $df=\omega$. $\square$

> **命题 3.5.2.** 设 $\sigma$ 为紧致黎曼曲面 $M$ 上的闭曲线, 则存在惟一的调和 $1$-形式 $\omega_\sigma$, 使得对于任意闭的 $1$-形式 $\eta$, 均有
> $$
> \int_\sigma\eta=\int_M\omega_\sigma\wedge\eta.
> $$

### 3.2 定理 3.5.4

> **定理 3.5.4 (双线性关系).** 设 $\eta$ 为 $M$ 上具有单极点 $\{p_1,p_2,\cdots,p_k\}$ 的亚纯微分, $\omega$ 为 $M$ 上的全纯微分. 如上选取 $2g$ 条不经过这些极点的闭曲线 $\{\sigma_i\}$, 记
> $$
> \Pi_i=\int_{\sigma_i}\omega,\qquad N_i=\int_{\sigma_i}\eta,\qquad i=1,2,\cdots,2g.
> $$
> **则有**
> $$
> \sum_{i=1}^{g}\left(\Pi_iN_{g+i}-\Pi_{g+i}N_i\right)=2\pi\sqrt{-1}\sum_{j=1}^{k}\mathrm{Res}_{p_j}(\eta)\int_{p_0}^{p_j}\omega,
> $$
> **其中, $p_0$ 是单连通区域 $M_0=M-\{\sigma_1,\cdots,\sigma_{2g}\}$ 中的一点, $\int_{p_0}^{p_j}\omega$ 表示 $\omega$ 沿着连接 $p_0$ 与 $p_j$ 且落在区域 $M_0$ 中的曲线上的积分.**

### 3.3 证明

> **证明. 定义映射 $I:M_0\to\mathbb C$ 为**
> $$
> I(p)=\int_{p_0}^{p}\omega,
> $$
> **则 $I$ 是定义好的光滑函数, 且在 $M_0$ 上有 $dI=\omega$.**

> **根据留数定理的证明, 我们有**
> $$
> \int_{\partial M_0}I\eta=2\pi\sqrt{-1}\sum_{j=1}^{k}\mathrm{Res}_{p_j}(I\eta)=2\pi\sqrt{-1}\sum_{j=1}^{k}\mathrm{Res}_{p_j}(\eta)\int_{p_0}^{p_j}\omega \tag{3.6}
> $$

> **另一方面, 我们也可在 $P$ 上计算如下**
> $$
> \int_{\sigma_i}I\eta+\int_{\sigma_i'}I\eta=\int_{\sigma_i}\left(I(z)-I(z')\right)\eta,
> $$
> **其中, 如果 $z$ 表示 $\sigma_i$ 上的点, 则用 $z'$ 表示 $\sigma_i^{-1}$ 上对应的点.**

> **另一方面, 由 $\omega$ 为闭形式得**
> $$
> I(z)-I(z')=-\int_{\sigma_{g+i}}\omega=-\Pi_{g+i},
> $$
> **从而有**
> $$
> \int_{\sigma_i}I\eta+\int_{\sigma_i'}I\eta=-\Pi_{g+i}\int_{\sigma_i}\eta=-\Pi_{g+i}N_i.
> $$

> **同理可得**
> $$
> \int_{\sigma_{g+i}}I\eta+\int_{\sigma_{g+i}'}I\eta=\Pi_iN_{g+i}.
> $$

> **这两个等式结合起来就推出**
> $$
> \int_{\partial M_0}=\sum_{i=1}^{g}\left(\Pi_iN_{g+i}-\Pi_{g+i}N_i\right) \tag{3.7}
> $$
> **由 (3.6) 及 (3.7) 就得到了欲证结果. $\square$**

### 3.4 一般形式的双线性关系

> **从上述定理的证明过程中我们实际上可以得到下面的等式**
> $$
> \int_M\omega\wedge\eta=\sum_{i=1}^{g}\left[\int_{\sigma_i}\omega\int_{\sigma_{g+i}}\eta-\int_{\sigma_{g+i}}\omega\int_{\sigma_i}\eta\right],
> $$
> **其中 $\omega,\eta$ 为任意光滑的闭 $1$-形式. 这也称为双线性关系.**

## 4. Abel 定理（定理 3.5.9）

### 4.1 典则基与周期矩阵

> **命题 3.5.5.** 设 $\{\sigma_i\}$ 如上. 如果 $\omega$ 为全纯微分, 且 $\int_{\sigma_i}\omega=0$, $i=1,\cdots,g$, 则 $\omega$ 恒为零.

> **证明.** 由已知条件, 我们也有 $\int_{\sigma_i}\bar\omega=0$, $i=1,\cdots,g$. 从而由双线性关系得
> $$
> \lVert\omega\rVert^2=\int_M\omega\wedge*\bar\omega=\sqrt{-1}\int_M\omega\wedge\bar\omega=0,
> $$
> 因此 $\omega=0$. $\square$

> **推论 3.5.6.** 存在 $H$ 的一组基 $\{\omega_i\}_{i=1}^{g}$, 使得
> $$
> \int_{\sigma_i}\omega_j=\delta_{ij},\qquad 1\le i,j\le g.
> $$

> **证明.** 设 $\{\omega'_i\}$（$i=1,\cdots,g$）为 $H$ 的一组基. 我们断言 $g$ 阶方阵 $\left(\int_{\sigma_i}\omega'_j\right)_{g\times g}$ 是非退化的. 事实上, 设 $c_j\in\mathbb C$, 使得 $\sum_{j=1}^{g}c_j\int_{\sigma_i}\omega'_j=0$, $i=1,\cdots,g$, 则
> $$
> \int_{\sigma_i}\left(\sum_{j=1}^{g}c_j\omega'_j\right)=0,\qquad i=1,\cdots,g.
> $$
> 这说明 $\sum_{j=1}^{g}c_j\omega'_j=0$, 从而 $c_j=0$, $j=1,\cdots,g$. 现在对基 $\{\omega'_i\}$ 做适当的线性变换就可得到所需要的新的基. $\square$

> **我们把满足引理条件的基 $\{\omega_i\}$ 称为 $H$ 的一组典则基. 记**
> $$
> Z=\left(\int_{\sigma_{g+i}}\omega_j\right)_{g\times g},
> $$
> **则有**

> **命题 3.5.7.** $Z$ 为 $g$ 阶对称方阵, 且其实部是正定对称的.

> **证明.** 根据双线性关系, 我们有
> $$
> 0=\int_M\omega_i\wedge\omega_j=\sum_{k=1}^{g}\left[\delta_{ki}\int_{\sigma_{g+k}}\omega_j-\delta_{kj}\int_{\sigma_{g+k}}\omega_i\right]=\int_{\sigma_{g+i}}\omega_j-\int_{\sigma_{g+j}}\omega_i.
> $$
> 这说明 $Z$ 是对称矩阵. 同理,
> $$
> \int_M\omega_i\wedge\bar\omega_j=-\sqrt{-1}\,\mathrm{Im}\left(\int_{\sigma_{g+i}}\omega_j\right).
> $$
> 因此, 当 $c_i\in\mathbb R$ 时, 令 $\omega=\sum_{i=1}^{g}c_i\omega_i$, 则
> $$
> 0\le\lVert\omega\rVert^2=\sqrt{-1}\int_M\omega\wedge\bar\omega=\sqrt{-1}\sum_{j,k=1}^{g}c_jc_k\int_M\omega_j\wedge\bar\omega_k=\sum_{j,k=1}^{g}\mathrm{Im}\left(\int_{\sigma_{g+j}}\omega_k\right)c_jc_k.
> $$
> 这说明 $\mathrm{Im}\,Z$ 为正定矩阵. $\square$

### 4.2 对偶调和形式与 Jacobi 簇

> **命题 3.5.8.** 设 $\{\sigma_i\}$ 如前. 记 $\omega_{\sigma_i}$ 为闭曲线 $\sigma_i$ 的对偶调和形式. 则
> (1) $\{\omega_{\sigma_i}\}$ 是 $M$ 上调和 $1$-形式空间 $H^1$ 的一组基;
> (2) 如果 $\sigma$ 为闭曲线, 则其对偶形式可表示为
> $$
> \omega_\sigma=\sum_{i=1}^{g}\left(n_{g+i}\omega_{\sigma_i}-n_i\omega_{\sigma_{g+i}}\right),
> $$
> 其中 $n_i$ 是 $\sigma$ 与 $\sigma_i$ 的相交数.

> **对任意闭曲线 $\sigma$, 定义线性泛函 $\varphi(\sigma):H\to\mathbb C$ 为**
> $$
> \varphi(\sigma)(\omega)=\int_\sigma\omega.
> $$
> **根据刚才的命题, 所有闭曲线所生成的泛函在 $g$ 维复线性空间 $H^{*}$ 中生成一格点群, 记为 $\mathrm{Im}\,\varphi$. 我们把商空间 (群) $H^{*}/\mathrm{Im}\,\varphi$ 称为 $M$ 的 Jacobian 簇, 也记为 $J(M)$, 这是一个 $g$ 维紧致复流形 (复环面).**
>
> **固定一点 $p_0\in M$, 设 $\omega_i$（$i=1,\cdots,g$）为 $H$ 的一组典则基. 对于 $p\in M$, 选择连接 $p_0$ 至 $p$ 的曲线, 令 $\mu(p)\in H^{*}$ 为**
> $$
> \mu(p)(\omega)=\int_{p_0}^{p}\omega,\qquad\forall\omega\in H.
> $$
> **这个线性泛函跟连接 $p_0$ 至 $p$ 的曲线有关, 然而 $\mu(p)$ 在商空间 $J(M)$ 中的像与曲线的选取无关, 我们把这个像仍记为 $\mu(p)$. 这样就定义了映射 $\mu:M\to J(M)$, 称为 Abel-Jacobi 映射. 如果 $D=\sum_k n_kp_k$ 为一个因子, 则规定**
> $$
> \mu(D)=\sum_k n_k\mu(p_k)\in J(M).
> $$

### 4.3 引理 3.5.10 与 3.5.11

> **引理 3.5.10.** 设 $p\neq q$ 为 $M$ 上两点, 则存在惟一的亚纯微分 $\omega_{pq}$, 使得
> (1) $\omega_{pq}$ 以 $p,q$ 为单极点, 没有其它极点, 且 $\omega_{pq}$ 在 $p$ 处的留数为 $1$, 在 $q$ 处的留数为 $-1$;
> (2) 对于前述闭曲线 $\{\sigma_i\}$, 有 $\int_{\sigma_i}\omega_{pq}=0$, $i=1,\cdots,g$.

> **证明.** 考虑因子 $-p-q$, 显然 $l(-p-q)=H$. 因此, 由 Riemann-Roch 公式, 有
> $$
> 0=\dim l(-p-q)=\dim i(-p-q)+d(-p-q)+1-g.
> $$
> 这说明 $\dim i(-p-q)=g+1$. 因为 $H\subset i(-p-q)$ 维数为 $g$, 这说明 $i(-p-q)$ 中存在非全纯的亚纯微分 $\omega_{pq}$, 此亚纯微分的极点只能为 $p$ 或 $q$, 且为单极点. 由留数定理知 $p,q$ 正好都是 $\omega_{pq}$ 的极点. 通过规一化不妨假设 $\omega_{pq}$ 在 $p$ 处的留数为 $1$, 在 $q$ 处的留数为 $-1$; 剩下的证明留作习题. $\square$

> **引理 3.5.11.** 设 $\omega_i$（$1\le i\le g$）为 $H$ 的典范基, 则上述亚纯微分 $\omega_{pq}$ 满足条件
> $$
> \int_{\sigma_{g+i}}\omega_{pq}=2\pi\sqrt{-1}\int_q^p\omega_i,\qquad 1\le i\le g,
> $$
> 其中, 积分所沿的从 $q$ 到 $p$ 的曲线在 $M_0(P)$ 内取.

> **证明.** 对全纯微分 $\omega_i$ 以及亚纯微分 $\omega_{pq}$ 用双线性关系, 有
> $$
> \sum_{j=1}^{g}\left(\int_{\sigma_j}\omega_i\int_{\sigma_{g+j}}\omega_{pq}-0\right)=2\pi\sqrt{-1}\left(\int_{p_0}^{p}\omega_i-\int_{p_0}^{q}\omega_i\right),
> $$
> 因为 $\{\omega_i\}$ 为典范基, $\int_{\sigma_j}\omega_i=\delta_{ij}$, 故上式立即推出我们所需要的结论. $\square$

### 4.4 定理 3.5.9

> **定理 3.5.9 (Abel).** 设 $M$ 是亏格为 $g$（$g\ge 1$）的紧致黎曼曲面, 则因子 $D$ 为主要因子的充要条件是 $d(D)=0$ 且 $\mu(D)=0\in J(M)$.

**必要性（$D$ 为主因子 $\Rightarrow\mu(D)=0$）**

> **设 $D$ 是次数为 $0$ 的因子, 我们可以把 $D$ 写为**
> $$
> D=\sum_{j=1}^{k}(p_j-q_j),\qquad p_i\neq q_j.
> $$
> **如果 $D=(f)$ 为主要因子, 令**
> $$
> \int_{\sigma_i}\frac{df}{f}=2\pi\sqrt{-1}\alpha_i,\qquad \alpha_i\in\mathbb Z,\quad i=1,\cdots,2g.
> $$

> **由于亚纯微分 $\frac{df}{f}$ 和 $\sum_{j=1}^{k}\omega_{p_jq_j}$ 具有相同的极点和留数, 从而 $\frac{df}{f}-\sum_{j=1}^{k}\omega_{p_jq_j}=\sum_{i=1}^{g}c_i\omega_i$ 为全纯微分. 我们有**
> $$
> c_i=\int_{\sigma_i}\sum_{j=1}^{g}c_j\omega_j=\int_{\sigma_i}\frac{df}{f}=2\pi\sqrt{-1}\alpha_i,\qquad i=1,\cdots,g.
> $$

> **另一方面,**
> $$
> \int_{\sigma_{g+i}}\frac{df}{f}-\sum_{j=1}^{k}\int_{\sigma_{g+i}}\omega_{p_jq_j}=\sum_{j=1}^{g}2\pi\sqrt{-1}\alpha_j\int_{\sigma_{g+i}}\omega_j,
> $$
> **利用前面的命题和引理, 上式整理后成为**
> $$
> \alpha_{g+i}-\sum_{j=1}^{k}\int_{q_j}^{p_j}\omega_i=\sum_{j=1}^{g}\alpha_j\int_{\sigma_{g+j}}\omega_i.
> $$

> **利用 Jacobi 映射进一步改写为**
> $$
> \mu(D)(\omega_i)=\alpha_{g+i}-\sum_{j=1}^{g}\alpha_j\int_{\sigma_{g+j}}\omega_i=\sum_{j=1}^{g}\left(\alpha_{g+j}\int_{\sigma_j}-\alpha_j\int_{\sigma_{g+j}}\right)\omega_i,
> $$
> **因此**
> $$
> \mu(D)(\omega)=\sum_{j=1}^{g}\left(\alpha_{g+j}\int_{\sigma_j}-\alpha_j\int_{\sigma_{g+j}}\right)\omega,\qquad\forall\omega\in H.
> $$
> **由 $\alpha_i\in\mathbb Z$（$1\le i\le 2g$）即知 $\mu(D)=0\in J(M)$.**

**充分性（$\mu(D)=0\Rightarrow D$ 为主因子）**

> **反之, 如果 $\mu(D)=0\in J(M)$, 则存在整数 $\beta_i$, $i=1,\cdots,2g$ 使得**
> $$
> \mu(D)(\omega)=\left(\sum_{j=1}^{2g}\beta_j\int_{\sigma_j}\right)\omega,\qquad\forall\omega\in H.
> $$
> **令 $\eta=\sum_{j=1}^{k}\omega_{p_jq_j}-2\pi\sqrt{-1}\sum_{j=1}^{g}\beta_{g+j}\omega_j$, 则**
> $$
> \int_{\sigma_i}\eta=-2\pi\sqrt{-1}\sum_{j=1}^{g}\beta_{g+j}\int_{\sigma_i}\omega_j=-2\pi\sqrt{-1}\beta_{g+i},
> $$
> **同理,**
> $$
> \int_{\sigma_{g+i}}\eta=2\pi\sqrt{-1}\sum_{j=1}^{k}\int_{q_j}^{p_j}\omega_i-2\pi\sqrt{-1}\sum_{j=1}^{g}\beta_{g+j}\int_{\sigma_{g+i}}\omega_j=2\pi\sqrt{-1}\beta_i.
> $$

> **这说明, 对任意不经过 $D$ 的闭曲线 $\sigma$, 均有 $\int_\sigma\eta\in 2\pi\sqrt{-1}\,\mathbb Z$. 因此, 如下函数 $f:M\to S$,**
> $$
> f(p)=\exp\left(\int_{p_0}^{p}\eta\right),\qquad p\in M
> $$
> **是定义好的亚纯函数, 显然有 $(f)=D$. $\square$**

## 5. Jacobi 反演（定理 3.5.13）

### 5.1 引理 3.5.12

> **我们知道, 次数同态 $d:\overline{\mathcal D}\to\mathbb Z$ 是从因子群到整数加群的同态, 主要因子群 $P$ 为 $\ker d$ 的子群, 我们称商群 $\ker d/P$ 为 $M$ 的 Picard 群, 也记为 $\mathrm{Pic}^0(M)$. Jacobi 映射自然诱导了加群同态**
> $$
> j:\mathrm{Pic}^0(M)\to J(M),\qquad j([D])=\mu(D).
> $$
> **Abel 定理告诉我们, 这是一个单同态. 下面我们来说明 $j$ 实际上也是一个满同态.**

> **引理 3.5.12.** 设 $M$ 是亏格为 $g$ 的紧致黎曼曲面, $(U,z)$ 为 $M$ 的一个局部坐标系. 则存在 $U$ 中 $g$ 个不同的点 $p_1,\cdots,p_g$ 以及 $H$ 的一组基 $\varphi_1,\cdots,\varphi_g$, 使得矩阵 $(f_i(p_j))_{g\times g}$ 是非退化的, 其中 $f_idz$ 是 $\varphi_i$ 的局部表示.

> **证明.** 先取一非零全纯微分 $\varphi_1$, $\varphi_1$ 在 $U$ 中不能恒为零, 因此存在一点, 记为 $p_1\in U$, 使得 $\varphi_1$ 在 $p_1$ 处非零. 因为 $\dim i(p_1)=g-1$, 我们在 $i(p_1)\subset H$ 中取全纯微分 $\varphi_2$, 使得 $\varphi_2$ 在某点 $p_2\in U$ 处非零. 这说明 $\dim i(p_1+p_2)=g-2$, 因此又可以在 $i(p_1+p_2)$ 中取全纯微分 $\varphi_3$, 使得 $\varphi_3$ 在某点 $p_3\in U$ 处非零. 如法炮制, 我们就得到 $g$ 个点 $p_1,\cdots,p_g\in U$, 以及 $g$ 个非零全纯微分 $\varphi_1,\cdots,\varphi_g$, 使得
> $$
> \varphi_i(p_j)=0,\ j=1,\cdots,i-1;\qquad \varphi_i(p_i)\neq 0.
> $$
> 如果在 $U$ 内 $\varphi_i=f_idz$, 则 $g$ 阶方阵 $(f_i(p_j))_{g\times g}$ 为下三角形的, 且对角线元素不为零, 因而为可逆矩阵. 显然, $\{\varphi_i\}$ 为 $H$ 的一组基. $\square$

### 5.2 定理 3.5.13

> **现在设 $p_1,\cdots,p_g$ 是这个引理中的 $g$ 个点, 我们定义一个新的映射如下. 考虑 $M^g$ (乘积流形), 令**
> $$
> \Psi:M^g\to\mathrm{Pic}^0(M),\qquad \Psi(x_1,\cdots,x_g)=\sum_{i=1}^{g}(x_i-p_i)\ \mathrm{mod}\ P.
> $$
> **记复合映射 $j\circ\Psi$ 为 $J$.**

> **定理 3.5.13 (Jacobi).** $\Psi:M^g\to\mathrm{Pic}^0(M)$ 为满射, $j:\mathrm{Pic}^0(M)\to J(M)$ 为加群同构, 因而 $J:M^g\to J(M)$ 也是满射.

> **证明.** 设 $D$ 为次数为零的因子. 考虑次数为 $g$ 的因子 $D_1=D+p_1+p_2+\cdots+p_g$. 由 Riemann-Roch 公式,
> $$
> \dim l(D_1)\ge d(D_1)+(1-g)=1.
> $$
> 因此存在非零亚纯函数 $f\in l(D_1)$. 此时, $(f)+D_1$ 是次数为 $g$ 的有效因子, 因而可以写为
> $$
> (f)+D_1=x_1+x_2+\cdots+x_g,\qquad x_i\in M,\quad 1\le i\le g.
> $$
> **这说明 $\Psi(x_1,\cdots,x_g)=[D]\in\mathrm{Pic}^0(M)$, 即 $\Psi$ 为满射.**

> **根据 Abel 定理, $j$ 为单射. 由于 $j$ 为加群同态, 为了说明 $j$ 为同构, 只要证明 $j$ 的像包含 $[0]\in J(M)$ 的一个开邻域即可. 我们来说明, $J=j\circ\Psi$ 的像的确包含这样的一个开邻域. 为此, 取 $[0]\in J(M)$ 附近的一个局部坐标映射如下: 它将 $\lambda\in H^{*}$ 映为 $(\lambda(\varphi_1),\cdots,\lambda(\varphi_g))\in\mathbb C^g$, 其中 $\{\varphi_i\}$ 是上面引理中 $H$ 的一组基. 在 $U$ 中取以 $p_i$ 为中心的两两不交的坐标圆盘 $B_i$, $B_i$ 上的坐标函数仍取为 $z$, 在这些坐标之下, $J$ 的局部表示为**
> $$
> F(z_1,\cdots,z_g)=\left(\sum_{j=1}^{g}\int_{p_j}^{z_j}f_1dz,\ \cdots,\ \sum_{j=1}^{g}\int_{p_j}^{z_j}f_gdz\right),
> $$
> **其中, 积分所用曲线都在各自坐标圆盘中选取. 如果 $F$ 的第 $i$ 个分量记为 $F_i$, 则**
> $$
> \frac{\partial F_i}{\partial z_j}=f_i(z_j).
> $$
> **因此, 根据上面的引理, $J$ 在 $(p_1,\cdots,p_g)\in M^g$ 处的 Jacobian 是非退化的. 由逆映射定理即知 $J$ 的像包含了一个开邻域, 这就证明了所需结论. $\square$**

> **定理 3.5.14.** 当 $g=1$ 时, 映射 $\mu:M\to J(M)$ 和 $J:M\to J(M)$ 均为全纯同构.

> **证明.** 注意到亏格为 $1$ 时 $\mu$ 和 $J$ 是同一类映射. 以 $\mu$ 为例, 我们说明 $\mu$ 为单射: 如果 $p\neq q$ 且 $\mu(p)=\mu(q)$, 则 $\mu(p-q)=0$, 由 Abel 定理, $p-q=(f)$, $f:M\to S$ 为亚纯函数. 此时 $f$ 仅有一个极点, 且为单极点, 从而 $f$ 为全纯同构, 这与 $g=1$ 相矛盾. 现在 $\mu:M\to J(M)$ 是从 $M$ 到黎曼环面的全纯单射, 因此必为全纯同构. $\square$

