"""Rebuild the HVAC paper DOCX skeleton with real figures and CSV tables.

This script uses direct OOXML editing so it does not depend on python-docx.
It reads the existing skeleton as a template and writes a separate revised file.
"""

from __future__ import annotations

import csv
from datetime import datetime
import html
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "hvac_paper_skeleton.docx"
OUTPUT = ROOT / "docs" / "hvac_paper_skeleton_q1_restructured.docx"
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

    hdrl = read("reports/block2_hdrl_lambda_sweep_summary.csv")
    t5 = [["Variant", "Scenario", "m_s", "Violation %", "Energy kWh", "RMSE center C"]]
    for _, r in hdrl.iterrows():
        t5.append([r["variant"], r["scenario"], fmt(r["m_s"]), fmt(r["violation_pct"], 2), fmt(r["energy_kwh"], 1), fmt(r["rmse_center_c"], 3)])

    morl = read("reports/morl_pareto_front_table.csv")
    t6 = [["Kind", "Label", "w comfort", "w energy", "m_s", "Violation %", "Energy kWh", "RMSE C"]]
    for _, r in morl.iterrows():
        t6.append([r["kind"], r["label"], fmt(r["w_comfort"], 2), fmt(r["w_energy"], 2), fmt(r["ms_mean"]), fmt(r["violation_pct_mean"], 2), fmt(r["energy_kwh_mean"], 1), fmt(r["rmse_mean"], 3)])

    return {"arch": t1, "pred": t2, "speed": t3, "thermo": t4, "hdrl": t5, "morl": t6}


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


def build_body(image_rids: dict[str, str]) -> str:
    tables = main_key_tables()
    parts: list[str] = []
    parts.append(p("When Predictive Surrogates Fail as RL Environments:", bold=True, size=40, align="center"))
    parts.append(p("A Calibrated Physical Twin as Soft Regularizer for HVAC Control", bold=True, size=34, align="center"))
    parts.append(p("Almaz Sapargali", italic=True, align="center"))
    parts.append(p("[TODO] Affiliation, address, country.", italic=True, color="C01020", align="center"))
    parts.append(p("Target journal: Results in Engineering (Elsevier, Q1)", italic=True, color="707070", align="center"))
    parts.append(p("Abstract", "Heading1"))
    parts.append(p("Reinforcement learning controllers for HVAC systems are typically trained on neural-network surrogates because high-fidelity simulators are too slow for the millions of environment steps consumed by modern policy-gradient methods. We test the assumption that a more physically faithful surrogate is automatically a better RL training environment on BOPTEST bestest_air. A calibrated physical twin with explicit zone thermal capacitance achieves strong predictive validity, but fails as a standalone closed-loop RL environment. We therefore use the calibrated twin as a frozen soft physical regularizer for a smoother data-driven surrogate. The hybrid backend reaches 1,786.8 environment steps/s on one CPU thread, an 85.0x speed-up over the live BOPTEST RTE HTTP loop under the same 15-min protocol, and restores live closed-loop control performance. The final results show that the optimal regularization strength is controller-family specific: thermostatic PPO benefits from lambda_temp=0.10, whereas HDRL and 17D MORL require lambda_temp=0.00 with power-only regularization."))
    parts.append(p("Keywords: HVAC control; deep reinforcement learning; digital twin; physics-informed machine learning; BOPTEST; multi-objective reinforcement learning.", italic=True))

    parts.append(p("1. Introduction", "Heading1"))
    parts.append(p("The paper is organized around a single falsifiable question: does improving predictive fidelity of a building surrogate automatically improve downstream RL training utility? Our experiments show that the answer is no. The physically calibrated twin is valuable, but its best role is not to replace the control-oriented surrogate; it is to regularize it."))
    parts.append(p("Contributions", "Heading2"))
    parts.append(p("1. A comfort-oriented v3 surrogate for direct supply-temperature control and RL rollout generation."))
    parts.append(p("2. A physically informed v3.5 grey-box surrogate with explicit C_zon identified through Stage A/B/C inverse calibration."))
    parts.append(p("3. A hybrid backend where v3 supplies the smooth RL dynamics and calibrated v3.5 acts as a frozen physical disagreement regularizer."))
    parts.append(p("4. Controller-family-specific evidence: lambda_temp=0.10 for thermostatic PPO, lambda_temp=0.00 for HDRL and 17D MORL."))
    parts.append(p("5. A reproducible Hou-and-Evins-style numerical audit with S1-S11 supplementary tables and real-data figures."))

    parts.append(p("2. Related Work", "Heading1"))
    parts.append(p("2.1 Deep reinforcement learning for HVAC control", "Heading2"))
    parts.append(p("[TODO] Position PPO, hierarchical RL, safe RL, and MORL HVAC literature."))
    parts.append(p("2.2 Surrogate and digital twin models for building energy", "Heading2"))
    parts.append(p("[TODO] Contrast predictive surrogate validity with closed-loop RL training utility."))
    parts.append(p("2.3 Physics-informed and physics-guided machine learning", "Heading2"))
    parts.append(p("[TODO] Distinguish hard PINN constraints from the soft frozen regularizer used here."))
    parts.append(p("2.4 BOPTEST benchmarking", "Heading2"))
    parts.append(p("[TODO] Describe BOPTEST, bestest_air, KPI definitions, and why BOPTEST RTE is the live evaluation layer."))

    parts.append(p("3. Methodology", "Heading1"))
    parts.append(p("3.1 Control-oriented surrogate v3", "Heading2"))
    parts.append(p("The v3 surrogate is a direct-TSup, two-headed neural surrogate trained from BOPTEST trajectories. Its primary value is control-oriented smoothness: it gives PPO a stable local environment with temperature and power heads. Its limitation is interpretability: it is a black-box dynamics model without explicit thermal capacitance."))
    parts.append(p("3.2 Physically informed surrogate v3.5 and inverse calibration", "Heading2"))
    parts.append(p("The v3.5 surrogate introduces a physical backbone with explicit zone thermal capacitance C_zon. Stage A cleans and aligns telemetry, Stage B solves the inverse task by identifying C_zon on excitation windows, and Stage C calibrates residual heads while freezing the identified physical parameter."))
    parts.append(p("3.3 Hybrid backend", "Heading2"))
    parts.append(p("The hybrid backend evolves the policy under v3 dynamics and computes an auxiliary disagreement penalty against frozen calibrated v3.5. Thus v3.5 does not enter the policy forward pass; it shapes the loss only."))
    parts.append(p("L_total = L_PPO + lambda_temp ||T_v3 - T_v3.5||^2 + lambda_power ||P_v3 - P_v3.5||^2", italic=True))
    parts.append(p("3.4 Controller families", "Heading2"))
    parts.append(p("The controller stack contains the BOPTEST built-in PI reference, thermostatic PPO, HDRL, and 17D preference-conditioned MORL. Each family is evaluated under the same 15-min control protocol where possible."))

    parts.append(p("4. Experimental Setup", "Heading1"))
    parts.append(p("4.1 Testbed", "Heading2"))
    parts.append(p("All live validation uses the BOPTEST bestest_air testcase through boptest_rte HTTP. This choice is deliberate: the same serving layer used in experiments is also used in the speed benchmark."))
    parts.append(p("4.2 Sample generation and preprocessing", "Heading2"))
    parts.append(p("The data generation, sample-size justification, split representativeness, Stage A preprocessing, scaling, input independence, and hyperparameters are reported in Supplementary Tables S1-S8."))
    parts.append(p("4.3 Runtime characteristics", "Heading2"))
    parts.append(table_xml(tables["speed"], [2500, 1700, 1700, 1700, 1760], 16))
    parts.append(caption("Table 1. CPU throughput benchmark under the same 15-min control protocol. Source: reports/speed_benchmark_table.csv."))

    parts.append(p("5. Results I: Digital Twin Fidelity", "Heading1"))
    parts.append(p("5.1 Architecture comparison", "Heading2"))
    parts.append(table_xml(tables["arch"], [1150, 2100, 900, 900, 800, 900, 900, 900, 1810], 14))
    parts.append(caption("Table 2. Architecture comparison of v3, calibrated v3.5, and hybrid_l010. Source: reports/hou_evins_architecture_justification_table.csv."))
    parts.append(p("5.2 Replicative validity", "Heading2"))
    parts.append(image_xml(image_rids["block1_replicative_validity_bars.png"], "block1_replicative_validity_bars", 6.4, 2.65))
    parts.append(caption("Figure 1. One-step/short-horizon surrogate fidelity and power-head calibration. Source: reports/figures/article_real/block1_replicative_validity_bars.png."))
    parts.append(image_xml(image_rids["block1_temperature_residual_histograms.png"], "block1_temperature_residual_histograms", 6.0, 3.25))
    parts.append(caption("Figure 2. Residual distribution for raw and calibrated v3.5 on prepared rollouts."))
    parts.append(p("5.3 Predictive validity", "Heading2"))
    parts.append(table_xml(tables["pred"], [1150, 850, 1100, 1100, 1000, 1200, 1200], 14))
    parts.append(caption("Table 3. Predictive validity over 1h/4h/8h/24h horizons. Source: reports/hou_evins_predictive_validity_table.csv."))
    parts.append(image_xml(image_rids["block1_predictive_validity_horizon_lines.png"], "block1_predictive_validity_horizon_lines", 6.4, 2.65))
    parts.append(caption("Figure 3. Horizon-wise predictive validity from the article-facing CSV table."))
    parts.append(image_xml(image_rids["block1_rollout_24h_temperature_trace.png"], "block1_rollout_24h_temperature_trace", 6.6, 3.85))
    parts.append(caption("Figure 4. Programmatic 24h rollout realism. Peak and typical traces are selected as calibrated-v3.5 lower-median RMSE episodes within each scenario, not by visual inspection; the bottom panel reports the full per-episode RMSE distribution across all 8 held-out prepared rollouts."))
    parts.append(p("5.4 Failure mode", "Heading2"))
    parts.append(p("The calibrated v3.5 twin is predictive but not a good standalone RL training environment. Its live closed-loop transfer RMSE exceeds 4 C in the failure experiments, motivating the hybrid regularizer rather than direct replacement of v3."))

    parts.append(p("6. Results II: Control Performance", "Heading1"))
    parts.append(p("6.1 PI baseline", "Heading2"))
    parts.append(p("The BOPTEST built-in PI controller is used as the reproducible standard reference, not as a custom-tuned strong PI baseline. Under yearly evaluation it has m_s=0.910, violation=63.59%, energy=104.07 kWh, and RMSE=3.395 C."))
    parts.append(p("6.2 Negative control: direct v3.5 warm-start", "Heading2"))
    parts.append(image_xml(image_rids["block2_warmstart_negative_eval_kpis.png"], "block2_warmstart_negative_eval_kpis", 6.4, 2.65))
    parts.append(caption("Figure 5. Scratch versus v3.5 warm-start post-training BOPTEST KPIs. Training reward monitor CSVs were not available, so this figure uses real evaluation summaries."))
    parts.append(p("6.3 Thermostatic PPO with hybrid regularization", "Heading2"))
    parts.append(table_xml(tables["thermo"], [1450, 1900, 1100, 1300, 1300, 1500], 15))
    parts.append(caption("Table 4. Thermostatic pure-v3 versus hybrid_l010 BOPTEST KPIs."))
    parts.append(image_xml(image_rids["block2_thermostatic_pure_v3_vs_hybrid_kpis.png"], "block2_thermostatic_pure_v3_vs_hybrid_kpis", 6.4, 2.65))
    parts.append(caption("Figure 6. KPI comparison for pure v3 and canonical hybrid_l010 in peak and typical heat windows."))
    parts.append(p("6.4 HDRL sensitivity to physical regularization", "Heading2"))
    parts.append(table_xml(tables["hdrl"], [1100, 1900, 1000, 1250, 1250, 1450], 14))
    parts.append(caption("Table 5. HDRL lambda_temp sweep. Source: reports/block2_hdrl_lambda_sweep_summary.csv."))
    parts.append(image_xml(image_rids["block2_hdrl_lambda_sweep_sensitivity.png"], "block2_hdrl_lambda_sweep_sensitivity", 6.4, 2.65))
    parts.append(caption("Figure 7. HDRL rejects the temperature disagreement penalty; m_s and violation rise as lambda_temp increases."))
    parts.append(image_xml(image_rids["block2_hdrl_l000_winter_tracking.png"], "block2_hdrl_l000_winter_tracking", 6.4, 2.85))
    parts.append(caption("Figure 8. HDRL lambda_temp=0 winter trace. The available trace contains zone temperature and commanded supply, not an explicit high-level setpoint."))
    parts.append(p("6.5 MORL and Pareto front", "Heading2"))
    parts.append(table_xml(tables["morl"], [1050, 1800, 850, 850, 900, 1200, 1200, 1200], 13))
    parts.append(caption("Table 6. MORL Pareto front and PI baseline. Source: reports/morl_pareto_front_table.csv."))
    parts.append(image_xml(image_rids["block2_morl_pareto_energy_vs_ms.png"], "block2_morl_pareto_energy_vs_ms", 6.2, 3.7))
    parts.append(caption("Figure 9. MORL Pareto front: energy versus m_s. The energy-only endpoint demonstrates expected safety collapse."))
    parts.append(image_xml(image_rids["block2_morl_5d_vs_17d_radar.png"], "block2_morl_5d_vs_17d_radar", 5.5, 5.0))
    parts.append(caption("Figure 10. Observation interface ablation: failed 5D MORL versus successful 17D MORL."))
    parts.append(image_xml(image_rids["block2_morl_17d_seasonal_heatmap.png"], "block2_morl_17d_seasonal_heatmap", 6.4, 2.1))
    parts.append(caption("Figure 11. Seasonal profile of the final 17D MORL agent."))

    parts.append(p("7. Results III: Transferability and Generalization", "Heading1"))
    parts.append(p("This section remains optional until Block 3 is executed. The current article can be submitted as a single-testcase BOPTEST study if transferability is framed as future work."))

    parts.append(p("8. Discussion", "Heading1"))
    parts.append(p("8.1 Predictive validity versus RL training utility", "Heading2"))
    parts.append(p("Predictive validation starts from real states, while closed-loop RL training repeatedly visits states generated by the surrogate itself. This difference explains why v3.5 can be a strong predictive twin and still fail as a standalone RL environment."))
    parts.append(p("8.2 Controller-family specificity", "Heading2"))
    parts.append(p("Thermostatic PPO benefits from a physical anchor because the observation/action interface is low-dimensional. HDRL and 17D MORL are more sensitive to the temperature disagreement channel and perform best with lambda_temp=0 and power-only regularization."))
    parts.append(p("8.3 Threats to validity", "Heading2"))
    parts.append(p("The current evidence is based on one BOPTEST testcase, one weather file, limited seed replication for some branches, and targeted sensitivity analysis rather than full HPO. These limitations should be stated explicitly in the submission."))

    parts.append(p("9. Conclusion", "Heading1"))
    parts.append(p("The experiments support a narrow but defensible claim: a calibrated physical twin is not automatically the best RL environment, but it is useful as a soft regularizer for a smoother control-oriented surrogate. This resolves the fidelity-to-control gap for thermostatic PPO and enables a working 17D MORL controller with a measurable comfort-energy Pareto front."))
    parts.append(p("Data availability", "Heading1"))
    parts.append(p("All numerical values are sourced from CSV artifacts under reports/ and outputs/. The figure-source manifest is reports/article_real_figures_manifest.csv."))

    parts.append(page_break())
    parts.append(p("Supplementary Material: Hou and Evins Numerical Artifacts", "Heading1"))
    parts.append(p("The following tables summarize the eleven article-facing numerical artifacts. The complete machine-readable versions remain in reports/hou_evins_*.csv."))
    for sid, title, rows in supplement_tables():
        parts.append(p(f"{sid}. {title}", "Heading2"))
        ncols = len(rows[0])
        widths = [9360 // ncols] * ncols
        widths[-1] += 9360 - sum(widths)
        parts.append(table_xml(rows, widths, 12 if ncols >= 7 else 14))

    parts.append(p("References", "Heading1"))
    parts.append(p("[TODO] Populate from bibliography.bib: Hou and Evins (2024), BOPTEST, PPO, PINN, DRL-HVAC, MORL-HVAC, and physics-guided ML references."))
    return "".join(parts)


def copy_template_with_new_body(image_paths: list[Path]) -> None:
    if not TEMPLATE.exists():
        raise FileNotFoundError(TEMPLATE)
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
    with zipfile.ZipFile(TEMPLATE, "r") as zin:
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
    figures = [
        "block1_replicative_validity_bars.png",
        "block1_temperature_residual_histograms.png",
        "block1_predictive_validity_horizon_lines.png",
        "block1_rollout_24h_temperature_trace.png",
        "block2_warmstart_negative_eval_kpis.png",
        "block2_thermostatic_pure_v3_vs_hybrid_kpis.png",
        "block2_hdrl_lambda_sweep_sensitivity.png",
        "block2_hdrl_l000_winter_tracking.png",
        "block2_morl_pareto_energy_vs_ms.png",
        "block2_morl_5d_vs_17d_radar.png",
        "block2_morl_17d_seasonal_heatmap.png",
    ]
    image_paths = [FIG_DIR / f for f in figures]
    missing = [str(p) for p in image_paths if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing figures: " + ", ".join(missing))
    copy_template_with_new_body(image_paths)


if __name__ == "__main__":
    main()
