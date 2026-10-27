以下以刘立刚老师 2008 年 ARAP 参数化为例说明。先从一个简单算法（如 Tutte）初始化，然后交替进行如下两步——首先为每个三角形寻找一个尽量保持原形状的局部近似（**Local 优化**），再回头调整 Jacobian 矩阵使网格整体保持连接（**Global 优化**）。

![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20251023215121312-1778207385711-1.png)

若矩阵 SVD 分解后两奇异值相等（$\sigma_1 = \sigma_2$），则该变换是相似变换（仅旋转+均匀缩放），由此构成的相似变换族记为 $\Omega_s$。用 Frobenius 范数量化当前 Jacobian $J_t$ 到 $\Omega_s$ 的距离：

$$
d(J_t,L_t)=||J_t-L_t||_F^2
$$

对于整个三角网格，累加所有三角形的差异得到一个如下的能量函数，这个就是我们要优化的能量函数

$$
E_{ARAP}=\sum_{t}A_t\|J_t-L_t\|_F^2,\quad L_t\in\Omega_s
\tag{4}
$$

这个优化能量有两部分是要优化的对象，其一是映射 Jacobian 矩阵 $J_t$，其二是局部优化目标 $L_t$。考虑先固定其中一个再优化另外一个，交替进行。

### 局部(Local)优化

固定当前映射的 $J_t$，对每个三角形独立寻找最优的相似变换近似 $L_t^*$：

$$
L_t^* = \arg\min_{L_t\in\Omega_s}\{d(J_t,L_t)\}
$$

注意到 $\|J_t-L_t\|_F^2=\mathrm{tr}((J_t-L_t)^T(J_t-L_t))$。这是经典的 **Procrustes 问题**：

在相似变换族 $\Omega_s=\{sR\mid s>0,\,R\in SO(2)\}$ 中，找与给定矩阵 $J_t$ Frobenius 距离最近的 $L_t$。

**Procrustes 解法.** 对 $J_t$ 作 SVD：$J_t=U\Sigma V^T$，$\Sigma=\mathrm{diag}(\sigma_1,\sigma_2)$。

但一般 SVD 只保证 $U,V$是正交的但未必是旋转矩阵。$\det(U)\det(V)=-1$ 时 $UV^T$ 含反射。

ARAP 要求 $L_t=sR$ 中的 $R$ 为保定向旋转，故需 **Signed SVD**：

若 $\det(U)\det(V)<0$，将 $\sigma_2$ 取负并翻转 $V$ 的对应列，使修正后的 $U,V\in SO(2)$。

在保定向的 SVD 下，最优相似变换可写为

$$
J_t=U\Sigma V^T,\quad \Sigma=\begin{pmatrix}\sigma_1&0\\0&\sigma_2\end{pmatrix}
\tag{5}
$$

$$
L_t^*= U \begin{pmatrix}s&0\\0&s\end{pmatrix} V^T,\quad s = \frac{\sigma_1+\sigma_2}{2}
$$

直观上：$U,V^T$ 给出 $J_t$ 的主方向（旋转），$s$ 把两个奇异值"拉平"为同一尺度。代入可得局部残差 $(\sigma_1-s)^2+(\sigma_2-s)^2$；当 $s=(\sigma_1+\sigma_2)/2$ 时取极小。

这个局部优化的效果可参看下图，其中黑色三角形是当前 $J_t$ 作用下的形状，红色三角形为最优的相似逼近 $L_t^*$。

![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20251023215506894-1778207385711-3.png)

### 全局(Global)优化

若直接令 $J_t = L_t$，各三角形独立优化后会破坏网格顶点间的连接关系——相邻三角形共用的顶点将不再重合。

![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250317141120034-1778207385711-2.png)

因此需要**Global 优化**：固定 $L_t$，在全局顶点位置 $\{u_t\}$ 上优化 $E_{ARAP}$。将上节推导的 $J_t$ 表达式代入（每个 $J_t$ 可写为该三角形三个顶点 $\{u_i, u_j, u_k\}$ 的线性函数）：

$$
\begin{aligned}
{\begin{pmatrix}{\frac{\partial u}{\partial x}}\\{\frac{\partial u}{\partial y}}\end{pmatrix} }=\frac{1}{2A_t}{\begin{pmatrix}{y_j-y_k}&{y_k-y_i}&{y_i-y_j}\\{x_k-x_j}&{x_i-x_k}&{x_j-x_i}\end{pmatrix} }
{\begin{pmatrix}u_i\\u_j\\u_k\end{pmatrix} }\\
{\begin{pmatrix}{\frac{\partial v}{\partial x}}\\{\frac{\partial v}{\partial y}}\end{pmatrix} }=\frac{1}{2A_t}{\begin{pmatrix}{y_j-y_k}&{y_k-y_i}&{y_i-y_j}\\{x_k-x_j}&{x_i-x_k}&{x_j-x_i}\end{pmatrix} }
{\begin{pmatrix}v_i\\v_j\\v_k\end{pmatrix} }
\end{aligned}
$$

可以将(2)式的能量转化为如下形式，我们优化的变量是向量 $\{u_t\}$

$$
\begin{aligned}
E_{\text{ARAP}}(u,L) = \frac{1}{2}\sum_{t=1}^T\sum_{i=0}^2\cot(\theta_t^i)\|(u_t^i-u_t^{i+1})-L_t(x_t^i-x_t^{i+1})\|^2\\
=\frac{1}{2} \sum_{he_{ij}}\cot(\theta_{ij})\|(u^i-u^j)-L_t(x^i-x^j)\|^2\\
\end{aligned}
$$

对向量 $\{u_t\}$ 求导并令其为零（寻找能量极小值的临界点），得到稀疏线性系统：

$$
\sum_{j\in N(i)}[\cot(\theta_{ij}) +\cot(\theta_{ji})](u^i-u^{j})
=\sum_{j\in N(i)}[\cot(\theta_{ij})L_{t(i,j)} +\cot(\theta_{ji})L_{t(j,i)}](x^i-x^{j})
\tag{6}
$$

最后可以求解上面的**稀疏线性方程组（Sparse Linear System）**来求得 $\{u_t\}$

### ARAP 能量即等距能量

上述 ARAP 优化的能量

$$
E_{\text{ARAP}} = \sum_{t} A_t \, \|J_t - L_t\|_F^2, \quad L_t \in \Omega_s
$$

其本质是**等距（isometry）能量**的另一种等价表述。

将 $J_t$ 的 SVD 分解记为 $J_t = U\Sigma V^\top$，其中 $\Sigma = \mathrm{diag}(\sigma_1, \sigma_2)$。则：

$$
\|J_t - L_t\|_F^2 = \|U\Sigma V^\top - U\,\hat{\Sigma}\,V^\top\|_F^2 = \|\Sigma - \hat{\Sigma}\|_F^2
$$

其中 $\hat{\Sigma} = sI$ 是相似变换对应的奇异值矩阵（均匀缩放 $s$）。展开得：

$$
\|\Sigma - sI\|_F^2 = (\sigma_1 - s)^2 + (\sigma_2 - s)^2
$$


即等距能量。



## 附录

### 三角面翻转与MIPS能量

<img src="https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250227120632868.png" alt="image-20250227120632868" style="zoom: 80%;" />

对于一些带有突出部分的曲面等复杂形状，如果参数化过程只是对共形能量或等距能量进行优化那么可能会造成**三角面的翻转**，而MIPS能量和对称Dirichlet能量都有对翻转进行惩罚。

其中MIPS（Most Isometric ParameterizationS）能量定义为奇异值之比：
$$
E_{\text{MIPS}} = \frac{\sigma_1}{\sigma_2} + \frac{\sigma_2}{\sigma_1}
$$

若直接对 $\sigma_1, \sigma_2$ 做优化，需要反复 SVD 分解且无法得到闭式梯度，难以高效求解。因此 MIPS 的关键在于**用 Jacobian 矩阵的代数不变量消去 SVD**。

利用恒等式 $\sigma_1^2 + \sigma_2^2 = \|J_t\|_F^2$ 和 $\sigma_1\sigma_2 = \det(J_t)$：

$$
E_{\text{MIPS}} = \frac{\sigma_1}{\sigma_2} + \frac{\sigma_2}{\sigma_1}
= \frac{\sigma_1^2 + \sigma_2^2}{\sigma_1 \sigma_2}
= \frac{\|J_t\|_F^2}{\det(J_t)}
$$

对每个三角形 $t$，$J_t$ 的分量是 UV 坐标的线性函数，因此 $E_{\text{MIPS}}$ 变为 UV 坐标的**有理函数**——分子是二次型，分母是三角形面积（亦为 UV 坐标的双线性形式）。

对三角网格，总能量为按面积加权的求和：

$$
E_{\text{MIPS}} = \sum_{t} A_t^{\text{3D}} \cdot \frac{\|J_t\|_F^2}{\det(J_t)}
$$

其中 $A_t^{\text{3D}}$ 是三角面片 $t$ 在原始 3D 曲面上的面积。$\det(J_t) > 0$ 保证无翻转，因此 MIPS 是**自障碍函数**（self-barrier）：翻转时 $\det(J_t) \to 0^+$ 导致能量趋于无穷大。

MIPS 与对称 Dirichlet 两者都充当翻转 barrier，但行为不同：

$$
E_{\text{MIPS}} = \frac{\sigma_1}{\sigma_2} + \frac{\sigma_2}{\sigma_1},\qquad
E_{\text{SD}} = \sigma_1^2 + \sigma_2^2 + \sigma_1^{-2} + \sigma_2^{-2}
$$

MIPS 仅阻止 $\sigma_i \to 0$（分母趋于零），而**对称 Dirichlet 同时阻止压缩（$\sigma_i \to 0$）和拉伸（$\sigma_i \to \infty$）**，因此对等距性的约束更强。在实践上，对称 Dirichlet 是更稳健的选择，但 MIPS 的化简形式 $\|J_t\|_F^2 / \det(J_t)$ 因其简洁性在教学中被广泛引用。



## 参考文献

[1] Liu, L., Zhang, L., Xu, Y., Gotsman, C., & Gortler, S. J. (2008). A local/global approach to mesh parameterization. *Computer Graphics Forum (SGP)*, 27(5), 1495–1504.

**实验链接**：https://lixiongguo.github.io/uv-unwrap-simple.html