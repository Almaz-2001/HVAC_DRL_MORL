"""
Generate the three main-text LaTeX tables of the Q1 paper from the canonical
Hou-and-Evins compliance CSVs and the prepared rollout / live-transfer
outputs. The script is safe to rerun: it always overwrites
`paper/tables/*.tex`, never touches the CSVs themselves, and falls back to a
placeholder LaTeX table with a TODO note when a required input is missing.

Tables produced:

- table1_architecture_comparison.tex
    Architecture-level comparison of v3 / v35_calibrated / hybrid_l010.
    Source: reports/hou_evins_architecture_justification_table.csv.

- table2_predictive_validity.tex
    1h / 4h / 8h / 24h prepared-rollout RMSE_T and MAE_T for raw_v35 and
    calibrated_v35.
    Source: reports/hou_evins_predictive_validity_table.csv (long form).

- table3_controller_performance.tex
    Live-BOPTEST closed-loop performance for PI / pure-v3 / hybrid_l010
    thermostatic / 17-D MORL across peak and typical heating windows.
    Source: outputs/block2_*/summary.csv (canonical single-seed numbers)
    with explicit TODO placeholders for the seed-CI columns until the
    3-seed validation runs are completed.

- table4_speed_benchmark.tex
    Environment-steps-per-second comparison: live BOPTEST RTE HTTP loop
    versus in-process v3 / v3.5 / hybrid surrogates on CPU at the same
    15-min control protocol.
    Source: reports/speed_benchmark_table.csv.

- table5_pareto_front.tex
    Yearly evaluation of the 5-point MORL Pareto sweep on bestest_air,
    with the BOPTEST built-in PI baseline included as the standard
    reference row. Marks the pre-registered canonical (0.50, 0.50) and
    the practical-deployment canonical (0.75, 0.25) per
    configs/morl_canonical_selection_log.yaml.
    Sources: reports/morl_pareto_front_table.csv,
             reports/pi_baseline_yearly_table.csv.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

PAPER_DIR = Path(__file__).resolve().parent
TABLES_DIR = PAPER_DIR / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

REPO_ROOT = PAPER_DIR.parent  # worktree root


def _data_root() -> Path:
    """Prefer the worktree root if it has the inputs; otherwise walk up to the
    main repository whose `reports/` and `outputs/` carry the canonical data."""
    candidates = [REPO_ROOT]
    parts = REPO_ROOT.parts
    if ".claude" in parts:
        idx = parts.index(".claude")
        candidates.append(Path(*parts[:idx]))
    for cand in candidates:
        reports = cand / "reports"
        outputs = cand / "outputs"
        if reports.exists() and outputs.exists():
            return cand
    return REPO_ROOT


DATA_ROOT = _data_root()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _find_csv(rel_path: str) -> Optional[Path]:
    """Look for a CSV first in the worktree, then in the parent repository."""
    for root in (REPO_ROOT, DATA_ROOT):
        path = root / rel_path
        if path.exists():
            return path
    return None


def _placeholder(path: Path, label: str, caption: str, missing: Iterable[str]) -> None:
    missing_str = "; ".join(missing)
    path.write_text(
        "% Auto-generated placeholder: required input(s) missing.\n"
        f"% Missing: {missing_str}\n"
        "\\begin{table}[t]\n"
        "  \\centering\n"
        f"  \\caption{{{caption}\\\\\n"
        f"  \\textcolor{{red}}{{[TODO: regenerate after producing {missing_str}]}}}}\n"
        f"  \\label{{{label}}}\n"
        "  \\begin{tabular}{l}\n"
        "    \\toprule\n"
        f"    Required CSV input not found: {missing_str} \\\\\n"
        "    \\bottomrule\n"
        "  \\end{tabular}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    print(f"[WARN] {path.name}: placeholder (missing {missing_str})")


def _fmt(value: object, fmt: str = "{:.3f}") -> str:
    if value is None:
        return "---"
    try:
        if pd.isna(value):
            return "---"
        return fmt.format(float(value))
    except (TypeError, ValueError):
        return str(value)


# ---------------------------------------------------------------------------
# Table 1 — Architecture comparison
# ---------------------------------------------------------------------------

def build_table1(out_path: Path) -> None:
    csv = _find_csv("reports/hou_evins_architecture_justification_table.csv")
    if csv is None:
        _placeholder(
            out_path,
            label="tab:architecture",
            caption=(
                "Architecture comparison of the three surrogate variants: "
                "control-oriented \\texttt{v3}, physically calibrated "
                "\\texttt{v3.5} and the hybrid backend \\texttt{hybrid\\_l010}."
            ),
            missing=["reports/hou_evins_architecture_justification_table.csv"],
        )
        return

    df = pd.read_csv(csv).set_index("variant")
    needed = ["v3", "v35_calibrated", "hybrid_l010"]
    for variant in needed:
        if variant not in df.index:
            _placeholder(
                out_path,
                label="tab:architecture",
                caption="Architecture comparison.",
                missing=[f"variant '{variant}' in {csv.name}"],
            )
            return

    def cell(variant: str, col: str, fmt: str = "{:.3f}") -> str:
        if col not in df.columns:
            return "---"
        return _fmt(df.loc[variant, col], fmt)

    body = []
    body.append("\\begin{table}[t]")
    body.append("  \\centering")
    body.append("  \\caption{Architecture comparison of the three surrogate variants. "
                "\\texttt{v3} is a data-driven feed-forward model on direct-TSup "
                "trajectories; \\texttt{v35\\_calibrated} is the physically informed "
                "RC-NeuralODE after Stage A/B/C calibration with explicit zone "
                "thermal capacitance $\\czon$; \\texttt{hybrid\\_l010} is the "
                "canonical hybrid backend ($\\lambda_{\\mathrm{temp}}=0.10$, "
                "$\\lambda_{\\mathrm{power}}=5\\times10^{-5}$). Block~1 fidelity "
                "columns are reproduced from "
                "\\texttt{reports/block1\\_surrogate\\_final\\_metrics.csv}; "
                "live-transfer and divergence columns from "
                "\\texttt{outputs/block13\\_*}.}")
    body.append("  \\label{tab:architecture}")
    body.append("  \\begin{tabular}{lccccccc}")
    body.append("    \\toprule")
    body.append("    & Explicit & Block~1 & Block~1 & Peak & Typical & Peak transfer & Typical transfer\\\\")
    body.append("    Variant & $\\czon$ & 1-step RMSE & 24h RMSE & $\\msmetric$ & $\\msmetric$ & RMSE\\,(\\si{\\celsius}) & RMSE\\,(\\si{\\celsius})\\\\")
    body.append("    \\midrule")
    name_map = {
        "v3":             "\\texttt{v3}",
        "v35_calibrated": "\\texttt{v3.5} calibrated",
        "hybrid_l010":    "\\texttt{hybrid\\_l010}",
    }
    for variant in needed:
        row = (
            f"    {name_map[variant]} & "
            f"{df.loc[variant].get('explicit_c_zon', '---')} & "
            f"{cell(variant, 'block1_temp_alignment_rmse_c')} & "
            f"{cell(variant, 'block1_rollout_24h_rmse_c')} & "
            f"{cell(variant, 'peak_control_m_s')} & "
            f"{cell(variant, 'typical_control_m_s')} & "
            f"{cell(variant, 'peak_transfer_temp_rmse_c')} & "
            f"{cell(variant, 'typical_transfer_temp_rmse_c')} \\\\"
        )
        body.append(row)
    body.append("    \\bottomrule")
    body.append("  \\end{tabular}")
    body.append("\\end{table}")

    out_path.write_text("\n".join(body) + "\n", encoding="utf-8")
    print(f"[OK] {out_path.name}: 3 rows")


# ---------------------------------------------------------------------------
# Table 2 — Predictive validity
# ---------------------------------------------------------------------------

def build_table2(out_path: Path) -> None:
    csv = _find_csv("reports/hou_evins_predictive_validity_table.csv")
    if csv is None:
        _placeholder(
            out_path,
            label="tab:predictive",
            caption=(
                "Predictive validity of the calibrated physical twin "
                "\\texttt{v3.5} versus its uncalibrated baseline across "
                "rollout horizons."
            ),
            missing=["reports/hou_evins_predictive_validity_table.csv"],
        )
        return

    df = pd.read_csv(csv)
    df = df[df["validity_type"] == "predictive_prepared_rollout"].copy()

    horizons = ["rollout_1h", "rollout_4h", "rollout_8h", "rollout_24h"]
    variants = ["raw_v35", "v35_calibrated"]
    metrics = ["RMSE_T_C", "MAE_T_C"]

    def lookup(variant: str, horizon: str, metric: str) -> str:
        sel = df[
            (df["variant"] == variant)
            & (df["horizon"] == horizon)
            & (df["metric"] == metric)
        ]
        if sel.empty:
            return "---"
        return _fmt(sel["value"].iloc[0], "{:.3f}")

    body = []
    body.append("\\begin{table}[t]")
    body.append("  \\centering")
    body.append("  \\caption{Predictive validity of the calibrated physical twin "
                "\\texttt{v3.5} versus the uncalibrated baseline \\texttt{raw\\_v35} "
                "across rollout horizons. Values are computed on the held-out "
                "prepared $15$-minute corpus (8~episodes). Calibration roughly "
                "halves the temperature RMSE at every horizon and the RMSE is "
                "nearly flat from 1\\,h to 24\\,h, indicating that the identified "
                "$\\czon$ produces a stable physical model rather than one that "
                "accumulates error with horizon. Source: "
                "\\texttt{reports/hou\\_evins\\_predictive\\_validity\\_table.csv}, "
                "originally from "
                "\\texttt{outputs/surrogate\\_v35\\_rollout\\_prepared\\_15min\\_*/horizon\\_metrics.csv}.}")
    body.append("  \\label{tab:predictive}")
    body.append("  \\begin{tabular}{ll" + "c" * len(horizons) + "}")
    body.append("    \\toprule")
    body.append("    Variant & Metric & " + " & ".join(h.replace("rollout_", "") for h in horizons) + " \\\\")
    body.append("    \\midrule")
    name_map = {"raw_v35": "\\texttt{raw\\_v35}", "v35_calibrated": "\\texttt{v35\\_calibrated}"}
    metric_label = {"RMSE_T_C": "RMSE\\,(\\si{\\celsius})", "MAE_T_C": "MAE\\,(\\si{\\celsius})"}
    for variant in variants:
        for j, metric in enumerate(metrics):
            prefix = name_map[variant] if j == 0 else ""
            row = f"    {prefix} & {metric_label[metric]}"
            for h in horizons:
                row += f" & {lookup(variant, h, metric)}"
            row += " \\\\"
            body.append(row)
        if variant != variants[-1]:
            body.append("    \\midrule")
    body.append("    \\bottomrule")
    body.append("  \\end{tabular}")
    body.append("\\end{table}")

    out_path.write_text("\n".join(body) + "\n", encoding="utf-8")
    print(f"[OK] {out_path.name}: {len(variants)} variants x {len(metrics)} metrics x {len(horizons)} horizons")


# ---------------------------------------------------------------------------
# Table 3 — Controller live BOPTEST performance
# ---------------------------------------------------------------------------

CONTROLLER_SOURCES = [
    # (display_name, summary_csv_relative_to_outputs, notes)
    # PI per-window remains TODO until a per-window PI run is added; the
    # yearly PI baseline is reported separately in Table 5.
    ("PI baseline (per-window)",     "_PI_PER_WINDOW_NOT_RUN_",                                         "yearly only; see Table 5"),
    ("Thermostatic pure v3",         "bestest_air_article7_style_15min/summary.csv",                    "filter controller==thermostatic"),
    ("Thermostatic hybrid\\_l010",   "block2_thermostatic_hybrid_v3_v35_l010/summary.csv",              "canonical hybrid"),
    ("MORL 17-D canonical",          "morl_hybrid_v3_v35_power_only/summary.csv",                       "canonical preference"),
]


def _read_first_row(csv_path: Path, scenario: str, controller_filter: Optional[str] = None) -> Optional[pd.Series]:
    if not csv_path.exists():
        return None
    df = pd.read_csv(csv_path)
    if controller_filter:
        col, _, value = controller_filter.partition("==")
        col = col.replace("filter ", "").strip()
        if col in df.columns:
            df = df[df[col] == value]
    if "scenario" in df.columns:
        df = df[df["scenario"] == scenario]
    if df.empty:
        return None
    return df.iloc[0]


def build_table3(out_path: Path) -> None:
    body = []
    body.append("\\begin{table}[t]")
    body.append("  \\centering")
    body.append("  \\caption{Live \\boptest{} closed-loop performance on the "
                "\\texttt{peak\\_heat\\_window} and \\texttt{typical\\_heat\\_window} "
                "scenarios. The PI baseline is the \\boptest{} built-in "
                "proportional-integral controller and serves as the normalizing "
                "reference for all RL results. Canonical configurations: "
                "$\\lambda_{\\mathrm{temp}}=0.10$ for thermostatic hybrid, "
                "$\\lambda_{\\mathrm{temp}}=0.00$ for MORL 17-D. "
                "\\textcolor{red}{[TODO: replace single-seed values with "
                "$\\mathrm{mean}\\pm\\mathrm{std}$ over $N=3$ seeds for the "
                "canonical rows once the 3-seed validation run completes.]}}")
    body.append("  \\label{tab:control}")
    body.append("  \\begin{tabular}{lccccc}")
    body.append("    \\toprule")
    body.append("    & \\multicolumn{2}{c}{\\texttt{peak\\_heat\\_window}} & \\multicolumn{2}{c}{\\texttt{typical\\_heat\\_window}} & \\\\")
    body.append("    \\cmidrule(lr){2-3}\\cmidrule(lr){4-5}")
    body.append("    Controller & $\\msmetric$ & Energy\\,(kWh) & $\\msmetric$ & Energy\\,(kWh) & Notes \\\\")
    body.append("    \\midrule")

    n_filled = 0
    n_missing = 0
    for name, rel, hint in CONTROLLER_SOURCES:
        controller_filter = hint if hint.startswith("filter ") else None
        csv = DATA_ROOT / "outputs" / rel
        peak = _read_first_row(csv, "peak_heat_window", controller_filter)
        typ  = _read_first_row(csv, "typical_heat_window", controller_filter)

        def cell(row, col):
            if row is None or col not in row or pd.isna(row[col]):
                return "---"
            return _fmt(row[col], "{:.3f}")

        note = "\\textcolor{red}{[TODO]}" if peak is None and typ is None else hint
        row_str = (
            f"    {name} & "
            f"{cell(peak, 'm_s')} & {cell(peak, 'energy_kwh')} & "
            f"{cell(typ,  'm_s')} & {cell(typ,  'energy_kwh')} & "
            f"\\footnotesize {note} \\\\"
        )
        body.append(row_str)
        if peak is None and typ is None:
            n_missing += 1
        else:
            n_filled += 1

    body.append("    \\bottomrule")
    body.append("  \\end{tabular}")
    body.append("\\end{table}")

    out_path.write_text("\n".join(body) + "\n", encoding="utf-8")
    print(f"[OK] {out_path.name}: {n_filled} filled, {n_missing} placeholder rows")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def build_table4(out_path: Path) -> None:
    csv = _find_csv("reports/speed_benchmark_table.csv")
    if csv is None:
        _placeholder(
            out_path,
            label="tab:speed",
            caption=(
                "Throughput comparison: environment steps per second on CPU "
                "for the live \\boptest{} RTE HTTP loop versus in-process "
                "surrogate backends."
            ),
            missing=["reports/speed_benchmark_table.csv"],
        )
        return

    df = pd.read_csv(csv).set_index("backend")
    order = [
        ("boptest_rte_http",        "\\boptest{} RTE (HTTP)"),
        ("v3_surrogate",            "\\texttt{v3} surrogate"),
        ("v35_calibrated_surrogate","\\texttt{v3.5} calibrated"),
        ("hybrid_v3_v35_surrogate", "\\texttt{hybrid\\_l010}"),
    ]
    missing = [k for k, _ in order if k not in df.index]
    if missing:
        _placeholder(
            out_path,
            label="tab:speed",
            caption="Throughput comparison.",
            missing=[f"backend '{m}' in {csv.name}" for m in missing],
        )
        return

    def cell(backend: str, col: str, fmt: str) -> str:
        return _fmt(df.loc[backend, col], fmt)

    body = []
    body.append("\\begin{table}[t]")
    body.append("  \\centering")
    body.append("  \\caption{Throughput comparison on CPU at the same \\SI{15}{\\minute} "
                "control protocol (100 episodes $\\times$ 96 steps = 9{,}600 transitions "
                "per backend). The live \\boptest{} RTE row uses the same HTTP API path "
                "that downstream RL training and live closed-loop validation actually use, "
                "so the speed-up factor in the last column reflects the practical, not the "
                "idealized, ratio. Surrogate timings exclude one-shot model loading. Source: "
                "\\texttt{reports/speed\\_benchmark\\_table.csv}.}")
    body.append("  \\label{tab:speed}")
    body.append("  \\begin{tabular}{lrrrr}")
    body.append("    \\toprule")
    body.append("    Backend & Steps/s & Median step (ms) & P95 step (ms) & Speed-up \\\\")
    body.append("    \\midrule")
    speedup_fmt = "{:.1f}$" + "\\times$"
    for backend, name in order:
        steps   = cell(backend, "env_steps_per_sec",     "{:,.1f}")
        median  = cell(backend, "median_raw_step_ms",    "{:.3f}")
        p95     = cell(backend, "p95_raw_step_ms",       "{:.3f}")
        speedup = cell(backend, "speedup_vs_boptest_rte", speedup_fmt)
        body.append(f"    {name} & {steps} & {median} & {p95} & {speedup} \\\\")
    body.append("    \\bottomrule")
    body.append("  \\end{tabular}")
    body.append("\\end{table}")

    out_path.write_text("\n".join(body) + "\n", encoding="utf-8")
    print(f"[OK] {out_path.name}: {len(order)} rows")


# ---------------------------------------------------------------------------
# Table 5 — MORL Pareto front (yearly) + PI baseline reference row
# ---------------------------------------------------------------------------

def build_table5(out_path: Path) -> None:
    pareto_csv = _find_csv("reports/morl_pareto_front_table.csv")
    pi_csv     = _find_csv("reports/pi_baseline_yearly_table.csv")
    missing = []
    if pareto_csv is None:
        missing.append("reports/morl_pareto_front_table.csv")
    if pi_csv is None:
        missing.append("reports/pi_baseline_yearly_table.csv")
    if missing:
        _placeholder(
            out_path,
            label="tab:pareto",
            caption="Yearly Pareto front for the 5-weight MORL sweep on \\boptest{} \\texttt{bestest\\_air}.",
            missing=missing,
        )
        return

    pareto = pd.read_csv(pareto_csv)
    pi     = pd.read_csv(pi_csv)
    pi_row = pi[pi["controller"] == "pi_builtin"].iloc[0] if not pi.empty else None

    # Group Pareto rows by preference vector and take seed-averaged values
    # (currently a single seed each, but the schema is forward-compatible)
    pareto_grouped = (
        pareto
        .groupby(["preference_w_comfort", "preference_w_energy", "canonical_designation"], as_index=False)
        .agg(
            n_seeds=("seed", "count"),
            m_s=("m_s", "mean"),
            violation_pct=("violation_pct", "mean"),
            energy_kwh=("energy_kwh", "mean"),
            rmse_yearly_c=("rmse_yearly_c", "mean"),
        )
        .sort_values("preference_w_comfort", ascending=False)
        .reset_index(drop=True)
    )

    designation_label = {
        "pareto_endpoint_comfort":          "comfort endpoint",
        "practical_deployment_canonical":   "\\textbf{practical canonical}",
        "pre_registered_canonical":         "\\textbf{pre-registered canonical}",
        "pareto_intermediate":              "intermediate",
        "pareto_endpoint_energy_collapse":  "energy collapse",
    }

    body = []
    body.append("\\begin{table}[t]")
    body.append("  \\centering")
    body.append("  \\caption{Yearly evaluation of the five-weight MORL Pareto sweep on "
                "\\boptest{} \\texttt{bestest\\_air} (single seed per preference vector at the "
                "time of writing; canonical rows will be re-rendered with $\\mathrm{mean}\\pm\\mathrm{std}$ "
                "once seeds 43 and 44 complete --- see "
                "\\texttt{configs/morl\\_canonical\\_selection\\_log.yaml}). The BOPTEST built-in PI "
                "controller is included as the standard reference row; it is the default tuning "
                "exposed by the testcase and is \\emph{not} a custom-tuned baseline (see "
                "Section~\\ref{ssec:res2_pi}). The (0.00, 1.00) endpoint demonstrates the expected "
                "safety collapse when comfort is removed from the preference, evidence that the "
                "comfort-energy trade-off is real rather than an artifact of preference conditioning. "
                "Sources: \\texttt{reports/morl\\_pareto\\_front\\_table.csv}, "
                "\\texttt{reports/pi\\_baseline\\_yearly\\_table.csv}.}")
    body.append("  \\label{tab:pareto}")
    body.append("  \\begin{tabular}{lcccccc}")
    body.append("    \\toprule")
    body.append("    Configuration & Designation & Yearly $\\msmetric$ & Violation\\,(\\%) & Energy\\,(kWh) & RMSE\\,(\\si{\\celsius}) & $N_{\\mathrm{seeds}}$ \\\\")
    body.append("    \\midrule")
    if pi_row is not None:
        body.append(
            "    \\boptest{} PI (built-in) & reference & "
            f"{_fmt(pi_row['m_s'], '{:.3f}')} & "
            f"{_fmt(pi_row['violation_pct'], '{:.2f}')} & "
            f"{_fmt(pi_row['energy_kwh'], '{:.2f}')} & "
            f"{_fmt(pi_row['rmse_yearly_c'], '{:.3f}')} & 1 \\\\"
        )
    body.append("    \\midrule")
    for _, r in pareto_grouped.iterrows():
        wc = r["preference_w_comfort"]
        we = r["preference_w_energy"]
        designation = designation_label.get(r["canonical_designation"], r["canonical_designation"])
        body.append(
            f"    MORL $w=({wc:.2f},\\,{we:.2f})$ & {designation} & "
            f"{_fmt(r['m_s'], '{:.4f}')} & "
            f"{_fmt(r['violation_pct'], '{:.2f}')} & "
            f"{_fmt(r['energy_kwh'], '{:.2f}')} & "
            f"{_fmt(r['rmse_yearly_c'], '{:.3f}')} & "
            f"{int(r['n_seeds'])} \\\\"
        )
    body.append("    \\bottomrule")
    body.append("  \\end{tabular}")
    body.append("\\end{table}")

    out_path.write_text("\n".join(body) + "\n", encoding="utf-8")
    print(f"[OK] {out_path.name}: PI baseline + {len(pareto_grouped)} Pareto points")


def main() -> None:
    print(f"[INFO] paper dir : {PAPER_DIR}")
    print(f"[INFO] data root : {DATA_ROOT}")
    build_table1(TABLES_DIR / "table1_architecture_comparison.tex")
    build_table2(TABLES_DIR / "table2_predictive_validity.tex")
    build_table3(TABLES_DIR / "table3_controller_performance.tex")
    build_table4(TABLES_DIR / "table4_speed_benchmark.tex")
    build_table5(TABLES_DIR / "table5_pareto_front.tex")


if __name__ == "__main__":
    main()
