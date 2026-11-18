---
layout: post
category: Parameterization
categories: ["Parameterization", "Parameterization-QuadRemeshing"]
title: "PGP — 周期全局参数化 (Periodic Global Parameterization)"
---

> 笔记整理自 *Periodic Global Parameterization*，Nicolas Ray、Wan Chiu Li、Bruno Lévy、Alla Sheffer、Pierre Alliez，ACM TOG 2006。
>
> **一句话**：给定曲面上一对正交分片线性向量场 $\vec K,\vec K^\perp$（通常是主曲率方向），PGP 求出两个**周期标量函数** $(\theta,\phi)$，使其梯度尽量与输入场对齐；由 $(\theta,\phi)$ 的 $2k\pi$ 等值线自动浮现出**四边形 chart 布局**，整个过程无需预先切割或分块。
>
> **核心技巧**：用三角函数替代变量 $U=(\cos\theta,\sin\theta),\ V=(\cos\phi,\sin\phi)$ 表达参数化，把 $2\pi$ **平移**与 $\pi/2$ **旋转**两类自由度**内建进 $\sin/\cos$**，于是优化阶段是一个**连续二次能量**，整数自由度只在最后逐三角形重建时显式确定——这与 MIQ 把整数跳变显式写进混合整数规划形成鲜明对比。

---

## 0. 背景与定位

参数化在曲面与简单 2D 域之间建立对应。任意拓扑曲面参数化的常见做法是**切缝**变成一个或多个圆盘，但切缝会带来渲染接缝、重网格化的人工对齐与尺寸跳变，且"最优切缝"本身极难求。全局光滑参数化（如 Khodakovsky et al. 2003）力图减少这些不连续，但通常**难以控制失真、奇异点数量与位置**，且多数需要预先把网格分块（chart 分割本身又是难题）。

对许多几何处理任务而言，**让参数化与主曲率方向对齐**很有价值（d'Azevedo 2000 指出曲率对齐能改善曲面拟合与重网格化的收敛性）。PGP 的贡献正是：

- 输入一对正交向量场，输出与之对齐的全局光滑参数化；
- **不需要预先分块、不需要切缝**——chart 布局（基复形拓扑）与参数化由同一个全局优化**同时浮现**；
- 生成的 chart 大多是连接规则（价为 4）的良形四边形；
- 既能构造**拟共形**（保角）也能构造**拟等距**（保角且保面积）参数化，后者以引入更多奇异点为代价。

> **与相关方法的关系**：Khodakovsky 2003 用过渡函数做 inter-chart 松弛、但需预分块；Polycube-maps 手工搭四边形 chart 布局；Gu & Yau 2003 用共形结构、奇异点数固定故 stretch 偏大；Gortler et al. 2004 用 one-forms 给出离散 Hopf-Poincaré 指标定理（奇异点指标之和 $=2-2g$）。PGP 的不同在于把**更多几何信息**（向量场对齐 + 失真）放进能量，并允许过渡函数含旋转自由度。

### 算法四阶段

| 阶段 | 内容 | 是否可选 |
|:---|:---|:---|
| ① 向量场平滑 | 把方向从各向异性区外推到各向同性区（主曲率在各向同性区无定义） | 可选预处理 |
| ② curl 校正 | 缩放向量场幅度抵消 directional curl，**大幅减少奇异点**（但放弃等距、保持共形） | 可选预处理 |
| ③ 替代变量参数化 | 在 $U,V$ 上建二次能量并求极小（**主步骤**，§2） | 必需 |
| ④ chart 提取与参数化 | 逐三角形重建 $(\theta,\phi)$、检测奇异、提取 chart、修复含奇异 chart（§3） | 必需 |

> 两个预处理是独立模块，本笔记按论文顺序放在 §4。

---

## 1. 流形与周期全局参数化

### 1.1 流形 (manifold) 与过渡函数

给定曲面 $S$，取一组（可重叠的）拓扑圆盘 $\{C\}$（称 **chart**）与一组映射 $\{\phi\}$ 把每个 chart 映到 2D 域 $\Omega$（坐标记为 $\theta,\phi$，用它们而非 $u,v$ 是为了强调其**周期性**）。若任意两 chart 的交 $C\cap C'$ 是拓扑圆盘，且两者的像由一个简单几何变换 **过渡函数 $\tau_{\phi\to\phi'}$** 联系：

$$
\forall p\in C\cap C',\qquad \phi'(p)=\tau_{\phi\to\phi'}\big(\phi(p)\big),
$$

则称 $\{\phi\}$ 为一个**全局参数化 / 流形**。

- 过渡函数全是**平移** → **仿射流形 (affine manifold)**；
- 允许更一般的全纯过渡函数（含相似变换：旋转 + 平移 + 缩放）→ **复流形 (complex manifold)**。

以往工作多用仿射流形；**PGP 构造复流形的一个子类**：过渡函数 = $2\pi$ 整数倍**平移** + $\pi/2$ 整数倍**旋转**。这个额外的旋转自由度，正是让参数化能灵活对齐输入向量场的关键。

### 1.2 从仿射到周期：兼容条件与替代变量

最简单的 chart 就是**三角形本身**。在初始设定里，全局参数化由三角形角点上的坐标 $\theta_i^T,\phi_i^T$ 给出（$i$ 是顶点全局索引，$T$ 是三角形）。

**仿射兼容**：共享边 $(j,k)$ 的两三角形 $T=(i,j,k)$、$T'=(k,j,l)$ 构成仿射流形当且仅当顶点坐标差一致：

$$
\binom{\theta_j^T}{\phi_j^T}-\binom{\theta_j^{T'}}{\phi_j^{T'}}
=\binom{\theta_k^T}{\phi_k^T}-\binom{\theta_k^{T'}}{\phi_k^{T'}}.
$$

**加 $2\pi$ 平移约束**：限制平移向量坐标为 $2\pi$ 整数倍，则三角函数值在公共顶点上一致：

$$
\binom{\cos\theta_j^T}{\sin\theta_j^T}
=\binom{\cos(\theta_j^{T'}+2s\pi)}{\sin(\theta_j^{T'}+2s\pi)}
=\binom{\cos\theta_j^{T'}}{\sin\theta_j^{T'}},\quad(\phi \text{ 同理}).
$$

于是对顶点 $i$，所有入射三角形给出的 $\cos\theta_i^T,\sin\theta_i^T$ 都相同——可**把它们提升为顶点变量**

$$
\boxed{\ U_i=(\cos\theta_i,\ \sin\theta_i),\qquad V_i=(\cos\phi_i,\ \sin\phi_i)\ }
$$

不再依赖三角形 $T$。这一步是 PGP 的精髓：用 $U,V$ 替代 $\theta,\phi$，$2\pi$ 平移自由度**自动消失**。

**再加 $\pi/2$ 旋转约束**（即 periodic global parameterization）：兼容条件 (2) 推广为——存在 $r\in\{0,1,2,3\}$ 使

$$
\binom{\cos\theta_j^T}{\sin\theta_j^T}
=\begin{pmatrix}0&-1\\ 1&0\end{pmatrix}^{r}\binom{\cos\theta_j^{T'}}{\sin\theta_j^{T'}},\quad(\phi \text{ 同理}).
$$

即顶点处的 $U_i$（resp. $\phi$）在不同三角形间至多相差**符号变化 + sin/cos 交换**。**奇数次旋转差会把 $\theta$ 与 $\phi$ 耦合（交换 $U$ 与 $V$）**——这是后面必须把 $U,V$ 合并成 4 维变量的原因。

---

## 2. 对齐能量（主步骤）

### 2.1 控制场、$\omega$ 与目标能量

输入：定义在顶点、面内线性插值的正交向量场 $\vec K,\vec K^\perp$；chart 尺寸参数 $\omega$。目标是构造复流形 $\{\phi^T\}=\{(\theta^T,\phi^T)\}$ 使每面梯度对齐：

$$
\nabla\theta^T=\omega\vec K,\qquad \nabla\phi^T=\omega\vec K^\perp.
$$

- **归一化**：梯度不应依赖输入场的幅值。求**拟等距**时取 $\lVert \vec K\rVert =\lVert \vec K^\perp\rVert =1$；若要减少奇异点，则先归一化再按 §4.1 的 curl 校正缩放（结果不再等距但仍**共形**）。
- **$\omega$ 控制 chart 大小**：因已归一化，$\omega$ 决定 $\theta,\phi$ 的周期；chart 边界取 $\theta=2k\pi,\ \phi=2k\pi$ 等值线，故 $\omega$ 直接定 chart 尺寸（论文取**平均边长的 10 倍**）。$\omega$ 过大可能产生非圆盘 chart，可由 Euler-Poincaré 特征检测并自动减小 $\omega$。

由于对任意标量场 $\rho$ 有 $\operatorname{curl}(\nabla\rho)=0$，式 (4) 有解仅当 $\operatorname{curl}\vec K=\operatorname{curl}\vec K^\perp=0$。一般输入未必无旋，故弱化为**最小化能量**：

$$
F=\int_S\Big(\lVert \nabla\theta^T-\omega\vec K\rVert ^2+\lVert \nabla\phi^T-\omega\vec K^\perp\rVert ^2\Big)\,dS.
$$

难点在于：如何在**不显式处理平移/旋转自由度**的前提下表达这种对齐。下面先引入平移不变（§2.2），再加旋转不变（§2.3）。

### 2.2 平移不变能量

由附录 A，可用 $F^*$ 替代 $F$（同极小点），其中把每面 $\vec K$ 换成面均值 $\vec K_T$，并因 $\nabla\theta^T,\nabla\phi^T$ 面内常值而写成面求和：

$$
F^*=\sum_T\Big(\lVert \nabla\theta^T-\omega\vec K_T\rVert ^2+\lVert \nabla\phi^T-\omega\vec K_T^\perp\rVert ^2\Big)A_T.
$$

直接对 $F_T$ 引入平移不变较难，故先看**沿边 $\vec e_i$** 的能量（以 $\theta$ 为例，$i\in\{1,2,3\}$，$\oplus$ 表示模 3 加）。沿边梯度为 $(\theta_{i\oplus2}-\theta_{i\oplus1})/\lVert \vec e_i\rVert $，$\vec K$ 沿边投影为 $\vec K\cdot\vec e_i/\lVert \vec e_i\rVert $：

$$
F^\theta_{e_i}=\int_{\vec e_i}\big(\theta_{i\oplus2}-\theta_{i\oplus1}-\vec K\cdot\vec e_i\big)^2/\lVert \vec e_i\rVert ^2\,ds.
$$

因 $\vec K$ 沿边线性，可用边均值 $\vec K_i=(\vec K_{i\oplus2}+\vec K_{i\oplus1})/2$ 并按 $\lVert \vec e_i\rVert $ 缩放（不改极小点）：

$$
F^\theta_{T,i}=\big((\theta_{i\oplus2}-\theta_{i\oplus1})-\omega\vec K_i\cdot\vec e_i\big)^2.
$$

此形式下**引入平移不变**只需把差换成模 $2\pi$ 的差：

$$
F^\theta_{T,i}=\min_s\big\{\big((2s\pi+\theta_{i\oplus2}-\theta_{i\oplus1})-\omega\vec K_i\cdot\vec e_i\big)^2\big\}.
$$

用一阶 Taylor 把"角度差"近似为"sin/cos 向量差的模"，整数 $s$ 被消去（周期性内建于 $\sin/\cos$）：

$$
F^\theta_{T,i}\simeq\left\lVert \,U_{i\oplus2}-R(\omega\vec K_i\cdot\vec e_i)\,U_{i\oplus1}\right\rVert ^2,
\qquad R(\alpha)=\begin{pmatrix}\cos\alpha&-\sin\alpha\\ \sin\alpha&\cos\alpha\end{pmatrix}.
$$

### 2.3 旋转不变能量

向量场一般**无法全局一致定向**（如球面）。在每个三角形内允许各顶点的控制场独立旋转 $r_i\in\{0,1,2,3\}$（即 $r_i\cdot\pi/2$），把 $\vec K_2,\vec K_3$ 旋到与 $\vec K_1$ 对齐；**旋转同时作用于控制场 $(\vec K_i,\vec K_i^\perp)$ 与未知量 $(\theta_i,\phi_i)$**。奇数旋转差意味着交换 $\theta\leftrightarrow\phi$，故二者不可再分离。式 (11) 推广为

$$
F_{T,i}=\min_{s,t}\left\lVert J^{r_{i\oplus2}}\binom{\theta_{i\oplus2}}{\phi_{i\oplus2}}-J^{r_{i\oplus1}}\binom{\theta_{i\oplus1}+2s\pi}{\phi_{i\oplus1}+2t\pi}-\binom{\delta_i}{\delta_i^\perp}\right\rVert ^2,
\quad J=\begin{pmatrix}0&-1\\1&0\end{pmatrix},
$$

其中

$$
r_i=\operatorname*{argmax}_{r\in\{0,1,2,3\}}\big(\vec K_1\cdot J^{r}\vec K_i\big),\qquad \vec K_i'=J^{r_i}\vec K_i,
$$
$$
\delta_i=\tfrac{\omega}{2}(\vec K_{i\oplus1}'+\vec K_{i\oplus2}')\cdot\vec e_i,\qquad
\delta_i^\perp=\tfrac{\omega}{2}(\vec K_{i\oplus1}'^{\perp}+\vec K_{i\oplus2}'^{\perp})\cdot\vec e_i.
$$

同样用一阶近似换成 sin/cos，得到 4 维变量 $X_i=(U_i;V_i)=(\cos\theta_i,\sin\theta_i,\cos\phi_i,\sin\phi_i)$ 的二次型：

$$
F_{T,i}\simeq\left\lVert \,M^{r_{i\oplus2}}X_{i\oplus2}-
\begin{pmatrix}\cos\delta_i&-\sin\delta_i&0&0\\ \sin\delta_i&\cos\delta_i&0&0\\ 0&0&\cos\delta_i^\perp&-\sin\delta_i^\perp\\ 0&0&\sin\delta_i^\perp&\cos\delta_i^\perp\end{pmatrix}M^{r_{i\oplus1}}X_{i\oplus1}\right\rVert ^2,
$$

$$
M=\begin{pmatrix}0&0&-1&0\\ 0&0&0&1\\ 1&0&0&0\\ 0&1&0&0\end{pmatrix}
$$

是编码"$\pi/2$ 旋转 + 交换 $U,V$"的 $4\times4$ 矩阵。

### 2.4 三角形积分形式

可直接取边能量之和 $\sum_{T,i}(F^\theta_{T,i}+F^\phi_{T,i})$（**边版本**），对规则采样有效，但**对各向异性网格敏感**。论文（附录 B）改用**面积分版本**，把面能量写成边能量的线性组合：

$$
F^*=\sum_T F_T=\sum_T\sum_{i=1}^3\lambda_i^T\big(F^\theta_{T,i}+F^\phi_{T,i}\big),
$$

权重 $(\lambda_1^T,\lambda_2^T,\lambda_3^T)$ 由附录 B 的 $3\times3$ 线性系统 (24) 求得，**只依赖三角形几何**，从而让参数化只随几何变化而不被网格各向异性带偏。

### 2.5 数值求解

代入 $\lambda_i^T$ 得到关于 $X_i$ 的总二次能量 $F^*$。锁定一个顶点 $U_1=(1,0),\ V_1=(1,0)$，对其余变量求极小——这是**稀疏对称系统**，用带 Jacobi 预条件的共轭梯度求解。

**问题**：$>50\mathrm K$ 顶点的模型，远离锁定点时 $\lVert U_i\rVert ,\lVert V_i\rVert $ 快速衰减，造成加权偏差与数值不稳定。

**解决**：加非线性罚项防止模衰减：

$$
F^{**}=F^*+\varepsilon\sum_i\big[(\lVert U_i\rVert ^2-1)^2+(\lVert V_i\rVert ^2-1)^2\big].
$$

用 Newton 法求解，初值取无罚项线性解，$\varepsilon=10^{-3}$，所有示例 $\le5$ 次外迭代即收敛到 $\lVert \nabla F^{**}\rVert <10^{-6}$。

> **罚项的额外好处**：奇异点对应 $\lVert U_i\rVert \to0$（模为零、能量 $F^*$ 高，见图 5）；同一区域出现两个奇异点会让罚项激增，于是优化**自发把奇异点均匀分散到整张曲面**——这是局部松弛方法做不到的。

---

## 3. 参数化提取

求解输出一组 $U_i,V_i$（即未知 $\theta_i,\phi_i$ 的 sin/cos）。重建完整参数化分四步：① 逐三角形重建 $(\theta,\phi)$；② 检测奇异点；③ 由 $2k\pi$ 周期定 chart 布局并对无奇异 chart 参数化；④ 修复含奇异 chart。

### 3.1 逐三角形重建（Algorithm 1）

给定 $T=(i,j,k)$ 的 $U,V$，要确定整数平移 $(s,t)$ 与旋转 $r$。把首顶点 $i$ 的自由度设为 $(r,s,t)=(0,0,0)$，则 $\theta_i^T=\operatorname{angle}(U_i),\ \phi_i^T=\operatorname{angle}(V_i)$（$\operatorname{angle}(U)=\operatorname{sign}(U_y)\arccos(U_x/\lVert U\rVert )$）。再沿每条边传播确定差值 $s_e^T,t_e^T,r_e^T$：

```
沿边 e=(i,j) 从 i 传播到 j：
  // 1. 确定并施加旋转 r_e（把 K_j 旋到与 K_i 最对齐）
  r_e^T ← argmax_{r∈{0,1,2,3}}  K_i · J^r K_j          // J = [[0,-1],[1,0]]
  K_j ← J^{r_e^T} K_j ;  K_j^⊥ ← J^{r_e^T} K_j^⊥
  θ_j^T ← angle(U_j^T) ;  φ_j^T ← angle(V_j^T)
  (θ_j^T, φ_j^T) ← J^{r_e^T} (θ_j^T, φ_j^T)             // 奇数旋转会交换 θ↔φ

  // 2. 确定并施加整数平移 s, t（显式最小化边能量）
  n ← e/‖e‖
  s_e^T ← argmin_s | θ_i^T − (π/ω) n·(K_i+K_j) − θ_j^T + 2sπ |
  t_e^T ← argmin_t | φ_i^T − (π/ω) n·(K_i^⊥+K_j^⊥) − φ_j^T + 2tπ |
  θ_j^T ← θ_j^T + 2 s_e^T π ;  φ_j^T ← φ_j^T + 2 t_e^T π
```

对三条边各做一次（按 $(i,j,k)$ 循环置换），即得该三角形的 $(\theta,\phi)$。

### 3.2 奇异顶点 / 边 / 三角形

逐三角形重建后需检查它们能否在参数空间拼成合法平面三角化（连续解在导数消失处必有奇异，离散下表现为违反合法三角化的元素）：

- **奇异顶点**：一环角和 $\neq 2\pi$（等价于对其一环邻域跑 Algorithm 1 得到**开放路径**）；
- **奇异边**：$(i,j)$ 与 $(j,i)$ 在参数空间长度不匹配；
- **奇异三角形**：三边传播得开放路径，或参数空间面积为负。

### 3.3 Chart 布局

chart 边界取 $\theta=2k\pi$ 与 $\phi=2k\pi$ 的等值线。**关键不变性**保证等值线在非奇异边上端点对齐、连成连续折线：

- **平移不变**：三角形若被 iso-$2k\pi$ 线穿过，平移 $2s\pi$ 后被 iso-$2(k+s)\pi$ 线在同位置穿过；
- **旋转不变**：旋转 $\pi/2$ 把 $\theta$ 的 iso 线换成 $\phi$ 的 iso 线（指标取负）。

相邻非奇异三角形间的过渡函数：

$$
\tau_s=s_i^{T_1}-s_i^{T_2},\quad \tau_t=t_i^{T_1}-t_i^{T_2},\quad \tau_r=r_e^{T_1}-r_e^{T_2},\qquad
\tau(p)=R^{\tau_r}p+(\tau_s,\tau_t),
$$

$R$ 为 $\pi/2$ 旋转——满足上述不变性，故 iso 线端点匹配。**Algorithm 2** 据此构造 chart 边界：逐三角形求与 $\theta=2k\pi$、$\phi=2k\pi$ 的交线段并存到边上 → 沿边合并相同 3D 位置的端点 → 求三角形内线段交点 → **递归剥除所有悬挂段**（价为 1 的端点逐一"啃掉"直到遇到价 $>2$）。无奇异 chart 用经典贪心拼合三角形得到参数化。

### 3.4 含奇异 Chart 的重参数化

含奇异点的 chart 无法靠展平重建，论文采用简单策略：

- **四边 chart**：用 mean-value coordinates [Floater 2003] 重参数化，调整边界顶点参数以保 $C^0$ 连续（图 6 A,B）；
- **N 边 chart**：在中心与各边中点各插一点，用测地线连接并沿其切割成四边形 chart，再如上参数化（图 6 C,D）；
- 如需更高的跨边界连续性，可再施加 [Khodakovsky 2003; Schreiner 2004] 的局部松弛。

实践中**仅 2–5% 的 chart 含奇异**需此处理。

---

## 4. 向量场预处理（可选）

### 4.1 Curl 校正

很多应用（如 quad-dominant 重网格化）更在意**奇异点少**而非严格等距——每个分叉点都会产生不想要的 T-vertex。归一化后的场，其 curl 只来自方向变化 (directional curl)；**curl 校正**在**保持方向不变**的前提下缩放幅度，让模长变化产生的 modular curl 抵消 directional curl（注意这不同于 Hodge 分解，后者会改方向）。

设单位场 $\vec K$，求标量场 $v$ 使 $\operatorname{curl}(v\vec K)=\vec 0$（收敛区 $v<1$、发散区 $v>1$）。因 $\vec K,\vec K^\perp$ 由 $\operatorname{curl}\vec K=\operatorname{div}\vec K^\perp\cdot\vec N$ 耦合，**同一个 $v$ 同时作用于两者**（复分析上：$\theta,\phi$ 构成 $\vec K$ 的复势，必为共形）。

为得线性公式，curl 校正里另设 $\vec K$ 方向在面内**线性变化**：取面局部正交标架 $(x,y)$，$\vec K=(\cos\gamma,\sin\gamma)$，$\gamma=ax+by+c$。零旋要求（逐面）：

$$
\operatorname{curl}(v\vec K)\cdot\vec N=\Big(-\tfrac{\partial v}{\partial y}+va\Big)\cos\gamma+\Big(\tfrac{\partial v}{\partial x}+vb\Big)\sin\gamma=0.
$$

求与旋转常数 $c$ 无关的解，即满足

$$
-\partial v/\partial y+va=0,\qquad \partial v/\partial x+vb=0,
$$

其解形如 $v=Ce^{ay-bx}$。取对数后 $\nabla\log v=(-b,\ a)$。由于全局零旋未必存在，对 $\tilde v_i=\log v_i$ 做最小二乘：

$$
G(\tilde v)=\sum_T A_T\left\lVert J_T\begin{pmatrix}\tilde v_1\\ \tilde v_2\\ \tilde v_3\end{pmatrix}-J\,J_T\begin{pmatrix}\gamma_1\\ \gamma_2\\ \gamma_3\end{pmatrix}\right\rVert ^2,\quad
J_T=\frac{1}{2A_T}\begin{pmatrix}y_2-y_3&y_3-y_1&y_1-y_2\\ x_3-x_2&x_1-x_3&x_2-x_1\end{pmatrix},
$$

（$J=\big(\begin{smallmatrix}0&-1\\1&0\end{smallmatrix}\big)$，$J_T$ 是面上分片线性梯度算子）。设 $\tilde v_1=0$ 解出其余，取 $v_i=\exp(\tilde v_i)$ 并按 $\max v_i$ 归一。最后把 $v$ 代回能量：

$$
F=\int_S\big(\lVert \nabla\theta-\omega v\vec K\rVert ^2+\lVert \nabla\phi-\omega v\vec K^\perp\rVert ^2\big)\,dS,
$$

照 §2 继续求解。**效果**：参数化仍共形但 stretch 略增，奇异点大幅减少（如 octopus 由 27 降到 0，图 8）。

### 4.2 向量场平滑

主曲率方向在**各向同性区**（$|k_{\max}/k_{\min}|-1\to0$）无定义。平滑过程把方向从各向异性区**外推**到各向同性区，并允许等值取模 $2\pi$/$\pi$/$(\pi/2)$。

对每个顶点设变量 $\alpha_i$ = $\vec K_i$ 与切平面内参考方向 $\vec H_i$ 的夹角（$\vec H_i$ 由某出边投影到切平面得到）。最小化"拟合 + 平滑"能量：

$$
R=(1-\rho)\underbrace{\sum_i\big|k_{\max i}/k_{\min i}\big|\,\big\lVert (\cos\alpha_i,\sin\alpha_i)-(\cos\alpha_i^0,\sin\alpha_i^0)\big\rVert ^2}_{\text{拟合项（按各向异性加权）}}
+\rho\underbrace{\sum_T R_T}_{\text{平滑项}},
$$

平滑项 $R_T=\sum_i\lambda_i^T R_{T,i}$（$\lambda_i^T$ 同附录 B），其边项

$$
R_{T,i}=\left\lVert \binom{\cos\alpha_{i\oplus2}}{\sin\alpha_{i\oplus2}}-\begin{pmatrix}\cos\beta_i&\sin\beta_i\\ -\sin\beta_i&\cos\beta_i\end{pmatrix}\binom{\cos\alpha_{i\oplus1}}{\sin\alpha_{i\oplus1}}\right\rVert ^2,\quad
\begin{cases}\cos\beta_i=\vec H_{i\oplus1}\cdot\vec H_{i\oplus2}\\ \sin\beta_i=(\vec H_{i\oplus1}\times\vec H_{i\oplus2})\cdot\vec N_T\end{cases}
$$

$\beta_i$ 是两参考方向夹角。用 §2.5 同样的 Newton + 罚项求解（$\rho=0.8$），罚项同样把奇异点均匀分布。解出后 $\vec K_i=\cos\alpha_i\,\vec H_i+\sin\alpha_i\,\vec H_i\times\vec N_i$，$\vec K_i^\perp=\vec N_i\times\vec K_i$。

> **取模与奇异点指标（Hopf-Poincaré）**：取模 $2\pi$ 得**极点 (pole)**（绕一圈转 $2\pi$）；改求 $\tilde\alpha_i=2\alpha_i$（模 $\pi$）得**半极点 half-pole**、$\tilde\alpha_i=4\alpha_i$（模 $\pi/2$）得**四分之一极点 quarter-pole**（实现上即把所有 $\alpha_i^0,\beta_i$ 除以 2 或 4，求解后再乘回）。球面上分别得 2 个极点、4 个半极点、8 个四分之一极点——按指标加权之和恒为 $2-2g$。做帽子的人正是用四个 quarter-pole 而非引入"分叉"奇异点。

---

## 5. 应用：曲率对齐的 Quad-Dominant 隐式重网格化

曲率对齐能改善逼近收敛 (d'Azevedo 2000)。以往显式做法 (Alliez 2003) 用 Runge-Kutta 沿主方向积分 **streamline**，难点是均匀布线、greedy seeding 导致分布不均、易漏掉细特征（图 13 左）。

PGP 给出**隐式**方案，无需积分 tracing：

1. 求 sin/cos、逐三角形参数化（§2,§3.1），**可跳过 chart 布局与奇异修复**；
2. 直接提取 iso-$\theta$、iso-$\phi$ 线（密度由用户指定，代替 $2k\pi$）作为初始多边形网格；
3. 非四边形面拆成 quad + triangle；
4. T-vertex 通过插入三角形处理。

因参数化拟共形，**除奇异点近邻外处处得到良形四边形**；多数元素近乎完美正方形、对齐曲率；同一参数化只改提取密度即得多分辨率结果；能捕获极细特征（如 hand 模型掌骨的管状结构）——这是显式 streamline 法易失败之处。

---

## 6. 与 MIQ 的核心区别

| | **PGP** (Ray 2006) | **MIQ** (Bommes 2009) |
|:---|:---|:---|
| 替代变量 | 顶点上 $U=(\cos\theta,\sin\theta),V=(\cos\phi,\sin\phi)$ | 直接优化 $\theta,\phi$ 与边上整数 |
| 周期性 ($2\pi$) | 三角函数**自动内建** | 显式写成边整数平移 $p_{ij}$ |
| 旋转歧义 ($\pi/2$) | 每三角形局部旋转控制场 $r_i$ | Phase 1 period jump；Phase 2 用 $r_e$ |
| 整数变量 | 优化时**不出现**，重建时隐式定 | 显式**混合整数二次规划** |
| 求解 | 二次能量 + Newton 罚项 | 贪心混合整数 + 局部 Gauss-Seidel |
| 奇异点 | 事后检测 + 重参数化 | Phase 1 求解中由 $p_{ij}$ 自然确定 |

**取舍**：PGP 避开了混合整数优化的复杂性、求解为连续优化；MIQ 对 quad layout 有更显式的控制。

---

## 7. 性能与失真（论文 Table I，1.7 GHz）

| Model | $\sharp\triangle$ | 方法 | Stretch | Shear | 时间 |
|:---|:---|:---|:---|:---|:---|
| Horse | 20K | Gu et al. | 6.777 | 0.07 | — |
| | | **PGP** | 1.07 | 0.20 | 45 s |
| | | ccPGP | 1.176 | 0.12 | 53 s |
| Bunny | 25K | Gu et al. | 2.65 | 0.042 | — |
| | | **PGP** | 1.029 | 0.167 | 58 s |
| | | ccPGP | 1.14 | 0.14 | 1m12s |
| Bull | 34.5K | Sander et al. | 1.030 | 0.156 | 1m11s |
| | | **PGP** | 1.064 | 0.177 | 1m26s |
| | | ccPGP | 1.209 | 0.089 | 1m35s |
| Camel | 78K | Sander et al. | 1.053 | 0.227 | 3m51s |
| | | **PGP** | 1.048 | 0.160 | 5m46s |
| | | ccPGP | 1.654 | 0.071 | 6m51s |
| David | 200K | **PGP** | 1.121 | 0.240 | 17m35s |
| | | ccPGP | 1.270 | 0.131 | 20m43s |
| Lion | 400K | **PGP** | 1.123 | 0.173 | 33m42s |
| | | ccPGP | 1.425 | 0.083 | 45m18s |

> ccPGP = 带 curl 校正的 PGP。相比 Gu & Yau 的全局共形参数化，PGP 的 **stretch 显著更低**（shear 略高）；curl 校正后 shear 进一步降低、奇异点大幅减少，但 stretch 增大。奇异点普遍只占三角形的 2–3%。

---

## 附录 A：分片线性向量场的积分（同极小点证明）

设面 $T$ 上分片线性场 $\vec K$、其面均值 $\vec K_T$，则 $F_T=\int_T(\nabla\theta-\omega\vec K)^2ds$ 与 $F_T'=\int_T(\nabla\theta-\omega\vec K_T)^2ds$ 同极小点：

$$
F_T=\int_T(\nabla\theta-\omega\vec K_T)^2ds+2(\nabla\theta-\omega\vec K_T)^{\!\top}\!\!\int_T(\omega\vec K_T-\omega\vec K)ds+\int_T(\omega\vec K_T-\omega\vec K)^2ds.
$$

首项即 $F_T'$；中项因 $\vec K_T$ 是均值而**消失**；末项与 $\theta$ 无关。故 $F_T=F_T'+\text{const}$，同极小点。$\blacksquare$

## 附录 B：面积分能量与 $\lambda_i^T$（式 24）

面能量写成边能量线性组合 $F_T=\sum_{i=1}^3\lambda_i^T(F^\theta_{T,i}+F^\phi_{T,i})$，其中 $(\lambda_1^T,\lambda_2^T,\lambda_3^T)$ 解

$$
\begin{pmatrix}e_{1,x}^2&e_{2,x}^2&e_{3,x}^2\\ e_{1,y}^2&e_{2,y}^2&e_{3,y}^2\\ 2e_{1,x}e_{1,y}&2e_{2,x}e_{2,y}&2e_{3,x}e_{3,y}\end{pmatrix}
\begin{pmatrix}\lambda_1^T\\ \lambda_2^T\\ \lambda_3^T\end{pmatrix}=\begin{pmatrix}1\\1\\0\end{pmatrix}.
$$

由展开并令两端相等得到。面积分版本相比边版本，对网格各向异性更鲁棒（图 16）。

---

## 附录 C：代码实现与论文的差异

> **注意**：`PGP.cpp` 的实现与 Ray et al. 2006 论文原版思路不同。

| | 论文 PGP | `PGP.cpp` 实现 |
|:---|:---|:---|
| 变量 | 顶点上 $U_i=(\cos\theta_i,\sin\theta_i)$ | 顶点上 $u_i,v_i$（直接坐标） |
| $2\pi$ 平移 | 三角函数自动内建 | **显式整数** $\mathbf p_T\in\mathbb Z^2$（每面） |
| $\pi/2$ 旋转 | 每三角形局部旋转 $r_i$ | **显式整数** $k_T\in\{0,1,2,3\}$（每面） |
| 能量 | $X_i$ 的二次型 + Newton 罚项 | $\lVert \nabla u-\text{target}\rVert ^2$ 的二次型 |
| 整数优化 | 不存在（事后 Algorithm 1 重建） | **交替优化**：贪心舍入 $k,p$ ↔ 解线性系统 |
| 求解器 | CG + Newton 外迭代 | Cholesky (SimplicialLDLT) + CG fallback |

**实现本质上是 PGP 目标的另一种离散化**：把论文用 $\sin/\cos$ 隐式处理的平移、旋转自由度，改成显式的**每面**整数变量 $k_T,\mathbf p_T$，再交替优化。这更接近 MIQ 的思路（显式整数跳变），但落在**面**而非**边**上。求解流程：

```
1. 初始：k=0, p=0，解 L u = b_u, L v = b_v
2. for iter in 1..maxIters:
   a. 固定 u,v → 逐面贪心舍入最优 (k, p)（对每个 k 尝试 p 的 ±1 邻域）
   b. 固定 k,p → 解线性系统得新 u,v
   c. 固定 u,v → 对每个 p_T 做 ±1 局部搜索接受降能
   d. 固定 k,p → 再解一次线性系统
```

能量（每面）：

$$
E=\sum_T A_T\Big[\big\lVert \nabla u_T-\big(R(k_T\pi/2)\,\mathbf d_T^u+\mathbf p_T\big)\big\rVert ^2+\big\lVert \nabla v_T-\big(R(k_T\pi/2)\,\mathbf d_T^v+\mathbf p_T\big)\big\rVert ^2\Big].
$$

实现位于 `cpp/conformal-parameterization/Parameterization/GlobalFieldsParam/PGP.cpp`。
