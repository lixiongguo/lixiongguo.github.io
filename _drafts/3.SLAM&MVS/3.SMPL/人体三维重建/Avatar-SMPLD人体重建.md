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



## IPNet：扫描 / 点云上的 SMPL 配准

> Bhatnagar et al., *Combining Implicit Function Learning and Parametric Models for 3D Human Reconstruction*（**IP-Net / IPNet**）, ECCV 2020.  
> 项目页：[virtualhumans.mpi-inf.mpg.de/ipnet](https://virtualhumans.mpi-inf.mpg.de/ipnet/) · 代码常与 MPI / RVH 网格配准工具链对照使用。

![屏幕截图12](../../../imgs/屏幕截图12-1795079134512-16.png)

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
