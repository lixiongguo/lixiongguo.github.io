---
layout: post
title: "TinyAD — 几何处理中的前向自动微分"
categories: ["Parameterization", "Parameterization-GeometricOptimization"]
mathjax: true
---

> **论文**：P. Schmidt, J. Born, D. Bommes, M. Campen, L. Kobbelt. [*TinyAD: Automatic Differentiation in Geometry Processing Made Simple*](https://doi.org/10.1111/cgf.14787). *Computer Graphics Forum* 41(5), SGP 2022.  
> **代码**：[github.com/patr-schm/TinyAD](https://github.com/patr-schm/TinyAD) · [TinyAD-Examples](https://github.com/patr-schm/TinyAD-Examples)

## 概述

网格参数化、形变、方向场、配准等任务的核心往往是**非线性优化**。研究迭代中需要反复改动目标函数与求解器，但手写梯度与 **Hessian** 既慢又易错；二阶信息虽能加速收敛，实现成本却常让人放弃。

TinyAD 的立场很直接：对几何处理里典型的**按元素（per-element）**能量，**编译期前向模式**二阶 AD 往往比反向模式 tape、图着色或符号求导都更灵活、更快。本文重点说明其**自动微分在实现层面如何工作**。

---

## 1. 问题形态：为何选前向模式？

总能量常为部分可分离和：

$$
f(\mathbf{x}) = \sum_{j\in\mathcal{E}} f_j(\mathbf{x}_j),
\qquad \mathbf{x}\in\mathbb{R}^n,
\tag{1}
$$

每个元素 $j$（三角形、四面体、边……）只依赖少量局部变量 $\mathbf{x}_j\in\mathbb{R}^k$，$k$ 通常为 3–24（平面三角面 $k=6$，四面体 $k=12$）。

| 模式 | 单元素代价（梯度+Hessian） | 特点 |
| :--- | :--- | :--- |
| **前向** | $O(k^2)$–$O(k^3)$ | 一次前向遍历；无 tape；控制流自由 |
| **反向** | 一阶 $O(k)$，二阶需额外遍 | 对大规模 $n$ 渐近更优；需图/tape；分支要 retape |

渐近上反向对 $n$ 更优，但当 $k$ 很小时常数因子主导。论文图 4：对 $\lVert x\rVert _2$（$x\in\mathbb{R}^k$）求梯度+Hessian，$k=6$ 时 TinyAD 比 ADOL-C 快约 **73 倍**；31.9 万三角面的参数化中，单线程前向也显著快于反向 tape（图 7）。

**核心设计**：不在全局 $n$ 维上做 AD，而在每个元素的 $k$ 维子问题上用 `TinyAD::Double<k>` 前向传播 $(v,\mathbf{g},\mathbf{H})$，再散射到全局稀疏 $\mathbf{g},\mathbf{H}$。

---

## 2. 实现总览：无 tape 的编译期前向 AD

```
用户 C++ 代码（与 double 写法相同）
        ↓  运算符重载 / 函数重载
每个标量携带 (v, grad, Hess)  ∈  R × R^k × R^{k×k}
        ↓  链式法则在编译期内联
元素局部 (f_j, g_j, H_j)
        ↓  索引散射 I_j^T
全局稀疏梯度 g、Hessian H
```

与反向模式（ADOL-C 等）的本质区别：

| | **TinyAD（前向）** | **反向 tape** |
| :--- | :--- | :--- |
| 计算图 | **不显式构建**；控制流与原始程序一致 | 执行时录制/回放 tape |
| 分支 | `if (det≤0) return ∞` 直接写 | 需 retape 或枚举分支 |
| 二阶 | 每个标量自带 $\mathbf{H}$，一次前向 | 需额外前向/后向遍 |
| 优化 | 导数表达式编译期已知 → 内联 + Eigen SIMD | 运行时解释 tape |

概念上接近 Mitsuba 渲染器中的前向 AD [Jakob 2010]，但 TinyAD 额外提供网格稀疏装配接口，并完整实现二阶规则。

---

## 3. 活跃标量 `Scalar<k>`：数据结构

类型别名 `TinyAD::Double<k> = Scalar<k, double>`。每个实例存三份数据：

$$
\text{活跃标量} \;=\; (v,\,\mathbf{g},\,\mathbf{H}),
\quad
v\in\mathbb{R},\;
\mathbf{g}=\frac{\partial v}{\partial \mathbf{x}}\in\mathbb{R}^k,\;
\mathbf{H}=\frac{\partial^2 v}{\partial \mathbf{x}^2}\in\mathbb{R}^{k\times k}.
\tag{2}
$$

$\mathbf{x}=(x_0,\ldots,x_{k-1})^\top$ 是**该元素内** $k$ 个活跃变量的向量；$k$ 在**编译期**固定（`Scalar<Eigen::Dynamic>` 可用但慢）。

### 3.1 初始化：源节点

第 $i$ 个活跃变量 $x_i$ 构造为：

$$
(x_i,\,\mathbf{e}_i,\,\mathbf{0}),
\qquad
(\mathbf{e}_i)_j = \delta_{ij}.
\tag{3}
$$

被动常量 $c$（rest shape、面积、约束目标等）构造为 $(c,\mathbf{0},\mathbf{0})$，与 `double` 隐式转换等价。

```cpp
using AD = TinyAD::Double<3>;
Eigen::Vector3<AD> x = AD::make_active({0.0, -1.0, 1.0});  // 三个源节点
Eigen::Vector3d y(2.0, 3.0, 5.0);                            // 被动向量
```

`make_active` 对 $i=0,\ldots,k-1$ 分别调用 `Scalar(val, i)`，在 `grad[i]` 置 1。

### 3.2 模板变体

| 类型 | 用途 |
| :--- | :--- |
| `Scalar<k, float>` | 单精度 |
| `Scalar<k, double, false>` | **仅梯度**，省掉 $\mathbf{H}$ 存储与运算 |
| `Scalar<Eigen::Dynamic, double>` | 运行时 $k$，灵活但慢 |

---

## 4. 导数传播：运算符如何实现

每个二元/一元运算 $c = o(a,b)$ 必须实现映射

$$
((v_a,\mathbf{g}_a,\mathbf{H}_a),\,(v_b,\mathbf{g}_b,\mathbf{H}_b))
\;\mapsto\;
(v_c,\mathbf{g}_c,\mathbf{H}_c).
\tag{4}
$$

以下 $\mathbf{x}$ 始终指该元素的 $k$ 维局部变量。

### 4.1 加减法（线性）

$$
c=a\pm b
\;\Rightarrow\;
\mathbf{g}_c=\mathbf{g}_a\pm\mathbf{g}_b,\quad
\mathbf{H}_c=\mathbf{H}_a\pm\mathbf{H}_b.
\tag{5}
$$

被动标量 $c=a\pm\beta$ 只改 $v$，导数不变。

### 4.2 乘法（积法则）

$$
c=ab
\;\Rightarrow\;
\frac{\partial c}{\partial \mathbf{x}}
= b\,\frac{\partial a}{\partial \mathbf{x}} + a\,\frac{\partial b}{\partial \mathbf{x}},
\tag{6}
$$

$$
\frac{\partial^2 c}{\partial \mathbf{x}^2}
= b\,\mathbf{H}_a + a\,\mathbf{H}_b
+ \frac{\partial a}{\partial \mathbf{x}}\,\frac{\partial b}{\partial \mathbf{x}}^\top
+ \frac{\partial b}{\partial \mathbf{x}}\,\frac{\partial a}{\partial \mathbf{x}}^\top.
\tag{7}
$$

实现中对应：

```cpp
res.val = a.val * b.val;
res.grad = b.val * a.grad + a.val * b.grad;
res.Hess = b.val * a.Hess + a.val * b.Hess
         + outer(a.grad, b.grad) + outer(b.grad, a.grad);
```

### 4.3 一元复合：`chain()` 与链式法则

对 $c = f(a)$，$a=a(\mathbf{x})$，库内统一用：

$$
\mathbf{g}_c = f'(a)\,\mathbf{g}_a,
\qquad
\mathbf{H}_c = f''(a)\,\mathbf{g}_a\mathbf{g}_a^\top + f'(a)\,\mathbf{H}_a.
\tag{8}
$$

源码（`Scalar::chain`）：

```cpp
res.grad = grad * a.grad;
res.Hess = Hess * outer(a.grad, a.grad) + grad * a.Hess;
```

**例：$\sqrt{a}$**

```cpp
const PassiveT f = std::sqrt(a.val);
return chain(f, 0.5/f, -0.25/(f*a.val), a);
```

**例：$e^a$** — $f'=f''=e^a$：

```cpp
const PassiveT exp_a = std::exp(a.val);
return chain(exp_a, exp_a, exp_a, a);
```

**例：$a^2$**（直接展开，等价于链式）：

```cpp
res.grad = 2.0 * a.val * a.grad;
res.Hess = 2.0 * (a.val * a.Hess + outer(a.grad, a.grad));
```

**例：$\log a$** — $f'=1/a$，$f''=-1/a^2$。

### 4.4 除法（商法则）

由 $c = a \cdot b^{-1}$ 与 $b^{-1}$ 的链式法则组合得到；实现为 `operator/` 重载，避免用户手写。

### 4.5 查询任意中间量

与 tape 式 AD 不同，**任意**中间活跃标量均可读导数：

```cpp
AD angle = acos(x.dot(y) / (x.norm() * y.norm()));
Eigen::Vector3d g = angle.grad;
Eigen::Matrix3d H = angle.Hess;
```

便于调试能量中某一项的局部曲率。

---

## 5. 与 Eigen 的集成：矩阵运算如何微分

`Scalar<k>` 可作为 `Eigen::Matrix<Scalar<k>, ...>` 的标量类型。矩阵乘、行列式、逆、归一化等**不**有单独的“矩阵 AD 引擎”，而是在 Eigen 表达式模板展开后，对每个标量分量调用上述规则。

例如 $3\times 3$ 矩阵求逆：每个输出分量是输入分量的有理函数，积法则与 `chain()` 在编译期内联展开。用户写法与 `double` 版一致：

```cpp
Eigen::Matrix2<T> J = M * Mr.inverse();
return A * (J.squaredNorm() + J.inverse().squaredNorm());
```

`T` 为 `double`（仅求值）或 `TinyAD::Double<6>`（求导）时，**同一份 lambda** 通过 `TINYAD_SCALAR_TYPE(element)` 切换。

被动与活跃可混用：`Eigen::Matrix2d`（rest shape）与 `Eigen::Matrix2<T>`（含活跃坐标）相乘时，被动侧导数为零，仅传播活跃侧的 $(v,\mathbf{g},\mathbf{H})$。

---

## 6. 控制流：为何前向模式“免费”支持分支

反向模式在 $x$ 依赖分支时，计算图结构随 $x$ 变化，必须 retape 或只微分当前分支。前向模式**不保存图**，只保存当前 $x$ 下的导数**数值**：

```cpp
if (M.determinant() <= 0.0)
    return (T)INFINITY;   // 翻转：能量无穷，该分支的 g,H 仍自洽
// 否则正常计算畸变
```

论文图 6 的更强例子：先根据当前多边形顶点 $x$ 做**最优三角剖分**，再对剖分后的三角形求畸变——剖分逻辑可用普通 `if/for`，AD 只沿**实际执行路径**传播。

线搜索阶段用 `func.eval(x)`（`T=double`），牛顿步用 `eval_with_derivatives`（`T=Double<k>`），同一 lambda 模板实例化两次，避免每步线搜索都做 AD。

---

## 7. 稀疏装配：`ScalarFunction` 的实现逻辑

### 7.1 变量句柄与索引图

```cpp
auto func = TinyAD::scalar_function<2>(mesh.vertices());
```

- 每个顶点句柄对应 $d=2$ 个标量 $(u,v)$；
- 内部维护 `variable_handles` → 全局下标的映射，$n = d\times|\text{vertices}|$。

### 7.2 注册元素与记录 $I_j$

```cpp
func.add_elements<3>(mesh.faces(), [&](auto& element) {
    using T = TINYAD_SCALAR_TYPE(element);
    Eigen::Vector2<T> a = element.variables(v0);  // 记录 (element, v0) 关系
    // ...
    return energy;
});
```

`element.variables(handle)` 做两件事：

1. 返回当前 $x$ 下该句柄的 $d$ 维向量（分量类型为 `T`）；
2. 在**注册阶段**建立该元素访问了哪些全局变量，即装配用的**提取矩阵** $I_j\in\{0,1\}^{k\times n}$：$\mathbf{x}_j = I_j \mathbf{x}$。

`add_elements<k>` 要求静态 valence；变长 stencil 用 `add_elements_dynamic<6,8,10,...>` 按 valence 分组到不同静态 $k$。

### 7.3 求值流程

对给定 $\mathbf{x}$，`eval_with_derivatives` 大致执行：

```
f ← 0, g ← 0, H ← 稀疏零矩阵
parallel for each element j:
    1. 从 x 取出局部 x_j，构造 k 个活跃 Scalar
    2. 用用户 lambda 计算 energy_j（全程 AD）
    3. 读出 f_j = energy.val, g_j = energy.grad, H_j = energy.Hess   // 各 k 维 / k×k
    4. f += w_j * f_j
       g += w_j * I_j^T g_j
       H += w_j * I_j^T H_j I_j        // 散射到全局稀疏位置
```

权重 $w_j$ 为元素面积/体积等（用户在能量里乘即可）。OpenMP 并行遍历元素（`func.settings.n_threads`）。

求导分布式成立：

$$
\nabla f = \sum_j I_j^\top \nabla f_j,
\qquad
\nabla^2 f = \sum_j I_j^\top (\nabla^2 f_j)\, I_j.
\tag{9}
$$

无需从全局计算图做图着色推断稀疏模式——**用户写 stencil 即定义稀疏结构**。

### 7.4 元素级 Hessian 投影

`eval_with_hessian_proj` 在第 3 步后对每个 $k\times k$ 的 $\mathbf{H}_j$ 做**特征分解**，将负特征值钳制：

- $\lambda_i \leftarrow \max(\lambda_i,\varepsilon)$（默认 $\varepsilon>0$），或
- $\lambda_i < 0$ 时取 $|\lambda_i|$（`projection_eps < 0`）。

再散射得到全局 $\mathbf{H}^+$，用于投影牛顿 $ \mathbf{H}^+ \Delta\mathbf{x} = -\mathbf{g}$。对 $k\le 12$ 的稠密特征分解极便宜；这与 [解析 Eigensystem](../../1.Parameterization/2.几何优化方法/2018-02-15-能量的Hessian投影.md) 的闭式 per-quadrature 投影是不同路线（通用能量 vs 各向同性闭式）。

### 7.5 向量值目标 `VectorFunction`

残差 $ \mathbf{r}(\mathbf{x})\in\mathbb{R}^m$、Gauss–Newton 所需 Jacobian $\mathbf{J}=\partial\mathbf{r}/\partial\mathbf{x}$：每个元素返回一段残差，装配逻辑与标量情形类似，用于 PolyVector 等（论文图 9）。

---

## 8. API 两层接口（用法摘要）

### 8.1 稠密小问题

```cpp
using AD = TinyAD::Double<3>;
Eigen::Vector3<AD> x = AD::make_active({0.0, -1.0, 1.0});
Eigen::Vector3d y(2.0, 3.0, 5.0);
AD angle = acos(x.dot(y) / (x.norm() * y.norm()));
Eigen::Vector3d g = angle.grad;
Eigen::Matrix3d H = angle.Hess;
```

### 8.2 网格稀疏问题

```cpp
auto func = TinyAD::scalar_function<2>(mesh.vertices());
func.add_elements<3>(mesh.faces(), [&](auto& element) { /* ... */ });
Eigen::VectorXd x = func.x_from_data([&](auto vh) { return param.row(vh.idx()); });
auto [f, g, H_proj] = func.eval_with_hessian_proj(x);
Eigen::VectorXd d = TinyAD::newton_direction(g, H_proj);
x = TinyAD::line_search(x, d, f, g, func);
```

---

## 9. 典型工作流：投影 Newton

```
x ← Tutte 初值
重复:
  (f, g, H_proj) ← func.eval_with_hessian_proj(x)
  d ← 解 H_proj d = -g
  若 newton_decrement(d, g) < ε: 停止
  x ← line_search(x, d, f, g, func)    // 内部用 eval，无 AD
```

对称 Dirichlet 面能量：$A(\lVert J\rVert _F^2+\lVert J^{-1}\rVert _F^2)$；翻转分支 `det≤0 → ∞` 见论文图 2 完整 listing。

---

## 10. 复杂度与性能要点

| 环节 | 量级 |
| :--- | :--- |
| 单元素 AD | $O(k^2)$ 梯度传播；$O(k^3)$ 级 Hessian 更新（常数小） |
| 全局装配 | $O(\#\mathcal{E}\cdot k^2)$ 非零写入 |
| 线性求解 | 常 dominate 总时间（图 7 底部） |
| 编译 | 模板内联导致编译单元较大；运行时无 tape 开销 |

优化来源：**编译期**已知全部导数表达式 → C++ 内联 + Eigen 固定尺寸 `Matrix<double,k,k>` 向量化。

---

## 11. 与其他 AD / 本博客笔记

| 工具 | 模式 | 二阶 | 分支 | 网格稀疏 |
| :--- | :--- | :--- | :--- | :--- |
| **TinyAD** | 前向 | ✓ | 自由 | `ScalarFunction` 原生 |
| ADOL-C | 反向 | ✓ | 需 retape | 着色推断 |
| ACORNS | 变换 | ✓ | 受限 | 需额外集成 |
| PyTorch | 反向 | 可能 | 动态图 | 稠密张量 |
| [Analytical Eigensystem](../../1.Parameterization/2.几何优化方法/2018-02-15-能量的Hessian投影.md) | 解析 | ✓ | — | 各向同性能量闭式 |
| 手工推导 | — | ✓ | — | 最快但难维护 |

| 笔记 | 联系 |
| :--- | :--- |
| [SLIM](../../1.Parameterization/2.几何优化方法/2018-01-02-可扩展局部单射映射-SLIM.md) | 局部-全局代理；TinyAD 可装真能量试原型 |
| [AQP](../../1.Parameterization/2.几何优化方法/2018-01-03-加速二次代理-AQP.md) | 二次代理加速；TinyAD 提供真 Hessian |
| [ShapeUp](几何优化-ShapeUp.md) | 约束投影不求导；TinyAD 负责可微能量 |

**何时不用 TinyAD**：单元素 $k$ 很大、仅需一阶且 $n$ 极大时，反向或解析雅可比可能更合适。

---

## 12. 构建

```bash
git clone https://github.com/patr-schm/TinyAD.git
# CMake: add_subdirectory(TinyAD) + target_link_libraries(... TinyAD::TinyAD)
```

要求 C++17、Eigen3。MIT 许可。

---

## 13. 小结

1. **`Scalar<k>`**：每个标量携带 $(v,\mathbf{g},\mathbf{H})$，源节点 $(x_i,\mathbf{e}_i,\mathbf{0})$。
2. **传播**：加减线性；乘法用积法则 (7)；一元用 `chain()` (8)；全部编译期内联。
3. **无 tape**：控制流与 `double` 程序相同；线搜索用被动 `eval` 省 AD。
4. **`ScalarFunction`**：用户 lambda 定义 stencil → 局部 $k$ 维 AD → $I_j^\top \mathbf{H}_j I_j$ 散射；可选 per-element PSD 投影。
5. **定位**：不为全局 $n$ 做 AD，而为网格上大量**微小** $k$ 维子问题做 AD——这与部分可分离结构 (1) 精确匹配。

---

## 参考文献

1. Schmidt P., Born J., Bommes D., Campen M., Kobbelt L. *TinyAD: Automatic Differentiation in Geometry Processing Made Simple*. CGF 41(5), 2022.
2. Griewank A., Walther A. *Evaluating Derivatives* — AD 理论。
3. Jakob W. Mitsuba renderer forward-mode AD, 2010.
4. Schmid P. Tutorial on AD in geometry processing, 2019.
