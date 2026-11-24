---
layout: post
title: "HMR：端到端回归人体形状与姿态"
categories: [TechSharing]
mathjax: true
---

> Kanazawa et al., *End-to-end Recovery of Human Shape and Pose*（常称 **HMR**）, CVPR 2018.
> 正是「SMPLify 式拟合 → 前馈神经网络」的代表作。

**一句话**：不再对每张图跑迭代优化，而是让网络**一步吐出** SMPL 参数 —— 把「优化」蒸馏成「推理」。

## 想法

不再对每张图做迭代优化，而是：

$$
\text{Image}\;\xrightarrow{\;\mathrm{CNN}\;}\;(\hat\beta,\hat\theta,\hat{\text{camera}}),
$$

端到端吐出 SMPL 参数（及弱透视相机），给定人框后可近实时。

## 训练信号怎么够

仅有野外 2D 关键时，重投影损失**严重欠定**（深度、体型可对冲）。HMR 的关键补充：

1. **关键重投影损失**（可训在只有 2D 标注的图上）；  
2. **对抗先验**：判别器判断 $(\beta,\theta)$ 是否像真实人体网格分布（用大量 3D mesh / MoCap，**不必与图像成对**）；  
3. 有 3D 监督时再加 3D 关节 / 参数损失。

迭代回归模块在特征上多步 refinement，类似「把优化器的几步展开进网络」。

## 和 SMPLify 的关系

| | SMPLify | HMR |
| :--- | :--- | :--- |
| 推理 | 每图优化 | 前馈一次（可再 refine） |
| 速度 | 慢 | 近实时 |
| 先验 | 显式能量项 | 数据驱动 + 对抗 |
| 输入 | 常依赖 2D 关节 | 可直接吃图像特征 |

实践中也常见：**HMR 初始化 → 少量 SMPLify 精修**。后续 **SPIN**（Kolotouros et al.）把「回归 ↔ 优化」在训练环里拧得更紧；**SMPL-X + SMPLify-X** 把手脸一并拟合。

> 口诀：**SMPLify = 优化拟合；HMR = 学会拟合**。

## 往下读

- 上一篇：[SMPLify：单图优化拟合](SMPLify单图拟合.md)
- 总览：[SMPL 人体参数化及其后续](Avatar-SMPL人体重建.md)（含着装扩展路线）

> **一句话记住**：HMR 没有发明新的约束，只是把「先验 + 重投影」换了个更快的执行方式 —— 约束还是那套，跑得更快。
