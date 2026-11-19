# NeRF：Mip-NeRF

> Jonathan T. Barron et al., *Mip-NeRF: A Multiscale Representation for Anti-Aliasing Neural Radiance Fields*, ICCV 2021.  
> 索引：[Nerf.md](Nerf.md) · 前置：[Nerf_三大组成部分.md](Nerf_三大组成部分.md)

## 1. 原始 NeRF 的多尺度毛病

原始 NeRF 把每个像素建成一条**零厚度射线**，在点上查 MLP。现实中一个像素对应相机后的一小截**视锥**：

- 训练分辨率与测试分辨率不一致时，点采样对不上像素脚印；  
- 远处物体在图像上只占不到一像素，却仍用「针尖」查询 → **锯齿、混叠、jaggies**；  
- 常见伪影：漂浮密度、边缘闪烁、缩小视角发糊或闪。

根因可以想成：连续场景被点采样，没有按像素面积做正确的预滤波（图形学里的 mipmap / footprint 思想）。

## 2. 核心想法：用视锥代替射线

Mip-NeRF 对每个像素构造从光心出发的**圆锥 / 截锥（frustum）**，体积渲染在锥体内做，而不是在中心射线上取点。

实践上把截锥内的积分区域近似成 **各向异性高斯**（在视锥坐标系或世界系里用均值 + 协方差描述那一小团空间）。后续所有「查询编码」都针对这团高斯，而不是单点。

## 3. Integrated Positional Encoding（IPE）

普通位置编码 $\gamma(\mathbf{x})$ 是点上的傅里叶特征。对高斯分布的 $\mathbf{x}$，需要的是

$$
\mathbb{E}_{\mathbf{x}\sim\mathcal{N}(\mu,\Sigma)}\bigl[\gamma(\mathbf{x})\bigr],
$$

即特征的期望——等价于对高频做衰减，频率越高、方差越大，期望振幅越小（自然抗锯齿）。

Mip-NeRF 给出该期望的**闭式 / 高效近似（IPE）**，再把 IPE 向量喂给 MLP。效果：

- 大 footprint（远、低分辨率）→ 高频自动压掉 → 糊得合理；  
- 小 footprint（近、高分辨率）→ 保留高频 → 细节在。

一个网络覆盖多尺度，不必像图形学那样显式存一串 mip 层级纹理。

## 4. 网络与训练上的简化

相对「coarse + fine 两套 MLP」：

- Mip-NeRF 常用**单一 MLP**，靠 IPE 表达尺度；  
- 采样策略仍可分层，但多尺度行为主要由编码承担；  
- 损失仍是渲染色与 GT 的误差，可对多分辨率数据更稳。

质量上在多尺度基准上明显好于原版 NeRF；算力仍偏重（仍是大 MLP 体渲染），加速要接 NGP 等。

## 5. 后续：Mip-NeRF 360

> Barron et al., *Mip-NeRF 360*, CVPR 2022.

无界 360° 户外场景：近景物体 + 遥远背景。引入：

- **收缩坐标（contract）**：把无界欧氏空间映到有界球内，远处被压挤；  
- **提议网络（proposal network）** 等改进采样，替代粗糙的两段式；  
- 继续用 mip / 抗锯齿思想。

许多「室外 NeRF」工作以 360 为基线。

## 6. 和本系列其它笔记

| 问题 | 谁管 |
|:---|:---|
| 点查询 + 基本体渲染 | [Nerf_三大组成部分.md](Nerf_三大组成部分.md) |
| 像素脚印 / 锯齿 | **本文 Mip-NeRF** |
| 训练太慢 | [Nerf_InstantNGP.md](Nerf_InstantNGP.md) |
| 显式网格 | [Nerf_Plenoxels.md](Nerf_Plenoxels.md) |

## 7. 一句话

**Mip-NeRF 把「针尖射线」换成「像素视锥」，用积分位置编码在特征里做预滤波——专治多分辨率锯齿，并衍生出无界场景的 Mip-NeRF 360。**
