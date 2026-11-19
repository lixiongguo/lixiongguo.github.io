---
layout: post
title: "数字衣服参数化建模（Sewing Pattern）"
categories: [TechSharing]
mathjax: true
---

> 主线：用 **2D 裁片 + 缝合关系（sewing pattern）** 做衣服的「本征参数」，而不是只在 SMPL 上叠位移。  
> 两支代表路线：  
> 1. **Korosteleva 线**（数据集 → NeuralTailor → GarmentCode / GarmentCodeData）：点云/程序化 ↔ 可缝制版型；  
> 2. **中山大学 Neural Sewing Machine（NSM）**：版型编码 → UV-position map → 可重建 / 可编辑 3D 衣。  
> 人体侧 SMPL / 着装配准见 [SMPL 人体重建](SMPL人体重建.md)；产业流程对照 Marvelous Designer / 制版见文末。

---

## 为何要「版型参数化」

| 表示 | 优点 | 问题 |
| :--- | :--- | :--- |
| SMPL + 位移 / 单层着装 mesh | 易跟人体、易动画 | 拓扑贴身体；裙等宽松衣别扭；设计与褶皱缠在一起 |
| 固定品类模板（袖长、腰围…） | 参数少、可控 | **一品一类模型**，难跨品类泛化 |
| 纯 3D 表面 / 隐式 | 细节多 | 难换尺码、难制造、难保证可展 |
| **Sewing pattern** | 贴近真实制衣；紧凑；可仿真、可改版、可跨品类统一描述 | 结构预测难（片数可变、缝边交叉） |

版型 ≈ 若干 **2D panels**（直线 / Bezier 边围成的闭合裁片）+ **stitch**（边与边如何缝）+（常有）裁片相对人体的摆放。  
它描述的是衣服的 **rest shape / 本征结构**，尽量与布料、重力、人体接触造成的形变解耦——这正是数字试衣、改版、跨体型重定向需要的。

传统工业：Clo3D / Marvelous Designer 里「画版 → 缝 → 物理仿真」。学习路线要回答两件事：

```text
3D 衣（扫描/仿真点云）  ──?──►  2D 版型 + 缝合     （NeuralTailor）
2D 版型 / 图像          ──?──►  结构保持的 3D 衣   （NSM 等）
```

---

## Korosteleva 线：从数据集到可编程版型

作者主页：[korosteleva.com/publication](https://korosteleva.com/publication/)。与「参数化衣服」直接相关的四步：

```text
Estimating Patterns from Scan（CGF 2021）  ← 几何：扫描分割 + 展平「抽版」
        ‖
Generating Datasets…（NeurIPS D&B 2021） ← 合成：带 GT 版型的大规模数据
        ↓
NeuralTailor（SIGGRAPH / TOG 2022）      ← 学习：点云 → 结构化版型
        ↓
GarmentCode（SIGGRAPH Asia / TOG 2023）
        ↓
GarmentCodeData（ECCV 2024）
```

### 0. Estimating Garment Patterns：静态扫描「抽版」（2021）

> Bang, Korosteleva, Lee, *Estimating Garment Patterns from Static Scan Data*, Computer Graphics Forum 2021.  
> 项目页常挂在 [korosteleva.com/publication/pattern_flattening_sb](https://korosteleva.com/publication/pattern_flattening_sb/)（Shape Estimation）。  
> 后文 / 同领域常把它和 **garment extraction from scan** 一类工作对照；另有他人论文题目即 *Garment Model Extraction from Clothed Mannequin Scan*（CGF），引用并改进本路线，不要和本篇作者表混淆。

**任务**：输入着装人**静态扫描**（三角网 + 纹理），自动得到**可仿真的 2D 版型**并摆回身体周围做 draping——经典几何管线，不是深度网络。

**流程概要**

```text
扫描
  → 拟合 SMPL（体型/姿态；可用多视 OpenPose 初始化）
  → 边界优化：上装↔皮肤、下装↔鞋/皮肤、上装↔下装
  → 缝线先验投影到衣面 → 裁成片
  → unpose + 展平 → 2D pattern，对齐身体供仿真
```

**相对 MRF 逐顶点分割的关键**：不按点分类（易孔洞、锯齿边界），而用**隐式边界曲线**在曲面上优化，把「衣服/皮肤」分界找准；缝线来自身体模板先验，**无需用户手动画缝、也不锁死少数参数模板**，裤/裙等可自动对应不同片形。

局限：依赖纹理/颜色分区、假设衣片拓扑不太黏连；展平质量受扫描几何与切缝影响。  
它是 NeuralTailor 之前的 **「扫描 → 版型」几何解**；NeuralTailor 则换成学习、吃点云、吐 Bezier 结构化版型，并追求未见拓扑泛化。

### 1. 带缝纫版型的 3D 衣数据集（2021）

> Korosteleva & Lee, *Generating Datasets of 3D Garments with Sewing Patterns*, NeurIPS Datasets & Benchmarks 2021.  
> 数据：[Zenodo](https://doi.org/10.5281/zenodo.5267549) · 生成器：[Garment-Pattern-Generator](https://github.com/maria-korosteleva/Garment-Pattern-Generator)

在约 **19 类基础模板**上采样参数，得到约 **2.2 万**件样本：每件含

- 披在 SMPL 平均女体 **T-pose** 上的 3D 衣；  
- 对应的**结构化 sewing pattern**；  
- 可选「扫描伪影」损坏几何。

品类覆盖 T 恤、外套、裤、裙、连体、连衣裙等变体。局限：姿态/体型变化少，重心在**设计空间**而非动态。  
这是后续 NeuralTailor / NSM 的公共数据底座之一。

### 2. NeuralTailor：点云 → 版型结构（2022）

> Korosteleva & Lee, *NeuralTailor: Reconstructing Sewing Pattern Structures from 3D Point Clouds of Garments*, TOG / SIGGRAPH 2022.  
> [arXiv:2201.13063](https://arxiv.org/abs/2201.13063) · [代码](https://github.com/maria-korosteleva/Garment-Pattern-Estimation)

**任务**：给定变形后的 3D 衣点云，回归 **panel 集合（基数可变）+ 每片几何 + 缝合关系**，得到可再仿真的本征版型。

**难点（结构化深度学习）**

1. Panel **数量随款式变**（set regression）；  
2. 每片本身是**边序列**（直线 / 二次 Bezier）；  
3. Stitch 是**跨片边对**连接，不是单向量能说清。

**结构概要**

| 模块 | 作用 |
| :--- | :--- |
| EdgeConv 点云编码 | 点级特征（可再做 attention） |
| **Point-level attention** | 按局部上下文为各 panel 聚特征（相对「一个全局码拆 LSTM」更利泛化） |
| Panel RNN / 解码 | 吐边向量序列 + 片的 3D 摆放 |
| Stitch 分类器 | 边对是否缝合 |

相对 baseline（全局 latent → 两层 LSTM）：attention + 独立 stitch 头后，能泛化到**训练未见过的版型拓扑**（数据集里预留的 test garment types）。  
过滤「不同版型却 3D 外形撞车」的样本，降低一对多歧义。

**一句话**：NeuralTailor 把「衣服参数化」落成 **可学习的 sewing pattern 逆问题**——从点云读出版型，而不是每品类一个袖长回归器。

### 3. GarmentCode：可编程参数版型（2023）

> Korosteleva & Sorkine-Hornung, *GarmentCode: Programming Parametric Sewing Patterns*, TOG / SIGGRAPH Asia 2023.  
> [项目 / 代码](https://github.com/maria-korosteleva/GarmentCode)

若 NeuralTailor 是「识别版型」，GarmentCode 是「**用程序写版型**」：

- 领域特定语言（DSL），按**部件 / 面向对象**组合衣片（领、袖、身片可互换）；  
- 参数可以是设计量 + **人体尺寸**，改尺码时由程序重算几何；  
- 自动化常见低层操作（如按位置打褶/省）；  
- 配置器里调语义参数，底层几何由 GarmentCode 程序生成，保证版型合法。

这是「参数化建模」的工程定义：参数不是黑盒 latent，而是**可解释、可组合、能量产**的制版程序。

### 4. GarmentCodeData（2024）

> Korosteleva et al., *GarmentCodeData: A Dataset of 3D Made-to-Measure Garments With Sewing Patterns*, ECCV 2024.

在 GarmentCode 管线上扩展：**量体裁衣**、更复杂款式、多体型、轻量姿态扰动；生成链路更开放（相对早期强依赖商业 CPU 仿真器的设定）。为下一波「版型 ↔ 3D」学习提供更难、更贴近成衣的数据。

---

## Neural Sewing Machine（中山大学，NeurIPS 2022）

> Chen, Wang, Zhu, Liang, Torr, Lin, *Structure-Preserving 3D Garment Modeling with Neural Sewing Machines*, NeurIPS 2022.  
> 单位：中山大学 + Oxford · [arXiv:2211.06701](https://arxiv.org/abs/2211.06701)

### 定位（与 NeuralTailor 反向）

| | NeuralTailor | **NSM** |
| :--- | :--- | :--- |
| 主方向 | 3D 点云 → 2D 版型 | **版型（及图像条件）→ 结构保持的 3D** |
| 核心输出 | panels + stitches | 多 panel 的 **UV-position map + mask** → 读出 mesh |
| 强调 | 拓扑泛化的结构回归 | 片内等距、片间缝合、法向等 **结构保持损失** |

NSM 把「缝纫机」做成网络：用 sewing pattern 作强先验，学**可重建、可操控**的通用衣服表示，而不假设衣与人体同拓扑（反衬 SMPL 位移对裙子的失效）。

### 统一版型编码

统计数据集上的裁片，聚成 **basic panel groups**；对每组边离散点做 **PCA**：

$$
\gamma = \mathrm{concat}_i(\gamma_i),\quad
\gamma_i=\text{第 }i\text{ 组 PCA 系数（该衣无此组则留空）}.
$$

不同品类、片数映射到**同一套系数向量**，得到跨品类共享 embedding。

### 3D 解码：按片的 UV-position map

- CNN \(D(\gamma)\) 预测各片 UV 上的 **3D 坐标图** \(Y^t\in\mathbb{R}^{H\times W\times 3}\)；  
- **Mask** 由 \(\mathrm{PCA}^{-1}(\gamma)\) 得到（避免网络糊掉细小片形）；  
- 每片一张 map，拓扑任意，不靠「投影到人体 UV」。

### 结构保持损失

$$
\mathcal{L}
=
\alpha_{\mathrm{rec}}\mathcal{L}_{\mathrm{rec}}
+\alpha_{\mathrm{inn}}\mathcal{L}_{\mathrm{inn}}
+\alpha_{\mathrm{int}}\mathcal{L}_{\mathrm{int}}
+\alpha_{\mathrm{nor}}\mathcal{L}_{\mathrm{nor}}.
$$

| 损失 | 作用 |
| :--- | :--- |
| \(\mathcal{L}_{\mathrm{rec}}\) | UV 上 3D 坐标对齐 |
| \(\mathcal{L}_{\mathrm{inn}}\) | 片内邻域边长 ≈ 常数（逼近等距，抑低频糊褶皱） |
| \(\mathcal{L}_{\mathrm{int}}\) | 应缝合的两边在 3D 上点对点贴合（消缝隙） |
| \(\mathcal{L}_{\mathrm{nor}}\) | 表面法向一致，保局部褶皱走向 |

### 能做什么

- 多样形状 / 拓扑下的衣服表示；  
- **图像 → 3D** 重建且结构更干净（缝、片边界）；  
- 在 embedding / 版型侧编辑：**换品类、改形状、改拓扑**（像数字缝纫机）。

评测同样建立在「带 sewing pattern 的公开 3D 衣数据」（Korosteleva 2021 系）上。

---

## 和「SMPL 着装线」怎么拼

```text
制衣本征：Sewing Pattern（NeuralTailor / GarmentCode / NSM）
              ↓ 物理仿真或 NSM 解码
         3D 衣 mesh（可穿在 SMPL 上）
              ↓
穿着外观：Octopus / MGN / BCNet / IPNet …（见 SMPL 笔记）
```

- 要 **换装、改款、对接生产**：优先版型参数；  
- 要 **从一张照片快速得到穿着人**：SMPL+衣或隐式人体往往更直接；  
- 高端管线常是：**版型（或扫描反求版型）→ 仿真/NSM → 再挂到人体动画**。

同属「学习衣服形变」但参数不是版型的：**TailorNet**（体型+姿态+款式 → 褶皱，偏动态代理）——与本文「制版参数」互补，不展开。

---

## 小结

| 工作 | 单位 / 作者 | 输入 → 输出 | 关键词 |
| :--- | :--- | :--- | :--- |
| **Estimating Patterns from Scan** | Bang, Korosteleva, Lee | 静态扫描 → 分割+展平版型 | 隐式边界、几何抽版 |
| 3D Garments + Patterns 数据 | Korosteleva & Lee | 模板采样 → 3D+版型 | 学习底座 |
| **NeuralTailor** | KAIST | 点云 → panels+stitches | attention set 回归、拓扑泛化 |
| **GarmentCode** | ETH | 程序参数 → 合法版型 | DSL、量体、部件组合 |
| GarmentCodeData | ETH 等 | 更难的量体 3D+版型 | 数据升级 |
| **Neural Sewing Machine** | **中山大学**等 | 版型 embedding → UV 衣；可图像重建/编辑 | PCA 统一编码、片内/片间结构损失 |

**一句话**：数字衣服的「真参数」往往是 **sewing pattern**；Korosteleva 线打通数据与点云反求版型并走向可编程制版，中大 **NSM** 则把版型缝进可学习的 3D 生成与结构保持编辑——两边合起来，才是完整的参数化衣物建模叙事。
