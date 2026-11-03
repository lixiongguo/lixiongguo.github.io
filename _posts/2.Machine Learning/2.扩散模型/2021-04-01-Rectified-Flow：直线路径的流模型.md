---
layout: post
title: "Rectified Flow：直线路径的流模型"
date: 2023-05-01
categories: [DiffusionModel]
---
> 本文是 Flow Matching 系列的第四篇，介绍 Rectified Flow——一种学习直线 ODE 路径以实现一步生成的简洁方法。建议先阅读第三篇：条件流匹配。

## 1. Rectified Flow 的基本思路

Rectified Flow（RF）很简单，是用学习常微分方程的方式来学习两个分布间的映射。

![image-20250711135433102](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250711135433102.png)

> Rectified flow 是一种极其简单的方法：学习一个神经 ODE 模型来在两个经验分布 $\pi_0$ 和 $\pi_1$ 之间进行传输。

基本的思路就是学习**直线路径**，可以通过求解一个非线性最小二乘：

![image-20250711135747825](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250711135747825.png)

$$\min_v \int_0^1 \mathbb{E}\bigl[\|(X_1 - X_0) - v(X_t, t)\|^2\bigr] \, dt, \quad X_t = t X_1 + (1-t) X_0$$

由于方法生成的是直线，所以只用一步 Euler 就能获得很好的结果：

![image-20250711135930889](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250711135930889.png)

> 在图像生成和翻译任务上，rectified flow 产生了几乎直线的流，即使仅用单步 Euler 离散化也能给出高质量结果。

---

## 2. 作为传输映射问题

### 2.1 传输问题

神经网络生成可以认为是一个传输映射问题（跟 Monge 问题是一个意思）：

![image-20250711140246192](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250711140246192.png)

> **传输问题**：给定两个分布 $X_0 \sim \pi_0$、$X_1 \sim \pi_1$ 的经验观测，求一个映射 $T: \mathbb{R}^d \to \mathbb{R}^d$（希望在某些意义下是最优的），使得 $Z_0 \sim \pi_0$ 时 $Z_1 = T(Z_0) \sim \pi_1$，即 $(Z_0, Z_1)$ 构成 $\pi_0$ 与 $\pi_1$ 的耦合（传输计划）。

$$T: \mathbb{R}^d \to \mathbb{R}^d, \quad Z_1 = T(Z_0) \sim \pi_1 \;\text{when}\; Z_0 \sim \pi_0$$

### 2.2 Rectified Flow 的完整定义

全部就是求解如下的一个非线性最小二乘：

![image-20250711140456644](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250711140456644.png)

> **Rectified Flow**：给定 $X_0 \sim \pi_0$、$X_1 \sim \pi_1$，rectified flow 是一个 ODE $dZ_t = v(Z_t, t)dt$，它将 $Z_0$ 从 $\pi_0$ 转换到遵循 $\pi_1$ 的 $Z_1$。漂移力 $v: \mathbb{R}^d \to \mathbb{R}^d$ 被设置为尽可能驱动流沿着从 $X_0$ 指向 $X_1$ 的直线方向，通过求解简单的最小二乘回归：
> $$\min_v \int_0^1 \mathbb{E}\bigl[\|(X_1 - X_0) - v(X_t, t)\|^2\bigr] dt, \quad X_t = t X_1 + (1-t) X_0$$
> 通过用 $X_1 - X_0$ 拟合漂移 $v$，rectified flow 将线性插值路径 $X_t$ 因果化，产生无需看到未来即可模拟的 ODE 流。

### 2.3 三个关键特性

这样计算出来的 Flow 有 3 个特性：

![image-20250711160914052](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250711160914052.png)

1. **非交叉性（Non-crossing）**：ODE $dZ_t = v(Z_t, t)dt$ 解存在唯一，不同路径不会交叉——即不存在位置 $z$ 和时间 $t$ 使得两条路径以不同方向穿过同一点，否则 ODE 解不唯一。而线性插值路径 $X_t$ 可能交叉（非因果），rectified flow 通过重新布线经过交点的单独轨迹来避免交叉，同时追踪与插值路径相同的密度图。可以将插值 $X_t$ 视为"修建道路"，rectified flow 视为粒子在道路上以近视、无记忆、非交叉方式通行，从而重建更确定的 $(Z_0, Z_1)$ 配对。

2. **降低传输代价**：若目标精确求解，rectified flow 的配对 $(Z_0, Z_1)$ 构成 $\pi_0, \pi_1$ 的有效耦合。原始数据对 $(X_0, X_1)$ 可以是任意耦合（通常是独立的，因为实际问题缺乏有意义的配对观测），而 rectified 耦合 $(Z_0, Z_1)$ 由 ODE 模型构造，具有确定的依赖关系。递归应用 rectified flow 可以得到"更直"的流路径——称为 *reflow* 过程。

3. **直线流实现快速采样**：几乎直线的路径在数值模拟中产生很小的离散化误差。完美直线路径可以用单步 Euler 精确模拟，相当于一步模型。这解决了现有连续时间 ODE/SDE 模型推理成本高的核心瓶颈，在生成式建模中极具吸引力。

### 2.4 非线性版

非线性版：

设 $X = \{X_t: t \in [0,1]\}$ 为连接 $X_0$ 和 $X_1$ 的任意时间可微随机过程，$\dot{X}_t$ 为其时间导数。

非线性 rectified flow 定义为 $dZ_t = v^*(Z_t, t)dt$（$Z_0 = X_0$），其中 $v^*(z,t) = \mathbb{E}[\dot{X}_t | X_t = z]$ 

可通过求解 $\min_v \int_0^1 \mathbb{E}\bigl[\|\dot{X}_t - v(X_t, t)\|^2\bigr] dt$ 来估计。
$$
v^*(z, t) = \mathbb{E}[\dot{X}_t \,|\, X_t = z], \quad \min_v \int_0^1 \mathbb{E}\bigl[\|\dot{X}_t - v(X_t, t)\|^2\bigr] \, dt
$$

