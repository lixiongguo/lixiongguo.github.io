---
layout: post
title: "Augmented Random Search（ARS）"
date: 2024-05-01
categories: [ReinforcementLearning]
mathjax: true
---

> **论文**：Horia Mania, Aurelia Guy, Benjamin Recht. [*Simple Random Search Provides a Competitive Approach to Reinforcement Learning*](https://arxiv.org/abs/1803.07055). NeurIPS 2018.
>
> 前置：[强化学习：介绍]({% post_url 2.Machine Learning/3.强化学习/2021-09-01-强化学习：介绍 %})；策略梯度背景见 [强化学习：策略梯度方法]({% post_url 2.Machine Learning/3.强化学习/2022-01-01-强化学习：策略梯度方法 %}).

**Augmented Random Search（ARS，增强随机搜索）** 表明：在 MuJoCo 连续控制等任务上，对**静态线性策略**做精心设计的**随机搜索**，无需价值网络、无需 BPTT、无需 replay，即可与 TRPO、PPO、进化策略（ES）等深度 RL 方法**同台竞技**。论文贡献不在复杂模型，而在一组**极简但关键的增强技巧**（镜像、滤波、对偶采样等），把朴素随机搜索推上 SOTA 水平。

---

## 1. 动机：随机搜索为何值得认真做？

策略梯度方法优化

$$
\max_\theta J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta}\!\left[\sum_{t=0}^{\infty} \gamma^t r_t\right],
$$

需估计 $\nabla_\theta J$，方差大、超参多、实现重。最朴素的替代是**随机搜索（Random Search, RS）**：在参数空间扰动 $\theta$，用 rollout 回报 $R(\theta)$ 作适应度，沿好的方向更新——本质是**零阶优化**（finite-difference / 进化式）。

长期以来 RS 被视为「基线太弱」。Mania et al. 指出：此前 RS 失败往往因为**策略类、预处理与采样方式**未调到位；对**线性策略 + 状态预处理 + 若干增强**后，RS 在 locomotion 上可与深度 RL 匹敌，且**并行极简、无反向传播**。

---

## 2. 策略类：静态线性策略

ARS 限制策略为**时间不变线性映射**（static linear policy）：

$$
a_t = \theta^\top \phi(s_t),
$$

- $s_t \in \mathbb{R}^d$：环境观测（关节角、角速度、躯干姿态等）；
- $\phi$：**固定预处理**（见 §4），不学习；
- $\theta \in \mathbb{R}^{d \times m}$：唯一可学习参数（$m$ 为动作维）；
- 动作 $a_t$ 经 $\tanh$ 或 clip 映射到环境允许范围。

**无 RNN、无深层 MLP**——表达能力有限，但 MuJoCo 步行/奔跑任务中足够，且参数量小、rollout 评估稳定。与 ES 论文（Salimans et al. 2017）用大型神经网络不同，ARS 刻意保持**极简策略类**，把算力花在**更多并行 rollout** 而非更大网络。

---

## 3. 基础随机搜索更新

设当前参数 $\theta$，采样 $n$ 个随机扰动 $\delta_i \sim \mathcal{N}(0, I)$，步长 $\sigma>0$，学习率 $\alpha>0$。对每个 $\theta_i' = \theta + \sigma \delta_i$ 在环境中 rollout，得回报 $R_i = R(\theta_i')$（整条 episode 折扣回报之和，或 MuJoCo 提供的 undiscounted total reward）。

**有限差分梯度估计**（与 ES 同族）：

$$
\nabla_\theta J(\theta) \approx \frac{1}{n\sigma}\sum_{i=1}^{n} (R_i - b)\,\delta_i,
\qquad
\theta \leftarrow \theta + \alpha \cdot \widehat{\nabla_\theta J},
$$

其中 $b$ 为基线（常取 batch 均值 $\bar{R}=\frac{1}{n}\sum_i R_i$），用于降方差。

**ARS 算法骨架**：

```
初始化 θ
repeat 每代:
    采样 δ_1, ..., δ_n ~ N(0, I)
    对每个 i（可含对偶 ±δ）:
        评估 R_i = rollout(θ + σ δ_i)   # 可并行
    用增强技巧处理 {R_i, δ_i}（§4）
    θ ← θ + α · (1/n) Σ (R_i - b) δ_i
until 收敛
```

无 critic、无 replay、无 autograd——只有**环境交互 + 向量加减**。

---

## 4. 四项增强（Augmentations）

论文核心：**ARS = RS + 下面技巧的组合**。

### 4.1 对偶采样（Antithetic sampling）

同时评估 $\theta+\sigma\delta_i$ 与 $\theta-\sigma\delta_i$，用成对差分：

$$
\widehat{g}_i = \frac{R(\theta+\sigma\delta_i) - R(\theta-\sigma\delta_i)}{2\sigma}\,\delta_i.
$$

**效果**：相同随机种子下梯度估计方差约减半；计算量翻倍但易并行，净收益大。

### 4.2 留一基线（Leave-one-out baseline）

第 $i$ 个扰动的基线不用全局均值，而用**去掉 $i$ 后的均值**：

$$
b_i = \frac{1}{n-1}\sum_{j\neq i} R_j.
$$

更新时用 $(R_i - b_i)\delta_i$。比统一 $\bar{R}$ 进一步降方差，且实现仍简单。

### 4.3 精英滤波（Filtering / Top-$k$）

只保留回报**最高**的 $k\%$ 扰动参与梯度聚合，其余丢弃：

$$
\theta \leftarrow \theta + \frac{\alpha}{|\mathcal{E}|}\sum_{i \in \mathcal{E}} (R_i - b)\,\delta_i,
$$

$\mathcal{E}$ 为 top-$k\%$ 索引集。抑制「差扰动」噪声，类似进化算法中的 **selection**，使更新方向更稳。

### 4.4 镜像增强（Mirroring）

四足/双足 locomotion 常具**左右对称**：若状态 $s$ 关于矢状面镜像得 $s^M$，最优动作亦应对称 $a^M$。ARS 在评估 $\theta+\sigma\delta$ 时：

- 用原始 $s_t$ rollout 得 $R$；
- 用镜像状态 $s_t^M$ 执行**镜像动作** rollout 得 $R^M$；
- 取 $\hat{R} = (R + R^M)/2$ 作为该扰动的适应度。

**效果**：等效样本翻倍、利用领域对称性，无需额外环境步数（同一扰动两次评估可并行）。**ARS-v2** = 上述全部 + mirroring；**ARS-v1** = 无 mirroring。

### 4.5 状态预处理（实现细节，非可选）

线性策略对输入尺度敏感，论文使用：

- **观测归一化**：running mean / std 白化 $s_t$；
- **丢弃冗余坐标**（如 MuJoCo 中不参与控制的维度）；
- **动作 clip** 到 $[-1,1]$。

$\phi(s)$ 常即为预处理后的 $s$；这些步骤对 RS 能否收敛**至关重要**——未归一化的 RS 往往完全失败。

---

## 5. 与进化策略（ES）及策略梯度的对比

| | **ARS** | **ES（OpenAI 2017）** | **TRPO / PPO** |
| :--- | :--- | :--- | :--- |
| 策略 | 线性 $\theta^\top s$ | 深度 MLP | 深度 MLP |
| 梯度 | 零阶（扰动） | 零阶（扰动） | 一阶（反向传播） |
| Critic | 无 | 无 | 有（PPO 可选） |
| 并行 | 极易（独立 rollout） | 极易 | 较难（需同步 GPU） |
| 样本效率 | 中（需大量 rollout） | 中 | 通常更高 |
| 实现 | 极短 | 中等 | 复杂 |

ARS 可看作 **ES 的极简专精版**：更小策略类 + 更强领域增强（mirroring、top-$k$、leave-one-out），在 **MuJoCo locomotion** 上用更少代码达到相当或更好性能。

与策略梯度的关系：RS 估计的是**同目标** $J(\theta)$ 的零阶梯度；当策略光滑、维度适中时，有限差分在并行充分时足够。深度非线性策略的高维参数空间里，一阶方法通常更样本高效，但 ARS 提醒：**问题结构 + 预处理** 有时比堆网络更重要。

---

## 6. 实验结论（论文）

在 **MuJoCo** 连续控制（HalfCheetah、Swimmer、Hopper、Walker2d、Ant 等）上：

- **ARS-v2** 在多个环境达到或超过当时 TRPO、ES、DDPG 等报告分数；
- 训练曲线**方差小**、复现性好；
- 单线程慢，但 **CPU 大规模并行** 时 wall-clock 有竞争力（论文强调数千核并行场景）。

**局限**：

- 任务限于**低维观测、平滑动力学**的 locomotion；
- **视觉输入、稀疏奖励、操作任务** 不适用线性策略；
- 样本效率仍低于调优良好的 PPO/SAC（若以环境步数计）；
- mirroring 需**已知对称性**，非通用。

---

## 7. 实现要点

1. **并行**：每个 $\theta+\sigma\delta_i$ 独立 rollout，无共享状态，适合多进程 / 集群；
2. **超参**：扰动尺度 $\sigma$、学习率 $\alpha$、种群大小 $n$、top-$k$ 比例需任务调参；论文给出各环境参考值；
3. **归一化**：观测 running normalization 每代更新，与策略更新交替；
4. **评估协议**：与 Gym 一致，取最后若干代的 max / mean score 报告；
5. 开源参考：论文作者发布 [ars](https://github.com/modestyachts/ars) 代码（数页核心逻辑）。

```python
# 单代更新核心（示意，含对偶 + top-k）
def ars_step(theta, env, n=64, sigma=0.02, alpha=0.02, top_frac=0.5):
    deltas = [np.random.randn(*theta.shape) for _ in range(n)]
    rewards = []
    for d in deltas:
        r_pos = rollout(env, theta + sigma * d)
        r_neg = rollout(env, theta - sigma * d)   # 对偶
        rewards.append((max(r_pos, r_neg), d))      # 或平均
    # top-k 筛选
    k = int(n * top_frac)
    elite = sorted(rewards, key=lambda x: -x[0])[:k]
    baseline = np.mean([r for r, _ in elite])
    grad = sum((r - baseline) * d for r, d in elite) / len(elite)
    return theta + alpha * grad
```

---

## 8. 小结

| 概念 | 内容 |
| :--- | :--- |
| **核心** | 线性策略 + 随机搜索零阶优化 |
| **增强** | 对偶采样、留一基线、top-$k$ 滤波、镜像对称 |
| **优势** | 实现极简、易并行、无反向传播 |
| **适用** | MuJoCo 类连续控制、低维状态 |
| **启示** | 深度 RL 不是唯一路径；结构与预处理同算法一样重要 |

ARS 在 RL 史上的意义是**祛魅**：并非所有控制问题都需要价值网络与反向传播；把随机搜索做到位，配合领域先验（对称、归一化），就能在标准 benchmark 上与复杂方法掰手腕。

---

## 参考文献

- Mania et al., *Simple Random Search Provides a Competitive Approach to Reinforcement Learning*, NeurIPS 2018. [arXiv:1803.07055](https://arxiv.org/abs/1803.07055)
- Salimans et al., *Evolution Strategies as a Scalable Alternative to Reinforcement Learning*, arXiv 2017.
- Williams, *Simple Statistical Gradient-Following Algorithms for Connectionist Reinforcement Learning*, 1992（REINFORCE 基础）.
- Schulman et al., *Trust Region Policy Optimization* (TRPO), ICML 2015（对比基线）.
