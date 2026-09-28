---
layout: post
title: "Hindsight Experience Replay（HER）"
date: 2024-04-01
categories: [ReinforcementLearning]
mathjax: true
---

> **论文**：Marcin Andrychowicz, Filip Wolski, Alex Ray, et al. [*Hindsight Experience Replay*](https://arxiv.org/abs/1707.01495). NeurIPS 2017.
>
> 前置：[强化学习：介绍]({% post_url 2.Machine Learning/3.强化学习/2021-09-01-强化学习：介绍 %})；稀疏奖励背景见 [强化学习：稀疏奖励问题]({% post_url 2.Machine Learning/3.强化学习/2022-02-01-强化学习：稀疏奖励问题 %}).

**Hindsight Experience Replay（HER，后见经验回放）** 解决**多目标、稀疏奖励**机器人任务中样本效率极低的问题。核心想法极其朴素：**一次没到达原定目标 $g$ 的轨迹，仍可作为「到达实际达成目标 $g'$」的成功经验**，经目标重标记（goal relabeling）后写入 replay buffer，与 off-policy 算法（DDPG 等）结合即可大幅加速学习。

---

## 1. 问题：稀疏奖励下的样本浪费

考虑机械臂推物块：状态 $s$ 含机械臂与物块位姿，**目标** $g$ 为物块应到达的 3D 坐标。奖励常为

$$
r(s,a,g)=
\begin{cases}
0 & \|f(s')-g\| < \epsilon \text{（成功）},\\
-1 & \text{否则},
\end{cases}
$$

其中 $f(s')$ 为**实际达成状态**（achieved goal，如物块位置），$s'$ 为执行 $a$ 后的状态。智能体随机探索时，**几乎永远碰不到** $+1$（或 $0$）——整条 episode 的 transition $(s_t,a_t,r_t,s_{t+1},g)$ 奖励全是 $-1$，对 $Q$ 或策略梯度**几乎不提供有用信号**，经验被白白丢弃。

人工 reward shaping 可缓解，但需领域知识且易 reward hacking（见稀疏奖励一文 PBRS 讨论）。HER 走另一条路：**不改环境奖励定义，改「这条经验算在哪个目标下」**。

---

## 2. 目标条件 MDP（Goal-Conditioned MDP）

HER 要求任务可表述为 **UVFA / 目标条件** 形式（与 Schaul et al. 2015 *Universal Value Function Approximators* 一脉）。

- **状态** $s \in \mathcal{S}$：环境完整观测（机械臂关节、物块位姿等）；
- **目标** $g \in \mathcal{G}$：任务指定量（物块目标位置）；训练时从分布 $p(g)$ 采样；
- **达成量** $f(s)\in\mathcal{G}$：从 $s$ 可解析提取的「当前达成了什么」（物块当前位置）；
- **动作** $a \in \mathcal{A}$；
- **转移** $s' \sim P(\cdot|s,a)$（$g$ 在 episode 内不变）；
- **奖励** $r(s,a,g)=R\bigl(f(s'), g\bigr)$，常取稀疏或稠密：
  - 稀疏：$R(f,g)=\mathbb{1}[\|f-g\|<\epsilon]$ 或 $0/-1$ 版本；
  - 稠密：$R(f,g)=-\|f-g\|_2$。

**策略与价值** 均条件于目标：

$$
\pi_\theta(a|s,g), \qquad Q_\phi(s,a,g).
$$

同一网络处理**不同目标**——学的是「在状态 $s$ 下为实现 $g$ 该做什么」，而非单一固定任务。

---

## 3. HER 核心思想

Episode 按原始目标 $g$  rollout，得到轨迹

$$
\tau = \bigl(s_0,a_0,r_0,s_1,\ldots,s_T\bigr), \quad g \text{ 固定}.
$$

若失败（$f(s_T)\neq g$），标准 RL **只存** $(s_t,a_t,r_t,s_{t+1},g)$，且 $r_t$ 全为负——**浪费**。

**后见之明（hindsight）**：事后看，智能体其实**成功到达了** $g' = f(s_{t'})$（常取 $t'=T$ 或未来某步）。若当初目标就是 $g'$，同一 $(s_t,a_t,s_{t+1})$ 会得到**更好（或成功）的奖励**：

$$
r'_t = R\bigl(f(s_{t+1}),\, g'\bigr).
$$

HER 将额外样本 $(s_t,a_t,r'_t,s_{t+1},g')$ 写入 replay buffer。**失败轨迹变成其他目标下的成功/近成功数据**，极大增加有效监督密度。

> **比喻**：射箭脱靶，但靶纸上箭簇位置明确——把「那一簇」当作新靶心，这次射击就是满分练习。

---

## 4. 算法：与 DDPG 的结合

HER 是 **replay 层面的数据增强**，不替换底层 RL 算法。论文用 **DDPG**；亦可接 TD3、SAC 等 off-policy 方法。

### 4.1 单条 transition 的重标记

存储时除原始 transition 外，以策略 $h$ 生成 $k$ 个**虚拟目标** $\tilde{g}$：

1. 从 episode 内按 $h$ 采样 $\tilde{g}$（见 §5）；
2. 重算 $ \tilde{r} = R(f(s_{t+1}), \tilde{g})$；
3. 存入 buffer：$(s_t, a_t, \tilde{r}, s_{t+1}, \tilde{g})$。

训练时 actor/critic 输入 $(s,g)$，与 DDPG 相同，只是 batch 里混有大量 relabeled 目标。

### 4.2 伪代码

```
对每个 episode:
    采样目标 g ~ p(g)
    用策略 π(·|·,g) 与环境交互，收集
        {(s_t, a_t, r_t, s_{t+1})}_{t=0}^{T-1}
    对每条 (s_t, a_t, r_t, s_{t+1}):
        buffer.add(s_t, a_t, r_t, s_{t+1}, g)          # 原始
        重复 k 次:
            g̃ ~ h( episode, t )                         # HER 策略
            r̃ = R( f(s_{t+1}), g̃ )
            buffer.add(s_t, a_t, r̃, s_{t+1}, g̃)       # 重标记
    从 buffer 采样 mini-batch，按 DDPG/TD3/SAC 更新
```

**超参**：每步 transition 额外 $k$ 个 HER 目标（论文常 $k=4$）；与 **future** 策略联用效果最好。

---

## 5. 四种目标采样策略 $h$

给定 episode 中时刻 $t$ 的 transition，如何选 $\tilde{g}$？

| 策略 | 采样方式 | 表现 |
| :--- | :--- | :--- |
| **final** | $\tilde{g} = f(s_T)$（episode 最终达成） | 较好 |
| **future** | $\tilde{g} = f(s_j)$，$j \sim \mathrm{Uniform}\{t+1,\ldots,T\}$ | **最佳（默认）** |
| **episode** | $\tilde{g} = f(s_j)$，$j \sim \mathrm{Uniform}\{0,\ldots,T\}$ | 一般 |
| **random** | $\tilde{g} = f(s_j)$，$j$ 来自 buffer 中随机 episode | 较差 |

**future 为何更好？** 从 $t$ 的**未来**状态取目标，保证 $\tilde{g}$ 是「从 $s_t$ 出发确实有机会到达」的达成量，且 $r'_t = R(f(s_{t+1}),\tilde{g})$ 常为非平凡信号（既非全成功也非全失败），利于 $Q$ 学习中间动态。final 只用终点，信号较粗；random 目标可能与当前轨迹无关，相关性弱。

---

## 6. 为何有效？（直觉与理论侧面）

**样本效率**：稀疏奖励下成功 transition 概率 $\propto \epsilon^{\text{步数}}$；HER 把每条轨迹扩展为 $O(kT)$ 条带**多样目标**的样本，其中大量在对应 $\tilde{g}$ 下具有**非零、一致**的奖励结构。

**与多任务学习**：可视为在 $\mathcal{G}$ 上同时学一族任务；失败轨迹为其他 $g'\in\mathcal{G}$ 提供正例。

**Off-policy 必要性**：重标记样本的 $(s,a)$ 由**旧策略**产生，须用 replay + 离策略校正（DDPG 的 target network、SAC 的熵正则等）。on-policy（PPO）不能原样复用 buffer 中旧轨迹的 relabeled 目标，需改造（如事后用新策略重估 advantage）。

**不保证最优的局限**：HER 教的是「到达各种曾出现过的 $g'$」，不直接优化**原定** $g$ 的成功率；实践中与原始 $(s,a,r,s',g)$ 混训，二者兼顾。

---

## 7. 论文实验要点

OpenAI 多指机械臂 **Fetch** 与 **Shadow Hand** 套件（MuJoCo + Gym）：

| 任务 | 说明 | 无 HER | 有 HER |
| :--- | :--- | :--- | :--- |
| FetchReach | 夹爪到点 | 易 | 更快 |
| FetchPush / PickAndPlace | 推/抓物块到目标 | **几乎学不会** | **可学会** |
| HandReach / 操作 | 高维灵巧手 | 极难 | 显著改善 |

关键结论：**在稀疏奖励、多目标机器人任务上，HER 是从完全失败到可解的分水岭**；稠密奖励或极简单任务上增益较小。

---

## 8. 实现要点

1. **分离** `observation` 与 `achieved_goal` / `desired_goal`（OpenAI Gym 的 `Observations` 字典接口即为此设计）；
2. Critic 输入 $\mathrm{concat}(s, g)$ 或分别编码后融合；Actor 同理；
3. 奖励函数 $R(f,g)$ 在 relabel 时**必须用同一函数重算**，不可复用旧 $r_t$；
4. `future` 策略：$j\ge t+1$，避免用当前 $f(s_t)$ 作目标导致 $r'_t$  trivial；
5. 归一化：状态、目标坐标常做 running normalization（Fetch 类任务敏感）；
6. 推荐栈：**HER + DDPG/TD3/SAC**；Stable-Baselines3、rlkit 等库内置 HER。

```python
# future 策略核心（示意）
def her_future_goal(episode_achieved_goals, t, k=4):
    T = len(episode_achieved_goals)
    goals = []
    for _ in range(k):
        j = np.random.randint(t + 1, T)   # 未来时刻
        goals.append(episode_achieved_goals[j])
    return goals

def relabel_reward(achieved_goal, desired_goal, sparse=True):
    if sparse:
        return 0.0 if np.linalg.norm(achieved_goal - desired_goal) < 0.05 else -1.0
    return -np.linalg.norm(achieved_goal - desired_goal)
```

---

## 9. 适用条件与局限

**适合**：目标空间 $\mathcal{G}$ 与 $f(s)$ 可明确定义；多目标/参数化目标（不同 $g$ 即不同任务）；稀疏或稠密 $R(f,g)$ 均可；连续控制 + off-policy。

**不适合或需改造**：单一固定目标、无法从状态提取 achieved goal；纯离散成功/失败且无几何中间量；on-policy 为主且不愿引入 off-policy 修正；目标与行为因果链过长且 $f(s)$ 不反映中间进展。

**后续工作（了解即可）**：**Curriculum HER**、**CEM-HER**、与 **demonstration** 结合、**Goal GAN** 自动生成课程目标等，均在 HER「重标记失败经验」框架上扩展。

---

## 10. 小结

| 概念 | 内容 |
| :--- | :--- |
| **问题** | 稀疏奖励下失败 episode 无学习信号 |
| **手段** | 用实际达成的 $g'$ 替换原目标 $g$，重算奖励 |
| **形式** | 目标条件 MDP，$\pi(a|s,g)$、$Q(s,a,g)$ |
| **策略** | future 采样 $\tilde{g}=f(s_{j})$，$j>t$ |
| **算法** | Replay 增强 + DDPG/TD3/SAC |

HER 的价值在于：**不修改环境、不手工 shaping，仅改变经验如何入库**，就把大量「废数据」变成稠密的多任务监督——这是后见之明在 RL 里最成功的应用之一。

---

## 参考文献

- Andrychowicz et al., *Hindsight Experience Replay*, NeurIPS 2017. [arXiv:1707.01495](https://arxiv.org/abs/1707.01495)
- Schaul et al., *Universal Value Function Approximators*, ICML 2015.
- Lillicrap et al., *Continuous Control with Deep Reinforcement Learning* (DDPG), ICLR 2016.
- Plappert et al., *Multi-Goal Reinforcement Learning: Challenging Robotics Environments and Request for Research*, 2018（Fetch/Hand 环境）.
