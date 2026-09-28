<!-- ---
layout: post
title: "第5章 §5.2 持续同调与Handle/Tunnel计算"
category: Parameterization
categories: ["Parameterization", "Parameterization-ComputationalConformalGeometry"]
--- -->

- 欧拉示性数 $\chi=V-E+F$，边界分量数 $n_b$，亏格 $g=(2-\chi-n_b)/2$；
- 在面邻接图上做 spanning tree，每条 **cotree 边**对应一条同调生成环 $\gamma_j$；
- 有多个边界分量时，还需连接各边界分量的路径。路径数 $n_p=2g+n_b-1$（闭曲面 $n_b=0$ 时 $n_p=2g$）。

## Tree-Cotree 算法

![Tree-Cotree算法](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20251030204651781.png)

### 6.1 算法流程

Tree-Cotree 是计算曲面的同调基底的经典算法。

![算法步骤1](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20251028140736064.png)

![算法步骤2](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20251028140847642.png)

![算法步骤3](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20251028140908958.png)



![算法步骤6](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20251030210725618.png)

![算法步骤7](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20251030212058915.png)

> **Tree-Cotree 将同调基底（割缝）显式地构造出来，为全局参数化和四边形网格化提供拓扑基础。**