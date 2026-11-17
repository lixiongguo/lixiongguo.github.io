## Eigen 解线性系统接口

几何处理 / libigl 代码里，稠密与稀疏系统几乎都经 **[Eigen](https://eigen.tuxfamily.org/)** 求解。统一写法是「分解器 `.compute(A)`（或构造时传入）→ `.solve(b)`」，同一分解可对多个右端项反复 `solve`。求解后应用 `solver.info() == Eigen::Success` 检查。不要写 `A.inverse() * b`（既慢又不稳）。

### 选型依赖问题语义，而非仅依赖数值外形

同一块数值矩阵（甚至同为「对称稀疏」）在几何/优化里对应的**数学问题不同**，正确求解器也不同。Eigen 无法从 entry 自动推断意图，需由建模者按结构选型：

| 问题结构                              | 代数性质                                                    | 要求解的对象                                               | 常用接口                                                     |
| ------------------------------------- | ----------------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------ |
| Laplace + 固定边界（Dirichlet）       | 离散余切 Laplace 在约束后一般为 **SPD**                     | 方阵 $A\boldsymbol{x}=\boldsymbol{b}$ 的唯一解             | 稠密 `LLT`；稀疏 `SimplicialLLT` / 实践中亦常见 `SimplicialLDLT` |
| KKT / 有约束二次规划鞍点              | 形如 $\begin{bmatrix}H&J^T\\J&0\end{bmatrix}$，**对称不定** | 同一方阵方程，但 Cholesky 会失败                           | `LDLT` / `SimplicialLDLT`；大规模宜用专门鞍点预条件或分块消元 |
| 超定拟合（ARAP 旋转拟合、点云回归等） | $A\in\mathbb{R}^{m\times n}$，$m>n$，一般 **不相容**        | $\min\|A\boldsymbol{x}-\boldsymbol{b}\|_2$，不是「解方阵」 | 稠密 `ColPivHouseholderQR`；稀疏可用 `LeastSquaresConjugateGradient`；忌盲目形成 $A^TA$ 再当 SPD 解（会平方条件数） |

**为何「看起来像」还不够**：

1. **对称 ≠ 正定**。KKT 与加约束前的纯 Neumann Laplace 都可能对称，但后者半定、前者不定——对二者调用 `LLT`/`SimplicialLLT` 会在分解阶段失败或给出不可信赖结果；应改 `LDLT` 或改约束/正则化使系统 SPD。
2. **矩形 ≠ 缺一个方阵解法**。超定问题目标是残差最小；即使用正规方程得到与 QR 相同的 $\boldsymbol{x}$（满秩时），数值路径已变成 $\kappa(A)^2$。意图是最小二乘时，接口应选 QR / LSCG，而不是先把问题捏成方阵再 `lu`/`llt`。
3. **先验来自离散化与约束**。Laplace + 充分 Dirichlet、能量 Hessian 在局部凸区域等，是建模给出的 **SPD 证书**；库无法廉价验证「全局正定」，故几何代码里常见「我们构造的是 SPD → 直接 `SimplicialLLT`」这一约定。

与后文接口表一致：**先验 SPD → Cholesky 系；对称不定 → LDLT 系；超定残差 → QR / 最小二乘迭代**——选型键是问题陈述，不是「矩阵碰巧是方的/对称的」。

### 稠密直接法

| 矩阵性质             | 对应前文       | Eigen 接口                                       | 典型写法                                                     |
| -------------------- | -------------- | ------------------------------------------------ | ------------------------------------------------------------ |
| 一般方阵             | LU             | `PartialPivLU` / `.lu()`                         | `x = A.lu().solve(b);`                                       |
| 对称正定             | Cholesky       | `LLT` / `.llt()`                                 | `x = A.llt().solve(b);`                                      |
| 对称（可不定）       | LDL$^\top$     | `LDLT` / `.ldlt()`                               | `x = A.ldlt().solve(b);`                                     |
| 矩形 / 最小二乘      | Householder QR | `HouseholderQR` / `.householderQr()`             | `x = A.householderQr().solve(b);`                            |
| 秩可能亏缺的最小二乘 | 列主元 QR      | `ColPivHouseholderQR` / `.colPivHouseholderQr()` | `x = A.colPivHouseholderQr().solve(b);`                      |
| 极病态 / 需秩揭示    | SVD            | `BDCSVD` / `JacobiSVD`                           | `x = A.bdcSvd(Eigen::ComputeThinU\|Eigen::ComputeThinV).solve(b);` |

```cpp
#include <Eigen/Dense>
using Eigen::MatrixXd;
using Eigen::VectorXd;

// SPD：离散 Laplace、正规方程 A^T A
Eigen::LLT<MatrixXd> llt(A);
VectorXd x = llt.solve(b);

// 对称不定：KKT 小块
Eigen::LDLT<MatrixXd> ldlt(A);
x = ldlt.solve(b);

// 超定最小二乘：A 为 m×n，m≥n（列主元 QR 更稳）
Eigen::ColPivHouseholderQR<MatrixXd> qr(A);
x = qr.solve(b);   // 最小化 ||A x - b||_2
```

**选用提示**：$A\succ 0$ 时优先 `LLT`；仅对称、可能不定用 `LDLT`；非对称方阵用 `PartialPivLU`；超定残差问题用 `ColPivHouseholderQR`（对应前文 Householder QR），避免先显式算 `A.transpose()*A` 再 `llt`（除非确定良态且要压榨速度）。

### 稀疏直接法与迭代法

大规模网格算子（余切 Laplace、Poisson）用 `SparseMatrix`：

| 场景            | Eigen 类                                  | 说明                          |
| --------------- | ----------------------------------------- | ----------------------------- |
| 稀疏 LU         | `SparseLU<SparseMatrix<double>>`          | 一般稀疏方阵                  |
| 稀疏 Cholesky   | `SimplicialLLT<SparseMatrix<double>>`     | SPD，几何中最常用             |
| 稀疏 LDL$^\top$ | `SimplicialLDLT<SparseMatrix<double>>`    | 对称可不定；libigl 泊松等常见 |
| CG              | `ConjugateGradient<SparseMatrix<double>>` | SPD；可设预条件               |
| BiCGSTAB        | `BiCGSTAB<SparseMatrix<double>>`          | 非对称稀疏                    |
| 最小二乘 CG     | `LeastSquaresConjugateGradient<...>`      | 超定稀疏，不显式形成 $A^TA$   |

```cpp
#include <Eigen/Sparse>
#include <Eigen/IterativeLinearSolvers>
using SpMat = Eigen::SparseMatrix<double>;

// 组装 A（Triplet）后...
Eigen::SimplicialLDLT<SpMat> solver;
solver.compute(A);
Eigen::VectorXd x = solver.solve(b);
assert(solver.info() == Eigen::Success);

// 迭代 + 不完全 Cholesky 预条件（病态 SPD）
Eigen::ConjugateGradient<SpMat, Eigen::Lower|Eigen::Upper,
                         Eigen::IncompleteCholesky<double>> cg;
cg.setMaxIterations(1000);
cg.setTolerance(1e-8);
cg.compute(A);
x = cg.solve(b);
```

**模式**：`compute` 做分解 / 预条件准备（贵）；`solve` 做回代或迭代（相对便宜）。同一 `A`、多个 `b`（多右端、多通道）应只 `compute` 一次。稀疏直接法前常配合 `AMDOrdering` / `COLAMDOrdering` 等重排序以降低 fill-in（`SimplicialLDLT` 默认已含填入友好的排序策略）。

与上文选型的对应关系：**稠密 SPD → `LLT`；稀疏网格 SPD → `SimplicialLLT`/`SimplicialLDLT`；超定拟合 → `ColPivHouseholderQR`；大规模病态 SPD → 预条件 `ConjugateGradient`**。