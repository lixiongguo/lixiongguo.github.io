我们要研究的三角网格由一个个三角形构成，作用在其上的映射可以认为是分别作用在逐个三角形上，在每个三角形上都是一个简单的线性变换，所以可以认为我们要研究的映射是一个**分段线性映射(Piecewise Linear Mapping)**。

![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20260528143757423.png)



接下来为了定义三角网格上的调和映射，我们先定义分段线性映射的梯度算子然后再定义其上的散度算子。

### 离散梯度(Gradient)

分段线性映射给出了顶点的值后，三角形内部的函数值可以通过**重心坐标（Barycentric Coordinate）**进行线性插值求得，梯度算子是线性算子，所以我们也用重心坐标进行插值。

![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250317142741458.png)

重心坐标 $\alpha$ 可以认为是小三角形与大三角形之间的**面积比**

$$
\alpha = \frac{A_i}{A_t} = \frac{\left( (\mathbf{x} - \mathbf{x}_j) \cdot \frac{(\mathbf{x}_k - \mathbf{x}_j)^\perp}{\|\mathbf{x}_k - \mathbf{x}_j\|} \right) \|\mathbf{x}_k - \mathbf{x}_j\|}{2 A_T} = \frac{(\mathbf{x} - \mathbf{x}_j) \cdot (\mathbf{x}_k - \mathbf{x}_j)^\perp}{2 A_T}
$$

其中 $A_t$ 是三角形有向面积
$$
A_t = \frac {1} {2}[ (x_iy_j - y_ix_j) + (x_jy_k - y_jx_k) + (x_ky_i - y_kx_i)]
$$
以重心坐标作为插值权重，分段线性映射可以表达为各顶点函数值关于重心坐标的线性组合

$$
f(x) = \alpha f_i + \beta f_j + \gamma f_k
$$

将**梯度算子 $\nabla$**作用于其上可得

$$
\begin{aligned}
\nabla f(\mathbf{x}) &= f_i \nabla \alpha + f_j \nabla \beta + f_k \nabla \gamma \\
\nabla \alpha &= \frac{(\mathbf{x}_k - \mathbf{x}_j)^\perp}{2A_T},\quad \nabla \beta = \frac{(\mathbf{x}_i - \mathbf{x}_k)^\perp}{2A_T},\quad \nabla \gamma = \frac{(\mathbf{x}_j - \mathbf{x}_i)^\perp}{2A_T}
\end{aligned}
$$

因此

$$
\nabla f(\mathbf{x}) = f_i \frac{(\mathbf{x}_k - \mathbf{x}_j)^\perp}{2A_T} + f_j \frac{(\mathbf{x}_i - \mathbf{x}_k)^\perp}{2A_T} + f_k \frac{(\mathbf{x}_j - \mathbf{x}_i)^\perp}{2A_T}
$$

![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20260529131919554.png)

### 离散散度(Divergence)

以下证明来自《Polygon Mesh Processing》,根据**散度定理(Divergence Theorem,又称高斯定理)**

$$
\int_{A_i} \operatorname{div} \mathbf{F}(\mathbf{u})\,\mathrm{d}A = \int_{\partial A_i} \mathbf{F}(\mathbf{u}) \cdot \mathbf{n}(\mathbf{u})\,\mathrm{d}s \tag{3}
$$

对于下面的顶点的小领域 $A_i$ 采用**Mixed Voronoi Cell**

![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250318142418809.png)

Mixed Voronoi Cell可以认为是某个顶点所有相邻边的中垂线围成的该顶点的一个领域，下图为单个三角形 $T$ 局部的情况

![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250318142917334.png)

那么对于Laplace算子则有

$$
\int_{A_i} \Delta f(\mathbf{u}) \,\mathrm{d}A = \int_{A_i} \operatorname{div} \nabla f(\mathbf{u}) \,\mathrm{d}A = \int_{\partial A_i} \nabla f(\mathbf{u}) \cdot \mathbf{n}(\mathbf{u}) \,\mathrm{d}s
$$

$\mathbf{n}$ 的朝向向外。

对每一个部分分别进行计算

$$
\begin{aligned}
\int_{\partial A_i \cap T} \nabla f(\mathbf{u}) \cdot \mathbf{n}(\mathbf{u})\,\mathrm{d}s
&= \nabla f(\mathbf{u}) \cdot (\mathbf{a} - \mathbf{b})^\perp
=\frac{1}{2}\, \nabla f(\mathbf{u}) \cdot (\mathbf{x}_j -\mathbf{x}_k)^\perp
\end{aligned}
$$

将之前计算的导数代入进去则有

$$
\begin{aligned}
\int_{\partial A_i \cap T} \nabla f(\mathbf{u}) \cdot \mathbf{n}(\mathbf{u})\,\mathrm{d}s
= &\, (f_j - f_i)\,\frac{(\mathbf{x}_i - \mathbf{x}_k)^\perp \cdot (\mathbf{x}_j - \mathbf{x}_k)^\perp}{4A_T}  + (f_k - f_i)\,\frac{(\mathbf{x}_j - \mathbf{x}_i)^\perp \cdot (\mathbf{x}_j - \mathbf{x}_k)^\perp}{4A_T}
\end{aligned} \tag{4}
$$

记 $\gamma_j,\gamma_k$ 分别为顶点 $v_j,v_k$ 处的内角。

由三角形面积公式

$$
A_t = \tfrac{1}{2}\sin\gamma_j \,\|\mathbf{x}_j - \mathbf{x}_i\|\,\|\mathbf{x}_j - \mathbf{x}_k\| = \tfrac{1}{2}\sin\gamma_k \,\|\mathbf{x}_i - \mathbf{x}_k\|\,\|\mathbf{x}_j - \mathbf{x}_k\|
$$

以及余弦定律

$$
\cos\gamma_j = \frac{(\mathbf{x}_j - \mathbf{x}_i)\cdot(\mathbf{x}_j - \mathbf{x}_k)}{\|\mathbf{x}_j - \mathbf{x}_i\|\,\|\mathbf{x}_j - \mathbf{x}_k\|}, \cos\gamma_k = \frac{(\mathbf{x}_i - \mathbf{x}_k)\cdot(\mathbf{x}_j - \mathbf{x}_k)}{\|\mathbf{x}_i - \mathbf{x}_k\|\,\|\mathbf{x}_j - \mathbf{x}_k\|}
$$

可得

$$
\int_{A_i} \Delta f(\mathbf{u})\,\mathrm{d}A = \frac{1}{2} \sum_{v_j \in \mathcal{N}_1(v_i)} (\cot \alpha^{ij} + \cot \beta^{ij})(f_j - f_i)
$$

从而我们最终得到**Laplace–Beltrami 算子**在三角网格上的离散化为(我们去掉前面常系数，并不影响结论)

$$
\Delta f(v_i) := \frac {1} {2 A_i} \sum_{v_j \in \mathcal{N}_1(v_i)} (\cot \alpha^{ij} + \cot \beta^{ij})(f_j - f_i) \tag{5}
$$

对于任意有向边$e_{ij}$,我们可以定义其**余切边权重$w_{ij}$(cotangent weight)**也称为**cot权重**

$$
w_{ij} = \cot\alpha_{ij} + \cot\beta_{ij} \tag{6}
$$

对于边界顶点少了一个外侧领居，所以会少一项。

![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20260624153345515.png)