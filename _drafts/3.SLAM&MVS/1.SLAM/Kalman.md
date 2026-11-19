---
layout: post
title: "维纳滤波与卡尔曼滤波"
categories: [TechSharing]
mathjax: true
---

> 路线：**维纳滤波**（平稳信号的最优线性估计，**频域 / 批处理**）→ **卡尔曼滤波**（动态系统的最优递推估计，**时域 / 递推**）→ **EKF / UKF / 粒子滤波**（处理非线性）。卡尔曼滤波是 SLAM、雷达跟踪、控制系统的事实标准；维纳滤波则是它的"频域前身"，理解维纳有助于看透卡尔曼"最优性"的真正含义。SLAM 中的相关应用见 [ORB-SLAM2](ORB_SLAM2.md) 与 [PnP算法](PnP算法.md)。

---

## 任务与设定

**最优估计问题**：给定一组**含噪观测**，估计一个**隐藏的真值**。两类典型场景：

| 场景 | 隐藏量 | 观测 |
|:---|:---|:---|
| 信号去噪 | 真实信号 \(x(t)\) | 加噪信号 \(y(t) = x(t) + v(t)\) |
| 目标跟踪 | 系统状态 \(\mathbf{x}_k\)（位置/速度/...） | 不完全 / 含噪测量 \(\mathbf{z}_k\)（GPS/雷达/...） |
| SLAM 位姿估计 | 相机位姿 \(\mathbf{T}_k \in \mathrm{SE}(3)\) | 图像特征点 / IMU 读数 |

如果"系统"是**平稳**的（统计特性不随时间变化），可用频域方法（**维纳滤波**）；如果系统是**动态**的（有显式状态转移方程），可使用时域递推（**卡尔曼滤波**）。

---

## 一、维纳滤波

### 1.1 问题定义

**Wiener Filter (1949)** 是 Norbert Wiener 在研究防空火力控制时提出的**线性最小均方误差（LMMSE）** 滤波器。**问题设定**：

- 真实信号 \(s(t)\) 与加性噪声 \(n(t)\)**联合平稳**（WSS），二阶统计量（自相关/互相关）已知；
- 观测 \(x(t) = s(t) + n(t)\)；
- 求一个**线性时不变（LTI）滤波器** \(h(t)\)，使输出

\[
\hat{s}(t) = (h * x)(t) = \int_{-\infty}^{\infty} h(\tau)\, x(t-\tau)\, d\tau
\]

**最小化**均方误差：

\[
\mathbb{E}\left[\,|e(t)|^2\,\right] = \mathbb{E}\left[\,|\hat{s}(t) - s(t)|^2\,\right]
\]

### 1.2 维纳-霍夫方程

将 LMMSE 条件 \(\mathbb{E}[e(t)\,x(\tau)] = 0\)（正交性原理）展开：

\[
\mathbb{E}\big[(\hat{s}(t) - s(t))\,x(\tau)\big] = 0
\]

代入 \(\hat{s}(t) = \int h(\alpha) x(t-\alpha) d\alpha\)，利用平稳性 \(\mathbb{E}[x(t-\alpha) x(\tau)] = R_{xx}(\tau - t + \alpha)\)：

\[
\boxed{\int_{-\infty}^{\infty} h(\alpha)\, R_{xx}(\tau - t + \alpha)\, d\alpha = R_{sx}(\tau - t)}
\]

即 **Wiener-Hopf 方程**。这是一个对 \(h\) 的**卷积型**线性方程，难以直接解。

### 1.3 频域解：对功率谱做"除法"

对两边取傅里叶变换（卷积变乘积），立刻得到**频域解**：

\[
\boxed{
H(\omega) = \frac{S_{sx}(\omega)}{S_{xx}(\omega)} = \frac{S_{ss}(\omega)}{S_{ss}(\omega) + S_{nn}(\omega)}
}
\]

其中：

| 符号 | 含义 |
|:---|:---|
| \(S_{ss}(\omega)\) | 真实信号的**功率谱密度**（PSD） |
| \(S_{nn}(\omega)\) | 噪声的功率谱密度 |
| \(S_{sx}(\omega)\) | 信号与观测的互功率谱 |
| \(H(\omega)\) | 维纳滤波器的**频率响应** |

**直观理解**：
- 在**信噪比高**的频段（\(S_{ss} \gg S_{nn}\)）→ \(H(\omega) \approx 1\)，**保留信号**；
- 在**信噪比低**的频段（\(S_{ss} \ll S_{nn}\)）→ \(H(\omega) \approx 0\)，**抑制噪声**。

这就是维纳滤波的本质：**按频段"动态加权"，信噪比高的频段权重高、噪比低的频段权重低**。

#### 维纳滤波频域响应示意

以一个真实信号频谱集中在**低频**、噪声为**白噪**（功率谱平坦）的典型情形为例：

```
   |H(ω)|
    1.0 ┤      ●──────────●              ← H(ω) ≈ 1（信号主导）
        │    ╱             ╲
    0.8 ┤   ╱                ╲
        │  ╱                   ╲
    0.6 ┤ ╱                      ╲
        │╱                         ╲
    0.4 ┤                            ╲
        │                              ╲
    0.2 ┤                                ●────────●     ← H(ω) ≈ 0（噪声主导）
        │                                             
    0.0 ┼──────┬──────┬──────┬──────┬──────┬──────→ ω
        0     ω₁     2ω₁    3ω₁    4ω₁    5ω₁
              ↑
          截止频率 ω_c
        （Sss(ω_c) ≈ Snn(ω_c)）
```

**关键观察**：
- 维纳滤波相当于一个**自适应低通滤波器**，截止频率 \(\omega_c\) 由**信噪比 = 1** 的频点自动决定；
- **信号频段**（低频）几乎完全保留（\(H \approx 1\)）；
- **噪声频段**（高频）几乎完全抑制（\(H \approx 0\)）；
- **过渡带**（\(\omega_c\) 附近）平滑衰减，避免振铃。

如果信号是宽带（如语音），频谱复杂，\(H(\omega)\) 也会出现对应的"凸凹"，但原则不变：**哪里信噪比高就放行，哪里信噪比低就压扁**。

### 1.4 维纳-霍夫方程的"病态" 与 FIR 近似

对**非平稳**或**因果**（必须 \(h(t) = 0,\ t<0\)）的情形，频域解不再干净。**FIR 维纳滤波**把问题离散化为线性方程组：

设滤波器长度为 \(L\)，\(\mathbf{h} = (h_0, h_1, \ldots, h_{L-1})^\top\)，则

\[
\mathbf{R}_{xx}\, \mathbf{h} = \mathbf{r}_{sx}
\]

其中 \(\mathbf{R}_{xx}\) 是 \(L \times L\) **Toeplitz** 自相关矩阵，\(\mathbf{r}_{sx}\) 是互相关向量。**Levinson-Durbin 递推**可在 \(O(L^2)\) 内求解（比通用 \(O(L^3)\) 快很多），且对**因果**情形给出**预测误差滤波器**（whitening filter）。

### 1.5 维纳滤波的局限

| 局限 | 后果 |
|:---|:---|
| 必须**平稳** | 时变系统（如目标跟踪）失效 |
| 必须知道**二阶统计量** | 需要预先估计 \(R_{ss}, R_{nn}\)，实际中常不准确 |
| **批处理**（要全段数据） | 难以做实时估计，存储与计算都是 \(O(N L)\) |
| **线性**约束 | 真实系统常含非线性，最优非线性滤波器须另寻他法 |

正是这 4 条局限，催生了 **卡尔曼滤波**：把"频域、平稳、批处理"换成"时域、动态、递推"。

---

## 二、卡尔曼滤波

### 2.1 状态空间模型

卡尔曼滤波 (Kalman, 1960) 解决**离散时间线性动态系统**的最优递推估计问题。系统写为：

**过程模型**（状态转移）：

\[
\mathbf{x}_k = \mathbf{F}_k\, \mathbf{x}_{k-1} + \mathbf{B}_k\, \mathbf{u}_k + \mathbf{w}_k, \quad \mathbf{w}_k \sim \mathcal{N}(\mathbf{0}, \mathbf{Q}_k)
\]

**观测模型**：

\[
\mathbf{z}_k = \mathbf{H}_k\, \mathbf{x}_k + \mathbf{v}_k, \quad \mathbf{v}_k \sim \mathcal{N}(\mathbf{0}, \mathbf{R}_k)
\]

| 符号 | 含义 | 维度 |
|:---|:---|:---:|
| \(\mathbf{x}_k\) | 状态向量（待估计） | \(n \times 1\) |
| \(\mathbf{F}_k\) | 状态转移矩阵 | \(n \times n\) |
| \(\mathbf{B}_k, \mathbf{u}_k\) | 控制输入矩阵与向量 | — |
| \(\mathbf{w}_k\) | 过程噪声 | \(\mathbf{Q}_k\) 是其协方差 |
| \(\mathbf{z}_k\) | 观测向量 | \(m \times 1\) |
| \(\mathbf{H}_k\) | 观测矩阵 | \(m \times n\) |
| \(\mathbf{v}_k\) | 观测噪声 | \(\mathbf{R}_k\) 是其协方差 |

**两条关键假设**：
1. 噪声 \(\mathbf{w}_k, \mathbf{v}_k\) 都是**零均值高斯**且互不相关；
2. 噪声是**白噪声**（不同步不相关）：\(\mathbb{E}[\mathbf{w}_k \mathbf{w}_j^\top] = \mathbf{Q}_k \delta_{kj}\)，对 \(\mathbf{v}_k\) 同。

**在 SLAM / 跟踪中的常见映射**：
- \(\mathbf{x}_k = [x, y, z, v_x, v_y, v_z, \ldots]^\top\)（位置 + 速度）
- \(\mathbf{F}_k\)：常速度模型 / 常加速度模型
- \(\mathbf{z}_k\)：GPS、雷达、视觉里程计、IMU

### 2.2 核心思想

> **递推贝叶斯估计**：每一时刻只关心"上一刻的后验 \(\to\) 这一刻的后验"，把全段数据问题化为**两步递推**（预测 + 更新）。  
> **在线性高斯假设下**：后验分布仍为高斯，可以用**均值 + 协方差**两个量完整刻画 → 解析解存在。

具体地，卡尔曼滤波等价于在**线性高斯**模型下做**精确贝叶斯滤波**。

### 2.3 五个递推公式

卡尔曼滤波每一步包含**预测（Predict）** 和**更新（Update）** 两步，共 5 个公式：

#### 预测（时间更新）

\[
\boxed{
\begin{aligned}
\hat{\mathbf{x}}_{k|k-1} &= \mathbf{F}_k\, \hat{\mathbf{x}}_{k-1|k-1} + \mathbf{B}_k\, \mathbf{u}_k \\
\mathbf{P}_{k|k-1} &= \mathbf{F}_k\, \mathbf{P}_{k-1|k-1}\, \mathbf{F}_k^\top + \mathbf{Q}_k
\end{aligned}
}
\]

> **物理含义**：用上一刻状态按动力学外推到这一刻，同时把过程噪声 \(\mathbf{Q}_k\) 累加进协方差 → **不确定性增大**。

#### 更新（观测更新）

\[
\boxed{
\begin{aligned}
\tilde{\mathbf{y}}_k &= \mathbf{z}_k - \mathbf{H}_k\, \hat{\mathbf{x}}_{k|k-1} \quad &\text{(创新 residual)} \\
\mathbf{S}_k &= \mathbf{H}_k\, \mathbf{P}_{k|k-1}\, \mathbf{H}_k^\top + \mathbf{R}_k \quad &\text{(创新协方差)} \\
\mathbf{K}_k &= \mathbf{P}_{k|k-1}\, \mathbf{H}_k^\top\, \mathbf{S}_k^{-1} \quad &\text{(卡尔曼增益)} \\
\hat{\mathbf{x}}_{k|k} &= \hat{\mathbf{x}}_{k|k-1} + \mathbf{K}_k\, \tilde{\mathbf{y}}_k \\
\mathbf{P}_{k|k} &= (\mathbf{I} - \mathbf{K}_k\, \mathbf{H}_k)\, \mathbf{P}_{k|k-1}
\end{aligned}
}
\]

> **物理含义**：用观测修正预测，修正幅度由**卡尔曼增益** \(\mathbf{K}_k\) 决定。  
> 预测 + 更新 后，**不确定性 \(\mathbf{P}_{k|k}\) 减小**（观测提供了信息）。

### 2.4 直觉图解

```text
            ┌───────────────────────────────┐
            │  上一刻后验                    │
            │  x̂_{k-1|k-1},  P_{k-1|k-1}    │
            └───────────────┬───────────────┘
                            ↓  预测 (Predict)
            ┌───────────────────────────────┐
            │  先验（外推）                  │
            │  x̂_{k|k-1},  P_{k|k-1}        │
            │   ↑ 不确定性增大（+ Q_k）      │
            └───────────────┬───────────────┘
                            ↓  观测到达 z_k
            ┌───────────────────────────────┐
            │  创新: ỹ_k = z_k - H x̂_{k|k-1}│
            │  增益: K_k = P_{k|k-1} H^T S^-1│
            │   ↑  K_k 大 → 信任观测多       │
            │   ↑  K_k 小 → 信任预测多       │
            └───────────────┬───────────────┘
                            ↓  更新 (Update)
            ┌───────────────────────────────┐
            │  本刻后验                      │
            │  x̂_{k|k} = x̂_{k|k-1} + K ỹ_k │
            │  P_{k|k} = (I - K H) P_{k|k-1} │
            │   ↑ 不确定性减小               │
            └───────────────────────────────┘
```

#### 协方差 \(\mathbf{P}_k\) 的"呼吸"过程

把多步连起来看，\(\mathbf{P}_k\) 呈现"先涨后落"的**呼吸模式**：

```
   P  (协方差 / 不确定性)
    ↑                    
    │      ╱╲          ╱╲          ╱╲          ╱╲
    │     ╱  ╲        ╱  ╲        ╱  ╲        ╱  ╲
    │    ╱    ╲      ╱    ╲      ╱    ╲      ╱    ╲
    │   ╱      ╲    ╱      ╲    ╱      ╲    ╱      ╲
    │  ╱        ╲  ╱        ╲  ╱        ╲  ╱        ╲
    │ ╱          ╲╱          ╲╱          ╲╱          ╲
    └─────────────────────────────────────────────────→  k
   k-1  k    k-1  k    k-1  k    k-1  k    k-1  k
   
       ↑涨↑    ↓落↓   ↑涨↑    ↓落↓   ↑涨↑    ↓落↓
      预测     更新    预测     更新    预测     更新
     (+Q_k)   (观测)  (+Q_k)   (观测)  (+Q_k)   (观测)
```

- **预测步**：\(\mathbf{P}_{k|k-1} = \mathbf{F} \mathbf{P}_{k-1|k-1} \mathbf{F}^\top + \mathbf{Q}_k\) → 协方差**增大**（过程噪声注入 + 转移矩阵放大）；
- **更新步**：\(\mathbf{P}_{k|k} = (\mathbf{I} - \mathbf{K}_k \mathbf{H}_k) \mathbf{P}_{k|k-1}\) → 协方差**减小**（观测提供了信息）；
- **稳态**：经过若干步后，涨与落达到平衡，\(\mathbf{P}_k \to \mathbf{P}_\infty\) 为常数 → 这就是 §3.2 提到的**稳态卡尔曼**，与维纳滤波等价。

> **直觉**：\(\mathbf{P}_k\) 像一个"皮球"，预测时充气变大、更新时放气变小；如果系统完全可观，最终会稳定在某个"半径"——这个半径取决于 \(\mathbf{Q}/\mathbf{R}\) 的比值。\(\mathbf{Q}\) 越大，皮球越大；\(\mathbf{R}\) 越大，皮球越小。

### 2.5 卡尔曼增益的物理含义

\[
\mathbf{K}_k = \mathbf{P}_{k|k-1}\, \mathbf{H}_k^\top\, (\mathbf{H}_k\, \mathbf{P}_{k|k-1}\, \mathbf{H}_k^\top + \mathbf{R}_k)^{-1}
\]

**两个极限**：

| 情形 | 增益 \(\mathbf{K}_k\) | 含义 |
|:---|:---|:---|
| \(\mathbf{R}_k \to 0\)（观测无噪声） | \(\mathbf{K}_k \to \mathbf{H}_k^{-1}\) | 完全信任观测，\(\hat{\mathbf{x}} \to \mathbf{H}^{-1} \mathbf{z}\) |
| \(\mathbf{P}_{k|k-1} \to 0\)（预测极准） | \(\mathbf{K}_k \to 0\) | 完全信任预测，忽略观测 |

直觉：**卡尔曼增益是"预测精度 vs 观测精度"的加权**。

### 2.6 推导要点：为什么这 5 个公式是"最优"的？

可从两条路径推导（详见 [附录 B](#附录-b卡尔曼滤波的贝叶斯推导)）：

1. **贝叶斯滤波路径**：在线性高斯假设下，预测步用全概率公式、更新步用贝叶斯公式；由于高斯分布的共轭性，后验仍为高斯，且均值/协方差的更新恰好给出上述 5 式。
2. **正交投影路径**：把 \(\hat{\mathbf{x}}_{k|k}\) 视为 \(\mathbf{x}_k\) 在由 \(\{z_1,\ldots,z_k\}\) 张成的线性子空间上的**正交投影**；投影定理给出 \(\mathbf{K}_k\) 的最优解，结果与上面一致。

**两条路径殊途同归**，因为在线性高斯情形下"贝叶斯最优"="LMMSE 最优"。

### 2.7 \(\mathbf{Q}, \mathbf{R}\) 的物理意义与调参

| 矩阵 | 物理含义 | 调参倾向 |
|:---|:---|:---|
| \(\mathbf{Q}_k\) | 过程噪声协方差：模型"不知道"或"不确定"的部分 | \(\mathbf{Q}\) 大 → 信任观测多，状态更"跟"测量；适合运动模型不准确时 |
| \(\mathbf{R}_k\) | 观测噪声协方差：传感器精度 | \(\mathbf{R}\) 大 → 信任预测多，状态更"平滑"；适合传感器噪声大时 |

**经验调参**：
- 增大 \(\mathbf{Q}\) → 滤波响应更快但噪声大；
- 增大 \(\mathbf{R}\) → 滤波输出更平滑但滞后；
- 工程上常通过 Allan 方差分析 IMU 的 \(\mathbf{Q}\)，通过标定/手册得到 \(\mathbf{R}\)，再小范围微调。

---

## 三、维纳 vs 卡尔曼

### 3.1 全面对比

| 维度 | 维纳滤波 | 卡尔曼滤波 |
|:---|:---|:---|
| **目标信号** | 平稳随机过程 | 动态系统状态 |
| **系统模型** | 隐式（只知二阶统计量） | 显式（\(\mathbf{F}, \mathbf{H}, \mathbf{Q}, \mathbf{R}\)） |
| **处理域** | **频域**（功率谱） | **时域**（状态空间） |
| **处理方式** | **批处理**（要全段数据） | **递推**（只需上一刻状态 + 本刻观测） |
| **最优准则** | LMMSE（LTI 滤波器） | LMMSE（线性高斯 = 精确贝叶斯） |
| **实时性** | 不支持 | 支持 |
| **非平稳** | 不支持 | 支持（\(\mathbf{F}_k, \mathbf{H}_k\) 可时变） |
| **非线性** | 不支持 | **不支持**（要 EKF/UKF/PF） |
| **计算复杂度（每步）** | \(O(L^2)\)，且只算一次 | \(O(n^2 + m^2 + n m)\)，每步一次 |
| **典型应用** | 信号去噪、通信均衡 | 雷达跟踪、GPS/INS 组合、SLAM、控制系统 |

### 3.2 关系：维纳是卡尔曼的"平稳 + 频域"特例

如果卡尔曼的状态空间模型是**线性时不变**且系统**平稳**，则**稳态卡尔曼滤波**（\(k \to \infty\) 后 \(\mathbf{P}_k \to \mathbf{P}_\infty\) 为常数）所得到的等效 LTI 滤波器，其频率响应**正好等于维纳滤波**。即：

> **维纳滤波 = 稳态卡尔曼滤波的频域表示**

这一关系意味着：
- 理解卡尔曼后，可以"反过来"用状态空间观点看维纳（把维纳视为卡尔曼的"无限时间 + 平稳"极限）；
- 在工程上，能用卡尔曼递推实现的，几乎都会用卡尔曼（计算量可控、实时性更好），维纳滤波多用于**离线信号处理**（如音频降噪、通信均衡器）。

#### 维纳-卡尔曼的关系示意

```
            ┌─────────────────────────────────────────────┐
            │   维纳滤波 (Wiener, 1949)                    │
            │   ─ 平稳信号 (WSS)                           │
            │   ─ 频域 / 批处理                            │
            │   ─ 二阶统计量 R_xx, R_sx                    │
            │   ─ LMMSE 等价于 LTI 滤波器                  │
            └───────────────────┬─────────────────────────┘
                                │
                                │ 加 "状态空间" + "递推"
                                │ (Wiener → Kalman)
                                ↓
            ┌─────────────────────────────────────────────┐
            │   卡尔曼滤波 (Kalman, 1960)                  │
            │   ─ 动态系统 (F, H, Q, R)                    │
            │   ─ 时域 / 递推                              │
            │   ─ 线性高斯下 = 精确贝叶斯                   │
            └───────────────────┬─────────────────────────┘
                                │
                                │ 加 "非线性"
                                │ (Kalman → EKF / UKF / PF)
                                ↓
            ┌─────────────────────────────────────────────┐
            │   非线性扩展 (EKF/UKF/PF)                    │
            │   ─ 局部线性化 / 无迹变换 / 随机采样         │
            │   ─ 处理 SLAM / VIO / 非线性跟踪             │
            └─────────────────────────────────────────────┘
```

> **三阶段递进关系**：维纳是"频域 / 平稳 / 批处理"的最优估计 → 卡尔曼把它搬到"时域 / 动态 / 递推" → 非线性扩展处理"任意系统"。每一阶段都**严格包含**前一阶段为特例：  
> - 维纳 ⊂ 稳态卡尔曼 ⊂ 一般卡尔曼 ⊂ EKF ⊂ 非线性滤波  
> - 反过来：每一阶段都为前一阶段**增加了更多能力**（时变性 / 非线性 / 任意分布）。

### 3.3 两种建模哲学：数据驱动 vs 模型驱动

一个常见的类比是：**维纳 = 黑盒**（只给输入输出、不解释内部）、**卡尔曼 = 白盒**（显式状态、显式递推）。这个类比**有道理但不完整**——更准确的描述是两者代表了**两种不同的建模哲学**。

#### 表层类比（合理）

| 维度 | 维纳 | 卡尔曼 |
|:---|:---|:---|
| 需要 | 二阶统计量 \(S_{ss}, S_{nn}\) | 系统模型 \(\mathbf{F}, \mathbf{H}, \mathbf{Q}, \mathbf{R}\) |
| 状态可见 | 不可见 | 实时可见（位置/速度/...） |
| 每步可解释 | 频域加权一句话 | 预测+更新，物理动作清楚 |
| 不确定性 | 没有显式概念 | 协方差 \(\mathbf{P}_k\) 实时可见 |

#### 三个陷阱（让类比复杂化）

1. **维纳是"白盒的频域封装"**。稳态卡尔曼的频率响应**严格等于**维纳滤波——维纳看似黑盒，实则是卡尔曼"无限时间 + 平稳"轨迹的预编译。
2. **卡尔曼在"模型错"时也是黑盒**。 \(\mathbf{F}, \mathbf{H}\) 错了，KF 会**自信地给出错误答案**——模型本身就是不可见变量。
3. **两者经常混用**。自适应 KF 用观测数据实时估计 \(\mathbf{Q}, \mathbf{R}\)（吸收维纳的统计思想）；维纳-卡尔曼混合先用 KF 跑稳态再封成 LTI 滤波器。

#### 更准确的对比：信任边界

| | 维纳 | 卡尔曼 |
|:---|:---|:---|
| **哲学** | **数据驱动**（统计） | **模型驱动**（机理） |
| **信什么** | **统计规律**（平稳、功率谱） | **物理规律**（状态转移方程） |
| **何时崩** | 信号不平稳 / 谱估计不准 | 模型不准确 / \(\mathbf{Q}, \mathbf{R}\) 不当 |
| **可解释性** | 频域清楚（哪个频段放行/压扁） | 时域清楚（每步在做什么） |

> **一句话**：卡尔曼信任"模型"（可能错），维纳信任"统计"（更难错但更难算）。

这个对立其实是**机器学习领域经典张力的最简版**——**可解释的概率模型**（白盒/小数据）vs **大规模神经网络**（黑盒/大数据）。本节给出的"信任模型 vs 信任数据"框架，在 §4 扩展（非线性用线性化近似模型）和 §6 调参（\(\mathbf{Q}, \mathbf{R}\) 用 Allan 方差经验定）里都会反复出现。

---

## 四、非线性扩展

### 4.1 扩展卡尔曼滤波（EKF）

**问题**：实际系统常含非线性：

\[
\mathbf{x}_k = f(\mathbf{x}_{k-1}, \mathbf{u}_k) + \mathbf{w}_k, \quad \mathbf{z}_k = h(\mathbf{x}_k) + \mathbf{v}_k
\]

**EKF 思路**：在 \(\hat{\mathbf{x}}_{k-1|k-1}\) 处对 \(f, h\) 做**一阶泰勒展开**（线性化），再用标准卡尔曼公式：

\[
\mathbf{F}_k = \left.\frac{\partial f}{\partial \mathbf{x}}\right|_{\hat{\mathbf{x}}_{k-1|k-1}}, \quad
\mathbf{H}_k = \left.\frac{\partial h}{\partial \mathbf{x}}\right|_{\hat{\mathbf{x}}_{k|k-1}}
\]

**优点**：实现简单、计算量小、广泛使用。  
**缺点**：
- 强非线性时**线性化误差大**，可能导致滤波发散；
- 需要解析求 Jacobian，复杂模型推导繁琐；
- 对高度非线性的旋转（\(\mathrm{SO}(3)\) 上的乘法）不友好 → 催生了**IEKF**（迭代 EKF）、**误差状态卡尔曼**（ESKF）。

**SLAM 中的应用**：早期 MonoSLAM 就是 EKF-based，把整张地图（上千路标）的状态放进一个超大协方差矩阵里做递推 → 后来被基于 BA 的方法取代（计算量与精度均占优）。

### 4.2 无迹卡尔曼滤波（UKF）

**思路**：不线性化函数，而用**确定性采样**（Unscented Transform）近似高斯分布的传播：

- 取一组**sigma 点**（围绕均值的 2n+1 个点，加权对称）；
- 把每个 sigma 点**通过非线性函数** \(f, h\) 传播；
- 用传播后的点重新估计均值和协方差。

**优点**：对中等非线性精度高于 EKF（精度到 2 阶泰勒，无需求 Jacobian）。  
**缺点**：
- 仍要求噪声高斯；
- 对**多模态分布**无能为力（高斯只能表达单峰）；
- 在 SLAM 大状态量下，计算量与 EKF 同阶，但实现稍复杂。

### 4.3 粒子滤波（Particle Filter, PF）

**思路**：放弃高斯假设，用一组**带权粒子**\(\{(\mathbf{x}^{(i)}, w^{(i)})\}_{i=1}^N\) 表达后验分布：

- **预测**：每个粒子按过程模型 \(f\) 随机采样；
- **更新**：根据观测似然 \(p(\mathbf{z}_k | \mathbf{x}_k^{(i)})\) 更新粒子权重；
- **重采样**：丢弃低权粒子、复制高权粒子，避免权重退化。

**优点**：可表达**任意分布**（多模态、强非线性）。  
**缺点**：
- 粒子数 \(N\) 随状态维数**指数增长** → 维度灾难；
- 难以做 SLAM 这类高维状态估计（V-SLAM 状态可达十几维）；
- 重采样带来**粒子贫化**问题。

**SLAM 中的应用**：FastSLAM 把 SLAM 分解为"轨迹 + 路标"，对每条候选轨迹用粒子滤波（PF 处理轨迹，路标用 EKF 处理），是 PF 在 SLAM 中的代表。

### 4.4 非线性扩展对比

| 方法 | 分布假设 | 处理方式 | 计算量 | 精度 | 适用 |
|:---|:---|:---|:---|:---|:---|
| **EKF** | 单峰高斯 | 一阶线性化 | \(O(n^2)\) | 中 | 弱非线性、Jacobian 易求 |
| **UKF** | 单峰高斯 | 无迹变换 | \(O(n^2)\) | 中-高 | 中等非线性、避 Jacobian |
| **PF** | 任意 | 随机采样 | \(O(N)\)，\(N \sim 10^3\)–\(10^6\) | 高（足够粒子） | 低维、强非线性、多模态 |
| **IEKF** | 单峰高斯 | 多次线性化 | \(O(k n^2)\) | 较高 | 同 EKF，但精度更好 |
| **ESKF** | 单峰高斯 | 误差状态线性化 | \(O(n^2)\) | 较高 | \(\mathrm{SO}(3)\) 等流形状态 |

---

## 五、SLAM 中的应用

### 5.1 卡尔曼 vs 批量优化（BA）

视觉 SLAM 后端的两大类方法：

| 维度 | 卡尔曼 / EKF 滤波 | BA（图优化） |
|:---|:---|:---|
| 估计方式 | **递推**：当前状态 = 上刻 + 本刻观测 | **批量**：用所有历史观测全局最优 |
| 数学形式 | 隐式利用历史（通过协方差传递） | 显式构建所有约束、求解稀疏线性方程 |
| 精度 | 次优（线性化 + 协方差近似） | **最优**（给定初值时） |
| 计算量 | \(O(n^2)\) / 步 | \(O(1)\) / 步（增量），但全局回环要重排 |
| 内存 | \(O(n^2)\)，状态大时压力大 | 关键帧数小时可接受 |
| 闭环 | 难以加入全局约束 | 自然支持（Pose Graph 优化） |
| 代表 | MonoSLAM（Davison 2007） | ORB-SLAM2、VINS-Mono、DSO |

> 现代视觉 SLAM **几乎都转向 BA 后端**，因为相机数据率高（10-30 Hz），关键帧数小（10-100 帧在线），批量优化的精度优势压倒滤波的递推简洁性。但 **EKF/ESKF 仍是 IMU 预积分 / 视觉-惯性融合（VIO）** 的标配——IMU 频率高（200-1000 Hz），递推是必要的。

### 5.2 实际系统举例

| 系统 | 滤波部分 | 优化部分 |
|:---|:---|:---|
| **ORB-SLAM2** | — | 纯 BA（motion-only + local BA + full BA） |
| **OKVIS** | EKF 短期预测 | Keyframe BA |
| **VINS-Mono** | EKF 预积分（视觉-IMU 紧耦合） | Sliding-window BA + Pose Graph 回环 |
| **MSCKF** | EKF on sliding window of camera states | 滤波框架内做多视图几何 |
| **ROVIO** | **IEKF** on error state | — |
| **S-MSCKF** (SStereo) | EKF with FEJ | Sliding window |

**VIO 中的角色**：
- IMU 预积分提供**短时高频**的状态递推（200-1000 Hz）；
- 视觉特征点 / SLAM 提供**低频高精**的位姿修正（10-30 Hz）；
- 二者通过 EKF 或图优化**紧耦合**，把 IMU 的运动约束与视觉的几何约束融合。

### 5.3 调参实例：VIO 中的 Q/R

以 VINS-Mono 为例，IMU 的过程噪声 \(\mathbf{Q}\) 由 **Allan 方差** 实验标定：
- 角度随机游走（ARW）→ 陀螺仪白噪声；
- 速度随机游走（VRW）→ 加速度计白噪声；
- 偏置不稳定性（Bias Instability）→ 偏置随机游走的强度。

观测噪声 \(\mathbf{R}\)（视觉重投影噪声）通常按**像素误差**设置：
- 高分辨率相机（>1MP）：\(\sigma \approx 1.0\)–\(1.5\) 像素；
- 低分辨率 / 鱼眼：\(\sigma \approx 1.5\)–\(2.0\) 像素；
- 或者根据特征点的**尺度 / 光度**自适应调整。

---

## 六、工程实现要点

### 6.1 数值稳定性

| 问题 | 后果 | 应对 |
|:---|:---|:---|
| \(\mathbf{P}\) 失去对称正定 | 数值异常，滤波发散 | **Joseph 形式**：\(\mathbf{P}_{k|k} = (\mathbf{I} - \mathbf{K} \mathbf{H}) \mathbf{P}_{k|k-1} (\mathbf{I} - \mathbf{K} \mathbf{H})^\top + \mathbf{K} \mathbf{R} \mathbf{K}^\top\) |
| \(\mathbf{S}\) 求逆病态 | 卡尔曼增益数值爆炸 | **QR 分解** / **Cholesky** 分解 / SVD 替代直接求逆 |
| 协方差矩阵非对称 | 累积误差 | 强制对称化：\(\mathbf{P} = \frac{1}{2}(\mathbf{P} + \mathbf{P}^\top)\) |
| 大状态量（如全 SLAM 地图） | \(O(n^3)\) 不可承受 | **稀疏化** / **Schur complement** / 改用 BA |

### 6.2 实现库

| 库 | 语言 | 特色 |
|:---|:---|:---|
| **Eigen** | C++ | 线性代数基础库，KF 自己写 |
| **OpenCV** `KalmanFilter` | C++/Python | 标准 KF 模板类，例子丰富 |
| **filterpy** | Python | 教学库，KF/EKF/UKF/PF 一应俱全 |
| **robot_localization** (ROS) | C++ | EKF/UKF 节点封装，多传感器融合 |
| **GTSAM** | C++ | iSAM2 增量式 BA + IMU 因子 |
| **Ceres / g2o** | C++ | 非线性优化（BA 风格） |
| **Madgwick / Mahony** | C++ | 轻量级 AHRS 滤波（IMU 姿态） |

### 6.3 常见失败模式

| 现象 | 可能原因 | 解决 |
|:---|:---|:---|
| 滤波发散 | \(\mathbf{Q}\) 设太小、\(\mathbf{R}\) 设太大、模型不匹配 | 增大 \(\mathbf{Q}\) 或加噪声自适应（自适应 KF） |
| 输出滞后 | \(\mathbf{R}\) 设过大 / 状态量多步没被观测 | 减小 \(\mathbf{R}\) / 检查观测模型 |
| 输出抖动 | \(\mathbf{R}\) 设过小 / \(\mathbf{Q}\) 设过大 | 增大 \(\mathbf{R}\) / 减小 \(\mathbf{Q}\) |
| 协方差矩阵奇异 | 状态完全可观 \(\mathbf{P}_{k|k} \to 0\) | 加入"软约束" / 限制 \(\mathbf{P}\) 下界 |

### 6.4 最小可运行示例：1D 恒速目标跟踪

下面给出一个**完整可跑**的例子——在 1D 直线上跟踪一个恒速运动的目标，每步用带噪雷达测量其位置。展示卡尔曼滤波相比"原始测量"的优势。

#### 6.4.1 问题设定

- **状态** \(\mathbf{x}_k = [p_k, v_k]^\top\)：位置 + 速度；
- **过程模型**（恒速，时间步 \(\Delta t = 1\)）：

\[
\mathbf{x}_k = \begin{bmatrix}1 & 1\\ 0 & 1\end{bmatrix} \mathbf{x}_{k-1} + \mathbf{w}_k
\]

- **观测模型**（只测位置）：

\[
z_k = \begin{bmatrix}1 & 0\end{bmatrix} \mathbf{x}_k + v_k
\]

- 过程噪声协方差 \(\mathbf{Q} = \begin{bmatrix}0.1 & 0\\ 0 & 0.1\end{bmatrix}\)，观测噪声协方差 \(R = 1.0\)。

#### 6.4.2 代码实现（filterpy + numpy）

```python
import numpy as np
import matplotlib.pyplot as plt
from filterpy.kalman import KalmanFilter

# === 1. 构造卡尔曼滤波器 ===
kf = KalmanFilter(dim_x=2, dim_z=1)

# 状态转移矩阵（恒速模型）
dt = 1.0
kf.F = np.array([[1, dt],
                 [0,  1]])

# 观测矩阵（只测位置）
kf.H = np.array([[1, 0]])

# 过程噪声协方差
kf.Q = np.array([[0.1, 0],
                 [  0, 0.1]])

# 观测噪声协方差
kf.R = np.array([[1.0]])

# 初始状态 [位置, 速度]
kf.x = np.array([[0.0],
                 [1.0]])

# 初始协方差（位置不确定较大，速度不确定更大）
kf.P = np.array([[10.0,  0.0],
                 [ 0.0, 10.0]])

# === 2. 生成仿真数据 ===
np.random.seed(42)
N = 50
true_pos = np.cumsum(np.ones(N) * 1.0)  # 真实位置（恒速 1 m/s）
true_vel = np.ones(N) * 1.0
meas_pos = true_pos + np.random.randn(N) * 1.0  # 带噪雷达测量

# === 3. 跑卡尔曼滤波 ===
est_pos, est_vel = [], []
for z in meas_pos:
    kf.predict()       # 预测
    kf.update(z)       # 更新
    est_pos.append(kf.x[0, 0])
    est_vel.append(kf.x[1, 0])

est_pos = np.array(est_pos)
est_vel = np.array(est_vel)

# === 4. 可视化对比 ===
fig, axes = plt.subplots(2, 1, figsize=(10, 6))

# 位置
axes[0].plot(true_pos, 'g-', label='真值', linewidth=2)
axes[0].plot(meas_pos, 'rx', label='雷达测量', alpha=0.5)
axes[0].plot(est_pos, 'b-', label='KF 估计', linewidth=2)
axes[0].set_ylabel('位置 (m)')
axes[0].legend()
axes[0].set_title('1D 恒速目标跟踪：KF vs 原始测量')

# 速度
axes[1].plot(true_vel, 'g-', label='真值', linewidth=2)
axes[1].plot(est_vel, 'b-', label='KF 估计', linewidth=2)
axes[1].set_xlabel('时间步')
axes[1].set_ylabel('速度 (m/s)')
axes[1].legend()

plt.tight_layout()
plt.savefig('kf_tracking.png', dpi=100)
plt.show()

# === 5. 打印统计 ===
print(f"测量 RMSE: {np.sqrt(np.mean((meas_pos - true_pos)**2)):.3f} m")
print(f"KF   RMSE: {np.sqrt(np.mean((est_pos - true_pos)**2)):.3f} m")
```

#### 6.4.3 预期输出

```
测量 RMSE: 0.965 m
KF   RMSE: 0.534 m
```

KF 估计的均方根误差比原始雷达测量**降低近一半**。

#### 6.4.4 关键观察

1. **位置图**：红线（测量）抖动大但跟得上；绿线（真值）平滑；蓝线（KF）**兼顾两者**——既平滑又紧跟真值；
2. **速度图**：KF 在没有直接测速的情况下，**仅靠位置观测**就能估计出速度（利用了 \(\mathbf{F}\) 中的速度-位置耦合）；
3. **协方差 \(\mathbf{P}\) 收敛**：从初始的 10.0 逐步收敛到稳态（取决于 \(\mathbf{Q}/\mathbf{R}\) 比值），与 §2.4 协方差"呼吸"图一致。

#### 6.4.5 调参实验

可以尝试修改以下参数，观察 KF 行为变化：

| 修改 | 现象 | 物理含义 |
|:---|:---|:---|
| 把 `kf.Q` 调到 `0.01` | KF 输出更平滑但滞后 | 信任动力学模型，忽略观测 |
| 把 `kf.R` 调到 `10.0` | KF 输出接近原始测量 | 信任观测，不信任模型 |
| 把 `dt` 改成 `0.1` | 状态转移更精细，预测更准 | 时间步长对 KF 影响显著 |
| 用 `kf.update(z, R=R_adaptive)` | 自适应观测噪声 | 实际中常按信号强度/距离调整 |

#### 6.4.6 扩展到 EKF

如果观测是非线性的（例如雷达测**距离 + 方位角**而非笛卡尔位置）：

```python
from filterpy.kalman import ExtendedKalmanFilter

ekf = ExtendedKalmanFilter(dim_x=4, dim_z=2)  # 状态 [x, vx, y, vy]

# 状态转移（恒速 2D）
ekf.F = np.array([[1, 1, 0, 0],
                  [0, 1, 0, 0],
                  [0, 0, 1, 1],
                  [0, 0, 0, 1]])

# 非线性观测：极坐标 = [range, bearing] = h(x)
def hx(x):
    px, _, py, _ = x
    r = np.sqrt(px**2 + py**2)
    b = np.arctan2(py, px)
    return np.array([r, b])

# 观测雅可比
def HJacob(x):
    px, _, py, _ = x
    r2 = px**2 + py**2
    r = np.sqrt(r2)
    return np.array([[px/r,   0,  py/r,  0],
                     [-py/r2, 0,  px/r2, 0]])

ekf.x = np.array([0, 1, 0, 1])[:, None]
ekf.P *= 10
# ... predict / update ...
```

EKF 与 KF 的接口几乎相同，只是 `update` 阶段多传一个 `hx` 和 `HJacob` 描述非线性观测。

> 完整可运行代码与更多例子见 filterpy 官方文档：<https://filterpy.readthedocs.io/>。

---

## 参考文献

1. Wiener N. *Extrapolation, Interpolation, and Smoothing of Stationary Time Series*. MIT Press, 1949.
2. Kalman R E. *A New Approach to Linear Filtering and Prediction Problems*. Trans. ASME, J. Basic Engineering, 82(1):35–45, 1960.
3. Welch G, Bishop G. *An Introduction to the Kalman Filter*. UNC-CH TR 95-041, 2006.（入门必读）
4. Thrun S, Burgard W, Fox D. *Probabilistic Robotics*. MIT Press, 2005.（第 3 章 EKF 详细推导）
5. Simon D. *Optimal State Estimation: Kalman, H∞, and Nonlinear Approaches*. Wiley, 2006.
6. Madwick S. *An efficient orientation filter for IMU/AHRS/MARG arrays*, 2010.（轻量级 IMU 滤波）

---

## 附录 A：维纳-霍夫方程的频域推导

从正交性原理 \(\mathbb{E}[e(t)\, x(\tau)] = 0\) 出发：

\[
\mathbb{E}\left[\left(\int h(\alpha) x(t-\alpha) d\alpha - s(t)\right) x(\tau)\right] = 0
\]

交换期望与积分（平稳性允许）：

\[
\int h(\alpha)\, \mathbb{E}[x(t-\alpha) x(\tau)]\, d\alpha = \mathbb{E}[s(t)\, x(\tau)]
\]

即

\[
\int h(\alpha)\, R_{xx}(\tau - t + \alpha)\, d\alpha = R_{sx}(\tau - t)
\]

对两边关于 \(\tau\) 做傅里叶变换（左边的 \(\alpha\) 积分变量对 \(\tau\) 的依赖通过 \(\tau - t + \alpha\) 进入）：

左边的 FT：\(\int_\tau \int_\alpha h(\alpha) R_{xx}(\tau - t + \alpha) d\alpha\, e^{-j \omega \tau} d\tau\)。令 \(\beta = \tau - t + \alpha\)，\(d\beta = d\tau\)：

\[
= \int_\alpha h(\alpha) \int_\beta R_{xx}(\beta) e^{-j \omega (\beta + t - \alpha)} d\beta\, d\alpha
= e^{-j\omega t} \int_\alpha h(\alpha) e^{j \omega \alpha} d\alpha \cdot S_{xx}(\omega)
= e^{-j\omega t}\, H(-\omega)\, S_{xx}(\omega)
\]

右边 FT：\(e^{-j \omega t} S_{sx}(\omega)\)。

约去 \(e^{-j \omega t}\)：

\[
H(-\omega)\, S_{xx}(\omega) = S_{sx}(\omega)
\]

若 \(h(t)\) 是**实**的，则 \(H(-\omega) = H^*(\omega)\)，得：

\[
H^*(\omega) = \frac{S_{sx}(\omega)}{S_{xx}(\omega)}
\]

若信号与噪声**不相关**（即 \(R_{sx} = R_{ss}\)），则 \(S_{sx} = S_{ss}\)，且 \(S_{xx} = S_{ss} + S_{nn}\)：

\[
H(\omega) = \frac{S_{ss}(\omega)}{S_{ss}(\omega) + S_{nn}(\omega)}
\]

这正是维纳滤波的频域解。

---

## 附录 B：卡尔曼滤波的贝叶斯推导

### B.1 假设与目标

- 状态空间模型如 §2.1，噪声为**高斯白噪声**；
- 目标：递推计算后验 \(p(\mathbf{x}_k | \mathbf{z}_{1:k})\)。

### B.2 预测步（时间更新）

由全概率公式与马尔可夫性：

\[
p(\mathbf{x}_k | \mathbf{z}_{1:k-1}) = \int p(\mathbf{x}_k | \mathbf{x}_{k-1})\, p(\mathbf{x}_{k-1} | \mathbf{z}_{1:k-1})\, d\mathbf{x}_{k-1}
\]

在线性高斯假设下，\(p(\mathbf{x}_{k-1} | \mathbf{z}_{1:k-1}) = \mathcal{N}(\hat{\mathbf{x}}_{k-1|k-1}, \mathbf{P}_{k-1|k-1})\)，\(p(\mathbf{x}_k | \mathbf{x}_{k-1}) = \mathcal{N}(\mathbf{F}_k \mathbf{x}_{k-1} + \mathbf{B}_k \mathbf{u}_k, \mathbf{Q}_k)\)。高斯分布的线性组合仍为高斯，**精确**得到：

\[
p(\mathbf{x}_k | \mathbf{z}_{1:k-1}) = \mathcal{N}(\hat{\mathbf{x}}_{k|k-1}, \mathbf{P}_{k|k-1})
\]

其中

\[
\hat{\mathbf{x}}_{k|k-1} = \mathbf{F}_k\, \hat{\mathbf{x}}_{k-1|k-1} + \mathbf{B}_k\, \mathbf{u}_k
\]
\[
\mathbf{P}_{k|k-1} = \mathbf{F}_k\, \mathbf{P}_{k-1|k-1}\, \mathbf{F}_k^\top + \mathbf{Q}_k
\]

### B.3 更新步（观测更新）

由贝叶斯公式：

\[
p(\mathbf{x}_k | \mathbf{z}_{1:k}) \propto p(\mathbf{z}_k | \mathbf{x}_k)\, p(\mathbf{x}_k | \mathbf{z}_{1:k-1})
\]

其中似然 \(p(\mathbf{z}_k | \mathbf{x}_k) = \mathcal{N}(\mathbf{H}_k \mathbf{x}_k, \mathbf{R}_k)\)，先验 \(p(\mathbf{x}_k | \mathbf{z}_{1:k-1}) = \mathcal{N}(\hat{\mathbf{x}}_{k|k-1}, \mathbf{P}_{k|k-1})\)。

**高斯 × 高斯 = 高斯**（共轭性），可直接写出归一化结果：

\[
p(\mathbf{x}_k | \mathbf{z}_{1:k}) = \mathcal{N}(\hat{\mathbf{x}}_{k|k}, \mathbf{P}_{k|k})
\]

其中均值与协方差的更新公式正是 §2.3 的更新 3 式。

#### 高斯共轭更新的几何直觉

把"先验 × 似然 = 后验"画在二维空间里（取状态二维为例）：

```
        p(x)
         ↑
         │       先验 p(x_k | z_{1:k-1})
         │          ╱╲
         │         ╱  ╲
         │        ╱    ╲       后验 p(x_k | z_{1:k})
         │       ╱      ╲      ╱╲
         │      ╱        ╲    ╱  ╲
         │     ╱          ╲  ╱    ╲
         │    ╱            ╲╱      ╲
         │   ╱        ★    ╳        ╲
         │  ╱        ↑    ↑ ↑        ╲
         │ ╱     先验均值  似然均值 后验均值
         │╱
         └──────────────────────────────→ x
                  似然 p(z_k | x_k)
                    (窄峰)
```

**关键观察**：

1. **先验**通常较宽（预测不确定性大）；
2. **似然**通常较窄（观测精度高，体现在 \(\mathbf{R}_k\) 小）；
3. **后验 = 先验 × 似然（归一化）**：宽度介于两者之间，均值被"拉向"似然的峰值；
4. **后验均值 = 先验均值 + 卡尔曼增益 × 创新**，与图中的"拉向"动作一致；
5. **后验协方差 < min(先验协方差, 似然协方差)**：融合两个高斯后不确定性一定**严格降低**（这是 KF "越来越准"的形式化保证）。

> **如果先验不是高斯怎么办？** 卡尔曼公式失效，必须用 EKF/UKF（仍要求单峰）甚至 PF（任意分布）。这就是非线性扩展存在的根本原因。

### B.4 推导" \(\propto\) "的归一化

把两边高斯写成指数形式：

\[
\exp\left(-\frac{1}{2}(\mathbf{z}_k - \mathbf{H}_k \mathbf{x}_k)^\top \mathbf{R}_k^{-1} (\mathbf{z}_k - \mathbf{H}_k \mathbf{x}_k) - \frac{1}{2}(\mathbf{x}_k - \hat{\mathbf{x}}_{k|k-1})^\top \mathbf{P}_{k|k-1}^{-1} (\mathbf{x}_k - \hat{\mathbf{x}}_{k|k-1})\right)
\]

整理为 \(\mathbf{x}_k\) 的二次型 \(-\frac{1}{2} \mathbf{x}_k^\top \mathbf{A} \mathbf{x}_k + \mathbf{b}^\top \mathbf{x}_k + C\)，其中

\[
\mathbf{A} = \mathbf{H}_k^\top \mathbf{R}_k^{-1} \mathbf{H}_k + \mathbf{P}_{k|k-1}^{-1}
\]
\[
\mathbf{b} = \mathbf{H}_k^\top \mathbf{R}_k^{-1} \mathbf{z}_k + \mathbf{P}_{k|k-1}^{-1} \hat{\mathbf{x}}_{k|k-1}
\]

后验协方差 = \(\mathbf{A}^{-1}\)，后验均值 = \(\mathbf{A}^{-1} \mathbf{b}\)。利用 Woodbury 恒等式化简，即得 §2.3 的更新式。

### B.5 一句话总结

> 在线**性高斯**假设下，预测 + 更新两步恰好闭合（高斯的共轭性保证后验仍为高斯），卡尔曼滤波的 5 式就是**精确贝叶斯滤波**的闭式解。这是它在"线性高斯"领域无法被超越的根本原因——它不是"近似"，而是"精确"。

---

## 附录 C：Joseph 形式协方差更新

直接用 \(\mathbf{P}_{k|k} = (\mathbf{I} - \mathbf{K}_k \mathbf{H}_k) \mathbf{P}_{k|k-1}\) 在浮点运算中**不能保证对称正定**——有限精度下会逐渐失去对称性，长期运行可能导致滤波发散。

**Joseph 形式**通过对残差做严格的二阶矩计算给出**数值稳定**的更新：

\[
\boxed{
\mathbf{P}_{k|k} = (\mathbf{I} - \mathbf{K}_k \mathbf{H}_k)\, \mathbf{P}_{k|k-1}\, (\mathbf{I} - \mathbf{K}_k \mathbf{H}_k)^\top + \mathbf{K}_k\, \mathbf{R}_k\, \mathbf{K}_k^\top
}
\]

可以验证：

- 第一项 \((\mathbf{I} - \mathbf{K} \mathbf{H}) \mathbf{P} (\mathbf{I} - \mathbf{K} \mathbf{H})^\top\)：保证**对称**（因为 \(\mathbf{M} \mathbf{A} \mathbf{M}^\top\) 形式自然对称，且若 \(\mathbf{P}\) 半正定则该表达式也半正定）；
- 第二项 \(\mathbf{K} \mathbf{R} \mathbf{K}^\top\)：补偿"舍去"的高阶项，保证与原式**数学上完全等价**。

工程上**几乎所有生产级 KF 实现**都用 Joseph 形式（例如 OpenCV `KalmanFilter`、ROS `robot_localization`）。

---

## 附录 D：维纳滤波的因果解与预测-滤波分解

当滤波器必须**因果**（\(h(t) = 0,\ t < 0\)）时，频域解不再干净——因为 \(H(\omega) = S_{ss}/(S_{ss} + S_{nn})\) 可能非因果。**经典做法**是把维纳-霍夫方程做"单边 z 变换"，然后分解为**预测误差滤波器**（用 Levinson-Durbin 递推）。

工程上有两个常见分解：

- **预测-滤波分解**：把维纳滤波器分解为"一步预测器"（白化滤波器）+ "因果平滑器"。其中预测器由 Levinson-Durbin 递推解出，平滑器则是预测器的"对偶"。

- **谱分解（Spectral Factorization）**：对 \(S_{ss}(\omega)\) 做谱分解 \(S_{ss}(\omega) = |L(\omega)|^2\)，其中 \(L(\omega)\) 是**最小相位**谱因子；则因果维纳滤波的频率响应为 \(H(\omega) = 1/L(\omega)\)。

这些推导相对繁复，详见经典教材 [Wiener 1949] 与 [Kailath 估计与检测理论]。工程上，**因果维纳滤波**常被**卡尔曼滤波**取代（卡尔曼自然就是因果的、时域的、递推的）。
