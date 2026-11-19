# 动态人体自由视角渲染：NHR 与 HumanNeRF

> 前置：[Nerf_三大组成部分.md](Nerf_三大组成部分.md)  
> 索引：[Nerf.md](Nerf.md)

本文对照两篇人体自由视角工作：

| | **NHR** | **HumanNeRF**（Weng et al.） |
|:---|:---|:---|
| 论文 | Wu, Wang, Hu, Yu. *Multi-View Neural Human Rendering*, CVPR 2020 | Weng, Curless, Srinivasan, Barron, Kemelmacher-Shlizerman. *HumanNeRF: Free-Viewpoint Rendering of Moving People from Monocular Video*, CVPR 2022 |
| 输入 | **多目**同步视频 + 每帧粗糙点云（MVS/SfM） | **单目**视频 + 分割 + 离架姿态估计 |
| 表示 | 点云特征 → 投影特征图 → CNN 解码（非体渲染 NeRF） | 规范 T-pose **体密度场** + 骨骼/非刚体运动场（NeRF 式体渲染） |
| 典型场景 | 摄影棚穹顶（数十相机） | YouTube 级非受控单目舞蹈等 |

二者都在做「动态人 + 新视角」，但一条走 **显式几何代理 + 神经纹理/补洞**，一条走 **规范空间体积场 + 可微变形**。另有同名的 Zhao et al. *HumanNeRF*（CVPR 2022，稀疏多目可泛化）见文末备注。

---

## 1. Multi-View Neural Human Rendering（NHR）

> 项目页：[wuminye.github.io/NHR](https://wuminye.github.io/NHR/) · 代码：[wuminye/NHR](https://github.com/wuminye/NHR)

### 1.1 问题设定

多相机穹顶同步拍摄动态表演者（论文系统可达约 80 相机、25 fps）。每帧用商业 SfM/MVS（如 Metashape）得到**带颜色的点云** $P_t$，但存在：

- 拓扑 / 点数随时间剧烈变化；  
- 遮挡造成**大洞**；  
- 手、发、鼻、脚、黑衣等纹理弱区域几何极差。

目标：在低保真动态点云引导下，端到端合成任意新视角的照片级 Free-Viewpoint Video（FVV），并尽量利用**时间一致性**弥补视角稀疏。

### 1.2 三模块管线

```text
每帧点云 P_t (+ 颜色)
    → FE: PointNet++ 提 3D 特征 D_t
    → PR: 投到目标相机 + Z-buffer 光栅化 → 2D 特征图 S
    → RE: 抗锯齿 U-Net（gated conv）→ RGB + 前景 mask
```

**FE（Feature Extraction）**  
用 **PointNet++** 在点云上提结构/语义特征。相对「每点每帧各学一套 descriptor」：共享网络吃**全时段、全视角**数据，利用人体形状在时间上的连贯性，减轻「每帧拓扑不一致」与「相机数少」带来的欠采样。输入常拼上点颜色与指向目标相机的归一化视线方向。

**PR（Projection & Rasterization）**  
给定目标内外参，把带特征的 3D 点投影到像平面，Z-buffer 处理遮挡，得到稀疏 2D 特征图 $S$；背景像素用可学习默认特征填充。梯度可经投影回传到 3D 点特征，端到端可训。

**RE（Rendering）**  
投影图有洞、穿透噪声。用带 **gated convolution** 的 U-Net 把 $S$ 解码为 RGB，并输出前景 mask。门控卷积把「洞 / 错点」当语义噪声，用注意力式掩码修复——比直接把 RGB 点云塞进 U-Net（PCR-U 基线）稳得多。

损失：像素 $L_1/L_2$ + VGG 感知损失 + mask 监督；训练时对相机做随机平移/缩放/旋转增广，提高任意视角泛化。

### 1.3 几何回环：Visual Hull 补洞

NHR 还能渲密集新视角的 **mask** → Shape-from-Silhouette 得到 visual hull，用来**补全**原始 MVS 点云（尤其黑衣、无纹理区）。补完几何后再微调渲染网络若干 epoch，可减轻视频闪烁。这是「渲染 ↔ 重建」的小闭环，而非纯前馈。

### 1.4 要点与局限

- **优点**：不依赖 SMPL 裸模；对脏点云鲁棒；手发等细节常优于纯纹理网格 / 点云直渲；可做 bullet-time。  
- **局限**：仍需多目穹顶与每帧点云；近距离拍摄时投影点过稀会失效；本质是 **2.5D 神经 IBR**，不是连续体积场。  
- **与 NeRF 关系**：时间线在 NeRF 爆发前（CVPR 2020）；后续人体 NeRF（Neural Body、HumanNeRF 等）常引用 NHR 作为多目神经人体渲染基线之一。

---

## 2. HumanNeRF（Weng et al., 2022）

> [arXiv:2201.04127](https://arxiv.org/abs/2201.04127) · 典型实现：[chungyiweng/humannerf](https://github.com/chungyiweng/humannerf)

### 2.1 问题设定

**单目**视频（可含复杂舞蹈、YouTube 素材）。预处理：每帧人像分割（可手工清一下）+ 离架 3D 姿态。目标：对任意一帧的姿态，合成**该时刻**人体的任意新视角（甚至 360° 环绕），含衣褶、脸部等高频细节。

难点：训练视角极窄，却要外推未见相机角；人体大形变超出一般 deformable NeRF 的「小变形」假设；SMPL 模板又容易在衣服上露馅。

### 2.2 核心：规范体积 + 观测←规范 的反向变形

把动态人写成

$$
F_o(\mathbf{x}_o)
=F_c\bigl(T(\mathbf{x}_o,\mathbf{p})\bigr),
$$

- $F_c:\mathbf{x}\mapsto(c,\sigma)$：**规范 T-pose** 下的连续辐射场（MLP）；  
- $T(\mathbf{x}_o,\mathbf{p})\mapsto\mathbf{x}_c$：由观测姿态 $\mathbf{p}=(J,\Omega)$（关节位置 + 局部旋转）引导的**运动场**，把观测空间点**映回**规范空间（backward warp）；  
- 在观测空间做标准 **NeRF 体渲染**，与输入帧比损失。

### 2.3 运动场分解：骨骼刚体 + 非刚性

$$
T = T_{\mathrm{NR}}\circ T_{\mathrm{skel}}.
$$

**骨骼部分 $T_{\mathrm{skel}}$**（逆 LBS 思想）  
在规范空间存骨骼 blend weight 体积 $W_c$（$K{+}1$ 通道，$K$ 根骨 + 背景），由 **CNN 从潜码生成显式体素网格**（避免对每根骨各跑一次 MLP；三线性插值自带平滑正则）。观测空间权重由规范权重经骨骼刚体变换拉回，再做加权混合，实现「粗骨架驱动的大运动」。

**非刚性部分 $T_{\mathrm{NR}}$**  
在骨骼变形之后加 MLP 预测的偏移 $\Delta\mathbf{x}$，刻画衣服飘动等骨架解释不了的细节。

**姿态精化**  
离架姿态有误差；网络再学一个小的姿态修正，与场联合优化，改善对齐。

### 2.4 优化技巧：延迟打开非刚性

若一开始就训 $T_{\mathrm{NR}}$，非刚性容易**吞掉本该由骨骼解释的运动**，新视角一差。做法：

1. 前期只开骨骼变形；  
2. 对非刚性 MLP 的位置编码频率加 **截断 Hann 窗**，随迭代逐渐放宽（coarse-to-fine）；  
3. 野生视频可推迟姿态精化启动。

损失：观测空间体渲染颜色（及必要正则）对 $\Theta=\{\theta_c,\theta_{\mathrm{skel}},\theta_{\mathrm{NR}},\theta_{\mathrm{pose}}\}$ 反传。量级印象：约 $400$k iter、数日量级 GPU（论文设定）。

### 2.5 要点与局限

- **优点**：真正单目复杂运动上的自由视角；显式拆开骨架 / 衣服运动，优于「一个变形场包打天下」；无需 SMPL 网格贴图。  
- **局限**：每人每段视频**单独优化**，贵；依赖分割与姿态质量；背景需抠掉；外推到训练未见的剧烈姿态仍会糊 / 穿帮。  
- **与 NHR**：NHR 用多目点云 + 图像空间 CNN；HumanNeRF 用单目 + 规范 NeRF。前者强在采集完备时的细节与工程闭环，后者强在「只有一条视频」时的可玩性。

---

## 3. 对照一览

```text
NHR (2020)                          HumanNeRF-Weng (2022)
多目穹顶 + 每帧 MVS 点云              单目视频 + 姿态
PointNet++ 特征                      规范空间 MLP (c,σ)
投影光栅化 → U-Net                   观测空间体渲染
补洞靠 visual hull 回环              变形靠骨骼体积 + 非刚性 MLP
显式几何代理主导                      隐式体积 + 显式骨架权重网格
```

| 维度 | NHR | HumanNeRF (Weng) |
|:---|:---|:---|
| 相机数 | 多 | 1 |
| 是否体渲染 | 否（特征图 CNN） | 是 |
| 人体先验 | 弱（点云语义） | 强（骨骼 LBS 结构） |
| 训练单位 | 可共享 / 分人 | 通常 per-video |
| 编辑 / 驱动 | 偏新视角合成 | 可换视角；姿态条件化 |

---

## 4. 备注：另一篇同名 HumanNeRF（Zhao et al., CVPR 2022）

Fuqiang Zhao 等 *HumanNeRF: Efficiently Generated Human Radiance Field from Sparse Inputs*（[项目页](https://zhaofuq.github.io/humannerf/)）也叫 HumanNeRF，但设定更接近「**稀疏多目 + 可泛化**」：跨视角聚合 pixel-aligned 特征、姿态嵌入的非刚性场，可对未见演员快速出图，并可小时级 per-scene fine-tune + 外观 blending。与 Weng 版「单目 per-video 优化规范场」不要混淆；和 NHR 同属多目人体线，但已换成 NeRF/IBR 混合范式。

---

## 5. 一句话

- **NHR**：多目动态点云上，用 PointNet++ 特征 + 可微投影 + 门控 U-Net 做神经人体渲染，并用新视角 mask 做 visual hull 补几何。  
- **HumanNeRF（Weng）**：单目视频上，优化 T-pose 体积外观，经**骨骼逆蒙皮 + 延迟非刚性场**映到每帧，再体渲染出任意新视角。
