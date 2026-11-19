# NeRF：Plenoxels（无 MLP 的辐射场）

> Sara Fridovich-Keil*, Alex Yu* et al., *Plenoxels: Radiance Fields without Neural Networks*, CVPR 2022.  
> 索引：[Nerf.md](Nerf.md) · 对照：[Nerf_InstantNGP.md](Nerf_InstantNGP.md)、[Nerf_三大组成部分.md](Nerf_三大组成部分.md)

## 1. 论点

NeRF 证明了「连续辐射场 + 体渲染 + 多视角光度」很强，但并不证明 **MLP 必不可少**。Plenoxels 问：若把密度和颜色直接存在 **稀疏体素** 里，用同样的体积渲染优化，能否又快又好？

答案：在许多基准上可以——训练显著快于原版 NeRF，质量可竞争。

## 2. 表示

- 场景放在规则网格上，只保留**非空**体素（稀疏）；  
- 每个体素存：  
  - 密度 $\sigma$；  
  - 视角相关颜色的 **球谐（SH）系数**（低阶即可覆盖中等非朗伯）；  
- 查询时对 $\mathbf{x}$ **三线性插值** 密度与 SH，再由方向算 $c(\mathbf{d})$。

无深度网络前向；优化变量就是这些格点系数。

## 3. 渲染与优化

沿射线采样 → 插值 $\sigma,c$ → 与 NeRF 相同的 α-compositing 得 $\hat C$ → 与 GT 比损失。

额外常用：

- **总变差（TV）** 等空间平滑，抑制网格噪声；  
- 粗到细或剪枝空体素，控制显存；  
- 可与金字塔调度一起用。

优化更像传统「可微体素拟合」，收敛路径与 Adam 训大 MLP 不同，往往更痛快。

## 4. 和 Instant-NGP / 原 NeRF

```text
原 NeRF：     PE → 大 MLP → (c,σ)
Plenoxels：   稀疏体素(σ, SH) → 插值 → (c,σ)
Instant-NGP： 哈希特征 → 小 MLP → (c,σ)
```

| | 显式程度 | 速度 | 灵活性 |
|:---|:---|:---|:---|
| 原 NeRF | 低 | 慢 | 高（隐式连续） |
| Plenoxels | 高 | 快 | 中（网格分辨率上限） |
| Instant-NGP | 中（混合） | 很快 | 较高 |

Plenoxels 的历史意义：把社区焦点从「加深 MLP」扭向「更好的空间数据结构 + 体渲染」。

## 5. 局限

- 分辨率与显存直接挂钩；超大场景要分块 / 稀疏八叉树类扩展（后续工作）。  
- SH 阶数限制高频高光；极端视角相关可能不如深层 MLP。  
- 表面抽取仍非 SDF，网格质量一般需后处理。

## 6. 一句话

**Plenoxels 用稀疏体素 + SH 换掉大 MLP，保留体渲染与多视角损失——证明 NeRF 的灵魂是可微辐射积分，不是神经网络本身。**
