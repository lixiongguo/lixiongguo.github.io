## 应用实例：华为 AutoBSS（BO 用于 AutoML）

[AutoBSS](https://arxiv.org/abs/2010.10261)（Y. Zhang, J. Zhang, Z. Zhong，**华为诺亚方舟实验室**，NeurIPS 2020）将 **贝叶斯优化**用于一类常被忽视的 **AutoML / NAS** 子问题：在**固定 block 结构**（如 ResNet bottleneck、MBConv）下，自动搜索 **Block Stacking Style (BSS)**——各 stage 堆叠多少 block、每 stage 通道/宽度如何分配——而非重新设计卷积算子或 block 内部拓扑。

### 6.1 背景：BSS 是什么，为何值得搜

现代 CNN 设计通常分两步：

1. **设计 block 结构**（如 ResNet 残差块、MobileNet 倒瓶颈、EfficientNet MBConv+SE）；
2. **堆叠 block 构成整网**（BSS）：每 stage 的 **block 数**、**通道数**、下采样时是否倍增通道等。

社区长期关注 (1)，(2) 多沿用人工经验：

- 下采样时通道**翻倍**（VGG、ResNet、ShuffleNet 等）；
- **中间 stage 分配更多 block**（ResNet 的「两头少、中间多」）。

论文指出：BSS 对精度影响**不可忽视**（如金字塔式 BSS 优于原始 ResNet 布局），但人工规则未必最优。**AutoBSS** 把 BSS 编码为定长向量 **BSSC**，在 FLOPs/时延约束下用 BO **数十次全量训练**即可搜到更优堆叠方式。

### 6.2 问题形式化

在算力预算 $B$ 下：

$$
x^* = \arg\max_{x\in\Lambda,\;\mathrm{FLOPs}(x)\le B} \mathrm{Acc}(x),
$$

| BO 概念 | AutoBSS |
| :--- | :--- |
| 决策 $x$ | **BSSC**：各 stage 通道 $C_i$、block 数 $L_i$、扩展因子 $T_i$ 等（依骨干网而定） |
| 目标 $f(x)$ | ImageNet 等任务上**完整训练**的 Top-1 精度（无早停、无权重共享） |
| 搜索空间 $\Lambda$ | 满足 FLOPs $\le B$ 的所有合法 BSSC；规模极大，实际在候选子集 $\Omega$ 上操作 |
| Surrogate | 对**精炼后**编码 $\hat{x}$ 建 GP，$y\approx\mathrm{Acc}$ |
| 采集 | **EI**；并行训 $k$ 个网时用 **EEI**（batch Expected Improvement） |

**EfficientNet-B0 的 BSSC 示例**（论文 §4.1）：9 个 stage，编码为

$$
\{C_3,\ldots,C_8,\; L_3,\ldots,L_8,\; T_3,\ldots,T_8\},
$$

$C_i$：stage $i$ 输出通道；$L_i$：block 个数；$T_i$：MBConv 扩展因子。ResNet / MobileNetV2 有各自 BSSC 定义（见论文附录 B.2）。

### 6.3 与常见 NAS 的对比：为何选 BO、为何要「改 BO」

| 方法 | 搜索对象 | 评估方式 | 典型采样量 | 问题 |
| :--- | :--- | :--- | :--- | :--- |
| BlockQNN 等 RL-NAS | 含 BSS | 早停、数千次评估 | $\gg 10^3$ | 有偏评估，排序与最终精度相关性差 |
| Once-for-All 等 | 宽/深 | **权重共享** supernet | 中 | 共享权重引入评估偏差 |
| EfficientNet | 缩放常数 | **网格搜索** 宽×深×分辨率 | 网格有限 | 不够灵活 |
| 随机搜索 [38] | 任意 | 全量/有偏均有 | 64+ | 强基线，但样本效率低 |
| **AutoBSS** | **仅 BSS** | **无偏全量训练** | **64**（4 轮×16） | 需把 BO 适配大离散空间 |

**核心论点**：

1. BSSC 描述各 stage **算力分配**，物理含义强 → 相近 BSSC 精度相近 → 适合 **GP + 平滑核**（§2、§6.6）；
2. 直接 BO 在**大离散空间**效果差 → 需要 **候选集压缩 + BSSC 精炼 + 聚类**，只在聚类中心上建 GP、跑 EI；
3. 样本效率足够高（$\sim 64$ 次）→ 可用**无偏评估**，避免早停/共享导致的搜索–最终精度脱节 [30,31]。

### 6.4 算法总览

```
┌─────────────────────────────────────────────────────────────┐
│  构造候选集 Ω（≈10⁴）→ 精炼 BSSC → k-means 聚类            │
│       ↓ 每轮：在聚类中心上 GP+EI/EEI 选 16 个 BSSC         │
│       ↓ 无偏训练 → 更新观测集 O → 迭代（共 4 轮）            │
└─────────────────────────────────────────────────────────────┘
```

**默认超参**（论文 §4.1）：$|\Omega|=10000$；**4 轮迭代**，每轮评估 **16** 个 BSSC，合计 **64** 次训练；聚类数每轮为 $16,\,160,\,N/10,\,N$（$N=|\Omega|$）；ResNet/MobileNet 训 **120 epoch**，EfficientNet **350 epoch**；FLOPs 阈值取原网 FLOPs。

### 6.5 候选集构造 (Candidate Set Construction)

全空间 $\Lambda$ 不可枚举。从 $\Lambda$ 抽子集 $\Omega$，满足：

1. $\Omega$ 与 $\Lambda$ **分布相近**（覆盖多样 BSS）；
2. $\Omega$ 中配置**期望精度**优于未入选者。

**按前缀随机采样**：BSSC $x=(x_0,\ldots,x_m)$，$x_i\in C^i$。理想采样概率

$$
P^i_j = \frac{|S(x[:i]\cup c^i_j)|}{\sum_{\hat{j}} |S(x[:i]\cup c^i_{\hat{j}})|},
\qquad
S(x[:r])=\{\hat{x}\in\Lambda:\hat{x}[:r]=x[:r]\},
\tag{AutoBSS-1}
$$

$|S(\cdot)|$ 难精确计算，用递归近似 $|S_D(x[:r])|$（深度 $D$，中位数 $c^i_{\mathrm{mid}}$）估计（论文式 (2)）。

**后处理**：随机选一维 $x_i$，在不超 FLOPs 前提下按步长**增大**通道或 block 数（增大算力通常不损精度），重复至无法增大——使 $\Omega$ 偏向「更强」配置。

### 6.6 BSSC 精炼 (Refining)

实验（ResNet18 上随机 220 个 BSS）：标准化后 BSSC 的欧氏距离与精度差 $|\mathrm{Acc}(x_1)-\mathrm{Acc}(x_2)|$ **正相关**，但关系**非线性**。BO/GP 依赖核的平滑/Lipschitz 假设：

$$
|\mathrm{Acc}(x_1)-\mathrm{Acc}(x_2)| \lesssim C\|\hat{x}_1-\hat{x}_2\|_2.
$$

从**第 2 轮迭代**起，用已评估样本训练线性层 $x\mapsto\hat{x}$（初始权重为单位阵），损失鼓励「距离 ∝ 精度差」：

$$
\mathcal{L}_{\mathrm{dy}}
= \left|
\frac{|y^{(0)}-y^{(1)}|}{\|\hat{x}^{(0)}-\hat{x}^{(1)}\|_2}
-
\frac{|y^{(2)}-y^{(3)}|}{\|\hat{x}^{(2)}-\hat{x}^{(3)}\|_2}
\right|^2,
\tag{AutoBSS-3}
$$

从四组已评估 $(x,y)$ 中采样训练。精炼后距离–精度差更接近线性上界（论文 Figure 2/3(b)），**GP 假设更成立**。

### 6.7 BSS 聚类 (Clustering)

对精炼 BSSC 做 **k-means**（欧氏距离）。**只在聚类中心**上建 GP、跑采集函数，而非在整个 $\Omega$ 上：

- 避免采样全挤在局部最优；
- 使每轮 16 个评估点**分散**，GP 更好覆盖候选集；
- 聚类数随迭代增加，与已评估样本增多、精炼更准相匹配。

**消融**（ResNet18，Table 2）：去掉聚类后 top-5 BSS 平均精度 **72.62%** vs 有聚类 **73.08%**（约 **0.46%** 降幅），说明聚类对 BO 选点至关重要。

### 6.8 GP 与 EI / EEI

对精炼编码 $\hat{x}$，**SE 核**（§3.1）：

$$
\kappa(\hat{x},\hat{x}_0)=\exp\!\left(-\frac{1}{2\sigma^2}\|\hat{x}-\hat{x}_0\|_2^2\right).
$$

观测集 $\mathcal{O}=\{(\hat{x}^{(i)},y^{(i)})\}$，$\tau=\max_i y^{(i)}$。

$$
\phi_{\mathrm{EI}}(\hat{x})=\mathbb{E}\bigl[\max\{0,\, f(\hat{x})-\tau\}\mid\mathcal{O}\bigr].
\tag{AutoBSS-4}
$$

**并行**训练多个网络时，用 **EEI** [34]：将 batch 内尚未评估的 $y^{(n+j)}$ 视为 GP 后验随机变量，对联合改进取期望

$$
\phi_{\mathrm{EEI}}(\hat{x})
=\mathbb{E}\Bigl[\mathbb{E}\bigl[\max\{0,f(\hat{x})-\tau\}\mid\mathcal{O},\{(x^{(n+k)},\hat{y}^{(n+k)})\}_{k<j}\bigr]\Bigr],
\tag{AutoBSS-5}
$$

在聚类中心上用 **Monte Carlo** 估计，取 $\phi_{\mathrm{EEI}}$ 最大者入 batch。最优 BSS 未必出现在**最后一轮**——EI 兼顾探索，与 §5.3 一致。

### 6.9 实验结果

**ImageNet 分类**（Table 1，同量级 FLOPs；括号内为相对原始 BSS 提升）：

| 骨干 | 原始 Top-1 | 随机 64 次 BSS | **AutoBSS** |
| :--- | :--- | :--- | :--- |
| ResNet18 | 71.21% | 72.34% | **73.22%** (+2.01%) |
| ResNet50 | 77.09% | 77.48% | **79.29%** (+1.08%，350 ep.) |
| MobileNetV2 | 72.13% | 72.13% | **74.50%** (+0.83%) |
| EfficientNet-B0 | 77.10% | 76.73% | **77.79%** (+0.69%) |
| EfficientNet-B1 | 79.10% | 78.56% | **79.48%** (+0.38%) |

相对**同空间随机 64 次**采样，AutoBSS 高约 **0.7%–1.1%**；相对 RL-NAS 搜过的 EfficientNet-B0 仍可提升，而 AutoBSS 仅需 **64** 次全量训练（RL 常需数万次有偏评估）。

**搜索过程观察**（ResNet18，Figure 3(a)）：

- **第 1 轮**已出现较好 BSS：候选集构造剔除了大量劣质配置，聚类避免全落局部极小；
- **后 2 轮**常出现全局最优附近样本：精炼 BSSC 与 GP 随 $|\mathcal{O}|$ 增大而更准。

**下游泛化**（换任务、换 FLOPs 阈值仍用搜到的 BSS 思想）：

| 任务 | 提升（论文报告） |
| :--- | :--- |
| MobileNetV2 压缩 (130M FLOPs) | Top-1 **69.65%**，优于 Meta Pruning / ThiNet 等 |
| COCO 检测 Mask R-CNN-R50 | bbox AP **+0.66%**，mask AP **+0.91%** |
| COCO RetinaNet-R50 | bbox AP **+0.63%** |
| VOC 语义分割 PSPNet / PSANet | mIoU **+1%** 量级 |

说明 BSS 是**跨任务**的宏观结构自由度，不只服务于分类。

### 6.10 搜到的 BSS 长什么样（定性）

论文对比原始 ResNet18 与搜得 BSS（Figure 4）：

- 原始：各 stage **算力均匀**（每 stage FLOPs $\approx$ 405M）；
- AutoBSS：**后期 stage 分配更多 FLOPs**；早期用**多层的窄 block**（大感受野）；最后一 stage 常仅 **1 个极宽 block**（语义特征需更多通道）。

结论：人工「均匀分配」并非最优；BSS 实质是在固定 block 下做**算力预算的最优分配**——与 BO 在离散空间上找 $x^*$ 的问题形态一致。

### 6.11 与华为其它 BO / AutoML 生态

| 产品 / 论文 | 层级 | BO 角色 |
| :--- | :--- | :--- |
| **AutoBSS** | 网络 **BSS 架构** | 定制 GP+EI/EEI+聚类/精炼，64 次无偏训练 |
| **[HEBO](https://github.com/huawei-noah/hebo)** | 通用黑盒（超参、混合变量） | 异方差进化 BO；NeurIPS 2020 BBO Challenge 冠军 |
| **ModelArts AutoSearch** | 训练 **超参** | SMAC（贝叶斯优化）、TPE、模拟退火 |

三者共用「**昂贵黑箱 + surrogate + 采集函数**」范式（本篇 §1–§5），但 **$x$ 的语义**与 **$f(x)$ 的评估成本**差几个数量级：AutoBSS 一次评估 = 整网 ImageNet 级训练；ModelArts 一次评估 = 单次训练 job；HEBO 面向更一般的函数查询接口。

**参考文献**：Y. Zhang, J. Zhang, Z. Zhong, *AutoBSS: An Efficient Algorithm for Block Stacking Style Search*, NeurIPS 2020. [arXiv:2010.10261](https://arxiv.org/abs/2010.10261)

---

## 7. 小结

| 模块 | 内容 |
| :--- | :--- |
| GP | 函数空间上的多元高斯；$m,k$ 定先验；样本路径、核=相似度、GPR+噪声 |
| 目标 | $\arg\min_{x\in\mathcal{X}} f(x)$，$f$ 黑箱、无梯度 |
| surrogate | GP 后验 $\mathcal{N}(\mu_t,\sigma_t^2)$ 见 (5)–(7) |
| 核 | SE (2)、Matérn (3) 等 |
| 选点 | $\max_x \alpha(x)$：UCB / PI / EI / Thompson |
| 迭代 | 评估 $f(x_{t+1})$，更新 $\mathcal{D}$，直至预算用尽 |
| 应用 | **AutoBSS**：BSSC 精炼+聚类+GP/EI/EEI，64 次无偏训练搜 BSS |

**参考文献（应用）**：Y. Zhang, J. Zhang, Z. Zhong, *AutoBSS: An Efficient Algorithm for Block Stacking Style Search*, NeurIPS 2020. [arXiv:2010.10261](https://arxiv.org/abs/2010.10261)