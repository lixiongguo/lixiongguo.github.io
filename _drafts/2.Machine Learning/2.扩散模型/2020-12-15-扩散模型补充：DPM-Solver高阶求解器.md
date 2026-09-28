---
layout: post
title: "扩散模型补充：DPM-Solver 高阶求解器"
date: 2023-08-01
categories: [DiffusionSupplement]
mathjax: true
---

> **论文**：Cheng Lu, Yuhao Zhou, Fan Bao, Jianfei Chen, Chongxuan Li, Jun Zhu. [*DPM-Solver: A Fast ODE Solver for Diffusion Probabilistic Model Sampling in Around 10 Steps*](https://arxiv.org/abs/2206.00927). NeurIPS 2022.
>
> 前置：[DDPM]({% post_url 2.Machine Learning/2.扩散模型/2020-09-01-DDPM：去噪扩散概率模型 %})、[DDIM]({% post_url 2.Machine Learning/2.扩散模型/2020-10-01-DDIM：去噪扩散隐式模型 %})、[EDM 统一框架]({% post_url 2.Machine Learning/2.扩散模型/2020-12-01-扩散模型补充：EDM统一框架 %}).

**DPM-Solver** 专为扩散 **概率流 ODE** 设计：利用其 **半线性结构**，线性部分解析积分，非线性部分（$\epsilon_\theta$）用指数加权 Taylor 展开逼近。**DDIM 100 步**的效果，DPM-Solver-2 约 **20 NFE**、DPM-Solver-3 约 **10 NFE** 即可达到。核心结论：**DDIM = DPM-Solver-1**（同一更新式，不同动机）。

![image-20250701195952902](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250701195952902.png)

---

## 1. 前向扩散与噪声调度

扩散模型定义前向过程 $\{x_t\}_{t \in [0,T]}$，对任意 $t \in [0,T]$，条件分布为

$$
q_{0t}(x_t \mid x_0) = \mathcal{N}(x_t \mid \alpha_t x_0,\, \sigma_t^2 I).
\tag{2.1}
$$

$\alpha_t, \sigma_t > 0$ 为可微 **噪声调度**，且信噪比 $\mathrm{SNR}(t) = \alpha_t^2/\sigma_t^2$ 关于 $t$ **严格递减**。以下 SDE 与 (2.1) 具有相同转移分布：

$$
dx_t = f(t) x_t\, dt + g(t)\, dw_t, \quad x_0 \sim q_0(x_0),
\tag{2.2}
$$

其中 $w_t$ 为标准维纳过程，且

$$
f(t) = \frac{d\log\alpha_t}{dt}, \qquad
g^2(t) = \frac{d\sigma_t^2}{dt} - 2\frac{d\log\alpha_t}{dt}\sigma_t^2.
\tag{2.3}
$$

离散 DDPM 中 $\alpha_t = \sqrt{\bar{\alpha}_t}$、$\sigma_t = \sqrt{1-\bar{\alpha}_t}$ 是 (2.1) 的特例。更一般的 $\alpha_t,\sigma_t$ 表述见 [EDM]({% post_url 2.Machine Learning/2.扩散模型/2020-12-01-扩散模型补充：EDM统一框架 %}).

---

## 2. 逆向过程与训练

### 2.1 反向 SDE

前向 SDE (2.2) 的 **reverse-time SDE**（Song et al.）为

$$
dx_t = \bigl[f(t)x_t - g(t)^2 \nabla_x \log q_t(x_t)\bigr] dt + g(t)\, d\bar{w}_t,
\quad x_T \sim q_T(x_T).
\tag{2.4}
$$

### 2.2 噪声预测网络

用 $\epsilon_\theta(x_t, t)$ 逼近 **缩放得分函数**：

$$
\epsilon_\theta(x_t, t) \approx -\sigma_t \nabla_x \log q_t(x_t).
$$

训练目标（与 DDPM 等价，权重记为 $\omega(t)$）：

$$
\mathcal{L}(\theta) = \int_0^T \omega(t)\,
\mathbb{E}_{q_0(x_0)}\,\mathbb{E}_{\epsilon \sim \mathcal{N}(0,I)}
\bigl[\|\epsilon_\theta(x_t, t) - \epsilon\|^2\bigr]\, dt + C,
$$

其中 $x_t = \alpha_t x_0 + \sigma_t \epsilon$，$C$ 与 $\theta$ 无关。

### 2.3 带噪声预测的逆向 SDE

将得分换为 $-\epsilon_\theta/\sigma_t$，从 $x_T \sim \mathcal{N}(0, \tilde{\sigma}^2 I)$ 采样：

$$
dx_t = \left[f(t)x_t + \frac{g(t)^2}{\sigma_t}\epsilon_\theta(x_t, t)\right] dt + g(t)\, d\bar{w}_t.
\tag{2.5}
$$

一阶 SDE 离散化对应 DDPM 祖先采样，通常需数百至上千步 NFE。

---

## 3. 概率流 ODE

### 3.1 从 SDE 到 ODE

SDE 离散化受维纳过程随机性限制，大步长易不收敛。与 (2.4) **边缘分布一致** 的概率流 ODE（PF-ODE）为

$$
\frac{dx_t}{dt} = f(t)x_t - \frac{1}{2}g(t)^2 \nabla_x \log q_t(x_t),
\quad x_T \sim q_T(x_T).
\tag{2.6}
$$

### 3.2 噪声预测形式

代入 $\epsilon_\theta$，定义 **扩散 ODE**：

$$
\frac{dx_t}{dt} = h_\theta(x_t, t)
:= f(t)x_t + \frac{g(t)^2}{2\sigma_t}\epsilon_\theta(x_t, t),
\quad x_T \sim \mathcal{N}(0, \tilde{\sigma}^2 I).
\tag{2.7}
$$

ODE 无随机项，可用更大步长。Song et al. 用通用 RK45 约 **60 NFE** 可达与 1000 步 SDE 相当的质量，但 **~10 步** 仍不足——DPM-Solver 填补这一空白。

---

## 4. 半线性结构与精确解

### 4.1 半线性分解

式 (2.7) 右端 = **线性项** $f(t)x_t$ + **非线性项** $\frac{g(t)^2}{2\sigma_t}\epsilon_\theta(x_t,t)$，属 **半线性 ODE**。黑箱 ODE 求解器把 $h_\theta$ 整体离散，线性项也引入误差。

**常数变易公式**（variation of constants）给出精确解：

$$
x_t = e^{\int_s^t f(\tau)\,d\tau} x_s
+ \int_s^t e^{\int_\tau^t f(r)\,dr}\,
\frac{g^2(\tau)}{2\sigma_\tau}\,
\epsilon_\theta(x_\tau, \tau)\, d\tau.
\tag{3.1}
$$

线性因子 $e^{\int_s^t f(\tau)d\tau} = \alpha_t/\alpha_s$ 可**精确计算**，误差仅来自 $\epsilon_\theta$ 的积分逼近。

### 4.2 log-SNR 变量 $\lambda_t$

定义 **半 log-SNR**：

$$
\lambda_t := \log\frac{\alpha_t}{\sigma_t}.
$$

因 SNR 随 $t$ 递减，$\lambda_t$ 关于 $t$ **严格递减**，存在逆函数 $t_\lambda(\cdot)$。由 (2.3) 可得

$$
g^2(t) = -2\sigma_t^2\,\frac{d\lambda_t}{dt}.
\tag{3.2}
$$

代入 (3.1) 并重写为对 $\lambda$ 的积分：

$$
x_t = \frac{\alpha_t}{\alpha_s} x_s
- \alpha_t \int_s^t \frac{d\lambda_\tau}{d\tau}\,\frac{\sigma_\tau}{\alpha_\tau}\,
\epsilon_\theta(x_\tau, \tau)\, d\tau.
\tag{3.3}
$$

换元 $\hat{x}_\lambda := x_{t_\lambda(\lambda)}$，$\hat{\epsilon}_\theta(\hat{x}_\lambda, \lambda) := \epsilon_\theta(x_{t_\lambda(\lambda)}, t_\lambda(\lambda))$，得

> **命题 3.1（扩散 ODE 精确解）**：给定 $s>0$ 处的 $x_s$，$t \in [0,s]$ 处解为

$$
x_t = \frac{\alpha_t}{\alpha_s} x_s
- \alpha_t \int_{\lambda_s}^{\lambda_t} e^{-\lambda}\,
\hat{\epsilon}_\theta(\hat{x}_\lambda, \lambda)\, d\lambda.
\tag{3.4}
$$

**关键**：逼近 $x_t$ 等价于逼近 $\hat{\epsilon}_\theta$ 在 $[\lambda_s, \lambda_t]$ 上的 **指数加权积分**——线性部分误差为零，属指数积分器（exponential integrator）经典问题。

---

## 5. DPM-Solver 数值方法

采样从 $t_0=T$ 递减到 $t_M=0$。记 $h_i = \lambda_{t_i} - \lambda_{t_{i-1}} > 0$（因 $\lambda$ 随 $t$ 减小而增大）。

### 5.1 单步精确形式与 Taylor 展开

由 (3.4)，从 $\tilde{x}_{t_{i-1}}$ 到 $t_i$ 的精确一步为

$$
x_{t_{i-1} \to t_i} = \frac{\alpha_{t_i}}{\alpha_{t_{i-1}}} \tilde{x}_{t_{i-1}}
- \alpha_{t_i} \int_{\lambda_{t_{i-1}}}^{\lambda_{t_i}} e^{-\lambda}\,
\hat{\epsilon}_\theta(\hat{x}_\lambda, \lambda)\, d\lambda.
\tag{3.5}
$$

在 $\lambda_{t_{i-1}}$ 处对 $\hat{\epsilon}_\theta$ 做 $(k{-}1)$ 阶 Taylor 展开：

$$
\hat{\epsilon}_\theta(\hat{x}_\lambda, \lambda)
= \sum_{n=0}^{k-1} \frac{(\lambda - \lambda_{t_{i-1}})^n}{n!}\,
\hat{\epsilon}_\theta^{(n)}(\hat{x}_{\lambda_{t_{i-1}}}, \lambda_{t_{i-1}})
+ \mathcal{O}\bigl((\lambda - \lambda_{t_{i-1}})^k\bigr).
$$

代入 (3.5)，积分 $\int e^{-\lambda}(\lambda-\lambda_{t_{i-1}})^n/n!\,d\lambda$ **可解析计算**（分部积分），得一般形式

$$
x_{t_{i-1} \to t_i}
= \frac{\alpha_{t_i}}{\alpha_{t_{i-1}}} \tilde{x}_{t_{i-1}}
- \alpha_{t_i} \sum_{n=0}^{k-1}
\hat{\epsilon}_\theta^{(n)}(\hat{x}_{\lambda_{t_{i-1}}}, \lambda_{t_{i-1}})
\int_{\lambda_{t_{i-1}}}^{\lambda_{t_i}} e^{-\lambda}\,
\frac{(\lambda - \lambda_{t_{i-1}})^n}{n!}\, d\lambda
+ \mathcal{O}(h_i^{k+1}).
\tag{3.6}
$$

用有限差分逼近各阶导数即得 **DPM-Solver-$k$**。

### 5.2 DPM-Solver-1

$k=1$ 时 $\int_{\lambda_{t_{i-1}}}^{\lambda_{t_i}} e^{-\lambda}d\lambda = \sigma_{t_i}(e^{h_i}-1)/\alpha_{t_i}$，丢弃 $\mathcal{O}(h_i^2)$：

$$
\tilde{x}_{t_i} = \frac{\alpha_{t_i}}{\alpha_{t_{i-1}}} \tilde{x}_{t_{i-1}}
- \sigma_{t_i}(e^{h_i} - 1)\,\epsilon_\theta(\tilde{x}_{t_{i-1}}, t_{i-1}),
\quad h_i = \lambda_{t_i} - \lambda_{t_{i-1}}.
\tag{3.7}
$$

每步 **1 次** $\epsilon_\theta$ 求值。

### 5.3 DPM-Solver-2

在 $\lambda$ 空间取中点 $s_i = t_\lambda\!\left(\frac{\lambda_{t_{i-1}}+\lambda_{t_i}}{2}\right)$：

1. $\tilde{x}_{t_0} \leftarrow x_T$
2. **for** $i = 1$ **to** $M$：
   - $u_i \leftarrow \dfrac{\alpha_{s_i}}{\alpha_{t_{i-1}}} \tilde{x}_{t_{i-1}}
     - \sigma_{s_i}\bigl(e^{h_i/2}-1\bigr)\,\epsilon_\theta(\tilde{x}_{t_{i-1}}, t_{i-1})$
   - $\tilde{x}_{t_i} \leftarrow \dfrac{\alpha_{t_i}}{\alpha_{t_{i-1}}} \tilde{x}_{t_{i-1}}
     - \sigma_{t_i}(e^{h_i}-1)\,\epsilon_\theta(u_i, s_i)$
3. **return** $\tilde{x}_{t_M}$

每步 **2 次** NFE；CIFAR-10 上 12 NFE 时 FID 约 5.28，同 NFE 的 RK2 约 16.40。

### 5.4 DPM-Solver-3

取 $r_1 = 1/3$，$r_2 = 2/3$，$s_{2i-1} = t_\lambda(\lambda_{t_{i-1}} + r_1 h_i)$，$s_{2i} = t_\lambda(\lambda_{t_{i-1}} + r_2 h_i)$：

$$
u_{2i-1} = \frac{\alpha_{s_{2i-1}}}{\alpha_{t_{i-1}}} \tilde{x}_{t_{i-1}}
- \sigma_{s_{2i-1}}(e^{r_1 h_i}-1)\,\epsilon_\theta(\tilde{x}_{t_{i-1}}, t_{i-1}),
$$

$$
D_{2i-1} = \epsilon_\theta(u_{2i-1}, s_{2i-1}) - \epsilon_\theta(\tilde{x}_{t_{i-1}}, t_{i-1}),
$$

$$
u_{2i} = \frac{\alpha_{s_{2i}}}{\alpha_{t_{i-1}}} \tilde{x}_{t_{i-1}}
- \sigma_{s_{2i}}(e^{r_2 h_i}-1)\,\epsilon_\theta(\tilde{x}_{t_{i-1}}, t_{i-1})
- \frac{\sigma_{s_{2i}} r_2}{r_1}\left(\frac{e^{r_2 h_i}-1}{r_2 h_i}-1\right) D_{2i-1},
$$

$$
D_{2i} = \epsilon_\theta(u_{2i}, s_{2i}) - \epsilon_\theta(\tilde{x}_{t_{i-1}}, t_{i-1}),
$$

$$
\tilde{x}_{t_i} = \frac{\alpha_{t_i}}{\alpha_{t_{i-1}}} \tilde{x}_{t_{i-1}}
- \sigma_{t_i}(e^{h_i}-1)\,\epsilon_\theta(\tilde{x}_{t_{i-1}}, t_{i-1})
- \frac{\sigma_{t_i}}{r_2}\left(\frac{e^{h_i}-1}{h_i}-1\right) D_{2i}.
$$

每步 **3 次** NFE；步数大幅减少，总 NFE 通常更低。

### 5.5 收敛阶（定理 3.2）

在 $\epsilon_\theta$ 满足正则性条件下，DPM-Solver-$k$（$k=1,2,3$）为 **$k$ 阶求解器**：

$$
\tilde{x}_{t_M} - x_0 = \mathcal{O}(h_{\max}^k),
\quad h_{\max} = \max_{1 \le i \le M}(\lambda_{t_i} - \lambda_{t_{i-1}}).
$$

$k \ge 4$ 需更多中间点，本文仅实现至 3 阶。

---

## 6. 步长与离散模型

### 6.1 时间步调度

1. **均匀 $\lambda$ 分割**（推荐）：
   $$\lambda_{t_i} = \lambda_T + \frac{i}{M}(\lambda_0 - \lambda_T), \quad i=0,\ldots,M.$$
   与按 $t$ 均匀分割不同；少步下经验效果更好。

2. **自适应步长**：组合不同阶 DPM-Solver 动态调整 $h_i$（详见论文 Appendix C）。

**NFE 分配**：优先用尽 DPM-Solver-3；余数用 1 步 Solver-1 或 2 补足。$\mathrm{NFE} \le 20$ 用均匀 $\lambda$；更大 NFE 可用自适应。

### 6.2 离散时间 DDPM

离散训练于 $n=0,\ldots,N-1$，模型 $\tilde{\epsilon}_\theta(x_n, n)$。连续化：

$$
\epsilon_\theta(x, t) := \tilde{\epsilon}_\theta\!\left(x,\, \frac{(N-1)t}{T}\right),
$$

即可对离散预训练模型直接套用 DPM-Solver。

---

## 7. DDIM = DPM-Solver-1

DDIM 单步更新（$t_{i-1} \to t_i$）：

$$
\tilde{x}_{t_i} = \frac{\alpha_{t_i}}{\alpha_{t_{i-1}}} \tilde{x}_{t_{i-1}}
- \alpha_{t_i}\left(\frac{\sigma_{t_{i-1}}}{\alpha_{t_{i-1}}} - \frac{\sigma_{t_i}}{\alpha_{t_i}}\right)
\epsilon_\theta(\tilde{x}_{t_{i-1}}, t_{i-1}).
\tag{4.1}
$$

由 $\sigma_t/\alpha_t = e^{-\lambda_t}$ 与 $h_i = \lambda_{t_i} - \lambda_{t_{i-1}}$，(4.1) **恒等于** (3.7)。

| 视角 | 说明 |
| :--- | :--- |
| **DDIM** | 非马尔可夫扩散的确定性采样 |
| **DPM-Solver-1** | 半线性 ODE + 指数积分的 1 阶特例 |
| **为何优于 Euler** | Euler 对整体 $h_\theta$ 离散，**未解析处理线性因子** $\alpha_t/\alpha_s$ |

DPM-Solver 将同一思想 **系统推广到 2/3 阶** 并给出收敛阶证明；与 [DDIM / Flow Matching]({% post_url 2.Machine Learning/2.扩散模型/2020-10-01-DDIM：去噪扩散隐式模型 %}) 的 ODE 视角一致。

### 与 RK 方法的对比

对 (2.7) 直接做显式 Runge–Kutta：同样 NFE 下 FID 明显差于 DPM-Solver（CIFAR-10，12 NFE：RK2 16.40 vs DPM-Solver-2 5.28）。即使在 $\lambda$ 坐标下做 RK，仍不如显式利用半线性结构的 DPM-Solver。

---

## 8. 总结

| 方法 | 阶数 | NFE/步 | 核心 |
| :--- | :--- | :--- | :--- |
| **DDPM 祖先采样** | 1（SDE） | 1 | 随机，需 ~1000 步 |
| **DDIM** | 1（ODE） | 1 | = DPM-Solver-1 |
| **RK45** | 4–5 | 多 | 黑箱 ODE，~60 NFE |
| **DPM-Solver-2** | 2 | 2 | $\lambda$ 中点 + 指数积分 |
| **DPM-Solver-3** | 3 | 3 | 两个中间点，~10 NFE 高质量 |

**训练无关**（training-free）：直接用于已有 $\epsilon_\theta$，无需重训。后续 **DPM-Solver++** 等在此基础上进一步改进高阶组合与引导采样。

---

## 参考文献

- Lu et al., *DPM-Solver*, NeurIPS 2022. [arXiv:2206.00927](https://arxiv.org/abs/2206.00927)
- Song et al., *Score-Based Generative Modeling through SDEs*, ICLR 2021.
- Song et al., *DDIM*, ICLR 2021.
- Hochbruck & Ostermann, *Exponential integrators*, Acta Numerica 2010.
