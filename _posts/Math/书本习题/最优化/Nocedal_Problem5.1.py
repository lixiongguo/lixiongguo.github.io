"""
Problem 5.1
===========
实现标准的 Conjugate Gradient (CG) 方法，用于求解线性方程组 Ax = b。

其中：
    A 为 Hilbert 矩阵：A[i][j] = 1 / (i + j + 1)   (0-based 索引)
    b 为全 1 向量。
    x0 = 0（初始点取全零向量）。

对 n = 5, 8, 12, 20 分别进行测试。


==================================================================
解题报告
==================================================================

一、算法：标准 Conjugate Gradient (CG)
------------------------------------------------------------------
CG 用于求解对称正定 (SPD) 线性方程组 Ax = b，核心迭代如下：

    r0 = b - A x0 ;  p0 = r0 ;  rs_old = r0 · r0
    for k = 0, 1, 2, ... :
        α_k   = rs_old / (p_k · A p_k)          # 步长
        x_{k+1} = x_k + α_k p_k
        r_{k+1} = r_k - α_k A p_k               # 更新残差
        rs_new = r_{k+1} · r_{k+1}
        if ||r_{k+1}|| < tol : break
        β_k   = rs_new / rs_old                 # 共轭系数
        p_{k+1} = r_{k+1} + β_k p_k
        rs_old = rs_new

理论性质：在精确算术下，CG 至多 n 步即可收敛到精确解
（n 为问题维度）。本实现中取最大迭代次数 max_iter = n，
初始点 x0 = 0。


二、Hilbert 矩阵是病态 (ill-conditioned) 的吗？—— 是的，且极其病态
------------------------------------------------------------------
Hilbert 矩阵 H_n 的元素 H_ij = 1/(i+j-1)（此处采用 0-based：1/(i+j+1)）。
它是经典的病态反例，理由如下：

1. 条件数爆炸式增长
   实测各维度下条件数 cond_2(A) = ||A||·||A^{-1}||：

        n =  5  ->  cond(A) ≈ 4.77e+05
        n =  8  ->  cond(A) ≈ 1.53e+10
        n = 12  ->  cond(A) ≈ 1.72e+16
        n = 20  ->  cond(A) ≈ 2.87e+18

   双精度浮点只有约 1e-16 的相对精度。当 cond(A) 达到 1e16 乃至 1e18
   时，输入或浮点舍入中哪怕 1e-16 量级的扰动，也会被放大成接近 100%
   的解误差（前向误差估计：||Δx||/||x|| ≤ cond(A)·(||Δb||/||b||)）。

2. 特征值极度聚集于 0
   Hilbert 矩阵的特征值分布范围极广（最大约 O(1)，最小约 1e-7 甚至更小），
   谱条件数 = λ_max / λ_min 巨大。CG 的收敛速度取决于特征值分布，
   病态使其迭代过程对舍入误差极为敏感。

3. 解分量大
   求解 Ax = 1 得到的解 x 某些分量高达数万量级，导致"小残差"并不等价于
   "小误差"。


三、测试结果与分析
------------------------------------------------------------------
运行 main() 得到（迭代次数、残差、与精确解相对误差）：

    n = 5   迭代 5  次 | 残差 ~5.8e-05  | 相对误差 ~2.6e-08   (准确)
    n = 8   迭代 8  次 | 残差 ~1.7e-03  | 相对误差 ~1.0e+00   (失效)
    n = 12  迭代 12 次 | 残差 ~2.4e-03  | 相对误差 ~1.0e+00   (失效)
    n = 20  迭代 20 次 | 残差 ~2.5e-03  | 相对误差 ~1.0e+00   (失效)

观察：
  * CG 的迭代次数均恰好等于 n —— 符合"精确算术下 n 步收敛"的理论预期。
  * 残差范数始终保持在 ~1e-3 量级，看似"收敛"，但对 n≥8，解与精确解
    的相对误差接近 100%。

结论：这并非 CG 实现有误，而是 Hilbert 矩阵高度病态所致。小 n（如 5）
尚可得到可靠解；大 n 时即使算法正确，浮点舍入也会使结果完全失真。
Hilbert 矩阵因此常被用作数值分析中检验算法稳健性的标准反例。

（注：若要更稳健地求解此类病态系统，可考虑预处理 CG (Preconditioned CG)、
正则化或更高精度算术等手段。）
"""

import numpy as np


def hilbert_matrix(n):
    """构造 n x n 的 Hilbert 矩阵: A[i][j] = 1/(i+j+1)。"""
    A = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            A[i, j] = 1.0 / (i + j + 1)
    return A


def conjugate_gradient(A, b, x0=None, tol=1e-10, max_iter=None):
    """
    标准 Conjugate Gradient 方法求解 Ax = b。

    参数
    ----
    A : ndarray, shape (n, n)
        对称正定矩阵（Hilbert 矩阵满足条件）。
    b : ndarray, shape (n,)
        右端项。
    x0 : ndarray, shape (n,) or None
        初始猜测，默认为全 0 向量。
    tol : float
        残差范数收敛阈值。
    max_iter : int or None
        最大迭代次数，默认为 n。

    返回
    ----
    x : ndarray
        求解得到的近似解。
    info : dict
        包含迭代次数、最终残差范数等诊断信息。
    """
    n = len(b)
    if x0 is None:
        x = np.zeros(n)
    else:
        x = x0.copy()

    r = b - A @ x        # 初始残差
    p = r.copy()         # 初始搜索方向
    rs_old = r @ r       # r^T r

    if max_iter is None:
        max_iter = n

    history = []

    for k in range(max_iter):
        Ap = A @ p
        alpha = rs_old / (p @ Ap)        # 步长
        x = x + alpha * p
        r = r - alpha * Ap               # 更新残差
        rs_new = r @ r
        res_norm = np.sqrt(rs_new)
        history.append(res_norm)

        if res_norm < tol:
            break

        beta = rs_new / rs_old           # 共轭系数
        p = r + beta * p
        rs_old = rs_new

    info = {
        "iterations": k + 1,
        "residual_norm": history[-1],
        "residual_history": history,
    }
    return x, info


def run_test(n):
    """对给定维度 n 运行一次 CG 测试。"""
    A = hilbert_matrix(n)
    b = np.ones(n)
    x0 = np.zeros(n)          # 初始点 x0 = 0

    x, info = conjugate_gradient(A, b, x0=x0)

    # 计算真实残差与相对误差
    residual = b - A @ x
    resid_norm = np.linalg.norm(residual)
    rel_resid = resid_norm / np.linalg.norm(b)

    # 与 numpy 精确解对比
    x_exact = np.linalg.solve(A, b)
    sol_err = np.linalg.norm(x - x_exact) / np.linalg.norm(x_exact)

    print(f"n = {n}")
    print(f"  迭代次数          : {info['iterations']}")
    print(f"  CG 残差范数        : {info['residual_norm']:.3e}")
    print(f"  真实相对残差       : {rel_resid:.3e}")
    print(f"  与精确解相对误差   : {sol_err:.3e}")
    print(f"  x = {np.array2string(x, precision=4, suppress_small=True)}")
    print()


def main():
    print("=" * 60)
    print("Conjugate Gradient 求解 Hilbert 矩阵方程 Ax = b (b = 1)")
    print("=" * 60)
    print()
    for n in [5, 8, 12, 20]:
        run_test(n)


if __name__ == "__main__":
    main()
