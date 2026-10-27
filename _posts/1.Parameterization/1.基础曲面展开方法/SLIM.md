参数化/变形除最小化畸变外，通常还要求映射**局部单射**——三角形不能翻转，否则纹理、重网格化等下游任务不可用（参见 [优化方法实现更好的映射](优化方法实现更好的映射.md)）。

**ARAP 的问题**：能量

$$
\mathcal{D}_{\text{ARAP}}(J) = \|J - R(J)\|_F^2
$$

对 shrink 有偏置——无限缩小三角形与适度缩放的畸变相当（论文 Fig. 6），高曲率区域常出现退化或翻转（Fig. 5：Gargoyle 99K 面产生 6K 翻转）。左图对比：ARAP 圆盘参数化出现重叠与高畸变；SLIM 最小化对称 Dirichlet 后无重叠、纹理均匀。

**已有 flip-preventing 能量的困难**：[Schüller et al. 2013; Fu et al. 2015; Smith & Schaefer 2015] 提出 $\det(J)<0 \Rightarrow \mathcal{D}=\infty$ 的能量，配合 Tutte 初值与受限线搜索可保证局部单射，但通用优化器（L-BFGS 等）慢且迭代次数随网格规模增长。SLIM 专为这类能量设计**可扩展**的 local/global 求解器，且能从**高度畸变初值**恢复——与 Stiffening、IRLS 等启发式不同，它直接最小化目标能量。

---

## 2. 问题表述

三角网格 $M=(V,F)$，参数化 $\Phi: M \to \mathbb{R}^{|V|\times 2}$ 为分段仿射映射。每个三角形 $f$ 的 Jacobian $J_f(x)=\nabla\varphi_f$ 为顶点坐标的线性函数。最小化

$$
\min_x \; E(x) = \sum_{f \in F} A_f \, \mathcal{D}(J_f(x))
$$

$A_f$ 为面积权重，$\mathcal{D}$ 为畸变度量。

### 2.1 ARAP 与 Local/Global

[Liu et al. 2008] 交替优化：

- **Local**：$R_f^k = R(J_f(x^{k-1}))$（SVD：$J=USV^T$，取 $R=UV^T$）
- **Global**：$\displaystyle x^k = \arg\min_x \sum_f A_f \|J_f(x) - R_f^k\|_F^2 + \lambda \|x - x^{k-1}\|^2$

ARAP 的二次代理 $P_R(J)=\|J-R\|_F^2$ 满足 Majorizer、梯度匹配、最近极小点三条性质（与 [AQP](几何优化-AQP.md) §3 相同），每步保证能量下降，但**不保证无翻转**。

### 2.2 对称 Dirichlet（SLIM 默认）

对等惩罚拉伸与压缩，$\mathcal{D}(J)=\mathcal{D}(J^{-1})$：

$$
\mathcal{D}(J_f) = \begin{cases}
\|J_f\|_F^2 + \|J_f^{-1}\|_F^2 & \det(J_f) \geq 0 \\
\infty & \det(J_f) < 0
\end{cases}
$$

$\det(J)<0$ 时能量无穷，配合受限线搜索保证三角形保持正向。梯度（$\det>0$）：

$$
\nabla_J \mathcal{D}(J) = 2J - 2J^{-T}
$$

---

## 3. 从标量权重到矩阵权重：SLIM 的核心推广

SLIM 的 local/global 框架来自 ARAP，但对称 Dirichlet 等能量**没有** ARAP 那样满足 Majorizer 的全局二次代理。论文的推进路线是：先回顾两类**标量加权**启发式及其局限，再说明为何必须升级为**矩阵加权**以匹配梯度。

### 3.1 标量加权代理：Stiffening 与 IRLS

**Greedy Stiffening** [Bommes et al. 2009] 在 ARAP 的 global 步中，对每个三角形引入标量权重 $w_f$，最小化

$$
\min_x \sum_{f \in F} A_f\, w_f^k \,\|J_f(x) - R_f^k\|_F^2
$$

思路：翻转或接近退化的元素加大 $w_f$，迫使优化器优先"修好"它们。这是**启发式**——加重一个元素的权重可能使邻域元素翻转，二者反复拉锯，算法可能永不收敛；且不保证每步产生下降方向（论文 Fig. 4）。

**IRLS**（Iteratively Reweighted Least Squares）[Pighin & Lewis 2007; Yoshizawa et al. 2004] 用另一套标量更新规则，使代理在数值上**局部匹配能量比值**而非梯度。对 $L^p$ 范数，取

$$
w_f^k = \frac{\mathcal{D}(J_f(x^{k-1}))}{\|J_f(x^{k-1}) - R_f^k\|_F^2}
$$

直觉：若某三角形几乎退化，分子（对称 Dirichlet）很大而分母（ARAP 代理）不大，则下一步加大 $w_f$ 以惩罚该元素；若某元素被过度缩放，$w_f < 1$ 减轻代理对它的惩罚。

SLIM 作者将 IRLS 规则嵌入自己的 local/global 框架做对比。实验表明：IRLS 比 Stiffening 好得多（Fig. 4：$\bar{E}=8.2$ vs $2140$），但**仍不能保证下降方向**，优化常会卡住；且它匹配的是**能量值之比**，不是**梯度**。

### 3.2 标量权重的根本局限

论文指出，标量 $w_f$ 的表达能力不足。考虑一个三角形 Jacobian 沿**一个轴**严重拉伸、沿**另一轴**几乎不变：

- 标量权重只能对整个 $\|J-R\|_F^2$ 统一缩放，**无法区分两个奇异方向**；
- 两个轴被等同惩罚，proxy 与真实能量 $\mathcal{D}(J)$ 的梯度方向不一致；
- 下降方向失真，在高曲率/高畸变区域尤其明显。

需要的是**按轴分别加权**——对每个奇异值方向施加不同惩罚。这无法用单个标量 $w_f$ 表达，但可以用 $2\times 2$ **矩阵** $W_f$ 左乘 $(J-R)$ 实现。

### 3.3 矩阵加权代理：为匹配梯度而设计

SLIM 将 ARAP 代理 $P_R(J)=\|J-R\|_F^2$ 推广为

$$
P_{R,W}(J) = \|W(J - R)\|_F^2
$$

$W$ 是仿射变换：在 $(J-R)$ 的不同方向上施加不同缩放，使代理在 $J^k$ 处与 $\mathcal{D}(J)$ **梯度一致**（而非仅能量值接近）：

$$
\nabla_J \|W(J-R)\|_F^2 \Big|_{J=J^k} = \nabla_J \mathcal{D}(J) \Big|_{J=J^k}
$$

展开左边（记 $S = J-R$）：

$$
\nabla_J \|WS\|_F^2 = \nabla_J \,\mathrm{tr}(W^T W S S^T) = (W^T W + W W^T)\, S
$$

令 $S = J^k - R^k$ 可逆（否则用伪逆），得

$$
W^T W + W W^T = \nabla_J \mathcal{D}(J)\,(J - R)^{-1}
$$

唯一解为矩阵主平方根：

$$
W = \left(\frac{1}{2}\,\nabla_J \mathcal{D}(J)\,(J - R)^{-1}\right)^{1/2}
$$

对 ARAP：$\nabla_J \mathcal{D} = 2(J-R)$，右端为 $2I$，得 $W=I$，**精确退化为标准 local/global**——说明矩阵加权是 ARAP 的自然推广，而非另起炉灶。

### 3.4 SVD 视角：矩阵权重 = 逐奇异值标量权重

旋转不变能量 $\mathcal{D}(J)$ 只依赖 $J$ 的奇异值。设 $J = USV^T$，Lemma 2 给出 $\nabla_J \mathcal{D}(J) = U\,\nabla_S \mathcal{D}(S)\,V^T$。代入式 (28)：

$$
W = U\left(\frac{1}{2}\,\nabla_S \mathcal{D}(S)\,(S-I)^{-1}\right)^{1/2} U^T = U S_W U^T
$$

**矩阵权重在旋转坐标系下是对角的**——本质上是对每个奇异值 $\sigma_i$ 分别赋权，即"逐轴标量权重"。例如对称 Dirichlet 在奇异值域的梯度为 $(\nabla_S \mathcal{D})_i = 2(\sigma_i - \sigma_i^{-3})$，得

$$
(S_W)_i = \sqrt{\frac{\sigma_i - \sigma_i^{-3}}{\sigma_i - 1}} \quad (\sigma_i \neq 1), \qquad (S_W)_i = 2 \quad (\sigma_i = 1)
$$

这才真正实现了 Stiffening/IRLS 想做而做不到的事：**沿拉伸大的轴多惩罚、沿另一轴少惩罚**。

### 3.5 与 IRLS 的对比小结

|          | Stiffening       | IRLS       | SLIM（矩阵加权）   |
| :------- | :--------------- | :--------- | :----------------- |
| 权重类型 | 标量 $w_f$       | 标量 $w_f$ | 矩阵 $W_f$         |
| 匹配目标 | 启发式加重翻转元 | 能量比值   | **梯度**           |
| 下降方向 | 不保证           | 不保证     | 实验上可靠         |
| 按轴区分 | 否               | 否         | **是**（SVD 对角） |

---

## 4. 矩阵加权代理（公式汇总）

对称 Dirichlet 在退化/翻转处为 $\infty$，**不存在**满足全局 Majorizer 的二次代理。SLIM 只要求**梯度匹配**与**最近极小点**（投影到最近旋转 $R$）一致。上节已给出从标量到矩阵的动机，这里汇总公式。

$$
P_{R,W}(J) = \|W(J - R)\|_F^2
$$

给定当前 $J^k$、$R^k$，求 $W^k$ 使（完整推导见 §3.3）：

$$
\nabla_J \|W(J - R)\|_F^2 \Big|_{J=J^k} = \nabla_J \mathcal{D}(J) \Big|_{J=J^k}
$$

推导（设 $J-R$ 可逆，否则用伪逆；细节见 §3.3）：

$$
W^T W + W W^T = \nabla_J \mathcal{D}(J)\,(J - R)^{-1}
$$

唯一解（矩阵主平方根）：

$$
W = \left(\frac{1}{2}\,\nabla_J \mathcal{D}(J)\,(J - R)^{-1}\right)^{1/2}
$$

对 ARAP：$\nabla_J \mathcal{D}_{\text{ARAP}} = 2(J-R)$，得 $W=I$，退化为标准 local/global。

---

## 5. 算法：Reweighted Local/Global

```
输入: 网格 M = (V, F)
初始化: x^0 ← Tutte(V, F)   // 无翻转初值

重复 k = 1, 2, ... 直到收敛:
  【Local】  对每个 f: R_f^k ← R(J_f(x^{k-1}))
  【Reweight】由式 (20) 更新 W_f^k
  【Global】  p^k ← argmin_x Σ_f A_f ‖W_f^k (J_f(x) - R_f^k)‖_F^2 + λ‖x - x^{k-1}‖^2
  【方向】   d^k ← p^k - x^{k-1}
  【线搜索】 x^k ← x^{k-1} + α d^k
             α_max ← 无翻转最大步长 [Smith & Schaefer 2015, §3.3]
             α ← min{0.8 α_max, 1}，在 [0, α_max] 上二分满足 Wolfe 条件
             最小化原始能量 E(x)，不含 proximal 项
```

每步解一个稀疏线性系统（Laplacian 结构，可预分解），实验上收敛到局部极小。论文未给出严格全局收敛证明（与 ARAP 相同）。

**线搜索**是关键：计算使某个三角形 $\det(J)=0$ 的临界步长 $\alpha_{\max}$，保证始终停留在可行域内——这是"给定可行初值 → 结果无翻转"的理论依据。

---

## 6. 与其他方法

| 方法                                 | 特点                        | 局限                                             |
| :----------------------------------- | :-------------------------- | :----------------------------------------------- |
| **Greedy Stiffening** [Bommes 2009]  | 逐步加重翻转元素权重        | 未达能量局部极小                                 |
| **IRLS** [Pighin & Lewis 2007]       | 标量权重局部近似            | 能量偏高（Fig. 4：$\bar{E}=8.2$ vs SLIM $10.6$） |
| **Bounded Distortion** [Lipman 2012] | 投影到扭曲有界空间          | 扭曲推向上界，非直接最小化                       |
| **L-BFGS** [Smith & Schaefer 2015]   | 通用拟牛顿 + barrier        | 迭代随网格规模增长                               |
| **AQP** [Kovalsky et al. 2016]       | Laplacian 预条件 + Nesterov | 不同路线；对 flip-preventing 能量 SLIM 更直接    |
| **SLIM**                             | 矩阵重加权 local/global     | 无严格收敛证明                                   |

Fig. 4：对称 Dirichlet 从 Tutte 初值，Stiffening $\bar{E}=2140$，IRLS $\bar{E}=8.2$，SLIM $\bar{E}=10.6$。

### 直观场景对比

| 场景                            | LSCM     | ARAP     | SLIM           |
| :------------------------------ | :------- | :------- | :------------- |
| 高曲率区域                      | 可能翻转 | 可能翻转 | **无翻转**     |
| 面积保持                        | 差       | 中等     | 可选保面积模式 |
| 角度保持                        | 好       | 中等     | 可选保角模式   |
| 带缝合约束 UV                   | 不支持   | 困难     | **原生支持**   |
| 四边形管线（Instant Meshes 等） | 不适用   | 不适用   | 广泛使用       |

---

## 7. 应用与实现

- **2D 参数化**：对称 Dirichlet、共形畸变等 flip-preventing 能量
- **3D 变形**：体网格局部单射变形
- **网格质量**：Lipman 等有界畸变能量
- **Seamless 参数化**：支持 seam 上梯度匹配（整数平移需额外处理）

**实现**：libigl `igl::slim()`；官方 C++ 支持 Eigen / PARDISO，默认对称 Dirichlet。

**实验亮点**（Fig. 2）：2500 万三角面，从高度畸变初值出发，**40 次迭代**（每次一个稀疏线性系统），80 分钟内得到低等距畸变、保证无翻转的参数化。Lucy 从 0.6M 到 10M 面，迭代次数相近——验证与细分密度解耦。

---

## 8. 总结

SLIM 的核心流程：

1. 在 **flip-preventing 能量**（对称 Dirichlet 等）上优化
2. 从标量加权（Stiffening/IRLS）**升级到矩阵加权**，使代理在 $J^k$ 处匹配目标能量梯度（§3）
3. 每步：**Local → Reweight → Global → 受限线搜索**
4. 迭代与几何复杂度相关，**与网格密度解耦** → 百万面可扩展

相比 ARAP/LSCM，SLIM 提供可依赖的**无翻转保证**和统一可扩展框架，是 Instant Meshes 等四边形网格管线的重要组件。

---

## 参考文献

- Rabinovich M., et al. *Scalable Locally Injective Mappings*. SIGGRAPH 2017.
- Liu T., et al. *A local/global approach to mesh parameterization*. CGF 2008.
- Smith J., Schaefer S. *Bijective parameterization with free boundaries*. SIGGRAPH 2015.
- Sorkine O., Alexa M. *As-rigid-as-possible surface modeling*. SGP 2007.
- Kovalsky S. Z., et al. *Accelerated Quadratic Proxy for Geometric Optimization*. SIGGRAPH 2016.
- Tutte W. T. *How to draw a graph*. Proc. London Math. Soc. 1963.
- Bommes M., et al. *Mixed-integer quadrangulation*. SIGGRAPH 2009.（Greedy Stiffening）
- Pighin F., Lewis J. P. *Practical least-squares for computer graphics*. 2007.（IRLS）

> **论文**：Shahar Z. Kovalsky, Meirav Galun, Yaron Lipman. [*Accelerated Quadratic Proxy for Geometric Optimization*](https://doi.org/10.1145/2897824.2925911). SIGGRAPH 2016.