# OpenMVS 纹理贴图与 MRF（*Let There Be Color!*）

> **引用结论：没有错。**  
> OpenMVS 的 `TextureMesh` 明确采用  
> Michael Waechter, Nils Moehrle, Michael Goesele,  
> *Let There Be Color! — Large-Scale Texturing of 3D Reconstructions*, **ECCV 2014**.  
> 官方 wiki「Mesh Texturing」即点名该文；同作者开源实现为 [mvs-texturing](https://github.com/nmoehrle/mvs-texturing)。

易混清的文献谱系：

| 文献 | 角色 |
|:---|:---|
| **Lempitsky & Ivanov**（2007 左右） | **MRF 视角标注**的基础框架：每面一片标签 + 数据项 / 接缝平滑项 + graph cut |
| Allène / Gal 等 | 改进数据项（投影面积、梯度幅度等） |
| **Waechter et al. 2014（Let There Be Color!）** | 面向大规模真实 MVS：可见性、光度一致性、Potts 平滑、全局+局部颜色校正；**OpenMVS 所跟的是这篇** |
| OpenMVS `TextureMesh` | 工程实现（细节/参数与原文可能略有出入，算法骨架一致） |

因此：「OpenMVS 用 MRF 贴图，参考 *Let There Be Color!*」——**正确**；若只写 Lempitsky，则说的是更早的数学原型，不是 OpenMVS 文档声明的直接参考。

## 1. 问题设定

输入：三角网格 + 已注册多视角图像（位姿来自 SfM，如 COLMAP）。  
目标：为每个三角面选一张源图采样颜色，打成纹理图集，使

- 细节尽量清晰（近景、合焦、分辨率够）；
- 接缝尽量不明显（曝光差、几何误差、遮挡物）；
- 能扛大规模（成百上千张图、千万级三角面）。

不做「每面多图混合」的主路径：混合在几何/位姿略错时易鬼影，且远近景混叠会糊掉近景细节。**每面恰好一个视角标签**是主流选择。

## 2. MRF 视角选择（核心）

对每个面 $F_i$ 赋标签 $\ell_i$（选用的输入视图编号），最小化成对 MRF 能量：

$$
E(\ell)
= \sum_{F_i} E_{\mathrm{data}}(F_i,\ell_i)
+ \sum_{(F_i,F_j)\in\mathrm{Edges}}
  E_{\mathrm{smooth}}(F_i,F_j,\ell_i,\ell_j).
$$

用 **graph cuts + α-expansion** 求多标签近似最小。

### 2.1 数据项 $E_{\mathrm{data}}$

衡量「这张图适不适合贴这个面」。*Let There Be Color!* 采用 Gal 风格：面投影到视图 $\ell_i$ 后，对投影区域内图像梯度幅度积分（Sobel），再取负作为代价——偏好

- 投影面积大（近、正视、分辨率高）；
- 纹理清晰（合焦、边缘多）。

仅靠梯度会踩坑：未重建的遮挡物（行人、树叶）往往比背景墙更「花」，反而被选中。原文用 **photo-consistency**（对各可见视图的面均值色做类 mean-shift / 高斯内点）惩罚不一致视图。

可见性预处理：背面剔除、视锥剔除、射线–网格求交遮挡检测（比纯 GPU 深度缓冲更准）。

### 2.2 平滑项 $E_{\mathrm{smooth}}$

Lempitsky 原式对接缝两侧纹理差做线积分——准，但组合爆炸、算不动，且模糊远景接缝「误差小」会反向偏好糊图。

*Let There Be Color!* 改为 **Potts**：

$$
E_{\mathrm{smooth}} = [\ell_i \neq \ell_j]
$$

（Iverson 括号：标签不同则付常数代价。）鼓励相邻面同标签 → 纹理块更紧凑，计算极快，且不偏向远景。

OpenMVS / 后续改进有时再加几何/颜色相关的接缝代价；骨架仍是「数据项选好图 + 平滑项少接缝」。

## 3. 颜色校正（接缝 levelling）

标签定好后，相邻 patch 常因曝光、白平衡、光照色温不一致而「色带」。两步：

### 3.1 全局顶点亮度/颜色校正（Lempitsky 型，原文改进采样）

接缝顶点拆成左右副本，求加性校正 $g_v$，使

- 接缝左右校正后颜色接近；
- 同一 patch 内相邻顶点的 $g$ 变化尽量平滑。

原文强调：不能只在顶点投影处采一个像素（位姿误差 + 尺度差会使左右采样对不齐），而要沿接缝边做加权采样再平均。三通道可并行优化（不仅亮度）。

### 3.2 局部 Poisson 编辑

全局后仍可能有细缝 → 只在每个 patch **边界一条窄带**（如 20px）解 Poisson，外边界取两侧均值、内边界固定，比整 patch 做 Poisson 省显存/时间。仍避免两图 Laplacian 混合，减少鬼影。

## 4. 管线串起来（OpenMVS 视角）

```text
Mesh + Images + Cameras
        │
        ▼
  面–视图可见性
        │
        ▼
  预计算 E_data（稀疏 face×view）
        │
        ▼
  MRF / Graph Cut → 每面一个视角标签
        │
        ▼
  同标签连通面聚成 texture patch / chart
        │
        ▼
  全局颜色校正 → 局部 Poisson
        │
        ▼
  Atlas 打包 + UV → 带纹理网格
```

可选后续：遮挡/空洞 **inpainting**、材质编辑等，不属原文核心，但是产品管线常见增强。

## 5. 与「图割贴图」口头说法的对应

分享材料里常说「用图割为每个面片选最优视角」——对应的就是上式 MRF 的 α-expansion；  
「接缝融合 / Poisson」——对应全局 $g_v$ + 局部 Poisson。  
口头上把平滑项说成「颜色差 + 梯度差」更接近 Lempitsky 原平滑项或某些工程变体；*Let There Be Color!* 正文默认平滑是 **Potts**，接缝外观主要靠后面的颜色校正解决。

## 6. 实践注意

- 几何与位姿误差会直接变成接缝；贴图救不了严重错位。  
- 曝光差极大时，全局校正仍可能在大色域跳变处吃力 → 采集侧尽量一致曝光，或分区重贴。  
- 未重建遮挡物依赖 photo-consistency；动态行人多时仍可能局部脏。  
- chart 过碎会影响 atlas 效率与接缝数量；有工作在 OpenMVS 上加平面分割改平滑项，减少 chart 碎片。

## 7. 后续工作（两条线）

*Let There Be Color!* 之后，多视角网格贴图大致分成：**仍用真实照片贴重建网格**，以及 **生成式给网格「画」纹理**（问题设定已不同）。

### 7.1 经典重建贴图线（LTBC 的直接后续）

定型「MRF 选视角 + 接缝颜色校正」后，后续多在**工程改进**，而非整套换范式：

| 方向 | 代表 / 做法 | 在解决什么 |
|:---|:---|:---|
| 开源落地 | **mvs-texturing**、**OpenMVS TextureMesh** | 规模化、可复现 |
| Chart / 碎片 | 平面分割（如 VSA）改平滑项 | chart 过碎、接缝多、色差块 |
| 选视图数据项 | 更细的清晰度、分辨率、遮挡先验 | 糊图、行人脏斑 |
| 对齐与融合 | 接缝处非刚性对齐、再 MRF 缝合；局部 Poisson / 梯度域 | 位姿误差导致的错位接缝 |
| 大场景分块 | 分 tile 贴再拼 | 城市场景内存与接缝 |
| 颜色优化 | **ColorMap** 一类全局颜色优化（Zhou & Koltun 等） | 比单纯 leveling 更系统的曝光/色差修正 |

工业物体级重建（COLMAP → OpenMVS）仍大量停在这一族。

### 7.2 学习方法介入「照片 → 纹理」

目标仍是：已有网格 + 真实照片 → 更干净的 atlas。

- **超分 / 补洞**：多视角融合得到的低清或残缺 atlas，用 CNN / 隐式场补全未见表面、抬高细节。  
- **可微纹理优化**：UV 纹理当地图参数，多视角渲染损失反传，减轻「硬标签 + 后处理」接缝。  
- **神经表示再 bake**：NeRF / 3DGS 先得到外观，再烘到 mesh UV（或引擎侧直接用高斯/辐射场）——常见「神经看效果 → bake 进传统管线」。

### 7.3 生成式贴图（约 2023 起；问题变了）

输入变成 **mesh + 文本 / 参考图**，不再依赖拍摄的多视角照片。产品场景是资产生产、风格化、缺纹理补全；接缝 / 多视角一致问题同构：

| 范式 | 代表 | 要点 |
|:---|:---|:---|
| 逐视角扩散再投影 | **TEXTure**、**Text2Tex** | 一圈视角逐步 paint UV，mask 保护已画好区域 |
| 潜空间 / UV 同步扩散 | **TexFusion**、**SyncMVD** | 多视角 denoising 经共享 latent/UV 对齐，减碎片与接缝 |
| 同步多视角 + 后处理 | **MVPaint**、**TexGen**、**ConTEXTure** | 同时生成一致多视图 → 反投影 / inpaint → seam smoothing |
| 再优化一致性 | ConsistenTex 等 | 过完备视角 → 选一致子集 → 对齐 → **仍可能用 MRF 缝合** |

不少生成式工作最后仍借用 **mvs-texturing / MRF 缝合** 作后处理——LTBC 的「标签 + 接缝」骨架还在用。

### 7.4 怎么记、怎么选型

```text
照片重建贴图（OpenMVS / LTBC）
  └─ 改进：选视图、chart、对齐、Poisson、可微 bake、神经补洞

生成式贴图（TEXTure / TexFusion / MVPaint…）
  └─ 解决「没有好照片 / 要风格化」；一致性靠扩散同步，不是梯度数据项
```

- **产线物体重建**：优先「更稳选视图 + 更少 chart + 更好 leveling / bake」，不必追生成式主线。  
- **缺面、脏遮挡、要电商风格**：生成式 / 交互编辑更相关。  
- **NeRF / 3DGS**：可绕过传统 atlas；进引擎时常仍回到 bake 纹理。

## 8. 一句话

**OpenMVS 纹理 = *Let There Be Color!*：MRF 为每面选一张图（graph cut），再用全局校正 + 边界 Poisson 抹平接缝——引用这篇是对的；更早的 Lempitsky & Ivanov 是其 MRF 骨架来源。后续一边把这套工程做稳，一边用可微 / 生成式扩展「无照片也能贴」的场景。**
