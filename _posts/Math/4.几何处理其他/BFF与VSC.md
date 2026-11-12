
## 边界自动调整方法 BFF (Boundary First Flattening)

曲面到平面的共形映射**不是唯一的**：圆盘型曲面 $M$ 可共形映到单位圆盘，也可映到任意单连通平面区域；区域之间同样存在共形对应。棋盘格交角处处保持直角，**平面边界形状是可控的**。

<img src="https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20260620212253121.png" alt="image-20260620212253121" style="zoom:50%;" />

## 理论分析

### 从 Cauchy–Riemann 到共轭调和对

<img src="/Users/lgxgeogo/Desktop/MyDoc/lixiongguo.github.io/imgs//image-20260717222501338.png" alt="image-20260717222501338" style="zoom:50%;" />

设 $f=a+b\mathrm{i}$，$J$ 为切平面上逆时针旋转 $90^\circ$。全纯条件

$$
df(JX)=\mathrm{i}\,df(X)
$$

对一切切向量 $X$ 成立。左边 $df(JX)=da(JX)+\mathrm{i}\,db(JX)$，右边 $\mathrm{i}(da(X)+\mathrm{i}\,db(X))=\mathrm{i}\,da(X)-db(X)$。比较实虚部：

$$
da(JX)=-db(X),\qquad db(JX)=da(X),
$$

写成梯度即

$$
\nabla a=-J\nabla b\quad\Leftrightarrow\quad J\nabla a=\nabla b.
$$

对第一式取散度：$\nabla\cdot\nabla a=-\nabla\cdot(J\nabla b)$。旋转梯度场无散，故

$$
\Delta a=0;
$$

同理 $\Delta b=0$。于是 $(a,b)$ 为**共轭调和对**：

$$
\Delta a=\Delta b=0,\qquad J\nabla a=\nabla b,\qquad |df|=|\nabla a|=e^u.
$$

右侧耳模型上 $a$、$b$ 标量场与棋盘格 $f$ 即此正交等比坐标网。

### Cherrier 方程：尺度与边界曲率的联系

共形改度量 $\tilde g=e^{2u}g$ 时，**Gauss 曲率与边界测地曲率**的关系由 **Cherrier 方程**（带边 Yamabe）给出：

$$
\begin{aligned}
\Delta u &= K - e^{2u}\widetilde K && \text{on } M,\\
\frac{\partial u}{\partial n} &= \kappa - e^{u}\widetilde\kappa && \text{on } \partial M.
\end{aligned}
$$

我们研究**平坦目标** $\widetilde K=0$ 时内部化为 Poisson 源问题 $\Delta u=K$。

边界式如下
$$
e^{u}\widetilde\kappa=\kappa-\frac{\partial u}{\partial n}.
$$

在离散设定中，顶点上存的是**曲率密度**（外角 / 角盈），长度缩放已并入对偶边长；

$$
\widetilde\kappa=\kappa-\frac{\partial u}{\partial n}\Big|_{\partial M}
$$

对内部方程积分，Green 公式给出

$$
\int_M\Delta u\,dA=\int_{\partial M}\frac{\partial u}{\partial n}\,ds=\int_M K\,dA
\quad(\widetilde K=0).
$$

圆盘 Gauss–Bonnet（$\chi=1$）：$\int_M K\,dA+\int_{\partial M}\kappa\,ds=2\pi$，故

$$
\int_{\partial M}\frac{\partial u}{\partial n}\,ds=2\pi-\int_{\partial M}\kappa\,ds=\Omega,
$$

$\Omega$ 为内部总角盈。

另外注意到目标外角还需 $\sum_i\widetilde\kappa_i=2\pi$，否则平面闭折线无法闭合。

### Poincaré–Steklov 算子 $\Lambda_\Omega$

将 Dirichlet 边界条件与 Neumann 边界条件互换的算子即 Poincaré–Steklov。


**Cherrier 的离散版本**
$$
\widetilde\kappa=\kappa-\Lambda_\Omega u,
\qquad
u=\Lambda_\Omega^\dagger(\kappa-\widetilde\kappa).
$$

## 数值求解

离散 Poisson $Aa=\phi$（$\phi$ 编码角盈等源项）按内部/边界分块后，**Dirichlet-to-Neumann** 由 Schur 补给出（完整消元见[附录](#附录schur-补与-dirichlet–neumann-映射)）：
$$
h=\bigl(A_{IB}^\top A_{II}^{-1}A_{IB}-A_{BB}\bigr)g
\quad(\phi=0),
$$

有源时为仿射映射

$$
\Lambda_\phi g:=\phi_B-A_{IB}^\top A_{II}^{-1}(\phi_I-A_{IB}g)-A_{BB}g.
$$

记带角盈源 $\Omega$ 的该算子为 $\Lambda_\Omega$。



二者互逆（去掉常数零空间后），故长度控制与曲率控制可随时切换，且**共用同一次 Laplace 因子化**。

**曲率驱动**：指定 $\widetilde\kappa$（如均匀 $\widetilde\kappa_i=2\pi/|B|$ 得近似圆边界；角点处集中曲率保留尖角）→ $u=\Lambda_\Omega^\dagger(\kappa-\widetilde\kappa)$ → 积分边界。  
**长度驱动**：指定边界 $u$（或由目标边长换算）→ $\widetilde\kappa=\kappa-\Lambda_\Omega u$ → 积分边界。



前式：给定边界尺度 $u$，调和/Poisson 延拓后读 Neumann，从当前外角 $\kappa$ 中减去即得目标外角。后式：给定目标外角，令 Neumann 数据 $h=\kappa-\widetilde\kappa$，经 Neumann-to-Dirichlet 得边界尺度。伪代码：

![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20251026182335699.png)

### 共轭分量

离散共形能量（LSCM / SCP 型）把 Cauchy–Riemann 写成二次型。令 $A$ 为 cotan-Laplace，$U$ 编码边界多边形的有向面积耦合：

$$
a^\top Ub:=\tfrac12\sum_{ij\in\partial M}(a_jb_i-a_ib_j),
$$

则

$$
E_C(a,b)
=\begin{bmatrix}a^\top&b^\top\end{bmatrix}
\begin{bmatrix}A&U\\U^\top&A\end{bmatrix}
\begin{bmatrix}a\\b\end{bmatrix}
=a^\top Aa+b^\top Ab+2a^\top Ub.
$$

几何上 $E_C$ 度量 $|\nabla a-J\nabla b|$ 的离散 $L^2$ 偏差；$E_C=0$ 当且仅当 $(a,b)$ 为共轭调和对。

**固定 $a$ 对 $b$ 求极小**：$\partial E_C/\partial b=0$ 给出

$$
Ab=-U^\top a.
$$

这是带 Neumann 数据 $h=U^\top a$ 的 Laplace 方程。对边界相邻顶点 $i,j,k$，由 $a^\top Ub$ 对 $b_j$ 求导得

$$
h_j=\tfrac12(a_k-a_i),
$$

即相邻实部差分。解出 $b$ 即为离散 **Hilbert 变换**（由 $a$ 恢复共轭 $b$）；连续极限正是 $\nabla b=(\nabla a)^\perp$。

### 边界到内部的延拓

$\widetilde\gamma$ 已知后，最简做法是对实、虚部各自 Dirichlet 调和延拓：

$$
\Delta a=0,\ a|_{\partial M}=\operatorname{Re}(\widetilde\gamma);
\qquad
\Delta b=0,\ b|_{\partial M}=\operatorname{Im}(\widetilde\gamma).
$$

分块形式即 $A_{II}a_I=-A_{IB}g$（$g=\operatorname{Re}(\widetilde\gamma)$），对 $b$ 同理。  
另一条路：只延拓 $a$，再解 $Ab=-U^\top a$ 得 $b$——二者共用同一 $A$ 的因子。因边界已由 Cherrier 保证相容，延拓后的 $(a,b)$ 近似共轭，映射近似共形。



### 算法流程总览

<img src="https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20260620211906353.png" alt="image-20260620211906353" style="zoom: 33%;" />

1. **边界数据**：Steklov 算子 $\Lambda_\Omega,\Lambda_\Omega^\dagger$ 在尺度 $u$ 与目标曲率 $\widetilde\kappa$ 之间互换，得到相容对；
2. **切向**：对曲率积分得目标边界单位切向 $\widetilde T$；
3. **闭曲线**：再积分 $\int e^u\widetilde T$ 重建 $\widetilde\gamma$；
4. **调和延拓**：$\Delta a=0$ 得 $\operatorname{Re}(f)$；
5. **Hilbert / 共轭**：$\mathcal{H}$ 恢复虚部，合成 $f$

**I. 互补边界数据**  

- 给定 $u$：$\widetilde\kappa\leftarrow\kappa-\Lambda_\Omega u$；  
- 给定 $\widetilde\kappa$：$u\leftarrow\Lambda_\Omega^\dagger(\kappa-\widetilde\kappa)$（先将 $\sum\widetilde\kappa$ 归一化到 $2\pi$）。

**II. 构造边界环**  
$\ell_{ij}^*=e^{(u_i+u_j)/2}\ell_{ij}$，按外角递推切向并积分得闭合 $\widetilde\gamma$。

**III. 全纯延拓**  
调和延拓（或 Hilbert）得到 $f:V\to\mathbb{C}$。

交互编辑（论文 §6.2）把拖拽的边角、边长换成顶点数据：

$$
\widetilde\kappa_i=\theta_{i,i+1}-\theta_{i-1,i},
\qquad
u_{ij}=\log\frac{\ell^*_{ij}}{\ell_{ij}},
\quad
u_j=\frac{\ell^*_{ij}u_{ij}+\ell^*_{jk}u_{jk}}{\ell^*_{ij}+\ell^*_{jk}}.
$$

第二式是「边尺度 → 顶点尺度」的长度加权平均（精确的 $u_i+u_j=2\log(\ell^*_{ij}/\ell_{ij})$ 一般无解，CETM 等亦不能任意钉死全部边长）。曲率归一化到 $2\pi$ 后，用 $\Lambda_\Omega$ 在角度模式与长度模式间切换；每次只需回代。

## Variational Surface Cut (VSC)

用变分法求切割路径 $\gamma$，使展平后度量扭曲最小，**无需显式参数化**。

![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20251010142551440.png)

网球示意：同一球面、不同接缝（哑铃 / Y 型 / 长螺旋）给出不同平面展开。切割本身是扭曲的控制变量。

![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20251010192434507.png)

切割可穿过三角形内部，不限于网格边。

传统方法在边上组合搜索；VSC 在连续曲线上用形状导数直接优化展平扭曲。

### Yamabe 方程与扭曲能量

切开后 $M_\gamma=M\setminus\gamma$ 为圆盘片。共形展平的 log 尺度 $u$ 满足

$$
\Delta u=-K\ \text{on }M_\gamma,\qquad u=0\ \text{on }\partial M_\gamma.
$$

（符号约定：此处 $\Delta$ 取正半定 Laplace–Beltrami，$\Delta u=-\mathrm{div}\nabla u$ 时源为 $+K$；与 BFF 节写法一致时只需统一符号。）边界 $u=0$ 表示切割处等距缩放；Springborn 等证明：固定 $\gamma$ 时，这使面积扭曲的 Dirichlet 能量最小。因此**不必算 $f$**，只需求 $u$。

![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20251010142836409.png)

定义

$$
E_D(\gamma):=\int_{M_\gamma}|\nabla u|^2\,dA.
$$

$E_D=0$ $\Leftrightarrow$ $u$ 为常数 $\Leftrightarrow$ 除整体缩放外无面积畸变。仅最小化 $E_D$ 无下界（加长 $\gamma$ 可任意降扭曲），故加长度正则

$$
E_L(\gamma):=\tfrac12\int_\gamma ds,\qquad
E(\gamma):=E_D(\gamma)+\alpha_L E_L(\gamma).
$$

### 形状导数预备

区域 $\Omega'\subset\Omega$ 沿边界法向以速度 $\sigma$ 变形时，对**不依赖区域的**标量场 $\psi$：

$$
D_\sigma\int_{\Omega'}\psi\,dA=\int_{\partial\Omega'}\psi\,\sigma\,ds,
\qquad
D_\sigma\int_{\partial\Omega'}\psi\,ds=\int_{\partial\Omega'}\Bigl(\frac{\partial\psi}{\partial n}+\kappa\psi\Bigr)\sigma\,ds.
$$

特别地，长度变分 $D_\sigma E_L=\int_\gamma\kappa_\gamma\sigma\,ds$（曲线缩短流）。

若被积函数依赖 PDE 解 $u(\Omega')$，上式不能直接用——需 Céa 方法。

### Céa 方法：从 Lagrangian 到边界速度

![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20251010145117349.png)

考虑 PDE 约束目标

$$
J(\Omega')=\int_{\Omega'}j(u)\,dA,
\qquad
\Delta u=f\ \text{on }\Omega',\quad u=0\ \text{on }\partial\Omega'.
$$

![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20251010192645924.png)

引入乘子 $p$（内部）、$\lambda$（边界），Lagrangian 为

$$
\mathcal{L}_{\Omega'}(u,p,\lambda)
=\int_{\Omega'}j(u)\,dA
+\int_{\Omega'}p(\Delta u-f)\,dA
+\int_{\partial\Omega'}\lambda u\,ds.
$$

**Céa 要点**：在 $\mathcal{L}$ 关于 $(u,p,\lambda)$ 的临界点上，$D_\sigma J=D_\sigma\mathcal{L}$，且可用「$\psi$ 固定」的普通形状导数公式计算——因为临界点处对状态的变分已由伴随方程消掉。

对 $(u,p,\lambda)$ 变分可得伴随问题（依赖 $j$）。对 **Dirichlet 能量** $j(u)=|\nabla u|^2$，伴随简化为：

- 边界乘子 $\lambda=0$（与「边界均匀尺度使 $E_D$ 最小」一致）；
- 不必单独解 $p$（问题自伴随）。

于是一般公式

$$
D_\sigma J=\int_{\partial\Omega'}\Bigl(j(u)+\lambda\frac{\partial u}{\partial n}\Bigr)\sigma\,ds
$$

在切割 $\gamma=\partial M_\gamma$ 上化为

$$
D_\sigma E_D=\int_\gamma|\nabla u|^2\,\sigma\,ds.
$$

又 $u|_{\gamma}\equiv 0$，切向导数为零，故 $|\nabla u|^2=(\partial u/\partial n)^2$，得到

$$
D_\sigma E_D(\gamma)=\int_\gamma\Bigl(\frac{\partial u}{\partial n}\Bigr)^2\sigma\,ds.
$$

切割有两侧 $u^\pm$，法向相对，扭曲项贡献差；加上长度项 $\alpha_L\int\kappa_\gamma\sigma\,ds$，总变分为

$$
D_\sigma E
=\int_\gamma\Biggl[
\underbrace{\Bigl(\frac{\partial u^+}{\partial n}\Bigr)^2}_{\sigma_D^+}
-\underbrace{\Bigl(\frac{\partial u^-}{\partial n}\Bigr)^2}_{\sigma_D^-}
+\underbrace{\alpha_L\kappa_\gamma}_{\sigma_L}
\Biggr]\sigma\,ds.
$$

取最速下降方向 $\sigma^*=\sigma_D^+-\sigma_D^-+\sigma_L$，梯度流为

$$
\boxed{
\frac{d}{dt}\gamma=-\sigma^*\,n,
\qquad
\sigma^*=\Bigl(\frac{\partial u^+}{\partial n}\Bigr)^2-\Bigl(\frac{\partial u^-}{\partial n}\Bigr)^2+\alpha_L\kappa_\gamma.
}
$$

含义：$\lvert\partial u/\partial n\rvert$ 大的一侧（尺度陡变、难展平）推动切割深入该侧；$\kappa_\gamma$ 抑制过度曲折。数值上在三角网格用 Eulerian / level-set 离散积分该流即可。





## 附录

### Poisson 方程离散化

$\Delta a=\phi$ 离散为 $Aa=P\phi$，$A$ 为 cotan-Laplace：

$$
A_{ij}=-\tfrac12\bigl(\cot\beta_p^{ij}+\cot\beta_q^{ij}\bigr),\quad
A_{ii}=-\sum_{j\sim i}A_{ij}.
$$

省略边界对偶边上的 cotan 贡献即对应**零 Neumann**组装。BFF 右端多用已积分的曲率密度，常可不显式出现 $P$。顶点按内部 $I$ / 边界 $B$ 分块后：

- **Neumann**：$Aa=[\phi_I;\ \phi_B-h]$（$h$ 为对偶边界边上的 $\int\partial a/\partial n$）；
- **Dirichlet**：$a_B=g$ 已知时 $A_{II}a_I=\phi_I-A_{IB}g$。

### Schur 补与 Dirichlet–Neumann 映射

纯 Neumann 有常数零空间，需固定锚点或加罚项。下文 $\Lambda_\Omega$ 的 Schur 补正是在此分块上消去 $a_I$ 得到的。



对可逆分块系统
$$
\begin{bmatrix}A&B\\C&D\end{bmatrix}
\begin{bmatrix}x\\y\end{bmatrix}
=
\begin{bmatrix}p\\q\end{bmatrix},
$$

由第一行 $x=A^{-1}(p-By)$ 代入第二行：

$$
\bigl(D-CA^{-1}B\bigr)y=q-CA^{-1}p.
$$

$S:=D-CA^{-1}B$ 为 $A$ 的 **Schur 补**——消去 $x$ 后 $y$ 的约化系数。

### 应用到 cotan-Laplace

$$
\begin{bmatrix}
A_{II}&A_{IB}\\
A_{IB}^\top&A_{BB}
\end{bmatrix}
\begin{bmatrix}a_I\\a_B\end{bmatrix}
=
\begin{bmatrix}\phi_I\\\phi_B\end{bmatrix}.
$$

已知 Dirichlet 数据 $a_B=g$ 时，

$$
a_I=A_{II}^{-1}(\phi_I-A_{IB}g).
$$

第二行残差在零 Neumann 组装约定下即离散 Neumann 数据 $h$：

$$
\begin{aligned}
h
&=\phi_B-A_{IB}^\top a_I-A_{BB}g\\
&=\phi_B-A_{IB}^\top A_{II}^{-1}(\phi_I-A_{IB}g)-A_{BB}g
=\Lambda_\phi g.
\end{aligned}
$$

$\phi=0$ 时

$$
h=\bigl(A_{IB}^\top A_{II}^{-1}A_{IB}-A_{BB}\bigr)g
=-\bigl(A_{BB}-A_{IB}^\top A_{II}^{-1}A_{IB}\bigr)g,
$$

括号内为边界相对 $A_{II}$ 的 Schur 补。反向：把 $h$ 并入右端解整域问题，取 $a_B$，即 $\Lambda^\dagger$。预因子化后每次求值只需回代——BFF 实时改边界的数值基础。更一般分块分解见 [线性方程组 $Ax=b$](../6.附录-数值计算与最优化/2016-06-11-线性方程组Ax=b.md)。
