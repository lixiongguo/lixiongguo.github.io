## Tong06

Tong06 希望通过两个 0-form \(u,v\) 的等值线生成四边形网格。直观地说，\((u,v)\) 是参数域坐标，\(u=\text{const}\) 与 \(v=\text{const}\) 两组等值线相交后形成 quad layout。

但如果要求 \(u,v\) 在整个闭合曲面上都是全局连续的 harmonic scalar potential，就会过于受限。例如在亏格为 0 的闭合曲面上，除了常数函数以外不存在有用的全局连续调和势函数。因此，仅靠全局连续的 \(u,v\) 不能生成有意义的四边形网格。

经典处理办法是加入 **pole singularity**：这相当于在曲面上打小孔。例如在球面顶部和底部各引入一个 pole 后，剩下的区域可以有全局连续的 harmonic potential \(u\)，其极值位于两个 pole，流线类似经线。但对应的 \(v\) 不能仍然全局连续，因为 \(dv\) 的闭合流线对应纬线。要真正推广等值线网格化方法，就必须允许 \(u,v\) 只在 patch 内连续，而在 patch 边界上以受控方式发生不连续。

因此，Tong06 的思路是：手动或自动设计 **singularity graph**，用它把曲面切分成若干 patch；在每个 patch 内求 harmonic potentials \(u,v\)，并在 patch 边界上施加特定的 singular continuity 条件。最后通过 \((u,v)\) 的整数等值线 tiling 出全局四边形网格。

## 利用微分形式对连续性分类

沿两个相邻 patch 的公共边界，\(u,v\) 的连续性可以分为三种基本类型：

1. **regular**：两个 patch 中的 \(u\) 方向和 \(v\) 方向分别匹配。
2. **reverse**：跨边界后 \(u,v\) 方向都反向。
3. **switch**：跨边界后 \(u\) 与 \(v\) 互换。

这些条件都是为了保证局部等值线在跨越 patch 边界时仍能拼成合法的四边形结构。

### Free Vertices

若顶点 \(i\) 位于某个 patch 内部，即不在任何 singularity line 上，则只需强制两个 0-form \(u,v\) 都满足 harmonicity。对应的离散 Laplace 方程为：

$$
\sum_{j\in N(i)} w_{ij}
\begin{pmatrix}
u_i-u_j\\
v_i-v_j
\end{pmatrix}
=0.
$$

这里 \(w_{ij}\) 是 cotangent Laplacian 或其他离散 Laplace 权重。

### Regular Singular Line

regular continuity 表示跨 patch 边界时，\(u\) 与 \(v\) 分别保持光滑，但允许相差常数偏移。设同一边界顶点在边界两侧的值分别为 \((u^-,v^-)\) 与 \((u^+,v^+)\)，则要求：

$$
u^- - u^+ = P_1,\qquad v^- - v^+ = P_2.
$$

其中 \((P_1,P_2)\) 是该 singularity line 上的常数平移。它保证跨边界后参数线不改变方向，只发生平移。

### Reverse Continuity

reverse continuity 表示跨 patch 边界时，两个 0-form 都改变方向。也就是说，边界两侧的参数方向相反，但仍然保持同一组 \(u/v\) 方向。可以理解为：

$$
du^+ = -du^-,\qquad dv^+ = -dv^-.
$$

在离散 Laplace 方程中，这会导致来自边界另一侧的邻接项以符号翻转的形式进入。其好处是最终线性系统仍可保持对称 Laplacian 结构，只是右端项出现由 singularity line 常数决定的非零项。

### Switch Continuity

switch continuity 表示跨 patch 边界时，\(u\) 与 \(v\) 互换。对于位于 switch singularity line 上的顶点，要求：

$$
du^+ = dv^-,\qquad dv^+ = -du^-.
$$

注意第二个式子中的负号：交换 \(u,v\) 会反转其中一个方向。若用常数 \(R_1,R_2\) 表示该 singularity line 上的偏移，则可写成：

$$
v^- - u^+ = R_1,\qquad v^+ + u^- = R_2.
$$

为了保证跨越这类不连续线后等值线仍然光滑，仍需对 \(u,v\) 施加 modified harmonicity。其局部形式可写为：

$$
\sum_{j\in N^-(i)} w_{ij}
\begin{pmatrix}
u_i-u_j\\
v_i-v_j
\end{pmatrix}
+
\sum_{j\in N^+(i)} w_{ij}
\begin{pmatrix}
u_i+v_j\\
v_i-u_j
\end{pmatrix}
=
\sum_{j\in N^+(i)} w_{ij}
\begin{pmatrix}
R_2\\
R_1
\end{pmatrix}.
$$

其中 \(N^-(i)\) 表示与当前 patch 同侧的邻接顶点，\(N^+(i)\) 表示跨过 singularity line 后的邻接顶点。

## Singularity 的性质

虽然上述几种连续性条件很简单，但它们已经能表达丰富的 singularity。特别地，前面提到的“带两个 pole 的 genus-0 曲面”可以通过一条连接两个 pole 的 singularity line 来处理。这条虚拟切线使球面变成一个沿 regular continuity 边界自接触的单一 patch。

在这种设定下，\(u,v\) 可以通过求解 modified Laplace equation 在每个顶点上得到；位于 singularity line 上的顶点会拥有不同的系数和非零右端项。

singularity line 的重要性质是：当 \(u,v\) 跨越它发生变化时，虽然势函数值本身改变了，但等值线仍可与之前保持完全相同。因此，它本质上是参数函数的受控不连续，而不是网格线的断裂。

## Singularity Graph

Singularity Graph 可以认为是一个 meta mesh：它的 meta-face 是原始网格上互不重叠的 patch，meta-edge 则被赋予一种 singular continuity 类型，即 regular、reverse 或 switch。

给定 singularity graph 后，需要为每条 meta-edge 指定连续性类型。这可以通过先给每个 meta-halfedge 标记为 \(u,-u,v,-v\) 中的一种来自动完成。标记依据是该 halfedge 与参数方向的对齐关系，即它沿着 \(u\)、\(-u\)、\(v\) 还是 \(-v\) 方向。

理想情况下，每个 meta-face 应该能映射成参数域中的正交多边形，且所有角度都是 \(\pi/2\) 的整数倍。边界到底选择与 \(u\) 还是 \(v\) 对齐，不影响最终四边形网格，因为整个多边形可以整体旋转 \(\pi/2\) 的整数倍。

给定一对 halfedge 标记后，meta-edge 的 singular continuity 类型可以按如下规则确定：

- **Regular**：\(\{u,-u\},\{-u,u\},\{v,-v\},\{-v,v\}\)。
- **Reverse**：\(\{u,u\},\{v,v\},\{-u,-u\},\{-v,-v\}\)。
- **Switch**：\(\{u,v\},\{v,-u\},\{-u,-v\},\{-v,u\}\)，以及对称情形 \(\{-u,v\},\{-v,-u\},\{u,-v\},\{v,-u\}\)。

这样，singularity graph 就把“patch 如何拼接”的拓扑信息转化为了线性系统中的边界条件。

## 算法

最终要求解一个线性系统：

$$
AU=B,
$$

其中 \(A\) 是 modified Laplacian matrix，\(U\) 同时包含所有未约束顶点的 \(u\) 与 \(v\) 值。组装矩阵时，对每条半边 \((v_i,v_j)\)：

1. 取权重 \(c=w_{ij}\)，初始化符号 \(\epsilon_u=\epsilon_v=1\)，右端项 \(b_u=b_v=0\)。
2. 如果 \(i\) 或 \(j\) 位于 singularity line 上，但二者不在同一条 line 上，则根据该顶点所在的连续性类型修改符号、交换变量或加入常数右端项。
3. 对 regular continuity，加入平移常数 \((P_1,P_2)\)。
4. 对 reverse continuity，翻转 \(\epsilon_u,\epsilon_v\)，并加入 \((Q_1,Q_2)\)。
5. 对 switch continuity，交换 \(u,v\) 的耦合关系，并加入 \((R_1,R_2)\)。
6. 最后把对应项写入 \(A\) 与 \(B\)。

因此，Tong06 的算法可以概括为：

1. 设计或生成 singularity graph，将曲面分成若干 patch。
2. 为每条 meta-edge 指定 regular / reverse / switch 连续性。
3. 根据这些连续性条件组装 modified Laplacian。
4. 求解两个分段连续的 harmonic potentials \(u,v\)。
5. 提取 \(u,v\) 的整数等值线，得到无缝的四边形网格。

