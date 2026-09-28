---
layout: post
title: "Score Matching：基于得分的生成模型"
date: 2022-12-01
categories: [DiffusionModel]
---
> 本文介绍 Score Matching（得分匹配，Song & Ermon 2019），它是 DDPM 和扩散模型背后的核心数学框架——通过学习数据分布的得分函数（score function）来实现生成。建议先阅读前两篇 DDPM 和 DDIM。

---

## 1. 什么是得分函数

### 1.1 定义

给定数据分布 $p_{\text{data}}(x)$，其**得分函数（score function）**定义为对数概率密度的梯度：

$$
\nabla_x \log p_{\text{data}}(x)
$$

得分函数是一个向量场——它指向概率密度增长最快的方向。直观地，得分函数告诉我们"如何微调 $x$ 以增加它在数据分布下的似然"。

### 1.2 与扩散模型的联系

回顾 DDPM 的逆向 SDE：

$$
dx_t = \left[f(x_t, t) - g(t)^2 \nabla_x \log p_t(x_t)\right] dt + g(t) d\bar{w}_t
$$

其中 $\nabla_x \log p_t(x_t)$ 正是时刻 $t$ 边缘分布的得分函数。**如果知道所有时刻的得分函数，就能从纯噪声逆转扩散过程生成数据。**



## 2. 得分匹配（Score Matching）

### 2.1 基本思想

得分匹配的目标是训练一个神经网络 $s_\theta(x)$ 来逼近真实得分 $\nabla_x \log p_{\text{data}}(x)$。直接使用 $\|s_\theta(x) - \nabla_x \log p_{\text{data}}(x)\|^2$ 作为损失是不可行的，因为我们不知道真实分布 $p_{\text{data}}$。

Hyvärinen（2005）提出了**隐式得分匹配**，通过分部积分消去未知的真实得分：

$$
\mathcal{L}_{\text{SM}}(\theta) = \mathbb{E}_{p_{\text{data}}(x)} \left[ \text{tr}(\nabla_x s_\theta(x)) + \frac{1}{2} \|s_\theta(x)\|^2 \right]
$$

当 $s_\theta(x) = \nabla_x \log p_{\text{data}}(x)$ 时该损失达到最小。

### 2.2 去噪得分匹配（DSM）

隐式得分匹配需要计算 $\nabla_x s_\theta(x)$ 的迹，在高维数据上计算开销大。**去噪得分匹配**（Denoising Score Matching, Vincent 2011）通过引入噪声规避了此问题：

$$
\mathcal{L}_{\text{DSM}}(\theta) = \mathbb{E}_{x \sim p_{\text{data}}, \tilde{x} \sim q_\sigma(\tilde{x}|x)} \left[ \left\| s_\theta(\tilde{x}) - \nabla_{\tilde{x}} \log q_\sigma(\tilde{x}|x) \right\|^2 \right]
$$

当 $q_\sigma(\tilde{x}|x) = \mathcal{N}(\tilde{x}|x, \sigma^2 I)$ 时，有：

$$
\nabla_{\tilde{x}} \log q_\sigma(\tilde{x}|x) = \frac{x - \tilde{x}}{\sigma^2}
$$

这正是 DDPM 中预测噪声 $\epsilon_\theta(x_t, t)$ 等价于预测得分函数的原因。

---



### 3.2 Langevin 动力学采样

训练好得分网络后，可通过**退火 Langevin 动力学**（Anneal Langevin Dynamics）采样。从 $L$ 到 $1$ 逐步降低噪声水平：

1. 初始化 $x_L \sim \mathcal{N}(0, I)$
2. **for** $i = L$ **to** $1$ **do**
3. $\quad$ 步长 $\alpha_i = \epsilon \cdot \sigma_i^2 / \sigma_L^2$
4. $\quad$ **for** $k = 1$ **to** $K$ **do**
5. $\quad\quad z \sim \mathcal{N}(0, I)$
6. $\quad\quad x \leftarrow x + \frac{\alpha_i}{2} s_\theta(x, \sigma_i) + \sqrt{\alpha_i} z$
7. $\quad$ **end for**
8. **end for**
9. **return** $x$





与DDPM关键联系：
$$
\epsilon_\theta(x_t, t) \approx -\sigma_t \cdot \nabla_x \log p_t(x_t) = -\sigma_t \cdot s_\theta(x_t, t)
$$

即 DDPM 的噪声预测网络 $\epsilon_\theta$ 实际上等价于缩放的得分网络。三种框架本质相同，只是参数化形式不同。

