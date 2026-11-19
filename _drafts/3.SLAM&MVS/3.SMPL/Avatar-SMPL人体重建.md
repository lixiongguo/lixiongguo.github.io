---
layout: post
title: "SMPL 人体参数化及其后续"
categories: [TechSharing]
mathjax: true
---

> 主线：**SMPL**（可微人体模板）→ **SMPLify**（2D 关键优化拟合）→ **HMR**（神经网络直接回归，替代逐图优化）→ 着装扩展：**ClothCap**（4D 扫描分割跟踪）→ **IPNet**（扫描/点云 → 双层隐式 + SMPL+D 配准）→ **Octopus**（图/短视频 → SMPL+顶点位移）→ **Multi-GarmentNet / BCNet**（身体与衣物分层）。  
> 隐式着装人体见 [PIFu 等](几何深度学习-隐式表达.md)；显式网格分析 / TightCap 见 [显式表达](几何深度学习-显示表达.md)；ClothCap 的 MRF 分割见 [MRF 应用 2](../../2.Machine%20Learning/1.机器学习与模式识别/MRF应用2-ClothCap.md)。

---

## SMPL

> Loper et al., *SMPL: A Skinned Multi-Person Linear Model*, SIGGRAPH Asia 2015.

### 在表达什么

一张**固定拓扑**三角网（约 6890 顶点）+ 骨架，用低维参数控制「长什么样」和「摆什么姿势」：

| 参数 | 含义 | 典型维度 |
| :--- | :--- | :--- |
| \(\beta\) | 体型（身高、胖瘦等） | \(\mathbb{R}^{10}\)（常用） |
| \(\theta\) | 姿态（各关节相对旋转） | \(\mathbb{R}^{3K}\)，\(K\) 关节（含根） |
| （可选）平移 / 相机 | 把人放到世界 / 图像里 | — |

输出是 posed 顶点 \(M(\beta,\theta)\)，可直接当 mesh 用，也可驱动服装、算关节。

### 生成公式（直觉）

1. **体型混合形状**：在休息姿态模板 \(\bar T\) 上，用 \(\beta\) 的 PCA 形变加出体型：

$$
T(\beta)=\bar T + B_S(\beta).
$$

2. **姿态相关形变（pose blend shapes）**：关节转动会引起皮肉拧动；用 \(\theta\) 再加一项 \(B_P(\theta)\)，减轻「糖果纸」伪影（相对纯 LBS）。

3. **关节位置**：由体型决定，\(J(\beta)\)。

4. **蒙皮（LBS）**：把 \(T(\beta)+B_P(\theta)\) 上的顶点按蒙皮权重 \(W\) 绑到骨骼变换上，得到最终顶点：

$$
M(\beta,\theta)=\mathrm{LBS}\bigl(T(\beta)+B_P(\theta),\;J(\beta),\;\theta,\;W\bigr).
$$

整条链路对 \(\beta,\theta\) **可微**，所以后面既能「优化拟合」，也能「网络回归 + 反传」。

### 为何成为标准

- 比「只回归关节点」多了**表面**，方便渲染、着装、物理；  
- 比每人扫一个 mesh 更紧凑，且姿态可编辑；  
- 局限：裸体贴身、无衣无发；手脸细节弱 → 后续 **SMPL-X**（脸/手）、**STAR** 等；着装要另加位移层或独立衣物 mesh（下文）。

---

## SMPLify

> Bogo, Kanazawa et al., *Keep it SMPL: Automatic Estimation of 3D Human Pose and Shape from a Single Image*, ECCV 2016.

### 流程：自下而上检测 + 自上而下拟合

```text
RGB 图像
  → CNN（DeepCut 等）估计 2D 关节 J_est
  → 优化 β, θ（及相机），使 SMPL 投影关节对齐 J_est
  → 得到可对齐图像的 3D mesh
```

目标函数大致包括：

- **重投影误差**：模型关节投影 vs 检测 2D 点（可按置信度加权）；  
- **姿态 / 体型先验**：惩罚不自然关节角、极端体型（用数据集统计）；  
- 其它正则（如脚底着地、深度合理性等，视实现而定）。

这是经典的 **「检测 + 生成模型优化」**：SMPL 强约束把病态的单图 3D 问题压成可解优化。

### 代价

单图要跑几十秒量级的非线性优化，难实时；依赖 2D 检测质量；衣物宽松时「衣服下的身体」更歧义。但它把「单图 → SMPL 参数」做成了可用基线，并留下大量可作伪标签的拟合结果。

---

## 用网络代替 SMPLify 优化：HMR

> Kanazawa et al., *End-to-end Recovery of Human Shape and Pose*（常称 **HMR**）, CVPR 2018.  
> 正是「SMPLify 式拟合 → 前馈神经网络」的代表作。

### 想法

不再对每张图做迭代优化，而是：

$$
\text{Image}\;\xrightarrow{\;\mathrm{CNN}\;}\;(\hat\beta,\hat\theta,\hat{\text{camera}}),
$$

端到端吐出 SMPL 参数（及弱透视相机），给定人框后可近实时。

### 训练信号怎么够

仅有野外 2D 关键时，重投影损失**严重欠定**（深度、体型可对冲）。HMR 的关键补充：

1. **关键重投影损失**（可训在只有 2D 标注的图上）；  
2. **对抗先验**：判别器判断 \((\beta,\theta)\) 是否像真实人体网格分布（用大量 3D mesh / MoCap，**不必与图像成对**）；  
3. 有 3D 监督时再加 3D 关节 / 参数损失。

迭代回归模块在特征上多步 refinement，类似「把优化器的几步展开进网络」。

### 和 SMPLify 的关系

| | SMPLify | HMR |
| :--- | :--- | :--- |
| 推理 | 每图优化 | 前馈一次（可再 refine） |
| 速度 | 慢 | 近实时 |
| 先验 | 显式能量项 | 数据驱动 + 对抗 |
| 输入 | 常依赖 2D 关节 | 可直接吃图像特征 |

实践中也常见：**HMR 初始化 → 少量 SMPLify 精修**。后续 **SPIN**（Kolotouros et al.）把「回归 ↔ 优化」在训练环里拧得更紧；**SMPL-X + SMPLify-X** 把手脸一并拟合。记口诀：**SMPLify = 优化拟合；HMR = 学会拟合**。

---

## ClothCap

> Pons-Moll, Pujades, Hu, Black, *ClothCap: Seamless 4D Clothing Capture and Retargeting*, SIGGRAPH 2017.

### 设定

输入是着装人的 **4D 扫描**（高分辨率网格序列，约 60 fps），不是单张 RGB。目标：把**多件衣服彼此分开、与身体分开**，跟踪布料形变，并**重定向**到新体型（虚拟试穿方向）。

### 做法要点

1. 先用（贴身）**SMPL** 对齐扫描，估计衣服下的身体姿态/体型；  
2. **MRF** 等在扫描上做部件分割（上装 / 下装 / 身体等），结合形状与外观；  
3. **多 mesh 模板**分别贴合各服装层，建立跨时间对应；  
4. 导出服装几何与运动，迁移到新的 SMPL 身体上。

相对「单层 SMPL+位移」：ClothCap 强调**分层服装资产**来自真实动态捕获。贵在采集设备与配准；是后来学习式衣物数据集（如 MGN 数据管线）的重要前序思想。

---

## IPNet：扫描 / 点云上的 SMPL 配准

> Bhatnagar et al., *Combining Implicit Function Learning and Parametric Models for 3D Human Reconstruction*（**IP-Net / IPNet**）, ECCV 2020.  
> 项目页：[virtualhumans.mpi-inf.mpg.de/ipnet](https://virtualhumans.mpi-inf.mpg.de/ipnet/) · 代码常与 MPI / RVH 网格配准工具链对照使用。

### 要解决什么问题

着装扫描要挂到 SMPL（或 **SMPL+D**）上，传统管线（工程里常称 **MPI_meshRegister / RVH_MeshRegister** 一类优化配准）大致是：

```text
扫描 → 多视角渲染 → 检 2D/3D 关键
     → 优化 SMPL(+D) 非刚贴合扫描
     → 再估「衣服下的身体」
```

慢、依赖纹理与关键初值、稀疏点云 / 单目深度时更脆。IPNet 的定位：**用一次前馈隐式网络，替掉配准里最难的「找对应 + 猜衣下身体」**，再做轻量优化，得到**可重姿态 / 可改体型**的 SMPL+D。

注意论文用语：隐式抽出来的静表面叫 **reconstruction**；挂到参数模型上叫 **registration**（既解释几何又可编辑）。

### 网络吐什么（双层 + 部位）

输入：着装人的**稀疏点云**（约数千点；也可不完整、单目深度）。编码器沿 **IF-Nets** 思路做多尺度体特征网格。

对任意查询点 \(p\in\mathbb{R}^3\)，联合预测：

1. **三区占据**（不是简单 in/out）：  
   - \(R_0\)：身体内部  
   - \(R_1\)：身体与衣服之间  
   - \(R_2\)：衣服之外  

   两条决策边界 → **内表面 \(S_{\mathrm{in}}\)（衣下身体）** + **外表面 \(S_o\)（着装外形）**。

2. **SMPL 部位标签**（约 14 类）：给后续拟合提供语义对应，减轻「袖子贴到躯干」类局部最小。

部位分类分数还可加权一组**分部位占据头**，减轻手等小区域被躯干点淹没的偏差。

### 配准两步（隐式 → 可编辑）

```text
点云 → IPNet → S_in, S_o, 部位对应
              ↓
         ① 优化 (β,θ,t)：SMPL 贴合 S_in（衣下身体好贴）
              ↓
         ② SMPL+D：在身体拟合基础上非刚位移贴合 S_o / 原扫描
              ↓
         可 re-pose / re-shape 的着装人
```

- ① 内表面接近裸模流形，比直接把 SMPL 往宽松外轮廓上拽稳得多；  
- ② 位移层吃衣、发、脸部细节；部位对应替代「必须很准的 3D 关节」作约束。

完整扫描上：对扫描采样 → 体素/点云送 IPNet → 同上流程，即用前馈预测**简化 MPI/RVH 式逐扫描重优化**。

### 和前后文的关系

| | ClothCap | IPNet | Octopus |
| :--- | :--- | :--- | :--- |
| 输入 | 4D 高分辨率扫描序列 | 稀疏/残缺点云或扫描 | RGB（分割）少数帧 |
| 核心 | MRF 分衣 + 多层跟踪 | 双层隐式 + 部位 → SMPL+D | 图 → \(\beta,\theta,D\) |
| 衣下身体 | 优化估计 | **网络显式预测 \(S_{\mathrm{in}}\)** | 含在 SMPL 里 |
| 可控性 | 捕获资产可 retarget | 配准后可编辑 | 前馈即可编辑 |

训练监督本身仍依赖「优化配准好的」内外表面与部位（论文用多视关键点等做好伪 GT）；**推理时**则用 IPNet 减轻同款工程负担。也可迁到 **MANO** 手部等其他参数模型。

**一句话**：IPNet = **IF-Net 式点云隐式** + **身体/衣服双层** + **SMPL 部位** → 稳健的扫描–SMPL+D 配准，对接并简化 MPI/RVH mesh register 管线。

---

## Octopus

> Alldieck et al., *Learning to Reconstruct People in Clothing from a Single RGB Camera*, CVPR 2019.

### 想法

从**单目短视频少数帧**（也可单帧）恢复个性化着装人体：

$$
\text{语义分割图（多帧）}
\;\to\;
\underbrace{\text{SMPL }(\beta,\theta)}_{\text{身体}}
+\underbrace{\text{顶点位移 }D}_{\text{衣/发/细节}}.
$$

关键设计：

1. **规范 T-pose 空间**预测形状与位移，使多帧特征在**姿态无关**的 latent 里融合；  
2. **Bottom-up + Top-down**：前馈快，但不一定严对齐轮廓 → 再用轮廓 / 关节重投影做 top-down 精修；  
3. 训练主要靠**合成 3D 数据**，推理可吃真实分割。

### 位置

「图像 → SMPL + 每顶点 offset」的代表，比纯 SMPL 多了衣发；但衣与身体仍粘在**同一拓扑**上，难单独换装、难做宽松裙摆大拓扑变化。精度论文报约数毫米级（设定相关），速度远快于早期逐帧优化重建。

---

## Multi-GarmentNet（MGN）

> Bhatnagar et al., *Multi-Garment Net: Learning to Dress 3D People from Images*, ICCV 2019.

### 想法

相对 Octopus 的「单层位移」：**身体与多件服装分层**，每件衣服是可与 SMPL 一起蒙皮、可迁移的 mesh：

$$
C(\theta,\beta,\{D_\ell\})
=
\bigl[\text{皮肤层},\;G_1(\theta,\beta,D_1),\;\ldots,\;G_L(\theta,\beta,D_L)\bigr].
$$

输入常用**多视角语义分割图 + 2D 关节**；网络回归体型/姿态与各衣位移（及衣橱式编码）。扫描侧把衣与身体**分别配准**，才能学到「从图到多层人」的映射。

### 能做什么

- 换装、换体型重定向；  
- 单件衣可进数字衣橱；  
- 比单层位移更接近「真正穿衣服」。  

代价：依赖分割与配准质量；品类受模板库限制。常与 **MGN 数据集**一起被引用（扫描 + SMPL 配准 + 较规整 UV）。

---

## BCNet

> Jiang et al., *BCNet: Learning Body and Cloth Shape from A Single Image*, ECCV 2020.

### 想法

**单张 RGB**（不必多视分割管线）同时估身体与服装。服装不绑死在 SMPL 顶点子集上：

- 每类衣有**独立 mesh + PCA 尺寸空间**（T-pose 下低维 \(\alpha\)）；  
- 与 SMPL **共享姿态 \(\theta\)**，但用网络预测服装自己的**蒙皮权重** \(W_g\)；  
- 再加位移 \(D\) 刻画穿着形变。

这样拓扑可比「SMPL 裁一块当衣服」更自由，对裙等宽松品类更友好。

### 和 MGN / Octopus 对比

| | Octopus | MGN | BCNet |
| :--- | :--- | :--- | :--- |
| 输入 | 单目 1–8 帧分割 | 多视分割+关节 | **单张 RGB** |
| 衣物表示 | SMPL 上位移 | 分层衣模板+位移 | 独立衣模板+学蒙皮 |
| 换装 | 弱（粘连） | 强 | 强（品类内） |
| 宽松衣 | 一般 | 中等 | 相对更好 |

---

## 脉络小结

```text
SMPL（2015）可微人体
    ↓
SMPLify（2016）2D 关节 → 优化 β,θ
    ↓
HMR（2018）图像 → 网络直接回归 β,θ   ←「代替优化」
    ↓
着装 / 配准
  ├─ ClothCap（2017）4D 扫描：MRF 分割 + 多层跟踪
  ├─ IPNet（2020）点云/扫描 → 双层隐式 + SMPL+D 配准（简化 MPI/RVH register）
  ├─ Octopus（2019）图/短视频 → SMPL + 顶点位移
  ├─ MGN（2019）多层可换装
  └─ BCNet（2020）单图身体+独立衣 mesh
```

| 方法 | 输入 | 输出 | 关键词 |
| :--- | :--- | :--- | :--- |
| SMPL | \(\beta,\theta\) | 裸身 mesh | LBS + blend shapes |
| SMPLify | 图 → 2D 关节 | 优化出的 \(\beta,\theta\) | 生成模型拟合 |
| HMR | RGB | 回归 \(\beta,\theta\) | 对抗先验、端到端 |
| ClothCap | 4D 扫描 | 分层衣 + 身体 | MRF 分割、重定向 |
| IPNet | 点云 / 扫描 | \(S_{\mathrm{in}},S_o\) + SMPL+D | 双层隐式、部位对应、配准 |
| Octopus | 单目少数帧 | SMPL + \(D\) | T-pose 融合、bottom-up/top-down |
| MGN | 分割图+关节 | 多层衣橱式 | 可换装 |
| BCNet | 单张 RGB | 身体 + 独立衣 | 学蒙皮、单图 |

**一句话**：SMPL 给出可微的人体「操作系统」；SMPLify 用优化把图挂上去，HMR 用网络学会同款映射；扫描侧 ClothCap 分衣、IPNet 用双层隐式稳住衣下身体并完成 SMPL+D 配准；图像侧再从 Octopus 单层位移走到 MGN / BCNet 可换装多层衣。

---

## 数据集（着装相关）

| 数据集 | 特点 |
| :--- | :--- |
| **MGN** | 扫描质量较好，常带 **SMPL 配准**与较规整 UV；规模相对小，适合多层衣学习 |
| **Cloth3D** | 大规模**合成**着装序列，利于训练动态 / 品类覆盖 |
| **DeepFashion3D** | 大量真实衣物扫描，偏服装几何本身 |
| IPNet 训练 / 评测 | Renderpeople 等着装扫描；衣下身体与部位标签多由优化配准（MPI/RVH 类）做伪监督；也可迁 MANO |

## 问题

高精人体有SMPL参数化表达，但是人体细节太多SMPL表达力不够。
难点：衣物本身薄壳结构难以MVS重建，复杂形态，动态褶皱，样式众多

## 其他参考

[迈向人工智能Fashion Design（一）- 服装制版模拟 - 知乎 (zhihu.com)](https://zhuanlan.zhihu.com/p/29620024)

[人体三维重建（一）——绪论 - 知乎 (zhihu.com)](https://zhuanlan.zhihu.com/p/442488645)