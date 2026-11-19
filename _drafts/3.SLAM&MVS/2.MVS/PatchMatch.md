# PatchMatch（与 PatchMatch Stereo）

> 图像编辑原型：Connelly Barnes et al., *PatchMatch: A Randomized Correspondence Algorithm for Structural Image Editing*, SIGGRAPH 2009.  
> 立体匹配：Michael Bleyer, Christoph Rhemann, Carsten Rother, *PatchMatch Stereo — Stereo Matching with Slanted Support Windows*, BMVC 2011.  
> 多视图延伸：Gipuma、COLMAP dense、ACMM 等；学习版见 [PatchMatchNet.md](PatchMatchNet.md)。

**PatchMatch** 本意是随机近邻场算法；在立体 / MVS 里被改造成「每像素维护一个（倾斜）平面假设，靠传播与随机 refine 搜索」，从而**不必扫满整段视差 / 深度**，显存与假设空间近似解耦。

## 1. 从图像编辑到立体

Barnes 的 PatchMatch 解决：在图像 $A$ 中为每个 patch 在图像 $B$ 找近似最近邻。核心循环：

1. **随机初始化**偏移场；
2. **传播**：邻居的好偏移很可能也适合当前像素；
3. **随机搜索**：在当前偏移附近指数缩小半径随机试探。

立体里「近邻」变成「使匹配代价最低的平面 / 深度」。大块表面往往共享相近几何，因此**区域里只要有一个像素猜对，传播就能铺开**——这是 PatchMatch Stereo 能工作的统计前提。

## 2. 正视窗口的偏见

局部立体常用固定窗口在整数视差上滑动，隐含假设：**窗口内视差恒定且正视（fronto-parallel）**。对倾斜面会：

- 把一块斜面拆成许多阶梯状正视片；
- 亚像素与斜面细节变差。

PatchMatch Stereo 的对策：为每个像素 $p$ 估计一张 **3D 平面** $f_p$，把支持窗投影到该平面上再算匹配代价——支持域可倾斜、可连续视差。

平面常用形式（左图坐标 $(x,y)$，视差 $d$）：

$$
d = a_f x + b_f y + c_f,
$$

或等价的「一点 + 法向」再转成 $(a,b,c)$。

## 3. 匹配代价（倾斜支持窗）

对像素 $p$、候选平面 $f$，在倾斜窗内聚合光度代价（常配 **adaptive support weights**：颜色相近、距离近则权重大，减轻跨边界污染）：

$$
m(p,f)
= \sum_{q\in W_p}
w(p,q)\,
\rho\bigl(I_L(q),\, I_R(q_f)\bigr),
$$

其中 $q_f$ 是把 $q$ 按平面 $f$ 投到右图的对应点，$\rho$ 为绝对差 / Census 等。目标：找 $f_p=\arg\min_f m(p,f)$。平面空间连续且无穷，穷举不可行 → 用 PatchMatch 式近似搜索。

## 4. 推理循环（Bleyer 2011）

左右视图各自维护平面场，迭代若干次。每次对每个像素大致做：

### 4.1 随机初始化

不为 $(a,b,c)$ 直接乱采样（空间不均匀）。更稳的做法：

1. 在允许视差范围内随机取 $z_0$，得点 $P=(x_0,y_0,z_0)$；
2. 随机单位法向 $\mathbf{n}$；
3. 转成平面参数。

希望：同一连通表面上至少一个像素的初值接近真平面，随后靠传播扩散。

### 4.2 Spatial propagation

邻居 $q$ 的平面 $f_q$ 很可能也适合 $p$。若

$$
m(p,f_q) < m(p,f_p),
$$

则接受 $f_p\leftarrow f_q$。扫描顺序常用蛇形 / 红黑棋盘（便于并行，如 Gipuma）。

### 4.3 View propagation

左右视差场强相关：把左图平面投到右图对应像素（或反之），若代价更低则接受。同时服务左右一致性。

### 4.4 Temporal propagation（可选）

视频立体时，从前 / 后帧传播平面假设。

### 4.5 Plane refinement

在当前「点 + 法向」表示上下扰动：视差与法向加随机增量，接受使 $m$ 下降的扰动；增量半径指数缩小，类似原版 PatchMatch 的 random search，逼近局部最优平面（亚像素）。

### 4.6 后处理

左右一致性检查剔遮挡；中值滤波等填洞。倾斜窗也可用来填代价体，再交给全局方法（兼顾大块无纹理与遮挡建模）。

## 5. 多视图立体中的谱系

| 方法 | 角色 |
|:---|:---|
| **Gipuma** | 多视图 PatchMatch；红黑并行传播；GPU |
| **COLMAP dense** | 像素级选视图 + 深度 / 法向联合；几何一致性 |
| **ACMM** | 自适应棋盘采样、多假设选视图、多尺度几何一致性 |
| **PatchmatchNet** | 可学习自适应传播 / 评价，级联粗到细；不再显式倾斜平面以省显存 |

共同哲学：**用空间相干性换穷举**；与 MVSNet「稠密代价体 + 3D CNN」相对。

## 6. 复杂度与直觉

- 每像素每迭代只评价少量候选平面（邻居 + 随机扰动），相对 $O(WHD)$ 的全视差扫描更轻。  
- 质量依赖：初值覆盖、传播是否跨边界、匹配度量对光照 / 弱纹理是否稳健。  
- 倾斜平面对大斜面友好；圆曲面是局部平面近似，实践中往往仍够用。

## 7. 与深度学习的接口

- DeepPruner：可微 PatchMatch 剪枝视差后再建薄代价体。  
- PatchmatchNet：传播偏移与评价窗口可学习，见 [PatchMatchNet.md](PatchMatchNet.md)。  
- MVSNet 系：仍可把 PatchMatch 深度作初值或后处理对照。

## 8. 一句话

**随机猜平面 → 向邻居 / 另一视角传播好的假设 → 局部随机 refine**：用空间相干性在无穷平面空间里做近似最近邻搜索，摆脱正视窗口偏见。
