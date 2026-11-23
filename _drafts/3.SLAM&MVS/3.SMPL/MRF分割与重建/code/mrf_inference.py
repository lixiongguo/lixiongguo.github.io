"""图像恢复的四种推理：精确 VE、精确行 DP、loopy BP、MH+模拟退火。

对应笔记：
  §6.4  VE 的代数视角（乘 -> 消元 -> 生成新因子），对数域里"乘"就是加
  §7.5  MCMC / MH，退火只是把温度从高降到低
  §6.7  BP：树上精确，网格有环 -> 只能近似，且不保证收敛
  §8.2  MPE = 联合最优，用 max 版本；普通边缘用 sum 版本

所有因子都在对数域：乘积 = 相加，求和 = logaddexp，最大化 = max。
这样一来 VE 的 max 版本和 sum 版本只差一个 reduce 算子，正好体现"MPE 算法族
就是常规算法的 max 版本"。
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from mrf_image import BinaryGridMRF


# ======================================================================
# 因子（对数域）
# ======================================================================
@dataclass
class Factor:
    """scope 为排序后的变量编号元组，vals 形状为 (2,)*len(scope)，存 log 值。"""

    scope: tuple[int, ...]
    vals: np.ndarray

    @property
    def n_rows(self) -> int:
        return 2 ** len(self.scope)


def _align_shape(scope: tuple[int, ...], target: tuple[int, ...]) -> tuple[int, ...]:
    """把 scope 形状对齐到 target（变量编号有序，所以子集只需补 1 维）。"""
    return tuple(2 if v in scope else 1 for v in target)


def multiply(a: Factor, b: Factor) -> Factor:
    """对数域相乘 = 相加（因子乘积）。"""
    scope = tuple(sorted(set(a.scope) | set(b.scope)))
    av = a.vals.reshape(_align_shape(a.scope, scope))
    bv = b.vals.reshape(_align_shape(b.scope, scope))
    return Factor(scope, av + bv)


def _reduce(factor: Factor, var: int, op: str):
    """消去 var：op='max' 求 MPE（带回溯表），op='sum' 求边缘（logaddexp）。"""
    axis = factor.scope.index(var)
    sep = factor.scope[:axis] + factor.scope[axis + 1:]
    if op == "max":
        vals = np.max(factor.vals, axis=axis)
        rec = (sep, np.asarray(np.argmax(factor.vals, axis=axis)))
    elif op == "sum":
        vals = np.logaddexp.reduce(factor.vals, axis=axis)
        rec = None
    else:
        raise ValueError(op)
    return Factor(sep, np.asarray(vals)), rec


def build_factors(model: BinaryGridMRF) -> list[Factor]:
    """把模型拆成"一元因子 + 每条边的二元因子"，即 BM 的 CPD / MN 的势。"""
    n = model.n
    u = model.unary_log()
    p = model.pair_log()
    factors: list[Factor] = [
        Factor((r * n + c,), u[r, c].copy()) for r in range(n) for c in range(n)
    ]
    for r in range(n):
        for c in range(n - 1):
            factors.append(Factor((r * n + c, r * n + c + 1), p.copy()))
    for r in range(n - 1):
        for c in range(n):
            factors.append(Factor((r * n + c, (r + 1) * n + c), p.copy()))
    return factors


# ======================================================================
# 1) 精确 MPE：max-product 变量消除
# ======================================================================
def mpe_ve(model: BinaryGridMRF, order: list[int] | None = None):
    """逐变量消元，消元时记录 argmax，最后反向回溯。

    返回 (bool 图, info)。info 里的 max_clique 用于对照笔记 §6.3：
        VE 复杂度 prop to exp(诱导图最大团顶点数) = 2**max_clique 行
    """
    n = model.n
    factors = build_factors(model)
    if order is None:
        # 逐列消元：2D 网格的树宽 = n，最大团约 n+1
        order = [r * n + c for c in range(n) for r in range(n)]

    records: dict[int, tuple[tuple[int, ...], np.ndarray]] = {}
    max_clique = 0
    for v in order:
        involved = [f for f in factors if v in f.scope]
        rest = [f for f in factors if v not in f.scope]
        joint = involved[0]
        for f in involved[1:]:
            joint = multiply(joint, f)
        max_clique = max(max_clique, len(joint.scope))
        new_factor, rec = _reduce(joint, v, "max")
        records[v] = rec
        factors = rest + [new_factor]

    leftover = factors[0]
    for f in factors[1:]:
        leftover = multiply(leftover, f)
    best_log_joint = float(np.asarray(leftover.vals).reshape(()))

    assign: dict[int, int] = {}
    for v in reversed(order):          # 反向：sep 里的变量都已确定
        sep, arg = records[v]
        assign[v] = int(arg[tuple(assign[s] for s in sep)]) if sep else int(arg)

    x = np.zeros(n * n, dtype=bool)
    for v, val in assign.items():
        x[v] = bool(val)
    info = {
        "max_clique": max_clique,
        "max_rows": 2 ** max_clique,
        "log_joint": best_log_joint,
        "order": order,
    }
    return x.reshape(n, n), info


# ======================================================================
# 2) 精确校验：按行状态做 DP（状态 = 整行，2^n 个）
# ======================================================================
def _row_dp_tables(model: BinaryGridMRF):
    n = model.n
    if n > 11:
        raise ValueError("行 DP 的状态数是 2^n，仅用于 n <= 11 的小网格校验")
    bits = ((np.arange(2 ** n)[:, None] >> np.arange(n)[None, :]) & 1).astype(np.intp)
    u = model.unary_log()
    p = model.pair_log()
    row_score = np.zeros((n, 2 ** n))
    for r in range(n):
        s = np.zeros(2 ** n)
        for c in range(n):
            s = s + u[r, c][bits[:, c]]
        for c in range(1, n):
            s = s + p[bits[:, c - 1], bits[:, c]]
        row_score[r] = s
    vert = np.zeros((2 ** n, 2 ** n))
    for c in range(n):
        vert += p[np.ix_(bits[:, c], bits[:, c])]
    return bits, row_score, vert


def mpe_row_dp(model: BinaryGridMRF, tables=None):
    """行状态 DP 求精确 MPE。与 VE 相互独立，用来验证 VE 没写错。"""
    bits, row_score, vert = tables if tables is not None else _row_dp_tables(model)
    n = model.n
    alpha = np.zeros((n, 2 ** n))
    parent = np.zeros((n, 2 ** n), dtype=np.intp)
    alpha[0] = row_score[0]
    for r in range(1, n):
        cand = alpha[r - 1][:, None] + vert
        parent[r] = np.argmax(cand, axis=0)
        alpha[r] = row_score[r] + np.max(cand, axis=0)
    rows = np.zeros(n, dtype=np.intp)
    rows[n - 1] = int(np.argmax(alpha[n - 1]))
    for r in range(n - 1, 0, -1):
        rows[r - 1] = parent[r][rows[r]]
    return bits[rows].astype(bool), {"log_joint": float(alpha[n - 1].max())}


def exact_marginals(model: BinaryGridMRF, tables=None) -> np.ndarray:
    """行状态 DP 的前向-后向，一次算出全部精确边缘 P(x_i=1|Y)。"""
    bits, row_score, vert = tables if tables is not None else _row_dp_tables(model)
    n = model.n
    alpha = np.zeros((n, 2 ** n))
    beta = np.zeros((n, 2 ** n))
    alpha[0] = row_score[0]
    for r in range(1, n):
        alpha[r] = row_score[r] + np.logaddexp.reduce(alpha[r - 1][:, None] + vert, axis=0)
    for r in range(n - 2, -1, -1):
        beta[r] = np.logaddexp.reduce(
            row_score[r + 1][None, :] + vert + beta[r + 1][None, :], axis=1
        )
    marg = np.zeros((n, n))
    for r in range(n):
        joint = alpha[r] + beta[r]
        for c in range(n):
            mask = bits[:, c] == 1
            log1 = np.logaddexp.reduce(joint[mask])
            log0 = np.logaddexp.reduce(joint[~mask])
            marg[r, c] = math.exp(log1 - np.logaddexp(log1, log0))
    return marg


# ======================================================================
# 3) loopy BP（max-product）
# ======================================================================
def mpe_bp(model: BinaryGridMRF, max_iter: int = 200, tol: float = 1e-10):
    """网格有环 -> 只能近似，且不保证收敛。

    消息按目标状态索引：m_{i->j}(x_j)；每条消息减去自身最大值（规范固定），
    否则对数域 max-product 的常数漂移会让"是否收敛"永远判不出来。
    """
    n = model.n
    u = model.unary_log()
    p = model.pair_log()

    nbrs: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for r in range(n):
        for c in range(n):
            lst = []
            if r > 0:
                lst.append((r - 1, c))
            if r < n - 1:
                lst.append((r + 1, c))
            if c > 0:
                lst.append((r, c - 1))
            if c < n - 1:
                lst.append((r, c + 1))
            nbrs[(r, c)] = lst

    msg = {(i, j): np.zeros(2) for i, lst in nbrs.items() for j in lst}
    converged = False
    it = 0
    for it in range(1, max_iter + 1):
        new = {}
        delta = 0.0
        for (i, j) in msg:
            acc = u[i].copy()
            for k in nbrs[i]:
                if k != j:
                    acc = acc + msg[(k, i)]
            m = np.max(acc[:, None] + p, axis=0)
            m = m - m.max()
            new[(i, j)] = m
            delta = max(delta, float(np.max(np.abs(m - msg[(i, j)]))))
        msg = new
        if delta < tol:
            converged = True
            break

    belief = np.zeros((n, n, 2))
    for (r, c) in nbrs:
        b = u[r, c].copy()
        for k in nbrs[(r, c)]:
            b = b + msg[(k, (r, c))]
        belief[r, c] = b
    x = belief[:, :, 1] > belief[:, :, 0]
    return x, {"iterations": it, "converged": converged}


# ======================================================================
# 4) MH + 模拟退火
# ======================================================================
def mpe_sa(
    model: BinaryGridMRF,
    steps: int = 200_000,
    t_high: float = 2.0,
    t_low: float = 0.02,
    seed: int = 0,
    init: np.ndarray | None = None,
):
    """单像素翻转提议 + 几何降温的 Metropolis 接受准则。

    单变量提议在这个模型里不会死锁（能量变化是局部的），所以不需要自定义提议；
    这正是笔记 §7.8 "硬条件 + 单变量提议 = 死锁"的对照面：软势没有硬约束。
    """
    n = model.n
    u = model.unary_log()
    p = model.pair_log()
    rng = np.random.default_rng(seed)

    if init is not None:
        x = np.array(init, dtype=bool)
    elif model.obs is not None:
        x = model.obs.copy()
    else:
        x = rng.random((n, n)) < 0.5

    xi = x.astype(np.intp)
    energy = model.energy(xi.astype(bool))
    best_x = x.copy()
    best_e = energy
    accepted = 0

    nbr_offset = ((-1, 0), (1, 0), (0, -1), (0, 1))
    for t in range(steps):
        temp = t_high * (t_low / t_high) ** (t / steps)
        r = int(rng.integers(n))
        c = int(rng.integers(n))
        a = xi[r, c]
        b = 1 - a
        dlog = u[r, c, b] - u[r, c, a]              # 局部 log 后验增量
        for dr, dc in nbr_offset:
            rr, cc = r + dr, c + dc
            if 0 <= rr < n and 0 <= cc < n:
                xb = xi[rr, cc]
                dlog += p[b, xb] - p[a, xb]
        if dlog >= 0.0 or rng.random() < math.exp(dlog / temp):
            xi[r, c] = b
            energy -= dlog
            accepted += 1
            if energy < best_e - 1e-12:
                best_e = energy
                best_x = xi.astype(bool).copy()

    return best_x, {
        "steps": steps,
        "accept_rate": accepted / max(steps, 1),
        "best_energy": best_e,
    }
