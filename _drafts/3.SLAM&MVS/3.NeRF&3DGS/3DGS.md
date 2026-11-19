# 3D Gaussian Splatting（3DGS）

> Kerbl, Kopanas, Leimkühler, Drettakis. *3D Gaussian Splatting for Real-Time Radiance Field Rendering*, SIGGRAPH / ACM TOG 2023.  
> 项目：[repo-sam.inria.fr/fungraph/3d-gaussian-splatting](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/)  
> SfM 常用 [ColMap](../2.MVS/ColMap.md)；后期清理见 [SuperSplat](SuperSplat.md)；与体积场对照见 [Nerf.md](../3.NeRF/Nerf.md)。

显式、无结构的 **3D 高斯椭球** 表示辐射场：可微投影成 2D splat，用 tile-based 光栅做有序 $\alpha$-blending；训练时自适应增删高斯。相对 NeRF 系：无需沿射线采样 MLP，训得快、渲得实时。

## 1. 输入与初始化

输入是静态场景的一组 RGB 图，以及由 SfM（Schönberger & Frahm 2016，实践中即 COLMAP）标定的相机；SfM 附带的稀疏点云用来初始化 3D 高斯集合。

## 2. 高斯原语定义

每个 3D Gaussian 由 **位置（均值）**、**协方差矩阵** 与 **不透明度 $\alpha$** 定义；外观（颜色）另用球谐（SH）等方向相关参数描述，训练中一并优化。

高度 **各向异性** 的体积 splat 能用较少原语紧凑表达细结构（薄面、线状几何等），表示相对紧凑。

优化对象包括：位置、协方差（经尺度/旋转参数化）、$\alpha$，以及 SH 系数。工程关键是 **tile-based 可微光栅器**：支持各向异性 splat 的有序 $\alpha$-blending 与深度排序。

## 3. 优化与渲染总流程（Fig. 2）

```text
SfM Points
  → Initialization → 3D Gaussians
  → Projection（相机位姿）
  → Differentiable Tile Rasterizer → Image
       ↑__________________|  梯度回传
       └─ Adaptive Density Control（分裂 / 克隆等控密度）
```

从前向看：稀疏点 → 高斯 → 投影 → tile 光栅 → 图像。反向：图像损失经光栅器回传到高斯参数，并并行做自适应密度控制。训完后同一渲染器可实时漫游。

![image-20250728192842128](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250728192842128.png)

## 4. 为何选 3D 高斯

3D 高斯 **可微**，且易投影为 2D splat，从而做快速 $\alpha$-blending 渲染——兼顾无结构显式表示与实时合成。

## 5. 3D → 2D 投影（EWA）

渲染需把 3D 高斯投到像平面。Zwicker et al. (2001) 给出到图像空间的投影：给定观察变换 $W$，相机系下协方差为

$$
\Sigma' = J W \Sigma W^{T} J^{T} \tag{5}
$$

其中 $J$ 是透视投影仿射近似的雅可比，$\Sigma$ 为世界系 3D 协方差。实践中取 $\Sigma'$ 的 $2\times 2$ 上块作为屏幕上椭圆 splat 的协方差。



## 6. 协方差的可优化参数化

直接优化 $\Sigma$ 难保证正半定。将协方差看成椭球构型，用缩放矩阵 $S$ 与旋转矩阵 $R$：

$$
\Sigma = R S S^{T} R^{T} \tag{6}
$$



为独立优化缩放与旋转，分开存储：

- 三维向量 $\mathbf{s}$ → 对角缩放矩阵 $S$；
- 四元数 $q$ → 旋转矩阵 $R$（需归一化为单位四元数）。

再合成 $\Sigma$，保证优化过程中椭球始终合法。



## 7. 参数一览

| 参数 | 符号 / 形式 | 作用 |
|:---|:---|:---|
| 位置 | 均值 $\mu$ | 高斯中心 |
| 尺度 | $\mathbf{s}\in\mathbb{R}^3$ | 各向异性拉伸 |
| 旋转 | 四元数 $q$ | 椭球朝向 |
| 不透明度 | $\alpha$ | 混合权重 |
| 外观 | SH 系数 | 视角相关颜色 |

## 8. 一句话

**3DGS = SfM 稀疏点初始化的各向异性 3D 高斯 + EWA 投影成 2D splat + tile 光栅 $\alpha$-blending + 自适应密度控制；显式可微，训练快、可实时渲染。**
