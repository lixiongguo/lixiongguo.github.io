# COLMAP

> Johannes L. Schönberger, Jan-Michael Frahm. *Structure-from-Motion Revisited*, CVPR 2016.  
> Johannes L. Schönberger, Enliang Zheng, Marc Pollefeys, Jan-Michael Frahm. *Pixelwise View Selection for Unstructured Multi-View Stereo*, ECCV 2016.  
> 项目：[colmap.github.io](https://colmap.github.io/) · [GitHub](https://github.com/colmap/colmap)

通用 **SfM + MVS** 开源管线：从无序 / 有序图像得到相机内外参、稀疏点，再到稠密深度 / 点云（可选网格）。增量 SfM 稳健性与完整度是社区事实标准之一；稠密阶段基于 **PatchMatch + 像素级选视图**。深度学习 MVS（MVSNet / CasMVSNet 等）几乎都把 COLMAP 的位姿与深度范围当输入骨架。

## 1. 总览

```text
图像集
  │
  ├─ 特征提取（SIFT / 可换）
  ├─ 匹配 + 几何验证 ──► scene graph
  │
  ├─ 增量 SfM
  │    初始像对 → 注册新图(PnP) → 三角化 → 滤波
  │    → 局部 BA / 周期性全局 BA + 再三角化
  │    ──► cameras + 稀疏点
  │
  └─ 稠密 MVS（可选）
       去畸变 → PatchMatch 深度/法向 → 融合 →（Poisson/Delaunay）网格
```

输出常见目录：`sparse/`（模型）、`dense/`（无畸变图、深度、融合点云）。SQLite `database.db` 存特征与匹配。

## 2. 对应搜索（Correspondence Search）

### 2.1 特征

默认 **SIFT / RootSIFT**（GPU 版常用）；也可用二进制特征换速度。近年来可用学习特征 + SuperGlue 等替换匹配，再写回 COLMAP 数据库。

### 2.2 匹配模式

| 模式 | 适用 |
|:---|:---|
| Exhaustive | 小集合，两两全匹配 |
| Sequential | 视频 / 有序环绕；邻域 + 可选闭环 |
| Vocabulary tree | 大集合（数千+），视觉近邻 + 空间重排 |
| Spatial | 有 GPS / 先验位置时 |

朴素全匹配 $O(N_I^2 N_F^2)$ 不可行；词汇树等近似是大规模前提。

### 2.3 几何验证与 scene graph

仅靠外观匹配含外点 → RANSAC 估计几何模型：

- 单应 $H$：纯旋转或近似平面；
- 基础矩阵 $F$ / 本质矩阵 $E$：一般运动；
- 可再标 panoramic / planar、检测水印时间戳等假连接（WTF）。

通过验证的像对成为 scene graph 的边，边上挂内点与模型类型。**全景对不用于三角化**，避免退化点。初始重建优先选非全景、最好已标定的像对。

## 3. 增量 SfM（核心）

### 3.1 初始化

精心选两视图：基线足够、重叠好、非全景。坏种子会导致整条增量链漂掉或断掉。稠密图区作种子更稳、BA 更冗余；稀疏处作种子往往更快但更脆。

### 3.2 图像注册（Next Best View）

已有 2D–3D 对应 → **PnP**（可含内参）把新相机纳入度量重建。选下一张图很关键：一张错注册可能级联污染。

COLMAP 用多分辨率网格打分：可见三角化点**数量多**且在图像上**分布均匀**者优先（避免点全挤在一角导致切除病态）。候选是「至少看到 $N_t$ 个已重建点」的未注册图。

### 3.3 三角化

新图既约束已有点，也通过多视图三角化扩展点集。特征轨迹常被错误合并 → **外点率可极高**。COLMAP 用 RANSAC 式多视图三角化：

- 采样两视图三角化，检查视差角 $\alpha$ 与 cheirality（正深度）；
- 共识集内重投影误差小于阈值；
- 递归剥离子轨迹，恢复被错误合并的多个三维点。

传递匹配（transitive tracks）对「只匹配外观相近短基线对」的集合尤其重要：能连上更大基线，提高后续注册稳定性。

### 3.4 Bundle Adjustment

重投影误差（示意）：

$$
E = \sum_j \rho_j\bigl\|
\pi(P_c, X_k) - x_j
\bigr\|_2^2.
$$

- **局部 BA**：每注册一张后，优化连通最强的一小撮相机 + 点（Cauchy 等鲁棒核）；
- **全局 BA**：模型规模增长一定比例后再做，摊销接近线性时间；
- 解算：小问题稀疏直接法，大问题 PCG（Ceres）；
- Internet 照片可用简单径向畸变模型；主点常固定图像中心。

**滤波**：大重投影误差、过小三角化角、异常焦距 / 畸变的相机剔除。

**再三角化（RT）**：全局 BA 前 / 后都做——漂移修正后补点、合并轨迹，再迭代「BA → RT → 滤波」直至变化变小。这是完整度相对 Bundler / VisualSFM 提升的重要原因之一。

**冗余视图挖掘**：互联网照片大量近重复视角；把高度重叠的相机合成组、共享相对位姿参数，降低 BA 相机系统规模。

## 4. 稠密 MVS

论文 *Pixelwise View Selection…*：在非结构化集合上做稳健稠密重建。

### 4.1 流程命令（概念）

1. `image_undistorter`：按 SfM 相机去畸变，准备 MVS 工作区；  
2. `patch_match_stereo`：每参考图估计深度 + 法向；  
3. `stereo_fusion`：多视图一致融合为稠密点云；  
4. 可选 `poisson_mesher` / `delaunay_mesher`。

### 4.2 PatchMatch 深度 / 法向

继承 PatchMatch Stereo 思想：每像素维护深度与法向（倾斜支持窗），随机初始化 + 传播 + 扰动 refine。相对「只估深度」的正视平面扫描，斜面更友好。

### 4.3 像素级选视图

不是整图固定 4 个源视图，而是**每个像素**按光度 / 几何先验选可用来源：

| 先验 | 直觉 |
|:---|:---|
| 遮挡 / 光度 | 匹配是否解释得通 |
| 三角化角 | 基线太小不稳定，太大易不重叠 |
| 分辨率 | 源图采样是否够细 |
| 入射角 | 掠射角纹理不可靠 |

用广义 EM：E 步推断可见性，M 步 PatchMatch 采样更新几何。可加**多视图几何一致性**：投到邻域深度再投回，同时 refine 与滤波。

### 4.4 融合

光度一致 + 几何一致的深度 / 法向经图滤波融合；输出带颜色的稠密点云。显存紧时可降 `max_image_size`、减少源视图数。

## 5. 实践要点（工程）

- **先验内参**：手机 EXIF / 标定表作初值，减轻焦距–尺度耦合；固定镜头可 share camera model。  
- **前景 mask**：提点阶段挡背景，稀疏点更贴物体（电商 / 物体级重建常用）。  
- **重叠与闭环**：环绕拍要保证匹配图连通；Sequential + loop detection 或词汇树补远距闭环。  
- **失败诊断**：注册率低 → 匹配不足 / 弱纹理 / 运动模糊；重投影误差大 → 曝光不均、错误匹配、错误种子。  
- **下游**：稀疏模型给 CasMVSNet 等作位姿与深度范围；也可用 COLMAP 自带稠密作基线对照。  
- **增量线上**：边上传边增量注册，先出稀疏预览再引导补拍。

## 6. 与相关方法的关系

| | COLMAP | 学习 MVS | GLOMAP 等 |
|:---|:---|:---|:---|
| 位姿 | 增量 SfM（可全局） | 通常假设已知 | 全局 SfM 另一路线 |
| 稠密 | PatchMatch + 选视图 | 代价体 / 级联 CNN | — |
| 优势 | 开箱稳健、可解释 | 弱纹理完整度 / 速度（GPU） | 大规模全局一致性 |
| 角色 | **几何骨干** | 常替换或增强稠密段 | 可替换增量 SfM |

同目录笔记：[PatchMatch.md](PatchMatch.md)、[PatchMatchNet.md](PatchMatchNet.md)、[MVSNet.md](MVSNet.md)、[CASMVSNet.md](CASMVSNet.md)。

## 7. 最小命令流（示意）

```text
feature_extractor → exhaustive/sequential/vocab_matcher
→ mapper（增量重建）
→ image_undistorter → patch_match_stereo → stereo_fusion
```

GUI 与 CLI 共用同一套模块；大规模优先词汇树匹配 + GPU SIFT + 合理 `max_num_features`。

## 8. 一句话

**稳健增量 SfM（选视图 + 鲁棒三角化 + 迭代 BA/再三角化）提供度量骨架，再以像素级选视图的 PatchMatch 做稠密——从无序照片到可度量三维的默认开源全栈。**
