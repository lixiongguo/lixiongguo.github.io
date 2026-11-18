交替极小化不是新的构造。换到对偶侧看：**ALM 是对偶函数上的邻近点法，ADMM 是把这一邻近步替换成 Douglas–Rachford 分裂 (DRS)**。沿用《有约束优化2》的记号：$\boldsymbol{c}(\boldsymbol{x},\boldsymbol{z})=\boldsymbol{x}-\boldsymbol{z}$，$\theta(\boldsymbol{\lambda})=\inf_{\boldsymbol{x},\boldsymbol{z}}\mathcal{L}(\boldsymbol{x},\boldsymbol{z},\boldsymbol{\lambda})$，其中 $\mathcal{L}$ 不含罚项。

#### 乘子步 = 对偶函数上的邻近点法

ALM 的乘子更新可写成

$$
\boldsymbol{\lambda}^{k+1}=\arg\max_{\boldsymbol{\lambda}}\Bigl\{\theta(\boldsymbol{\lambda})-\frac{1}{2\rho}\bigl\lVert \boldsymbol{\lambda}-\boldsymbol{\lambda}^{k}\bigr\rVert_2^2\Bigr\},
$$

即每步不追 $\theta$ 的精确极大点，而追「加上回拉二次项后」的极大点，回拉强度由 $\rho$ 控制——这就是**邻近点法 (proximal point)**。与《有约束优化2》§关键恒等式 (★) 中的 $-\frac{1}{2\mu}\lVert \boldsymbol{\lambda}\rVert_2^2$（该篇的 $\mu$ 即本篇的 $\rho$）只差正则的对象：那里正则 $\boldsymbol{\lambda}$ 本身（消去后得到罚函数），这里正则 $\boldsymbol{\lambda}-\boldsymbol{\lambda}^{k}$（消去后得到乘子步）。

用该篇 §小例 的同一问题验证：$\min\frac12x^2$ s.t. $x-1=0$，$\theta(\lambda)=-\frac12\lambda^2+\lambda$。

- **ALM**：由 $\partial_x\mathcal{L}_\rho=0$ 得 $x=\frac{\rho+\lambda}{1+\rho}$，故 $c=x-1=\frac{\lambda-1}{1+\rho}$，$\lambda^{+}=\lambda-\rho c=\frac{\lambda+\rho}{1+\rho}$；
- **邻近点法**：驻点方程 $1-\lambda-\frac{\lambda-\lambda^{k}}{\rho}=0$，解出 $\lambda^{+}=\frac{\lambda^{k}+\rho}{1+\rho}$。

两式相同。按本篇 $\mathcal{L}_\rho$ 的写法，邻近项系数是 $1/(2\rho)$，即 $\rho$ 同时是罚参数与邻近项参数。

#### 对偶函数是两项之和

$$
\theta(\boldsymbol{\lambda})
=\inf_{\boldsymbol{x}}\bigl\{f(\boldsymbol{x})-\boldsymbol{\lambda}^T\boldsymbol{x}\bigr\}
+\inf_{\boldsymbol{z}}\bigl\{g(\boldsymbol{z})+\boldsymbol{\lambda}^T\boldsymbol{z}\bigr\}
=-f^{*}(\boldsymbol{\lambda})-g^{*}(-\boldsymbol{\lambda}).
$$

第一项只含 $f$、第二项只含 $g$，两个 prox 可分别计算。而邻近点法要求的是**整体** prox，即 $\arg\min_{\boldsymbol{x},\boldsymbol{z}}\mathcal{L}_\rho$——$f$、$g$ 仍然耦合。DRS 做的就是把这个整体 prox 换成两个。

#### DRS 三行

对 $\min_{\boldsymbol{\lambda}}\Phi_1(\boldsymbol{\lambda})+\Phi_2(\boldsymbol{\lambda})$：

$$
\begin{aligned}
\boldsymbol{\mu}^{k}&=\operatorname{prox}_{\Phi_1}\bigl(\boldsymbol{\nu}^{k}\bigr), \\\\
\boldsymbol{\lambda}^{k}&=\operatorname{prox}_{\Phi_2}\bigl(2\boldsymbol{\mu}^{k}-\boldsymbol{\nu}^{k}\bigr), \\\\
\boldsymbol{\nu}^{k+1}&=\boldsymbol{\nu}^{k}+\boldsymbol{\lambda}^{k}-\boldsymbol{\mu}^{k}.
\end{aligned}
$$

$\boldsymbol{\nu}$ 是辅助（影子）变量，不是乘子；$\boldsymbol{\lambda}^{k}$ 才是乘子。三个动作是：一次 prox、**反射后**再一次 prox、按两个结果之差修正 $\boldsymbol{\nu}$。反射不可省：只做两次投影（POCS）时，两个集合接近相切就会来回振荡。

#### 代入：Moreau 恒等式把对偶 prox 换回原变量

$$
\operatorname{prox}_{\gamma h^{*}}(\boldsymbol{v})=\boldsymbol{v}-\gamma\,\operatorname{prox}_{h/\gamma}\!\left(\boldsymbol{v}/\gamma\right),
$$

即「对 $h^{*}$ 求 prox」等于「对 $h$ 求 prox」再加一个平移，不必显式构造共轭函数。取 $\Phi_1=f^{*}(\cdot)$、$\Phi_2=g^{*}(-\cdot)$ 代入并化简，得到 ADMM 三行：

| DRS（对偶侧）                                                | ADMM（原变量侧，本篇符号）                                   |
| :----------------------------------------------------------- | :----------------------------------------------------------- |
| $\boldsymbol{\mu}^{k}=\operatorname{prox}_{\Phi_1}(\boldsymbol{\nu}^{k})$ | $\boldsymbol{x}$-步：$\min_{\boldsymbol{x}}\Bigl\{f(\boldsymbol{x})+\frac{\rho}{2}\bigl\lVert \boldsymbol{x}-\boldsymbol{z}^{k}-\boldsymbol{u}^{k}\bigr\rVert_2^2\Bigr\}$ |
| $\operatorname{prox}_{\Phi_2}(2\boldsymbol{\mu}^{k}-\boldsymbol{\nu}^{k})$ | $\boldsymbol{z}$-步：$\min_{\boldsymbol{z}}\Bigl\{g(\boldsymbol{z})+\frac{\rho}{2}\bigl\lVert \boldsymbol{x}^{k+1}-\boldsymbol{z}+\boldsymbol{u}^{k}\bigr\rVert_2^2\Bigr\}$ |
| $\boldsymbol{\nu}^{k+1}=\boldsymbol{\nu}^{k}+\boldsymbol{\lambda}^{k}-\boldsymbol{\mu}^{k}$ | $\boldsymbol{u}^{k+1}=\boldsymbol{u}^{k}-\bigl(\boldsymbol{x}^{k+1}-\boldsymbol{z}^{k+1}\bigr)$ |

两边的对应关系是：**一次对偶 prox ↔ 一次原始极小化**（Moreau 恒等式），**影子点的累加 $\boldsymbol{\nu}^{k+1}-\boldsymbol{\nu}^{k}$ ↔ 乘子的修正量 $\rho(\boldsymbol{x}-\boldsymbol{z})$**。$\boldsymbol{u}=\boldsymbol{\lambda}/\rho$ 是缩放乘子；反射 $2\boldsymbol{\mu}-\boldsymbol{\nu}$ 的作用是把「上一次 prox 的落点」与「影子点尚未抵消的偏移」一起递进第二个 prox，避免在两个集合几乎相切时来回振荡。按本篇的符号约定，这个偏移在 $\boldsymbol{z}$-步上表现为 $+\boldsymbol{u}^{k}$，在 $\boldsymbol{x}$-步上表现为 $-\boldsymbol{u}^{k}$。

#### 三点推论

1. **收敛性来自 DRS。** DRS 只要求 $f$、$g$ 闭、凸、真，不要求光滑或强凸，ADMM 的收敛保证由此继承。反之，三块 ADMM 没有对应的 DRS 定理，故一般不保证收敛。
2. **$\rho$ 的尺度。** 它既是罚参数，又是邻近项系数（与 DRS 步长互为倒数）。$\rho$ 大，对偶几乎不正则，快但不稳；$\rho$ 小，正则强，稳但慢——这是实践需要残差平衡的原因。
3. **硬约束时 $\rho$ 退化。** 若 $f$、$g$ 都是指示函数，$\operatorname{prox}$ 即投影，与 $\rho$ 无关；此时 ADMM 退化为「投影 + 反射 + 投影」，可调参数只剩松弛因子。

#### 适用范围

上述「对偶函数为两项之和」依赖 $\boldsymbol{c}$ 对 $(\boldsymbol{x},\boldsymbol{z})$ **线性可分**（$\boldsymbol{x}-\boldsymbol{z}$ 或 $\boldsymbol{D}\boldsymbol{x}-\boldsymbol{z}$）。一般非线性约束的 ALM 无此分离：其乘子步仍是邻近点法，但不能写成 DRS，因而不是 ADMM。