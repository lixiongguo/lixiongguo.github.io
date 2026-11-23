---
layout: post
title: "基于GAN生成网络的重建"
categories: [TechSharing]
mathjax: true
---

> 路线：**cGAN**（条件对抗）→ **Pix2Pix / CycleGAN**（图像翻译与 PatchGAN）→ **Pix2Surf**（衣物 → SMPL UV）→ **Adversarial Loss** 在超分 / 修复等后续视觉任务中的延续。GAN 基础见 [生成模型与 GAN]({% post_url 2.Machine Learning/1.机器学习与模式识别/2022-07-01-GAN及其后续优化 %})；感知超分见 [ESRGAN](ESRGAN.md)。

---

## cGAN（Conditional GAN）

> Mirza & Osindero, *Conditional Generative Adversarial Nets*, arXiv:1411.1784, 2014.

### 无条件 GAN 缺什么？

原始 GAN（Goodfellow 2014）学的是无条件分布 $p(x)$：从噪声 $z\sim p_z$ 生成样本，判别器只判「像不像真数据」。这适合「随便出一张脸」，但重建 / 翻译任务要的是：

$$
\text{给定条件 }y\text{（标签、边缘图、语义图、另一模态…），生成对应的 }x\sim p(x\mid y).
$$

没有条件时，$G(z)$ 无法被告知「该出哪一类 / 哪一结构」；事后用类别分类器筛样本既慢又弱。**cGAN 把条件直接喂进生成器与判别器**，把对抗学习从 $p(x)$ 扩成 $p(x\mid y)$。

### 形式化

记条件为 $y$（下文与 Pix2Pix 的条件图 $x$ 是同一角色，符号随论文习惯而变）。

**生成器**：$G(z\mid y)$（或简写 $G(z,y)$）——噪声与条件一起决定输出。  
**判别器**：$D(x\mid y)$——看到的是**成对** $(x,y)$，既要像真样本，又要和 $y$ **匹配**。

目标函数相对原版 GAN，处处多一个 $y$：

$$
\begin{aligned}
\min_G\max_D\;\mathcal{L}_{\mathrm{cGAN}}(G,D)
&=
\mathbb{E}_{x\sim p_{\mathrm{data}}(x\mid y)}\bigl[\log D(x\mid y)\bigr] \\
&\quad+
\mathbb{E}_{z\sim p_z(z)}\bigl[\log\bigl(1-D\bigl(G(z\mid y)\mid y\bigr)\bigr)\bigr].
\end{aligned}
$$

训练博弈不变：$D$ 尽量把真对 $(x,y)$ 判真、假对 $(G(z,y),y)$ 判假；$G$ 尽量骗过 $D$。均衡处，$G$ 逼近条件数据分布 $p_{\mathrm{data}}(x\mid y)$。

实现上条件 $y$ 的注入方式常见几种：

| 方式 | 做法 | 适用 |
| :--- | :--- | :--- |
| 拼接 | 把 $y$（或 embedding）与 $z$ / 特征在通道维 concat | 图像条件、类别 one-hot |
| 特征调制 | FiLM、SPADE 等用 $y$ 调归一化参数 | 语义图 → 高分辨率图 |
| 跨注意力 | $y$ 作 key/value，$G$ 查询 | 文本、多 token 条件 |

早期 cGAN 论文多用「类别向量拼到 $z$ / 拼到 $D$ 输入」；Pix2Pix 把 $y$ 换成**整张条件图**，是同一框架的结构化特例。

### 为何 $D$ 也必须看条件？

若只有 $G$ 看 $y$、$D$ 只判 $x$ 真假：

- $G$ 可以生成「很像真图、但与 $y$ 无关」的样本（例如条件是「猫」，却出一张好看的狗）；  
- $D$ 无法惩罚这种**条件错配**，因为真假分布边缘上它仍像真实图像。

因此 cGAN 的判别对象是联合：真样本为 $(x,y)\sim p_{\mathrm{data}}$，假样本为 $(G(z,y),y)$。$D$ 学会的是「在这个条件下是否真实且对齐」。

### 条件可以是什么？

| 条件 $y$ | 典型任务 | 后文落点 |
| :--- | :--- | :--- |
| 类别 / 属性 | 指定类生成 | 数据增广 |
| **图像**（边缘、分割、灰度…） | 图像翻译 | **Pix2Pix** |
| 另一域图像（无配对） | 域迁移 | CycleGAN（双向 cGAN + 循环） |
| 低分辨率图 | 条件超分 | SRGAN 系（对抗 + 感知） |
| 隐变量 / 姿态码 | 可控生成 | 部分人体外观模型 |

共同点：**用 $y$ 收窄解空间**，对抗项只在「与 $y$ 相容」的切片里逼分布，比无条件 GAN 更适合有监督或弱监督的视觉重建。

### 与「纯回归」的分工

条件任务也可用 $G=\arg\min\|G(y)-x\|_1$，但像素损失偏好条件均值 → **模糊**。cGAN 额外要求输出落在真实条件分布的高密度区，从而：

- 保留合理的高频（纹理、边缘锐度）；  
- 在一对多映射里（一边缘多种合法上色）可配合噪声 $z$ 表达多模态（实践中图像翻译常把 $z$ 弱化或去掉，改靠 dropout 噪声）。

工程配方几乎总是：

$$
\mathcal{L}
=
\mathcal{L}_{\mathrm{cGAN}}
+\lambda\,\mathcal{L}_{\mathrm{rec}}(G(y),x)
\quad(\mathcal{L}_{\mathrm{rec}}=L_1\text{ / 感知损失等}).
$$

**$\mathcal{L}_{\mathrm{rec}}$ 管对齐与低频对齐，$\mathcal{L}_{\mathrm{cGAN}}$ 管是否像真。** 后文 Pix2Pix 正是这一配方在「图→图」上的标准实现。

---

## Pix2Pix

> Isola et al., *Image-to-Image Translation with Conditional Adversarial Networks*, CVPR 2017.

### 为什么“纯 U-Net”做不好图像翻译？

若只用像素损失（$L_1$ / $L_2$）训练 U-Net：

- **模糊**：像素损失偏好条件均值，高频纹理被平均掉；
- **感知不对齐**：低维语义对了，材质、锐利边缘仍假；
- **无分布约束**：输出只要“靠近 GT 均值”即可，不必落在真实图像流形上。

对抗项逼迫 $G(x)$ 在局部统计上像真图；PatchGAN 正是用低维、局部判决换来锐利纹理。因此 Pix2Pix = **U-Net 对齐结构 + cGAN/PatchGAN 补细节**，而不是单纯回归。

把上一节的 cGAN **特化成图像→图像翻译**：条件是输入图 $x$（语义分割、边缘、灰度等），目标是输出图 $y$（照片、上色等）。$G$、$D$ 都看到 $x$：
$$
\mathcal{L}_{\mathrm{cGAN}}(G,D)
=
\mathbb{E}_{x,y}\!\bigl[\log D(x,y)\bigr]
+
\mathbb{E}_{x,z}\!\bigl[\log\bigl(1-D(x,G(x,z))\bigr)\bigr].
$$

再加 $L_1$ 重建，避免只靠对抗而漂移：

$$
\mathcal{L}_{L_1}(G)=\mathbb{E}_{x,y,z}\bigl[\|y-G(x,z)\|_1\bigr],
\quad
G^*=\arg\min_G\max_D\;
\mathcal{L}_{\mathrm{cGAN}}+\lambda\mathcal{L}_{L_1}.
$$

默认架构：**U-Net 生成器** + **PatchGAN 判别器** + $L_1$。下面分开说清为什么。

### 生成器为什么用 U-Net？

许多翻译任务里，输入与输出**共享大量低层结构**（例如上色：边缘位置几乎不变；分割→照片：物体轮廓对齐）。若只用「编码器压成瓶颈再解码」的 encoder–decoder，低层细节必须挤过窄通道，易丢对齐信息。

**U-Net** 在对称层之间加 **skip connection**，把编码器的高分辨率特征直接接到解码器，相当于给网络一条「抄近路」：

- 低频 / 布局：可走瓶颈里的语义路径；  
- 边缘、纹理位置：可走跳连，保证空间对齐。

因此 Pix2Pix 的 $G$ 默认 U-Net，而不是光秃 encoder–decoder。

### 为什么 PatchGAN 更好？

判别器的感受野决定它在“管”图像的哪一尺度。Pix2Pix 对比了三种极端：

| 判别器 | 感受野 | 实际效果 |
| :--- | :--- | :--- |
| **PixelGAN**（$1\times1$） | 单像素 | 只对齐颜色直方图，几乎不改空间结构 |
| **ImageGAN**（整图） | 全图 | 参数多、难训；偏重全局是否像真图，对局部纹理约束弱 |
| **PatchGAN**（如 $70\times70$） | 局部块 | 锐利纹理、少模糊；参数少，可卷积滑过任意分辨率 |

![image-20260731215111765](../../../imgs/image-20260731215111765.png)

论文消融里还能读到更细的现象：

- **PixelGAN**：几乎不提升空间锐度，但会让颜色更饱和（论文 Figure 7 有量化）。例如仅用 $L_1$ 时巴士偏灰，加上 PixelGAN 后更容易出正确的红色——相当于轻量做了**颜色直方图匹配**，对空间结构帮助有限。  
- **$16\times16$ PatchGAN**：已能逼出锐利输出，FCN-score 也不错，但容易出现**拼贴 / tiling 伪影**。  
- **$70\times70$ PatchGAN**：减轻 tiling，分数略好，是默认折中。  
- **再放大到整图 ImageGAN**（论文约 $286\times286$ 感受野）：观感未见明显更好，FCN-score 反而明显更差——参数更多、网络更深，更难训。

**全卷积翻译**：PatchGAN 的另一好处是固定 patch 大小的 $D$ 可滑过**任意大图**。生成器同样可全卷积推理：在 $256\times256$ 上训练后，直接推 $512\times512$（如地图↔航拍），无需改结构。

**为何局部判决反而更好**（相对整图 $D$）：

1. **与 $L_1$ 分工**：$L_1$ 已能抓住低频（整体布局、大色块）；再让整图 $D$ 重复管低频收益有限。PatchGAN 专盯**高频**——边缘、材质、重复纹理是否像真，两者互补。
2. **马尔可夫假设**：假定相距超过 $N$ 的像素条件独立，图像是**纹理的马尔可夫随机场**。对风格化、上色、分割→照片这类任务，局部统计往往就是“真假”的关键。
3. **参数与泛化**：全卷积、参数量远小于 ImageGAN；同一套 $D$ 可滑窗用于训练时未见过的分辨率。
4. **训练信号更密**：一张图产出许多 patch 判决，梯度更丰富，不易只优化“整图平均看起来还行”而放过局部糊斑。

经验上：$N$ 太小（近 PixelGAN）细节仍弱；$N$ 太大接近 ImageGAN 则纹理变糊、训练变重。中等 patch（论文常用约 70）在质量与开销上折中最好。因此 Pix2Pix 的默认配方是 **U-Net + PatchGAN + $L_1$**。



---

## CycleGAN

> Zhu et al., *Unpaired Image-to-Image Translation using Cycle-Consistent Adversarial Networks*, ICCV 2017.

Pix2Pix / 标准 cGAN 需要**成对** $(x,y)$。许多域迁移（照片↔画风、夏↔冬）拿不到配对，CycleGAN 改用**无配对**数据：域 $X$、$Y$ 各有一批样本，学双向映射 $G:X\to Y$、$F:Y\to X$。对抗项仍是「条件在域上的真假」（各域一套判别器），额外用循环拴住内容：

- **对抗**：使 $G(X)$ 像 $Y$，$F(Y)$ 像 $X$；
- **循环一致**：强制 $F(G(x))\approx x$、$G(F(y))\approx y$，防止任意一对一乱映射。

$$
\mathcal{L}_{\mathrm{cyc}}(G,F)
=
\mathbb{E}_{x\sim X}\bigl[\|F(G(x))-x\|_1\bigr]
+
\mathbb{E}_{y\sim Y}\bigl[\|G(F(y))-y\|_1\bigr].
$$

总目标大致为两个域的 GAN 损失 + $\lambda\mathcal{L}_{\mathrm{cyc}}$（常再加 identity 损失稳住色彩）。相对 Pix2Pix：牺牲配对监督的精度，换来无标注域迁移能力；三维重建管线里常作**外观迁移 / 数据增广**前置，而不是直接出几何。

---



---

## 参考文献

1. Ian Goodfellow et al. *Generative Adversarial Nets*. NeurIPS 2014.
2. Mehdi Mirza, Simon Osindero. *Conditional Generative Adversarial Nets*. arXiv:1411.1784, 2014.
3. Phillip Isola, Jun-Yan Zhu, Tinghui Zhou, Alexei A. Efros. *Image-to-Image Translation with Conditional Adversarial Networks*. CVPR 2017. ([Pix2Pix](https://phillipi.github.io/pix2pix/))
4. Jun-Yan Zhu, Taesung Park, Phillip Isola, Alexei A. Efros. *Unpaired Image-to-Image Translation using Cycle-Consistent Adversarial Networks*. ICCV 2017. ([CycleGAN](https://junyanz.github.io/CycleGAN/))
5. Aymen Mir, Thiemo Alldieck, Gerard Pons-Moll. *Learning to Transfer Texture from Clothing Images to 3D Humans*. CVPR 2020. ([Pix2Surf](https://virtualhumans.mpi-inf.mpg.de/pix2surf/))
6. Christian Ledig et al. *Photo-Realistic Single Image Super-Resolution Using a Generative Adversarial Network*. CVPR 2017. (SRGAN)
7. Xintao Wang et al. *ESRGAN: Enhanced Super-Resolution Generative Adversarial Networks*. ECCVW 2018.
8. Ting-Chun Wang et al. *High-Resolution Image Synthesis and Semantic Manipulation with Conditional GANs*. CVPR 2018. (pix2pixHD，多尺度 PatchGAN)
9. Matthew Loper et al. *SMPL: A Skinned Multi-Person Linear Model*. SIGGRAPH Asia 2015.
10. Bharat Lal Bhatnagar et al. *Multi-Garment Net: Learning to Dress 3D People from Images*. ICCV 2019.
11. Justin Johnson, Alexandre Alahi, Li Fei-Fei. *Perceptual Losses for Real-Time Style Transfer and Super-Resolution*. ECCV 2016.
12. Max Jaderberg et al. *Spatial Transformer Networks*. NeurIPS 2015.
