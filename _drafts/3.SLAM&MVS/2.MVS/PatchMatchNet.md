# PatchmatchNet

> Fangjinhua Wang, Silvano Galliani, Christoph Vogel, Pablo Speciale, Marc Pollefeys.  
> *PatchmatchNet: Learned Multi-View Patchmatch Stereo*, CVPR 2021 (Oral).  
> [arxiv](https://arxiv.org/abs/2012.01411) · [code](https://github.com/FangjinhuaWang/PatchmatchNet)

在 MVSNet / CasMVSNet 一脉「建 3D 代价体 + 3D CNN 正则」之外的另一条高效路线：把传统 **PatchMatch**（随机初始化 → 传播 → 评价）做成**可学习、多尺度级联、端到端**的深度图 MVS。不靠巨型 3D 代价体正则，显存与深度采样数近似解耦，更适合高分辨率与资源受限设备。

相对 CasMVSNet 等（论文 Fig.1，$1152\times 864$）：精度有竞争力，同时约 **≥2.5× 更快、显存约减半**。

## 1. 动机：为何还要 PatchMatch？

| 路线 | 代表 | 瓶颈 |
|:---|:---|:---|
| 单次代价体 | MVSNet | $W\cdot H\cdot D\cdot F$ 立方涨 |
| 级联代价体 | CasMVSNet, UCS-Net, CVP-MVSNet | 仍有多级 3D 体积与 3D CNN |
| 沿深度扫 | R-MVSNet | 省显存但更慢 |
| **学习 PatchMatch** | **PatchmatchNet** | 每像素只维护少量假设，靠传播利用空间相干 |

传统 Gipuma / COLMAP / ACMM 已证明：深度图有空间相干性，不必对每个像素穷举全深度。PatchmatchNet 保留这一效率，并把 **传播 / 评价** 换成基于深度特征的自适应模块。

## 2. 总览

```text
{I_i} ──► FPN 多尺度特征
              │
     ┌────────┴────────┐
     │  Stage 3 (粗)   │  逆深度随机初始化 + PatchMatch×2
     │  Stage 2        │  局部扰动 + 传播/评价 ×2
     │  Stage 1        │  再细化 ×1（该阶段可关传播）
     └────────┬────────┘
              │
     RGB 引导上采样细化 ──► 全分辨率深度
```

阶段 $k$ 上深度图分辨率约为 $W/2^k \times H/2^k$（输入 $W\times H$）。**Stage 0 不做 PatchMatch**，直接从 stage 1 上采样并用参考图细化。

每次 PatchMatch 迭代：

1. **Initialization / Local perturbation**：产生深度假设  
2. **Adaptive propagation**：从邻居借假设  
3. **Adaptive evaluation**：warp → 匹配代价 → 空间聚合 → soft 回归  

## 3. Initialization 与局部扰动

**最粗阶段第一次迭代**：在逆深度范围上按像素随机采 $D_f$ 个假设（均匀覆盖逆深度区间），利于复杂大场景，且与视差空间更一致。论文训练用 $D_f=48$。

**后续迭代 / 更细阶段**：在上一估计（可上采样）附近做 **local perturbation**——在归一化逆深度邻域 $R_k$ 内均匀采 $N_k$ 个假设，$R_k$ 随阶段收窄（如 $R_3=0.38,\ R_2=0.09,\ R_1=0.04$；$N_3=16,\ N_2=N_1=8$）。比「只靠传播」更多样，能局部纠错。

## 4. Adaptive Propagation

经典红黑棋盘固定邻居传播（Gipuma）易跨物体边界。这里用 **Deformable Convolution** 思想：在固定网格偏移 $\{o_i\}$ 上再学像素相关偏移 $\{\Delta o_i\}$，从参考特征 $F_0$ 预测：

$$
D_p(p) = \bigl\{ D\bigl(p + o_i + \Delta o_i(p)\bigr) \bigr\}_{i=1}^{K_p}.
$$

$D$ 为上一迭代深度。效果：边界像素倾向从物体内侧取假设；弱纹理区可从更大邻域取一致深度，加快收敛。

实现上 stage 3/2/1 的 $K_p$ 常取 $16,8,0$（最细 PatchMatch 阶段可关闭传播，只靠局部扰动）。

## 5. Adaptive Evaluation

### 5.1 可微 Warp

对参考像素 $p$、假设深度 $d_j$，投到源视角 $i$：

$$
p_{i,j}
= K_i\bigl(
R_{0,i}\,K_0^{-1}\,p\,d_j + t_{0,i}
\bigr),
$$

双线性采样源特征 $F_i(p_{i,j})$。注意这里是**逐像素不同假设**的稀疏匹配，不是整幅 fronto-parallel 平面扫满 $D$ 层再堆成稠密 4D 体再上 3D U-Net。

### 5.2 分组相关 + 像素级视角权重

特征按通道均分成 $G$ 组，组内做相关（group-wise correlation）：

$$
S_i(p,j)^{g}
= \frac{G}{C}\bigl\langle F_0(p)^{g},\, F_i(p_{i,j})^{g}\bigr\rangle.
$$

**视角权重** $w_i(p)$：在最粗阶段首次迭代、用初始多样假设上的相似度，经 $1\times1\times1$ 的轻量 3D 卷积 + sigmoid，对每个假设出置信，再取

$$
w_i(p) = \max_j P_i(p,j).
$$

之后各阶段固定并用上采样复用，避免每迭代重估。多视角聚合：

$$
\bar S(p,j)
= \frac{\sum_i w_i(p)\,S_i(p,j)}{\sum_i w_i(p)}.
$$

再经小网络压成标量代价 $C(p,j)$。

### 5.3 自适应空间代价聚合

在假想窗口（正视平面邻域）上聚合，偏移同样可学习，避免跨边界：

$$
\tilde C(p,j)
= \frac{1}{\sum_k w_k d_k}
\sum_{k=1}^{K_e}
w_k d_k\, C(p+p_k+\Delta p_k,\, j),
$$

$w_k,d_k$ 由特征相似与深度相似调制（细节见原文补充）。弱纹理扩大上下文，边界保持贴边。论文各阶段 $K_e=9$。

### 5.4 深度回归

对 $-\tilde C$ 沿假设维 softmax 得 $P$，期望回归：

$$
D(p)=\sum_{j} d_j\, P(p,j).
$$

概率分布同样可作置信，供后续滤波。

**不参数化倾斜平面（slanted plane）**：省显存；空间模式交给自适应评价窗口。

## 6. 细化与损失

Stage 1 深度上采样到全分辨率：分别提深度特征与参考图特征，反卷积对齐后拼接，2D CNN 学残差（深度先归一化到 $[0,1]$），得 $D_{\mathrm{ref}}$。

各阶段每次 PatchMatch 迭代 + 最终细化均用 smooth L1：

$$
L_{\mathrm{total}}
= \sum_{k=1}^{3}\sum_{i=1}^{n_k} L_i^{k} + L_{\mathrm{ref}}^{0}.
$$

## 7. 稳健训练（视角采样）

许多方法固定选「得分最高的 2 个源视图」训练，可见性过强，视角权重网络学不好遮挡。PatchmatchNet：对每个参考视图，从得分前十的源视图中**随机抽 4 个**（训练时 $N=5$ 含参考）。增加多样性，并让弱相关视角参与，强化可见性估计与泛化。

## 8. 与 MVSNet / CasMVSNet 对照

| | MVSNet | CasMVSNet | PatchmatchNet |
|:---|:---|:---|:---|
| 深度假设 | 全域均匀密采样 | 级联收窄范围 | 随机 / 局部扰动 + 传播 |
| 正则 | 稠密 3D 代价体 + 3D CNN | 多级较小 3D 体 | **无** 3D 体正则；空间靠传播与自适应聚合 |
| 匹配度量 | 特征方差 | 同左 | 分组相关 + 视角权重 |
| 粗到细 | 弱（特征下采样） | 代价体 cascade | PatchMatch cascade + RGB 细化 |
| 显存 vs $D$ | 近似线性于 $D$（体积） | 仍依赖各级 $D_k$ | 主要随假设数与特征，远轻于满体积 |
| 典型优势 | 范式奠基 | 高精度高分 | **速度 / 显存**，完整度强 |

DTU 上 overall 与 CasMVSNet / UCS-Net 同档（约 $0.35\,\mathrm{mm}$），完整度往往更好；ETH3D / Tanks and Temples 上泛化也扎实。点云融合后处理可沿用 MVSNet 类光度 + 几何滤波。

## 9. 局限与直觉

- 粗阶段若大片错误，细阶段局部扰动范围有限；自适应传播是纠边与补洞的关键。  
- 仍要已知相机；无倾斜平面时，大倾角表面依赖特征与聚合窗口是否贴表面。  
- 「高效」不等于永远最高精度：追求极致精度时，级联代价体族仍常更强，但代价是算力。

## 10. 一句话

**用可学习的自适应传播与评价，把 PatchMatch 嵌进多尺度级联深度图 MVS——丢掉 3D 代价体正则，换高分辨率下的速度与显存。**
