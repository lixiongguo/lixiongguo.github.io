# NeRF

> 对应原始论文 Mildenhall et al., *NeRF*, ECCV 2020。  
> 索引：[Nerf.md](Nerf.md)

NeRF 能端到端做新视角合成，靠三块咬合在一起的设计：**连续场表示**、**可微体渲染**、**沿射线的采样策略**。缺一块就训不动或画不清。

## 1. MLP 辐射场表示

### 1.1 函数形式

场景被建成可学习映射

$$
F_\theta:(\mathbf{x},\mathbf{d})\mapsto\bigl(c(\mathbf{x},\mathbf{d}),\,\sigma(\mathbf{x})\bigr).
$$

| 符号 | 含义 |
|:---|:---|
| $\mathbf{x}\in\mathbb{R}^3$ | 世界坐标位置 |
| $\mathbf{d}$ | 单位视线方向（常作笛卡尔分量） |
| $\sigma(\mathbf{x})\ge 0$ | 体密度，只随位置变 |
| $c\in[0,1]^3$ | 沿 $\mathbf{d}$ 观察到的 RGB |

密度与方向解耦：同一点从不同方向看可以颜色不同（高光、非朗伯），但「有没有东西」由 $\sigma$ 决定。原始实现里 MLP 约 8 层宽 256，中间有 skip connection；方向在较深层才拼进去预测颜色。

### 1.2 为什么需要位置编码

深层网络偏爱低频函数（Spectral Bias）。直接喂 $(x,y,z)$ 会得到过平滑的一团雾，细纹理拟合不动。NeRF 用傅里叶特征（positional encoding）：

$$
\gamma(p)=\bigl(
\sin(2^0\pi p),\cos(2^0\pi p),\ldots,
\sin(2^{L-1}\pi p),\cos(2^{L-1}\pi p)
\bigr),
$$

对每个坐标分量（及方向分量）做 $L$ 级（位置常用 $L=10$，方向 $L=4$），再送入 MLP。直观上：给网络一套可组合的高频基，细节才写得进场。

### 1.3 优化目标（与表示的关系）

参数 $\theta$ 不直接拟合点云，而是让**渲染结果**对齐训练图像：

$$
\mathcal{L}=\sum_{\mathbf{r}}\bigl\|\hat C(\mathbf{r})-C_{\mathrm{gt}}(\mathbf{r})\bigr\|_2^2.
$$

因此表示必须能嵌入一条可微的「点 → 像素」渲染链——即下一节体渲染。

### 1.4 局限（留给后续工作）

- 大 MLP + 每射线数百次查询 → 训练 / 推断都慢 → [Nerf_NSVF.md](Nerf_NSVF.md)（稀疏八叉树跳空）、[Nerf_InstantNGP.md](Nerf_InstantNGP.md)、[Nerf_Plenoxels.md](Nerf_Plenoxels.md)。  
- $\sigma$ 场表面模糊 → 抽 mesh 差 → [Nerf_NeuS.md](Nerf_NeuS.md)。  
- 理想细射线 → 多尺度锯齿 → [Nerf_MipNeRF.md](Nerf_MipNeRF.md)。

## 2. Ray Marching 与体渲染

### 2.1 连续形式

像素对应相机射线 $\mathbf{r}(t)=\mathbf{o}+t\mathbf{d}$，$t\in[t_n,t_f]$。经典体积渲染：

$$
\hat C(\mathbf{r})
=\int_{t_n}^{t_f}
T(t)\,\sigma\bigl(\mathbf{r}(t)\bigr)\,
c\bigl(\mathbf{r}(t),\mathbf{d}\bigr)\,dt,
$$

透射率

$$
T(t)=\exp\!\left(-\int_{t_n}^{t}\sigma\bigl(\mathbf{r}(s)\bigr)\,ds\right)
$$

表示「从相机走到 $t$ 还没被挡住的概率」。$T\sigma\,c$ 即该处贡献的颜色。

### 2.2 离散 α-compositing

在采样点 $t_i$ 上，段长 $\delta_i=t_{i+1}-t_i$，定义

$$
\alpha_i=1-\exp(-\sigma_i\delta_i),\qquad
T_i=\prod_{j=1}^{i-1}(1-\alpha_j),
\qquad
\hat C=\sum_i T_i\alpha_i c_i.
$$

也可额外渲染期望深度 $\hat D=\sum_i T_i\alpha_i t_i$ 等辅助量。前到后累乘 $T$ 时，若累积不透明度接近 1 可提前终止（加速推断）。

### 2.3 为何「可微」关键

$\hat C$ 对 $\{c_i,\sigma_i\}$、进而对 $\theta$ 可导（注意 $\alpha$ 对 $\sigma$ 的指数形式）。训练时随机抽一批像素射线，渲出色与 GT 比损失，反传更新场——**无需**显式深度监督（当然加深度会更稳）。

### 2.4 与传统图形学的关系

形式来自吸收式体积渲染（emission-absorption）；NeRF 把介质参数交给神经网络，用多视角照片当监督。和光栅化 mesh 不同：几何藏在密度里，遮挡由积分自动处理。

## 3. 采样：Stratified + Hierarchical

积分质量几乎完全取决于沿射线采在哪。

### 3.1 Stratified sampling

把 $[t_n,t_f]$ 切成 $N$ 个等宽箱，第 $i$ 箱内

$$
t_i\sim\mathcal{U}\Bigl[t_n+\frac{i-1}{N}(t_f-t_n),\;
t_n+\frac{i}{N}(t_f-t_n)\Bigr].
$$

相对固定等距采样：减少与场景结构共振造成的条纹，并在期望上覆盖整段区间。

### 3.2 Hierarchical volume sampling（coarse → fine）

仅均匀采样会浪费大量空空间查询。NeRF 用两套网络 / 两阶段：

1. **Coarse**：较少 stratified 点，渲染得到权重 $w_i=T_i\alpha_i$。  
2. 把 $\{w_i\}$ 归一化成分段常数 PDF，对 $t$ 做**逆变换采样**，得到偏向高贡献区域的新样本。  
3. **Fine**：合并 coarse 点与新点，再查网络并渲染；coarse、fine 的 $\hat C$ 都进损失。

效果：样本自动贴到表面附近，同等查询预算下细节更好。

### 3.3 实践数字（原始设定量级）

- Coarse / fine 各约 64 点量级（论文设定随实现略有出入）；  
- 每迭代数万条射线；一张 $800\times 800$ 图推断需上亿次 MLP 前向 → 慢的根源。

## 4. 串起来的训练心智模型

```text
位姿已知的训练图
    → 随机像素 → 射线 (o, d)
    → stratified 采样
    → coarse MLP → 权重 PDF
    → 重要性采样 + fine MLP
    → 体渲染 Ĉ_coarse, Ĉ_fine
    → ‖Ĉ − C_gt‖²
    → 反传更新 θ
```

推断时通常只用 fine（或单网络变体），整图每个像素一条射线积分。

## 5. 一句话

**MLP（加位置编码）回答「这点什么颜色、多密」；体渲染把沿射线的答案积成像素；分层 + 粗到细采样决定算力花在真正有面的地方。**
