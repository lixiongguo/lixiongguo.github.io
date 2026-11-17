> **记号**：拉格朗日函数按 Nocedal & Wright 取负号 $\mathcal{L}_\rho=f+g-\boldsymbol{\lambda}^T(\boldsymbol{x}-\boldsymbol{z})+\frac{\rho}{2}\lVert \boldsymbol{x}-\boldsymbol{z}\rVert^2$；罚参数沿用 Boyd 的 $\rho$，它与《有约束优化2》的 $\mu$ 是同一个量（$\rho\equiv\mu$）。缩放乘子记 $\boldsymbol{u}=\boldsymbol{\lambda}/\rho$。

## 交替方向乘子法 (ADMM)

**交替方向乘子法 (Alternating Direction Method of Multipliers, ADMM)** 可视为增广拉格朗日法在**变量分裂**情形下的实现：把「两项缠在同一变量上」的困难问题拆成两个子问题，交替对各自变量做极小化，再更新乘子。

### 原形式

许多实际能量可写成**同一变量上的两项之和**：

$$
\min_{\boldsymbol{x}}\; f(\boldsymbol{x}) + g(\boldsymbol{x}).
$$

典型情形：

- $f$ **光滑**（二次能量、对数障碍等），$g$ **非光滑**（$\ell_1$、盒约束指示函数、总变差）——无法对 $f+g$ 直接做牛顿法；
- $f$ 与 $g$ 各自有高效的 **proximal 算子**或闭式极小化，但**合在一起**没有；
- 参数化中常见 $f(\boldsymbol{x}) + g(\boldsymbol{D}\boldsymbol{x})$（$\boldsymbol{D}$ 为差分/梯度算子）：$f$ 在变量 $\boldsymbol{x}$ 上简单，$g$ 在「图像梯度」$\boldsymbol{D}\boldsymbol{x}$ 上简单，直接联合优化仍困难。

若对 $f+g$ 整体调用 ALM 或牛顿法，每步都要同时处理光滑项与非光滑项（或跨算子 $\boldsymbol{D}$ 的耦合），内层代价高、数值不稳。**ADMM 的思路是引入辅助变量，把两项拆到不同变量上，再用线性等式把它们绑在一起。**

### 分裂形式

引入辅助变量 $\boldsymbol{z}$，将原问题**等价**改写为

$$
\min_{\boldsymbol{x},\,\boldsymbol{z}}\; f(\boldsymbol{x}) + g(\boldsymbol{z})\\
\quad\text{s.t.}\quad \boldsymbol{x} - \boldsymbol{z} = \boldsymbol{0}.
$$

在约束 $\boldsymbol{x}=\boldsymbol{z}$ 满足时，目标恰为 $f(\boldsymbol{x})+g(\boldsymbol{x})$，故与原形式等价；分裂后 $f$ 只出现在 $\boldsymbol{x}$ 上、$g$ 只出现在 $\boldsymbol{z}$ 上，为交替求解创造条件。

对约束 $\boldsymbol{x}-\boldsymbol{z}=\boldsymbol{0}$ 套用《有约束优化2》的增广拉格朗日模板（该篇 $\boldsymbol{c}(\boldsymbol{x})=\boldsymbol{0}$，此处 $\boldsymbol{c}(\boldsymbol{x},\boldsymbol{z})=\boldsymbol{x}-\boldsymbol{z}$）：

$$
\mathcal{L}_\rho(\boldsymbol{x},\boldsymbol{z},\boldsymbol{\lambda})
:= f(\boldsymbol{x}) + g(\boldsymbol{z})
- \boldsymbol{\lambda}^T(\boldsymbol{x}-\boldsymbol{z})
+ \frac{\rho}{2}\lVert \boldsymbol{x}-\boldsymbol{z}\rVert_2^2.
$$

**标准 ALM** 每步联合极小化 $\mathcal{L}_\rho$ over $(\boldsymbol{x},\boldsymbol{z})$，再做乘子步 $\boldsymbol{\lambda}^{k+1}=\boldsymbol{\lambda}^{k}-\rho(\boldsymbol{x}^{k+1}-\boldsymbol{z}^{k+1})$；**ADMM** 改为**交替**极小化——先固定 $\boldsymbol{z}^k$ 优化 $\boldsymbol{x}$，再固定 $\boldsymbol{x}^{k+1}$ 优化 $\boldsymbol{z}$：

$$
\begin{aligned}
\boldsymbol{x}^{k+1} &= \arg\min_{\boldsymbol{x}}\;
\Bigl\{ f(\boldsymbol{x}) + \frac{\rho}{2}\bigl\lVert \boldsymbol{x}-\boldsymbol{z}^k-\boldsymbol{\lambda}^k/\rho\bigr\rVert_2^2 \Bigr\}, \\\\
\boldsymbol{z}^{k+1} &= \arg\min_{\boldsymbol{z}}\;
\Bigl\{ g(\boldsymbol{z}) + \frac{\rho}{2}\bigl\lVert \boldsymbol{x}^{k+1}-\boldsymbol{z}+\boldsymbol{\lambda}^k/\rho\bigr\rVert_2^2 \Bigr\}, \\\\
\boldsymbol{\lambda}^{k+1} &= \boldsymbol{\lambda}^k - \rho\bigl(\boldsymbol{x}^{k+1}-\boldsymbol{z}^{k+1}\bigr).
\end{aligned}
$$

两处符号都来自 $\mathcal{L}_\rho$ 的负号：$\boldsymbol{x}$-步把 $\boldsymbol{x}$ 拉向 $\boldsymbol{z}^k+\boldsymbol{\lambda}^k/\rho$，故式中出现 $-\boldsymbol{\lambda}^k/\rho$；$\boldsymbol{z}$-步把 $\boldsymbol{z}$ 拉向 $\boldsymbol{x}^{k+1}-\boldsymbol{\lambda}^k/\rho$，故式中出现 $+\boldsymbol{\lambda}^k/\rho$。

$\boldsymbol{x}$-步与 $\boldsymbol{z}$-步各自是「原项 + 二次近端项」，记 $\boldsymbol{u}^k=\boldsymbol{\lambda}^k/\rho$，常写成

$$
\boldsymbol{x}^{k+1} = \mathrm{prox}_{f/\rho}\!\bigl(\boldsymbol{z}^k + \boldsymbol{u}^k\bigr),
\qquad
\boldsymbol{z}^{k+1} = \mathrm{prox}_{g/\rho}\!\bigl(\boldsymbol{x}^{k+1} - \boldsymbol{u}^k\bigr),
\qquad
\boldsymbol{u}^{k+1}=\boldsymbol{u}^k-\bigl(\boldsymbol{x}^{k+1}-\boldsymbol{z}^{k+1}\bigr),
$$

其中 $\mathrm{prox}_{h/\rho}(\boldsymbol{v})=\arg\min_{\boldsymbol{u}} h(\boldsymbol{u})+\frac{\rho}{2}\lVert \boldsymbol{u}-\boldsymbol{v}\rVert_2^2$。乘子更新与 ALM 完全相同；差别在于 $\boldsymbol{x}$、$\boldsymbol{z}$ **不同时**做内层极小化。

> **与 Boyd 书的符号差异**：Boyd 等人把增广拉格朗日写成 $f+g+\boldsymbol{\lambda}^T(\boldsymbol{x}-\boldsymbol{z})+\frac{\rho}{2}\lVert \cdot\rVert^2$，三步相应为 $\lVert \boldsymbol{x}-\boldsymbol{z}+\boldsymbol{u}\rVert^2$、$\lVert \boldsymbol{x}-\boldsymbol{z}+\boldsymbol{u}\rVert^2$、$\boldsymbol{u}\mathrel{+}=\boldsymbol{x}-\boldsymbol{z}$。本篇取 N&W 的负号，等价于把乘子重新定号（$\boldsymbol{\lambda}\to-\boldsymbol{\lambda}$），因此 $\boldsymbol{u}$ 与 Boyd 书中的 $\boldsymbol{u}$ 反号。两种写法给出的迭代点与收敛性完全相同。

**推广（线性算子耦合）**：原形式为 $f(\boldsymbol{x})+g(\boldsymbol{D}\boldsymbol{x})$ 时，令 $\boldsymbol{z}=\boldsymbol{D}\boldsymbol{x}$，分裂为

$$
\min_{\boldsymbol{x},\boldsymbol{z}}\; f(\boldsymbol{x}) + g(\boldsymbol{z})
\quad\text{s.t.}\quad \boldsymbol{D}\boldsymbol{x} - \boldsymbol{z} = \boldsymbol{0},
$$

迭代公式同上，仅把 $\boldsymbol{x}-\boldsymbol{z}$ 换为 $\boldsymbol{D}\boldsymbol{x}-\boldsymbol{z}$；$\boldsymbol{x}$-步一般需求解线性系统（$\boldsymbol{D}^T\boldsymbol{D}$ 或 $f$ 的 Hessian 参与），$\boldsymbol{z}$-步仍常为 prox / 投影。更一般的 $\boldsymbol{A}\boldsymbol{x}+\boldsymbol{B}\boldsymbol{z}=\boldsymbol{b}$ 属同一框架，本文以 $\boldsymbol{x}=\boldsymbol{z}$ 及 $\boldsymbol{D}\boldsymbol{x}=\boldsymbol{z}$ 为主。

### 与增广拉格朗日法的关系

|        | **ALM**（《有约束优化2》§增广拉格朗日法）                     | **ADMM**                                                     |
| ------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| 问题   | $\min f(\boldsymbol{x})$ s.t. $\boldsymbol{c}(\boldsymbol{x})=\boldsymbol{0}$ | $\min f(\boldsymbol{x})+g(\boldsymbol{x})$，分裂为 $f(\boldsymbol{x})+g(\boldsymbol{z})$，$\boldsymbol{x}=\boldsymbol{z}$ |
| 变量   | 单块 $\boldsymbol{x}$                                        | $\boldsymbol{x}$、$\boldsymbol{z}$ 各管一项                  |
| 内层   | 联合 $\arg\min_{\boldsymbol{x}} \mathcal{L}_A(\boldsymbol{x},\boldsymbol{\lambda}^k;\mu)$ | 交替 $\mathrm{prox}_{f/\rho}$、$\mathrm{prox}_{g/\rho}$      |
| 约束   | 一般非线性 $\boldsymbol{c}$ 可直接处理                        | 耦合为线性（$\boldsymbol{x}-\boldsymbol{z}=\boldsymbol{0}$ 或 $\boldsymbol{D}\boldsymbol{x}=\boldsymbol{z}$） |
| 子问题 | 常需牛顿 / L-BFGS                                            | $f$、$g$ 结构合适时闭式或快速                                |
| 对偶侧 | 对偶函数上的**邻近点法**（§与邻近点法、DRS 的关系）          | 对偶函数上的 **DRS**：一个 prox 拆成两个                     |

表中 ALM 一侧用该篇的记号 $\mathcal{L}_A(\cdot,\cdot;\mu)$，本篇的 $\rho$ 与其中的 $\mu$ 是同一个罚参数（$\rho\equiv\mu$），乘子步 $\boldsymbol{\lambda}^{k+1}=\boldsymbol{\lambda}^{k}-\rho(\boldsymbol{x}^{k+1}-\boldsymbol{z}^{k+1})$ 与 $\boldsymbol{\lambda}^{k+1}=\boldsymbol{\lambda}^{k}-\mu\boldsymbol{c}(\boldsymbol{x}^{k+1})$ 形式一致。

二者共享增广拉格朗日与乘子更新；ALM 的两条性质在分裂问题上同样成立：对偶不准时增大 $\rho$ 可驱动 $\boldsymbol{x}-\boldsymbol{z}\to\boldsymbol{0}$；对偶最优且 $\rho$ 足够大时，有限 $\rho$ 下可精确实现 $\boldsymbol{x}=\boldsymbol{z}$。

### 与邻近点法、DRS 的关系

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
\boldsymbol{\mu}^{k}&=\mathrm{prox}_{\Phi_1}\bigl(\boldsymbol{\nu}^{k}\bigr), \\\\
\boldsymbol{\lambda}^{k}&=\mathrm{prox}_{\Phi_2}\bigl(2\boldsymbol{\mu}^{k}-\boldsymbol{\nu}^{k}\bigr), \\\\
\boldsymbol{\nu}^{k+1}&=\boldsymbol{\nu}^{k}+\boldsymbol{\lambda}^{k}-\boldsymbol{\mu}^{k}.
\end{aligned}
$$

$\boldsymbol{\nu}$ 是辅助（影子）变量，不是乘子；$\boldsymbol{\lambda}^{k}$ 才是乘子。三个动作是：一次 prox、**反射后**再一次 prox、按两个结果之差修正 $\boldsymbol{\nu}$。反射不可省：只做两次投影（POCS）时，两个集合接近相切就会来回振荡。

#### 代入：Moreau 恒等式把对偶 prox 换回原变量

$$
\mathrm{prox}_{\gamma h^{*}}(\boldsymbol{v})=\boldsymbol{v}-\gamma\,\mathrm{prox}_{h/\gamma}\!\left(\boldsymbol{v}/\gamma\right),
$$

即「对 $h^{*}$ 求 prox」等于「对 $h$ 求 prox」再加一个平移，不必显式构造共轭函数。取 $\Phi_1=f^{*}(\cdot)$、$\Phi_2=g^{*}(-\cdot)$ 代入并化简，得到 ADMM 三行：

| DRS（对偶侧）                                                       | ADMM（原变量侧，本篇符号）                                                                                        |
| :------------------------------------------------------------------ | :---------------------------------------------------------------------------------------------------------------- |
| $\boldsymbol{\mu}^{k}=\mathrm{prox}_{\Phi_1}(\boldsymbol{\nu}^{k})$  | $\boldsymbol{x}$-步：$\min_{\boldsymbol{x}}\Bigl\{f(\boldsymbol{x})+\frac{\rho}{2}\bigl\lVert \boldsymbol{x}-\boldsymbol{z}^{k}-\boldsymbol{u}^{k}\bigr\rVert_2^2\Bigr\}$ |
| $\mathrm{prox}_{\Phi_2}(2\boldsymbol{\mu}^{k}-\boldsymbol{\nu}^{k})$ | $\boldsymbol{z}$-步：$\min_{\boldsymbol{z}}\Bigl\{g(\boldsymbol{z})+\frac{\rho}{2}\bigl\lVert \boldsymbol{x}^{k+1}-\boldsymbol{z}+\boldsymbol{u}^{k}\bigr\rVert_2^2\Bigr\}$ |
| $\boldsymbol{\nu}^{k+1}=\boldsymbol{\nu}^{k}+\boldsymbol{\lambda}^{k}-\boldsymbol{\mu}^{k}$ | $\boldsymbol{u}^{k+1}=\boldsymbol{u}^{k}-\bigl(\boldsymbol{x}^{k+1}-\boldsymbol{z}^{k+1}\bigr)$                    |

两边的对应关系是：**一次对偶 prox ↔ 一次原始极小化**（Moreau 恒等式），**影子点的累加 $\boldsymbol{\nu}^{k+1}-\boldsymbol{\nu}^{k}$ ↔ 乘子的修正量 $\rho(\boldsymbol{x}-\boldsymbol{z})$**。$\boldsymbol{u}=\boldsymbol{\lambda}/\rho$ 是缩放乘子；反射 $2\boldsymbol{\mu}-\boldsymbol{\nu}$ 的作用是把「上一次 prox 的落点」与「影子点尚未抵消的偏移」一起递进第二个 prox，避免在两个集合几乎相切时来回振荡。按本篇的符号约定，这个偏移在 $\boldsymbol{z}$-步上表现为 $+\boldsymbol{u}^{k}$，在 $\boldsymbol{x}$-步上表现为 $-\boldsymbol{u}^{k}$。

#### 三点推论

1. **收敛性来自 DRS。** DRS 只要求 $f$、$g$ 闭、凸、真，不要求光滑或强凸，ADMM 的收敛保证由此继承。反之，三块 ADMM 没有对应的 DRS 定理，故一般不保证收敛。
2. **$\rho$ 的尺度。** 它既是罚参数，又是邻近项系数（与 DRS 步长互为倒数）。$\rho$ 大，对偶几乎不正则，快但不稳；$\rho$ 小，正则强，稳但慢——这是实践需要残差平衡的原因。
3. **硬约束时 $\rho$ 退化。** 若 $f$、$g$ 都是指示函数，$\mathrm{prox}$ 即投影，与 $\rho$ 无关；此时 ADMM 退化为「投影 + 反射 + 投影」，可调参数只剩松弛因子。

#### 适用范围

上述「对偶函数为两项之和」依赖 $\boldsymbol{c}$ 对 $(\boldsymbol{x},\boldsymbol{z})$ **线性可分**（$\boldsymbol{x}-\boldsymbol{z}$ 或 $\boldsymbol{D}\boldsymbol{x}-\boldsymbol{z}$）。一般非线性约束的 ALM 无此分离：其乘子步仍是邻近点法，但不能写成 DRS，因而不是 ADMM。

> **几何处理中的对应**：FastHGP 的 ATP 在「局部单射凸集」与「调和映射导数子空间」之间交替投影并加切向修正，即本节 $f=\iota_B$、$g=\iota_{\operatorname{Im}\tilde J}$ 的情形——两个 prox 都是投影，$\rho$ 退化（推论 3）。
