---
layout: post
title: "Conformal Mesh Deformations with Möbius Transformations"
date: 2026-06-17
category: Parameterization
categories: ["Parameterization", "Parameterization-ConformalMapping"]
---

Vaxman、Müller、Weber 在 SIGGRAPH 2015 发表 [*Conformal Mesh Deformations with Möbius Transformations*](https://doi.org/10.1145/2766915)（ACM TOG 34(4), Article 55），从 **"曲面由圆构成"**（surfaces from circles）的视角，用**逐面、分片相容的 Möbius 变换**统一三角网格与**圆多边形网格**（circular meshes）的共形编辑与插值。

- 不变量：**圆、交比（cross-ratio）、外接圆交角**
- 应用：手柄形变、两形状插值/外推，**可控共形误差**
- 实现：[avaxman/MoebiusCode](https://github.com/avaxman/MoebiusCode)（基于 libhedra / libigl）

与 `Mobius Registration`（球面参数化对齐）不同，本文处理的是**嵌入空间 $\mathbb{R}^2/\mathbb{R}^3$ 中的网格形变**，且在圆网格上**内禀保持共圆性**（concyclity），而非事后投影。

---

## 动机：多种"离散共形"如何统一？

连续曲面共形映射保角、局部相似，利于保留纹理与细节（图 2：同约束下共形形变比非共形更少剪切）。但离散情形存在多套定义：

| 传统路线 | 不变量 | 局限 |
| :--- | :--- | :--- |
| **Circle patterns** (Bobenko–Springborn) | 四边形复交比、外接圆交角 | 全局变换保不变量，缺灵活编辑 |
| **Metric conformal** (Springborn et al.) | 边长交比 / 共形因子 $u_i$ | 仅度量缩放，难直接约束 $\mathbb{R}^3$ 顶点位置 |
| **局部 Jacobian QC** (ARAP/SLIM 等) | 拟共形误差 | 多为 $f:\mathbb{R}^2\to\mathbb{R}^2$，非统一 3D 嵌入形变 |
| **Spin transformations** (Crane et al. 2011) | 共形形变 | 无法施加位置约束 |

本文用 **PCM（piecewise-compatible Möbius）** 参数化，把圆模式与度量共形归结为**角变量**上的模/辐角条件，并支持手柄约束下的 Gauss–Newton 优化。

---

## 复平面：单面 Möbius 与角倒数

归一化 Möbius 变换 $m_f(z)=\dfrac{a_f z+b_f}{c_f z+d_f}$，$a_f d_f-b_f c_f=1$。

边 $(z_i,z_k)$ 的像满足闭式（**不**把边映为直线，而是连接像顶点的弦）：

$$
m_f(z_k)-m_f(z_i)=\frac{a_f d_f-b_f c_f}{(c_f z_i+d_f)(c_f z_k+d_f)}(z_k-z_i).
$$

定义 **角倒数**（corner reciprocal）

$$
X_{f,i}=(c_f z_i+d_f)^{-1},
$$

则

$$
\boxed{\; m_f(z_k)-m_f(z_i)=z_{ik}\, X_{f,i}\, X_{f,k} \;}
$$

- 分子 $(a,b)$ 控制平移；边变换只依赖分母，故**一个顶点位置 + 全部 $X$** 即可定整个面变换；
- $|X_{f,i}X_{f,k}|$ 为边缩放，$\arg(X_{f,i}X_{f,k})$ 为边旋转；
- 单面内 $X$ 仅确定到**符号**（系数可乘 $-1$）。

---

## PCM：分片相容 Möbius 变换

相邻面 $f,g$ 共享边 $ik$，各自 Möbius 映射在共享顶点上必须一致。**相容条件**：

$$
\boxed{\; w_k-w_i = z_{ik}\, X_{f,i} X_{f,k} = z_{ik}\, X_{g,i} X_{g,k} \;}
$$

满足 (2) 的角倒数集合称为 **可积（integrable）**，确定变形网格 $w$（差全局平移）。

**PCM 变换**：每个面经某个 Möbius 变到像面；三角网格在 $\mathbb{C}$ 上任意形变都是 PCM（每面 3 顶点唯一确定 Möbius）。四边形等圆网格上 PCM 自然保持**共圆四边形**的 Möbius 等价类。

---

## 离散共形：交比与两个子类

### 复交比

$$
\mathrm{cr}[i,j,k,l]=\frac{(z_i-z_j)(z_k-z_l)}{(z_j-z_k)(z_l-z_i)}.
$$

Möbius 变换保 $\mathrm{cr}$。四边形共圆 $\Leftrightarrow$ $\mathrm{cr}\in\mathbb{R}$；$\mathrm{cr}=-1$ 为正方形 Möbius 等价类（conformal square）。

在 PCM 下，内边 $ik$ 两侧交比变化仅依赖角倒数比：

$$
\frac{X_{f,i}}{X_{g,i}}=\frac{X_{g,k}}{X_{f,k}},\qquad
\mathrm{cr}_w = \mathrm{cr}_z \left(\frac{X_{f,k}}{X_{g,k}}\right)^2.
$$

两邻面为**同一** Möbius 变换 $\Leftrightarrow$ $(X_{g,k},X_{g,i})=(X_{f,k},X_{f,i})$。

### Metric Conformal（MC）

**长度交比** $|\mathrm{cr}|$ 不变。等价于 Springborn 的离散度量共形：顶点共形因子 $u_i$ 使 $|w_{ij}|=|z_{ij}|\exp((u_i+u_j)/2)$。

在 PCM 中：**MC** $\Leftrightarrow$ 顶点 $i$ 处所有邻接角倒数模相同：$|X_{f,i}|=|X_{g,i}|$，且 $u_i=2\log|X_{f,i}|$。

### Intersection-Angle Preserving（IAP）

**交比辐角**编码两三角外接圆交角 $\phi_{ik}$（图 6）：$\mathrm{cr}=|\mathrm{cr}|\,e^{i(\pi-\phi)}$。

**IAP** $\Leftrightarrow$ $X_{f,i}/X_{g,i}\in\mathbb{R}$（同相位）。MC 与 IAP 互补；**同时成立**时各角倒数相等，整体为**单个** Möbius 变换。

---

## 四元数：3D PCM

顶点 $q\in\mathrm{Im}\,\mathbb{H}$，Möbius 变换

$$
m(q)=(aq+b)(cq+d)^{-1}.
$$

**虚部保持**（$m(\mathrm{Im}\,\mathbb{H})\subset\mathrm{Im}\,\mathbb{H}$）的二次条件：

$$
a\bar{c}\in\mathrm{Im}\,\mathbb{H},\quad b\bar{d}\in\mathrm{Im}\,\mathbb{H},\quad a\bar{d}-\bar{b}c\in\mathbb{R}.
$$

10 个实自由度（对比复平面 6 个）。**三点不能唯一定** 3D Möbius：第四点落在三点确定的**球面 pencil** 上，每面有一族变换——实践中直接用角倒数 $X_{f,i|k}=(c_f q_i+d_f)^{-1}$，边相容：

$$
m(q_k)-m(q_i)=X_{f,i}\,q_{ik}\,X_{f,k}.
$$

四元数交比在 Möbius 下共轭而非不变，但 **MC**（$|X|$ 匹配）与 **IAP**（$X_{g,i}^{-1}X_{f,i}\in\mathbb{R}$）仍可用；3D 中 IAP 过强，论文**主要用 MC / AMAP**。

---

## 编辑：AMAP 与反演加权

### 变量系统

| 系统 | 变量 | 规模（三角网） | 用途 |
| :--- | :--- | :--- | :--- |
| **CV**（角变量） | $X$ + $w$ | $\approx 7|V|$ | 3D、多边形面 |
| **ED**（边偏差） | $Y_v$ + $w$（可选 $e_{ik}$） | $\approx 2|V|$–$5|V|$ | 2D，变量更少 |

### As-Möbius-as-possible（AMAP）

理想离散共形 = 顶点一圈内**单一** Möbius $\Leftrightarrow$ 邻面角倒数相等。能量（ED，2D 无约束形式）：

$$
E_{\mathrm{AMAP}}=\sum_{ik\in E}\lVert w_{ik}-Y_i z_{ik} Y_k\rVert ^2,
$$

并加线性手柄约束 $w_i=w_i^*$。

**反演加权** $E_{\mathrm{INV}}=\alpha_{\mathrm{INV}}\sum_{(i,k)\in E}|Y_i-Y_k|^2$：$c_f=0$ 时为相似变换、无反演；减小 $\alpha_{\mathrm{INV}}$ 更共形，增大则更均匀缩放（图 10）。默认 $\alpha_{\mathrm{INV}}=0.1$（2D）、$0.5$（3D）。

### MC / IAP 专项优化

- **CV + MC**：约束 $|X_{f,i}|^2=|X_{g,i}|^2$；
- **CV + IAP**：$X_{g,i}X_{f,i}\in\mathbb{R}$；
- **ED**：边偏差 $e_{ik}$，$|e_{ik}|=1$ 得 MC，$e_{ik}\in\mathbb{R}$ 得 IAP。

多边形圆网格：每面角变量默认**单面 Möbius**，面内交比自动保持。

---

## 插值：Möbius 误差 $\Gamma$

两对应网格 $M_0,M_1$（$t=0,1$），先提取 $M_0\to M_1$ 的角倒数 $X$，对内边定义

$$
\boxed{\;\Gamma_{ik}=X_{g,k}X_{f,k}^{-1}=(c_g q_k+d_g)^{-1}(c_f q_k+d_f)\;}
$$

$\Gamma_{ik}=1$ 表示两边为同一 Möbius；$|\Gamma|$、$\arg\Gamma$ 分别为**长度/相位交比商**（MC/IAP 误差）。

**插值步骤**：

1. 从 $M_0,M_1$ 解 AMAP（$w$ 固定为 $M_1$）得 $\Gamma_{ik}$；
2. $\Gamma_{ik}(t)=\Gamma_{ik}^{\,t}$（对数插值，AMAP 下常接近 1）；
3. 用二次能量 $E_{\mathrm{PRES}}$ 求系数 $c,d$，满足 (8) 与边相容；
4. 重建中间网格 $M_0^{(t)}$，再乘**全局** Möbius 对齐（2D：$2\times 2$ 矩阵幂；3D：球面 pencil + 单位球上三角对齐）。

**性质**：$\prod_{k\in\mathcal{N}(i)}\Gamma_{ik}=1$ 在幂 $t$ 下保持；MC 有界插值加约束 $|c_g q_i+d_g|^2|\Gamma|^2=|c_f q_i+d_f|^2$。

---

## 优化器

全部采用 [Tang et al. 2014] 的 **guided projection Gauss–Newton**：能量 $E=\sum_k \alpha_k F_k^2$，二次等式约束 $C_l=0$，每步解 $J^{\mathsf T}J D=-J^{\mathsf T}F$ 并线搜索。$\alpha$ 逐迭代减半以优先满足约束；$\beta=10^{-6}$ 保持接近上一迭代。

## 公式与 Ceres 对应（按论文 + 官方代码）

下面把论文里的 AMAP/INV 目标，与 `libhedra` 里 Ceres 残差块做一一对应。

### 1) 论文中的优化表达（ED 变量系统）

论文第 6.2 节（ED 系统）核心是：

$$
E_{\text{AMAP,ED}}^{2D}=\sum_{(i,k)\in E}\left|\,w_{ik}-Y_i z_{ik}Y_k\,\right|^2,
\qquad
E_{\text{AMAP,ED}}^{3D}=\sum_{(i,k)\in E}\left\lVert \,w_{ik}-Y_i q_{ik}Y_k\,\right\rVert ^2
$$

其中 $w_{ik}=w_k-w_i$，2D 用复数乘法，3D 用四元数乘法。

反演控制项（论文中的 $E_{\text{INV}}$）：

$$
E_{\text{INV}}=\alpha_{\text{INV}}\sum_{(i,k)\in E}\lVert Y_i-Y_k\rVert ^2
$$

位置约束（硬约束写法）：

$$
C_{\text{pos}}(i)=w_i-w_i^*=0.
$$

此外，在“精确 MC/IAP”模式下，ED 里再加边偏差约束（论文 6.3）：

$$
|e_{ik}|^2=1 \quad(\text{MC}),\qquad \Im(e_{ik})=0 \quad(\text{IAP}).
$$

### 2) Ceres 实现里的残差块（`CeresQuatDeformSolver.h`）

官方代码（`libhedra/include/hedra/CeresQuatDeformSolver.h`）把上面的项写成 NLLS 残差：

- **AMAPError**（4 维残差）  
  对每条边构造
  $$
  r^{\text{AMAP}}_{ik}= (w_j-w_i)-\overline{Y_i}\,q_{ij}\,Y_j
  $$
  （代码用 `QConjT(Yi)` + `QMultT`，然后把四元数 4 分量都作为残差）。

- **RigidityError**（代码里对应论文 $E_{\text{INV}}$ 的离散化）  
  $$
  r^{\text{INV}}_{ik}=Y_i-Y_j
  $$
  逐分量加入残差，权重由 `rigidityFactor` 控制。

- **DCError**（离散共形软约束，标量残差）  
  代码写成
  $$
  r^{\text{DC}}_{ik}= \lVert w_j-w_i\rVert ^2-\lVert \overline{Y_i}\,q_{ij}\,Y_j\rVert ^2
  $$
  并乘 `DCFactor`。这等价于“长度交比一致”在边上的软约束版本。

总目标就是最小化这些残差平方和（省略常数）：

$$
\min \sum_{ik}\lVert r^{\text{AMAP}}_{ik}\rVert ^2
 + \lambda_{\text{inv}}\sum_{ik}\lVert r^{\text{INV}}_{ik}\rVert ^2
 + \lambda_{\text{dc}}\sum_{ik}(r^{\text{DC}}_{ik})^2.
$$

### 3) 句柄约束在 Ceres 中的实现方式

论文写的是 $w_i=w_i^*$。在 Ceres 代码里不是加罚项，而是把对应位置参数块设为常量：

- `problem->SetParameterBlockConstant(currSolution + 3*constIndices(i));`

这相当于**硬约束**句柄位置。

### 实现查证（MoebiusCode / libhedra）

- **是否化为非线性最小二乘？**  
  是。论文与代码都把问题写成残差平方和（并带约束/罚项）的迭代优化，本质是（约束）**非线性最小二乘**框架。
- **官方实现是否使用 Ceres？**  
  是，但要区分层次：  
  1) `MoebiusCode` 顶层构建脚本里明确 `find_package(Ceres REQUIRED)` 并链接 `${CERES_LIBRARIES}`；  
  2) README 又说明核心算法在 `libhedra` 的 traits + `LMSolver`（Levenberg-Marquadt）中；  
  3) `libhedra` 内也确实包含 `CeresQuatDeformSolver.h` / `CeresMRSolver.h` 等 Ceres 求解器实现。  
  因此更准确的表述是：**官方代码栈包含并使用 Ceres，同时也使用 libhedra 自身的 LM/GN 风格求解器，不是“只用 Ceres”这一种路径。**

---

## 参考文献

1. A. Vaxman, C. Müller, O. Weber. **Conformal Mesh Deformations with Möbius Transformations**. *ACM Trans. Graph.* 34(4), 55:1–11, 2015. [DOI: 10.1145/2766915](https://doi.org/10.1145/2766915)
2. A. I. Bobenko, B. A. Springborn. *Variational Principles for Circle Patterns and Koebe's Theorem*. 2004.
3. B. Springborn, P. Schröder, U. Pinkall. *Conformal Equivalence of Triangle Meshes*. SIGGRAPH 2008.
4. K. Crane et al. *Spin Transformations of Discrete Surfaces*. SIGGRAPH 2011.
5. C. Tang et al. *Guided Projection for Constrained Optimization*. SIGGRAPH 2014.
6. A. Vaxman et al. *Canonical Möbius Subdivision*. SIGGRAPH Asia 2018.
7. avaxman. **MoebiusCode** (official demo repo). [GitHub](https://github.com/avaxman/MoebiusCode)（`CMakeLists.txt` 含 `find_package(Ceres REQUIRED)`；README 说明核心在 `libhedra` traits + LM solver）。
8. avaxman. **libhedra**. [GitHub](https://github.com/avaxman/libhedra)（含 `include/hedra/LMSolver.h`、`include/hedra/CeresQuatDeformSolver.h`、`include/hedra/CeresMRSolver.h`）。
