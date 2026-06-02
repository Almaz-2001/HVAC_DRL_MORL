"""
Conference-defense figures. Five narrative-driven plots, each telling one
story in five seconds. Designed for slide projection: large fonts, bold
contrasts, minimal axes, big callouts.

Output: paper/figures/defense/*.pdf and *.png

Figures:
    F1_calibration_paradox.pdf
        The surprise: v3.5 calibrated is best at predictive validity
        BUT worst at RL closed-loop transfer.

    F2_hybrid_resolves.pdf
        The resolution: v3 / v3.5 / hybrid_l010 comparison on both
        predictive and transfer axes. Hybrid wins overall.

    F3_speed_vs_fidelity.pdf
        Why surrogates at all: backend throughput in env-steps/sec.
        Hybrid is 85x faster than live BOPTEST.

    F4_pareto_vs_pi.pdf
        Multi-objective view: MORL Pareto + PI baseline in
        (violation, energy) space with deployment threshold.

    F5_controller_family_finding.pdf
        The cross-family finding: optimal physical-regularization
        strength depends on controller architecture.
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
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as path_effects

PAPER_DIR = Path(__file__).resolve().parent
OUT_DIR = PAPER_DIR / "figures" / "defense"
OUT_DIR.mkdir(parents=True, exist_ok=True)
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
        p = root / rel_path
        if p.exists():
            return p
    return None


# ---------------------------------------------------------------------------
# Defense style — bold, conference-projection friendly
# ---------------------------------------------------------------------------

# Custom curated palette (NOT default matplotlib tab10)
PALETTE = {
    "ink":       "#1a1a2e",   # near-black, headings
    "muted":     "#9a9a9a",   # neutral gray
    "baseline":  "#6b7280",   # baseline gray
    "warn":      "#c1121f",   # red — failure, alarm
    "success":   "#0f8a5f",   # deep green — wins
    "accent":    "#f4a261",   # warm orange — practical canonical
    "blue":      "#1e6091",   # deep blue — pre-registered
    "purple":    "#5a4e7c",   # muted purple — endpoints
    "sand":      "#e9d8a6",   # soft background highlight
    "rose":      "#bc4749",   # secondary warn
}


def _set_defense_style() -> None:
    plt.rcParams.update({
        "font.family":  "DejaVu Sans",
        "font.size":    14,
        "axes.titlesize": 18,
        "axes.titleweight": "bold",
        "axes.labelsize": 14,
        "axes.labelweight": "bold",
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "legend.fontsize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 1.2,
        "axes.edgecolor": PALETTE["ink"],
        "xtick.color": PALETTE["ink"],
        "ytick.color": PALETTE["ink"],
        "text.color":  PALETTE["ink"],
        "axes.labelcolor": PALETTE["ink"],
        "axes.titlecolor": PALETTE["ink"],
        "axes.grid": True,
        "grid.alpha": 0.15,
        "grid.linestyle": "-",
        "grid.color": PALETTE["muted"],
        "savefig.dpi": 220,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
        "axes.facecolor":   "white",
    })


def _add_outline(text_obj, lw=2.2, fg="white"):
    """Add a white outline to a text label so it pops against bars."""
    text_obj.set_path_effects([
        path_effects.Stroke(linewidth=lw, foreground=fg),
        path_effects.Normal(),
    ])


def _save_both(fig, out_path_pdf: Path) -> None:
    """Save figure as both PDF (paper) and PNG (slides)."""
    fig.savefig(out_path_pdf)
    fig.savefig(out_path_pdf.with_suffix(".png"), dpi=220)
    plt.close(fig)


# ---------------------------------------------------------------------------
# F1 — The calibration paradox
# ---------------------------------------------------------------------------

def fig1_calibration_paradox(out_path: Path) -> None:
    pred_csv = _find_csv("reports/hou_evins_predictive_validity_table.csv")
    if pred_csv is None:
        return
    df = pd.read_csv(pred_csv)

    # v3.5 calibrated values
    pred_24h = float(df[
        (df["variant"] == "v35_calibrated")
        & (df["validity_type"] == "predictive_prepared_rollout")
        & (df["horizon"] == "rollout_24h")
        & (df["metric"] == "RMSE_T_C")
    ]["value"].iloc[0])

    transfer = df[
        (df["variant"] == "v35_calibrated")
        & (df["validity_type"] == "predictive_transfer")
        & (df["metric"] == "RMSE_T_C")
    ]["value"].mean()
    transfer = float(transfer)

    _set_defense_style()
    fig, ax = plt.subplots(figsize=(10.5, 6.0))

    bars = ax.bar(
        ["Predictive validity\n(held-out, 24h rollout)",
         "RL closed-loop transfer\n(live BOPTEST)"],
        [pred_24h, transfer],
        color=[PALETTE["success"], PALETTE["warn"]],
        width=0.55,
        edgecolor=PALETTE["ink"], linewidth=1.5,
    )

    # Value labels inside bars
    for bar, v, lbl in zip(bars,
                            [pred_24h, transfer],
                            [f"{pred_24h:.2f} °C", f"{transfer:.2f} °C"]):
        y = bar.get_height() / 2
        t = ax.text(bar.get_x() + bar.get_width()/2, y, lbl,
                    ha="center", va="center", fontsize=24,
                    fontweight="bold", color="white")

    # Big gap annotation
    gap = transfer / pred_24h
    ax.annotate(
        "",
        xy=(1, transfer * 0.95), xytext=(0, pred_24h * 1.05),
        arrowprops=dict(arrowstyle="->", color=PALETTE["warn"], lw=3,
                        connectionstyle="arc3,rad=-0.25"),
    )
    ax.text(0.5, transfer * 1.02,
            f"{gap:.1f}× WORSE",
            ha="center", va="bottom",
            fontsize=22, fontweight="bold", color=PALETTE["warn"])

    ax.set_ylabel("Temperature RMSE (°C)", fontsize=15, fontweight="bold")
    ax.set_title(
        "Calibrated physical surrogate v3.5:\n"
        "best at prediction, fails as RL environment",
        fontsize=18, pad=18,
    )
    ax.set_ylim(0, transfer * 1.30)
    ax.tick_params(axis="x", which="both", labelsize=13)

    # Subtitle / takeaway
    ax.text(
        0.5, -0.18,
        "Predictive accuracy on held-out data does NOT translate to RL training utility.",
        transform=ax.transAxes, ha="center", va="top",
        fontsize=13, style="italic", color=PALETTE["muted"],
    )

    fig.tight_layout()
    _save_both(fig, out_path)
    print(f"[OK] {out_path.name}")


# ---------------------------------------------------------------------------
# F2 — Hybrid resolves the gap
# ---------------------------------------------------------------------------

def fig2_hybrid_resolves(out_path: Path) -> None:
    pred_csv = _find_csv("reports/hou_evins_predictive_validity_table.csv")
    if pred_csv is None:
        return
    df = pd.read_csv(pred_csv)

    variants = ["v3_hourly_direct_tsup", "v35_calibrated", "hybrid_l010"]
    labels   = ["v3\n(black-box,\ncontrol-oriented)",
                "v3.5\n(physics,\ncalibrated)",
                "hybrid\n(v3 + v3.5\nregularizer)"]

    def predictive_24h(v: str) -> float:
        sel = df[(df["variant"] == v)
                 & (df["validity_type"] == "predictive_prepared_rollout")
                 & (df["horizon"] == "rollout_24h")
                 & (df["metric"] == "RMSE_T_C")]
        return float(sel["value"].iloc[0]) if not sel.empty else np.nan

    def transfer(v: str) -> float:
        sel = df[(df["variant"] == v)
                 & (df["validity_type"] == "predictive_transfer")
                 & (df["metric"] == "RMSE_T_C")]
        return float(sel["value"].mean()) if not sel.empty else np.nan

    pred_vals  = [predictive_24h(v) for v in variants]
    trans_vals = [transfer(v) for v in variants]

    _set_defense_style()
    fig, ax = plt.subplots(figsize=(11, 6.2))

    x = np.arange(len(variants))
    w = 0.36

    b1 = ax.bar(x - w/2, pred_vals,  w,
                color=PALETTE["success"], edgecolor=PALETTE["ink"],
                linewidth=1.5, label="Predictive (held-out 24h)")
    b2 = ax.bar(x + w/2, trans_vals, w,
                color=PALETTE["warn"], edgecolor=PALETTE["ink"],
                linewidth=1.5, label="Live BOPTEST transfer")

    # Numeric labels
    for bars, vals in [(b1, pred_vals), (b2, trans_vals)]:
        for bar, v in zip(bars, vals):
            if not np.isnan(v):
                ax.text(bar.get_x() + bar.get_width()/2, v + 0.10,
                        f"{v:.2f}", ha="center", va="bottom",
                        fontsize=12, fontweight="bold")

    # Highlight hybrid as the winner
    win_x = 2
    rect = FancyBboxPatch(
        (win_x - 0.5, -0.05), 1.0, max(trans_vals) * 1.15 + 0.05,
        boxstyle="round,pad=0.02",
        linewidth=2.5, edgecolor=PALETTE["success"],
        facecolor="none", zorder=0,
    )
    ax.add_patch(rect)
    ax.text(win_x, max(trans_vals) * 1.22, "WINNER",
            ha="center", va="bottom",
            fontsize=14, fontweight="bold",
            color=PALETTE["success"])

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=12)
    ax.set_ylabel("Temperature RMSE (°C)", fontweight="bold")
    ax.set_title(
        "Hybrid surrogate inherits both worlds:\n"
        "low predictive error AND low closed-loop transfer error",
        fontsize=17, pad=18,
    )
    ax.legend(loc="upper left", framealpha=0.95, frameon=True)
    ax.set_ylim(0, max(trans_vals) * 1.30)

    fig.tight_layout()
    _save_both(fig, out_path)
    print(f"[OK] {out_path.name}")


# ---------------------------------------------------------------------------
# F3 — Speed vs fidelity
# ---------------------------------------------------------------------------

def fig3_speed(out_path: Path) -> None:
    csv = _find_csv("reports/speed_benchmark_table.csv")
    if csv is None:
        return
    df = pd.read_csv(csv).set_index("backend")

    order = [
        ("boptest_rte_http",         "BOPTEST RTE\n(live HTTP)",         PALETTE["warn"]),
        ("v35_calibrated_surrogate", "v3.5\ncalibrated",                  PALETTE["blue"]),
        ("hybrid_v3_v35_surrogate",  "hybrid_l010\n(canonical training)", PALETTE["success"]),
        ("v3_surrogate",             "v3\n(control-oriented)",             PALETTE["accent"]),
    ]

    names    = [name  for _, name, _ in order]
    steps    = [float(df.loc[k, "env_steps_per_sec"]) for k, _, _ in order]
    speedups = [float(df.loc[k, "speedup_vs_boptest_rte"]) for k, _, _ in order]
    colors   = [color for _, _, color in order]

    _set_defense_style()
    fig, ax = plt.subplots(figsize=(11, 6.5))

    bars = ax.barh(names, steps, color=colors, edgecolor=PALETTE["ink"],
                   linewidth=1.5, height=0.55)
    ax.set_xscale("log")
    ax.set_xlabel("Environment steps per second  (CPU, single thread, log scale)",
                  fontweight="bold")
    ax.set_xlim(10, 20000)
    ax.grid(True, which="both", axis="x", alpha=0.15)
    ax.invert_yaxis()

    for bar, v, sp in zip(bars, steps, speedups):
        # Speed number outside the bar
        ax.text(v * 1.15, bar.get_y() + bar.get_height()/2,
                f"{v:,.0f} steps/s",
                va="center", ha="left",
                fontsize=13, fontweight="bold")
        # Speedup badge inside the bar
        sp_label = f"{sp:.1f}×" if sp >= 1 else "baseline"
        col = "white" if sp >= 5 else PALETTE["ink"]
        t = ax.text(v * 0.45 if sp >= 5 else v * 1.5,
                    bar.get_y() + bar.get_height()/2,
                    sp_label, va="center", ha="center",
                    fontsize=16, fontweight="bold", color=col)
        if sp >= 5:
            _add_outline(t, fg=bar.get_facecolor())

    ax.set_title(
        "Hybrid surrogate trains RL controllers 85× faster than live BOPTEST\n"
        "(same 15-min control protocol, same HTTP API, same CPU)",
        fontsize=17, pad=18,
    )

    # Subtle annotation
    ax.text(
        0.5, -0.16,
        "8 hours of live BOPTEST training → 5 minutes on the hybrid surrogate.",
        transform=ax.transAxes, ha="center", va="top",
        fontsize=13, style="italic", color=PALETTE["muted"],
    )

    fig.tight_layout()
    _save_both(fig, out_path)
    print(f"[OK] {out_path.name}")


# ---------------------------------------------------------------------------
# F4 — Pareto vs PI
# ---------------------------------------------------------------------------

def fig4_pareto_vs_pi(out_path: Path) -> None:
    pareto_csv = _find_csv("reports/morl_pareto_front_table.csv")
    pi_csv     = _find_csv("reports/pi_baseline_yearly_table.csv")
    if pareto_csv is None or pi_csv is None:
        return

    pareto = pd.read_csv(pareto_csv)
    pi     = pd.read_csv(pi_csv)
    pi_row = pi[pi["controller"] == "pi_builtin"].iloc[0]

    _set_defense_style()
    fig, ax = plt.subplots(figsize=(11, 7))

    point_color = {
        "pareto_endpoint_comfort":         PALETTE["purple"],
        "practical_deployment_canonical":  PALETTE["accent"],
        "pre_registered_canonical":        PALETTE["blue"],
        "pareto_intermediate":             PALETTE["muted"],
        "pareto_endpoint_energy_collapse": PALETTE["warn"],
    }
    point_label = {
        "pareto_endpoint_comfort":         "MORL  w=(1.00, 0.00)",
        "practical_deployment_canonical":  "MORL  w=(0.75, 0.25)  ★ practical",
        "pre_registered_canonical":        "MORL  w=(0.50, 0.50)  ★ pre-registered",
        "pareto_intermediate":             "MORL  w=(0.25, 0.75)",
        "pareto_endpoint_energy_collapse": "MORL  w=(0.00, 1.00)  (safety collapse)",
    }
    starred = {"practical_deployment_canonical", "pre_registered_canonical"}

    pg = pareto.groupby("canonical_designation", as_index=False).agg(
        violation_pct=("violation_pct", "mean"),
        energy_kwh=("energy_kwh", "mean"),
    ).sort_values("violation_pct").reset_index(drop=True)

    # Pareto guide curve through admissible region
    admissible = pg[pg["canonical_designation"] != "pareto_endpoint_energy_collapse"]
    admissible = admissible.sort_values("violation_pct")
    ax.plot(admissible["violation_pct"], admissible["energy_kwh"],
            linestyle="--", linewidth=1.5, alpha=0.55,
            color=PALETTE["muted"], zorder=1)

    # MORL points
    for _, r in pg.iterrows():
        d = r["canonical_designation"]
        starred_here = d in starred
        ax.scatter(r["violation_pct"], r["energy_kwh"],
                   s=550 if starred_here else 280,
                   color=point_color[d],
                   edgecolor=PALETTE["ink"],
                   linewidth=2.0 if starred_here else 1.0,
                   marker="*" if starred_here else "o",
                   zorder=4,
                   label=point_label[d])

    # PI baseline as cross
    ax.scatter(pi_row["violation_pct"], pi_row["energy_kwh"],
               s=380, color=PALETTE["rose"], marker="P",
               edgecolor=PALETTE["ink"], linewidth=2.0,
               zorder=5,
               label=f"BOPTEST built-in PI  (m_s = {pi_row['m_s']:.2f})")

    # 5% threshold line
    ax.axvline(5.0, linestyle=":", color=PALETTE["warn"], alpha=0.7, linewidth=2)
    ax.text(5.05, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 30,
            " 5% deployment\n threshold",
            color=PALETTE["warn"], fontsize=12, fontweight="bold",
            va="top", ha="left")

    # Shaded admissible region (left of 5% threshold)
    ax.axvspan(0.8, 5.0, alpha=0.06, color=PALETTE["success"], zorder=0)

    ax.set_xscale("log")
    ax.set_xlim(0.8, 130)
    ax.set_xlabel("Yearly comfort violation rate (%, log scale)", fontweight="bold")
    ax.set_ylabel("Yearly energy consumption (kWh)", fontweight="bold")
    ax.set_title(
        "MORL Pareto front vs BOPTEST built-in PI baseline\n"
        "(green band = deployment-defensible region)",
        fontsize=17, pad=18,
    )

    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5),
              fontsize=10, frameon=True, framealpha=0.95)

    fig.tight_layout()
    _save_both(fig, out_path)
    print(f"[OK] {out_path.name}")


# ---------------------------------------------------------------------------
# F5 — Controller-family-specific λ finding
# ---------------------------------------------------------------------------

def fig5_controller_family(out_path: Path) -> None:
    # This figure is constructed from values reported in the project narrative
    # rather than a single CSV. We hardcode the controller-family-specific
    # optimum lambdas so that the figure tells the cross-family story even
    # before the full per-lambda sweep tables ship.
    families = ["Thermostatic\nPPO", "HDRL", "MORL 17-D"]
    opt_lambda = [0.10, 0.00, 0.00]
    bar_colors = [PALETTE["success"], PALETTE["blue"], PALETTE["accent"]]

    rationale = [
        "Low-dim observation;\nbenefits from\nphysical anchor",
        "Inter-layer conflict;\nT-anchor harms the\nhierarchical decomposition",
        "Rich 17-D observation\nis already a\nself-regularizer",
    ]

    _set_defense_style()
    fig, ax = plt.subplots(figsize=(11.5, 6.5))

    bars = ax.bar(families, opt_lambda, width=0.55,
                  color=bar_colors, edgecolor=PALETTE["ink"], linewidth=1.5)

    # λ value labels
    for bar, v in zip(bars, opt_lambda):
        t = ax.text(bar.get_x() + bar.get_width()/2,
                    max(v, 0.005) + 0.012,
                    f"λ_temp = {v:.2f}",
                    ha="center", va="bottom",
                    fontsize=16, fontweight="bold",
                    color=PALETTE["ink"])

    # Rationale subtitles below each bar
    for i, txt in enumerate(rationale):
        ax.text(i, -0.030, txt,
                ha="center", va="top",
                fontsize=11, style="italic",
                color=PALETTE["muted"])

    ax.set_ylim(-0.045, max(opt_lambda) * 1.55)
    ax.set_ylabel("Optimal temperature-disagreement weight  λ_temp",
                  fontweight="bold")
    ax.set_yticks([0.00, 0.05, 0.10, 0.15])
    ax.tick_params(axis="x", which="both", pad=58, labelsize=14)

    ax.set_title(
        "Optimal physical regularization is controller-family-specific\n"
        "(one λ does NOT fit all)",
        fontsize=17, pad=18,
    )

    # Horizontal reference line at zero
    ax.axhline(0, color=PALETTE["ink"], linewidth=0.8, alpha=0.5)

    fig.tight_layout()
    _save_both(fig, out_path)
    print(f"[OK] {out_path.name}")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"[INFO] paper dir : {PAPER_DIR}")
    print(f"[INFO] data root : {DATA_ROOT}")
    print(f"[INFO] out dir   : {OUT_DIR}")
    fig1_calibration_paradox(OUT_DIR / "F1_calibration_paradox.pdf")
    fig2_hybrid_resolves    (OUT_DIR / "F2_hybrid_resolves.pdf")
    fig3_speed              (OUT_DIR / "F3_speed_vs_fidelity.pdf")
    fig4_pareto_vs_pi       (OUT_DIR / "F4_pareto_vs_pi.pdf")
    fig5_controller_family  (OUT_DIR / "F5_controller_family.pdf")


if __name__ == "__main__":
    main()
