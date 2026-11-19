# NeRF：NeuS（SDF + 体渲染抽网格）

> Peng Wang et al., *NeuS: Learning Neural Implicit Surfaces by Volume Rendering for Multi-view Reconstruction*, NeurIPS 2021.  
> 索引：[Nerf.md](Nerf.md) · 前置：[Nerf_三大组成部分.md](Nerf_三大组成部分.md)

## 1. 密度场抽网格为什么难受

原 NeRF 的 $\sigma(\mathbf{x})$：

- 表面是「密度变高的一层雾」，没有清晰零水平集；  
- 阈值随意 → Marching Cubes 出洞、厚壁、噪点；  
- 多视角光度只约束「积分颜色对」，不直接约束「是一张薄曲面」。

做新视角可以，做 **CAD / 测量 / 传统渲染资产** 往往不够。

## 2. NeuS 的表示

改学 **有符号距离函数（SDF）**

$$
f_\theta(\mathbf{x})\approx \mathrm{dist}(\mathbf{x},\mathcal{S}),
$$

零水平集 $\{f=0\}$ 即表面；符号区分内外。颜色仍可用 MLP：$c(\mathbf{x},\mathbf{d})$（或只依赖 $\mathbf{x}$）。

关键：训练监督主要是图像，不是 GT 网格 —— 必须把 SDF **接到体积渲染**上，才能用 $\hat C$ 与照片对齐。

## 3. 从 SDF 到渲染权重

不能直接把 $f$ 当 $\sigma$。NeuS 用 logistic / sigmoid 密度思想，构造沿射线的不透明度权重，使得：

- 权重峰值落在射线与表面交点附近；  
- 一阶近似下与无遮挡的表面渲染一致；  
- 对 SDF 尺度等做了仔细归一，避免「胖表面」「瘦没了」。

（公式细节见原文；实现上即「SDF → α → 与 NeRF 相同的 compositing」。）

于是损失仍可以是

$$
\mathcal{L}_{\mathrm{rgb}}=\sum\|\hat C-C_{\mathrm{gt}}\|^2,
$$

外加 Eikonal 等约束 $\|\nabla f\|\approx 1$，让 $f$ 更像真距离场，表面更干净。

## 4. 训练与输出

- 输入：多视角图 + 位姿（可选 mask）；  
- 优化：SDF 网络 + 颜色网络（可加特征网格加速）；  
- 导出：对 $f=0$ 做 MC / 变分表面抽取 → **三角网格**；颜色可烘焙成顶点色或纹理。

质量上，物体级重建的表面完整度、光滑度常明显好于对 NeRF 密度硬阈值。

## 5. 同族工作（地图）

| 方法 | 要点 |
|:---|:---|
| **VolSDF** | 也把 SDF 接到体渲染，密度变换形式不同 |
| **HF-NeuS** 等 | 高频细节、大场景改进 |
| **Neuralangelo** 等 | 哈希编码 + SDF，细节更强 |
| 传统 MVS mesh | 显式匹配 + 融合；弱纹理弱，但管线成熟 |

选型：要 **可编辑封闭表面** 优先 SDF 族；只要新视角、可上 3DGS / NGP。

## 6. 和 nvdiffrec 的分工

- NeuS：隐式表面 + 渲染，几何质量好，材质通常仍是「神经颜色」。  
- [Nerf_nvdiffrec.md](Nerf_nvdiffrec.md)：直接优化三角网格 + **PBR 材质 + 光照**，进引擎更直接。  

可先 NeuS 出 mesh，再烘焙 / 可微细化材质。

## 7. 一句话

**NeuS 用 SDF 换密度，并把 SDF 接到体渲染上——多视角照片既能出新视角，也能抽出干净三角网格。**
