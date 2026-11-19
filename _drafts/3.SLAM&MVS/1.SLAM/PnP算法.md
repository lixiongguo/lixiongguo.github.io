# PnP 算法：P3P、EPnP 与 OpenCV `solvePnP`

> 前置：[相机模型 / 透视投影](相机模型.md)。记号与 OpenCV calib3d 一致：世界点 $P_w$、像素 $p$、内参 $A$（亦记 $K$）、外参 $[R\mid t]$。

**Perspective-n-Point (PnP)**：已知相机内参，以及 $n$ 组**世界三维点**与其**图像二维投影**的对应，估计相机相对世界坐标系的位姿 $(R,t)\in\mathrm{SE}(3)$。它是视觉定位、AR、SLAM 跟踪与标定中最常用的位姿求解器之一。

---

## 1. 问题形式

给定：

- 内参 $A$（及可选畸变系数；实践中常先把像素反投影到归一化平面）；
- 对应 $\{(P_i,\,p_i)\}_{i=1}^n$，其中 $P_i=(X_i,Y_i,Z_i)^\top$ 在**物体/世界系**，$p_i=(u_i,v_i)^\top$ 为像素。

求 $R\in\mathrm{SO}(3)$、$t\in\mathbb{R}^3$，使投影残差最小。无畸变针孔模型下：

$$
s_i\begin{bmatrix}u_i\\v_i\\1\end{bmatrix}
=
A\begin{bmatrix}R\mid t\end{bmatrix}
\begin{bmatrix}P_i\\1\end{bmatrix},
\qquad s_i>0.
\tag{1}
$$

或先归一化：$\tilde{p}_i=A^{-1}(u_i,v_i,1)^\top$，再在归一化像平面上拟合

$$
\tilde{p}_i \;\propto\; R P_i + t.
\tag{2}
$$

非线性最小二乘形式（重投影误差）为

$$
\min_{R,t}\sum_{i=1}^{n}
\Bigl\|
\pi\bigl(A(RP_i+t)\bigr)-p_i
\Bigr\|_2^2,
\tag{3}
$$

其中 $\pi(X,Y,Z)=(X/Z,\,Y/Z)$。实用流程几乎总是：**代数/几何方法求初值** → **（可选）RANSAC 剔外点** → **LM 精化**。

### 自由度与最少点数

| 未知量 | 自由度 |
| :--- | ---: |
| 旋转 $R$ | 3 |
| 平移 $t$ | 3 |
| **合计** | **6** |

每对 2D–3D 对应提供 2 个独立约束（像素的 $u,v$），故一般至少需要 **$n=3$** 即可有限多解；**$n\ge 4$** 时通常唯一（一般位置）。$n=3$ 的算法族称 **P3P**；$n$ 较大时常用 **EPnP**、IPPE、SQPnP 等做 $O(n)$ 初值。

### 与相关问题的区别

| 问题 | 已知 | 求解 |
| :--- | :--- | :--- |
| **PnP** | $K$ + 3D–2D | $(R,t)$ |
| **相对位姿 / 本质矩阵** | $K$ + 2D–2D（两视图） | 相对 $R,t$（尺度不定） |
| **DLT 单应** | 平面上 3D–2D 或 2D–2D | $H$；平面场景可再分解出位姿 |
| **绝对方位 (P$n$P 无 $K$)** | 仅 3D–2D | 内参+外参，需更多点 |

---

## 2. P3P：三点透视

**P3P** 是最小求解器：用 **3** 对对应求有限个候选位姿，常嵌在 RANSAC 内；第 4 点用于消歧。

### 2.1 几何图景

记相机光心为 $O$，三个世界点 $A,B,C$。已知边长 $AB,BC,CA$（由世界坐标算出）及图像上的方向（归一化射线）。三角形 $OAB$、$OBC$、$OCA$ 共享边 $OA,OB,OC$，形成**三个边长未知、顶角由图像射线夹角固定**的三角形。

令

$$
\begin{aligned}
a&=\|B-C\|,\quad b=\|A-C\|,\quad c=\|A-B\|,\\
\cos\alpha&=\langle \hat{u}_B,\hat{u}_C\rangle,\quad
\cos\beta=\langle \hat{u}_A,\hat{u}_C\rangle,\quad
\cos\gamma=\langle \hat{u}_A,\hat{u}_B\rangle,
\end{aligned}
$$

其中 $\hat{u}_A,\hat{u}_B,\hat{u}_C$ 为归一化图像射线。设未知深度 $x=\|OA\|$、$y=\|OB\|$、$z=\|OC\|$，由余弦定理：

$$
\begin{aligned}
a^2 &= y^2+z^2-2yz\cos\alpha,\\
b^2 &= x^2+z^2-2xz\cos\beta,\\
c^2 &= x^2+y^2-2xy\cos\gamma.
\end{aligned}
\tag{4}
$$

这是关于 $(x,y,z)$ 的二次方程组，经典消元可化为**一元四次方程**，最多 **4** 组正解（深度为正）。每组深度确定 $A,B,C$ 在相机系下的坐标后，再与世界坐标做 **绝对定向**（Kabsch / SVD）得 $R,t$。

### 2.2 常用实现

| 方法 | 要点 |
| :--- | :--- |
| **Gao et al. 2003** | 经典代数消元 + 四次方程；OpenCV 早期默认之一 |
| **Kneip et al. 2011** | 更稳的几何推导，避免部分退化；OpenCV `SOLVEPNP_P3P` |
| **Ke & Roumeliotis 2017** | 另类代数形式；`SOLVEPNP_AP3P`，噪声下常更稳 |

**消歧**：第四点重投影误差最小的候选保留；RANSAC 中则看内点最多者。

**退化**：三点共线、光心落在三点所在平面、或夹角过小导致数值病态时，P3P 失败或出现假解——实践中配合第 4 点与 RANSAC。

---

## 3. EPnP：$O(n)$ 的高效非迭代法

**EPnP**（Efficient PnP，Lepetit, Moreno-Noguer, Fua, IJCV 2009）是应用最广的**多点**初值算法：复杂度 **$O(n)$**，通常用 $n\ge 4$（推荐 $\ge 6$），把位姿估计化为对**四个控制点**坐标的线性系统。

### 3.1 核心思想

任意世界点写成四个**控制点** $C_j^w\in\mathbb{R}^3$（$j=1,\ldots,4$）的仿射组合：

$$
P_i^w=\sum_{j=1}^{4} \alpha_{ij}\, C_j^w,
\qquad \sum_{j=1}^{4}\alpha_{ij}=1.
\tag{5}
$$

$\alpha_{ij}$ 由世界坐标唯一确定（对每个 $P_i$ 解 $4\times 4$ 小系统）。同一组权重在相机系下仍成立：

$$
P_i^c=\sum_{j=1}^{4} \alpha_{ij}\, C_j^c.
\tag{6}
$$

于是未知量从「整条轨迹上的 $R,t$」收缩为 **12 个标量**（四个控制点的相机坐标 $C_j^c\in\mathbb{R}^3$）。

### 3.2 线性系统

将 (6) 代入投影方程，整理后得到关于控制点坐标的齐次线性方程

$$
M\begin{bmatrix}C_1^c\\\vdots\\C_4^c\end{bmatrix}=\boldsymbol{0},
\tag{7}
$$

$M$ 为 $2n\times 12$ 矩阵（每点贡献两行）。解落在 $M$ 的零空间；维数通常为 1–4，记基为 $\{v_k\}$，则

$$
\begin{bmatrix}C_1^c\\\vdots\\C_4^c\end{bmatrix}
=\sum_{k=1}^{N} \beta_k v_k,
\qquad N\le 4.
\tag{8}
$$

再用控制点之间的**距离约束**（世界系已知 $\|C_i^w-C_j^w\|$）对 $\beta$ 建二次约束，得到小规模非线性问题（$N\le 4$），可闭式或极小二次求解。最后由 $\{C_j^w\}\leftrightarrow\{C_j^c\}$ 做一次 SVD 绝对定向得 $R,t$。

### 3.3 性质与注意点

- **优点**：对大 $n$ 极快；实现成熟（OpenCV `SOLVEPNP_EPNP`）。
- **精化**：原文建议再用 Gauss–Newton 最小化重投影误差（OpenCV 的 `solvePnP` 可加 `flags` 后接 `solvePnPRefineLM`）。
- **平面场景**：四点共面时控制点选取与零空间维数需特殊处理；平面位姿更常用 **IPPE**（见下）。
- **外点敏感**：EPnP 本身是全数据最小二乘型，**必须**外裹 RANSAC（`solvePnPRansac`）。

---

## 4. 其他常用求解器（对照）

| 算法 | 适用 | 复杂度 / 备注 |
| :--- | :--- | :--- |
| **P3P / AP3P** | $n=3$（+第 4 点验证） | 最小解；RANSAC 假设生成器 |
| **EPnP** | $n\ge 4$ | $O(n)$；通用默认初值 |
| **DLT / 直接线性变换** | $n\ge 6$ | 估计 $3\times 4$ 投影矩阵再 RQ 分解；噪声下不如 EPnP |
| **IPPE** | **共面**点，$n\ge 4$ | 平面位姿两解，再选优；标定时常用 |
| **SQPnP** | 一般 $n$ | 全局最优二次松弛，更慢更稳 |
| **迭代 LM** | 有好初值 | 精化 (3)，不单独当最小解 |

逻辑关系可以记为：

```text
最小样本 (RANSAC 内)     多数内点上的初值        精化
   P3P / AP3P      →     EPnP / IPPE / SQPnP  →   LM / VVS
```

---

## 5. OpenCV：`solvePnP` 与 `solvePnPRansac`

### 5.1 接口要点

```cpp
bool solvePnP(objectPoints, imagePoints, cameraMatrix, distCoeffs,
              rvec, tvec, useExtrinsicGuess, flags);

bool solvePnPRansac(..., rvec, tvec, ..., flags, /* RANSAC 参数 */);

void solvePnPRefineLM(...);   // 在已有 rvec,tvec 上 LM 精化
```

- `objectPoints`：世界/物体系 3D 点（`CV_64F` / `CV_32F`，$N\times 3$ 或 `vector<Point3f>`）。
- `imagePoints`：对应像素。
- `cameraMatrix`：内参 $A$；$`distCoeffs`$ 非空时内部先去畸变。
- `rvec`：旋转向量（Rodrigues），与 $R$ 等价；$`tvec`$ 为 $t$。
- **约定**：得到的是把**物体点变到相机系**的变换：$P_c = R P_w + t$（与 [相机模型](相机模型.md) 中 ${}^{c}T_w$ 一致）。

### 5.2 `flags` 常用取值

| 标志 | 算法 |
| :--- | :--- |
| `SOLVEPNP_ITERATIVE` | 有初值时的 LM；若 `useExtrinsicGuess=false` 则先用线性法初值再迭代 |
| `SOLVEPNP_EPNP` | EPnP |
| `SOLVEPNP_P3P` | Kneip P3P（需恰好 4 个点：3 求姿态 + 1 验证） |
| `SOLVEPNP_AP3P` | Ke 的 AP3P |
| `SOLVEPNP_IPPE` / `SOLVEPNP_IPPE_SQUARE` | 共面 / 正方形标记 |
| `SOLVEPNP_SQPNP` | SQPnP（较新版本） |

经验建议：

1. **一般场景、点多**：`solvePnPRansac` + `SOLVEPNP_EPNP`（或默认），再 `solvePnPRefineLM`。
2. **RANSAC 假设步**：内层用 `SOLVEPNP_P3P` / `AP3P`（每次抽 4 点）。
3. **平面标定板 / AprilTag**：`IPPE` 或 `IPPE_SQUARE`。
4. 已有上一帧位姿：`useExtrinsicGuess=true` + `ITERATIVE`，作时序跟踪的局部精化。

### 5.3 与 Python 的对应

```python
ok, rvec, tvec = cv2.solvePnP(obj, img, K, dist, flags=cv2.SOLVEPNP_EPNP)
ok, rvec, tvec, inliers = cv2.solvePnPRansac(obj, img, K, dist, flags=cv2.SOLVEPNP_EPNP)
rvec, tvec = cv2.solvePnPRefineLM(obj, img, K, dist, rvec, tvec)
R, _ = cv2.Rodrigues(rvec)
```

---

## 6. 实践要点（SLAM / 定位）

1. **坐标系**：明确 3D 点是世界系还是物体系；OpenCV 输出的是「物体 → 相机」。SLAM 地图点通常在世界系，得到的即世界到相机的 $(R,t)$，取逆得相机轨迹 $T_{wc}$。
2. **尺度**：PnP 用的是**度量** 3D 点，尺度已由地图/标定给出；与纯视觉两视图不同，**无尺度歧义**。
3. **外点**：匹配误对应极常见，生产代码几乎总用 `solvePnPRansac`；内点阈值再 LM。
4. **共面**：地面、墙面、标定板上点共面时，优先 IPPE，避免 EPnP 共面退化。
5. **数值**：3D 点相对相机深度跨度极大或点团成一线时病态；可做点归一化或检查条件数。
6. **与 BA 的关系**：跟踪线程用 PnP 实时求当前帧位姿；后端再把位姿与地图点放进重投影 BA 联合优化——PnP 是「单帧固定地图」的特例。

---

## 7. 小结

| 关键词 | 含义 |
| :--- | :--- |
| **PnP** | 已知 $K$ 与 3D–2D 对应，求 $(R,t)$ |
| **P3P** | $n=3$ 最小解，至多 4 候选；RANSAC 利器 |
| **EPnP** | 控制点参数化，$O(n)$ 初值；OpenCV 默认主力之一 |
| **`solvePnP`** | OpenCV 统一入口：选 flags 切换算法，常与 RANSAC + LM 精化串联 |

**公式主线**：投影模型 (1)–(3) → P3P 余弦定理 (4) → EPnP 控制点 (5)–(8) → 绝对定向得 $R,t$ → 重投影 LM。

---

## 参考文献

- Lepetit V., Moreno-Noguer F., Fua P. *EPnP: An Accurate O(n) Solution to the PnP Problem*. IJCV, 2009.
- Gao X.-S., et al. *Complete Solution Classification for the Perspective-Three-Point Problem*. IEEE TPAMI, 2003.
- Kneip L., Scaramuzza D., Siegwart R. *A Novel Parametrization of the Perspective-Three-Point Problem for a Direct Computation of Absolute Camera Position and Orientation*. CVPR, 2011.
- Ke T., Roumeliotis S. *An Efficient Algebraic Solution to the Perspective-Three-Point Problem*. CVPR, 2017.
- Collins T., Bartoli A. *Infinitesimal Plane-Based Pose Estimation (IPPE)*. IJCV, 2014.
- OpenCV：[`solvePnP`](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html#ga549c2075fac14897bbd13c5ada8dd673) / [`solvePnPRansac`](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html#ga50620f0e26e02caa2e9adc07b5fbf24e).
