---
layout: post
title: "Flow Matching：连续标准化流的仿真无关训练"
date: 2023-03-01
categories: [DiffusionModel]
---
> 本文是 Flow Matching 系列的第二篇，介绍 Flow Matching 如何实现对连续标准化流（CNF）的仿真无关训练。建议先阅读第一篇：标准化流基础。

## 1. 从 CNF 到 Flow Matching

Flow Matching 是一个 **simulation-free** 的训练 CNF 方法，基于对**固定的（fixed）条件概率路径**（conditional probability paths）的向量场的回归。

![image-20250731091244588](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250731091244588.png)

$$
p_t(x) = [\phi_t]_\sharp \, p_0(x), \quad \frac{\partial p_t(x)}{\partial t} = -\text{div}(v_t(x) p_t(x))
$$
即密度变化 = 概率质量的流入/流出。

![image-20250731091346094](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250731091346094.png)

> 核心思路：不求解单个复杂的映射函数，而是用一个向量场（velocity field）驱动连续变换。密度变化由散度（divergence）刻画——散度为正表示概率质量流出，散度为负表示流入。由此将生成问题转化为学习一个"引导"概率流动的向量场。



> Flow Matching 兼容一族通用的高斯概率路径，用于在噪声和数据样本之间进行变换——这包含了现有的扩散路径作为特例。

Flow Matching 也有更好的生成路径。非 diffusion probability paths 实现了更高效的 CNF 训练。



> Flow Matching 为训练扩散模型提供了一种替代方案。更重要的是，它为使用非扩散概率路径训练 CNF 打开了大门。

OT（Optimal Transport）Displacement path 比 diffusion path 要更加高效：

> 特别值得关注的是使用最优传输（OT）位移插值来定义条件概率路径。这些路径比扩散路径更高效，提供更快的训练和采样，并具有更好的泛化能力。在 ImageNet 上使用 Flow Matching 训练 CNF 证明了这一点。

## 2. 向量场的定义

向量场的定义：$\phi_t(x)$ 是 $\mathbb{R}^d$ 的点，而 $v_t$ 是 $\mathbb{R}^d$ 的向量。

![image-20250709201223238](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250709201223238.png)

$$\frac{d\phi_t(x)}{dt} = v_t(\phi_t(x)), \quad \phi_0(x) = x$$

CNF 就是用 Flow 将一个简单分布 $p_0$ 转化为一个复杂分布 $p_1$（Push Forward）。

![image-20250709201922658](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250709201922658.png)

$$p_t = [\phi_t]_\sharp \, p_0$$

![image-20250709201954876](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250709201954876.png)

$$p_t(x) = p_0(\phi_t^{-1}(x)) \left|\det \frac{d\phi_t^{-1}(x)}{dx}\right|$$

用神经网络建模向量场 $v_t$：

> 用神经网络来建模向量场 $v_t$：$v_t(x; \theta)$，其中 $\theta$ 为网络参数。

## 3. Flow Matching 训练目标

将目标分布参数化为 $p_1(x, \theta)$，求其到 $p_0$ 的变换：

![image-20250928084055471](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20250928084055471.png)

$$\mathcal{L}(\theta) = \text{KL}(p_{\text{data}}(x) \| p_1(x; \theta)) = -\mathbb{E}_{p_{\text{data}}(x)}[\log p_1(x; \theta)] + \text{const}$$

我们的目的是训练一个能回归出目标向量场的模型。事实上，我们可以通过 FM 构造 OT 路径：



> 我们提出 Flow Matching 目标，一个简单直观的训练目标：回归到能生成期望概率路径的目标向量场。



> 我们在 ImageNet 这一大规模高多样性的图像数据集上验证了 Flow Matching 及通过最优传输路径的构造。我们发现可以轻松训练模型以达到有竞争力的结果。

对应的 Flow Matching 的训练目标如下，就是匹配一个向量场 $u_t(x)$：

$$\mathcal{L}_{\text{FM}}(\theta) = \mathbb{E}_{t, p_t(x)} \| v_t(x; \theta) - u_t(x) \|^2$$

下一篇将解决 FM 目标在实际中不可行的问题，介绍**条件概率路径与边缘化**这一核心技巧。
