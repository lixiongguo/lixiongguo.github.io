---
layout: post
title: "ESRGAN：感知超分的增强版 SRGAN"
categories: [TechSharing]
mathjax: true
---

> **论文**：Xintao Wang et al. [*ESRGAN: Enhanced Super-Resolution Generative Adversarial Networks*](https://arxiv.org/abs/1809.00219). ECCV Workshops 2018（PIRM-SR Challenge 感知区第一）。  
> 代码：[xinntao/ESRGAN](https://github.com/xinntao/ESRGAN)。GAN 基础见 [生成模型与 GAN]({% post_url 2.Machine Learning/1.机器学习与模式识别/2022-07-01-GAN及其后续优化 %})。

**一句话**：在 SRGAN 上改三处——**生成器（RRDB、去 BN）**、**判别器（Relativistic average GAN）**、**感知损失（激活前特征）**——得到更自然的纹理、更少伪影。

思想主线可记为：

```text
MSE/PSNR 超分（均值解、过平滑）
    → 感知损失（VGG 特征空间，Johnson / Bruna）
    → GAN 推自然流形（Goodfellow；人脸超分等先行）
    → SRGAN 合流（ResNet 生成器 + VGG content + 对抗）
    → ESRGAN 增强三件套
```

---

## 1. 学术思想追溯：SRGAN 之前

单图超分（SISR）本质是**严重不适定**：同一 LR 对应无穷多 HR。目标函数选什么，就决定落在哪一类解上。

### 1.1 像素损失与“均值解”

经典监督超分（含早期 CNN）几乎都最小化 **MSE**，等价于抬高 PSNR。Ledig 等用流形示意（SRGAN Fig. 3）：多个同样合理的高纹理 HR 在像素空间取平均 → **过平滑**。因此 PSNR 高 ≠ 观感好；放大倍数越大（如 $\times4$），缺纹理越刺眼。

深度路线里程碑：

| 工作 | 思想 |
| :--- | :--- |
| **SRCNN**（Dong et al., 2014） | 端到端学 LR→HR，仍以 MSE 为主 |
| **更深 / 递归 CNN**（VDSR、DRCN 等） | 加深与长程依赖，指标继续涨，平滑问题仍在 |
| **亚像素卷积**（Shi et al., ESPCN） | 在 LR 特征上学习上采样，快且准——后被 SRResNet/SRGAN 采用 |

### 1.2 感知损失：从像素空间跳出

若监督应贴近人眼，就该在**感知特征**上比，而不是逐像素：

- **Gatys** 风格迁移：用 VGG 特征做内容/风格；
- **Bruna et al.**：在 VGG / scattering 特征空间做 SR；
- **Johnson et al.**（ECCV 2016）：正式提出 **perceptual loss**，用预训练 VGG 特征的欧氏距离训超分与风格迁移网络。

要点：特征空间对“像素扰动但语义相近”更不敏感，优化目标更接近感知相似度。

### 1.3 GAN：把解推到自然图像流形

Goodfellow 的 GAN 提供另一条路：不显式规定“像什么”，而用判别器学“像不像真图”。生成器被逼进入**高概率自然图像区域**。

在逆问题 / 生成上的先声包括：Mathieu、Denton 等用 GAN 做视频/图像生成；Yu & Porikli 等把对抗项接到**人脸大倍率超分**；风格迁移与修复里也有 GAN + 特征损失（Li & Wand、Dosovitskiy & Brox 等）。

尚未解决的是：在一般自然图像、$\times4$ 上，把 **深度残差生成器 + 感知内容损失 + 对抗** 做成可复现、且 MOS 显著优于 MSE 方法的统一框架——这就是 **SRGAN**。

---

## 2. SRGAN：感知超分的合流点

> Ledig et al., *Photo-Realistic Single Image Super-Resolution Using a Generative Adversarial Network*, CVPR 2017.

### 2.1 问题陈述

如何在大倍率下恢复**细纹理**？SRGAN 的回答：换目标函数。定义感知损失 = **content（内容）** + **adversarial（对抗）**：

$$
\ell^{\mathrm{SR}}
=
\underbrace{\ell_X^{\mathrm{SR}}}_{\text{content}}
+
10^{-3}\underbrace{\ell_{\mathrm{Gen}}^{\mathrm{SR}}}_{\text{adversarial}}.
$$

- Content：可用 MSE，或（更关键）**VGG 特征距离**（激活后 $\phi_{i,j}$）；
- Adversarial：生成器最小化 $-\log D(G(I^{\mathrm{LR}}))$，骗过判别器。

对抗 min-max 与标准 GAN 同构，作用是把 $I^{\mathrm{SR}}$ 推向自然图像流形，避免停在 MSE 均值解。

### 2.2 架构：SRResNet + 判别器

| 模块 | 设计 |
| :--- | :--- |
| **生成器 $G$** | $B$ 个 residual block（$3\times3$、BN、PReLU），末尾 **亚像素卷积** 升分辨率；多数算力在 LR 特征空间 |
| **判别器 $D$** | 类 VGG 加深：stride 降分辨率、通道 64→512，最后 sigmoid 出“真图概率” |

单独用 MSE 训同一骨架得 **SRResNet**：PSNR/SSIM 很强，但观感仍偏糊。再换成感知损失 + GAN 得 **SRGAN**：PSNR 往往下降，**MOS 大幅上升**——首次系统证明：一般自然图 $\times4$ 也可做到接近照片级纹理。

### 2.3 SRGAN 凝固下来的范式

后世（含 ESRGAN）默认继承的三点：

1. **两套目标分离**：PSNR 网络 vs 感知/GAN 网络，不可用单一 PSNR 评感知；  
2. **$G$：深残差 + LR 空间计算 + 可学习上采样**；  
3. **损失：VGG content + 小权重对抗**（再可加像素项）。

局限（ESRGAN 针对之处）：BN 在深网 + GAN 下易伪影；标准判别器只判绝对真假；VGG **激活后**特征稀疏、亮度易偏；纹理有时假、噪。

Blau et al. 随后形式化 **感知–失真权衡**；PIRM-SR 用

$$
\mathrm{PI}=\tfrac12\bigl((10-\mathrm{Ma})+\mathrm{NIQE}\bigr)
$$

（越低越好）评感知。ESRGAN 在此范式上增强三件套，并夺感知区第一。

---

## 3. 生成器：去 BN + RRDB

整体仍沿用 SRResNet 式布局：多数计算在 **LR 特征空间**，再上采样到 HR。两处改动：

### 3.1 去掉 Batch Normalization

BN 在训练用 batch 统计、测试用全局估计；训练/测试分布不一致时易出伪影。更深、且在 **GAN 框架**下训练时更明显。去掉 BN 后：

- 训练更稳、伪影更少；
- 泛化更好；
- 省算力与显存（与 EDSR 等 PSNR 方法经验一致）。

### 3.2 Residual-in-Residual Dense Block（RRDB）

用 **RRDB** 替换 SRGAN 的普通 residual block：

- **多层残差**：残差套残差（residual-in-residual）；
- **主路径用 dense block**：层间稠密连接，容量更大（思路近 Residual Dense Network）。

辅助技巧（便于训很深的网）：

1. **Residual scaling**：残差支路乘 $\beta\in(0,1)$ 再加回主路，抑不稳定；
2. **更小初始化**：残差结构在参数方差较小时更好训。

实践中常用约 **23 个 RRDB** 的深模型（另有 16 块、容量近 SRGAN 的变体）。

---

## 4. 判别器：Relativistic average GAN（RaGAN）

标准 SRGAN 判别器判“这张图是真还是假”：$D(x)=\sigma(C(x))$。

**Relativistic discriminator** 改判相对真实性：“真图 $x_r$ 是否比假图 $x_f$ 更真”。RaD：

$$
D_{\mathrm{Ra}}(x_r,x_f)=\sigma\bigl(C(x_r)-\mathbb{E}_{x_f}[C(x_f)]\bigr).
$$

损失（对称形式）：

$$
\begin{aligned}
L_D^{\mathrm{Ra}}
&=
-\mathbb{E}_{x_r}\!\bigl[\log D_{\mathrm{Ra}}(x_r,x_f)\bigr]
-\mathbb{E}_{x_f}\!\bigl[\log\bigl(1-D_{\mathrm{Ra}}(x_f,x_r)\bigr)\bigr],
\\
L_G^{\mathrm{Ra}}
&=
-\mathbb{E}_{x_r}\!\bigl[\log\bigl(1-D_{\mathrm{Ra}}(x_r,x_f)\bigr)\bigr]
-\mathbb{E}_{x_f}\!\bigl[\log D_{\mathrm{Ra}}(x_f,x_r)\bigr].
\end{aligned}
$$

要点：$L_G^{\mathrm{Ra}}$ **同时依赖真、假样本**，生成器能从两端拿梯度；标准 GAN 里生成器一侧往往只“推假图变真”。实验上有助于更锐边缘与更细纹理。

---

## 5. 感知损失：用激活前特征

SRGAN 在 VGG 的 **ReLU 之后**特征上算距离。ESRGAN 改用 **激活前**：

1. **激活后极稀疏**（文中举例深网层激活率可低至约 11%）→ 监督弱；
2. 激活后特征易导致重建**亮度偏暗**；激活前更密、监督更强 → 亮度更准、边缘更利、纹理更丰。

常用 VGG19 的 `conv` 特征（如文中记法 VGG19-54：第 5 段池化前第 4 个卷积等）。PIRM 变体还试过基于材质识别微调的 **MINC** 感知损失（更偏纹理而非物体类别）。

生成器总损失：

$$
L_G = L_{\mathrm{percep}} + \lambda\, L_G^{\mathrm{Ra}} + \eta\, L_1,
$$

其中 $L_1=\mathbb{E}\|G(x_i)-y\|_1$，$x_i$ 为 LR，$y$ 为 HR；典型 $\lambda=5\times10^{-3}$，$\eta=10^{-2}$。

---

## 6. 训练与网络插值

### 6.1 两阶段训练

1. **PSNR 预训练**：仅 $L_1$，得到 $G_{\mathrm{PSNR}}$；  
2. **GAN 微调**：以 $G_{\mathrm{PSNR}}$ 初始化，用上式 $L_G$ 训对抗阶段。

预训练作用：避开极差局部最优；判别器一开始看到的是“还行的”超分图，而非纯噪声/黑图，更易专注纹理真假。

数据：DIV2K，常再加 Flickr2K、OST 等丰富纹理；$\times 4$；HR patch 如 $128\times128$；Adam。

### 6.2 Network interpolation（平衡清晰与保真）

纯 GAN 锐但易噪，纯 PSNR 糊但干净。对两套网络**参数线性插值**：

$$
\theta_G^{\mathrm{INTERP}}=(1-\alpha)\,\theta_G^{\mathrm{PSNR}}+\alpha\,\theta_G^{\mathrm{GAN}},
\quad \alpha\in[0,1].
$$

任意 $\alpha$ 都可得可用模型，**无需重训**即可连续调节风格。对比：

| 策略 | 效果 |
| :--- | :--- |
| **网络插值** | 平滑折中，伪影下降同时保留纹理 |
| **图像像素插值** | 常陷入“要么糊要么噪” |
| **改 $\lambda,\eta$ 重训** | 可调但成本高，难连续扫风格 |

---

## 7. 效果与位置

相对 SRGAN / EnhanceNet 等：动物毛发、草地、建筑结构更自然，人脸等处少“假皱纹”类伪影；相对 EDSR/RCAN 等 PSNR 方法：不追求最高 PSNR，但观感明显更锐。

后续生态：Real-ESRGAN 等面向真实退化（模糊、压缩、噪声），工程上更常用；本笔记聚焦原版 ESRGAN 相对 SRGAN 的三点增强。

---

## 8. 小结

| 阶段 | 核心主张 |
| :--- | :--- |
| MSE 超分 | 指标友好 → 均值解、过平滑 |
| 感知损失 | 在 VGG 特征空间对齐 |
| GAN | 解应落在自然图像流形 |
| **SRGAN** | 残差 $G$ + VGG content + 对抗，首次系统做出照片级 $\times4$ |
| **ESRGAN** | 去 BN/RRDB、RaGAN、激活前特征 + 网络插值 |

| 模块 | SRGAN | ESRGAN |
| :--- | :--- | :--- |
| 生成器块 | Residual + BN | **RRDB，无 BN** |
| 判别器 | 绝对真/假 | **RaGAN 相对真假** |
| 感知损失 | VGG 激活后 | **激活前特征** |
| 风格折中 | 调损失重训 | **网络参数插值** |

---

## 参考文献

1. Christian Ledig et al. *Photo-Realistic Single Image Super-Resolution Using a Generative Adversarial Network*. CVPR 2017. (SRGAN) [arXiv:1609.04802](https://arxiv.org/abs/1609.04802)
2. Xintao Wang et al. *ESRGAN: Enhanced Super-Resolution Generative Adversarial Networks*. ECCV Workshops 2018. [arXiv:1809.00219](https://arxiv.org/abs/1809.00219)
3. Chao Dong, Chen Change Loy, Kaiming He, Xiaoou Tang. *Learning a Deep Convolutional Network for Image Super-Resolution*. ECCV 2014. (SRCNN)
4. Wenzhe Shi et al. *Real-Time Single Image and Video Super-Resolution Using an Efficient Sub-Pixel Convolutional Neural Network*. CVPR 2016. (ESPCN)
5. Justin Johnson, Alexandre Alahi, Li Fei-Fei. *Perceptual Losses for Real-Time Style Transfer and Super-Resolution*. ECCV 2016.
6. Leon A. Gatys, Alexander S. Ecker, Matthias Bethge. *Image Style Transfer Using Convolutional Neural Networks*. CVPR 2016.
7. Joan Bruna, Pablo Sprechmann, Yann LeCun. *Super-Resolution with Deep Convolutional Sufficient Statistics*. ICLR 2016.
8. Ian Goodfellow et al. *Generative Adversarial Nets*. NeurIPS 2014.
9. Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun. *Deep Residual Learning for Image Recognition*. CVPR 2016.
10. Alexia Jolicoeur-Martineau. *The relativistic discriminator: a key element missing from standard GAN*. ICLR 2019. (RaGAN)
11. Bee Lim et al. *Enhanced Deep Residual Networks for Single Image Super-Resolution*. CVPRW 2017. (EDSR)
12. Yulun Zhang et al. *Residual Dense Network for Image Super-Resolution*. CVPR 2018.
13. Yochai Blau, Tomer Michaeli. *The Perception-Distortion Tradeoff*. CVPR 2018.
14. Yochai Blau et al. *PIRM Challenge on Perceptual Super-Resolution*. ECCVW 2018.
