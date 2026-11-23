"""MN 图像恢复：图像、模型与能量（对应笔记 §3.6 建模 + §8.2 MPE）。

书中给的数值
------------
一元势   亮 0.4 / 暗 0.6
二元势   相邻同色 0.9 / 异色 0.1     <- 只是"相对权重"，不是概率

书里 MPE 实验隐含的观测通道（噪声信道），本实现补齐：

    x_i --(If x_i then Flip(1-eps) else Flip(eps))--> y_i
    即 P(y_i = x_i) = 1 - eps

观测 y 作为证据进入一元项，于是后验（未归一化）：

    P(X|Y) prop prod_i prior(x_i) * lik(y_i|x_i) * prod_{(i,j)} psi(x_i,x_j)

能量：

    E(X) = -log P(X|Y) + const
    MPE  = argmax 后验 = argmin 能量        <- 与 MRF 能量最小化是同一件事

注意：势 0.9/0.1 未归一化，一元项之和也不为 1，因此 P(X|Y) 必须先有 Z 才成分布。
本文件只做"未归一化乘积"，Z 由推理算法隐式处理（VE 不需要显式求 Z）。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

# 10x10 的测试图：一个 6x6 实心方块。用实心块而不是细线条，是因为
# Ising 型平滑势本来就偏向"大块同色"，细线会被它当成噪声抹掉
# （这本身是模型与先验的匹配问题，不是算法问题）。
_LETTER_10 = [
    "..........",
    "..........",
    "..######..",
    "..######..",
    "..######..",
    "..######..",
    "..######..",
    "..######..",
    "..........",
    "..........",
]


def make_test_image(n: int = 10) -> np.ndarray:
    """生成真值图。n=10 用固定图案，其余尺寸生成一个粗壮的 "T"。

    刻意让亮区面积占比大（约 40%-50%）、边界短：平滑势偏向大块同色，
    面积/周长比太小（细线、小圆点）时无论算法多准都会被先验抹掉。
    """
    if n == 10:
        return np.array([[ch == "#" for ch in row] for row in _LETTER_10])
    yy, xx = np.mgrid[0:n, 0:n] / max(n - 1, 1)
    bar = (yy >= 0.10) & (yy <= 0.50) & (xx >= 0.08) & (xx <= 0.92)
    stem = (yy >= 0.50) & (yy <= 0.90) & (xx >= 0.36) & (xx <= 0.64)
    return bar | stem


def corrupt(img: np.ndarray, eps: float, rng: np.random.Generator) -> np.ndarray:
    """按噪声信道的同一分布生成观测：以概率 eps 翻转每个像素。"""
    flip = rng.random(img.shape) < eps
    return img ^ flip


def error_rate(x: np.ndarray, truth: np.ndarray) -> float:
    return float(np.mean(np.asarray(x, dtype=bool) != np.asarray(truth, dtype=bool)))


@dataclass
class BinaryGridMRF:
    """n x n 二值网格上的 MN（4 邻接）。

    obs=None 表示无证据 -> 模型退化为纯先验，其 MPE 就是"先验最想要的那张图"。
    """

    n: int
    obs: np.ndarray | None = None
    prior_bright: float = 0.4      # 书中一元势：亮 0.4 / 暗 0.6
    pair_same: float = 0.9         # 书中二元势：同色 0.9 / 异色 0.1
    pair_weight: float = 1.0       # 二元势的指数 beta：1.0 = 书中字面值
    noise: float = 0.2             # 观测通道翻转率 eps

    def __post_init__(self) -> None:
        if self.obs is not None:
            obs = np.asarray(self.obs, dtype=bool)
            if obs.shape != (self.n, self.n):
                raise ValueError(f"obs 形状应为 {(self.n, self.n)}，实际 {obs.shape}")
            self.obs = obs

    # ---- 势 -------------------------------------------------------------
    @property
    def n_vars(self) -> int:
        return self.n * self.n

    def pair_log(self) -> np.ndarray:
        """2x2 的对数二元势，索引 [x_i, x_j]。

        pair_weight 是"平滑强度"：势的 beta 次方，等价于把 log 势整体缩放。
        书中只给了 0.9/0.1 这一组数字，但它和似然（log(0.8/0.2)=1.386/像素）
        不在同一尺度上：一条异色边的代价 log 9 = 2.197，比单个像素的证据还贵，
        于是 beta=1 时证据被平滑压死、MPE 退化成全暗（见 demo 实验 A）。
        这正是笔记 §2.1 "参数太自信会压死数据" 的实例。
        """
        same = math.log(self.pair_same)
        diff = math.log(1.0 - self.pair_same)
        base = np.array([[same, diff], [diff, same]], dtype=float)
        return self.pair_weight * base

    def unary_log(self) -> np.ndarray:
        """(n, n, 2) 的对数一元势 = log 先验 + log 似然（证据已并入）。"""
        prior = np.array([1.0 - self.prior_bright, self.prior_bright])
        u = np.broadcast_to(np.log(prior), (self.n, self.n, 2)).astype(float).copy()
        if self.obs is not None:
            eps = self.noise
            lik_table = np.array([[1.0 - eps, eps], [eps, 1.0 - eps]])  # [y, x]
            u += np.log(lik_table[self.obs.astype(np.intp)])
        return u

    # ---- 能量 -----------------------------------------------------------
    def energy(self, x: np.ndarray) -> float:
        """E(X) = -log P(X|Y)，常数项省略；MPE 即 E 最小。"""
        x = np.asarray(x, dtype=bool)
        xi = x.astype(np.intp)
        n = self.n
        u = self.unary_log()
        p = self.pair_log()
        rows = np.arange(n)[:, None]
        cols = np.arange(n)[None, :]
        e = -float(u[rows, cols, xi].sum())
        e -= float(p[xi[:, 1:], xi[:, :-1]].sum())     # 水平边
        e -= float(p[xi[1:, :], xi[:-1, :]].sum())     # 垂直边
        return e

    def log_joint(self, x: np.ndarray) -> float:
        return -self.energy(x)


def as_bool_array(x: np.ndarray) -> np.ndarray:
    return np.asarray(x, dtype=bool)
