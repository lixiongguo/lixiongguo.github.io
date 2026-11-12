本文整理 *Instant Transport Maps on 2D Grids* (Nader, Guennebaud, 2014) 的核心思路，并结合 `cpp/OptimalTransports/gridOT_solver` 的代码实现说明。该方法针对 **2D 均匀网格域**上的 L² 最优传输，提出了一个 **无需求导（derivative-free）** 的高效算法。

这类方法适合的问题是：

> 已知单位正方形上的一个非均匀密度图，快速构造一张把该密度推到均匀分布的连续传输映射。

从代码角度看，它不是输出一个离散的运输矩阵，而是输出一张可查询的 `TransportMap`：

```cpp
Eigen::Vector2d x(0.5, 0.5);
Eigen::Vector2d y = map.fwd(x);      // 正向映射 T(x)
Eigen::Vector2d x0 = map.inv(y);     // 反向映射 T^{-1}(y)
```

所以它更像是 **求一张变形网格**，而不是求一个稀疏/稠密 transport plan 矩阵。

---

## 问题方向与符号说明

论文推导中常见两种等价写法，二者互为逆映射：

1. 从非均匀密度 $u$ 传到均匀密度 $v=1$；
2. 从均匀密度传到非均匀目标密度。

`gridOT_solver` 代码采用的是第一种方向，也就是焦散/照明设计中更常用的写法：

$$
\text{source density } u \longrightarrow \text{uniform target}.
$$

因此代码中的 `density` 更准确地说是**源密度**，也是每个 cell 的面积膨胀因子。质量守恒要求变形后的 cell 面积满足：

$$
\operatorname{area}(T(C_j)) = h^2 u_j.
$$

如果某个源 cell 的密度 $u_j$ 大，它携带的质量多；传到均匀目标后，必须占据更大的目标面积。因此代码里会让该 cell 的变形面积变大。反过来，低密度 cell 变形后面积较小。

这一点和焦散/照明设计里的直觉一致：源平面能量均匀发出，经过映射后在目标平面形成指定亮度分布。

## Monge-Ampère方程

给定源密度 $u$（定义在 $U \subset \mathbb{R}^2$）和目标密度 $v$（定义在 $V \subset \mathbb{R}^2$），最优传输映射 $T: U \to V$ 满足：

$$
M = \{ T: U \to V \mid u = v(T) \det(J_T) \}, \quad (9)
$$

其中 $J_T$ 是 $T$ 的 Jacobian 矩阵。寻求最小化 L² 传输代价的映射：

$$
c(T) = \int_U \lVert x - T(x)\rVert ^2 \, u(x) \, dx. \quad (6)
$$

Brenier 定理保证该问题存在唯一最小化映射，且可写为某个凸标量势的梯度：

$$
T(x) = \nabla \phi(x). \quad (7)
$$

代入密度保持方程 (9) 得到 **Monge-Ampère 椭圆 PDE**：

$$
u(x) = v(\nabla \phi(x)) \det(D^2 \phi(x)), \quad \forall x \in U. \quad (8)
$$



## 简化设定：焦散设计问题

不失一般性，设目标为均匀分布 $v = 1$，则方程 (8) 简化为：

$$
\det(D^2 \phi(x)) = u(x). \quad (10)
$$

在 2D 均匀网格上离散化：源密度 $u$ 为分段常数 $u = (u_1, u_2, \dots, u_n)^T$，其中 $n = h_x \times h_y$。



## Kantorovich 势与位移分解

为高效处理 Monge-Ampère 方程中的非线性项（行列式），引入 **Kantorovich 势** $\psi$，将映射分解为位移场：

$$
T(x) = x + \nabla \psi(x). \quad (12)
$$

$\psi$ 与原始凸势 $\phi$ 的关系为：

$$
\phi(x) = \frac{1}{2}\lVert x\rVert ^2 + \psi(x),
$$

对应的 Hessian 关系（在 2D 下）：

$$
H_\phi = I + H_\psi.
$$

代入方程 (10)：

$$
\det(I + H_\psi) = u(x). \quad (13)
$$

---

## 行列式与 Laplace 算子的关系

数值观察（见图3）：$\Delta \psi$ 的量级通常远大于 $\det(H_\psi)$。

![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250914180450797.png)

> **图3**：标量势 $\psi$ 的 Laplace 算子（左）与 Hessian 行列式（右）量级对比。Laplacian 主导，Hessian 行列式相对较小。

利用恒等式 $\det(I + A) = 1 + \operatorname{tr}(A) + \det(A)$（对 2×2 矩阵），方程 (13) 可写为：

$$
1 + \Delta \psi + \det(H_\psi) = u.
$$

等价地：

$$
\Delta \psi + \det(H_\psi) + 1 - u = 0. \quad (13')
$$

---

## 离散化：每个 Cell 的方程

在均匀网格上，对每个 cell $C_j$，变换后面积应满足：

$$
\operatorname{area}(T(C_j)) = h^2 u_j, \quad \forall j.
$$

利用散度定理，变换后面积可近似为：

$$
\operatorname{area}(T(C_j)) \approx h^2 \left( \Delta \psi + \det(H_\psi) + 1 \right)_j.
$$

从而得到离散方程（每个 cell 一个方程）：

$$
\mathcal{F}_j(\psi) = \left( \Delta \psi + \det(H_\psi) + 1 - u \right)_j = 0. \quad (15)
$$

其中 $\Delta \psi$ 可用标准有限差分近似，$\det(H_\psi)$ 可用 cell 四角梯度向量构成的四边形**有向面积**计算：

$$
q_j = \det(J_T(x_j)) = \det(H_\psi(x_j)) \approx \frac{1}{2} Q_j.
$$

$Q_j$ 为由 $\nabla \psi$ 在 cell 四角的值定义的四边形有向面积。

更直观地说，代码并不会真的显式计算每个 cell 上的 $H_\psi$，而是直接看这个 cell 被映射后变成了多大的四边形。

设一个规则 cell 的四个角为：

$$
x_{00},x_{10},x_{11},x_{01}.
$$

映射后四个角变成：

$$
T(x_{ab})=x_{ab}+\nabla\psi(x_{ab}).
$$

于是 cell 的面积变化可以直接通过变形后四边形的有向面积得到。这个做法比显式离散 Hessian 更稳定，也更贴近几何：最优传输的质量守恒本质上就是面积守恒/面积匹配。

所以本文后面会把残差写成：

$$
r_j(\psi)=\operatorname{area}(T(C_j))-h^2u_j.
$$

这和方程

$$
\Delta \psi+\det(H_\psi)+1-u=0
$$

是同一件事的两个视角：

- PDE 视角：Jacobian 行列式匹配密度；
- 代码视角：每个源 cell 携带的质量，匹配它在均匀目标中的占据面积。



## Newton 法求解

方程 (15) 是全非线性系统，可用 Newton 法迭代求解。每一步需求解线性化系统：

$$
\Delta \psi^{(k+1)} + A(\psi^{(k)}) : D^2(\delta \psi) = u - 1 - \det(H_{\psi^{(k)}}),
$$

其中 $A = \operatorname{cof}(I + H_\psi)$ 为余因子矩阵。



## 代码实现：`gridOT_solver`

`cpp/OptimalTransports/gridOT_solver` 中的实现并没有直接组装完整 Newton 线性化矩阵，而是采用论文 *Instant Transport Maps on 2D Grids* 的 **derivative-free** 思路：用固定的伪 Laplacian 作为主要求解方向，再用共轭 Jacobian 方向和一维精确线搜索处理非线性的面积项。

这个目录主要由两部分组成：

- `otsolver_2dgrid.h/.cpp`：负责求解 $\psi$，并生成变形后的网格；
- `transport_map.h/.cpp`：把原始网格和变形网格封装成可查询的映射对象。

核心类是：

```cpp
otmap::GridBasedTransportSolver solver;
solver.init(n);
otmap::TransportMap map = solver.solve(density);
```

其中 `density` 是长度为 $n^2$ 的源密度向量，也就是每个 cell 在均匀目标中的面积膨胀因子，按 cell 顺序展开：

$$
\mathrm{id}(i,j)=j+i n.
$$

代码中对应：

```cpp
inline int make_face_index(int i, int j) const { return j+i*m_gridSize; }
```

这里先介绍原始 `GridBasedTransportSolver` 的调用方式，因为它最贴近论文实现；若在外部系统中使用统一 `ot::Solver` 接口，则需要注意适配层采用的源/目标约定。

### 参数含义

`SolverOptions` 控制迭代行为：

```cpp
struct SolverOptions
{
  BetaOpt beta = BetaOpt::ConjugateJacobian;
  int max_iter = 1000;
  double threshold = 1e-7;
  double max_ratio = std::numeric_limits<double>::max();
};
```

各参数含义如下：

- `beta`：搜索方向策略。`Zero` 表示只用伪 Laplacian 方向；`ConjugateJacobian` 会加入共轭 Jacobian 修正，通常收敛更快；
- `max_iter`：最大迭代次数；
- `threshold`：残差平方归一化后的停止阈值；
- `max_ratio`：限制源密度最大/最小比值，避免极端密度导致网格折叠或线搜索困难。

### 1. 输入密度归一化

在 `adjust_density()` 中，代码先把源密度归一化为总质量 1：

$$
\sum_j u_j h^2 = 1.
$$

对应代码逻辑为：

```cpp
double I = density.sum()*m_element_area;
density /= I;
```

这里：

$$
h^2 = \texttt{m\_element\_area} = \frac{1}{n^2}.
$$

也就是说，代码实际求的是：

> 将单位正方形上的非均匀源密度 `density`，传输到均匀目标分布。

如果源密度的最大/最小比值太大，`max_ratio` 还会对密度做一次平滑式调整，避免数值上出现过于尖锐的分布。

### 2. 网格与未知量

`init(n)` 做三件事：

1. 建立 $(n+1)\times(n+1)$ 的规则四边形网格；
2. 设置 cell 数量 $n^2$；
3. 预组装并分解伪 Laplacian 矩阵。

未知量 $\psi$ 存在 cell 上，因此有 $n^2$ 个自由度。梯度 $\nabla\psi$ 则计算在顶点上：

```cpp
VectorXd xk = VectorXd::Zero(n);        // cell 上的 ψ
MatrixX2d vtx_grads;                    // 顶点上的 ∇ψ
```

映射为：

$$
T(x)=x+\nabla\psi(x).
$$

所以最终输出不是直接返回 $\psi$，而是把原始网格顶点加上顶点梯度，得到变形后的 mesh：

```cpp
forward_mesh->points()[j] += m_cache_residual_vtx_grads.row(j).transpose();
return TransportMap(m_mesh, forward_mesh, p_density);
```

### 3. 伪 Laplacian 预条件方向

代码在 `initialize_laplacian_solver()` 中组装一个固定的伪 Laplacian 矩阵。它不是标准五点 stencil，而是作用在 cell 中心的对角邻域：

$$
\frac14
\begin{bmatrix}
2 & 0 & 2\\
0 & -8 & 0\\
2 & 0 & 2
\end{bmatrix}.
$$

代码中为了直接得到正定系统，实际组装的是 $-L$：

```cpp
double w = -0.5;
L_entries.push_back(Triplet(id, make_face_index(row_id_1, col_id_1), w));
L_entries.push_back(Triplet(id, make_face_index(row_id_1, col_id_2), w));
L_entries.push_back(Triplet(id, make_face_index(row_id_2, col_id_1), w));
L_entries.push_back(Triplet(id, make_face_index(row_id_2, col_id_2), w));
L_entries.push_back(Triplet(id, id, -sw));
```

由于 $\psi$ 加常数不改变 $\nabla\psi$，Laplacian 有一个常数零空间。代码通过弱约束固定一个自由度：

```cpp
m_mat_L.coeffRef(0,0) += std::abs(m_mat_L.coeffRef(0,0))*1e4;
```

之后用 Cholesky / LDLT 预分解，迭代中反复求解：

$$
d_{\mathrm{hat}} = (-L)^{-1} r.
$$

并投影掉常数方向：

```cpp
d_hat = m_laplacian_solver.solve(rk);
d_hat.array() -= d_hat.mean();
```

这一步可以理解为：用 Poisson 方程给残差做一个平滑的修正方向。

### 4. 残差：变形后面积 - 源 cell 质量

理论上的离散方程是：

$$
\operatorname{area}(T(C_j)) = h^2 u_j.
$$

代码里的残差正是：

$$
r_j(\psi)=\operatorname{area}(T(C_j))-h^2u_j.
$$

实现位置是 `compute_residual()`：

```cpp
compute_vertex_gradients(psi, vtx_grads);
compute_face_area(fwd_area, vtx_grads, m_gridSize);
out = fwd_area - m_element_area* (*m_input_density);
return out.squaredNorm() / m_element_area;
```

其中 `compute_face_area()` 用变形后四边形的两条对角线叉乘计算面积：

$$
\operatorname{area}(Q)=\frac12 (d_1 \times d_2).
$$

代码中的 `+e` 和 `-e` 表示原始规则网格 cell 的边长：

$$
e = \frac{1}{n}.
$$

因此 `vtx_grads` 只存位移 $\nabla\psi$，真正的顶点位置是：

$$
x+\nabla\psi(x).
$$

### 4.1 顶点梯度如何由 cell 势得到

`psi` 定义在 cell 上，而映射要移动网格顶点，因此需要把 cell 上的标量势转成顶点上的梯度。代码里的 `compute_vertex_gradients()` 对内部顶点使用相邻四个 cell 的差分：

```cpp
vtx_grads(vid+j,0) = 0.5*w*(p10+p11-p00-p01);
vtx_grads(vid+j,1) = 0.5*w*(p01+p11-p00-p10);
```

其中：

$$
w=n=\frac{1}{h}.
$$

这相当于在顶点处用周围四个 cell 的中心势值估计：

$$
\partial_x\psi,\qquad \partial_y\psi.
$$

边界上没有完整的四邻域，所以代码使用单侧差分，并把四个角点位移设为 0：

```cpp
vtx_grads.row(make_vtx_index(0,0)).setZero();
vtx_grads.row(make_vtx_index(m_gridSize,0)).setZero();
vtx_grads.row(make_vtx_index(0,m_gridSize)).setZero();
vtx_grads.row(make_vtx_index(m_gridSize,m_gridSize)).setZero();
```

这等价于给边界施加较弱的稳定约束，使映射不会因为势函数常数自由度和边界不确定性而整体漂移。

### 5. 共轭 Jacobian 方向

基础方向 $d_{\mathrm{hat}}$ 只用了固定 Laplacian，不能完全表达非线性 Monge-Ampère 项。代码可选择使用 `BetaOpt::ConjugateJacobian`，把当前方向和上一步方向组合：

$$
d_k=d_{\mathrm{hat}}+\beta d_{k-1}.
$$

对应：

```cpp
beta = compute_conjugate_jacobian_beta(xk,rkm1,rk,d_hat,d,alpha);
d = d_hat + beta*d;
```

`compute_conjugate_jacobian_beta()` 用有限差分估计 Jacobian 对方向的作用，避免显式组装完整 Jacobian。这就是 derivative-free 的关键之一。

### 6. 精确一维线搜索

确定方向 $d$ 后，代码不是随便取步长，而是利用面积残差沿直线：

$$
\psi(t)=\psi_k+t d
$$

的特殊结构。由于 cell 面积由四边形叉乘给出，而顶点位置对 $t$ 是线性的，所以每个 cell 的残差是关于 $t$ 的二次多项式：

$$
r(\psi_k+t d)=r_k+b t+a t^2.
$$

因此误差平方：

$$
E(t)=\lVert r_k+b t+a t^2\rVert ^2
$$

是四次多项式。代码在 `compute_1D_problem_parameters()` 中求每个 cell 的 $a,b$，然后在 `solve_1D_problem()` 中构造四次多项式系数：

```cpp
z <<  ek*m_element_area,
      2.*b.dot(rk),
      b.squaredNorm()+2*a.dot(rk),
      2.*a.dot(b),
      a.squaredNorm();
```

再求导得到三次多项式：

$$
E'(t)=0.
$$

代码用 companion matrix 求三次方程根，选择使残差最小的实根作为步长 `alpha`：

```cpp
EigenSolver<Matrix3d> eig(C);
xk1 = xk + alpha * dir;
rk1 = a*(alpha*alpha)+b*alpha+rk;
```

这就是该算法速度快的重要原因：一维线搜索是解析的，不需要反复试探很多次。

从几何上看，这一步很漂亮：因为每个顶点位置对 $\alpha$ 是线性的，而四边形面积是两个向量叉乘，所以面积对 $\alpha$ 最多是二次；所有 cell 的误差平方求和自然变成四次多项式。因此线搜索不是“数值试步”，而是利用了网格面积公式的代数结构。

### 7. 输出 `TransportMap`

迭代结束后，代码重新计算最终顶点梯度，把原始网格顶点移动到目标位置：

```cpp
compute_vertex_gradients(xk, m_cache_residual_vtx_grads);
auto forward_mesh = std::make_shared<Surface_mesh>(*m_mesh);
for(unsigned int j=0; j<m_cache_residual_vtx_grads.rows(); ++j)
  forward_mesh->points()[j] += m_cache_residual_vtx_grads.row(j).transpose();
```

`TransportMap` 保存两张网格：

1. `origin_mesh`：原始规则网格；
2. `fwd_mesh`：由 $x+\nabla\psi(x)$ 得到的变形网格。

之后可以调用：

```cpp
map.fwd(p);       // 正向映射
map.inv(p);       // 反向映射
map.inv_fast(p);  // 加速反向映射
```

内部通过网格/BVH 找到点所在面片，并在对应四边形中插值。

### 8. 与理论公式的对应关系

| 理论对象 | 代码变量/函数 |
|---|---|
| 网格大小 $n$ | `m_gridSize` |
| cell 数量 $n^2$ | `m_pb_size` |
| cell 面积 $h^2$ | `m_element_area` |
| 源密度 $u_j$ / 面积因子 | `m_input_density` |
| Kantorovich 势 $\psi$ | `xk` |
| 顶点梯度 $\nabla\psi$ | `compute_vertex_gradients()` / `m_cache_residual_vtx_grads` |
| 变形后 cell 面积 | `compute_face_area()` |
| 残差 $r_j=\operatorname{area}(T(C_j))-h^2u_j$ | `compute_residual()` |
| 伪 Laplacian | `m_mat_L` |
| 预条件方向 | `d_hat = m_laplacian_solver.solve(rk)` |
| 共轭方向 | `d = d_hat + beta*d` |
| 精确线搜索步长 | `solve_1D_problem()` |
| 最终映射 | `TransportMap::fwd()` |

因此，代码层面的算法流程更准确地写成：

1. `init(n)`：建立规则网格，预组装并分解伪 Laplacian；
2. `adjust_density()`：归一化源密度；
3. 从 $\psi=0$ 开始；
4. `compute_residual()`：计算当前变形后 cell 面积与源 cell 质量的差；
5. 解 Poisson 型系统得到初始搜索方向；
6. 用共轭 Jacobian 修正搜索方向；
7. 沿该方向做解析一维线搜索；
8. 更新 $\psi$，直到残差小于阈值；
9. 输出 $T(x)=x+\nabla\psi(x)$ 对应的 `TransportMap`。

## 一个完整调用例子

下面例子构造一个 $64\times64$ 的源密度，把它传输到单位正方形上的均匀分布：

```cpp
#include "gridOT_solver/otsolver_2dgrid.h"

#include <Eigen/Dense>
#include <cmath>
#include <cstdio>

int main()
{
    const int n = 64;
    Eigen::VectorXd density(n * n);

    // 源密度：中心附近质量更大，边缘较小
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            const double x = (j + 0.5) / n;
            const double y = (i + 0.5) / n;
            const double dx = x - 0.5;
            const double dy = y - 0.5;
            density(j + i * n) =
                std::exp(-(dx * dx + dy * dy) / (2.0 * 0.15 * 0.15)) + 1e-3;
        }
    }

    otmap::GridBasedTransportSolver solver;
    solver.set_verbose_level(1);
    solver.init(n);

    otmap::SolverOptions opt;
    opt.max_iter = 1000;
    opt.threshold = 1e-7;
    opt.beta = otmap::BetaOpt::ConjugateJacobian;

    otmap::TransportMap map = solver.solve(density, opt);

    Eigen::Vector2d p(0.5, 0.5);
    Eigen::Vector2d q = map.fwd(p);
    std::printf("T(0.5, 0.5) = (%f, %f)\n", q.x(), q.y());
    return 0;
}
```

如果源密度来自灰度图，需要先把图像灰度采样成 `density(j+i*n)`。注意 `solve()` 内部会自动归一化总质量，所以输入灰度不一定需要预先使积分为 1，但必须非负，并且最好不要有严格的 0 值。

## 方法特点与适用范围

这个栅格 OT 方法的优点：

- **速度快**：Laplacian 矩阵只分解一次，迭代中反复复用；
- **不显式组装完整 Jacobian**：用共轭 Jacobian 和线搜索吸收非线性；
- **输出连续映射**：不是只有 cell-to-cell 的离散匹配，而是可查询任意点的 `fwd()` / `inv()`；
- **适合图像/焦散设计**：输入天然是规则网格密度。

限制也比较明显：

- 主要适用于 **二维单位方形规则网格**；
- 源密度过尖锐时，可能需要用 `max_ratio` 平滑密度；
- 映射质量依赖网格分辨率，细节受 $n$ 限制；
- 输出是由变形四边形网格插值得到的映射，并非解析闭式解；
- 若要求从任意连续源密度到离散点集，应该使用半离散 OT；若要求两幅图像之间的密度流，也可以考虑 AHT/Benamou 类型方法。

## 与其他两个实现的关系

当前 `cpp/OptimalTransports` 中有三类 OT 求解器：

- `gridOT_solver`：栅格源密度 $\rightarrow$ 均匀目标，输出连续网格映射；
- `SemiOT_solver`：栅格源密度 $\rightarrow$ 带权点集，输出 Laguerre/Power 图对应的半离散映射；
- `BenamouOT_solver`：栅格密度 $\rightarrow$ 栅格密度，基于 AHT/Benamou 思路迭代消旋，输出稠密位移/映射场。

三者都可以理解为在求 $T_\#\mu=\nu$，但离散方式不同：

- gridOT 把未知势 $\psi$ 放在 cell 上，把映射表示为变形网格；
- SemiOT 把目标写成 Dirac 点，把映射表示为 Laguerre 单元分割；
- Benamou/AHT 在两个图像密度之间直接求稠密映射场。

因此选择时可以按输入/输出形态判断：

- 目标是图像密度，希望得到规则网格上的连续变形：选 `gridOT_solver`；
- 目标是采样点/质点：选 `SemiOT_solver`；
- 两端都是图像，并且希望得到类似 image morphing 的稠密映射：选 `BenamouOT_solver`。



## 总结：算法流程

1. 初始化 $\psi = 0$；
2. 根据 $\psi$ 计算顶点位移 $\nabla\psi$；
3. 由变形后四边形面积计算残差
   $$
   r_j=\operatorname{area}(T(C_j))-h^2u_j;
   $$
4. 解伪 Laplacian 系统得到初始搜索方向；
5. 用共轭 Jacobian 修正方向；
6. 沿该方向做精确一维线搜索，更新 $\psi$；
7. 重复直到残差小于阈值；
8. 输出传输映射
   $$
   T(x)=x+\nabla\psi(x).
   $$
