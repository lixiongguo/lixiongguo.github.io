# NeRF：从图像提取网格、材质与光照（nvdiffrec）

> Jacob Munkberg et al., *Extracting Triangular 3D Models, Materials, and Lighting From Images*, CVPR 2022（NVIDIA，常称 **nvdiffrec**）。  
> 索引：[Nerf.md](Nerf.md) · 相关：[Nerf_NeuS.md](Nerf_NeuS.md)、[MRF_Texture.md](../2.MVS/MRF_Texture.md)

## 1. 动机

纯 NeRF / 即时 NGP：新视角漂亮，但

- 几何不是三角网格；  
- 外观不是 albedo / roughness / metalness；  
- 光照烘焙在场里，难换环境光、难进游戏引擎。

工业与内容管线要的是：**mesh + UV/PBR + lights**。该文目标是从多视角图像**直接优化**这类资产。

## 2. 优化什么

典型变量包括：

1. **形状**：可微的三角网格（或 DMTet 等可学习四面体 / 符号场再抽三角）；  
2. **材质**：PBR 参数纹理（扩散色、金属度、粗糙度、法线等）；  
3. **光照**：环境贴图 / 球谐 / 可学习探针。

用 **可微渲染器**（可微光栅 + 着色）把当前资产渲成图像，与训练视角比损失，反传更新上述参数。

## 3. 和体积 NeRF 的差别

| | NeRF 族 | nvdiffrec |
|:---|:---|:---|
| 主表示 | 辐射场 / SDF | 三角网格 + 纹理 |
| 渲染 | 体积分 | 光栅化 + PBR |
| 输出 | 像素 / 隐式场 | DCC / 引擎友好资产 |
| 编辑 | 难（换光、换材质） | 相对容易 |

体积方法可当**初始化或几何代理**；最终交付仍常落到这类可微网格优化，或传统 MVS mesh + [MRF 贴图](../2.MVS/MRF_Texture.md)。

## 4. 管线直觉

```text
多视角 RGB + 位姿
    → 初始化形状（视觉壳 / 粗 mesh / 神经场）
    → 可微渲染 ↔ 图像损失（+ 正则）
    → 联合更新 几何 / 材质 / 光照
    → 导出 .obj/.glb + 纹理 + HDRI
```

挑战：几何与材质–光照歧义（暗处是黑漆还是没光）；常用正则、延迟拆分（先形后材）、多光照假设缓解。

## 5. 后续生态（一笔）

同方向还有提取 mesh 的可微表面、神经纹理烘焙、以及「NeRF/3DGS → 网格」后处理工具链。选型口诀：

- 只要逛一逛新视角 → NeRF / 3DGS；  
- 要进 Unity / Unreal / 电商 3D → **mesh + PBR**（本文或 NeuS→烘焙）。

## 6. 一句话

**nvdiffrec 把多视角重建目标从「神经辐射场」扳回「可微三角网格 + 材质 + 光照」——服务的是图形资产生产，而不只是新视角视频。**
