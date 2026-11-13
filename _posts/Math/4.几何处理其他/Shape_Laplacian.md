# Laplace–Beltrami 谱：ShapeDNA 与 Shape Google

> 两篇"谱能拿来做形状描述"的经典：**ShapeDNA**（Reuter, Wolter, Peinecke, 2002–2006）把全局谱当形状指纹；**Shape Google**（Ovsjanikov, Ben-Chen, Solomon, Butscher, Guibas, SIGGRAPH 2011）用谱造出的**局部**描述子（HKS）做词袋检索与形状对应。

## 0. 共同起点

对 Laplace–Beltrami 算子做特征分解

$$
\Delta\phi_i=\lambda_i\phi_i,\qquad 0=\lambda_0\leqslant\lambda_1\leqslant\lambda_2\leqslant\cdots
$$

有限元离散后是广义特征问题 $\mathbf{A}\mathbf{v}=\lambda\mathbf{M}\mathbf{v}$（$\mathbf{A}$ 为余切刚度矩阵，$\mathbf{M}$ 为质量矩阵，即 cotan Laplacian 的广义版本）。贯穿全文的三个性质：

- **等距不变**：弯曲不变形地改变形状时，$\lambda_i$ 与 $\phi_i$ 都不变；
- **尺度敏感**：整体放大 $c$ 倍，$\lambda_i\to\lambda_i/c^2$，跨形状比较必须先归一化；
- 特征值只反映**全局**信息，特征函数 $\phi_i(x)$ 才携带**局部**信息。

## 1. ShapeDNA：把整个谱当指纹

取前 $N$ 个特征值拼成描述向量（去掉恒为 0 的 $\lambda_0$）：

$$
\mathrm{DNA}(S)=(\lambda_1,\lambda_2,\ldots,\lambda_N),
$$

常再按 $\lambda_1$ 或体积归一化，以消掉尺度。

- **为什么可行**：谱由内在几何决定，等距形变、刚体运动、顶点编号、网格离散都不改它；对噪声也稳健。
- **怎么用**：向量本身就是特征——直接近邻检索、SVM 分类、聚类；只需一次稀疏特征分解，代价远低于建立逐点对应。也可对切下来的一块（部分形状、截面）单独求谱。
- **局限**：
  1. 只给**全局**信息，不给点对应，无法直接做配准或属性迁移；
  2. 理论上**同谱异构**（isospectral drums）存在，谱并不唯一决定形状；
  3. 对**拓扑变化**（补洞、亏格改变）敏感；非等距的变形同样会改变谱。

## 2. Shape Google：局部 HKS + 几何词

### 2.1 局部描述子：热核签名 HKS

热核

$$
K_t(x,y)=\sum_{i\ge 0}e^{-\lambda_i t}\phi_i(x)\phi_i(y)
$$

的对角元 $K_t(x,x)=\sum_i e^{-\lambda_i t}\phi_i(x)^2$ 是"经过时间 $t$ 仍留在 $x$ 附近的热量"——局部几何的多尺度摘要：$t$ 小时只由局部曲率决定，$t$ 大时逐步扩散到全局。取一组尺度拼成签名

$$
h(x)=\bigl(K_{t_1}(x,x),\ \ldots,\ K_{t_n}(x,x)\bigr),
$$

它等距不变、对采样与噪声稳健，但**不是尺度不变**（同 ShapeDNA 的理由）。离散即 $\mathbf{K}_t=\Phi e^{-\Lambda t}\Phi^{\mathsf T}$ 取对角元，只需前若干特征对——与 [Heat_Geodesic](../../Math/4.几何处理其他/Heat_Geodesic.md) 的热方法同源。

### 2.2 从描述子到"几何词"

1. 形状上采样一批点，各算一份 HKS；
2. 对全库描述子做 k-means，得到**几何词典**（几百到上千个词）；
3. 每个形状表示为词的直方图，用 TF-IDF 加权，压低常见词、突出判别性词；
4. 检索时用直方图距离（$L^1$/交集）取近邻。

### 2.3 空间敏感：geometric expressions

纯词袋丢掉了空间关系。论文引入 **expression**：在局部参考系下把"词 + 相对位置/方向"量化，形成类似 NLP 中 bigram 的词对。直方图因此携带空间结构，除检索外还能支撑**形状对应**：先用 HKS 给出候选匹配，再用 expression 做空间一致性筛选。

### 2.4 局限

1. HKS 是**标量**函数，不反映方向，难以区分镜像与某些局部对称；
2. 对**拓扑变化**不稳健；
3. 词袋结果依赖采样密度、词典大小与 k-means 初始化。

## 3. 两者对比

| | ShapeDNA | Shape Google |
| :--- | :--- | :--- |
| 特征 | 全局谱向量 | 逐点 HKS + 词袋直方图 |
| 不变性 | 等距不变（需归一化尺度） | 同上 |
| 给出对应 | 否 | 是（HKS 匹配 + expression 一致性） |
| 计算 | 一次稀疏特征分解 | 特征分解 + k-means 建词典 |
| 主要弱点 | 同谱异构、拓扑敏感、无对应 | 标量描述子不辨方向、依赖采样与词典 |

一句话：**ShapeDNA 用"特征值"描述整体，Shape Google 用"特征函数"描述局部**；前者便宜但只能比对，后者贵些但能建立对应。
