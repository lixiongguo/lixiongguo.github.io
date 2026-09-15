## Voronoi 图：空间划分的基础

给定平面上 $n$ 个点（称为**站点**或 **sites**）$S = \{s_1, s_2, \ldots, s_n\}$，Voronoi 图将平面划分为 $n$ 个** Voronoi 单元（Cell）**：

$$
V(s_i) = \{ p \in \mathbb{R}^2 : d(p, s_i) \leq d(p, s_j), \forall j \neq i \}
$$
即 $V(s_i)$ 是平面上所有"距离 $s_i$ 最近"的点的集合。每个 Voronoi 单元是一个**凸多边形**。

| 性质 | 说明 |
|:---|:---|
| **凸性** | 每个 Voronoi 单元都是凸多边形 |
| **最近邻查询** | 点 $p$ 落在哪个单元，哪个站点就是 $p$ 的最近邻 |
| **$n$ 个站点 → $O(n)$ 条 Voronoi 边 → $O(n)$ 个 Voronoi 顶点** | 欧拉公式保证：$V - E + F = 2$ |
| **Voronoi 顶点** | 每个顶点同时等距于至少 3 个站点（即外接圆心） |

最直观的方法：对每个站点，计算它到所有其他站点的**垂直平分线（Bisector）**，然后求所有半平面的交集。每个站点需要 $O(n \log n)$ 求交，$n$ 个站点总计 $O(n^2 \log n)$。这太慢了。我们需要更高效的方法。

Fortune（1987）算法使用一条**从上到下移动的扫描线**来高效构建 Voronoi 图。它的精妙之处在于：不直接比较站点之间的距离，而是通过一条**海滩线（Beach Line）**间接维护距离关系。

### 2.2 海滩线与抛物线

**抛物线定义**：给定一个焦点 $s_i$ 和一条准线（扫描线 $y = y_L$），满足"到焦点距离 = 到准线距离"的点的轨迹是一条抛物线。

$$
\text{Parabola}_{s_i}: \sqrt{(x - x_i)^2 + (y - y_i)^2} = y_L - y
$$
**海滩线**是所有已发现站点的抛物线的"下包络"（lower envelope）：
$$
\text{BeachLine}(x) = \min_{s_i \in S_{\text{above}}} \text{Parabola}_{s_i}(x)
$$
海滩线有一个极为重要的性质：

> **海滩线上的每个点，到最近的上方站点和到扫描线的距离相等。**

这意味着：**如果两个站点的抛物线在海滩线上相交，交点恰好是这两个站点的 Voronoi 边与海滩线的交汇处**。因此，沿着海滩线追踪交点的移动轨迹，就能得到 Voronoi 边。

![image-20260714194211678](/Users/lgxgeogo/Desktop/MyDoc/lixiongguo.github.io/imgs//image-20260714194211678.png)

Fortune 算法只处理两种事件：

**① 站点事件（Site Event）**

当扫描线到达一个新的站点 $s_i$ 时触发。

```
处理站点事件(s_i):
  1. 在海滩线上找到 x 坐标最接近 s_i 的弧段 arc
  2. 将 arc 分裂为左弧 arc_left 和右弧 arc_right
  3. 在两者之间插入 s_i 的新弧段 arc_new
  4. 新增两个 breakpoint（Voronoi 边的生长起点）
  5. 检查 arc_left 和 arc_new 之间、arc_new 和 arc_right 之间
     是否形成有效的圆事件
```

**② 圆事件（Circle Event）**

当三个相邻弧段对应的抛物线收缩到一个公共点时触发——这个点就是 Voronoi 顶点。

```
处理圆事件(arc_middle):
  1. 从海滩线中删除中间弧段 arc_middle
  2. 新增一个 Voronoi 顶点（两条 Voronoi 边的交点）
  3. 合并左右弧段的 breakpoint，产生一条新的 Voronoi 边
  4. 检查合并后的相邻弧段是否形成新的有效圆事件
```

> **直觉**：圆事件意味着中间站点的"领地"被左右两个邻居彻底挤掉了。被挤掉的那个点恰好是三个站点的**外接圆最低点**。

数据结构：事件队列用优先队列（最小堆），按事件 $y$ 排序，插入/删除 $O(\log n)$；海滩线用平衡 BST（如红黑树），叶节点为弧段、内部节点为 breakpoint（Voronoi 边），查找与更新 $O(\log n)$；已确定的边与顶点用 DCEL 存储，边插入 $O(1)$。

复杂度：时间 $O(n\log n)$，空间 $O(n)$：站点事件 $n$ 个，有效圆事件 $O(n)$，每事件对 BST 做常数次 $O(\log n)$ 操作。

退化情况：同高站点按 $x$ 次序处理；四点及以上共圆时 Voronoi 顶点度 $>3$，需合并圆事件；三点共线则外接圆退化、无圆事件；重合站点预处理去重。



## Delaunay 三角剖分

给定平面上 $n$ 个点的点集 $P$，Delaunay 三角剖分是满足**空圆性质**的三角剖分：

> 对于三角剖分中的每一个三角形 $\triangle p_i p_j p_k$，其外接圆的**严格内部**不包含 $P$ 中的任何其他点。

等价定义（Delaunay 边）：

> 一条边 $e = (p_i, p_j)$ 是 Delaunay 边，当且仅当存在一个通过 $p_i$ 和 $p_j$ 的圆，其内部不包含 $P$ 中任何其他点。


### 关键性质

| 性质 | 说明 |
|:---|:---|
| **空圆性** | 每个三角形的外接圆为空（定义性质） |
| **最大化最小角** | 在所有三角剖分中，Delaunay 三角剖分使最小内角最大化 |
| **唯一性** | 无四点共圆时唯一；四点共圆时可翻转对角线 |
| **凸包** | 外层边界构成点集的凸包 |
| **最近邻** | 每个点的最近邻一定是其 Delaunay 邻居 |
| **对偶性** | 与 Voronoi 图互为对偶（见下一节） |
| **Lifting 性质** | Delaunay = 抬升点三维凸包的**下投影**（见下） |

### 3.2 Growing Circle（扩张圆）直觉

空圆性质可用**扩张圆（growing / expanding circle）**来读：圆心沿边的垂直平分线移动，圆始终穿过两端点，半径随之增大，直到「碰到」第三个站点为止。

**边是否为 Delaunay。** 固定 $p_i,p_j$，过这两点的圆，其圆心必在线段 $p_ip_j$ 的**垂直平分线**上。取以 $p_ip_j$ 为直径的圆作为最小者（圆心为中点），沿平分线向某一侧连续移动圆心——此即一串**growing circle**：

1. 圆始终过 $p_i,p_j$，内部起初通常为空（或至少直径圆是候选）；
2. 半径增大，直到圆周**首次碰到**另一个站点 $p_k$；
3. 若在碰触瞬间圆的**内部仍不含**其他点，则 $(p_i,p_j)$ 满足空圆边定义，因而是 **Delaunay 边**；同时 $\triangle p_i p_j p_k$ 的外接圆即为该停滞时刻的圆，故该三角形也是 Delaunay 三角形。

向平分线**另一侧**再做一次扩张，通常会碰到另一点 $p_\ell$，对应共享边 $p_ip_j$ 的另一个相邻三角形（内部边两侧各一）。

**三角形外接圆。** 对已是 Delaunay 的三角形，其外接圆可视为扩张过程的**终止态**：圆「卡住」在三个站点上，且内部空——这正是本节开头的空圆定义。若扩张尚未到第三点时内部已「吞进」某点，则该候选边/三角形不合法，需翻边或在 Bowyer–Watson 中被标为坏三角形。

<img src="/Users/lgxgeogo/Desktop/MyDoc/lixiongguo.github.io/imgs//image-20260714203718725.png" alt="image-20260714203718725" style="zoom:50%;" />

**与 Voronoi 的衔接。** 扩张圆的圆心始终在 $p_ip_j$ 的垂直平分线上，而该平分线正是站点 $p_i,p_j$ 之间的 **Voronoi 边**所在直线。圆停在第三点 $p_k$ 时，圆心同时等距于 $p_i,p_j,p_k$，即落在第三条平分线上——三点外心，也就是 **Voronoi 顶点**。因此：
$$
\text{growing circle 卡住三国点}
\;\Longleftrightarrow\;
\text{空外接圆}
\;\Longleftrightarrow\;
\text{Delaunay 三角形}
\;\Longleftrightarrow\;
\text{一个 Voronoi 顶点}.
$$

四点共圆时，同一圆心处「同时」碰上第四点，扩张在两侧终止圆重合。

### Lifting 性质（抛物面提升）

空圆性看起来像二维判定，但可通过一次坐标变换变成三维凸包。想法是：把每个平面点**竖直抬高**到抛物面上，使「是否在圆内」变成「是否在某张平面的下方」——后者正是凸包下侧面的定义。

**提升映射。** 对 $p=(x,y)$ 令
$$
\hat{p}=\bigl(x,\;y,\;x^2+y^2\bigr),
$$
即抬到旋转抛物面 $z=x^2+y^2$ 上；点集 $P$ 提升为 $\hat{P}$。

**结论（下投影）。** 对 $\hat{P}$ 求三维凸包 $\mathrm{CH}(\hat{P})$，只保留**下包络**（从 $z=-\infty$ 往上看得到的那些面，记为 $\partial_{-}\mathrm{CH}$），再沿 $z$ 方向投影回 $xy$ 平面——得到的三角剖分恰为 Delaunay：

$$
\boxed{\mathrm{Delaunay}(P)=\pi_{xy}\!\bigl(\partial_{-}\mathrm{CH}(\hat{P})\bigr)},
\qquad \pi_{xy}:(x,y,z)\mapsto(x,y).
$$

无四点共圆时，每个下三角面一一对应一个 Delaunay 三角形。上包络的投影则是**最远点 Delaunay**（对偶于最远点 Voronoi），与日常最近邻 Delaunay 不是同一对象。

构造管道：抬升 → 3D 凸包 → **只要下面、丢掉上面** → 投影回 2D；复杂度 $O(n\log n)$。

![image-20260714194923763](../../../imgs//image-20260714194923763.png)

<img src="/Users/lgxgeogo/Desktop/MyDoc/lixiongguo.github.io/imgs//image-20260714195237033.png" alt="image-20260714195237033" style="zoom:50%;" />

**为何圆变成平面。** 平面上的圆
$$
(x-a)^2+(y-b)^2=r^2
$$
展开为 $x^2+y^2-2ax-2by+(a^2+b^2-r^2)=0$。在抛物面上用 $z$ 替换 $x^2+y^2$，立刻得到**线性方程**
$$
z-2ax-2by+c=0,\qquad c=a^2+b^2-r^2,
$$
即三维中一张平面 $\Pi$。反过来，不平行于 $z$ 轴的平面与抛物面相交，交线投影回 $xy$ 仍是圆（或退化成直线）。因此：

| 平面上 | 抬升后 |
|:---|:---|
| $q$ 在圆**内** | $\hat{q}$ 在 $\Pi$ **下方**（$z$ 更小） |
| $q$ 在圆**外** | $\hat{q}$ 在 $\Pi$ **上方** |
| $q$ 在圆周上 | $\hat{q}$ 落在 $\Pi$ 上（四点共圆 $\Leftrightarrow$ 四点抬升共面） |

**空圆何以等于下侧面。** 取候选三角形 $\triangle p_ip_jp_k$，其三抬升点张成平面 $\Pi$。若外接圆**内部不含**其他点，则一切其余 $\hat{q}$ 都在 $\Pi$ 上方——从下方看，$\hat{p}_i\hat{p}_j\hat{p}_k$ 没有被别的点挡住，正是凸包的一张**下侧面**。投影回去就是 Delaunay 三角形。若有点落在圆内，对应抬升点会戳到 $\Pi$ 下方，该面不可能出现在下包络上。

![image-20260714195957273](/Users/lgxgeogo/Desktop/MyDoc/lixiongguo.github.io/imgs//image-20260714195957273.png)

**InCircle 谓词 = 三维定向。** 判定第四点是否在外接圆内，可用
$$
\mathrm{InCircle}(p_i,p_j,p_k,q)
=
\det\begin{bmatrix}
x_i&y_i&x_i^2+y_i^2&1\\
x_j&y_j&x_j^2+y_j^2&1\\
x_k&y_k&x_k^2+y_k^2&1\\
x_q&y_q&x_q^2+y_q^2&1
\end{bmatrix}.
$$
这恰是四面体 $(\hat{p}_i,\hat{p}_j,\hat{p}_k,\hat{q})$ 的有向体积：符号告诉你 $\hat{q}$ 在 $\Pi$ 哪一侧，为零则四点抬升共面（共圆）。故空圆检验就是一次 3D orient；许多库把 Delaunay 直接当作凸包算法的副产品。

**附带读法。** Lawson 翻边：四边形两条对角线中，落在下表面上的那条才是 Delaunay，另一条抬升后沉入凸包内部。后文 Voronoi 对偶也可由此读出——下侧面所对应圆的圆心（圆参数 $(a,b)$）正是外心，也即 Voronoi 顶点。

