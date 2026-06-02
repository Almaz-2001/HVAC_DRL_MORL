"""
Generate the two main-text PDF figures of the Q1 paper:

- fig_block1_surrogates.pdf
    Block 1 visual: surrogate fidelity. Two panels.
      Panel (a) Multi-horizon predictive validity. Line plot of RMSE_T over
                {1h, 4h, 8h, 24h} for raw_v35 vs calibrated_v35 on the
                prepared rollout corpus.
      Panel (b) Fidelity-to-RL gap. Grouped bars comparing 24h predictive
                rollout RMSE (held-out) with live BOPTEST closed-loop
                transfer RMSE for v3, v3.5 calibrated, and hybrid_l010.
                The 'gap' is the central visual: v3.5 has the best
                predictive RMSE but the worst transfer RMSE.

- fig_block2_pareto_vs_pi.pdf
    Block 2 visual: MORL Pareto front + PI baseline reference. Single
    panel scatter of (yearly violation %, yearly energy kWh) for the 5
    MORL preference vectors, the BOPTEST built-in PI baseline, and the
    thermostatic anchors. Pre-registered and practical-deployment
    canonical points are highlighted. A 5% violation threshold is drawn
    as a vertical line for deployment reference.

Inputs:
    reports/hou_evins_predictive_validity_table.csv
    reports/morl_pareto_front_table.csv
    reports/pi_baseline_yearly_table.csv

Outputs:
    paper/figures/fig_block1_surrogates.pdf
    paper/figures/fig_block2_pareto_vs_pi.pdf

Safe to rerun. Missing inputs produce a placeholder PDF with a red
in-figure note rather than raising.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PAPER_DIR = Path(__file__).resolve().parent
FIG_DIR = PAPER_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
REPO_ROOT = PAPER_DIR.parent


def _data_root() -> Path:
    candidates = [REPO_ROOT]
    parts = REPO_ROOT.parts
    if ".claude" in parts:
        idx = parts.index(".claude")
        candidates.append(Path(*parts[:idx]))
    for cand in candidates:
        if (cand / "reports").exists():
            return cand
    return REPO_ROOT


DATA_ROOT = _data_root()


def _find_csv(rel_path: str) -> Optional[Path]:
    for root in (REPO_ROOT, DATA_ROOT):
        path = root / rel_path
        if path.exists():
            return path
    return None


# ---------------------------------------------------------------------------
# Style — consistent palette across both figures
# ---------------------------------------------------------------------------

COLORS = {
    "raw_v35":        "#888888",  # neutral gray
    "v3":             "#1f77b4",  # blue
    "v35_calibrated": "#d62728",  # red
    "hybrid_l010":    "#2ca02c",  # green
    "pi_baseline":    "#7f7f7f",  # gray, distinct from raw_v35
    "morl_endpoint":  "#9467bd",  # purple for extreme preferences
    "morl_canonical_pre":   "#1f77b4",  # blue, pre-registered
    "morl_canonical_prac":  "#ff7f0e",  # orange, practical-deployment
    "morl_intermediate":    "#bcbd22",  # olive
    "morl_energy_collapse": "#e377c2",  # pink
}

MARKERS = {
    "raw_v35":        "o",
    "v3":             "s",
    "v35_calibrated": "D",
    "hybrid_l010":    "^",
    "pi_baseline":    "P",
    "morl_endpoint":  "X",
    "thermostatic":   "v",
}


def _set_paper_style() -> None:
    plt.rcParams.update({
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": "--",
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })


def _placeholder_figure(out_path: Path, title: str, message: str) -> None:
    fig, ax = plt.subplots(figsize=(6.0, 3.5))
    ax.set_axis_off()
    ax.text(
        0.5, 0.5,
        f"PLACEHOLDER — {title}\n\n{message}",
        ha="center", va="center", color="red", wrap=True,
        transform=ax.transAxes,
    )
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[WARN] {out_path.name}: placeholder ({message})")


# ---------------------------------------------------------------------------
# Figure 1 — Block 1 surrogate fidelity
# ---------------------------------------------------------------------------

def build_fig_block1(out_path: Path) -> None:
    pred_csv = _find_csv("reports/hou_evins_predictive_validity_table.csv")
    if pred_csv is None:
        _placeholder_figure(out_path, "Block 1 surrogates",
                            "reports/hou_evins_predictive_validity_table.csv not found")
        return

    df = pd.read_csv(pred_csv)

    # Panel (a) data: multi-horizon RMSE_T for raw_v35 and calibrated_v35
    pred = df[(df["validity_type"] == "predictive_prepared_rollout")
              & (df["metric"] == "RMSE_T_C")].copy()
    pred["horizon_h"] = pred["horizon"].str.replace("rollout_", "").str.replace("h", "").astype(int)
    pred = pred.sort_values(["variant", "horizon_h"])

    horizons = sorted(pred["horizon_h"].unique())
    raw_rmse = [
        pred[(pred["variant"] == "raw_v35") & (pred["horizon_h"] == h)]["value"].iloc[0]
        if not pred[(pred["variant"] == "raw_v35") & (pred["horizon_h"] == h)].empty
        else np.nan
        for h in horizons
    ]
    cal_rmse = [
        pred[(pred["variant"] == "v35_calibrated") & (pred["horizon_h"] == h)]["value"].iloc[0]
        if not pred[(pred["variant"] == "v35_calibrated") & (pred["horizon_h"] == h)].empty
        else np.nan
        for h in horizons
    ]

    # Panel (b) data: fidelity-to-RL gap
    # Predictive: take 24h rollout RMSE_T per variant
    # Transfer: take mean of peak+typical live RMSE_T per variant
    gap_variants = ["v3_hourly_direct_tsup", "v35_calibrated", "hybrid_l010"]
    gap_labels = ["v3", "v3.5\ncalibrated", "hybrid\\_l010"]

    def transfer_rmse(variant: str) -> float:
        sel = df[
            (df["variant"] == variant)
            & (df["validity_type"] == "predictive_transfer")
            & (df["metric"] == "RMSE_T_C")
        ]
        if sel.empty:
            return np.nan
        return float(sel["value"].mean())

    def predictive_24h(variant: str) -> float:
        sel = df[
            (df["variant"] == variant)
            & (df["validity_type"] == "predictive_prepared_rollout")
            & (df["horizon"] == "rollout_24h")
            & (df["metric"] == "RMSE_T_C")
        ]
        if sel.empty:
            return np.nan
        return float(sel["value"].iloc[0])

    predictive_vals = [predictive_24h(v) for v in gap_variants]
    transfer_vals   = [transfer_rmse(v) for v in gap_variants]

    # ---- draw ----
    _set_paper_style()
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(10.5, 4.0))

    # Panel (a)
    ax_a.plot(horizons, raw_rmse, marker="o", linewidth=2, color=COLORS["raw_v35"],
              label="raw v3.5 (uncalibrated)")
    ax_a.plot(horizons, cal_rmse, marker="D", linewidth=2, color=COLORS["v35_calibrated"],
              label="calibrated v3.5")
    ax_a.set_xlabel("Rollout horizon (hours)")
    ax_a.set_ylabel("Temperature RMSE (°C)")
    ax_a.set_title("(a) Multi-horizon predictive validity")
    ax_a.set_xticks(horizons)
    ax_a.legend(loc="center right", framealpha=0.9)
    ax_a.set_ylim(0, max(max(raw_rmse), max(cal_rmse)) * 1.15)
    # Annotation: the gap collapses with calibration
    if not np.isnan(cal_rmse[-1]) and not np.isnan(raw_rmse[-1]):
        ax_a.annotate(
            f"{(1 - cal_rmse[-1]/raw_rmse[-1])*100:.0f} reduction\nat 24 h",
            xy=(24, cal_rmse[-1]), xytext=(15, (raw_rmse[-1] + cal_rmse[-1]) / 2),
            fontsize=9, ha="center",
            arrowprops=dict(arrowstyle="->", color="black", alpha=0.6, lw=1),
        )

    # Panel (b) - grouped bars
    x = np.arange(len(gap_variants))
    width = 0.38
    bars_pred = ax_b.bar(x - width/2, predictive_vals, width,
                         color=COLORS["v35_calibrated"], alpha=0.85,
                         label="predictive (24 h, held-out)")
    bars_trans = ax_b.bar(x + width/2, transfer_vals, width,
                          color=COLORS["v3"], alpha=0.85,
                          label="live BOPTEST transfer")
    ax_b.set_xticks(x)
    ax_b.set_xticklabels(gap_labels)
    ax_b.set_ylabel("Temperature RMSE (°C)")
    ax_b.set_title("(b) Fidelity-to-RL gap")
    ax_b.legend(loc="upper right", framealpha=0.9)

    # Value labels on top of each bar
    for bars, vals in [(bars_pred, predictive_vals), (bars_trans, transfer_vals)]:
        for bar, v in zip(bars, vals):
            if not np.isnan(v):
                ax_b.text(bar.get_x() + bar.get_width()/2, v + 0.08,
                          f"{v:.2f}", ha="center", va="bottom", fontsize=9)

    # Annotate the v3.5 gap explicitly
    if not np.isnan(predictive_vals[1]) and not np.isnan(transfer_vals[1]):
        gap_factor = transfer_vals[1] / predictive_vals[1]
        ax_b.annotate(
            f"{gap_factor:.1f}× gap",
            xy=(1 + width/2, transfer_vals[1]),
            xytext=(1, max(transfer_vals) * 0.65),
            fontsize=10, color="darkred", fontweight="bold", ha="center",
            arrowprops=dict(arrowstyle="->", color="darkred", lw=1.5),
        )

    ax_b.set_ylim(0, max([v for v in transfer_vals if not np.isnan(v)]) * 1.20)

    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[OK] {out_path.name}: 2 panels")


# ---------------------------------------------------------------------------
# Figure 2 — Block 2 Pareto vs PI
# ---------------------------------------------------------------------------

def build_fig_block2(out_path: Path) -> None:
    pareto_csv = _find_csv("reports/morl_pareto_front_table.csv")
    pi_csv = _find_csv("reports/pi_baseline_yearly_table.csv")
    if pareto_csv is None or pi_csv is None:
        _placeholder_figure(out_path, "Block 2 Pareto vs PI",
                            "missing morl_pareto or pi_baseline CSV")
        return

    pareto = pd.read_csv(pareto_csv)
    pi = pd.read_csv(pi_csv)

    _set_paper_style()
    fig, ax = plt.subplots(figsize=(8.0, 5.5))

    # ---- Plot 5 MORL Pareto points ----
    # Color by canonical designation
    designation_color = {
        "pareto_endpoint_comfort":         COLORS["morl_endpoint"],
        "practical_deployment_canonical":  COLORS["morl_canonical_prac"],
        "pre_registered_canonical":        COLORS["morl_canonical_pre"],
        "pareto_intermediate":             COLORS["morl_intermediate"],
        "pareto_endpoint_energy_collapse": COLORS["morl_energy_collapse"],
    }
    designation_label = {
        "pareto_endpoint_comfort":         "MORL (1.00, 0.00)\ncomfort endpoint",
        "practical_deployment_canonical":  "MORL (0.75, 0.25)\npractical canonical",
        "pre_registered_canonical":        "MORL (0.50, 0.50)\npre-registered canonical",
        "pareto_intermediate":             "MORL (0.25, 0.75)",
        "pareto_endpoint_energy_collapse": "MORL (0.00, 1.00)\nenergy collapse",
    }

    pareto_grouped = (
        pareto.groupby(["canonical_designation"], as_index=False)
        .agg(
            violation_pct=("violation_pct", "mean"),
            energy_kwh=("energy_kwh", "mean"),
        )
    )

    # Sort by violation_pct for clean visual flow
    pareto_grouped = pareto_grouped.sort_values("violation_pct").reset_index(drop=True)
    for _, r in pareto_grouped.iterrows():
        is_canonical = r["canonical_designation"] in (
            "pre_registered_canonical", "practical_deployment_canonical"
        )
        ax.scatter(
            r["violation_pct"], r["energy_kwh"],
            s=260 if is_canonical else 160,
            color=designation_color[r["canonical_designation"]],
            edgecolor="black", linewidth=1.5 if is_canonical else 0.8,
            marker="*" if is_canonical else "o",
            zorder=4 if is_canonical else 3,
            label=designation_label[r["canonical_designation"]],
        )

    # Pareto-curve guide line through the 4 admissible (non-collapse) points
    admissible = pareto_grouped[
        pareto_grouped["canonical_designation"] != "pareto_endpoint_energy_collapse"
    ].sort_values("violation_pct")
    if len(admissible) >= 2:
        ax.plot(
            admissible["violation_pct"], admissible["energy_kwh"],
            linestyle="--", color="gray", alpha=0.5, linewidth=1.2, zorder=1,
            label="Pareto guide (admissible region)",
        )

    # ---- PI baseline reference ----
    pi_row = pi[pi["controller"] == "pi_builtin"].iloc[0]
    ax.scatter(
        pi_row["violation_pct"], pi_row["energy_kwh"],
        s=300, color=COLORS["pi_baseline"], edgecolor="black",
        linewidth=1.5, marker="P", zorder=5,
        label=f"BOPTEST PI (built-in)\nm_s={pi_row['m_s']:.3f}",
    )

    # ---- Vertical 5% deployment threshold ----
    ax.axvline(5.0, linestyle=":", color="red", alpha=0.6, linewidth=1.5)
    ax.text(5.0, ax.get_ylim()[1] * 0.02 if ax.get_ylim()[1] > 0 else 5.0,
            " 5% deployment\n threshold",
            color="red", fontsize=9, va="bottom", ha="left", alpha=0.8)

    ax.set_xlabel("Yearly comfort violation rate (%)")
    ax.set_ylabel("Yearly energy consumption (kWh)")
    ax.set_title("Block 2: MORL Pareto front vs BOPTEST PI baseline (yearly)")

    # Log-scale x because violation spans 1.5% to 87%
    ax.set_xscale("log")
    ax.set_xlim(0.8, 130)

    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), framealpha=0.95,
              fontsize=8, frameon=True)

    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[OK] {out_path.name}: {len(pareto_grouped)} Pareto points + PI baseline")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"[INFO] paper dir : {PAPER_DIR}")
    print(f"[INFO] data root : {DATA_ROOT}")
    build_fig_block1(FIG_DIR / "fig_block1_surrogates.pdf")
    build_fig_block2(FIG_DIR / "fig_block2_pareto_vs_pi.pdf")


if __name__ == "__main__":
    main()
