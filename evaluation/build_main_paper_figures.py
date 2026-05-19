from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "figures" / "article_real"
OUT.mkdir(parents=True, exist_ok=True)


def save(fig: plt.Figure, stem: str) -> None:
    fig.patch.set_facecolor("white")
    fig.savefig(OUT / f"{stem}.png", dpi=220, bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def box(ax, xy, w, h, text, fc="#eef4f7", ec="#2f4858", fontsize=9):
    patch = FancyBboxPatch(
        xy,
        w,
        h,
        boxstyle="round,pad=0.03,rounding_size=0.04",
        linewidth=1.3,
        facecolor=fc,
        edgecolor=ec,
    )
    ax.add_patch(patch)
    ax.text(xy[0] + w / 2, xy[1] + h / 2, text, ha="center", va="center", fontsize=fontsize, wrap=True)
    return patch


def arrow(ax, start, end, text=None, color="#3d5a80"):
    arr = FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=12, linewidth=1.4, color=color)
    ax.add_patch(arr)
    if text:
        ax.text(
            (start[0] + end[0]) / 2,
            (start[1] + end[1]) / 2 + 0.04,
            text,
            ha="center",
            va="bottom",
            fontsize=8,
            color=color,
        )


def figure_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(10.4, 5.0))
    ax.axis("off")
    ax.set_xlim(-0.02, 1.04)
    ax.set_ylim(0, 1)
    ax.set_title("Hybrid backend: v3 dynamics with frozen v3.5 physical regularizer", fontsize=12, weight="bold", pad=10)

    box(ax, (0.03, 0.56), 0.16, 0.18, "State s_t\npolicy obs", fc="#f7f7f7")
    box(ax, (0.27, 0.60), 0.19, 0.17, "PPO policy\npi_theta(a|s)", fc="#e9f5db")
    box(ax, (0.55, 0.63), 0.19, 0.16, "v3 surrogate\ntrain-time dynamics", fc="#dceefb")
    box(ax, (0.55, 0.31), 0.19, 0.16, "calibrated v3.5\nfrozen physical twin", fc="#fde2e4")
    box(ax, (0.29, 0.20), 0.20, 0.15, "PPO objective\n+ disagreement loss", fc="#fff3bf")
    box(ax, (0.83, 0.58), 0.14, 0.20, "next state\nreward", fc="#f7f7f7")

    arrow(ax, (0.19, 0.65), (0.27, 0.68), "s_t")
    arrow(ax, (0.46, 0.69), (0.55, 0.71), "a_t")
    arrow(ax, (0.74, 0.71), (0.83, 0.68))
    arrow(ax, (0.46, 0.62), (0.55, 0.39), "same (s,a)", color="#b23a48")
    arrow(ax, (0.55, 0.39), (0.49, 0.28), color="#b23a48")
    arrow(ax, (0.55, 0.67), (0.49, 0.31), color="#3d5a80")
    arrow(ax, (0.38, 0.35), (0.36, 0.60), "L_total", color="#a67c00")
    ax.text(
        0.50,
        0.08,
        r"$L_{total}=L_{PPO}+\lambda_{temp}\|T_{v3}-T_{v3.5}\|^2+\lambda_{power}\|P_{v3}-P_{v3.5}\|^2$",
        ha="center",
        fontsize=10,
    )
    fig.subplots_adjust(left=0.03, right=0.98, top=0.86, bottom=0.12)
    save(fig, "main_fig1_pipeline_schematic")


def figure_fidelity_gap() -> None:
    arch = pd.read_csv(ROOT / "reports" / "hou_evins_architecture_justification_table.csv")
    pred = pd.read_csv(ROOT / "reports" / "hou_evins_predictive_validity_table.csv")
    rows = []
    for model, label in [("v3", "v3"), ("v35_calibrated", "v3.5 calibrated"), ("hybrid_l010", "hybrid_l010")]:
        if model == "v35_calibrated":
            pred_val = float(pred[(pred["model"] == "v3.5_calibrated") & (pred["horizon"] == "24h")]["RMSE_T"].iloc[0])
        else:
            pred_val = float(pred[(pred["model"] == model) & (pred["horizon"] == "24h")]["RMSE_T"].iloc[0])
        transfer = arch[arch["variant"].eq(model)]
        live = float(np.nanmean([transfer["peak_transfer_temp_rmse_c"].iloc[0], transfer["typical_transfer_temp_rmse_c"].iloc[0]]))
        rows.append((label, pred_val, live))
    df = pd.DataFrame(rows, columns=["model", "predictive_24h_rmse", "live_transfer_rmse"])

    x = np.arange(len(df))
    width = 0.36
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.bar(x - width / 2, df["predictive_24h_rmse"], width, label="Predictive 24h RMSE", color="#4c78a8")
    ax.bar(x + width / 2, df["live_transfer_rmse"], width, label="Live BOPTEST transfer RMSE", color="#f58518")
    ax.set_xticks(x, df["model"])
    ax.set_ylabel("Temperature RMSE (C)")
    ax.set_title("Fidelity-to-control gap", weight="bold")
    ax.set_ylim(0, float(df[["predictive_24h_rmse", "live_transfer_rmse"]].to_numpy().max()) * 1.22)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, loc="upper left")
    for i, (pred_val, live_val) in enumerate(zip(df["predictive_24h_rmse"], df["live_transfer_rmse"])):
        ax.text(i - width / 2, pred_val + 0.07, f"{pred_val:.2f}", ha="center", fontsize=8)
        ax.text(i + width / 2, live_val + 0.07, f"{live_val:.2f}", ha="center", fontsize=8)
        if pred_val > 0:
            ax.text(i, max(pred_val, live_val) + 0.25, f"{live_val / pred_val:.1f}x", ha="center", fontsize=9, color="#7a3e00")
    save(fig, "main_fig3_fidelity_to_rl_gap")


def figure_transfer_heatmap() -> None:
    matrix = pd.read_csv(ROOT / "reports" / "block3_transfer_matrix.csv")
    regimes = ["none", "partial", "full"]
    short_tests = ["heat pump", "hydronic", "commercial"]
    vals = np.full((len(short_tests), len(regimes)), np.nan)
    labels = [["" for _ in regimes] for _ in short_tests]
    for i, row in matrix.iterrows():
        vals[i, 0] = 1 if row["none_controller_verdict"] == "PASS" else -1
        labels[i][0] = row["none_controller_verdict"]
        # Partial live KPI is unchanged under frozen-controller scope; unrun cells are structural, not missing evidence.
        vals[i, 1] = vals[i, 0]
        labels[i][1] = "same as\nnone"
        vals[i, 2] = 1 if row["full_controller_verdict"] == "PASS" else -1
        labels[i][2] = row["full_controller_verdict"]

    fig, ax = plt.subplots(figsize=(7.6, 3.6))
    cmap = plt.matplotlib.colors.ListedColormap(["#d73027", "#1a9850"])
    norm = plt.matplotlib.colors.BoundaryNorm([-1.5, 0, 1.5], cmap.N)
    ax.imshow(vals, cmap=cmap, norm=norm, aspect="auto")
    ax.set_xticks(np.arange(len(regimes)), regimes)
    ax.set_yticks(np.arange(len(short_tests)), short_tests)
    ax.set_title("Block 3 controller verdict heatmap", weight="bold")
    for i in range(len(short_tests)):
        for j in range(len(regimes)):
            ax.text(j, i, labels[i][j], ha="center", va="center", color="white", fontsize=9, weight="bold")
    ax.set_xlabel("Recalibration regime")
    ax.set_ylabel("Target testcase")
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    save(fig, "main_fig5_block3_transfer_verdict_heatmap")


def figure_czon_consistency() -> None:
    matrix = pd.read_csv(ROOT / "reports" / "block3_transfer_matrix.csv")
    labels = ["heat pump", "hydronic", "commercial"]
    ratios = matrix["c_zon_ratio_vs_bestest_air"].to_numpy(dtype=float)
    mean = ratios.mean()
    std = ratios.std(ddof=0)
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    bars = ax.bar(labels, ratios, color=["#4c78a8", "#72b7b2", "#f58518"], width=0.58)
    ax.axhline(mean, color="#333333", linestyle="--", linewidth=1.2, label=f"mean={mean:.2f}x")
    ax.fill_between([-0.5, 2.5], mean - std, mean + std, color="#999999", alpha=0.12, label=f"+/-1 sigma={std:.2f}x")
    ax.set_ylim(0, max(2.3, ratios.max() + 0.25))
    ax.set_ylabel("C_zon ratio vs bestest_air")
    ax.set_title("Hydronic-family C_zon consistency", weight="bold")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, loc="lower right")
    for bar, val in zip(bars, ratios):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.04, f"{val:.2f}x", ha="center", fontsize=9)
    save(fig, "main_fig6_block3_czon_consistency")


def main() -> None:
    figure_pipeline()
    figure_fidelity_gap()
    figure_transfer_heatmap()
    figure_czon_consistency()


if __name__ == "__main__":
    main()
