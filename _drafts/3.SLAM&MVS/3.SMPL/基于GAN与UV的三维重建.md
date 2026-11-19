---
layout: post
title: "基于GAN与UV的三维重建"
categories: [TechSharing]
mathjax: true
---

> 主线：把 **UV 空间当作 3D 形状 / 纹理的可学习图像表达**，把几何回归、对齐与跨样本纹理生成"摊回 2D 像素域"，从而能复用整套图像域的 encoder-decoder / GAN / Diffusion 工具。三篇代表工作命中三个不同侧面：
> 1. **PRNet**（ECCV 2018）：**UV Position Map**，把 3D 顶点坐标直接编码为 RGB 图，端到端从单张人脸回归 3D 形状 + 稠密对齐；
> 3. **AUV-Net**（CVPR 2022, NVIDIA Toronto）：把 UV **本身**也变可学习，让"相同语义部位在 UV 空间同一位置"，使纹理迁移、跨形状纹理合成成为普通图像编辑。
> 关联：cGAN / Pix2Pix 视角见 [基于GAN的三维重建](基于GAN的三维重建.md)；SMPL / 人体重建见 [Avatar-SMPL人体重建](Avatar-SMPL人体重建.md)；衣物版型 / 缝合建模见 [Avatar-数字衣服参数化建模](Avatar-数字衣服参数化建模.md)；隐式 / NeRF 路线见 [几何深度学习-隐式表达](几何深度学习-隐式表达.md)。
> 

---

## PRNet：Position Map Regression Network（ECCV 2018）

> Yao Feng, Fan Wu, Xiaohu Shao, Yu Wang, Xi Zhou. *Joint 3D Face Reconstruction and Dense Alignment with Position Map Regression Network*. ECCV 2018.  
> arXiv: 1803.07835. 项目页 / 代码: yfeng95/PRNet。

### 1. 问题与动机

3D 人脸重建有两条传统路线：

- **3DMM 拟合**：解 BFM / 3DMM 参数后生成 mesh；可解释、紧凑，缺点是参数线性子空间表达力受限、拟合常丢高频细节；
- **体素 / 点云 / 隐式表达**：直接预测 occupancy / SDF / NeRF；表达力强，但要么计算重、要么依赖多视角，**单图稠密对齐 + 稠密形状**难以同时拿下。

PRNet 想要的：**单张图像 → 完整、稠密、带像素级对应**的 3D 人脸 mesh，并且**端到端**训练。它给出的解药是把 3D 形状"伪装成 2D 图像"，交给一个标准 CNN 来回归。

### 2. 核心表达：UV Position Map

传统 UV map 存的是纹理颜色 \((R, G, B)\)。**PRNet 把 UV 每个位置上的 3D 顶点坐标当作 RGB 存起来**：对 3DMM / GT mesh 上的每个顶点 \(v=(x, y, z)\)，按它的 UV 坐标 \((u, v)\) 写入位置图：

\[
P(u, v) \;=\; (x, y, z) \quad \text{（编码为 R=x, G=y, B=z）}
\]

得到的"位置图"和一张普通彩色图同尺寸（论文用 256×256×3），但每个像素不是颜色，而是**该 UV 块对应的 3D 顶点坐标**。再做一次标准的"重投影"就能从位置图还原完整 mesh。

这种表达带来三大好处：

| 好处 | 原因 |
| :--- | :--- |
| **表达力无上限** | 表达是连续的，可承载任意高频细节；非线性 3DMM 也只是其中一种参数化 |
| **直接当图像任务** | 网络输出 RGB 图，encoder-decoder / GAN 的全部工具可直接复用 |
| **稠密对齐 = 白送** | 像素 ↔ UV ↔ 3D 顶点一一对应；不再需要 landmark 检测器做后处理稠密对齐 |

### 3. 网络结构

PRNet 主体是一个 **encoder-decoder**，结构上接近 U-Net：

```
   I (人脸 RGB)  ──→  Encoder (ResNet-style)
                          ↓
                     Decoder (up-conv + skip)
                          ↓
              UV Position Map Pos(I) ∈ R^{256×256×3}
                          ↓
                   (可选) Render / Texture Map 模块
                          ↓
                   3D Mesh + Dense UV
```

- **Encoder**：论文用类 ResNet-18 的 backbone；decoder 用 up-conv + skip 输出 256×256×3；
- **UV 固定**：位置图所用 UV 是**预先定义**的（基于 BFM 平均脸的固定 unwrap），"3D 顶点 → UV → 像素"映射是固定的，反查只需标准 `texture mapping`；
- **不需要 3DMM 后拟合的 landmark 检测**：稠密对齐由网络隐式学到。

### 4. 损失函数

逐像素监督 + 一致性 / 几何正则：

\[
\mathcal{L} \;=\; \lambda_{\mathrm{pix}} \mathcal{L}_{\mathrm{pixel}} \;+\; \lambda_{\mathrm{w}} \mathcal{L}_{\mathrm{weight}} \;+\; \lambda_{\mathrm{reg}} \mathcal{L}_{\mathrm{reg}}
\]

- \(\mathcal{L}_{\mathrm{pixel}}\)：预测位置图与 GT 位置图之间的 **L2**（注意是坐标差、不是颜色差）；
- \(\mathcal{L}_{\mathrm{weight}}\)：按 **面部区域 mask** 加权（眼睛 / 嘴 / 脸颊这些高频区权重更大），强迫模型先把这些难区做对；
- \(\mathcal{L}_{\mathrm{reg}}\)：对位置图做**对称 / 平滑**正则，使结果的人脸在拓扑上更合理。

训练增广包含随机遮挡、姿态与颜色抖动；推理时一次前向，得到 3D mesh + 像素级 UV 对应，可直接做 3D 编辑 / 表情重定向 / 光照估计。

### 5. 关键洞察与局限

**洞察**：3D 几何重建的关键不在网络结构，而在**表达选择**。把"3D 顶点坐标"按固定 UV 编码成 RGB 图，就把一个不规则几何问题变成了标准图像回归问题，CNN / GAN / Diffusion 全套工具都可以搬过来用。

**局限**：
- UV 是**预先 unwrap** 的，无法处理"拓扑动态变化"（张嘴、闭眼带来的 UV 切块变动）；
- 训练数据有偏（西方人脸为主），跨种族 / 极端表情泛化受限；
- 模型只管几何，**纹理**靠 UV 网格采样，纹理质量继承输入照明的"涂抹感"；
- 没显式解耦身份 / 表情 / 光照，编辑能力弱于 3DMM 路线。

### 6. 影响

后来 "**Position/UV Map as a canonical image**" 的思路被广泛继承：

- 人脸：MGCNet、3DDFA-V2、FaceScape 等沿用并扩展；
- 人体 / 手：DensePose 的 UV 坐标系、SMPL / 手部 mesh 回归都有"把 3D 顶点编成 2D 像素"的变体（详见 [人体视觉重建_DensePose](人体视觉重建_DensePose.md)）；
- 一般物体：**AUV-Net** 把"UV 当图像"思想**学出来**，不再依赖手工 unwrap（见第三节）；
- 纹理生成：**TexGarment**（CVPR 2025）把 UV Position Map 当 **layout control**，复用 PRNet 思路在 UV 上做 diffusion（见下一节）。

---

## AUV-Net：Learning Aligned UV Maps（CVPR 2022）

> Xu Chen, Tianjian Jiang, Thomas Le Wang, Roland V. Lepro, Koki Nagata, 等. *AUV-Net: Learning Aligned UV Maps for Texture Transfer and Synthesis*. CVPR 2022. NVIDIA Toronto AI Lab.  
> arXiv: 2204.03105. 项目页: research.nvidia.com/labs/toronto-ai/AUV-NET/.  
> 注：原笔记写作 "AUVNet"，标准引文是 **AUV-Net**；本文按 CVPR 2022 正式引用。

### 1. 为什么"传统 UV"不够好？

把 3D 网格拍扁到 2D 的"UV unwrap"已经是图形学几十年的老问题。但**传统 UV 几乎都"不对齐"**：

- 同一类物体的两张 mesh，UV 通常因参数化算法 / 接缝位置不同而**布局不同**；
- 同一段 mesh 上"左前轮"在两张 UV 图的位置可能**截然不同**。

后果是：想用 **CycleGAN / Pix2Pix / Diffusion 直接在 UV 图上做纹理迁移或生成**时，必须**逐模型重新训练**，因为"左前轮"在 UV 中不在固定位置。这是"UV 作为图像表达"路线一直没普及的真正瓶颈。

AUV-Net 直接把这个问题打成学习问题：**让网络学一个 aligned UV，使相同语义部位在 UV 空间落在同一位置。**

### 2. 核心思想

目标：学一个嵌入 \(\Phi: \mathcal{S} \rightarrow \mathbb{R}^2\)，把 3D 网格 \(\mathcal{S}\) 上每个点映到 2D UV 平面，使：

- **对齐性**：来自不同实例的同一语义部位（例如"左前轮"）在 UV 空间落在**同一位置**；
- **可微 / 可逆**：UV ↔ 3D 之间通过可微渲染 / 采样算子打通，以便后面用图像级 GAN / Diffusion 直接生成 UV 图；
- **局部等距**：把**局部**几何保留（UV 上距离近似 surface 测地距离），不要为了对齐把网格严重扭曲。

得到这个 UV 之后，**纹理迁移、跨实例纹理合成、单视图纹理重建**都退化为普通图像任务——和上一节 TexGarment 的 pipeline 可以直接拼装。

### 3. 方法概览

AUV-Net 用两个阶段：

```
(a) UV-Generator（学 aligned UV）：
    输入 3D mesh  ──→  Surface Network (PointNet++ / DGCNN)
                              ↓
                        对每个 3D 点预测 2D UV 坐标 U(p)
                              ↓
              对齐 / 等距 / 单射正则 + 对比 / 监督

(b) Texture 用 UV：当 (a) 训好后，纹理图像 I ∈ R^{H×W×3}
   可作为 3D 表面纹理，图像域工具随你用。
```

具体模块：

| 模块 | 作用 |
| :--- | :--- |
| **Surface Network** | PointNet++ / DGCNN 风格，对点云 / mesh 提取 per-point 特征 |
| **UV-Generator head** | 小 MLP per-point 预测 2D UV 坐标 |
| **Differentiable renderer** | 把 UV 图当作"纹理图"在 mesh 上渲染，提供几何-图像一致性的可微反馈 |
| **Texture Generator (CVN)** | 在学出的 UV 域上做 CycleGAN-style 纹理迁移 / 合成；可直接套通用图像模型 |

**Aligned UV 的几个关键正则**（论文给出加权组合）：

- **Chamfer / correspondence 对齐 loss**：利用有相同语义部位标注的 pair 数据，使 \(\Phi(p_s) \approx \Phi(p_{t'})\)；
- **Distortion regularizer**：限制局部 area distortion（Jacobian 范数），让 UV 局部等距；
- **Bijectivity / smoothness 正则**：避免 UV 退化（折叠），鼓励平滑。

训练后用学到的 \(\Phi\) 把每个 mesh 的"UV 网格"提取出来 —— 之后的纹理问题就退化为图像问题。

### 4. 三个亮点应用

1. **纹理迁移**：A 车的纹理可"贴"到 B 车（两者 UV 已对齐）；效果接近 *"texture style transfer on aligned UV space"*；
2. **跨实例纹理合成**：给定未贴图 mesh，用 GAN / Diffusion **在 UV 域**生成新纹理，再用可微渲染直接绘到表面；以前针对每种模型要重训，现在直接搬图像模型；
3. **单视图 3D 纹理重建**：单张 RGB 输入 → 预测 UV 纹理图 → 用 AUV-Net 的 UV 映回 mesh。CVN (Conditional Versatile Network) 在实验里展示了这一点。

### 5. 与 PRNet / TexGarment 的关系与差异

| 维度 | PRNet | TexGarment | AUV-Net |
| :--- | :--- | :--- | :--- |
| **UV 来源** | 手工预先 unwrap（按 BFM / 模板） | 手工 / 模板（衣物 UV） | **学出来的** Aligned UV |
| **表达的是什么** | 3D 顶点坐标 | 布局控制 + 纹理 RGB | 2D UV 坐标（再到纹理） |
| **类别** | 人脸（拓扑固定） | 衣物（用通用 UV 模板） | **通用物体**（车、马、椅子…） |
| **可处理的拓扑变化** | 弱 | 中（依赖模板） | 强（同语义对齐允许小拓扑差异） |
| **下游任务** | 几何回归 | 纹理生成（diffusion） | 纹理迁移 / 合成 / 生成 |

可以这样理解三者的递进：

- **PRNet** 把 "3D 顶点坐标"投影到固定 UV，用图像域解**几何**；
- **TexGarment** 在固定 UV 上用 diffusion 解**纹理**，并把 3D structure 通过 cross-attention 注入；
- **AUV-Net** 把 "UV 本身" 当成可学习量，让"任意 3D 形状 → aligned UV" 变成一个可学习 encoder，再用图像域解**纹理** —— 是一般化的 TexGarment。

### 6. 局限

- 需要**类别级**的对齐先验（同类的不同实例），跨类（车 → 动物）困难；
- 对极薄、自交、不流形的 mesh 处理困难；
- UV 对齐质量受训练数据对（pair / landmark 标注）覆盖度限制；
- 渲染回 mesh 的一致性仍依赖 differentiable renderer 的数值稳定。

---

## 三篇工作的共同主线与对比

```
PRNet (ECCV 2018)         TexGarment (CVPR 2025)              AUV-Net (CVPR 2022)
─────────────             ──────────────                      ──────────────
        ┌──────────「3D ↔ UV ↔ 2D 图像生成器」──────────┐
        │                                                  │
  UV 固定 (predefined)   UV 固定 (衣物模板)              UV 学出来 (aligned)
  存 3D 坐标              存 "layout control"               存 2D UV 坐标
  解 几何 (回归)           解 纹理 (diffusion)                解 纹理 (迁移/生成)
```

**共同点**：

- 都把 3D 形状 / 纹理映射到 **2D 像素域**，从而复用图像模型工具；
- 都有 **端到端学习** 的核心思想；
- 都**不依赖多视角**：PRNet 单图、AUV-Net 单视图纹理生成、TexGarment 仅靠预训练 DiT + 3D structure condition。

**差异**：

| 维度 | PRNet | TexGarment | AUV-Net |
| :--- | :--- | :--- | :--- |
| 任务 | 单图 → 3D 形状 + 稠密对齐 | mesh + text → 3D 纹理化衣物 | 跨实例纹理迁移 / 合成 / 单视图纹理重建 |
| UV 来源 | 手工 (按 BFM 平均脸) | 衣物模板 | **学习** |
| 监督信号 | 像素级 GT 位置图 | text + 3D structure 引导 | 对齐 / 等距 / 渲染一致性 |
| 表达类别 | 仅几何 | 仅纹理 | 仅纹理 |
| 底层生成器 | encoder-decoder (CNN) | **Diffusion Transformer** | CycleGAN / 可微渲染 |
| 输入 | 单张图像 | mesh + 文本 / 衣物图像 | 跨实例 pair / 单图 |

**后续可拼接方向**：

- **TexGarment + AUV-Net**：在 aligned UV 上做 diffusion 纹理生成，等于"会跨实例对齐" + "会画细纹理"两套能力合体；
- **PRNet 的表达被循环引用**：从 UV Position Map 解几何，到用它当 layout control，再到 Aligned UV，三者构成了 "**3D → UV → 2D image**" 这条主线的完整三段。

---

## 参考文献

1. Feng Y, Wu F, Shao X, Wang Y, Zhou X. *Joint 3D Face Reconstruction and Dense Alignment with Position Map Regression Network*. ECCV 2018. arXiv: 1803.07835.
3. Chen X, Jiang T, Le Wang T, Lepro R V, Nagata K, et al. *AUV-Net: Learning Aligned UV Maps for Texture Transfer and Synthesis*. CVPR 2022. arXiv: 2204.03105.
