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

对约束 $\boldsymbol{x}-\boldsymbol{z}=\boldsymbol{0}$ 套用本篇增广拉格朗日模板（与 §增广拉格朗日法 中 $c(\boldsymbol{x})=\boldsymbol{0}$ 相同，此处 $c(\boldsymbol{x},\boldsymbol{z})=\boldsymbol{x}-\boldsymbol{z}$）：

$$
L_\rho(\boldsymbol{x},\boldsymbol{z},\boldsymbol{\lambda})
= f(\boldsymbol{x}) + g(\boldsymbol{z})
+ \boldsymbol{\lambda}^T(\boldsymbol{x}-\boldsymbol{z})
+ \frac{\rho}{2}\|\boldsymbol{x}-\boldsymbol{z}\|_2^2.
$$

**标准 ALM** 每步联合极小化 $L_\rho$ over $(\boldsymbol{x},\boldsymbol{z})$；**ADMM** 改为**交替**极小化——先固定 $\boldsymbol{z}^k$ 优化 $\boldsymbol{x}$，再固定 $\boldsymbol{x}^{k+1}$ 优化 $\boldsymbol{z}$：

$$
\begin{aligned}
\boldsymbol{x}^{k+1} &= \arg\min_{\boldsymbol{x}}\;
\Bigl\{ f(\boldsymbol{x}) + \frac{\rho}{2}\bigl\|\boldsymbol{x}-\boldsymbol{z}^k+\boldsymbol{\lambda}^k/\rho\bigr\|_2^2 \Bigr\}, \\\\
\boldsymbol{z}^{k+1} &= \arg\min_{\boldsymbol{z}}\;
\Bigl\{ g(\boldsymbol{z}) + \frac{\rho}{2}\bigl\|\boldsymbol{x}^{k+1}-\boldsymbol{z}+\boldsymbol{\lambda}^k/\rho\bigr\|_2^2 \Bigr\}, \\\\
\boldsymbol{\lambda}^{k+1} &= \boldsymbol{\lambda}^k + \rho\bigl(\boldsymbol{x}^{k+1}-\boldsymbol{z}^{k+1}\bigr).
\end{aligned}
$$

第二、三式中，$\boldsymbol{x}$-步与 $\boldsymbol{z}$-步各自是「原项 + 二次近端项」，常记为

$$
\boldsymbol{x}^{k+1} = \mathrm{prox}_{f/\rho}\!\bigl(\boldsymbol{z}^k - \boldsymbol{\lambda}^k/\rho\bigr),
\qquad
\boldsymbol{z}^{k+1} = \mathrm{prox}_{g/\rho}\!\bigl(\boldsymbol{x}^{k+1} + \boldsymbol{\lambda}^k/\rho\bigr),
$$

其中 $\mathrm{prox}_{h/\rho}(\boldsymbol{v})=\arg\min_{\boldsymbol{u}} h(\boldsymbol{u})+\frac{\rho}{2}\|\boldsymbol{u}-\boldsymbol{v}\|_2^2$。乘子更新与 ALM 完全相同；差别在于 $\boldsymbol{x}$、$\boldsymbol{z}$ **不同时**做内层极小化。

**推广（线性算子耦合）**：原形式为 $f(\boldsymbol{x})+g(\boldsymbol{D}\boldsymbol{x})$ 时，令 $\boldsymbol{z}=\boldsymbol{D}\boldsymbol{x}$，分裂为

$$
\min_{\boldsymbol{x},\boldsymbol{z}}\; f(\boldsymbol{x}) + g(\boldsymbol{z})
\quad\text{s.t.}\quad \boldsymbol{D}\boldsymbol{x} - \boldsymbol{z} = \boldsymbol{0},
$$

迭代公式同上，仅把 $\boldsymbol{x}-\boldsymbol{z}$ 换为 $\boldsymbol{D}\boldsymbol{x}-\boldsymbol{z}$；$\boldsymbol{x}$-步一般需求解线性系统（$\boldsymbol{D}^T\boldsymbol{D}$ 或 $f$ 的 Hessian 参与），$\boldsymbol{z}$-步仍常为 prox / 投影。更一般的 $\boldsymbol{A}\boldsymbol{x}+\boldsymbol{B}\boldsymbol{z}=\boldsymbol{b}$ 属同一框架，本文以 $\boldsymbol{x}=\boldsymbol{z}$ 及 $\boldsymbol{D}\boldsymbol{x}=\boldsymbol{z}$ 为主。

### 与增广拉格朗日法的关系

|        | **ALM**（本篇 §增广拉格朗日法）                              | **ADMM**                                                     |
| ------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| 问题   | $\min f(\boldsymbol{x})$ s.t. $c(\boldsymbol{x})=\boldsymbol{0}$ | $\min f(\boldsymbol{x})+g(\boldsymbol{x})$，分裂为 $f(\boldsymbol{x})+g(\boldsymbol{z})$，$\boldsymbol{x}=\boldsymbol{z}$ |
| 变量   | 单块 $\boldsymbol{x}$                                        | $\boldsymbol{x}$、$\boldsymbol{z}$ 各管一项                  |
| 内层   | $\arg\min_{\boldsymbol{x}} L_\rho(\boldsymbol{x},\boldsymbol{\lambda}^k)$ | 交替 $\mathrm{prox}_{f/\rho}$、$\mathrm{prox}_{g/\rho}$      |
| 约束   | 一般非线性 $c$ 可直接处理                                    | 耦合为线性（$\boldsymbol{x}-\boldsymbol{z}=\boldsymbol{0}$ 或 $\boldsymbol{D}\boldsymbol{x}=\boldsymbol{z}$） |
| 子问题 | 常需牛顿 / L-BFGS                                            | $f$、$g$ 结构合适时闭式或快速                                |

二者共享增广拉格朗日与乘子更新；ADMM 的两条性质（§增广拉格朗日法）在分裂问题上同样成立：对偶不准时增大 $\rho$ 可驱动 $\boldsymbol{x}-\boldsymbol{z}\to\boldsymbol{0}$；对偶最优且 $\rho$ 足够大时，有限 $\rho$ 下可精确实现 $\boldsymbol{x}=\boldsymbol{z}$。