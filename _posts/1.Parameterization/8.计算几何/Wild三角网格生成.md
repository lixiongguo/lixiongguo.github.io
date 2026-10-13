#### "In the Wild" 网格生成：TetWild / fTetWild / TriWild

传统网格生成方法（如 TetGen）要求输入是"干净"的——水密、流形、无自交。然而在实际应用中，从三维扫描、CAD 导出、网络下载等渠道获取的网格往往是**"野生"的（in the wild）**：可能包含非流形边、自相交面片、孔洞、重复面片等各种缺陷。NYU 的 Daniele Panozzo 团队（Yixin Hu, Teseo Schneider 等）提出了一系列突破性的工作，实现了**对任意输入网格的无条件鲁棒网格生成**。

![In the Wild 网格生成流水线](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/wild_meshing_pipeline.svg)

##### TetWild：无条件鲁棒的四面体网格生成

**TetWild**（Hu et al., SIGGRAPH 2018）是这一方向的奠基工作，其核心贡献在于：

> **给定任意三角面片集合（triangle soup），无需用户交互，自动生成分析就绪（analysis-ready）的高质量四面体网格。**

**核心设计——ε-Envelope（包络）**：

TetWild 引入了**特征包络（feature envelope）** 的概念，这是其鲁棒性的关键：

$$\text{Envelope}_\epsilon(\partial \Omega) = \{ x \in \mathbb{R}^3 : d(x, \partial \Omega) \leq \epsilon \}$$

其中 $\epsilon$ 是用户设定的容差参数。TetWild 保证：

1. **输入面片保留**：所有输入三角形（经修复后）都在输出四面体网格的面中被保留
2. **包络约束**：输出网格的边界面位于输入表面网格的 $\epsilon$-包络内
3. **质量保证**：所有四面体满足有界的 AMIPS 能量（见下文）

**算法流水线**：

```
输入: Triangle Soup（任意三角面片集合）
输出: 高质量四面体网格

1. 预处理（Preprocessing）
   - 去除重复面片和退化面片
   - 一致化法向量
   - 识别并修复自相交区域

2. 四面体化（Tetrahedralization）
   - 使用有理数运算（exact arithmetic）确保鲁棒性
   - 基于 BSP 树（Binary Space Partitioning）加速空间查询
   - 增量插入输入三角形的边和面

3. 网格优化（Mesh Improvement）
   - 使用 AMIPS 能量作为质量度量
   - 顶点平滑（Smoothing）
   - 边翻转（Edge Flip）和面交换（Face Swap）
   - 边分裂（Edge Split）和边折叠（Edge Collapse）
   - 过滤违反包络约束的无效元素
   - 迭代直到所有四面体满足质量阈值
```

**AMIPS 能量（Approximated Minimal Isotropic Sigmoidal Energy）**：

TetWild 使用 AMIPS 能量作为四面体质量的统一度量。对于四面体 $T$，其 AMIPS 能量为：

$$E_{\text{AMIPS}}(T) = \frac{|T|^{2/3}}{3} \sum_{i=1}^{3} \sigma_i + \frac{3}{\sigma_i} - 4$$

其中 $\sigma_i$ 是 Jacobi 矩阵的奇异值。AMIPS 能量的性质：

- **下界为 3**（对应正四面体）
- **值越大质量越差**
- **可微**，便于梯度优化
- **各向同性**（isotropic），不偏向任何特定方向

**TetWild 的理论保证**：

| 保证           | 说明                                            |
| :------------- | :---------------------------------------------- |
| **无条件终止** | 算法对任何输入都保证终止                        |
| **水密输出**   | 输出网格一定是封闭的、流形的                    |
| **有界质量**   | 所有四面体的 AMIPS 能量有上界                   |
| **几何逼近**   | 输出面与输入面的 Hausdorff 距离 $\leq \epsilon$ |

**TetWild 的局限**：

- 使用**有理数算术**（rational arithmetic），计算开销较大
- 运行速度相对较慢
- 有理数坐标的网格在转换为浮点坐标后**可能不再是有效的**

---

##### fTetWild：快速的鲁棒四面体网格生成

**fTetWild**（Hu, Schneider, Wang et al., SIGGRAPH 2020）是 TetWild 的加速版本，在保持鲁棒性的同时大幅提升了速度。

**核心改进——用浮点运算替代有理数运算**：

fTetWild 的关键洞察是：通过**交错构建与优化**的策略，可以在全程使用**浮点运算**的同时保持鲁棒性，无需代价高昂的有理数精确计算。

> **核心思想**：不是先插入所有三角形再全局优化，而是**每插入一个输入三角形后立即进行局部优化**，始终保持一个合法的浮点四面体网格。

**增量交错流水线**：

```
不同于 TetWild 的 "先插入 → 后优化"：

TetWild:  [插入全部三角形] → [全局优化]
fTetWild: [插入△₁] → [局部优化] → [插入△₂] → [局部优化] → ...
```

这个交错策略带来两个关键优势：

1. **保持网格有效性**：每次局部优化后，网格始终是合法的浮点四面体网格
2. **避免精度累积**：局部问题在局部解决，不会累积成全局的数值退化

**fTetWild vs TetWild 详细对比**：

| 维度             | TetWild                            | fTetWild                                       |
| :--------------- | :--------------------------------- | :--------------------------------------------- |
| **算术精度**     | 有理数（精确但昂贵）               | 浮点数（快速）                                 |
| **速度**         | 基准                               | **~10x 加速**                                  |
| **网格有效性**   | 有理数坐标有效，浮点转换后可能无效 | **浮点坐标直接有效**                           |
| **输入面片保留** | 保证所有面片都被保留               | 实际中几乎全部保留（理论上不保证）             |
| **新增功能**     | —                                  | 布尔运算（并/交/差）、背景尺寸场、开放边界平滑 |
| **质量保证**     | AMIPS 能量有界                     | 同样的质量保证                                 |
| **大规模数据集** | Thingi10K 测试通过                 | Thingi10K 全部成功                             |

**布尔运算**：

fTetWild 新增了对多个输入网格直接执行布尔运算的能力：

```bash
# 并集
./fTetWild -i mesh1.obj mesh2.obj -o union --op 0
# 交集
./fTetWild -i mesh1.obj mesh2.obj -o intersection --op 1
# 差集
./fTetWild -i mesh1.obj mesh2.obj -o difference --op 2
```

这使得 fTetWild 特别适合 CAD/CAE 工作流中的几何处理。

**关键参数**：

| 参数            | 含义                           | 默认值 |
| :-------------- | :----------------------------- | :----- |
| `-l, --lr`      | 理想边长（= 包围盒对角线 × l） | 0.05   |
| `-e, --epsr`    | 包络厚度（= 包围盒对角线 × e） | 1e-3   |
| `--stop-energy` | AMIPS 能量停止阈值             | 10     |
| `--max-its`     | 最大优化迭代次数               | 80     |
| `--bg-mesh`     | 外部背景网格（局部尺寸控制）   | —      |

---

##### TriWild：鲁棒的二维约束三角剖分

**TriWild**（Hu, Schneider, Gao et al., SIGGRAPH 2019）是 "In the Wild" 框架的二维版本，支持带有**曲线约束**的鲁棒三角剖分。

**核心特性——曲线约束**：

与传统的二维约束 Delaunay 三角剖分（只能处理直线段约束）不同，TriWild 能够直接处理**参数曲线**（如 Bézier 曲线）作为约束：

| 约束类型     | 输入格式               | 说明                 |
| :----------- | :--------------------- | :------------------- |
| **线性约束** | `.obj`（线段集合）     | 传统 PSLG            |
| **曲线约束** | `.json`（Bézier 曲线） | 参数曲线作为约束边界 |

**算法流程**：

```
输入: 线段集合 + Bézier 曲线集合
输出: 满足约束的高质量三角网格

1. 曲线采样：将 Bézier 曲线离散为高密度线段
2. 构建 ε-Envelope：确保采样后的线段在包络内逼近原始曲线
3. 增量三角剖分：交错插入线段和局部优化
4. AMIPS 能量优化：保证三角形质量
5. 输出：线性网格或高阶网格（保留曲线信息）
```

**特征包络与曲线逼近**：

TriWild 使用**相对特征包络参数** `feature-envelope-r` 控制曲线逼近精度：

$$d_{\text{Hausdorff}}(\text{output}, \text{input curves}) \leq \epsilon$$

其中 $\epsilon$ 由用户设定的相对容差决定：

- 线性约束默认：`feature-envelope-r = 1e-3`
- 曲线约束默认：`feature-envelope-r = 2e-3`

**输出模式**：

TriWild 支持两种输出模式：

1. **线性网格**（`--output-linear-mesh`）：将曲线约束近似为直线段的三角剖分
2. **高阶网格**：在三角形的边上存储曲线参数信息，实现精确的曲线表示

**TriWild 的意义**：

TriWild 解决了二维约束三角剖分中长期存在的一个问题——如何鲁棒地处理曲线约束。传统方法需要先将曲线离散为大量小线段（可能导致网格过密或约束丢失），而 TriWild 通过包络机制在精度和效率之间取得了良好的平衡。

---

##### Wild Meshing 家族的统一框架

TetWild、fTetWild、TriWild 共同构成了 **"Wild Meshing"** 家族，其统一的核心理念是：

> **不再要求输入是"完美"的几何体，而是在算法内部自动处理所有输入缺陷，对用户完全透明。**

**统一的设计原则**：

1. **ε-Envelope 作为几何逼近的核心约束**：所有方法都使用包络约束来控制输出与输入的偏差
2. **AMIPS 能量作为质量度量**：统一的能量函数驱动网格优化
3. **浮点运算 + 局部优化 = 鲁棒性**：fTetWild 和 TriWild 证明了浮点运算配合局部优化可以达到与精确算术同等的鲁棒性
4. **无条件终止**：对任何输入都保证算法终止
5. **黑盒分析**：用户只需提供几何模型和容差参数，无需了解网格生成的内部细节

**与其他方法的对比**：

| 方法             | 输入要求           | 鲁棒性               | 速度           | 质量保证           |
| :--------------- | :----------------- | :------------------- | :------------- | :----------------- |
| **TetGen**       | 干净的水密网格     | ❌ 对缺陷输入可能失败 | 快             | 角度/半径-边比有界 |
| **CGAL 3D Mesh** | 干净的 PSLG        | ❌ 需要预处理         | 中等           | Delaunay 质量保证  |
| **TetWild**      | 任意 triangle soup | ✅ 无条件鲁棒         | 较慢（有理数） | AMIPS 有界         |
| **fTetWild**     | 任意 triangle soup | ✅ 无条件鲁棒         | ✅ 快（浮点）   | AMIPS 有界         |
| **TriWild**      | 线段 + 曲线        | ✅ 无条件鲁棒         | 快             | AMIPS 有界         |

**参考文献**：

- Hu, Y., Zhou, Q., Gao, X., Jacobson, A., Zorin, D., & Panozzo, D. (2018). [Tetrahedral meshing in the wild](https://dl.acm.org/doi/10.1145/3197517.3201353). *ACM Trans. Graph.* (SIGGRAPH)
- Hu, Y., Schneider, T., Wang, B., Zorin, D., & Panozzo, D. (2020). [Fast tetrahedral meshing in the wild](https://dl.acm.org/doi/10.1145/3386569.3392385). *ACM Trans. Graph.* (SIGGRAPH)
- Hu, Y., Schneider, T., Gao, X., Zhou, Q., Jacobson, A., Zorin, D., & Panozzo, D. (2019). [TriWild: Robust triangulation with curve constraints](https://cs.nyu.edu/~yixinhu/triwild.pdf). *ACM Trans. Graph.* (SIGGRAPH)

---

### 三角网格的光顺与简化