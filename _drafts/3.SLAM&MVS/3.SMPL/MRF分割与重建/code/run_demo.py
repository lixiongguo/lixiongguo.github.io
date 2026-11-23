"""MN 图像恢复 + MPE：把书里第 5 章建的模型、第 12 章的 MPE 任务跑完整。

用法::

    python run_demo.py                          # 实验 A(书中字面值) + B(校准) + C(大规模)
    python run_demo.py --n 11 --noise 0.25      # 换规模/噪声
    python run_demo.py --beta 0.35              # 换平滑强度
    python run_demo.py --big 32 --steps 400000  # 加大规模实验
    python run_demo.py --no-save                # 不写 PNG

三个实验各自要回答的问题
------------------------
A  用书中字面的数值（一元 0.4/0.6，二元 0.9/0.1）直接求 MPE 会得到什么？
   -> 全暗。因为一条异色边的代价 log 9 = 2.197，超过单像素证据 log(0.8/0.2) = 1.386，
      平滑把证据压死了。这不是算法错，是"势的相对尺度"问题（笔记 §2.1、§3.4）。
B  把平滑强度 beta 调到与似然同一尺度后：去噪是否有效？MPE 与"逐像素边缘阈值"
   是否同一个解？（笔记 §8.2 的核心论断）+ 用独立实现的行 DP 交叉验证 VE。
C  n=32 时 VE 的因子是 2^33 行，撑不住；只能换 loopy BP / SA（笔记 §11.2 决策树）。
"""

from __future__ import annotations

import argparse
import sys
import time
import unicodedata
from pathlib import Path

import numpy as np

import mrf_image as mi
import mrf_inference as mf


# ----------------------------------------------------------------------
# 输出辅助（中文按双宽补齐，保证表格对齐）
# ----------------------------------------------------------------------
def _width(s: str) -> int:
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)


def _pad(s: str, width: int) -> str:
    return s + " " * max(width - _width(s), 0)


def show_ascii(title: str, img: np.ndarray) -> None:
    print(f"\n{title}")
    for row in np.asarray(img, dtype=bool):
        print("  " + "".join("##" if v else ".." for v in row))


def render_table(rows, ref: np.ndarray, model, truth: np.ndarray) -> None:
    head = ("方案", "错像素/总数", "错误率", "能量 E", "与基准不一致", "备注")
    widths = (26, 12, 8, 11, 14, 34)
    line = "  ".join(_pad(h, w) for h, w in zip(head, widths))
    print(line)
    print("-" * _width(line))
    for name, x, note in rows:
        x = np.asarray(x, dtype=bool)
        diff = int(np.sum(x != ref))
        cells = (
            _pad(name, widths[0]),
            _pad(f"{diff}/{ref.size}", widths[1]),
            _pad(f"{mi.error_rate(x, truth):.3f}", widths[2]),
            _pad(f"{model.energy(x):.3f}", widths[3]),
            _pad(f"{diff}", widths[4]),
            _pad(note, widths[5]),
        )
        print("  ".join(cells))


def banner(title: str) -> None:
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


# ----------------------------------------------------------------------
# 一次完整对照实验
# ----------------------------------------------------------------------
def run_case(
    label: str,
    n: int,
    noise: float,
    seed: int,
    steps: int,
    pair_weight: float,
    verbose: bool = True,
):
    truth = mi.make_test_image(n)
    rng = np.random.default_rng(seed)
    obs = mi.corrupt(truth, noise, rng)

    prior_model = mi.BinaryGridMRF(n=n, obs=None, pair_weight=pair_weight)
    model = mi.BinaryGridMRF(n=n, obs=obs, noise=noise, pair_weight=pair_weight)

    banner(
        f"{label}：{n}x{n}，一元势 亮{model.prior_bright}/暗{1 - model.prior_bright:.1f}，"
        f"二元势 同色{model.pair_same}/异色{1 - model.pair_same:.1f}，"
        f"平滑强度 beta={pair_weight}，观测噪声 eps={noise}"
    )

    t0 = time.perf_counter()
    x_prior, _ = mf.mpe_ve(prior_model)
    t_prior = time.perf_counter() - t0

    t0 = time.perf_counter()
    x_ve, info_ve = mf.mpe_ve(model)
    t_ve = time.perf_counter() - t0

    tables = mf._row_dp_tables(model)
    t0 = time.perf_counter()
    x_dp, info_dp = mf.mpe_row_dp(model, tables=tables)
    t_dp = time.perf_counter() - t0

    t0 = time.perf_counter()
    marg = mf.exact_marginals(model, tables=tables)
    x_thr = marg > 0.5
    t_marg = time.perf_counter() - t0

    t0 = time.perf_counter()
    x_bp, info_bp = mf.mpe_bp(model)
    t_bp = time.perf_counter() - t0

    t0 = time.perf_counter()
    x_sa, info_sa = mf.mpe_sa(model, steps=steps, seed=seed)
    t_sa = time.perf_counter() - t0

    if verbose:
        print(
            f"\n模型：{model.n_vars} 个二值变量，{2 * n * (n - 1)} 条边（4 邻接）；"
            f"证据：观测错 {int((obs != truth).sum())} 像素"
        )
        print(
            f"VE：诱导图最大团 {info_ve['max_clique']} 个变量 -> 最大因子 "
            f"{info_ve['max_rows']} 行，用时 {t_ve * 1e3:.1f} ms；"
            f"先验 MPE {t_prior * 1e3:.1f} ms，边缘阈值 {t_marg * 1e3:.1f} ms"
        )
        print(
            f"VE 最优 log 后验 {info_ve['log_joint']:.6f} vs 行 DP {info_dp['log_joint']:.6f}"
            f"（差 {abs(info_ve['log_joint'] - info_dp['log_joint']):.2e}），"
            f"两解相同 = {np.array_equal(x_ve, x_dp)}"
        )

    rows = [
        ("先验 MPE（无证据）", x_prior, "只有先验势，不看观测"),
        ("观测图（未去噪）", obs, "把证据直接当答案"),
        ("精确 VE MPE", x_ve, "基准（精确）"),
        ("行 DP MPE", x_dp, "独立实现，交叉验证"),
        ("逐像素边缘阈值", x_thr, "每个边缘取 argmax 再拼"),
        ("loopy BP MPE", x_bp, f"{info_bp['iterations']} 轮，收敛={info_bp['converged']}"),
        ("MH+退火 MPE", x_sa, f"接受率 {info_sa['accept_rate']:.4f}"),
    ]
    if verbose:
        print()
        render_table(rows, x_ve, model, truth)

        e_ve = model.energy(x_ve)
        e_thr = model.energy(x_thr)
        e_bp = model.energy(x_bp)
        print(
            f"\nMPE 与边缘阈值解相差 {int(np.sum(x_ve != x_thr))} 个像素；"
            f"E(MPE)={e_ve:.3f} <= E(阈值)={e_thr:.3f}（差 {e_thr - e_ve:.3f}）"
        )
        if e_bp > e_ve + 1e-9:
            print(
                f"注意 BP：像素错 {int(np.sum(x_bp != truth))} 个、能量 {e_bp:.3f}，"
                f"高于精确解的 {e_ve:.3f} —— 说明 BP 收敛到的只是某个不动点，"
                "判据必须是后验概率而不是 Hamming 距离"
            )
        if np.array_equal(x_sa, x_ve):
            print("SA 命中与精确解相同的配置")
        else:
            print(
                f"SA 未命中精确解，能量差 {model.energy(x_sa) - e_ve:+.3f}"
                "（单像素翻转 + 有限步数的 MCMC 误差）"
            )

    return dict(
        label=label, n=n, noise=noise, pair_weight=pair_weight,
        truth=truth, obs=obs, x_prior=x_prior, x_ve=x_ve, x_dp=x_dp,
        x_thr=x_thr, x_bp=x_bp, x_sa=x_sa, model=model,
        info_ve=info_ve, info_bp=info_bp, info_sa=info_sa, marg=marg,
        timing=dict(ve=t_ve, dp=t_dp, marg=t_marg, bp=t_bp, sa=t_sa),
    )


# ----------------------------------------------------------------------
# 大规模：VE 撑不住，只能 BP / SA
# ----------------------------------------------------------------------
def run_large(n: int, noise: float, seed: int, steps: int, pair_weight: float) -> dict:
    truth = mi.make_test_image(n)
    obs = mi.corrupt(truth, noise, np.random.default_rng(seed))
    model = mi.BinaryGridMRF(n=n, obs=obs, noise=noise, pair_weight=pair_weight)

    banner(
        f"实验 C：{n}x{n} 同一模型（beta={pair_weight}），看算法选择（笔记 §11.2）"
    )
    print(
        f"若用 VE：网格树宽 = n = {n}，最大团约 {n + 1} 个变量 -> 最大因子 "
        f"{2 ** (n + 1):,} 行，且中间因子数量随网格增长，实际不可行"
    )

    t0 = time.perf_counter()
    x_bp, info_bp = mf.mpe_bp(model)
    t_bp = time.perf_counter() - t0

    t0 = time.perf_counter()
    x_sa, info_sa = mf.mpe_sa(model, steps=steps, seed=seed)
    t_sa = time.perf_counter() - t0

    rows = [
        ("观测图（未去噪）", obs, f"证据错 {int((obs != truth).sum())} 像素"),
        ("loopy BP MPE", x_bp, f"{info_bp['iterations']} 轮，收敛={info_bp['converged']}，{t_bp:.1f}s"),
        ("MH+退火 MPE", x_sa, f"接受率 {info_sa['accept_rate']:.4f}，{t_sa:.1f}s"),
    ]
    print()
    render_table(rows, obs, model, truth)
    print("本表'不一致'列相对观测图统计：大模型下没有精确解可作基准。")
    e_bp, e_sa = model.energy(x_bp), model.energy(x_sa)
    better = "SA" if e_sa < e_bp else "BP"
    print(
        f"BP 能量 {e_bp:.3f}，SA 能量 {e_sa:.3f}，差 {e_bp - e_sa:+.3f}"
        f"（能量更低的是 {better}；此规模没有精确值，只能比较各自的后验，不能看像素像不像）"
    )
    return dict(truth=truth, obs=obs, x_bp=x_bp, x_sa=x_sa)


# ----------------------------------------------------------------------
# 画图
# ----------------------------------------------------------------------
def save_figure(res: dict, out_dir: Path) -> Path | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n未安装 matplotlib，跳过 PNG 输出")
        return None

    panels = [
        ("truth", res["truth"]),
        (f"observation (eps={res['noise']})", res["obs"]),
        ("prior MPE (no evidence)", res["x_prior"]),
        ("exact VE MPE", res["x_ve"]),
        ("marginal threshold", res["x_thr"]),
        ("loopy BP MPE", res["x_bp"]),
        ("MH anneal MPE", res["x_sa"]),
    ]
    fig, axes = plt.subplots(2, 4, figsize=(12, 6.2))
    for ax, (title, img) in zip(axes.ravel(), panels):
        ax.imshow(np.asarray(img, bool), cmap="gray_r", vmin=0, vmax=1, interpolation="nearest")
        ax.set_title(title, fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
    axes.ravel()[-1].axis("off")
    fig.suptitle(
        f"MN image restoration {res['n']}x{res['n']}, "
        f"unary 0.4/0.6, pairwise 0.9/0.1 (beta={res['pair_weight']}), noise {res['noise']}",
        fontsize=10,
    )
    fig.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"mrf_denoise_{res['n']}x{res['n']}_beta{res['pair_weight']}_eps{res['noise']}.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="MN 图像恢复 + MPE（《概率编程实战》第 5 章建模 / 第 12 章 MPE）"
    )
    ap.add_argument("--n", type=int, default=10, help="精确实验网格边长，受行 DP 限制须 <= 11")
    ap.add_argument("--noise", type=float, default=0.2, help="观测通道翻转率 eps")
    ap.add_argument("--beta", type=float, default=0.4, help="平滑强度（二元势的指数）")
    ap.add_argument("--seed", type=int, default=0, help="随机种子")
    ap.add_argument("--steps", type=int, default=200_000, help="SA 提议步数")
    ap.add_argument("--big", type=int, default=32, help="大规模实验边长，0 表示跳过")
    ap.add_argument("--no-save", action="store_true", help="不写 PNG")
    ap.add_argument("--only-b", action="store_true", help="只跑实验 B")
    args = ap.parse_args(argv)

    if args.n > 11:
        print("精确实验的行 DP 需要 2^n 个状态，请用 --n <= 11", file=sys.stderr)
        return 2

    res_b = None
    if not args.only_b:
        # A：书中字面数值 -> 证据被平滑压死
        res_a = run_case(
            "实验 A（书中字面数值）", args.n, args.noise, args.seed, args.steps, 1.0
        )
        print(
            "\n结论 A：beta=1 时 MPE 是全暗图。一条异色边的代价 log(0.9/0.1)=2.197，"
            "而单个像素的证据只有 log(0.8/0.2)=1.386，平滑必然压倒证据；\n"
            "        这正是笔记 §2.1 的'参数太自信会压死数据'，也是 §3.4 '势只是相对权重'"
            "在数值上的直接后果——0.9/0.1 只是相对大小，没有绝对尺度。"
        )
        del res_a

    # B：把平滑强度调到与似然同一尺度
    res_b = run_case(
        "实验 B（平滑强度校准）", args.n, args.noise, args.seed, args.steps, args.beta
    )
    show_ascii(f"真值 {args.n}x{args.n}", res_b["truth"])
    show_ascii(f"观测（错 {int((res_b['obs'] != res_b['truth']).sum())} 像素）", res_b["obs"])
    show_ascii(f"精确 VE MPE（错 {int((res_b['x_ve'] != res_b['truth']).sum())} 像素）", res_b["x_ve"])
    show_ascii(f"逐像素边缘阈值（错 {int((res_b['x_thr'] != res_b['truth']).sum())} 像素）", res_b["x_thr"])
    print(
        "\n结论 B：MPE 才是联合最优；边缘阈值解虽然每个像素各自最可能，"
        "拼起来却不是能量最低的整体配置（形状被磨圆、小结构被抹掉）。"
    )

    if args.big:
        run_large(args.big, args.noise, args.seed, args.steps, args.beta)

    if not args.no_save:
        path = save_figure(res_b, Path(__file__).resolve().parent / "out")
        if path:
            print(f"\n图已保存：{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
