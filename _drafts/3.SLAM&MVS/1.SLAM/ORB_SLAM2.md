# ORB-SLAM2

> Raúl Mur-Artal, Juan D. Tardós. *ORB-SLAM2: An Open-Source SLAM System for Monocular, Stereo, and RGB-D Cameras*, IEEE Transactions on Robotics, 33(5):1255–1262, 2017.  
> arXiv：[1610.06475](https://arxiv.org/abs/1610.06475) · 项目页：[webdiis.unizar.es/~raulmur/orbslam](http://webdiis.unizar.es/~raulmur/orbslam/) · 代码：[raulmur/ORB_SLAM2](https://github.com/raulmur/ORB_SLAM2)（GPLv3）  
> 前作：Mur-Artal, Montiel, Tardós. *ORB-SLAM: A Versatile and Accurate Monocular SLAM System*, TRO 2015（单目）。

在单目 ORB-SLAM 上扩展为 **同一套特征 + BA 后端**，同时支持单目 / 双目 / RGB-D：闭环、重定位、地图复用；标准 CPU 实时。双目与深度使尺度可观，避免单目的尺度漂移与困难初始化。地图是 **稀疏 ORB 点 + 关键帧**，目标是长期、全局一致定位，而非稠密重建（可用关键帧位姿反投影深度做可视化）。

## 1. 相对 ORB-SLAM（单目）的贡献

| 贡献 | 要点 |
|:---|:---|
| 多传感器统一前端 | 双目匹配 / RGB-D 深度合成「虚拟右目」$u_R$，后端与输入模态无关 |
| 度量尺度 BA | 单目 + 双目观测一起进 BA，轨迹与地图带真实尺度 |
| 近 / 远立体点策略 | 深度 $<40\times$ 基线为近点（可单帧三角化，强平移/尺度）；远点多靠旋转、需多视图支撑 |
| 闭环后 Full BA | Pose-graph 纠漂后另开线程做全局 BA，再与持续建图结果合并 |
| Localization Mode | 关建图与闭环，VO 轨迹 + 地图匹配，已建好区域近零漂移轻量定位 |
| 开源一体 | 据称首个开源、同时覆盖 mono / stereo / RGB-D 的完整视觉 SLAM |

## 2. 系统架构

三主线程 + 可选第四线程（图 2）：

```text
输入帧（mono / stereo / RGB-D）
  │
  ├─ Tracking
  │    预处理（提 ORB / 立体匹配或深度→虚拟立体）
  │    → 与局部地图匹配 → motion-only BA 求当前位姿
  │    → 关键帧判定
  │
  ├─ Local Mapping
  │    管理局部地图 → Local BA（共视窗口）
  │    地图点创建 / 剔除，关键帧剔除
  │
  └─ Loop Closing
       DBoW2 回环检测 → 几何验证 → Pose-graph（SE3，无尺度漂移）
       → 另开线程 Full BA → 与运行中新增关键帧/点合并
```

共性基础设施（继承自 ORB-SLAM）：

- **ORB**：跟踪、建图、地点识别同一特征；对旋转 / 尺度与曝光变化较稳，提点匹配快。
- **DBoW2**：回环与重定位。
- **共视图（covisibility）+ 最小生成树**：取局部窗口，使 Tracking / Local Mapping 复杂度不随全局地图线性爆炸。

## 3. 关键点类型（III-A）

| 类型 | 定义 | 作用 |
|:---|:---|:---|
| 立体关键点 $\mathbf{x}_s=(u_L,v_L,u_R)$ | 左右匹配；RGB-D：$u_R=u_L-f_x b/d$ | 近点：尺度+平移+旋转；远点：旋转准、平移弱 |
| 单目关键点 $\mathbf{x}_m=(u_L,v_L)$ | 无有效视差 / 深度 | 多视图三角化，无尺度，贡献旋转与平移 |

近 / 远阈值（约 $40\times$ 基线）来自早期立体 SLAM（Paz et al.）。KITTI 高速路等「场景几乎全是远点」时，必须靠近点数量触发更密关键帧，否则平移不稳。

## 4. 启动与 BA（III-B / III-C）

**启动**：双目 / RGB-D 首帧即可建关键帧并用地图点初始化，无需单目那套多视图 SfM 冷启动。

**三类 BA**（g2o / LM，Huber）：

1. **Motion-only BA**（跟踪）：只优化当前 $\mathbf{R},\mathbf{t}$，最小化重投影误差。
2. **Local BA**：共视关键帧 $\mathcal{K}_L$ + 其观测点 $\mathcal{P}_L$；看到这些点但不在窗口内的关键帧固定。
3. **Full BA**：全局关键帧与点；原点关键帧固定以消 gauge。

投影：单目 $\pi_m$ 为针孔；整流立体 $\pi_s$ 额外输出右目横坐标（基线 $b$）：

$$
\pi_s\begin{bmatrix}X\\Y\\Z\end{bmatrix}
=
\begin{bmatrix}
f_x X/Z+c_x\\
f_y Y/Z+c_y\\
f_x(X-b)/Z+c_x
\end{bmatrix}
$$

## 5. 闭环与关键帧策略（III-D / III-E）

- 尺度可观 → 闭环几何验证与 pose-graph 用 **刚体 SE3**，不再用单目的相似变换（Sim3）纠尺度漂移。
- Full BA 与建图并行：若 BA 中途又检测到新环则中止并重来；结束后把校正经生成树传播到 BA 期间新增的关键帧与点。
- 关键帧：**先密插后剔除**。额外条件：跟踪到的近点 $<\tau_t$ 且本帧还能新建 $\ge\tau_c$ 个近立体点则插帧（论文经验值 $\tau_t=100,\ \tau_c=70$）。

## 6. Localization Mode（III-F）

关闭 Local Mapping 与 Loop Closing。跟踪同时用：

- **地图点匹配**：已建区域零漂移；
- **VO 匹配**：当前帧与上一帧由立体/深度新建的 3D 点，穿越未建图区域时仍可跟，但会积漂。

适合已知环境长期定位（论文举例：已建好空间里的 VR 视点跟踪）。

## 7. 实验要点（原文）

| 数据集 | 传感器 | 结论摘要 |
|:---|:---|:---|
| **KITTI** | 车载双目 | 多数序列相对误差 $<1\%$；相对 Stereo LSD-SLAM 多数更准；01 高速路近点少，平移略难、旋转仍准；相对单目无尺度漂移，01 可跑通 |
| **EuRoC** | MAV 双目 | 厘米级 RMSE；V2_03 严重模糊会丢跟（可加 IMU） |
| **TUM RGB-D** | Kinect 等 | 相对 ElasticFusion / Kintinuous / DVO / RGB-D SLAM，多数序列平移 RMSE 更优；强调「要最准位姿时 BA 优于 ICP / 光度+深度」，且无需 GPU |

计时：Tracking 均值低于帧周期 → 实时；Local BA / Full BA 随共视密度与环大小变化大。

## 8. 局限与后续脉络

- **稀疏**：无内生稠密网格；要表面需外接深度融合 / MVS。
- **特征依赖**：弱纹理、运动模糊、纯旋转探索仍脆弱（单目更甚）。
- **动态物体、非重叠多相机、鱼眼** 等原文列为未来工作。
- 后续常见延伸：ORB-SLAM3（多地图、视觉–惯性、鱼眼）、各类语义 / 动态 / 稠密前端改写，但仍常以本系统的关键帧 BA + DBoW 闭环为骨架。

与 [ColMap](../2.MVS/ColMap.md) 对照：COLMAP 偏离线 / 批处理 SfM+MVS；ORB-SLAM2 偏在线增量、实时位姿与稀疏地图复用。

## 9. 一句话

**ORB-SLAM2 = 统一 ORB 特征 + 共视图局部 BA + DBoW 闭环，把单目 ORB-SLAM 接到双目/RGB-D：近远立体点给度量尺度，闭环后 Full BA，另有轻量地图定位模式。**
