**Step 1：构造 cut graph 与同调路径**

- 欧拉示性数 $\chi=V-E+F$，边界分量数 $n_b$，亏格 $g=(2-\chi-n_b)/2$；
- 在面邻接图上做 spanning tree，每条 **cotree 边**对应一条同调生成环 $\gamma_j$；
- 有多个边界分量时，还需连接各边界分量的路径。路径数 $n_p=2g+n_b-1$（闭曲面 $n_b=0$ 时 $n_p=2g$）。

**Step 2：计算 period 系数 $\mu_j$**

将 $\tilde\phi$ 在 cover 上的值沿有向路径 $\gamma_j$ 积分（离散为边差分之和）：

$$
\mu_j^u(\tilde\phi)=\sum_{e\in\gamma_j}\big(\tilde u(v_b)-\tilde u(v_a)\big),
\mu_j^v(\tilde\phi)=\sum_{e\in\gamma_j}\big(\tilde v(v_b)-\tilde v(v_a)\big).
$$

全局连续要求 $\mu_j(\phi)\in\mathbb Z$；若要求**纯四边形网格**（分支点落在格点而非格心），则需 $\mu_j(\phi)\in 2\mathbb Z$。

**Step 3：harmonic 修正 $\psi$**

令目标 period 为舍入值

$$
\Delta\mu_j = \mathrm{round}_{2\mathbb Z}\big(\mu_j(\tilde\phi)\big)-\mu_j(\tilde\phi),
$$

在 cover 上构造 harmonic 基 $\{h_j\}$，满足 $\mu_k(h_j)=\delta_{kj}$（通过 KKT 系统：$\Delta h_j=0$ 且 period 约束）。令

$$
\psi=\sum_j \Delta\mu_j\, h_j, \phi=\tilde\phi+\psi.
$$

对 $u,v$ 分量分别做上述修正，则修正后 period 落入 $2\mathbb Z$，参数线全局无缝。

**Step 4：投影回原曲面（Phase 6）**

- 普通顶点（$ls=0$）：取 sheet $0$ 上的 cover UV；
- 分支顶点（$ls\neq 0$）：对所有 sheet preimage 的 UV 取平均；
- 最后将 $(u,v)$ 线性归一化到 $[0,1]^2$。



![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20251204204913972.png)

![](https://lgximgs.oss-cn-beijing.aliyuncs.com/images/image-20251204204942930.png)