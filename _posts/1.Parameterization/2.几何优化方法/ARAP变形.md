# ARAP 变形（As-Rigid-As-Possible）

三角网格 $S=(\mathbf{P},E)$：静止顶点 $\mathbf{p}_i$，变形后的未知顶点 $\mathbf{p}'_i$（$i=1,\ldots,n$），边 $(i,j)\in E$，$N(i)$ 为顶点 $i$ 的一环邻居。每个顶点配一个未知旋转 $\mathbf{R}_i\in SO(3)$。手柄顶点要求 $\mathbf{p}'_k=\mathbf{q}_k$，$\mathbf{q}_k$ 为用户拖到的位置。

$$
E(S')=\sum_{i=1}^{n} w_i \sum_{j\in N(i)} w_{ij}\lVert(\mathbf{p}'_i-\mathbf{p}'_j)-\mathbf{R}_i(\mathbf{p}_i-\mathbf{p}_j)\rVert ^2
$$

- 权重取余切权 $w_{ij}=\frac{1}{2}(\cot\alpha_{ij}+\cot\beta_{ij})$，$\alpha_{ij},\beta_{ij}$ 为边 $(i,j)$ 两侧的对角；
- $w_i=\bigl(\sum_{j\in N(i)} w_{ij}\bigr)^{-1}$ 做归一化，使每个顶点的邻域权之和为 1，否则顶点度数与采样密度会带来偏置；归一化后 $w_i$ 可直接并入 $w_{ij}$。它抹平的是每个邻域**内部**的尺度，逐顶点求和对分辨率的依赖仍在（见 §5）。

含义：把每个顶点的**一环邻域**用一个刚性变换（旋转 $\mathbf{R}_i$ 加隐式平移）去近似。由此得到两点：
- **全局旋转不变**：整体施加同一旋转 $\mathbf{Q}$ 时，取 $\mathbf{R}_i=\mathbf{Q}$ 即可让能量为零；
- **局部刚性**：$\mathbf{R}_i$ 逐顶点独立，故形状各部分能各自旋转——这就是*尽可能刚性*。

> **为何按顶点而非按面**：$\mathbb{R}^3$ 中的三角网格余维为 1，按面分配旋转无法度量沿边的弯曲，结果会"起皱"；余维为 0 的单元（平面三角网格、四面体）才可以按面/按单元分配——参数化中的 local/global（[Liu et al. 2008]）正是按三角形分配。

对实体形状，还有一个等价的连续写法：把变形梯度 $\mathbf{F}:=\mathbf{I}+\nabla\mathbf{d}$（$\mathbf{d}=\mathbf{p}'-\mathbf{p}$ 为位移）与最近旋转比较，$\int\lVert\mathbf{F}-\mathbf{R}\rVert ^2\,dA$ 即共旋线弹性（[Chao et al. 2010]）。

![大旋转下的 ARAP 变形](../../../imgs/knight-arap-large-rotation.gif)

## 局部步：求每个顶点的最优旋转

固定所有 $\mathbf{p}'_i$，各 $\mathbf{R}_i$ 相互独立。能量中对 $\mathbf{R}_i$ 有贡献的部分为

$$
\sum_{j\in N(i)} w_{ij}\lVert(\mathbf{p}'_i-\mathbf{p}'_j)-\mathbf{R}_i(\mathbf{p}_i-\mathbf{p}_j)\rVert ^2
=\text{const}-2\operatorname{tr}\bigl(\mathbf{R}_i\mathbf{S}_i\bigr),
$$

其中 $\mathbf{S}_i$ 是加权协方差矩阵

$$
\mathbf{S}_i=\sum_{j\in N(i)} w_{ij}\,(\mathbf{p}_i-\mathbf{p}_j)(\mathbf{p}'_i-\mathbf{p}'_j)^{\mathsf T}.
$$

最大化 $\operatorname{tr}(\mathbf{R}_i\mathbf{S}_i)$

对 $\mathbf{S}_i=\mathbf{U}_i\Sigma_i\mathbf{V}_i^{\mathsf T}$ 做 SVD，取
$$
\mathbf{R}_i=\mathbf{V}_i\mathbf{U}_i^{\mathsf T}.
$$

## 全局步：解一个线性系统

固定所有 $\mathbf{R}_i$，令 $\partial E/\partial \mathbf{p}'_i=0$，得逐顶点的 Poisson 方程

$$
\sum_{j\in N(i)} w_{ij}\,(\mathbf{p}'_i-\mathbf{p}'_j)
=\sum_{j\in N(i)} \frac{w_{ij}}{2}\,(\mathbf{R}_i+\mathbf{R}_j)(\mathbf{p}_i-\mathbf{p}_j).
$$

右端只依赖上一步的旋转，视作已知量；左端是标准的 Laplace 结构（余切 Laplacian × 顶点坐标），把三个坐标分量并列即得一个稀疏线性系统。加上手柄约束 $\mathbf{p}'_k=\mathbf{q}_k$ 后解之。
