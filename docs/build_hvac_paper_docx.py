"""Rebuild the HVAC paper DOCX skeleton with real figures and CSV tables.

This script uses direct OOXML editing so it does not depend on python-docx.
It reads the existing skeleton as a template and writes a separate revised file.
"""

from __future__ import annotations

import csv
from datetime import datetime
import html
import runpy
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_CANDIDATES = [
    ROOT / "docs" / "hvac_paper_skeleton.docx",
    ROOT / "draft" / "legacy_archive" / "docs_archive" / "hvac_paper_skeleton.docx",
]
OUTPUT = ROOT / "docs" / "hvac_paper_skeleton_q1_restructured_patched.docx"
OUTPUT_FALLBACK = ROOT / "docs" / "hvac_paper_skeleton_q1_restructured_updated.docx"
FIG_DIR = ROOT / "reports" / "figures" / "article_real"

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
}


def esc(text: object) -> str:
    if text is None:
        return ""
    text = "" if pd.isna(text) else str(text)
    return html.escape(text, quote=False)


def fmt(value: object, digits: int = 3) -> str:
    if value is None or pd.isna(value):
        return ""
    try:
        x = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(x) >= 100:
        return f"{x:,.1f}"
    return f"{x:.{digits}f}"


def p(text: str = "", style: str | None = None, bold: bool = False, italic: bool = False, size: int | None = None, color: str | None = None, align: str | None = None) -> str:
    ppr = ""
    if style:
        ppr += f'<w:pStyle w:val="{style}"/>'
    if align:
        ppr += f'<w:jc w:val="{align}"/>'
    ppr_xml = f"<w:pPr>{ppr}</w:pPr>" if ppr else ""
    rpr = ""
    if bold:
        rpr += "<w:b/>"
    if italic:
        rpr += "<w:i/>"
    if size:
        rpr += f'<w:sz w:val="{size}"/>'
    if color:
        rpr += f'<w:color w:val="{color}"/>'
    rpr_xml = f"<w:rPr>{rpr}</w:rPr>" if rpr else ""
    return f"<w:p>{ppr_xml}<w:r>{rpr_xml}<w:t>{esc(text)}</w:t></w:r></w:p>"


def page_break() -> str:
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def caption(text: str) -> str:
    return p(text, italic=True, size=18, color="555555")


def table_xml(rows: list[list[object]], widths: list[int] | None = None, font_size: int = 16) -> str:
    if not rows:
        return ""
    ncols = max(len(r) for r in rows)
    if widths is None:
        base = 9360 // ncols
        widths = [base] * ncols
        widths[-1] += 9360 - sum(widths)
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    out = [
        '<w:tbl><w:tblPr><w:tblW w:w="9360" w:type="dxa"/>'
        '<w:tblLayout w:type="fixed"/>'
        '<w:tblBorders>'
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="D9D9D9"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="D9D9D9"/>'
        '</w:tblBorders></w:tblPr>',
        f"<w:tblGrid>{grid}</w:tblGrid>",
    ]
    for ridx, row in enumerate(rows):
        out.append("<w:tr>")
        for cidx in range(ncols):
            text = row[cidx] if cidx < len(row) else ""
            shade = '<w:shd w:fill="EAF2F8"/>' if ridx == 0 else ""
            bold = "<w:b/>" if ridx == 0 else ""
            out.append(
                f'<w:tc><w:tcPr><w:tcW w:w="{widths[cidx]}" w:type="dxa"/>{shade}'
                '<w:tcMar><w:top w:w="80" w:type="dxa"/><w:left w:w="90" w:type="dxa"/>'
                '<w:bottom w:w="80" w:type="dxa"/><w:right w:w="90" w:type="dxa"/></w:tcMar>'
                '</w:tcPr>'
                f'<w:p><w:r><w:rPr>{bold}<w:sz w:val="{font_size}"/></w:rPr><w:t>{esc(text)}</w:t></w:r></w:p>'
                "</w:tc>"
            )
        out.append("</w:tr>")
    out.append("</w:tbl>")
    return "".join(out)


def image_xml(rid: str, name: str, width_in: float = 6.2, height_in: float = 3.6) -> str:
    cx = int(width_in * 914400)
    cy = int(height_in * 914400)
    return f"""
<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing>
<wp:inline distT="0" distB="0" distL="0" distR="0">
<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="1" name="{esc(name)}"/>
<a:graphic xmlns:a="{NS['a']}"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
<pic:pic xmlns:pic="{NS['pic']}"><pic:nvPicPr><pic:cNvPr id="0" name="{esc(name)}"/><pic:cNvPicPr/></pic:nvPicPr>
<pic:blipFill><a:blip r:embed="{rid}" xmlns:r="{NS['r']}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>
</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>
"""


def read(path: str) -> pd.DataFrame:
    return pd.read_csv(ROOT / path)


def small_table_from_df(df: pd.DataFrame, columns: list[str], max_rows: int = 12) -> list[list[str]]:
    shown = df[columns].head(max_rows).copy()
    rows = [columns]
    for _, row in shown.iterrows():
        rows.append([fmt(row[c]) if pd.api.types.is_numeric_dtype(shown[c]) else str(row[c]) for c in columns])
    return rows


def main_key_tables() -> dict[str, list[list[str]]]:
    arch = read("reports/hou_evins_architecture_justification_table.csv")
    t1 = [["Variant", "Role", "Physics", "C_zon", "Peak m_s", "Typical m_s", "Peak energy", "Typical energy", "Article position"]]
    for _, r in arch.iterrows():
        t1.append([
            r["variant"],
            r["role"],
            r["explicit_physics"],
            r["explicit_c_zon"],
            fmt(r["peak_control_m_s"]),
            fmt(r["typical_control_m_s"]),
            fmt(r["peak_energy_kwh"], 1),
            fmt(r["typical_energy_kwh"], 1),
            r["article_position"],
        ])

    pred = read("reports/hou_evins_predictive_validity_table.csv")
    t2 = [["Model", "Horizon", "RMSE_T", "MAE_T", "R2_T", "RMSE_P", "MAE_P"]]
    for _, r in pred.iterrows():
        t2.append([r["model"], r["horizon"], fmt(r["RMSE_T"]), fmt(r["MAE_T"]), fmt(r["R2_T"]), fmt(r["RMSE_P"], 1), fmt(r["MAE_P"], 1)])

    speed = read("reports/speed_benchmark_table.csv")
    t3 = [["Backend", "Steps/s", "Median step ms", "P95 step ms", "Speed-up"]]
    for _, r in speed.iterrows():
        t3.append([r["backend"], fmt(r["env_steps_per_sec"], 1), fmt(r["median_raw_step_ms"], 3), fmt(r["p95_raw_step_ms"], 3), f"{fmt(r['speedup_vs_boptest_rte'], 1)}x"])

    thermo_pure = read("outputs/bestest_air_article7_style_15min/summary.csv")
    thermo_pure = thermo_pure[thermo_pure["controller"] == "thermostatic"].assign(model="pure_v3")
    thermo_hyb = read("outputs/block2_thermostatic_hybrid_v3_v35_l010/summary.csv").assign(model="hybrid_l010")
    thermo = pd.concat([thermo_pure, thermo_hyb], ignore_index=True)
    t4 = [["Model", "Scenario", "m_s", "Violation %", "Energy kWh", "RMSE center C"]]
    for _, r in thermo.iterrows():
        t4.append([r["model"], r["scenario"], fmt(r["m_s"]), fmt(r["violation_pct"], 2), fmt(r["energy_kwh"], 1), fmt(r.get("rmse_center_c", r.get("rmse_22_c")), 3)])

    universal = read("outputs/universal_validation/bestest_air/thermostatic_bestest_air_article/thermostatic_universal_yearly_summary.csv")
    t4b = [["Scenario", "m_s", "Violation %", "Energy kWh", "RMSE C", "T min", "T max", "T mean"]]
    for _, r in universal.iterrows():
        t4b.append([
            r["name"],
            fmt(r["ms"]),
            fmt(r["viol_pct"], 2),
            fmt(r["energy_kwh"], 1),
            fmt(r["rmse"], 3),
            fmt(r["t_min"], 2),
            fmt(r["t_max"], 2),
            fmt(r["t_mean"], 2),
        ])

    hdrl = read("reports/block2_hdrl_lambda_sweep_summary.csv")
    t5 = [["Variant", "Scenario", "m_s", "Violation %", "Energy kWh", "RMSE center C"]]
    for _, r in hdrl.iterrows():
        t5.append([r["variant"], r["scenario"], fmt(r["m_s"]), fmt(r["violation_pct"], 2), fmt(r["energy_kwh"], 1), fmt(r["rmse_center_c"], 3)])

    morl = read("reports/morl_pareto_front_table.csv")
    t6 = [["Kind", "Label", "w comfort", "w energy", "m_s", "Violation %", "Energy kWh", "RMSE C"]]
    for _, r in morl.iterrows():
        t6.append([r["kind"], r["label"], fmt(r["w_comfort"], 2), fmt(r["w_energy"], 2), fmt(r["ms_mean"]), fmt(r["violation_pct_mean"], 2), fmt(r["energy_kwh_mean"], 1), fmt(r["rmse_mean"], 3)])

    transfer = read("reports/block3_transfer_matrix.csv")
    t7 = [["Testcase", "None", "Full", "m_s RL", "m_s PI", "Energy delta", "Full RMSE gain", "C_zon ratio", "Interpretation"]]
    for _, r in transfer.iterrows():
        t7.append([
            r["testcase"],
            r["none_controller_verdict"],
            r["full_controller_verdict"],
            fmt(r["m_s_rl"], 3),
            fmt(r["m_s_pi"], 3),
            f"{fmt(r['energy_delta_pct_vs_pi'], 1)}%",
            f"{fmt(r['rmse_improvement_pct'], 1)}%",
            f"{fmt(r['c_zon_ratio_vs_bestest_air'], 2)}x",
            r["primary_interpretation"],
        ])

    return {"arch": t1, "pred": t2, "speed": t3, "thermo": t4, "universal_bestest_air": t4b, "hdrl": t5, "morl": t6, "transfer": t7}


def paper_numbers() -> dict[str, str]:
    """Centralize article numbers so captions/text stay tied to CSV artifacts."""
    pred = read("reports/hou_evins_predictive_validity_table.csv")
    matched = read("reports/block1_corpus_matched_comparison.csv")
    arch = read("reports/hou_evins_architecture_justification_table.csv")
    transfer = read("reports/block3_transfer_matrix.csv")
    speed = read("reports/speed_benchmark_table.csv")

    def pred_rmse(model: str, horizon: str = "24h") -> float:
        return float(pred[(pred["model"].eq(model)) & (pred["horizon"].eq(horizon))]["RMSE_T"].iloc[0])

    def matched_rmse(variant: str) -> float:
        return float(matched[matched["variant"].eq(variant)]["rmse_24h_c"].iloc[0])

    def arch_value(variant: str, col: str) -> float:
        return float(arch[arch["variant"].eq(variant)][col].iloc[0])

    hp = transfer[transfer["testcase"].eq("bestest_hydronic_heat_pump")].iloc[0]
    hyd = transfer[transfer["testcase"].eq("bestest_hydronic")].iloc[0]
    com = transfer[transfer["testcase"].eq("singlezone_commercial_hydronic")].iloc[0]
    rmse_gain_min = float(transfer["rmse_improvement_pct"].min())
    rmse_gain_max = float(transfer["rmse_improvement_pct"].max())
    czon_min = float(transfer["c_zon_ratio_vs_bestest_air"].min())
    czon_max = float(transfer["c_zon_ratio_vs_bestest_air"].max())
    speed_hybrid = speed[speed["backend"].eq("hybrid_v3_plus_v35")]
    if speed_hybrid.empty:
        speed_hybrid = speed[speed["backend"].str.contains("hybrid", case=False, na=False)]
    speed_row = speed_hybrid.iloc[0]

    return {
        "v35_cal_24h": f"{pred_rmse('v3.5_calibrated'):.3f}",
        "v3_24h": f"{pred_rmse('v3'):.3f}",
        "v3_hourly_24h": f"{matched_rmse('v3_hourly'):.3f}",
        "v3_matched_24h": f"{matched_rmse('v3_15min_matched'):.3f}",
        "raw_v35_24h": f"{matched_rmse('v35_raw'):.3f}",
        "v35_arch_24h": f"{matched_rmse('v35_calibrated'):.3f}",
        "v35_peak_live": f"{arch_value('v35_calibrated', 'peak_transfer_temp_rmse_c'):.2f}",
        "v35_typical_live": f"{arch_value('v35_calibrated', 'typical_transfer_temp_rmse_c'):.2f}",
        "hybrid_peak_rmse": f"{arch_value('hybrid_l010', 'peak_transfer_temp_rmse_c'):.3f}",
        "hybrid_typical_rmse": f"{arch_value('hybrid_l010', 'typical_transfer_temp_rmse_c'):.3f}",
        "hybrid_peak_ms": f"{arch_value('hybrid_l010', 'peak_control_m_s'):.4f}",
        "hybrid_typical_ms": f"{arch_value('hybrid_l010', 'typical_control_m_s'):.4f}",
        "hybrid_steps": f"{float(speed_row['env_steps_per_sec']):,.1f}",
        "hybrid_speedup": f"{float(speed_row['speedup_vs_boptest_rte']):.1f}",
        "block3_gain_min": f"{rmse_gain_min:.1f}",
        "block3_gain_max": f"{rmse_gain_max:.1f}",
        "block3_czon_min": f"{czon_min:.2f}",
        "block3_czon_max": f"{czon_max:.2f}",
        "hp_ms_rl": f"{float(hp['m_s_rl']):.3f}",
        "hp_ms_pi": f"{float(hp['m_s_pi']):.3f}",
        "hp_threshold": f"{float(hp['pass_threshold_m_s']):.3f}",
        "hp_energy_delta_abs": f"{abs(float(hp['energy_delta_pct_vs_pi'])):.1f}",
        "hp_raw_rmse": f"{float(hp['raw_rmse_t_c']):.3f}",
        "hp_full_rmse": f"{float(hp['full_rmse_t_c']):.3f}",
        "hp_czon": f"{float(hp['c_zon_ratio_vs_bestest_air']):.2f}",
        "hyd_ms_rl": f"{float(hyd['m_s_rl']):.3f}",
        "hyd_threshold": f"{float(hyd['pass_threshold_m_s']):.3f}",
        "hyd_energy_delta_abs": f"{abs(float(hyd['energy_delta_pct_vs_pi'])):.1f}",
        "hyd_raw_rmse": f"{float(hyd['raw_rmse_t_c']):.3f}",
        "hyd_full_rmse": f"{float(hyd['full_rmse_t_c']):.3f}",
        "hyd_czon": f"{float(hyd['c_zon_ratio_vs_bestest_air']):.2f}",
        "com_ms_rl": f"{float(com['m_s_rl']):.3f}",
        "com_ms_pi": f"{float(com['m_s_pi']):.3f}",
        "com_threshold": f"{float(com['pass_threshold_m_s']):.3f}",
        "com_energy_delta": f"{float(com['energy_delta_pct_vs_pi']):.1f}",
        "com_raw_rmse": f"{float(com['raw_rmse_t_c']):.3f}",
        "com_full_rmse": f"{float(com['full_rmse_t_c']):.3f}",
        "com_czon": f"{float(com['c_zon_ratio_vs_bestest_air']):.2f}",
    }


def supplement_tables() -> list[tuple[str, str, list[list[str]]]]:
    specs = [
        ("S1", "Sample generation", "reports/hou_evins_sample_generation_table.csv", ["dataset_id", "rows", "step_sec", "controller_or_policy_mix", "intended_role", "article_status"]),
        ("S2", "Sample-size justification", "reports/hou_evins_sample_size_justification_table.csv", ["dataset_id", "rows", "primary_metric_name", "primary_metric_value", "decision", "justification"]),
        ("S3", "Split representativeness", "reports/hou_evins_split_representativeness_table.csv", ["pipeline", "split_mode", "train_rows", "val_rows", "representativeness_assessment", "assessment_note"]),
        ("S4", "Stage A processing", "reports/hou_evins_stage_a_processing_table.csv", ["stage_a_operation", "implementation", "parameter_or_rule", "purpose"]),
        ("S5", "Feature significance and encoding", "reports/hou_evins_feature_justification_table.csv", ["variant", "obs_ablation", "power_feature_mode", "t_zone_feature_mode", "peak_m_s", "typical_m_s", "decision"]),
        ("S6", "Scaling", "reports/hou_evins_scaling_table.csv", ["variable", "context", "scaling_method", "parameters", "justification"]),
        ("S7", "Input independence", "reports/hou_evins_input_independence_table.csv", ["feature_i", "feature_j", "pearson_r", "normalized_mutual_info", "interpretation"]),
        ("S8", "Training hyperparameters", "reports/hou_evins_training_hyperparams_table.csv", ["param", "value", "source_file", "justification"]),
        ("S9", "Architecture justification", "reports/hou_evins_architecture_justification_table.csv", ["variant", "role", "explicit_physics", "explicit_c_zon", "peak_control_m_s", "typical_control_m_s", "article_position"]),
        ("S10", "Targeted sensitivity", "reports/hou_evins_targeted_sensitivity_table.csv", ["sensitivity_axis", "tested_values", "selection_metric", "winner", "numerical_reason"]),
        ("S11", "Predictive validity", "reports/hou_evins_predictive_validity_table.csv", ["model", "horizon", "RMSE_T", "MAE_T", "RMSE_P", "MAE_P", "source_note"]),
    ]
    out = []
    for sid, title, path, columns in specs:
        df = read(path)
        rows = small_table_from_df(df, columns, max_rows=18)
        out.append((sid, f"{title} ({path})", rows))
    return out


def build_body_compact(image_rids: dict[str, str]) -> str:
    """Build the compact <=30-page main-paper version: 8 figures + 7 tables."""
    nums = paper_numbers()
    tables = main_key_tables()
    parts: list[str] = []

    def fig(filename: str, name: str, caption_text: str, width: float = 6.4, height: float = 3.2) -> None:
        parts.append(image_xml(image_rids[filename], name, width, height))
        parts.append(caption(caption_text))

    parts.append(p("Physics-informed surrogate roles for reinforcement-learning HVAC control", "Title"))
    parts.append(p("Compact Q1 main-paper draft: high-impact figures and consolidated tables", italic=True, color="555555"))

    parts.append(p("1. Introduction", "Heading1"))
    parts.append(p("Buildings remain a major energy-consuming sector, and HVAC operation is one of the few operational levers that can reduce energy demand without changing the building envelope. Reinforcement learning is attractive because it can optimize nonlinear comfort-energy trade-offs, but practical HVAC RL depends on the model used for training. A surrogate that predicts thermal trajectories well is not automatically a good reinforcement-learning environment: the policy is trained in the surrogate's induced state distribution, not only on held-out one-step forecasts."))
    parts.append(p("This paper tests that assumption directly in BOPTEST. We separate three roles: a compact control-oriented surrogate v3, a physically informed calibrated twin v3.5, and a hybrid backend that rolls out through v3 while using frozen v3.5 only as a soft disagreement regularizer. The study proceeds through three blocks: digital-twin fidelity, downstream control/MORL, and transferability to hydronic-family testcases. The main-paper visual set is intentionally compact; detailed per-episode, per-seed, and per-testcase diagnostics are retained in the supplementary material and block dossiers."))

    parts.append(p("2. Related Work and Research Gap", "Heading1"))
    parts.append(p("Prior work covers surrogate validation, predictive-information RL, safety-filtered DRL, hierarchical and multi-objective HVAC RL, transfer learning, and offline-RL distribution shift. The gap addressed here is the missing role separation between predictive surrogate quality and downstream RL training utility. Table 1 positions the paper against the studies used to motivate the design."))
    parts.append(table_xml([
        ["Reference", "Domain", "Method", "Training environment", "Model type", "Control objective", "Key limitation", "How this paper differs"],
        ["Hou & Evins [17]", "Building surrogate validation", "Protocol for surrogate reporting", "Offline datasets", "NN surrogate", "Predictive validity", "Does not test RL utility", "Extends protocol to live-control utility and transfer."],
        ["Gao et al. [18]", "HVAC DRL", "GRU predictive information", "Simulation", "Recurrent predictor", "Comfort-energy", "Predictive signal assumed useful", "Shows predictive fidelity can hurt if used as rollout backend."],
        ["Wang et al. [19]", "Safe DRL", "MPC filtering", "Simulation/control loop", "Safety filter", "Safe actions", "Hard safety layer", "Tests soft physical regularization without action projection."],
        ["Liao et al. [21]", "HDRL HVAC", "Hierarchical RL", "Simulation", "Controller hierarchy", "Comfort/energy/AQ", "No surrogate role audit", "Tests whether physical regularization transfers to HDRL."],
        ["Coraci et al. [23]", "Transfer/real building", "Online transfer", "Target adaptation", "Controller adaptation", "Deployment transfer", "Allows policy adaptation", "Separates surrogate transfer from frozen-controller transfer."],
        ["Offline RL survey [27]", "RL methodology", "Distribution shift", "Offline data", "Policy/data support", "OOD robustness", "Generic RL framing", "Shows surrogate-induced distribution shift in HVAC control."],
    ], [1050, 1050, 1150, 1250, 1150, 1100, 1300, 2310], 11))
    parts.append(caption("Table 1. Literature positioning and research gap. The contribution sits between surrogate modeling, HVAC DRL, safety/transfer learning, and distribution-shift methodology."))

    parts.append(p("3. Methodology", "Heading1"))
    fig("block1_q1_fig01_pipeline.png", "overall_pipeline", "Figure 1. Overall experimental pipeline. Block 1 calibrates and audits surrogate roles; Block 2 tests controller-family utility; Block 3 tests transferability under pre-registered target-testcase regimes.", 6.4, 2.9)
    parts.append(p("3.1 Surrogate roles", "Heading2"))
    parts.append(table_xml([
        ["Surrogate/backend", "Architecture", "Input dim", "Output", "Physical structure", "Parameters", "Training corpus", "Calibration", "Role in RL"],
        ["v3", "Compact dual-head MLP", "8", "dT, HVAC power", "No explicit physics", "8,482", "legacy hourly + matched 15-min check", "Supervised", "Primary rollout environment"],
        ["raw v3.5", "RC-NeuralODE + residual heads", "15-min prepared", "T_next, power", "C_zon backbone", "~50k", "10,744 rows", "None", "Architecture-only negative baseline"],
        ["calibrated v3.5", "RC-NeuralODE + residual heads", "15-min prepared", "T_next, power", "identified C_zon", "~50k", "10,744 rows", "Stage A/B/C", "Predictive twin and frozen teacher"],
        ["hybrid", "v3 rollout + frozen v3.5 teacher", "policy obs", "rollout + disagreement", "soft physical regularizer", "v3 + v3.5", "same source corpus", "lambda weights", "Canonical thermostatic PPO backend"],
    ], [1150, 1350, 650, 950, 1200, 800, 1300, 950, 2010], 11))
    parts.append(caption("Table 2. Surrogate architectures and calibration summary. Detailed v3 dual-head layers are provided in the supplementary material."))

    parts.append(p("3.2 Controller interface and training protocol", "Heading2"))
    parts.append(table_xml([
        ["Component", "Definition used in main experiments", "Why it matters"],
        ["Observation", "17D TSup-style state: physical variables, cyclic time, ambient forecast, previous action/history", "MORL 5D failed; 17D recovers usable preference-conditioned control."],
        ["Action", "Continuous normalized action mapped to supply-temperature command 18-35 C plus fan/intensity channel", "Keeps controller compatible with bestest_air source testcase."],
        ["Reward", "Comfort + energy + smoothness; MORL scalarizes comfort/energy/safety weights", "Separates thermostatic, HDRL, and MORL objectives."],
        ["Thermostatic PPO", "PPO, final-policy live BOPTEST evaluation, lambda_temp sweep", "Primary positive hybrid result."],
        ["HDRL", "Hierarchical PPO variant, lambda_temp sweep", "Tests controller-family specificity."],
        ["MORL", "Preference-conditioned pretrain/finetune; canonical N=5 seeds", "Tests Pareto trade-offs and seed variance."],
    ], [1550, 4550, 3260], 12))
    parts.append(caption("Table 4. Controller training configuration, observation/action interface, and reward definition. Full hyperparameters are in the supplementary reproducibility tables."))

    parts.append(p("4. Experimental Setup", "Heading1"))
    parts.append(p("All live-control experiments use BOPTEST RTE 1.0.0-dev through the HTTP API. Blocks 1 and 2 use bestest_air as the source testcase under 900 s control steps and 21-24 C comfort bounds. Block 3 uses bestest_hydronic_heat_pump, bestest_hydronic, and singlezone_commercial_hydronic through documented actuator adapters. The evaluation uses two horizons intentionally: 14-day peak/typical windows for source-case controller-family analysis, and yearly evaluation for transferability normalization against testcase-native PI baselines."))
    parts.append(p("Pre-registration and replay checks are part of the experimental setup. BOPTEST replay for a fixed checkpoint is bit-identical at the reported metric precision, so observed seed variance is attributed to RL training stochasticity rather than simulator nondeterminism."))

    parts.append(p("5. Results I: Digital Twin Fidelity", "Heading1"))
    fig("main_fig2_stage_abc_czon.png", "stage_abc_czon", "Figure 2. Stage A/B/C calibration and C_zon identification. The calibrated physical twin improves one-step, 24h, and power metrics while identifying C_zon through a smooth Stage-B trajectory.", 6.4, 2.75)
    fig("main_fig3_matched_corpus_decomposition.png", "matched_decomposition", "Figure 3. Matched-corpus decomposition. The v3-to-v3.5 predictive-fidelity gain is split into corpus-resolution and Stage A/B/C calibration contributions rather than attributed entirely to physics.", 6.4, 2.75)
    parts.append(table_xml([
        ["Metric / variant", "Raw or baseline", "Calibrated / matched", "Absolute change", "Relative / interpretation"],
        ["1-step RMSE_T", "0.384 C", "0.235 C", "-0.149 C", "-38.9% after Stage A/B/C"],
        ["24h rollout RMSE_T", "1.466 C raw v3.5", "0.644 C calibrated v3.5", "-0.822 C", "-56.1% within v3.5 family"],
        ["Power MAE", "810 W", "482 W", "-328 W", "-40.5% after power-head refinement"],
        ["C_zon", "4.200e5 J/K prior", "4.413e5 J/K", "+2.13e4 J/K", "+5.1%; physically plausible update"],
        ["v3 hourly", "1.557 C", "0.876 C v3 15-min", "-0.681 C", "74.6% of v3-to-v3.5 gap is corpus shift"],
        ["v3 15-min to v3.5 calibrated", "0.876 C", "0.644 C", "-0.232 C", "25.4% of gap is Stage A/B/C calibration"],
    ], [1700, 1800, 1800, 1400, 2660], 12))
    parts.append(caption("Table 3. Stage A/B/C and matched-corpus calibration metrics. This combines the reviewer-mitigation evidence from Tables 4-5 of the full results dossier."))
    parts.append(p(f"Block 1 establishes the first central result: calibrated v3.5 is the best predictive twin, reaching 24h RMSE_T={nums['v35_cal_24h']} C, but this alone does not imply control utility. The matched-corpus check prevents overclaiming: moving v3 to 15-min telemetry explains a large fraction of the original v3-vs-v3.5 gap, while Stage A/B/C still supplies the final measured improvement."))

    parts.append(p("6. Results II: Control Performance and MORL", "Heading1"))
    fig("main_fig4_fidelity_control.png", "fidelity_control", "Figure 4. Predictive fidelity does not imply RL training utility. Calibrated v3.5 wins predictive fidelity but fails as a standalone PPO backend; the hybrid role separation restores live BOPTEST performance.", 6.4, 2.75)
    fig("main_fig5_morl_pareto_variance.png", "morl_summary", "Figure 5. MORL Pareto structure and seed-variance diagnostics. Canonical N=5 points expose high seed variance; the N=3 seasonal-inversion mechanism was falsified by extension to N=5.", 6.7, 2.65)
    parts.append(table_xml([
        ["Family / policy", "Best backend or variant", "Primary result", "m_s / variance", "Verdict"],
        ["Thermostatic PPO", "hybrid_l010", f"Peak/typical RMSE {nums['hybrid_peak_rmse']} / {nums['hybrid_typical_rmse']} C", f"m_s {nums['hybrid_peak_ms']} / {nums['hybrid_typical_ms']}", "Hybrid regularization supported"],
        ["Direct v3.5 PPO", "standalone calibrated v3.5", f"Live RMSE {nums['v35_peak_live']} / {nums['v35_typical_live']} C", "m_s > 1.0", "Negative control; predictive twin fails as RL env"],
        ["HDRL", "lambda_temp=0", "Temperature regularizer hurts hierarchy", "best at lambda=0", "Controller-family specificity"],
        ["MORL 17D", "power-only hybrid", "Pareto sweep usable after 17D interface", "canonical N=5 high variance", "Promising but not deployment-stable"],
        ["MORL N=5 test", "neutral/practical canonicals", "Replay deterministic; action-saturation hypothesis falsified", "sigma/mean > threshold", "Report with limitations"],
    ], [1500, 1650, 3050, 1550, 1610], 12))
    parts.append(caption("Table 5. Block 2 main controller and MORL summary. Detailed HDRL lambda rows, MORL sweep rows, and per-seed values are in the supplementary material."))

    parts.append(p("7. Results III: Transferability", "Heading1"))
    fig("main_fig5_block3_transfer_verdict_heatmap.png", "block3_transfer_heatmap", "Figure 6. Block 3 transferability matrix. Controller transfer is adapter-mediated and frozen-controller scoped; partial/full surrogate recalibration does not fine-tune the controller.", 6.0, 2.35)
    fig("main_fig6_block3_czon_consistency.png", "block3_czon", "Figure 7. C_zon consistency across hydronic testcases. Full Stage A/B/C recalibration re-identifies hydronic-family thermal capacitance at approximately 1.9x bestest_air.", 5.8, 2.65)
    parts.append(table_xml(tables["transfer"], [1500, 550, 550, 650, 650, 850, 850, 850, 2960], 11))
    parts.append(caption("Table 6. Block 3 transfer matrix, combining testcase selection, adapter-mediated controller verdicts, full surrogate recalibration, and C_zon re-identification. Source: reports/block3_transfer_matrix.csv."))
    parts.append(p(f"Block 3 gives a component-level result. The surrogate component transfers: full Stage A/B/C recalibration improves target-testcase RMSE_T by {nums['block3_gain_min']}-{nums['block3_gain_max']}% and identifies C_zon consistently in the {nums['block3_czon_min']}-{nums['block3_czon_max']}x range relative to bestest_air. The controller component does not transfer in a deployment-ready way: residential hydronic cases fail by comfort, while the commercial hydronic case passes the scalar m_s threshold only with a {nums['com_energy_delta']}% energy penalty."))

    parts.append(p("8. Audit and Hypothesis Closure", "Heading1"))
    fig("main_fig8_audit_timeline.png", "audit_timeline", "Figure 8. Audit/pre-registration timeline. Predictions, adapter mappings, and Block 3 manifest entries were committed before corresponding BOPTEST runs; results were appended afterward.", 6.4, 2.0)
    parts.append(table_xml([
        ["Hypothesis", "Pre-registered claim", "Operational criterion", "Verdict", "Evidence"],
        ["H1 strong", "Frozen recipe transfers directly", "mode=none PASS on >=2/3 target cases without severe KPI penalty", "Falsified", "Residential hydronic cases fail; commercial passes m_s but +35.3% energy."],
        ["H2 medium", "Partial surrogate recalibration is sufficient", "Stage C only improves controller verdict", "Falsified structurally", "Controller is frozen, so live KPI cannot change from mode=none."],
        ["H3 weak surrogate side", "Full recalibration gives useful target twin", "RMSE_T improves under full Stage A/B/C", "Supported", "60.2-87.8% RMSE_T improvement across N=3 target cases."],
        ["H3 weak controller side", "Full surrogate recalibration rescues frozen controller", "Controller PASS after full", "Falsified/split", "Surrogate succeeds, controller remains regime-dependent."],
        ["MORL action-saturation", "N=3 seasonal inversion persists at N=5", "Feb sigma <0.005 and winter ratio >20x", "Falsified", "Feb sigma rose and inversion collapsed at N=5."],
    ], [1250, 2400, 2200, 1250, 2260], 11))
    parts.append(caption("Table 7. Hypothesis closure table. Falsified hypotheses are retained as results rather than rewritten post hoc."))

    parts.append(p("9. Discussion", "Heading1"))
    parts.append(p("The main implication is role separation. A physics-informed model can be valuable without being a safe rollout environment. In this project, v3.5 is valuable as a calibrated teacher and transferable physical prior, while v3 remains the smoother control-learning environment. The hybrid backend works because it assigns each model to the role it can support empirically."))
    parts.append(p("The second implication is methodological caution. MORL Pareto points and seasonal variance patterns are unstable at small seed counts; the N=5 extension falsified an initially plausible mechanism. Transferability also splits by component: inverse surrogate calibration transfers more reliably than frozen controllers. These negative or mixed findings strengthen the paper because they define the boundary of the proposed method rather than overclaiming universal deployment readiness."))
    parts.append(p("The main limitation is that controller fine-tuning on target-recalibrated hydronic surrogates is out of scope. Block 3 therefore identifies the bottleneck, not the full solution. A natural next study is target-specific PPO fine-tuning on the full Stage A/B/C recalibrated surrogate, evaluated against the same pre-registered threshold and a two-axis deployment criterion that prevents energy penalties from hiding behind composite m_s PASS labels."))

    parts.append(p("10. Conclusion", "Heading1"))
    parts.append(p("This paper shows that surrogate design for HVAC reinforcement learning must be evaluated by functional role, not by predictive score alone. Calibrated v3.5 improves predictive fidelity and transfers as a physical inverse-calibration pipeline, but fails as a standalone PPO rollout backend. The hybrid backend resolves this by combining v3 rollout dynamics with frozen-v3.5 soft regularization. The resulting method improves thermostatic PPO, reveals controller-family limits in HDRL and MORL, and identifies controller-adapter mismatch as the transferability boundary on hydronic testcases."))

    parts.append(p("References", "Heading1"))
    parts.append(p("[1]-[27] Full bibliography follows the numbered reference list maintained in the project related-works folder and the current DOCX bibliography section.", italic=True))
    return "".join(parts)


def build_body(image_rids: dict[str, str]) -> str:
    return build_body_compact(image_rids)
    tables = main_key_tables()
    nums = paper_numbers()
    parts: list[str] = []
    parts.append(p("When Predictive Surrogates Fail as RL Environments:", bold=True, size=40, align="center"))
    parts.append(p("A Calibrated Physical Twin as Soft Regularizer for HVAC Control", bold=True, size=34, align="center"))
    parts.append(p("Almaz Sapargali", italic=True, align="center"))
    parts.append(p("[TODO] Affiliation, address, country.", italic=True, color="C01020", align="center"))
    parts.append(p("Target journal: Results in Engineering (Elsevier, Q1)", italic=True, color="707070", align="center"))
    parts.append(p("Abstract", "Heading1"))
    parts.append(p(f"Reinforcement learning controllers for HVAC systems are typically trained on neural-network surrogates because high-fidelity simulators are too slow for the millions of environment steps consumed by modern policy-gradient methods. A natural assumption is that a more physically faithful surrogate produces a better training environment. We test that assumption on the BOPTEST bestest_air testcase and report a negative result: a calibrated physical twin with explicit zone thermal capacitance reaches a 24-hour rollout RMSE of {nums['v35_cal_24h']} C versus {nums['raw_v35_24h']} C uncalibrated, yet fails as a stand-alone RL training environment with live closed-loop RMSE above 4 C. We resolve the gap by using the calibrated twin as a frozen soft physical regularizer for a smoother control-oriented surrogate. The canonical hybrid backend sustains {nums['hybrid_steps']} environment steps/s on one CPU thread, an {nums['hybrid_speedup']}x speed-up over the live BOPTEST RTE HTTP loop under the same 15-min protocol, and restores live closed-loop RMSE to {nums['hybrid_peak_rmse']} C on the peak window and {nums['hybrid_typical_rmse']} C on the typical window. The optimal regularization strength is controller-family specific: lambda_temp=0.10 for thermostatic PPO, but lambda_temp=0.00 for HDRL and 17D MORL. A pre-registered transferability block further shows that the Stage A/B/C inverse surrogate-calibration pipeline transfers across three hydronic BOPTEST testcases with {nums['block3_gain_min']}-{nums['block3_gain_max']}% RMSE_T improvement and consistent C_zon re-identification in the {nums['block3_czon_min']}-{nums['block3_czon_max']}x range versus bestest_air, whereas frozen controller transfer is regime-dependent and not deployment-ready without target-specific fine-tuning. All numerical justifications are provided in Supplementary Tables S1-S11."))
    parts.append(p("Keywords: HVAC control; deep reinforcement learning; digital twin; physics-informed machine learning; BOPTEST; multi-objective reinforcement learning.", italic=True))

    parts.append(p("1. Introduction", "Heading1"))
    parts.append(p("Motivation", "Heading2"))
    parts.append(p("Buildings remain one of the largest energy-consuming and carbon-relevant sectors worldwide, which makes operational improvements in heating, ventilation, and air-conditioning systems a central lever for decarbonization and grid-responsive demand management [1]. Yet HVAC operation is still governed by a persistent modeling problem: controllers must negotiate comfort, energy use, weather variability, and equipment constraints in systems whose dynamics are nonlinear, partially observed, and strongly building-specific. In that setting, the model used for control is not a secondary implementation detail; it largely determines whether advanced control can be trained, benchmarked, and transferred in a credible way."))
    parts.append(p("For that reason, building-control research has long invested in control-oriented dynamic models and predictive optimization. Comparative studies of advanced control strategies show the continuing relevance of predictive control for building energy management [2], while grey-box identification remains attractive because it preserves physically interpretable structure without requiring the full modeling burden of a white-box simulator [3]. At the same time, the emergence of community testbeds has changed how such methods can be evaluated. The Building Optimization Testing Framework (BOPTEST) established a standardized, simulation-based environment for benchmarking building control strategies [4], and the subsequent OpenAI-Gym interface lowered the barrier for testing reinforcement-learning controllers under a common evaluation workflow [5]."))
    parts.append(p("Within these benchmarked settings, reinforcement learning has moved from proof-of-concept toward explicit comparison with established control paradigms. Recent work has directly compared reinforcement learning and model predictive control for building energy system optimization [6], and hybrid formulations such as reinforced model predictive control have attempted to combine predictive planning and learning in a single framework [7]. This direction is important because RL offers flexibility in nonlinear and multi-objective settings, but it also inherits acute sample-efficiency and generalization challenges, especially when the learning process depends not on the real building, but on a simulated or learned environment whose inductive biases may shape the policy as much as the reward function itself."))
    parts.append(p("Gap", "Heading2"))
    parts.append(p("The modeling literature has responded by moving beyond purely black-box prediction. Physics-constrained deep learning has shown that thermal models can be structured to preserve physically meaningful and operationally plausible dynamics [8]. In parallel, transfer-oriented work has demonstrated that thermal-dynamics representations can be adapted across buildings with limited target data [9], and that RL-based HVAC controllers can also be transferred across heterogeneous buildings and operating conditions [10]. These studies make physical priors and transfer mechanisms highly relevant to scalable building control, but they also raise a more subtle question that has not yet been resolved cleanly: what kind of surrogate is actually most useful inside the control-learning loop?"))
    parts.append(p("Recent work on digital-twin-enabled building control sharpens that question further. Simulated digital twins are increasingly proposed as reusable environments for building-application development [11], and surrogate-accelerated workflows in BOPTEST suggest that differentiable or data-driven approximations can drastically reduce computational cost while retaining useful predictive behavior over control horizons [12]. At the same time, recent reviews of field demonstrations show that reliable deployment evidence for MPC and RL remains limited and methodologically uneven [13], while newer model-based RL studies increasingly emphasize continual transfer [14] and counterfactual surrogate modeling [15] as routes to better data efficiency. Taken together, these lines of work suggest that benchmark quality, surrogate quality, and transfer quality are now central bottlenecks in the field. However, the literature still tends to assume, implicitly or explicitly, that a surrogate with better predictive fidelity will also be a better environment for learning a controller."))
    parts.append(p("Hypothesis and study design", "Heading2"))
    parts.append(p("This article addresses that unresolved assumption directly. Rather than treating surrogate quality as a single scalar property, the study evaluates building surrogates in two distinct roles: first, as predictive models of HVAC dynamics, and second, as training environments for reinforcement learning. The analysis is performed in a standardized BOPTEST workflow anchored on a single-zone source case and then extended to related hydronic-family target cases. Methodologically, the study contrasts a compact control-oriented black-box surrogate with a physically informed RC-NeuralODE surrogate, separates data-resolution effects from calibration effects through matched-corpus experiments, and tests whether physical structure contributes most when used as a direct rollout model, as a soft regularizer, or as a transferable calibration prior."))
    parts.append(p("The working hypothesis is therefore not that more physics is always better. The stricter hypothesis is role-dependent: predictive structure, training utility, and transferability may diverge, and a physically calibrated twin may be more useful as a constraint on learning than as the environment in which the policy is optimized. This hypothesis is evaluated through three linked blocks. Block 1 tests predictive fidelity and the fidelity-to-RL gap. Block 2 tests downstream control utility across thermostatic PPO, HDRL, and MORL controller families. Block 3 tests cross-testcase transfer under a pre-registered protocol that separates surrogate recalibration from frozen-controller deployment."))
    parts.append(p("Contribution and results summary", "Heading2"))
    parts.append(p("The resulting perspective leads to a contribution that is both negative and constructive. The negative result is that better long-horizon predictive fidelity does not necessarily imply better reinforcement-learning training utility: a surrogate that more accurately reproduces thermal trajectories can still induce inferior live control when used directly inside policy optimization. The constructive result is that these objectives can be partially reconciled when surrogate roles are separated: a fast control-oriented model can supply rollout dynamics, while a calibrated physical twin constrains learning through disagreement penalties, yielding a hybrid environment that is simultaneously tractable, physically informed, and empirically stronger in transfer."))
    parts.append(p(f"The study further shows that this logic is controller-family specific, that observation-interface design can dominate controller outcomes in multi-objective settings, and that inverse surrogate recalibration transfers across related target testcases more reliably than frozen controllers do. In the bestest_air source case, calibrated v3.5 achieves strong predictive validity but fails as a standalone RL rollout backend; the hybrid v3/v3.5 backend restores live control performance for thermostatic PPO. In the MORL branch, the N=5 seed extension falsifies an initially plausible seasonal action-saturation explanation and motivates cautious reporting of Pareto points with seed uncertainty. In the Block 3 transfer experiments, full Stage A/B/C recalibration improves temperature RMSE by {nums['block3_gain_min']}-{nums['block3_gain_max']}% across three hydronic testcases and consistently re-identifies C_zon in the {nums['block3_czon_min']}-{nums['block3_czon_max']}x range versus bestest_air, while frozen controller transfer remains regime-dependent and not deployment-ready."))
    parts.append(p("By framing surrogate design as a question of functional role rather than absolute predictive score, the paper aims to clarify how physics, data, and benchmarking should be combined in learning-based HVAC control. The central claim is therefore not that more physics is always better, nor that black-box surrogates are sufficient in isolation, but that predictive structure, training utility, and transferability must be evaluated separately and then recombined deliberately. This framing has direct implications for scalable digital twins, for the interpretation of benchmark results in building control, and for the practical path from simulation-based training to building-ready control policies."))
    parts.append(p("Contributions", "Heading2"))
    parts.append(p("1. A comfort-oriented v3 surrogate for direct supply-temperature control and RL rollout generation."))
    parts.append(p("2. A physically informed v3.5 grey-box surrogate with explicit C_zon identified through Stage A/B/C inverse calibration."))
    parts.append(p("3. A hybrid backend where v3 supplies the smooth RL dynamics and calibrated v3.5 acts as a frozen physical disagreement regularizer."))
    parts.append(p("4. Controller-family-specific evidence: lambda_temp=0.10 for thermostatic PPO, lambda_temp=0.00 for HDRL and 17D MORL."))
    parts.append(p("5. A pre-registered transferability analysis across three hydronic BOPTEST testcases, showing uniform surrogate-side transfer under full Stage A/B/C recalibration and regime-dependent frozen-controller transfer."))
    parts.append(p("6. A reproducible Hou-and-Evins-style numerical audit with S1-S11 supplementary tables and real-data figures."))

    parts.append(p("2. Related Work", "Heading1"))
    parts.append(p("2.1 Deep reinforcement learning for HVAC control", "Heading2"))
    parts.append(p("Deep reinforcement learning has become a major line of HVAC-control research because it can optimize energy and comfort without requiring a fully specified model predictive controller. The technical review by Al Sayed et al. [16] frames this literature as a response to the limits of fixed rule-based control, classical optimization, and manual supervisory tuning. Recent HVAC-RL work has moved beyond simple single-action PPO: Wang et al. [19] combine DRL with MPC-style safety filtering; Sun et al. [29] study winter residential air-conditioning control under predicted disturbances; Savino et al. [28] compare low-level DRL controllers against ASHRAE G36 sequences in multi-zone buildings; and Liao et al. [21] use hierarchical DRL to handle hybrid discrete-continuous HVAC action spaces and multi-objective rewards. These studies establish that learning-based control can be competitive, but they also show that safety, action representation, and evaluation protocol strongly affect the final result."))
    parts.append(p("Our work follows this line but asks a narrower and more falsifiable question: when does a high-fidelity surrogate improve downstream RL control? The Block 2 results show that the answer is controller-family specific. Thermostatic PPO benefits from a calibrated physical disagreement penalty at lambda_temp=0.10, while HDRL and 17D MORL reject the same temperature channel and perform best with lambda_temp=0. This prevents a generic claim that physics regularization is always useful. Instead, the contribution is an empirical role assignment: calibrated physics is valuable as a soft teacher for some controllers, not as a universal rollout backend."))
    parts.append(p("2.2 Surrogate and digital twin models for building energy", "Heading2"))
    parts.append(p("Surrogate models and digital twins are widely used because live building simulators and high-fidelity Modelica emulators are too slow for RL-scale policy optimization. Hou and Evins [17] argue that neural-network building surrogates require a disciplined development and evaluation protocol: sample generation, preprocessing, split representativeness, feature justification, scaling, architecture selection, sensitivity analysis, and multi-horizon predictive validation should all be reported explicitly. We adopt this protocol as the reporting backbone for Block 1 and extend it with a downstream-control test: a surrogate is not considered successful merely because it predicts well; it must also be tested as part of the RL training and live BOPTEST deployment loop."))
    parts.append(p(f"Predictive information can improve HVAC RL when it is injected in the right form. Gao et al. [18] show that GRU-based predictive information can improve DRL control in an office-building case study. Our result is complementary but more cautionary. The calibrated v3.5 physical twin is clearly the best forecasting model in Block 1, reaching 24h RMSE_T={nums['v35_cal_24h']} C after Stage A/B/C calibration. However, PPO trained directly on this model fails in live closed-loop BOPTEST with comfort RMSE above 4 C. This separates predictive validity from RL training utility. It also links to the offline-RL distribution-shift concern discussed by Samani et al. [27]: a model that is accurate on held-out trajectories may still induce a poor policy-learning landscape when the agent leaves the data-supported region."))
    parts.append(p("2.3 Physics-informed and safety-aware learning", "Heading2"))
    parts.append(p("Physics-informed HVAC learning can be implemented in several ways. One direction imposes physical or safety structure directly on the controller, for example through thermodynamically constrained actor-critic objectives or MPC-based safety filters. Hedayat et al. [20] represent this hard-constraint direction for HVAC optimization, while Wang et al. [19] use a DRL-MPC architecture to keep learning-based actions inside a safe operational envelope. These approaches are designed to prevent unsafe actions at deployment time."))
    parts.append(p("The present work uses a different mechanism. The calibrated v3.5 twin is not a hard safety filter, does not project actions, and does not replace the live BOPTEST evaluation layer. It remains frozen during RL training and contributes only a soft disagreement term against the control-oriented v3 surrogate: L_total = L_PPO + lambda_temp ||T_v3 - T_v3.5||^2 + lambda_power ||P_v3 - P_v3.5||^2. This design is intentionally weaker than hard safety filtering, but it isolates the scientific question of whether physical fidelity helps as a training regularizer. The negative controls show why that distinction matters: direct v3.5 rollout and v3.5 warm-start both fail, whereas the soft-regularized hybrid succeeds for thermostatic PPO."))
    parts.append(p("2.4 Multi-objective RL and Pareto analysis", "Heading2"))
    parts.append(p("HVAC control is inherently multi-objective: reducing energy use can conflict with thermal comfort, equipment smoothness, and safety. The multi-objective sequential decision-making survey by Roijers et al. [22] provides the general framework for scalarization and Pareto-front analysis. Recent HVAC-RL studies, including Liao et al. [21], operationalize this idea through weighted comfort, air-quality, and energy rewards. Our MORL block follows this scalarization perspective but treats the Pareto result as an empirical object requiring seed analysis rather than as a single-trajectory demonstration."))
    parts.append(p("The resulting finding is intentionally conservative. The 17D MORL sweep identifies plausible comfort-energy trade-offs, but the canonical preference points remain seed-sensitive at N=5. The pre-registered action-saturation hypothesis, initially motivated by an N=3 seasonal pattern, was falsified when seeds 45 and 46 were added. This is not reported as a failure to hide; it is part of the methodological contribution. In this domain, small-seed seasonal patterns can be transient, and aggregate Pareto points must be reported with uncertainty."))
    parts.append(p("2.5 Transfer learning and cross-testcase generalization", "Heading2"))
    parts.append(p("A second branch of the literature asks how controllers trained in one building can be transferred to another. Coraci et al. [23] study online transfer learning in a real office building and use imitation/fine-tuning to reduce deployment burden. Hou et al. [24] propose multi-source transfer learning for DRL HVAC deployment, where source environments are selected to improve target training efficiency. Kadamala et al. [25] also evaluate DRL transfer learning between HVAC scenarios, and Coraci et al. [26] study heterogeneous transfer across diverse energy systems. These works typically allow some form of target adaptation of the policy."))
    parts.append(p(f"Block 3 deliberately fixes a stricter question before running the hydronic transfer experiments. It asks which components of the bestest_air recipe transfer without post-hoc controller fine-tuning. The answer is component-level. Full Stage A/B/C surrogate recalibration transfers across three hydronic BOPTEST testcases, improving RMSE_T by {nums['block3_gain_min']}-{nums['block3_gain_max']}% and re-identifying C_zon consistently in the {nums['block3_czon_min']}-{nums['block3_czon_max']}x range versus bestest_air. The frozen controller, however, is not deployment-ready: residential hydronic testcases fail by comfort, while the commercial hydronic testcase passes the pre-registered scalar threshold only with a {nums['com_energy_delta']}% energy penalty. This positions controller fine-tuning on the target-recalibrated surrogate as future work rather than as an unreported post-hoc rescue."))
    parts.append(p("2.6 BOPTEST benchmarking", "Heading2"))
    parts.append(p("BOPTEST provides the live evaluation layer for this paper. Blum et al. [4] introduced BOPTEST as a simulation-based benchmarking framework with containerized building emulators, a common HTTP API, overwriteable control points, baseline controllers, and standardized KPI reporting. BOPTEST exposes realistic Modelica building models through a standard interface so that control algorithms can be benchmarked without physical installation. We use BOPTEST RTE version 1.0.0-dev as the authoritative closed-loop evaluator, not merely as a data generator."))
    parts.append(p("This choice is important for the paper's logic. All surrogate models are intermediate artifacts; live BOPTEST remains the final arbiter of controller performance. The Block 1 fidelity-to-control gap, the Block 2 hybrid-backend selection, and the Block 3 hydronic transfer results all depend on this separation. A model can win on predictive RMSE and lose in closed-loop control; only the BOPTEST deployment layer exposes that failure."))

    parts.append(p("3. Methodology", "Heading1"))
    parts.append(p("3.1 Problem formulation", "Heading2"))
    parts.append(p("The HVAC control problem is treated as a finite-horizon Markov decision process with state s_t, continuous action a_t, stochastic exogenous weather w_t, transition model f, and reward r_t. At each 900 s control step, the controller observes a compact building state, chooses an HVAC command, receives the next zone temperature and power response, and accumulates an objective that penalizes comfort violation, unnecessary energy use, and abrupt control changes. The live system transition is the BOPTEST RTE emulator. The learning-time transition is either the control-oriented surrogate v3, the physically informed surrogate v3.5, or the hybrid backend that combines the two in different roles."))
    parts.append(p("The action for the bestest_air source testcase is a normalized two-dimensional vector a_t in [-1,1]^2. The first component maps to a supply-temperature command T_supply in [18,35] C, and the second component controls the fan/intensity channel used by the surrogate and PPO policy. The canonical thermostatic observation contains 17 features: five physical variables, four cyclic time encodings, five weather forecast terms at 1/3/6/12/24 h horizons, and three history terms consisting of the previous action and the previous temperature change. Ablation variants remove or transform parts of this observation, but the article-facing controller uses the validated no_delta_t / clipped_log / raw-style encoding reported in the experiment artifacts."))
    parts.append(p("The reward used for thermostatic PPO is comfort-first. Inside the 21-24 C comfort band, the agent receives a target-tracking bonus around the band center and a small energy penalty. Outside the band, comfort violation dominates; winter underheating receives a stronger penalty than mild overshoot because underheating is the observed high-risk failure mode in the source testcase. A smoothness term penalizes squared action changes. When the hybrid backend is active, an additional disagreement penalty is added against the frozen calibrated v3.5 teacher. In compact form:"))
    parts.append(p("r_t = r_track(T_zone) + r_smooth(a_t-a_{t-1}) + r_power(P_t) - lambda_temp ||T_v3 - T_v3.5||^2 - lambda_power ||P_v3 - P_v3.5||^2", italic=True))
    parts.append(p("For MORL, the scalar reward is replaced by a preference-conditioned scalarization of comfort and energy components, with weights w = (w_comfort, w_energy, w_safety). The canonical preference points are w=(0.50,0.50,0.00) and w=(0.75,0.25,0.00), each later extended to N=5 seeds under the pre-registered stopping rule."))

    parts.append(p("3.2 Surrogate roles and model variants", "Heading2"))
    parts.append(p("The study compares three surrogate roles rather than three interchangeable models. The v3 surrogate is a compact black-box model designed for stable rollout gradients; calibrated v3.5 is a physically informed RC-NeuralODE-like model designed for predictive validity and parameter interpretation; the hybrid backend uses v3 as the policy rollout environment and v3.5 as a frozen physical teacher. This role separation is the central methodological decision because a model can be useful as a predictor while being harmful as an RL environment."))
    parts.append(table_xml([
        ["Model/backend", "Primary role", "Physical structure", "Training use", "Article question tested"],
        ["v3", "Control-oriented rollout model", "Black-box two-head neural dynamics", "Direct PPO/HDRL/MORL environment", "Can a smooth surrogate support live-control transfer?"],
        ["v3.5", "Predictive physical twin", "Explicit C_zon plus residual heads", "Standalone negative control; frozen teacher in hybrid", "Does better predictive fidelity imply better RL utility?"],
        ["hybrid_l010", "Role-separated backend", "v3 rollout + frozen v3.5 disagreement", "Thermostatic PPO environment with lambda_temp=0.10", "Can physical fidelity help as soft regularization instead of rollout replacement?"],
    ], [1450, 1900, 1900, 2050, 2060], 13))
    parts.append(caption("Table M1. Methodological role separation between v3, v3.5, and the hybrid backend. The models are not evaluated only by predictive RMSE; each is tested in the role it is supposed to play inside the controller pipeline."))

    parts.append(p("3.3 Control-oriented surrogate v3", "Heading2"))
    parts.append(p("The v3 surrogate maps the encoded state and continuous action to one-step predictions of zone-temperature change and HVAC power. Its architecture is intentionally small: a shared multilayer perceptron feeds a temperature head and a power head. The active article path now supports the same 900 s / 15-min step used by v3.5 and BOPTEST yearly validation, so corpus-matched v3 checks can separate timestep effects from physics-calibration effects. v3 is not presented as a physically interpretable digital twin; its purpose is to give PPO a smooth, fast, differentiable-enough environment whose local dynamics do not destabilize policy optimization."))
    parts.append(p("The v3 training objective combines temperature and power prediction losses on BOPTEST-generated direct-TSup traces. It is evaluated by multi-horizon rollout RMSE and, more importantly, by downstream live BOPTEST transfer after a policy has been trained on it. This is why v3 remains relevant even when v3.5 is more accurate as a forecasting model: RL training utility is an empirical closed-loop property, not a direct consequence of one-step prediction loss."))

    parts.append(p("3.4 Physically informed surrogate v3.5 and Stage A/B/C calibration", "Heading2"))
    parts.append(p("The v3.5 surrogate introduces an explicit zone thermal capacitance C_zon and neural residual heads. Its calibration follows a three-stage inverse protocol adapted from the Hou-and-Evins reporting framework [17]. Stage A prepares causal 15-min telemetry by correcting alignment, bias, power scaling, and feature consistency. Stage B identifies C_zon on excitation-rich rows while residual corrections are constrained. Stage C freezes the identified capacitance and fits residual temperature/power heads to capture dynamics not represented by the scalar RC backbone."))
    parts.append(table_xml([
        ["Stage", "Input", "Optimized quantity", "Frozen quantity", "Reason"],
        ["A", "Raw BOPTEST telemetry", "No learning; preprocessing only", "n/a", "Prevent latency, bias, or scaling artifacts from being identified as physics."],
        ["B", "Prepared excitation windows", "C_zon", "Residual heads largely constrained", "Recover a physically interpretable thermal capacitance."],
        ["C", "Prepared all-row corpus", "Residual temperature and power heads", "C_zon", "Improve predictive fidelity without moving the identified physical parameter."],
    ], [700, 2100, 2100, 1800, 2660], 13))
    parts.append(caption("Table M2. Stage A/B/C inverse-calibration protocol for v3.5. The article reports C_zon as a physical parameter only because Stage B and Stage C are separated."))
    parts.append(p("This separation is also used in Block 3. On hydronic transfer cases, partial recalibration means Stage C only with C_zon frozen from bestest_air, while full recalibration means Stage A/B/C on the target testcase. The difference between these regimes allows the paper to distinguish residual-head adaptation from actual re-identification of building thermal mass."))

    parts.append(p("3.5 Hybrid backend and loss coupling", "Heading2"))
    parts.append(p("The hybrid backend is not an ensemble simulator. The policy state transition is still produced by v3. At each training step, the same state-action pair is also evaluated by the calibrated v3.5 teacher, and the difference between the two predicted temperature/power responses is converted into an auxiliary penalty. Therefore v3.5 influences the policy through the loss surface but never becomes the rollout dynamics. This prevents the policy from inheriting the unstable training landscape observed when PPO is trained directly on v3.5."))
    parts.append(p("L_total = L_PPO + lambda_temp ||T_v3 - T_v3.5||^2 + lambda_power ||P_v3 - P_v3.5||^2", italic=True))
    parts.append(p("The values of lambda_temp and lambda_power are not assumed universal. Block 2 sweeps lambda_temp for thermostatic PPO and HDRL, then carries only the empirically supported channels into MORL. The final interpretation is role- and controller-specific: calibrated physics helps thermostatic PPO at lambda_temp=0.10, but HDRL and MORL use the power-only variant because temperature disagreement degrades their closed-loop behavior."))
    parts.append(image_xml(image_rids["main_fig1_pipeline_schematic.png"], "main_fig1_pipeline_schematic", 6.7, 3.05))
    parts.append(caption("Figure 1. Hybrid backend schematic. The PPO policy rolls out through the smooth v3 surrogate while the calibrated v3.5 physical twin remains frozen and contributes only the disagreement regularizer."))

    parts.append(p("3.6 Controller families", "Heading2"))
    parts.append(p("Four controller families are used. The BOPTEST built-in PI controller is the reference baseline because it is testcase-native and reproducible. Thermostatic PPO is the main source-case controller and acts directly on the continuous T_supply/fan-style action interface. HDRL tests whether the same regularization logic survives a hierarchical action representation. MORL tests preference-conditioned comfort-energy trade-offs using scalarized reward weights and a 17D observation interface. The point is not to claim a single universal controller, but to test whether the surrogate conclusion remains stable across controller classes."))
    parts.append(table_xml([
        ["Controller", "Role in paper", "Training backend", "Key methodological check"],
        ["PI", "Reference baseline", "Built into BOPTEST", "Defines testcase-native yearly normalization and live comparison."],
        ["Thermostatic PPO", "Main positive hybrid result", "v3, v3.5, or hybrid", "Tests whether calibrated physics helps as soft regularization."],
        ["HDRL", "Negative-result controller-family check", "Hybrid lambda sweep", "Tests whether lambda_temp=0.10 transfers beyond thermostatic PPO."],
        ["17D MORL", "Preference/Pareto analysis", "Power-only hybrid variant", "Tests seed stability and comfort-energy scalarization under N=5 canonical seeds."],
    ], [1300, 2200, 1900, 3960], 13))
    parts.append(caption("Table M3. Controller families and their methodological role. Each controller answers a different falsifiable question rather than merely adding another benchmark row."))

    parts.append(p("3.7 Transferability methodology", "Heading2"))
    parts.append(p("Block 3 is pre-registered before running target-testcase BOPTEST evaluations. The transfer question is component-level: does the surrogate calibration pipeline transfer, and does the frozen controller transfer? Three regimes are defined. In mode=none, the frozen bestest_air recipe is deployed on the target testcase through a documented actuator adapter. In mode=partial, Stage C residual heads are recalibrated on target telemetry while C_zon and the controller remain frozen. In mode=full, Stage A/B/C is rerun on target telemetry, but the controller remains frozen. Because controller fine-tuning is explicitly excluded, any improvement in surrogate fidelity is not allowed to rescue the live controller verdict post hoc."))

    parts.append(p("4. Experimental Setup", "Heading1"))
    parts.append(p("4.1 Testbeds and serving layer", "Heading2"))
    parts.append(p("All live-control experiments are executed through BOPTEST RTE version 1.0.0-dev using the HTTP API. This is intentional: the same serving layer is used for telemetry collection, live validation, replay determinism tests, and the speed benchmark. Blocks 1 and 2 use bestest_air as the source testcase because it provides the direct supply-temperature control convention used by the v3/v3.5 surrogate family. Block 3 evaluates transfer to three related hydronic-family targets: bestest_hydronic_heat_pump, bestest_hydronic, and singlezone_commercial_hydronic."))
    parts.append(table_xml([
        ["Testcase", "Role", "Actuator interface", "Reason for inclusion"],
        ["bestest_air", "Source testcase for Blocks 1-2", "Direct supply-temperature style control", "Canonical training/evaluation case for v3, v3.5, hybrid PPO, HDRL, and MORL."],
        ["bestest_hydronic_heat_pump", "Primary Block 3 target", "Hydronic heat-pump setpoints and overrides", "Closest hydronic target; tests adapter-mediated transfer under nonlinear heat-pump physics."],
        ["bestest_hydronic", "Secondary Block 3 target", "Hydronic heating override/setpoint interface", "Tests whether the hydronic result replicates without heat-pump nonlinearity."],
        ["singlezone_commercial_hydronic", "Stretch Block 3 target", "Commercial hydronic interface", "Tests scale and regime sensitivity of controller transfer and C_zon re-identification."],
    ], [1700, 1550, 2200, 3910], 12))
    parts.append(caption("Table E1. Testcase roles. Hydronic transfer is adapter-mediated, not literal direct-TSup transfer, because the target actuators differ from bestest_air."))

    parts.append(p("4.2 Data generation and preprocessing", "Heading2"))
    parts.append(p("The source-case surrogate corpus is generated from BOPTEST trajectories under direct supply-temperature excitation and policy-like rollouts. The v3/v3.5 comparison uses a prepared 15-min corpus for calibrated v3.5 and a corpus-matched v3 retraining check to separate timestep/corpus effects from physical calibration effects. The article reports data generation, sample-size justification, split representativeness, Stage A preprocessing, scaling, input independence, and training hyperparameters in Supplementary Tables S1-S8."))
    parts.append(p("For Block 3, target telemetry is collected with the hydronic adapter policy used in live transfer. This keeps the target calibration corpus aligned with the actuator mapping actually used by the frozen controller. Adapter smoke tests are run before yearly control evaluation to verify that high-supply commands produce higher heat power and no lower final zone temperature than low-supply commands."))

    parts.append(p("4.3 Training and calibration workflow", "Heading2"))
    parts.append(p("The workflow has three layers. First, Block 1 trains and validates v3 and v3.5, including the two-pass canonical v3.5 calibration in which Stage B identifies C_zon and Stage C refines residual heads. Second, Block 2 trains controller families on the selected surrogate backend and evaluates them live on BOPTEST bestest_air. Third, Block 3 freezes the bestest_air controller, applies documented target adapters, and tests none/partial/full surrogate recalibration regimes on hydronic targets. This sequencing prevents leakage: Block 3 target results are not used to retune Block 2 controllers."))
    parts.append(p("Training is CPU-oriented. PPO runs use Stable-Baselines3-style policies and project-specific wrappers, while surrogate training uses PyTorch. Where canonical seed analysis is required, seeds are propagated through Python random, NumPy, PyTorch, PYTHONHASHSEED, and action/observation spaces. MORL canonical points are extended to N=5 only under the pre-registered stopping rule; there is no N=7 cascade after the bounded extension."))

    parts.append(p("4.4 Runtime characteristics", "Heading2"))
    parts.append(table_xml(tables["speed"], [2500, 1700, 1700, 1700, 1760], 16))
    parts.append(caption("Table 1. CPU throughput benchmark under the same 15-min control protocol. Source: reports/speed_benchmark_table.csv."))
    parts.append(p("Runtime is reported because it is part of the method, not just an implementation detail. BOPTEST RTE is the authoritative live evaluator, but it is too slow to serve as the main PPO training loop. Therefore the paper distinguishes live-evaluation fidelity from training-time throughput. The hybrid backend is slower than v3 because it evaluates both v3 and frozen v3.5, but it still preserves an 85.0x speed-up over the live BOPTEST RTE HTTP loop under the same 15-min stepping protocol."))

    parts.append(p("4.5 Evaluation protocol and metrics", "Heading2"))
    parts.append(p("All control evaluations use a 900 s control step and the same comfort band [21,24] C. The primary raw quantities are zone-temperature trajectory, violation percentage, energy consumption in kWh, RMSE to the comfort-band center, and the scalar safety metric m_s. The paper never reports m_s alone: energy and comfort are always shown beside it because a scalar threshold can hide multi-objective trade-offs. This is especially important in Block 3, where the commercial hydronic testcase passes the pre-registered m_s threshold but uses substantially more energy than PI."))
    parts.append(p("Comfort violation at a step is computed as v_t = max(0, 21 - T_zone,t, T_zone,t - 24). Violation percentage is the fraction of control steps with v_t > 0. Temperature RMSE is reported either against the comfort-band center or against BOPTEST trajectory targets, depending on whether the task is control evaluation or surrogate predictive validation. Energy is integrated from reported HVAC power over the 900 s step. For transferability, the pre-registered pass/fail rule is m_s_RL <= 1.25 * m_s_PI on the same testcase yearly evaluation."))
    parts.append(p("Evaluation horizons: per-window versus yearly", "Heading3"))
    parts.append(p("We use a deliberate two-horizon evaluation protocol. The 14-day peak_heat_window and typical_heat_window scenarios are used for the in-testcase analyses of Sections 5 and 6 because they isolate controller-family behaviour at the operating extremes of the bestest_air scope: worst-case cold stress and mild average operation. The full yearly horizon is used for the transferability analysis of Section 7 because cross-testcase normalisation against each testcase's built-in PI baseline is fairest under full-year KPI averaging, which includes the target testcase's complete heating and non-heating regimes. Both evaluations share the same delta t = 900 s control protocol, the same comfort band [21, 24] C, and the same composite m_s metric; only the time horizon and the consequent normalisation differ."))

    parts.append(p("4.6 Statistical and audit protocol", "Heading2"))
    parts.append(p("The seed protocol is deliberately asymmetric because compute is dominated by live BOPTEST yearly evaluation. Single-seed sweeps are used for broad Pareto exploration. The two canonical MORL preference points are then expanded to N=5 seeds when the pre-registered instability rule is triggered. Per-seed monthly diagnostics, replay determinism checks, and post-N=5 falsification logging are recorded in configs/morl_canonical_selection_log.yaml. The replay test for seed 42 is bit-identical across all 12 monthly scenarios, so observed seed variance is attributed to RL training stochasticity rather than BOPTEST simulator nondeterminism."))
    parts.append(p("Block 3 is also pre-registered. The manifest specifies testcase candidates, excluded regimes, actuator-compatibility requirements, pass/fail criteria, early-termination logic, and append-only result slots before target-testcase runs. Adapter specifications are committed before live control runs when direct-TSup compatibility fails. This audit structure is included to make negative outcomes usable: a failed transfer cell is evidence about scope boundaries, not a post-hoc failure to tune."))

    parts.append(p("4.7 Reproducibility and audit trail", "Heading2"))
    parts.append(p("The project repository is https://github.com/Almaz-2001/HVAC_DRL_MORL.git. The reproducibility roadmap is maintained in roadmap.md, and the Block 3 pre-registration manifest is configs/block3_testcase_manifest.yaml. Three audit anchors are cited in the paper: MORL canonical pre-registration commit 93df9b364657ac77bbe3642e4bc277d1eb8a8b60; MORL post-N=5 falsification commit 62dc859d02f5f4a75fa4b55d8477c1d4e6206449; and Block 3 open/close commits 1861e48dc0eacb2e2c466ba0e0d03502d9185723 / b915bfc635c287dd1da907ce84ce44c81378edd5. A follow-up audit commit 7ada793bde6d9ae1483c389b813b11cc60bdec8a records the Block 3 close SHA in the manifest."))
    parts.append(p("Experiments use BOPTEST RTE version 1.0.0-dev through the HTTP-Docker service. The local analysis environment used for this document reports Python 3.11.9 and PyTorch 2.10.0+cpu; training and BOPTEST control runs are configured for CPU execution only (configs/*/agent.yaml device=cpu, surrogate_device=cpu), with no GPU used. Seed handling explicitly propagates the seed through Python random, NumPy, PyTorch, PYTHONHASHSEED, and action/observation spaces where available. A fixed-checkpoint BOPTEST replay test was bit-identical across all 12 monthly scenarios, so canonical seed variance is attributed to RL training stochasticity rather than simulator nondeterminism."))

    parts.append(p("5. Results I: Digital Twin Fidelity", "Heading1"))
    parts.append(p("Block 1 tests the paper's first falsifiable assumption: a more predictive digital twin should be the better RL training environment. The result is deliberately two-sided. The calibrated v3.5 physical twin is the best predictive model, but it is not the best closed-loop RL backend. Its successful role is narrower: v3.5 becomes a frozen physical teacher, while the smoother v3 model remains the rollout environment used by PPO."))

    parts.append(p("5.1 Control-oriented v3 versus physically calibrated v3.5", "Heading2"))
    parts.append(p("The v3 surrogate is a small two-headed direct-TSup model: a temperature-delta head and a power head share the same compact state/action encoding. Its design priority is not long-horizon forecasting, but smooth control-oriented gradients for PPO. The checkpoint contains 8,482 trainable parameters and trains with AdamW, cosine annealing, gradient clipping, and short multi-horizon losses. The original frozen article baseline was trained on a 51,200-row hourly corpus, but the current surrogate_v3 reference has been updated to the same 900 s / 15-min corpus used by v3.5. The corpus-matched v3 branch is therefore the correct apples-to-apples reference when attributing the v3-vs-v3.5 predictive gap."))
    parts.append(p("The v3.5 surrogate adds explicit physics through a learnable zone thermal capacitance C_zon and neural residual heads. Its calibration is not a single black-box fit. It follows the Stage A/B/C inverse-calibration protocol adapted from Hou and Evins [17]: Stage A cleans and aligns BOPTEST telemetry, Stage B identifies C_zon on excitation-rich windows, and Stage C refines residual temperature and power heads while keeping the physical parameter frozen. This separation is important because it allows us to report what was learned as physics and what was absorbed by the residual network."))

    parts.append(p("5.2 Stage A/B/C inverse calibration", "Heading2"))
    parts.append(table_xml([
        ["Stage", "Operation", "Article-facing evidence", "Interpretation"],
        ["A", "Latency, bias, power scaling, denoising, causal delta recomputation", "10,744 prepared 15-min rows; lag/bias/power corrections reported in S4", "Removes measurement artifacts before physical identification."],
        ["B", "Bayesian inverse identification of C_zon on high-excitation rows", "C_zon = 4.413e5 J/K, +5.1% versus 4.200e5 J/K prior", "Data produce a moderate, physically plausible update rather than an unconstrained fit."],
        ["C", "Residual temperature and power head refinement with C_zon frozen", "One-step RMSE_T near 0.235 C; power MAE near 482 W in canonical calibrated artifact", "Residual heads correct unmodelled dynamics without moving the identified capacitance."],
    ], [900, 2350, 2750, 3360], 13))
    parts.append(caption("Table 3. Stage A/B/C calibration summary. Detailed machine-readable sources: reports/hou_evins_stage_a_processing_table.csv, outputs/draft calibration summaries, and Supplementary Tables S4/S8/S11."))
    parts.append(p("Stage A is bookkeeping rather than learning: it prevents telemetry latency, static temperature bias, or power-meter scaling from being misidentified as building physics. Stage B is the physical identification step. It filters the calibration set to transient windows where C_zon is identifiable, then optimizes the scalar capacitance while residual heads are frozen. The final estimate, 4.413e5 J/K, is close enough to the 4.200e5 J/K prior to confirm prior sanity, but far enough from it to show that the data did update the physical model. Stage C then refines the neural residual heads. In the canonical two-pass implementation, the first pass improves temperature alignment and the second pass refines the power head; seeing zero Stage-B epochs in the final power-only JSON is therefore expected, not a calibration failure."))

    parts.append(p("5.3 Predictive validity", "Heading2"))
    parts.append(image_xml(image_rids["block1_replicative_validity_bars.png"], "block1_replicative_validity_bars", 6.2, 2.75))
    parts.append(caption("Figure 2a. Aggregate prepared-rollout errors. Calibrated v3.5 reduces recursive temperature error relative to raw v3.5 and the legacy v3 reference, while power error remains a separate residual-head calibration problem. This figure replaces a large predictive-validity table in the main text; full numbers remain in Supplementary Table S11."))
    parts.append(image_xml(image_rids["block1_predictive_validity_horizon_lines.png"], "block1_predictive_validity_horizon_lines", 6.4, 2.65))
    parts.append(caption(f"Figure 2b. Multi-horizon predictive validity across 1h/4h/8h/24h rollouts. The calibrated v3.5 twin reduces 24h RMSE_T to {nums['v35_cal_24h']} C, while the control-oriented v3 remains near {nums['v3_24h']} C at 24h. Hybrid_l010 shares v3 rollout dynamics; its predictive curve is therefore v3-like by construction."))
    parts.append(image_xml(image_rids["block1_rollout_24h_temperature_trace.png"], "block1_rollout_24h_temperature_trace", 6.4, 3.05))
    parts.append(caption("Figure 2c. Programmatically selected 24h rollout trace. The trace visualizes the held-out BOPTEST temperature trajectory against the calibrated v3.5 physical twin and the v3 baseline, supporting the aggregate 24h RMSE_T result without hand-picking a visually favorable episode."))
    parts.append(image_xml(image_rids["block1_temperature_residual_histograms.png"], "block1_temperature_residual_histograms", 6.2, 2.65))
    parts.append(caption("Figure 2d. Residual distributions. The calibrated model reduces the temperature residual spread, making the physical-twin improvement visible beyond a single mean RMSE number."))
    parts.append(p(f"The predictive-validity result is unambiguous, but it must be read with the corpus distinction explicit. Against the original hourly-corpus v3 baseline, calibrated v3.5 reaches 24h RMSE_T={nums['v35_arch_24h']} C versus {nums['v3_hourly_24h']} C. In the stricter matched-corpus check, the same v3 architecture trained on the 10,744-row 15-min corpus reaches {nums['v3_matched_24h']} C, still worse than calibrated v3.5 but much better than the legacy hourly checkpoint. Thus the full v3-to-v3.5 gain is not solely a physics-calibration effect: part comes from moving v3 onto the same 15-min telemetry resolution, and the remaining gap is the physically calibrated Stage A/B/C contribution. This establishes v3.5 as the correct model for physical forecasting and parameter interpretation, but not yet as the correct model for RL training."))
    parts.append(table_xml([
        ["Variant", "Corpus", "Step", "24h RMSE_T", "Interpretation"],
        ["v3 legacy", "51,200 transitions", "3600 s", "1.557 C", "Historical frozen v3 baseline and speed reference"],
        ["v3 matched", "10,744 transitions", "900 s", f"{nums['v3_matched_24h']} C", "Current 15-min apples-to-apples v3 reference"],
        ["raw v3.5", "10,744 transitions", "900 s", f"{nums['raw_v35_24h']} C", "Physical structure without Stage A/B/C is insufficient"],
        ["calibrated v3.5", "10,744 transitions", "900 s", f"{nums['v35_arch_24h']} C", "Best predictive twin after Stage A/B/C"],
    ], [1400, 2100, 900, 1300, 3660], 13))
    parts.append(caption("Table 4b. Corpus-matched Block 1 attribution. Source: reports/block1_corpus_matched_comparison.json. The active v3 path is 15-min compatible; the hourly v3 row is retained as a legacy baseline, not as the only v3 implementation."))

    parts.append(p("5.4 Runtime feasibility", "Heading2"))
    parts.append(p("The speed benchmark in Table 1 gives the computational reason for using surrogates at all. The BOPTEST RTE HTTP loop runs at 21.0 environment steps/s under the same 900 s control protocol. In-process v3 reaches 4,626 steps/s; calibrated v3.5 reaches 2,400 steps/s; the hybrid backend reaches 1,787 steps/s because it evaluates both v3 and frozen v3.5. Even the slowest surrogate is therefore 85.0x faster than the live RTE loop. This speed is not just a convenience: PPO-scale training would be impractical if every policy update required live BOPTEST HTTP stepping."))

    parts.append(p("5.5 Fidelity-to-control gap", "Heading2"))
    parts.append(image_xml(image_rids["main_fig3_fidelity_to_rl_gap.png"], "main_fig3_fidelity_to_rl_gap", 6.4, 3.25))
    parts.append(caption("Figure 3. Fidelity-to-control gap. Predictive 24h RMSE alone does not determine live closed-loop utility: calibrated v3.5 is the most predictive model but produces the largest live BOPTEST transfer error when used as the standalone RL backend."))
    parts.append(p(f"The closed-loop result reverses the predictive ranking. PPO trained directly on calibrated v3.5 fails on live BOPTEST: the architecture table reports peak/typical live transfer RMSE of {nums['v35_peak_live']}/{nums['v35_typical_live']} C and m_s above 1.0. This is a deployment-level failure, not a marginal loss of accuracy. In contrast, the hybrid backend keeps v3 as the rollout dynamics and uses v3.5 only as a frozen disagreement regularizer. On the thermostatic peak and typical windows, hybrid_l010 reaches live comfort RMSE of {nums['hybrid_peak_rmse']} C and {nums['hybrid_typical_rmse']} C, with m_s={nums['hybrid_peak_ms']} and {nums['hybrid_typical_ms']} respectively."))
    parts.append(p("This is the central Block 1 conclusion. Predictive fidelity and RL training utility are different objectives. v3.5 is the better digital twin, but a poor standalone control-learning landscape. v3 is the smoother control surrogate, but physically weaker. The hybrid backend assigns each model the role it can actually support: v3 supplies the learnable rollout surface; v3.5 supplies a physically calibrated soft target through L_total = L_PPO + lambda_temp||T_v3 - T_v3.5||^2 + lambda_power||P_v3 - P_v3.5||^2. Block 2 then tests whether that regularization role remains valid across controller families."))

    parts.append(p("6. Results II: Control Performance", "Heading1"))
    parts.append(p("Block 2 asks whether the Block 1 surrogate result survives contact with control: which backend actually produces useful live BOPTEST policies? The answer is controller-family specific. The calibrated v3.5 physical twin fails as a standalone rollout model and as a warm-start source, but succeeds as a frozen soft regularizer for thermostatic PPO. HDRL and MORL reject the temperature-disagreement channel and require a power-only variant. Thus the paper's claim is not that physics regularization is universally beneficial; it is that calibrated physics is useful only in the right role and with controller-specific weighting."))
    parts.append(p("6.1 PI baseline", "Heading2"))
    parts.append(p("The BOPTEST built-in PI controller is used as the reproducible standard reference, not as a custom-tuned strong PI baseline. Under yearly evaluation it has m_s=0.910, violation=63.59%, energy=104.07 kWh, and RMSE=3.395 C."))
    parts.append(p("6.2 Negative control: direct v3.5 warm-start", "Heading2"))
    parts.append(p("The direct v3.5 warm-start is a negative control: better physical predictive fidelity does not by itself create a better RL backend. PPO trained directly on calibrated v3.5 fails with m_s above 1.0 and live comfort RMSE above 4 C. Warm-starting from v3.5 also hurts later hybrid training rather than helping it. This closes the obvious alternative explanation that v3.5 might simply be useful as a pretraining environment."))
    parts.append(image_xml(image_rids["block2_warmstart_negative_eval_kpis.png"], "block2_warmstart_negative_eval_kpis", 6.1, 2.75))
    parts.append(caption("Figure 4a. Direct-v3.5 warm-start negative control. The physically calibrated twin is valuable as a frozen regularizer, not as a standalone rollout environment or warm-start source."))
    parts.append(p("6.3 Thermostatic PPO with hybrid regularization", "Heading2"))
    parts.append(p("Thermostatic PPO is the controller family that benefits most clearly from temperature disagreement regularization. The hybrid_l010 backend uses v3 for rollout dynamics and frozen v3.5 only as a disagreement penalty. On the peak window it nearly matches pure v3 safety while saving energy; on the typical window it improves m_s, violation, RMSE, and energy simultaneously. This is the positive Block 2 result: v3.5 is useful when it shapes the loss surface without replacing v3 as the rollout environment."))
    parts.append(image_xml(image_rids["block2_thermostatic_pure_v3_vs_hybrid_kpis.png"], "block2_thermostatic_pure_v3_vs_hybrid_kpis", 6.2, 2.75))
    parts.append(caption("Figure 4b. Thermostatic PPO comparison. Hybrid_l010 is the verified compromise: v3 supplies the learnable dynamics and v3.5 supplies physical disagreement regularization."))
    parts.append(image_xml(image_rids["hybrid_boptest_comfort_traces.png"], "hybrid_boptest_comfort_traces", 6.2, 2.75))
    parts.append(caption("Figure 4c. Live BOPTEST comfort traces for the hybrid controller. The trace-level view explains the KPI improvement physically: the hybrid policy stays close to the 21-24 C comfort band rather than winning only on aggregate metrics."))
    parts.append(image_xml(image_rids["hybrid_boptest_power_energy_traces.png"], "hybrid_boptest_power_energy_traces", 6.2, 2.65))
    parts.append(caption("Figure 4d. Hybrid power and cumulative-energy traces. This figure makes the comfort-energy mechanism visible and replaces the large yearly sanity table in the main text; detailed yearly outputs remain in the artifacts."))
    parts.append(p("6.4 HDRL sensitivity to physical regularization", "Heading2"))
    parts.append(p("HDRL provides the main negative result for the temperature channel. As lambda_temp increases, the safety metric and violation rate degrade; the best HDRL configuration is lambda_temp=0. This prevents a generic claim that physical disagreement penalties are always beneficial. The correct promotion rule from thermostatic to HDRL is not to copy lambda_temp=0.10, but to keep the v3 rollout dynamics and retain only the weak power-channel regularizer."))
    parts.append(image_xml(image_rids["block2_hdrl_lambda_sweep_sensitivity.png"], "block2_hdrl_lambda_sweep_sensitivity", 6.2, 2.75))
    parts.append(caption("Figure 4e. HDRL lambda sweep. The thermostatic-optimal temperature disagreement regularizer over-constrains HDRL; lambda_temp=0 is best on both peak and typical windows. This is the visual negative result that prevents overclaiming physics regularization."))
    parts.append(p("6.5 MORL and Pareto front", "Heading2"))
    parts.append(image_xml(image_rids["block2_morl_5d_vs_17d_radar.png"], "block2_morl_5d_vs_17d_radar", 6.1, 3.0))
    parts.append(caption("Figure 4f. MORL 5D versus 17D observation interface. The 5D path fails; the 17D TSup-style observation path recovers a usable MORL policy on the same power-only hybrid backend."))
    parts.append(image_xml(image_rids["block2_morl_pareto_energy_vs_ms.png"], "block2_morl_pareto_energy_vs_ms", 6.2, 3.7))
    parts.append(caption("Figure 4g. Block 2 MORL Pareto front with PI reference. Non-canonical sweep points are seed42-only; the two pre-registered canonical points are shown as N=5 means with 95% CI error bars. The energy-only endpoint demonstrates expected safety collapse, while canonical uncertainty shows that MORL remains promising but not deployment-stable."))
    parts.append(p("MORL N=5 falsification result", "Heading3"))
    parts.append(p("The neutral canonical w=(0.50,0.50,0.00) closes at m_s=0.187 +/- 0.078 over five seeds (sigma/mean=0.418). The practical canonical w=(0.75,0.25,0.00) improves the mean operating point to m_s=0.139 but remains high-variance at N=5. The replay test showed bit-identical BOPTEST yearly evaluation for a fixed checkpoint, so the variance is attributed to RL training stochasticity rather than simulator nondeterminism. The post-N=5 test falsified the action-saturation/seasonal-inversion hypothesis; the correct article claim is therefore that MORL is promising but not deployment-stable without future policy stabilization such as validation-based checkpoint selection or ensemble policy selection."))
    parts.append(image_xml(image_rids["block2_morl_seasonal_variance_inversion.png"], "block2_morl_seasonal_variance_inversion", 6.2, 2.45))
    parts.append(caption("Figure 4h. MORL monthly seed-variance heatmap after the N=5 falsification test. The earlier N=3 seasonal-inversion mechanism does not survive the pre-registered extension; the defensible result is high, distributed seed variance rather than an action-saturation mechanism."))

    parts.append(p("7. Results III: Transferability and Generalization", "Heading1"))
    parts.append(p("Block 3 reports a pre-registered transferability characterization of the hybrid recipe across three related BOPTEST hydronic testcases. Unlike Sections 5 and 6, which operate inside bestest_air, this section asks which components of the recipe transfer to a different actuator and envelope regime. The manifest was committed before Block 3 BOPTEST runs; result cells are appended rather than rewriting the pre-registration block."))
    parts.append(p("7.1 Pre-registered protocol", "Heading2"))
    parts.append(p("The protocol crosses three testcases with recalibration regimes none, partial, and full. The target testcases are bestest_hydronic_heat_pump, bestest_hydronic, and singlezone_commercial_hydronic. The primary live-control verdict is m_s_RL <= 1.25 x m_s_PI under the same 15-min yearly evaluation protocol. Controller fine-tuning on the target-recalibrated surrogate is explicitly excluded from Block 3; it is reserved as future Block 4 work."))
    parts.append(p("7.2 Actuator-interface adaptation", "Heading2"))
    parts.append(p("bestest_air exposes a direct supply-temperature style interface, but the hydronic testcases expose heat-pump, pump, valve, boiler, radiator, or commercial AHU variables. Therefore Block 3 transfer is adapter-mediated, not literal direct-TSup transfer. Each adapter mechanically maps the frozen policy's temperature-like action to documented hydronic setpoint and enable variables. The adapter is not learned and is smoke-tested before yearly evaluation."))
    parts.append(p("7.3 Transfer matrix", "Heading2"))
    parts.append(table_xml(tables["transfer"], [1750, 650, 650, 700, 700, 900, 900, 900, 2210], 12))
    parts.append(caption("Table 7. Block 3 transfer matrix. Controller verdicts use the pre-registered threshold m_s_RL <= 1.25 x m_s_PI. Full surrogate gains are diagnostic because the controller remains frozen by protocol. Source: reports/block3_transfer_matrix.csv."))
    parts.append(image_xml(image_rids["main_fig5_block3_transfer_verdict_heatmap.png"], "main_fig5_block3_transfer_verdict_heatmap", 6.0, 2.35))
    parts.append(caption("Figure 5. Block 3 transferability matrix. Red/green cells show the pre-registered controller verdict across three target testcases and three recalibration regimes. The partial regime is structurally identical to none for live-control KPIs because the controller remains frozen."))
    parts.append(p("7.4 Testcase-level interpretation", "Heading2"))
    parts.append(p(f"The primary testcase, bestest_hydronic_heat_pump, fails controller transfer at mode=none: m_s_RL={nums['hp_ms_rl']} versus m_s_PI={nums['hp_ms_pi']} and threshold {nums['hp_threshold']}. Energy is {nums['hp_energy_delta_abs']}% below PI, so the failure mode is comfort rather than energy. Full Stage A/B/C recalibration is strongly positive on the surrogate side, reducing RMSE_T from {nums['hp_raw_rmse']} C to {nums['hp_full_rmse']} C and re-identifying C_zon at {nums['hp_czon']}x the bestest_air value."))
    parts.append(p(f"The secondary testcase, bestest_hydronic, replicates this residential hydronic pattern. The frozen controller has m_s_RL={nums['hyd_ms_rl']} against threshold {nums['hyd_threshold']} and saves {nums['hyd_energy_delta_abs']}% energy versus PI, again failing on comfort. Full recalibration reduces RMSE_T from {nums['hyd_raw_rmse']} C to {nums['hyd_full_rmse']} C and re-identifies C_zon at {nums['hyd_czon']}x bestest_air."))
    parts.append(p(f"The stretch testcase, singlezone_commercial_hydronic, breaks the binary failure pattern in a useful way. It is a threshold PASS on safety (m_s_RL={nums['com_ms_rl']} versus m_s_PI={nums['com_ms_pi']} and threshold {nums['com_threshold']}), but it consumes {nums['com_energy_delta']}% more energy than PI. Full recalibration again succeeds on the surrogate side, reducing RMSE_T from {nums['com_raw_rmse']} C to {nums['com_full_rmse']} C and identifying C_zon at {nums['com_czon']}x bestest_air."))
    parts.append(p("7.5 Aggregate finding", "Heading2"))
    parts.append(p(f"Two patterns emerge. First, the surrogate component is uniformly transferable: full Stage A/B/C recalibration improves RMSE_T by {nums['block3_gain_min']}-{nums['block3_gain_max']}% across the three hydronic testcases, while C_zon ratios are tightly clustered in the {nums['block3_czon_min']}-{nums['block3_czon_max']}x range. This supports testcase-portability of the Hou-and-Evins inverse calibration pipeline on the hydronic family."))
    parts.append(image_xml(image_rids["main_fig6_block3_czon_consistency.png"], "main_fig6_block3_czon_consistency", 5.8, 2.65))
    parts.append(caption("Figure 6. Block 3 C_zon consistency. Full Stage A/B/C recalibration re-identifies the hydronic-family thermal capacitance at approximately 1.9x the bestest_air canonical value across all three target testcases."))
    parts.append(p(f"Second, the frozen controller component is regime-dependent and not deployment-ready. On the two residential hydronic testcases it fails the safety threshold while saving energy. On the commercial hydronic testcase it passes the safety threshold but inflates energy by {nums['com_energy_delta']}%. Both modes reflect the same boundary: the transferred policy was trained on the direct-supply-temperature geometry of bestest_air, and a mechanical adapter cannot make it understand the target actuator's response curve."))
    parts.append(p("7.6 Hypothesis closure and threshold caveat", "Heading2"))
    parts.append(p(f"H1_strong is falsified: frozen mode=none transfer is not deployment-ready across N=3 hydronic testcases. H2_medium is falsified by structural definition because partial recalibration updates only the surrogate while the live controller remains frozen. H3_weak is split: it is supported on the surrogate side and falsified on the controller side. The commercial cell also exposes a limitation of single-axis thresholds: it is a pre-registered threshold PASS on m_s, but not a deployment-ready pass because energy deteriorates by {nums['com_energy_delta']}% versus PI."))

    parts.append(p("8. Discussion", "Heading1"))
    parts.append(p("8.1 Predictive validity versus RL training utility", "Heading2"))
    parts.append(p("The central methodological result is that predictive validity and RL training utility are related but not equivalent. Predictive validation starts from held-out real BOPTEST states and measures whether a model can reproduce the next trajectory under known actions. Closed-loop RL training repeatedly visits states generated by the surrogate itself; small biases can therefore reshape the policy's experienced state distribution and produce qualitatively different control behavior. This explains why calibrated v3.5 can be a strong predictive twin and still fail as a standalone RL backend."))
    parts.append(p("The hybrid backend resolves this mismatch by separating roles. The smoother v3 model remains the rollout environment, preserving a learnable control landscape. The calibrated v3.5 model acts only as a frozen soft regularizer, injecting physical information without forcing the policy to optimize inside the grey-box model's own closed-loop dynamics. This is the main reason the paper frames v3.5 as a regularizer rather than as a replacement simulator."))
    parts.append(p("8.2 Controller-family specificity", "Heading2"))
    parts.append(p("The regularizer is not universally beneficial. Thermostatic PPO benefits from the physical anchor because its observation/action interface is low-dimensional and the disagreement penalty stabilizes the local temperature-power trade-off. HDRL and 17D MORL are more sensitive to the temperature disagreement channel and perform best with lambda_temp=0 or power-only regularization. This controller-family specificity is important: the article does not claim a universal physics-guided penalty, but a measured role for physical disagreement that depends on the controller architecture."))
    parts.append(p("The MORL findings sharpen this point. The 17D observation interface makes the Pareto sweep possible, but the canonical seed analysis remains high-variance at N=5. The failed action-saturation hypothesis is reported as a falsification result rather than hidden as noise. For deployment-oriented MORL, the next methodological layer should be policy stabilization, for example validation-based checkpoint selection, early stopping, or seed ensembles. Those techniques are deliberately not applied post-hoc in this paper because they would change the pre-registered canonical evaluation protocol."))
    parts.append(p("8.3 Transferability boundary", "Heading2"))
    parts.append(p(f"Block 3 decomposes transferability into a surrogate component and a controller component. The surrogate component transfers strongly: full Stage A/B/C recalibration improves RMSE_T by {nums['block3_gain_min']}-{nums['block3_gain_max']}% across all three hydronic testcases, and the identified C_zon ratios are tightly clustered in the {nums['block3_czon_min']}-{nums['block3_czon_max']}x range versus bestest_air. This consistency suggests that the inverse-calibration pipeline is portable across the tested hydronic family and that the hydronic cases are physically distinct from bestest_air rather than simple actuator aliases."))
    parts.append(p(f"The controller component does not transfer in a deployment-ready sense. On the two residential hydronic cases, the frozen controller saves energy but fails the comfort/safety threshold. On the commercial hydronic case, it passes the pre-registered m_s threshold but uses {nums['com_energy_delta']}% more energy than PI. These two failure modes have the same root: the transferred policy was trained for direct supply-temperature geometry and a mechanical adapter cannot teach it the target actuator response curve. The natural Block 4 experiment is therefore controller fine-tuning on the target-recalibrated surrogate, not further surrogate calibration alone."))
    parts.append(p("8.4 Threats to validity", "Heading2"))
    parts.append(p("Several limits remain. The bestest_air controller evidence uses one weather file and targeted sensitivity analysis rather than full hyperparameter optimization. HDRL is single-seed. MORL canonical points use N=5 but remain high-variance, so MORL is reported as promising rather than deployment-stable. Block 3 uses three related hydronic testcases, not arbitrary building archetypes, multi-zone systems, or climate zones. The 85x speed-up is measured against the practical BOPTEST RTE HTTP-Docker deployment rather than bare FMU evaluation; a direct-FMU benchmark is logged as a platform-limited reproducibility item."))
    parts.append(p("Two-horizon evaluation protocol. Sections 6 and 7 use different time horizons: 14-day peak/typical windows for in-testcase controller diagnostics and yearly evaluation for cross-testcase transferability. This is a deliberate methodological split documented in Section 4.4 rather than a silent change of metric. The two horizons can in principle disagree on relative controller ranking; therefore we do not interpret the Block 2 targeted-window results as yearly deployment guarantees. The qualitative findings that calibration improves predictive validity, that the hybrid backend resolves the fidelity-to-RL gap, and that hydronic transfer is limited by the frozen controller-adapter interface are not based on a hidden switch of comfort band, time step, or safety metric."))
    parts.append(p(f"The Block 3 threshold also has a known limitation. The pre-registered verdict uses m_s_RL <= 1.25 x m_s_PI, which is useful for auditability but can mask individual KPI deterioration. The commercial hydronic testcase is the example: it is a threshold PASS on m_s but not a deployment-ready pass because energy increases by {nums['com_energy_delta']}% versus PI. Future transferability protocols should use a tiered verdict: composite safety threshold plus per-KPI floors for energy and violation rate."))

    parts.append(p("9. Conclusion", "Heading1"))
    parts.append(p("This paper tests a common assumption in physics-informed RL for buildings: that a more predictive physical twin should be the better RL environment. On BOPTEST bestest_air, the answer is negative. Calibrated v3.5 improves long-horizon predictive fidelity, but direct use as the RL backend fails in live closed-loop control. The successful role of the calibrated twin is narrower and more useful: it serves as a frozen soft regularizer for a smoother v3 rollout backend."))
    parts.append(p("The resulting hybrid recipe gives a reproducible control improvement for thermostatic PPO and preserves the speed advantage required for RL training. It also clarifies limits. HDRL rejects the temperature disagreement channel, and MORL produces a usable 17D Pareto front but remains high-variance at N=5 canonical seeds. These are not hidden weaknesses; they define where the method works and where additional stabilization is required."))
    parts.append(p(f"The transferability block extends the contribution beyond bestest_air. Across three hydronic BOPTEST testcases, the Stage A/B/C inverse surrogate-calibration pipeline transfers robustly, with {nums['block3_gain_min']}-{nums['block3_gain_max']}% RMSE_T improvement and consistent C_zon re-identification in the {nums['block3_czon_min']}-{nums['block3_czon_max']}x range versus bestest_air. The frozen controller component does not transfer in a deployment-ready sense: residential hydronic cases fail comfort, while the commercial case passes the scalar threshold only by accepting a large energy penalty. The final conclusion is therefore component-level: the surrogate physics representation transfers; the controller-adapter interface is the bottleneck."))
    parts.append(p("The immediate next experiment is not another surrogate diagnostic, but target-specific controller fine-tuning on the target-recalibrated surrogate under a tiered comfort-energy transfer criterion. That experiment is intentionally left outside the current pre-registered scope so that the present paper can report the falsifications and boundaries without moving the goalposts."))
    parts.append(p("Data availability", "Heading1"))
    parts.append(p("All numerical values are sourced from CSV artifacts under reports/ and outputs/. The figure-source manifest is reports/article_real_figures_manifest.csv."))

    parts.append(page_break())
    parts.append(p("Supplementary Material: Hou and Evins Numerical Artifacts", "Heading1"))
    parts.append(p("The following tables summarize the eleven article-facing numerical artifacts adapted from the Hou-and-Evins surrogate reporting protocol [17]. The complete machine-readable versions remain in reports/hou_evins_*.csv."))
    for sid, title, rows in supplement_tables():
        parts.append(p(f"{sid}. {title}", "Heading2"))
        ncols = len(rows[0])
        widths = [9360 // ncols] * ncols
        widths[-1] += 9360 - sum(widths)
        parts.append(table_xml(rows, widths, 12 if ncols >= 7 else 14))

    parts.append(p("References", "Heading1"))
    references = [
        "[1] Zhang S, Ma M, Zhou N, Yan J. GLOBUS: Global building renovation potential by 2070. arXiv preprint arXiv:2406.04133, 2024.",
        "[2] Arroyo J, Spiessens F, Helsen L. Comparison of optimal control techniques for building energy management. Frontiers in Built Environment. 2022;8:849754. doi:10.3389/fbuil.2022.849754.",
        "[3] Arroyo J, Spiessens F, Helsen L. Identification of multi-zone grey-box building models for use in model predictive control. Journal of Building Performance Simulation. 2020;13(4):472-486. doi:10.1080/19401493.2020.1770861.",
        "[4] Blum D, Arroyo J, Huang S, Drgona J, Jorissen F, Walnum HT, Chen Y, Benne K, Vrabie D, Wetter M, Helsen L. Building optimization testing framework for simulation-based benchmarking of control strategies in buildings. Journal of Building Performance Simulation. 2021;14(5):586-610. doi:10.1080/19401493.2021.1986574.",
        "[5] Arroyo J, Manna C, Spiessens F, Helsen L. An OpenAI-Gym environment for the Building Optimization Testing Framework. Proceedings of the 17th IBPSA Conference; 2021 Sep 1-3; Bruges, Belgium.",
        "[6] Wang D, Zheng W, Wang Z, Wang Y, Pang X, Wang W. Comparison of reinforcement learning and model predictive control for building energy system optimization. Applied Thermal Engineering. 2023;228:120430. doi:10.1016/j.applthermaleng.2023.120430.",
        "[7] Arroyo J, Manna C, Spiessens F, Helsen L. Reinforced model predictive control for building energy management. Applied Energy. 2022;309:118346. doi:10.1016/j.apenergy.2021.118346.",
        "[8] Drgona J, Tuor AR, Chandan V, Vrabie DL. Physics-constrained deep learning of multi-zone building thermal dynamics. arXiv preprint arXiv:2011.05987, 2020.",
        "[9] Jiang Z, Lee YM. Deep transfer learning for thermal dynamics modeling in smart buildings. arXiv preprint arXiv:1911.03318, 2019.",
        "[10] Xu S, Wang Y, Wang Y, O'Neill Z, Zhu Q. One for many: transfer learning for building HVAC control. arXiv preprint arXiv:2008.03625, 2020.",
        "[11] Fierro G, Prakash AK, Blum D, Bender J, Paulson E, Wetter M. Notes paper: enabling building application development with simulated digital twins. BuildSys '22; 2022 Nov 9-10; Boston, MA, USA. doi:10.1145/3563357.3564060.",
        "[12] Mostafavi S, Song C, Sharma A, Goyal R, Brito A. Benchmarking model predictive control algorithms in Building Optimization Testing Framework. arXiv preprint arXiv:2301.13447, 2023.",
        "[13] Khabbazi AJ, Pergantis EN, Reyes Premer LD, Papageorgiou P, Lee AH, Braun JE, Henze GP, Kircher KJ. Lessons learned from field demonstrations of model predictive control and reinforcement learning for residential and commercial HVAC: a review. arXiv preprint arXiv:2503.05022, 2025.",
        "[14] Bekal GU, Ghareeb A, Pujari A. Continual reinforcement learning for HVAC systems control: integrating hypernetworks and transfer learning. arXiv preprint arXiv:2503.19212, 2025.",
        "[15] Ruiz de Vargas JM, Raisch F, Nagy Z, Pinson P, Goebel C. Counter-Dyna: data-efficient RL-based HVAC control using counterfactual building models. arXiv preprint arXiv:2605.04555, 2026.",
        "[16] Al Sayed K et al. Reinforcement learning for HVAC control in intelligent buildings: a technical and conceptual review. Journal of Building Engineering. 2024;95:110085.",
        "[17] Hou J, Evins R. A protocol for developing and evaluating neural network-based surrogate models and its application to building energy prediction. Renewable and Sustainable Energy Reviews. 2024;193:114283.",
        "[18] Gao H et al. Successful application of predictive information in deep reinforcement learning control: a case study based on an office building HVAC system. Energy. 2024;291:130344.",
        "[19] Wang Z et al. Safe deep reinforcement learning for building energy management. Applied Energy. 2025;377:124328.",
        "[20] Hedayat Z, Ziarati SR, Manganelli M. A physics-informed reinforcement learning framework for HVAC optimization: thermodynamically-constrained DDPG with uncertainty-aware safety verification. 2025.",
        "[21] Liao B et al. Year-round operational optimization of HVAC systems using hierarchical deep reinforcement learning with multi-objective reward mechanisms. Applied Energy. 2025;390:125816.",
        "[22] Roijers DM, Vamplew P, Whiteson S, Dazeley R. A survey of multi-objective sequential decision-making. Journal of Artificial Intelligence Research. 2013;48:67-113.",
        "[23] Coraci D et al. A scalable approach for real-world implementation of DRL controllers in buildings based on online transfer learning: the HiLo case study. Energy and Buildings. 2025;329:115254.",
        "[24] Hou J et al. Multi-source transfer learning method for enhancing the deployment of deep reinforcement learning in multi-zone building HVAC control. Energy and Buildings. 2024;322:114696.",
        "[25] Kadamala P et al. Enhancing HVAC control systems through transfer learning with deep reinforcement learning agents. Smart Energy. 2024;13:100131.",
        "[26] Coraci D et al. An innovative heterogeneous transfer learning framework to enhance the scalability of deep reinforcement learning controllers for building energy management. Building Simulation. 2024;17:739-770.",
        "[27] Samani MR et al. Distribution shift, generalization and OOD challenge in offline reinforcement learning: a comprehensive survey. Neural Computing and Applications. 2026.",
        "[28] Savino M et al. Deploying deep reinforcement learning for low-level HVAC control in multi-zone buildings: a comparative study with ASHRAE G36 sequences. Energy and Buildings. 2025;348:116456.",
        "[29] Sun Y et al. Individual room air-conditioning control in high-insulation residential building during winter: a deep reinforcement learning-based control model for reducing energy consumption. Energy and Buildings. 2024;323:114799.",
    ]
    for ref in references:
        parts.append(p(ref, size=18))
    return "".join(parts)


def copy_template_with_new_body(image_paths: list[Path]) -> None:
    template = next((p for p in TEMPLATE_CANDIDATES if p.exists()), None)
    if template is None:
        raise FileNotFoundError("No DOCX template found in: " + ", ".join(str(p) for p in TEMPLATE_CANDIDATES))
    timestamped_output = ROOT / "docs" / f"hvac_paper_skeleton_q1_restructured_updated_{datetime.now():%Y%m%d_%H%M%S}.docx"
    output_path = None
    for candidate in (OUTPUT, OUTPUT_FALLBACK, timestamped_output):
        try:
            with zipfile.ZipFile(candidate, "w", zipfile.ZIP_DEFLATED):
                pass
            candidate.unlink()
            output_path = candidate
            break
        except PermissionError:
            continue
    if output_path is None:
        raise PermissionError("Could not acquire a writable DOCX output path.")
    with zipfile.ZipFile(template, "r") as zin:
        document_xml = zin.read("word/document.xml").decode("utf-8")
        rels_xml = zin.read("word/_rels/document.xml.rels").decode("utf-8")
        sect_match = document_xml.rfind("<w:sectPr")
        sect_pr = ""
        if sect_match != -1:
            end = document_xml.find("</w:sectPr>", sect_match)
            if end != -1:
                sect_pr = document_xml[sect_match : end + len("</w:sectPr>")]

        ET.register_namespace("", "http://schemas.openxmlformats.org/package/2006/relationships")
        rels = ET.fromstring(rels_xml)
        image_rids: dict[str, str] = {}
        next_id = 100
        for img in image_paths:
            rid = f"rId{next_id}"
            next_id += 1
            image_rids[img.name] = rid
            rel = ET.SubElement(rels, "Relationship")
            rel.set("Id", rid)
            rel.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image")
            rel.set("Target", f"media/{img.name}")
        new_rels_xml = "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>" + ET.tostring(rels, encoding="unicode")

        body = build_body(image_rids) + sect_pr
        start = document_xml.find("<w:body>")
        end = document_xml.rfind("</w:body>")
        new_doc_xml = document_xml[: start + len("<w:body>")] + body + document_xml[end:]

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, new_doc_xml.encode("utf-8"))
                elif item.filename == "word/_rels/document.xml.rels":
                    zout.writestr(item, new_rels_xml.encode("utf-8"))
                else:
                    zout.writestr(item, zin.read(item.filename))
            for img in image_paths:
                zout.write(img, f"word/media/{img.name}")
    print(f"Wrote {output_path}")


def main() -> None:
    full_text_backup = ROOT / "docs" / "hvac_paper_skeleton_q1_restructured_patched_BACKUP_before_cuts.docx"
    visual_policy = ROOT / "docs" / "apply_main_paper_visual_policy.py"
    if full_text_backup.exists() and visual_policy.exists():
        # Keep this legacy entry point safe: rebuild from the full paper draft,
        # then apply only the agreed main-paper figure/table policy.
        shutil.copy2(full_text_backup, OUTPUT)
        runpy.run_path(str(visual_policy), run_name="__main__")
        return

    figures = [
        "block1_q1_fig01_pipeline.png",
        "main_fig2_stage_abc_czon.png",
        "main_fig3_matched_corpus_decomposition.png",
        "main_fig4_fidelity_control.png",
        "main_fig5_morl_pareto_variance.png",
        "main_fig5_block3_transfer_verdict_heatmap.png",
        "main_fig6_block3_czon_consistency.png",
        "main_fig8_audit_timeline.png",
    ]
    figure_dirs = [FIG_DIR, ROOT / "reports" / "figures"]
    image_paths = []
    for f in figures:
        path = next((d / f for d in figure_dirs if (d / f).exists()), FIG_DIR / f)
        image_paths.append(path)
    missing = [str(p) for p in image_paths if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing figures: " + ", ".join(missing))
    copy_template_with_new_body(image_paths)


if __name__ == "__main__":
    main()
