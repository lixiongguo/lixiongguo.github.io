# Multi-View Stereo: A Tutorial（读书笔记）

> Yasutaka Furukawa, Carlos Hernández.  
> *Multi-View Stereo: A Tutorial*, Foundations and Trends in Computer Graphics and Vision, 9(1–2):1–148, 2013/2015.  
> DOI: [10.1561/0600000052](https://doi.org/10.1561/0600000052) · PDF: [carlos-hernandez.org](https://carlos-hernandez.org/papers/fnt_mvs_2015.pdf)

经典 **MVS 总览教程**：把多视图立体框成「在已知相机下，找最能解释图像的几何」——核心是 **光度一致性（photo-consistency）** + **高效优化 / 表示**。偏实践算法与工业可用管线，是读 COLMAP / PMVS / 深度图 MVS / 学习 MVS 前很好的地图。

## 1. 问题与总管线

**目标**：给定一组照片，估计最可能解释这些照片的 3D 形状。若材质、视角、光照全未知，问题严重不适定；在常见假设（刚体、近似朗伯、有纹理）下，立体对应是最稳健、应用最广的线索之一。

**输入约定**：图像 + **相机参数**（位姿与内参）。教程反复强调：

> **MVS 的上限 ≈ 输入图像质量 × 相机参数精度。**  
> 近年 MVS 能「出实验室」，很大程度上靠 SfM 把位姿做准。

通用流水线（Fig. 1.2）：

```text
采集图像
  → SfM / BA 求相机 + 稀疏点
  → MVS 求稠密几何
  →（可选）材质 / 纹理
```

采集场景三分法：实验室可控 → 户外小场景 → 车载 / 航拍 / 互联网众包超大规模。

## 2. 相机、SfM 与 BA（为 MVS 铺路）

- **针孔模型** $P=K[R|t]$；实践常简化为焦距 + 位姿；广角需径向畸变，可先去畸变再进 MVS，或在管线内支持畸变。  
- **Rolling shutter** 对视频 MVS 是额外复杂度。  
- **SfM**：特征 → 匹配 → 轨迹 → 增量/全局运动结构；无序集依赖好描述子与可扩展匹配。  
- **BA**：最小化重投影误差；MVS 对重投影误差极敏感——因为常用对极几何把匹配收成 **1D 搜索**，误差大时正确对应根本对不上。目标常是 **亚像素** RMSE；误差大时可适当降采样图像（只要纹理仍够）。

同目录：[ColMap.md](ColMap.md)。

## 3. 光度一致性（Chapter 2 核心）

把几何假设 $X$ 与图像联系起来：在支撑域 $\Omega$ 上比较外观。通用形式是「在可见视图上聚合相似度」。

| 度量 | 不变性 | 特点 |
|:---|:---|:---|
| **SSD / SAD** | 弱 | 快；光照一致时好用；SAD 对离群更稳 |
| **NCC / ZNCC** | 增益/偏置 | 互联网/光照变化首选；弱纹理、重复纹理易挂 |
| **Census / Rank** | 增益/偏置（序关系） | 深度边界常比 NCC 稳；无纹理区差 |
| **Mutual Information** | 更强（近似双射） | 模态差大时有用；立体里精度往往不如 NCC/Census |

**彩色处理**：勿简单拼通道再 NCC（会被跨通道强度差主导）；宜分通道 NCC 再平均，或分通道去均值后统一算方差。

**归一化 / 聚合**：把原始代价映到 $[0,1]$ 或似然；可再沿邻域滤波。表示可以是体素场、当前曲面上的值、或稀疏 $(p,C(p))$ 列表。

**可见性死结**：算一致性要知道谁看见谁，而可见性又依赖几何。破局手段包括：

1. **Space carving** 类有序可见性（相机凸包等约束）；  
2. **粗可见性**：位姿聚类 / 视簇，把百万图拆成每参考图附近几十张窄基线问题（大规模关键）；  
3. **迭代**：用当前几何做遮挡（z-buffer），再重建；依赖好初值，常作 refine；  
4. **统计鲁棒**：不显式遮挡，靠一致性统计压掉坏图。

## 4. 算法谱系：按输出表示分类（Chapter 3）

教程用 **场景表示** 作主轴分类（另可参考 Seitz et al. Middlebury MVS  taxonomy）：

| 表示 | 在做什么 | 代表脉络 |
|:---|:---|:---|
| **Depth map(s)** | 每参考视图一张深度（+ 可选法向），再融合 | 平面扫描、SGM 聚合、PatchMatch Stereo、COLMAP dense |
| **Point cloud** | 直接长稠密点 / 面片 | **PMVS/CMVS**（Furukawa–Ponce） |
| **Volumetric** | 体素占用 / TSDF 等，再抽等值面 | Space carving、体素 graph-cut、深度融合进体积 |
| **Mesh** | 直接或 refine 三角网格 | 变分光一致性网格 refine |

### 4.1 深度图路线（工业最常见）

1. 对参考图建深度假设（fronto-parallel 或倾斜平面）；  
2. 单应 / 投影 warp 源图，算 photo-consistency；  
3. 正则（局部窗、SGM、MRF、PatchMatch 传播……）；  
4. 多视图滤波 + 融合 → 点云 / 体积 / 网格。

同目录：[SGM.md](SGM.md)、[PatchMatch.md](PatchMatch.md)、[ColMap.md](ColMap.md) 稠密段。

### 4.2 点云 / 面片路线（PMVS）

从特征种子扩散：匹配 → 扩张 → 滤波，得到面向相机的小面片点云；CMVS 做图像聚类以扩规模。完整度与细节在经典时代极强，仍是教程重点案例之一。

### 4.3 体积融合与网格 refine

多深度图融进 TSDF / 占有场再抽面；或在网格上直接优化 photo-consistency + 平滑能量，适合已有粗几何后的细节雕刻。

## 5. 结构先验（Chapter 4）

纯光度在弱纹理、镜面、重复结构上不够。教程讨论引入场景结构：

- **Depth → Plane map**：每像素平面（PatchMatch Stereo 倾斜窗）；  
- **几何基元**：曼哈顿、平面块、建筑语法等；  
- **图像分类 / 语义**：天空、地面、立面先验引导匹配与融合。

今天的学习 MVS、语义 MVS 可看作这条线的数据驱动版。

## 6. 软件、采集与应用（Chapter 5）

- **软件生态**（教程年代）：PMVS/CMVS、各种学术代码；今日对照 **COLMAP、OpenMVS、商用 RealityCapture / Metashape** 等。  
- **采集建议**：足够重叠与基线、避免运动模糊与过曝、尽量刚性场景、纹理不足处补纹理或换算法/先验。  
- **应用**：文物、地图、影视、电商物体、街景等。

## 7. 局限与开放问题（Chapter 6，当时视角）

- 非朗伯、透明、无纹理、细结构、动态场景；  
- 超大规模与在线 / 实时；  
- 外观与几何联合（不仅几何）；  
- 与主动深度、语义、学习方法的结合。

**2015 年后的补丁（读教程时对照）**：深度学习 MVS（[MVSNet.md](MVSNet.md)、[CASMVSNet.md](CASMVSNet.md)、[PatchMatchNet.md](PatchMatchNet.md)）用 CNN 特征与代价体 / 学习 PatchMatch 补弱纹理；神经辐射场 / 3DGS 换表示，但「位姿 + 多视图一致性」骨架仍通。

## 8. 章节地图（对照原文）

| Ch | 内容 |
|:---:|:---|
| 1 | 采集、相机、SfM、BA、MVS 定位 |
| 2 | Photo-consistency 度量与可见性 |
| 3 | 深度图 / 点云 / 体积 / 网格算法 |
| 4 | 结构先验 |
| 5 | 软件、采集实践、应用 |
| 6 | 局限与未来 |

## 9. 与本目录其它笔记的关系

```text
本教程（问题定义 + 光度 + 表示分类）
    │
    ├─ SfM 骨架     → ColMap
    ├─ 深度正则     → SGM / PatchMatch
    ├─ 工业稠密     → ColMap MVS
    ├─ 学习深度图   → MVSNet / CasMVSNet / PatchmatchNet
    └─ 纹理（几何后）→ MRF_Texture（Let There Be Color）
```

## 10. 一句话

**MVS = 在可靠相机下，用可鲁棒的光度一致性，在深度图 / 点云 / 体积 / 网格等表示上做大规模优化；教程把度量、可见性与算法谱系摊开——后续 COLMAP 与学习 MVS 都站在这张地图上。**
