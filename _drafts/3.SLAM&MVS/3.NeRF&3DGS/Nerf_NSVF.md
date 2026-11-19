# NeRF：Neural Sparse Voxel Fields（NSVF）

> Lingjie Liu\*, Jiatao Gu\*, Kyaw Zaw Lin, Tat-Seng Chua, Christian Theobalt.  
> *Neural Sparse Voxel Fields*, NeurIPS 2020.  
> 项目页：[vcai.mpi-inf.mpg.de/projects/NSVF](https://vcai.mpi-inf.mpg.de/projects/NSVF/) · 代码：[facebookresearch/NSVF](https://github.com/facebookresearch/NSVF) · [arXiv:2007.11571](https://arxiv.org/abs/2007.11571)  
> 索引：[Nerf.md](Nerf.md) · 前置：[Nerf_三大组成部分.md](Nerf_三大组成部分.md)

原始 NeRF 用**一个全局 MLP** 描述整场景，射线在近远平面间均匀 / 分层采样，大量查询落在空空间。NSVF（刘玲杰等）的核心回答是：把隐式场**拴在稀疏体素八叉树上**——只在有内容的格子里做体渲染，空格子直接跳过。推断相对 NeRF 常 **>10×** 加速，画质也往往更好，并天然支持编辑与多场景共享解码器。

## 1. 动机：空空间才是慢的主因

体渲染积分要在非空区域密采样才能画清。NeRF 虽有 coarse→fine 重要性采样，但**每条射线预算仍固定**，空区域照样吃掉大量 MLP 前向（$800\times800$ 约数十秒级）。

经典图形学用 BVH / **稀疏体素八叉树** 跳空。NSVF 把同一思想嵌进可微神经渲染：显式稀疏结构决定「哪里值得积」，隐式 MLP 仍负责「积出来什么颜色」。

## 2. 表示：体素限定的局部隐式场

设场景非空部分落在稀疏体素集合 $\mathcal{V}=\{V_1,\ldots,V_K\}$ 内。NSVF 不是一个全局 $F_\theta$，而是**一簇体素限定场**（参数 $\theta$ 在体素间共享）：

$$
F_\theta^i:\;
\mathbf{p}\mapsto\bigl(c(\mathbf{p},\mathbf{d}),\,\sigma(\mathbf{p})\bigr),
\qquad \mathbf{p}\in V_i.
$$

### 2.1 体素顶点特征 + 三线性插值

相对「直接喂坐标 $\mathbf{p}$」，NSVF 在每个体素的 **8 个顶点**存放可学习 embedding（实验中常用 **32 维**）。查询点 $\mathbf{p}\in V_i$ 时，先对八顶点特征做**三线性插值**得到局部特征 $g_i(\mathbf{p})$，再（常配合位置编码）送入共享 MLP 得到 $(c,\sigma)$。

直观效果：

- 区域相关的几何 / 材质信息写进显式特征，减轻 MLP 负担；  
- 高频细节比纯 PE + 大网更容易「落在格子上」；  
- 消融显示：**仅体素 embedding** 往往就比仅 PE 提升大，二者并用最好。

两个极端特例有助于定位 NSVF：

| 设定 | 退化为 |
|:---|:---|
| 整场景一个「无穷大体素」、$g$ 退化为坐标 | 接近 **NeRF** |
| $g$ 直接存 $(c,\sigma)$、无 MLP | 接近 **显式体素**（如 Neural Volumes） |

NSVF 夹在中间：**显式稀疏结构 + 隐式局部解码**。

## 3. 渲染：先求交，再只在体素内行进

1. **Ray–voxel 求交**：对稀疏八叉树做 AABB 测试（层次结构下很快；$10^4$–$10^5$ 个体素量级即可支撑复杂场景）。得到射线穿过的体素序列。  
2. **体素内 ray marching**：只在相交体素内按步长 $\tau$ 采样；可把体素边界交点也纳入采样点。空空间**根本不进入** MLP。  
3. **体渲染复合**：与 NeRF 相同的 $\alpha$-compositing；透射率接近 1 时可**提前终止**（实体后方不再积）。背景可用可学习 $c_{\mathrm{bg}}$。

与 NeRF 粗细双网相比：NSVF **通常不需要第二套 coarse 网络**，同预算下可在非空区域采得更密，质量与速度双赢。

训练时还可偏置采样：优先抽「至少打中一个体素」的射线，减少无效监督。

## 4. 渐进学习：自剪枝 + 八叉树细分

仅靠固定粗网格不够。NSVF 用两步把八叉树「长」到场景形状上。

### 4.1 初始化

从一个大致包住场景的包围盒出发，按体素数约千量级切分初始体素（边长 $l\sim\sqrt[3]{V/1000}$）。若有粗几何（点云、视觉外壳），也可直接体素化初始化（ScanNet 等室内场景常用深度点云）。

### 4.2 Self-pruning（自剪枝）

几何成形后，周期性删掉「几乎全透明」的体素。对体素 $V_i$ 内均匀采 $G$ 点（文中 $G=16^3$），若

$$
\min_{j}\,\exp\bigl(-\sigma(g_i(p_j))\bigr)\;>\;\gamma
\qquad(\gamma\approx 0.5),
$$

则认为该体素可剪掉。不依赖外部分割模块，故称 **self-pruning**（例如每 2500 step 一次）。

### 4.3 Progressive refinement（渐进加细）

训练若干阶段后，将步长 $\tau$ 与体素边长 $l$ **同时减半**：每个体素细分为 $2^3$ 子体素，新顶点特征由原八顶点**三线性插值**初始化。合成场景约 4 阶段、真实场景约 3 阶段（如在 5k / 25k / 75k step 细分）。模型容量随细分逐步增大，细节跟着上来。

```text
粗包围盒体素
  → 联合训练 embedding + MLP
  → self-pruning 去空壳
  → 八叉树细分（特征插值初始化）
  → 重复剪枝 / 细分
  → 稀疏占用贴合场景
```

## 5. 损失与实现量级

渲染损失仍是像素 $L_2$，并加 Lombardi et al. 的 beta 分布正则 $\Omega(\cdot)$ 鼓励透明度更「干净」：

$$
\mathcal{L}
=\sum_{\mathbf{r}\in\mathcal{R}}
\bigl\|\hat C(\mathbf{r})-C^*(\mathbf{r})\bigr\|_2^2
+\lambda\,\Omega(\cdot).
$$

量级印象（论文设定）：batch 约 4 张图、每图 2048 射线；网络权重约 **3–16 MB**（随体素数 $10$k–$100$k 变，MLP 约 2 MB）；相对 NeRF 双 MLP ~5 MB 同量级，但**查询次数**因跳空大幅下降。

## 6. 能力扩展（显式结构换来的红利）

| 任务 | 做法 |
|:---|:---|
| **多场景学习** | 各场景自有体素 embedding，**共享**密度/颜色 MLP；比纯超网络 NeRF 稳得多 |
| **场景编辑 / 合成** | 移动、复制、删除稀疏体素即可重组物体，无需重训解码器 |
| **动态人** | 在规范空间或分时结构上挂稀疏体素（论文演示） |
| **大尺度室内** | 用粗几何初始化体素，inside-out 漫游更可行 |

这些是「纯一个黑盒 MLP」很难直接做的操作。

## 7. 与后续加速路线的关系

| | NSVF (2020) | Instant-NGP | Plenoxels |
|:---|:---|:---|:---|
| 空间结构 | 稀疏八叉树 + 顶点 embedding | 多分辨率哈希网格 | 稀疏体素 + SH |
| 解码 | 共享 MLP | 极小 MLP | 几乎无 MLP |
| 跳空 | 八叉树 AABB + 剪枝 | 占用网格 | 稀疏体素 |
| 编辑性 | 强（显式体素） | 弱一些 | 中等 |

NSVF 是较早把 **「稀疏体素加速 NeRF」** 讲清楚并开源的工作之一；后续 Instant-NGP / Plenoxels 等在工程与编码上走得更远，但「显式占用 + 局部特征」的主线一脉相承。详见 [Nerf_InstantNGP.md](Nerf_InstantNGP.md)、[Nerf_Plenoxels.md](Nerf_Plenoxels.md)。

## 8. 一句话

**NSVF = 稀疏体素八叉树决定「在哪积分」+ 顶点特征三线性插值 + 共享 MLP 解码 $(c,\sigma)$；用 self-pruning 与渐进细分从照片里长出占用结构，从而跳过空空间、加速并便于编辑。**
