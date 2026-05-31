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
    parts.append(p("Reinforcement learning controllers for HVAC systems are typically trained on neural-network surrogates because high-fidelity simulators are too slow for the millions of environment steps consumed by modern policy-gradient methods. A natural assumption is that a more physically faithful surrogate produces a better training environment. We test that assumption on the BOPTEST bestest_air testcase and report a negative result: a calibrated physical twin with explicit zone thermal capacitance reaches a 24-hour rollout RMSE of 0.64 C versus 1.47 C uncalibrated, yet fails as a stand-alone RL training environment with live closed-loop RMSE above 4 C. We resolve the gap by using the calibrated twin as a frozen soft physical regularizer for a smoother control-oriented surrogate. The canonical hybrid backend sustains 1,786.8 environment steps/s on one CPU thread, an 85.0x speed-up over the live BOPTEST RTE HTTP loop under the same 15-min protocol, and restores live closed-loop RMSE to 0.795 C on the peak window and 0.633 C on the typical window. The optimal regularization strength is controller-family specific: lambda_temp=0.10 for thermostatic PPO, but lambda_temp=0.00 for HDRL and 17D MORL. A pre-registered transferability block further shows that the Stage A/B/C inverse surrogate-calibration pipeline transfers across three hydronic BOPTEST testcases with 60.2-87.8% RMSE_T improvement and consistent C_zon re-identification near 1.9x bestest_air, whereas frozen controller transfer is regime-dependent and not deployment-ready without target-specific fine-tuning. All numerical justifications are provided in Supplementary Tables S1-S11."))
    parts.append(p("Keywords: HVAC control; deep reinforcement learning; digital twin; physics-informed machine learning; BOPTEST; multi-objective reinforcement learning.", italic=True))

    parts.append(p("1. Introduction", "Heading1"))
    parts.append(p("The paper is organized around a falsifiable question: does improving predictive fidelity of a building surrogate automatically improve downstream RL training utility? Our experiments show that the answer is no. The physically calibrated twin is valuable, but its best role is not to replace the control-oriented surrogate; it is to regularize it. We then ask a second, pre-registered transferability question: which parts of the recipe transfer beyond bestest_air? The answer is component-level rather than binary: the surrogate calibration pipeline transfers strongly, while the frozen controller does not transfer in a deployment-ready sense."))
    parts.append(p("Contributions", "Heading2"))
    parts.append(p("1. A comfort-oriented v3 surrogate for direct supply-temperature control and RL rollout generation."))
    parts.append(p("2. A physically informed v3.5 grey-box surrogate with explicit C_zon identified through Stage A/B/C inverse calibration."))
    parts.append(p("3. A hybrid backend where v3 supplies the smooth RL dynamics and calibrated v3.5 acts as a frozen physical disagreement regularizer."))
    parts.append(p("4. Controller-family-specific evidence: lambda_temp=0.10 for thermostatic PPO, lambda_temp=0.00 for HDRL and 17D MORL."))
    parts.append(p("5. A pre-registered transferability analysis across three hydronic BOPTEST testcases, showing uniform surrogate-side transfer under full Stage A/B/C recalibration and regime-dependent frozen-controller transfer."))
    parts.append(p("6. A reproducible Hou-and-Evins-style numerical audit with S1-S11 supplementary tables and real-data figures."))

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
    parts.append(image_xml(image_rids["main_fig1_pipeline_schematic.png"], "main_fig1_pipeline_schematic", 6.7, 3.05))
    parts.append(caption("Figure 1. Hybrid backend schematic. The PPO policy rolls out through the smooth v3 surrogate while the calibrated v3.5 physical twin remains frozen and contributes only the disagreement regularizer."))
    parts.append(p("3.4 Controller families", "Heading2"))
    parts.append(p("The controller stack contains the BOPTEST built-in PI reference, thermostatic PPO, HDRL, and 17D preference-conditioned MORL. Each family is evaluated under the same 15-min control protocol where possible."))

    parts.append(p("4. Experimental Setup", "Heading1"))
    parts.append(p("4.1 Testbed", "Heading2"))
    parts.append(p("Blocks 1 and 2 use the BOPTEST bestest_air testcase through boptest_rte HTTP. This choice is deliberate: the same serving layer used in experiments is also used in the speed benchmark. Block 3 extends the evaluation to three related single-zone hydronic testcases: bestest_hydronic_heat_pump, bestest_hydronic, and singlezone_commercial_hydronic. These transfer cases are adapter-mediated because their actuator interfaces are not literal direct supply-temperature interfaces."))
    parts.append(p("4.2 Sample generation and preprocessing", "Heading2"))
    parts.append(p("The data generation, sample-size justification, split representativeness, Stage A preprocessing, scaling, input independence, and hyperparameters are reported in Supplementary Tables S1-S8."))
    parts.append(p("4.3 Runtime characteristics", "Heading2"))
    parts.append(table_xml(tables["speed"], [2500, 1700, 1700, 1700, 1760], 16))
    parts.append(caption("Table 1. CPU throughput benchmark under the same 15-min control protocol. Source: reports/speed_benchmark_table.csv."))
    parts.append(p("4.4 Evaluation protocol", "Heading2"))
    parts.append(p("All live-control results use 900 s control steps and 14-day monthly scenarios unless otherwise stated. Comfort is evaluated against the 21-24 C zone-temperature band. The main scalar safety metric is m_s, reported together with violation percentage and energy so that single-axis threshold decisions do not hide multi-objective trade-offs."))
    parts.append(p("Evaluation horizons: per-window versus yearly", "Heading3"))
    parts.append(p("We use a deliberate two-horizon evaluation protocol. The 14-day peak_heat_window and typical_heat_window scenarios are used for the in-testcase analyses of Sections 5 and 6 because they isolate controller-family behaviour at the operating extremes of the bestest_air scope: worst-case cold stress and mild average operation. The full yearly horizon is used for the transferability analysis of Section 7 because cross-testcase normalisation against each testcase's built-in PI baseline is fairest under full-year KPI averaging, which includes the target testcase's complete heating and non-heating regimes. Both evaluations share the same delta t = 900 s control protocol, the same comfort band [21, 24] C, and the same composite m_s metric; only the time horizon and the consequent normalisation differ."))
    parts.append(p("4.5 Reproducibility and audit trail", "Heading2"))
    parts.append(p("The project repository is https://github.com/Almaz-2001/HVAC_DRL_MORL.git. The reproducibility roadmap is maintained in roadmap.md, and the Block 3 pre-registration manifest is configs/block3_testcase_manifest.yaml. Three audit anchors are cited in the paper: MORL canonical pre-registration commit 93df9b364657ac77bbe3642e4bc277d1eb8a8b60; MORL post-N=5 falsification commit 62dc859d02f5f4a75fa4b55d8477c1d4e6206449; and Block 3 open/close commits 1861e48dc0eacb2e2c466ba0e0d03502d9185723 / b915bfc635c287dd1da907ce84ce44c81378edd5. A follow-up audit commit 7ada793bde6d9ae1483c389b813b11cc60bdec8a records the Block 3 close SHA in the manifest."))
    parts.append(p("Experiments use BOPTEST RTE version 1.0.0-dev through the HTTP-Docker service. The local analysis environment used for this document reports Python 3.11.9 and PyTorch 2.10.0+cpu; training and BOPTEST control runs are configured for CPU execution only (configs/*/agent.yaml device=cpu, surrogate_device=cpu), with no GPU used. Seed handling explicitly propagates the seed through Python random, NumPy, PyTorch, PYTHONHASHSEED, and action/observation spaces where available. A fixed-checkpoint BOPTEST replay test was bit-identical across all 12 monthly scenarios, so canonical seed variance is attributed to RL training stochasticity rather than simulator nondeterminism."))

    parts.append(p("5. Results I: Digital Twin Fidelity", "Heading1"))
    parts.append(p("Block 1 tests the paper's first falsifiable assumption: a more predictive digital twin should be the better RL training environment. The result is deliberately two-sided. The calibrated v3.5 physical twin is the best predictive model, but it is not the best closed-loop RL backend. Its successful role is narrower: v3.5 becomes a frozen physical teacher, while the smoother v3 model remains the rollout environment used by PPO."))

    parts.append(p("5.1 Control-oriented v3 versus physically calibrated v3.5", "Heading2"))
    parts.append(table_xml(tables["arch"], [1150, 2100, 900, 900, 800, 900, 900, 900, 1810], 14))
    parts.append(caption("Table 2. Architecture comparison of v3, calibrated v3.5, and hybrid_l010. Source: reports/hou_evins_architecture_justification_table.csv."))
    parts.append(p("The v3 surrogate is a small two-headed direct-TSup model: a temperature-delta head and a power head share the same compact state/action encoding. Its design priority is not long-horizon forecasting, but smooth control-oriented gradients for PPO. The checkpoint contains 8,482 trainable parameters and trains with AdamW, cosine annealing, gradient clipping, and short multi-horizon losses. The original frozen article baseline was trained on a 51,200-row hourly corpus, but the current surrogate_v3 reference has been updated to the same 900 s / 15-min corpus used by v3.5. The corpus-matched v3 branch is therefore the correct apples-to-apples reference when attributing the v3-vs-v3.5 predictive gap."))
    parts.append(p("The v3.5 surrogate adds explicit physics through a learnable zone thermal capacitance C_zon and neural residual heads. Its calibration is not a single black-box fit. It follows the Stage A/B/C inverse-calibration protocol: Stage A cleans and aligns BOPTEST telemetry, Stage B identifies C_zon on excitation-rich windows, and Stage C refines residual temperature and power heads while keeping the physical parameter frozen. This separation is important because it allows us to report what was learned as physics and what was absorbed by the residual network."))

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
    parts.append(table_xml(tables["pred"], [1150, 850, 1100, 1100, 1000, 1200, 1200], 14))
    parts.append(caption("Table 4. Predictive validity over 1h/4h/8h/24h horizons. Source: reports/hou_evins_predictive_validity_table.csv."))
    parts.append(image_xml(image_rids["block1_predictive_validity_horizon_lines.png"], "block1_predictive_validity_horizon_lines", 6.4, 2.65))
    parts.append(caption("Figure 2a. Block 1 predictive validity across 1h/4h/8h/24h horizons. The calibrated v3.5 twin reduces 24h RMSE_T to 0.644 C, while the control-oriented v3 remains near 1.56 C at 24h. Hybrid_l010 shares v3 rollout dynamics; its predictive curve is therefore v3-like by construction."))
    parts.append(image_xml(image_rids["block1_rollout_24h_temperature_trace.png"], "block1_rollout_24h_temperature_trace", 6.4, 3.05))
    parts.append(caption("Figure 2b. Programmatically selected 24h rollout trace. The trace visualizes the held-out BOPTEST temperature trajectory against the calibrated v3.5 physical twin and the v3 baseline, supporting the aggregate 24h RMSE_T result without hand-picking a visually favorable episode."))
    parts.append(p("The predictive-validity result is unambiguous, but it must be read with the corpus distinction explicit. Against the original hourly-corpus v3 baseline, calibrated v3.5 reaches 24h RMSE_T=0.644 C versus 1.558 C. In the stricter matched-corpus check, the same v3 architecture trained on the 10,744-row 15-min corpus reaches 0.876 C, still worse than calibrated v3.5 but much better than the legacy hourly checkpoint. Thus the full v3-to-v3.5 gain is not solely a physics-calibration effect: part comes from moving v3 onto the same 15-min telemetry resolution, and the remaining gap is the physically calibrated Stage A/B/C contribution. This establishes v3.5 as the correct model for physical forecasting and parameter interpretation, but not yet as the correct model for RL training."))
    parts.append(table_xml([
        ["Variant", "Corpus", "Step", "24h RMSE_T", "Interpretation"],
        ["v3 legacy", "51,200 transitions", "3600 s", "1.557 C", "Historical frozen v3 baseline and speed reference"],
        ["v3 matched", "10,744 transitions", "900 s", "0.876 C", "Current 15-min apples-to-apples v3 reference"],
        ["raw v3.5", "10,744 transitions", "900 s", "1.466 C", "Physical structure without Stage A/B/C is insufficient"],
        ["calibrated v3.5", "10,744 transitions", "900 s", "0.644 C", "Best predictive twin after Stage A/B/C"],
    ], [1400, 2100, 900, 1300, 3660], 13))
    parts.append(caption("Table 4b. Corpus-matched Block 1 attribution. Source: reports/block1_corpus_matched_comparison.json. The active v3 path is 15-min compatible; the hourly v3 row is retained as a legacy baseline, not as the only v3 implementation."))

    parts.append(p("5.4 Runtime feasibility", "Heading2"))
    parts.append(p("The speed benchmark in Table 1 gives the computational reason for using surrogates at all. The BOPTEST RTE HTTP loop runs at 21.0 environment steps/s under the same 900 s control protocol. In-process v3 reaches 4,626 steps/s; calibrated v3.5 reaches 2,400 steps/s; the hybrid backend reaches 1,787 steps/s because it evaluates both v3 and frozen v3.5. Even the slowest surrogate is therefore 85.0x faster than the live RTE loop. This speed is not just a convenience: PPO-scale training would be impractical if every policy update required live BOPTEST HTTP stepping."))

    parts.append(p("5.5 Fidelity-to-control gap", "Heading2"))
    parts.append(image_xml(image_rids["main_fig3_fidelity_to_rl_gap.png"], "main_fig3_fidelity_to_rl_gap", 6.4, 3.25))
    parts.append(caption("Figure 3. Fidelity-to-control gap. Predictive 24h RMSE alone does not determine live closed-loop utility: calibrated v3.5 is the most predictive model but produces the largest live BOPTEST transfer error when used as the standalone RL backend."))
    parts.append(p("The closed-loop result reverses the predictive ranking. PPO trained directly on calibrated v3.5 fails on live BOPTEST: the architecture table reports peak/typical live transfer RMSE of 4.32/4.40 C and m_s above 1.0. This is a deployment-level failure, not a marginal loss of accuracy. In contrast, the hybrid backend keeps v3 as the rollout dynamics and uses v3.5 only as a frozen disagreement regularizer. On the thermostatic peak and typical windows, hybrid_l010 reaches live comfort RMSE of 0.795 C and 0.633 C, with m_s=0.0866 and 0.0411 respectively."))
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
    parts.append(table_xml(tables["thermo"], [1450, 1900, 1100, 1300, 1300, 1500], 15))
    parts.append(caption("Table 4. Thermostatic pure-v3 versus hybrid_l010 BOPTEST KPIs."))
    parts.append(p("Thermostatic PPO is the controller family that benefits most clearly from temperature disagreement regularization. The hybrid_l010 backend uses v3 for rollout dynamics and frozen v3.5 only as a disagreement penalty. On the peak window it nearly matches pure v3 safety while saving energy; on the typical window it improves m_s, violation, RMSE, and energy simultaneously. This is the positive Block 2 result: v3.5 is useful when it shapes the loss surface without replacing v3 as the rollout environment."))
    parts.append(image_xml(image_rids["block2_thermostatic_pure_v3_vs_hybrid_kpis.png"], "block2_thermostatic_pure_v3_vs_hybrid_kpis", 6.2, 2.75))
    parts.append(caption("Figure 4b. Thermostatic PPO comparison. Hybrid_l010 is the verified compromise: v3 supplies the learnable dynamics and v3.5 supplies physical disagreement regularization."))
    parts.append(p("Unified evaluator sanity check", "Heading3"))
    parts.append(p("The new universal yearly validation runner uses testcase-aware presets so that bestest_air is evaluated with the article-style observation encoding while hydronic transfer cases use the Block 3 adapter presets. Table 4b records the current bestest_air thermostatic yearly output from the universal runner; it is included as an audit/sanity table rather than replacing the frozen Block 2 KPI table above."))
    parts.append(table_xml(tables["universal_bestest_air"], [1500, 850, 950, 1050, 850, 850, 850, 850], 13))
    parts.append(caption("Table 4b. Universal yearly validation sanity check for bestest_air thermostatic PPO. Source: outputs/universal_validation/bestest_air/thermostatic_bestest_air_article/thermostatic_universal_yearly_summary.csv."))
    parts.append(p("6.4 HDRL sensitivity to physical regularization", "Heading2"))
    parts.append(table_xml(tables["hdrl"], [1100, 1900, 1000, 1250, 1250, 1450], 14))
    parts.append(caption("Table 5. HDRL lambda_temp sweep. Source: reports/block2_hdrl_lambda_sweep_summary.csv."))
    parts.append(p("HDRL provides the main negative result for the temperature channel. As lambda_temp increases, the safety metric and violation rate degrade; the best HDRL configuration is lambda_temp=0. This prevents a generic claim that physical disagreement penalties are always beneficial. The correct promotion rule from thermostatic to HDRL is not to copy lambda_temp=0.10, but to keep the v3 rollout dynamics and retain only the weak power-channel regularizer."))
    parts.append(image_xml(image_rids["block2_hdrl_lambda_sweep_sensitivity.png"], "block2_hdrl_lambda_sweep_sensitivity", 6.2, 2.75))
    parts.append(caption("Figure 4c. HDRL lambda sweep. The thermostatic-optimal temperature disagreement regularizer over-constrains HDRL; lambda_temp=0 is best on both peak and typical windows."))
    parts.append(p("6.5 MORL and Pareto front", "Heading2"))
    parts.append(table_xml([
        ["Variant", "Obs dim", "RMSE_T", "Violation %", "Energy kWh", "m_s", "Interpretation"],
        ["MORL 5D basic", "5", "4.96", "74.5", "121.0", "1.046", "failed observation interface"],
        ["MORL 17D power-only", "17", "0.72", "4.9", "248.6", "0.099", "canonical usable path"],
    ], [1400, 800, 900, 1100, 1100, 900, 3160], 14))
    parts.append(caption("Table 6a. MORL observation-interface ablation. Source: reports/block2_morl_comparison_summary.csv."))
    parts.append(image_xml(image_rids["block2_morl_5d_vs_17d_radar.png"], "block2_morl_5d_vs_17d_radar", 6.1, 3.0))
    parts.append(caption("Figure 4d. MORL 5D versus 17D observation interface. The 5D path fails; the 17D TSup-style observation path recovers a usable MORL policy on the same power-only hybrid backend."))
    parts.append(table_xml(tables["morl"], [1050, 1800, 850, 850, 900, 1200, 1200, 1200], 13))
    parts.append(caption("Table 6b. MORL Pareto front and PI baseline. Source: reports/morl_pareto_front_table.csv."))
    parts.append(image_xml(image_rids["block2_morl_pareto_energy_vs_ms.png"], "block2_morl_pareto_energy_vs_ms", 6.2, 3.7))
    parts.append(caption("Figure 4e. Block 2 MORL Pareto front with PI reference. Non-canonical sweep points are seed42-only; the two pre-registered canonical points are shown as N=5 means with 95% CI error bars. The energy-only endpoint demonstrates expected safety collapse, while canonical uncertainty shows that MORL remains promising but not deployment-stable."))
    parts.append(p("MORL N=5 falsification result", "Heading3"))
    parts.append(p("The neutral canonical w=(0.50,0.50,0.00) closes at m_s=0.187 +/- 0.078 over five seeds (sigma/mean=0.418). The practical canonical w=(0.75,0.25,0.00) improves the mean operating point to m_s=0.139 but remains high-variance at N=5. The replay test showed bit-identical BOPTEST yearly evaluation for a fixed checkpoint, so the variance is attributed to RL training stochasticity rather than simulator nondeterminism. The post-N=5 test falsified the action-saturation/seasonal-inversion hypothesis; the correct article claim is therefore that MORL is promising but not deployment-stable without future policy stabilization such as validation-based checkpoint selection or ensemble policy selection."))
    parts.append(image_xml(image_rids["block2_morl_17d_seasonal_heatmap.png"], "block2_morl_17d_seasonal_heatmap", 6.2, 2.75))
    parts.append(caption("Figure 4f. MORL seasonal seed-variance heatmap at N=5. The earlier N=3 seasonal-inversion mechanism does not survive the pre-registered extension; high seed variance is the defensible result."))

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
    parts.append(p("The primary testcase, bestest_hydronic_heat_pump, fails controller transfer at mode=none: m_s_RL=0.665 versus m_s_PI=0.464 and threshold 0.579. Energy is 7.3% below PI, so the failure mode is comfort rather than energy. Full Stage A/B/C recalibration is strongly positive on the surrogate side, reducing RMSE_T from 1.421 C to 0.565 C and re-identifying C_zon at 1.89x the bestest_air value."))
    parts.append(p("The secondary testcase, bestest_hydronic, replicates this residential hydronic pattern. The frozen controller has m_s_RL=0.976 against threshold 0.938 and saves 5.8% energy versus PI, again failing on comfort. Full recalibration reduces RMSE_T from 2.666 C to 0.335 C and re-identifies C_zon at 1.95x bestest_air."))
    parts.append(p("The stretch testcase, singlezone_commercial_hydronic, breaks the binary failure pattern in a useful way. It is a threshold PASS on safety (m_s_RL=0.431 versus m_s_PI=0.628 and threshold 0.785), but it consumes 35.3% more energy than PI. Full recalibration again succeeds on the surrogate side, reducing RMSE_T from 1.952 C to 0.238 C and identifying C_zon at 1.91x bestest_air."))
    parts.append(p("7.5 Aggregate finding", "Heading2"))
    parts.append(p("Two patterns emerge. First, the surrogate component is uniformly transferable: full Stage A/B/C recalibration improves RMSE_T by 60.2%, 87.4%, and 87.8% across the three hydronic testcases, while C_zon ratios are tightly clustered at 1.89x, 1.95x, and 1.91x. This supports testcase-portability of the Hou-and-Evins inverse calibration pipeline on the hydronic family."))
    parts.append(image_xml(image_rids["main_fig6_block3_czon_consistency.png"], "main_fig6_block3_czon_consistency", 5.8, 2.65))
    parts.append(caption("Figure 6. Block 3 C_zon consistency. Full Stage A/B/C recalibration re-identifies the hydronic-family thermal capacitance at approximately 1.9x the bestest_air canonical value across all three target testcases."))
    parts.append(p("Second, the frozen controller component is regime-dependent and not deployment-ready. On the two residential hydronic testcases it fails the safety threshold while saving energy. On the commercial hydronic testcase it passes the safety threshold but inflates energy by 35.3%. Both modes reflect the same boundary: the transferred policy was trained on the direct-supply-temperature geometry of bestest_air, and a mechanical adapter cannot make it understand the target actuator's response curve."))
    parts.append(p("7.6 Hypothesis closure and threshold caveat", "Heading2"))
    parts.append(p("H1_strong is falsified: frozen mode=none transfer is not deployment-ready across N=3 hydronic testcases. H2_medium is falsified by structural definition because partial recalibration updates only the surrogate while the live controller remains frozen. H3_weak is split: it is supported on the surrogate side and falsified on the controller side. The commercial cell also exposes a limitation of single-axis thresholds: it is a pre-registered threshold PASS on m_s, but not a deployment-ready pass because energy deteriorates by 35.3% versus PI."))

    parts.append(p("8. Discussion", "Heading1"))
    parts.append(p("8.1 Predictive validity versus RL training utility", "Heading2"))
    parts.append(p("The central methodological result is that predictive validity and RL training utility are related but not equivalent. Predictive validation starts from held-out real BOPTEST states and measures whether a model can reproduce the next trajectory under known actions. Closed-loop RL training repeatedly visits states generated by the surrogate itself; small biases can therefore reshape the policy's experienced state distribution and produce qualitatively different control behavior. This explains why calibrated v3.5 can be a strong predictive twin and still fail as a standalone RL backend."))
    parts.append(p("The hybrid backend resolves this mismatch by separating roles. The smoother v3 model remains the rollout environment, preserving a learnable control landscape. The calibrated v3.5 model acts only as a frozen soft regularizer, injecting physical information without forcing the policy to optimize inside the grey-box model's own closed-loop dynamics. This is the main reason the paper frames v3.5 as a regularizer rather than as a replacement simulator."))
    parts.append(p("8.2 Controller-family specificity", "Heading2"))
    parts.append(p("The regularizer is not universally beneficial. Thermostatic PPO benefits from the physical anchor because its observation/action interface is low-dimensional and the disagreement penalty stabilizes the local temperature-power trade-off. HDRL and 17D MORL are more sensitive to the temperature disagreement channel and perform best with lambda_temp=0 or power-only regularization. This controller-family specificity is important: the article does not claim a universal physics-guided penalty, but a measured role for physical disagreement that depends on the controller architecture."))
    parts.append(p("The MORL findings sharpen this point. The 17D observation interface makes the Pareto sweep possible, but the canonical seed analysis remains high-variance at N=5. The failed action-saturation hypothesis is reported as a falsification result rather than hidden as noise. For deployment-oriented MORL, the next methodological layer should be policy stabilization, for example validation-based checkpoint selection, early stopping, or seed ensembles. Those techniques are deliberately not applied post-hoc in this paper because they would change the pre-registered canonical evaluation protocol."))
    parts.append(p("8.3 Transferability boundary", "Heading2"))
    parts.append(p("Block 3 decomposes transferability into a surrogate component and a controller component. The surrogate component transfers strongly: full Stage A/B/C recalibration improves RMSE_T by 60.2-87.8% across all three hydronic testcases, and the identified C_zon ratios are tightly clustered near 1.9x bestest_air. This consistency suggests that the inverse-calibration pipeline is portable across the tested hydronic family and that the hydronic cases are physically distinct from bestest_air rather than simple actuator aliases."))
    parts.append(p("The controller component does not transfer in a deployment-ready sense. On the two residential hydronic cases, the frozen controller saves energy but fails the comfort/safety threshold. On the commercial hydronic case, it passes the pre-registered m_s threshold but uses 35.3% more energy than PI. These two failure modes have the same root: the transferred policy was trained for direct supply-temperature geometry and a mechanical adapter cannot teach it the target actuator response curve. The natural Block 4 experiment is therefore controller fine-tuning on the target-recalibrated surrogate, not further surrogate calibration alone."))
    parts.append(p("8.4 Threats to validity", "Heading2"))
    parts.append(p("Several limits remain. The bestest_air controller evidence uses one weather file and targeted sensitivity analysis rather than full hyperparameter optimization. HDRL is single-seed. MORL canonical points use N=5 but remain high-variance, so MORL is reported as promising rather than deployment-stable. Block 3 uses three related hydronic testcases, not arbitrary building archetypes, multi-zone systems, or climate zones. The 85x speed-up is measured against the practical BOPTEST RTE HTTP-Docker deployment rather than bare FMU evaluation; a direct-FMU benchmark is logged as a platform-limited reproducibility item."))
    parts.append(p("Two-horizon evaluation protocol. Sections 6 and 7 use different time horizons: 14-day peak/typical windows for in-testcase controller diagnostics and yearly evaluation for cross-testcase transferability. This is a deliberate methodological split documented in Section 4.4 rather than a silent change of metric. The two horizons can in principle disagree on relative controller ranking; therefore we do not interpret the Block 2 targeted-window results as yearly deployment guarantees. The qualitative findings that calibration improves predictive validity, that the hybrid backend resolves the fidelity-to-RL gap, and that hydronic transfer is limited by the frozen controller-adapter interface are not based on a hidden switch of comfort band, time step, or safety metric."))
    parts.append(p("The Block 3 threshold also has a known limitation. The pre-registered verdict uses m_s_RL <= 1.25 x m_s_PI, which is useful for auditability but can mask individual KPI deterioration. The commercial hydronic testcase is the example: it is a threshold PASS on m_s but not a deployment-ready pass because energy increases by 35.3% versus PI. Future transferability protocols should use a tiered verdict: composite safety threshold plus per-KPI floors for energy and violation rate."))

    parts.append(p("9. Conclusion", "Heading1"))
    parts.append(p("This paper tests a common assumption in physics-informed RL for buildings: that a more predictive physical twin should be the better RL environment. On BOPTEST bestest_air, the answer is negative. Calibrated v3.5 improves long-horizon predictive fidelity, but direct use as the RL backend fails in live closed-loop control. The successful role of the calibrated twin is narrower and more useful: it serves as a frozen soft regularizer for a smoother v3 rollout backend."))
    parts.append(p("The resulting hybrid recipe gives a reproducible control improvement for thermostatic PPO and preserves the speed advantage required for RL training. It also clarifies limits. HDRL rejects the temperature disagreement channel, and MORL produces a usable 17D Pareto front but remains high-variance at N=5 canonical seeds. These are not hidden weaknesses; they define where the method works and where additional stabilization is required."))
    parts.append(p("The transferability block extends the contribution beyond bestest_air. Across three hydronic BOPTEST testcases, the Stage A/B/C inverse surrogate-calibration pipeline transfers robustly, with 60.2-87.8% RMSE_T improvement and consistent C_zon re-identification near 1.9x bestest_air. The frozen controller component does not transfer in a deployment-ready sense: residential hydronic cases fail comfort, while the commercial case passes the scalar threshold only by accepting a large energy penalty. The final conclusion is therefore component-level: the surrogate physics representation transfers; the controller-adapter interface is the bottleneck."))
    parts.append(p("The immediate next experiment is not another surrogate diagnostic, but target-specific controller fine-tuning on the target-recalibrated surrogate under a tiered comfort-energy transfer criterion. That experiment is intentionally left outside the current pre-registered scope so that the present paper can report the falsifications and boundaries without moving the goalposts."))
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
    figures = [
        "main_fig1_pipeline_schematic.png",
        "block1_predictive_validity_horizon_lines.png",
        "block1_rollout_24h_temperature_trace.png",
        "main_fig3_fidelity_to_rl_gap.png",
        "block2_warmstart_negative_eval_kpis.png",
        "block2_thermostatic_pure_v3_vs_hybrid_kpis.png",
        "block2_hdrl_lambda_sweep_sensitivity.png",
        "block2_morl_5d_vs_17d_radar.png",
        "block2_morl_17d_seasonal_heatmap.png",
        "block2_morl_pareto_energy_vs_ms.png",
        "main_fig5_block3_transfer_verdict_heatmap.png",
        "main_fig6_block3_czon_consistency.png",
    ]
    image_paths = [FIG_DIR / f for f in figures]
    missing = [str(p) for p in image_paths if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing figures: " + ", ".join(missing))
    copy_template_with_new_body(image_paths)


if __name__ == "__main__":
    main()
