"""
Graphical abstract for the paper.

Results in Engineering requires a single image (max 2400 x 1800 px,
ideally landscape) that summarises the paper at a glance. The
graphical abstract here is a 4-panel composite:

  (a) The calibration paradox        — predictive RMSE wins, RL transfer
                                       loses
  (b) The hybrid resolution          — pure v3 vs hybrid_l010 on live
                                       BOPTEST
  (c) Controller-family lambda map   — thermostatic 0.10, HDRL 0.00,
                                       MORL 0.00
  (d) Component-decomposition transfer — surrogate side PASS,
                                         controller side FAIL across
                                         the hydronic family

Output:  paper/figures/graphical_abstract.{pdf,png}
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, Rectangle

PAPER_DIR = Path(__file__).resolve().parent
OUT_DIR = PAPER_DIR / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PALETTE = {
    "ink": "#1a1a2e",
    "muted": "#9a9a9a",
    "warn": "#c1121f",
    "success": "#0f8a5f",
    "accent": "#f4a261",
    "blue": "#1e6091",
    "purple": "#5a4e7c",
    "light_bg": "#f5f3ee",
}

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    }
)


def panel_a(ax) -> None:
    """Predictive RMSE bars (lower=better) and live transfer RMSE bars."""
    variants = ["raw\nv3.5", "calibrated\nv3.5", "v3\nFFN"]
    pred = [1.47, 0.64, 2.10]  # 24-h rollout RMSE, deg C
    transfer = [4.30, 4.32, 0.89]  # live BOPTEST peak RMSE, deg C
    x = np.arange(len(variants))
    w = 0.36

    ax.bar(
        x - w / 2,
        pred,
        w,
        color=PALETTE["blue"],
        edgecolor=PALETTE["ink"],
        linewidth=0.8,
        label="held-out 24-h rollout",
    )
    ax.bar(
        x + w / 2,
        transfer,
        w,
        color=PALETTE["warn"],
        edgecolor=PALETTE["ink"],
        linewidth=0.8,
        label="live BOPTEST transfer",
    )
    for xi, p, t in zip(x, pred, transfer):
        ax.text(xi - w / 2, p + 0.05, f"{p:.2f}", ha="center", va="bottom", fontsize=8)
        ax.text(xi + w / 2, t + 0.05, f"{t:.2f}", ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(variants, fontsize=9)
    ax.set_ylabel("temperature RMSE  (deg C)")
    ax.set_ylim(0, 5.5)
    ax.set_title(
        "(a)  The calibration paradox:  best predictive twin = worst RL env",
        loc="left",
        fontsize=10,
    )
    ax.legend(loc="upper center", frameon=False, ncols=1)
    ax.grid(axis="y", alpha=0.25)


def panel_b(ax) -> None:
    """Hybrid resolution: pure v3 vs hybrid_l010 on peak/typical windows."""
    windows = ["peak heat", "typical heat"]
    pure_v3_ms = [0.073, 0.095]
    hybrid_ms = [0.087, 0.041]
    x = np.arange(len(windows))
    w = 0.36

    ax.bar(
        x - w / 2,
        pure_v3_ms,
        w,
        color=PALETTE["accent"],
        edgecolor=PALETTE["ink"],
        linewidth=0.8,
        label="pure v3",
    )
    ax.bar(
        x + w / 2,
        hybrid_ms,
        w,
        color=PALETTE["success"],
        edgecolor=PALETTE["ink"],
        linewidth=0.8,
        label="hybrid_l010",
    )
    for xi, p, h in zip(x, pure_v3_ms, hybrid_ms):
        ax.text(xi - w / 2, p + 0.003, f"{p:.3f}", ha="center", va="bottom", fontsize=8)
        ax.text(xi + w / 2, h + 0.003, f"{h:.3f}", ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(windows, fontsize=9)
    ax.set_ylabel("composite KPI  m_s  (lower = better)")
    ax.set_ylim(0, max(pure_v3_ms + hybrid_ms) * 1.4)
    ax.set_title(
        "(b)  Hybrid loss closes the gap on thermostatic PPO",
        loc="left",
        fontsize=10,
    )
    ax.legend(loc="upper right", frameon=False)
    ax.grid(axis="y", alpha=0.25)


def panel_c(ax) -> None:
    """Controller-family lambda map (heat-stripe diagram)."""
    families = ["Thermostatic\nPPO", "HDRL\n(hierarchical)", "MORL\n(17-D obs)"]
    lambdas = [0.10, 0.00, 0.00]
    colors = [PALETTE["success"], PALETTE["muted"], PALETTE["muted"]]
    x = np.arange(len(families))

    bars = ax.bar(x, lambdas, color=colors, edgecolor=PALETTE["ink"], linewidth=0.9, width=0.55)
    for xi, val in zip(x, lambdas):
        text = f"lambda* = {val:.2f}"
        ax.text(xi, val + 0.005, text, ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(families, fontsize=9)
    ax.set_ylabel("optimal  lambda_temp")
    ax.set_ylim(0, 0.16)
    ax.set_title(
        "(c)  Optimal lambda is controller-family specific",
        loc="left",
        fontsize=10,
    )
    ax.grid(axis="y", alpha=0.25)

    # Annotation
    ax.text(
        1.0,
        0.13,
        "no universal lambda;\nrich obs / hierarchy provide\nintrinsic regularisation",
        ha="center",
        va="top",
        fontsize=8.5,
        style="italic",
        color=PALETTE["ink"],
    )


def panel_d(ax) -> None:
    """Component-decomposition view: surrogate PASS, controller FAIL."""
    ax.set_xlim(-0.5, 3.5)
    ax.set_ylim(-0.5, 2.5)
    ax.set_axis_off()

    # Two column headers
    ax.text(
        0.5,
        2.2,
        "Surrogate component\n(C_zon ratio: 1.91 +/- 0.03)",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color=PALETTE["success"],
    )
    ax.text(
        2.5,
        2.2,
        "Controller component\n(frozen direct-TSup policy)",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color=PALETTE["warn"],
    )

    testcases = ["heat_pump", "hydronic", "commercial"]
    for i, tc in enumerate(testcases):
        y = 1.5 - i * 0.65
        ax.text(-0.35, y, tc, ha="left", va="center", fontsize=9, color=PALETTE["ink"])
        # surrogate PASS chip
        chip_s = FancyBboxPatch(
            (0.1, y - 0.18),
            0.8,
            0.36,
            boxstyle="round,pad=0.02,rounding_size=0.05",
            facecolor=PALETTE["success"],
            edgecolor=PALETTE["ink"],
            linewidth=0.8,
            alpha=0.85,
        )
        ax.add_patch(chip_s)
        ax.text(0.5, y, "PASS", ha="center", va="center", fontsize=9, color="white", fontweight="bold")
        # controller FAIL chip
        chip_c = FancyBboxPatch(
            (2.1, y - 0.18),
            0.8,
            0.36,
            boxstyle="round,pad=0.02,rounding_size=0.05",
            facecolor=PALETTE["warn"],
            edgecolor=PALETTE["ink"],
            linewidth=0.8,
            alpha=0.85,
        )
        ax.add_patch(chip_c)
        ax.text(2.5, y, "FAIL", ha="center", va="center", fontsize=9, color="white", fontweight="bold")

    ax.text(
        1.5,
        -0.25,
        "Surrogate transfers structurally / Controller transfers only when action interface matches",
        ha="center",
        va="center",
        fontsize=9,
        style="italic",
        color=PALETTE["ink"],
    )
    ax.set_title(
        "(d)  Component-level decomposition across BOPTEST hydronic family  (Block 3, N = 3)",
        loc="left",
        fontsize=10,
    )


def build_graphical_abstract() -> None:
    fig = plt.figure(figsize=(11.5, 7.8))
    gs = fig.add_gridspec(2, 2, hspace=0.42, wspace=0.30)
    axes = [
        fig.add_subplot(gs[0, 0]),
        fig.add_subplot(gs[0, 1]),
        fig.add_subplot(gs[1, 0]),
        fig.add_subplot(gs[1, 1]),
    ]

    panel_a(axes[0])
    panel_b(axes[1])
    panel_c(axes[2])
    panel_d(axes[3])

    fig.suptitle(
        "Calibrated physical twin as a soft regulariser for HVAC reinforcement learning",
        fontsize=13,
        fontweight="bold",
        color=PALETTE["ink"],
        y=0.99,
    )
    fig.text(
        0.5,
        0.945,
        "BOPTEST bestest_air (source) + 3 hydronic testcases (transfer)  —  hybrid backend 85x faster than RTE HTTP-Docker",
        ha="center",
        va="center",
        fontsize=10,
        style="italic",
        color=PALETTE["muted"],
    )

    for ext in ("pdf", "png"):
        path = OUT_DIR / f"graphical_abstract.{ext}"
        fig.savefig(path)
        print(f"[OK] wrote {path}")
    plt.close(fig)


if __name__ == "__main__":
    build_graphical_abstract()
