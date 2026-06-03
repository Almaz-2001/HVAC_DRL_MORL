"""Assemble the Q1 main-paper results from Block 1/2/3 artifacts.

The script keeps the main paper compact:
- removes existing main-body figures/tables/captions from hvac_paper_final_q1.docx
- replaces Results I/II/III with paper-ready summaries sourced from the
  block1/2/3 complete-results documents and project CSV artifacts
- inserts only the agreed high-impact main figures/tables

Detailed block-level figures/tables remain in supplementary_material.docx.
"""

from __future__ import annotations

import importlib.util
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from lxml import etree as LET


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "docs" / "hvac_paper_final_q1.docx"
BACKUP = ROOT / "docs" / "hvac_paper_final_q1_before_block_results_assembly.docx"
FIG_DIR = ROOT / "reports" / "figures" / "article_real"

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

for prefix, uri in NS.items():
    if prefix != "rel":
        ET.register_namespace(prefix, uri)


def load_builder():
    path = ROOT / "docs" / "build_hvac_paper_docx.py"
    spec = importlib.util.spec_from_file_location("paper_builder", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def para_text(el: LET._Element) -> str:
    return "".join(t.text or "" for t in el.findall(".//w:t", NS)).strip()


def has_drawing(el: LET._Element) -> bool:
    return el.find(".//w:drawing", NS) is not None


def is_caption_paragraph(el: LET._Element) -> bool:
    text = para_text(el)
    return text.startswith("Figure ") or text.startswith("Table ")


def parse_fragments(xml: str) -> list[LET._Element]:
    wrapper = (
        f'<root xmlns:w="{NS["w"]}" xmlns:r="{NS["r"]}" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f"{xml}</root>"
    )
    return list(LET.fromstring(wrapper.encode("utf-8")))


def find_paragraph_index(children: list[LET._Element], startswith: str) -> int:
    for i, child in enumerate(children):
        if child.tag == f"{{{NS['w']}}}p" and para_text(child).startswith(startswith):
            return i
    raise ValueError(f"Heading not found: {startswith}")


def replace_section(body: LET._Element, start_heading: str, end_heading: str, xml: str) -> None:
    children = list(body)
    start = find_paragraph_index(children, start_heading)
    end = find_paragraph_index(children, end_heading)
    for child in children[start + 1 : end]:
        body.remove(child)
    for offset, el in enumerate(parse_fragments(xml), start=1):
        body.insert(start + offset, el)


def insert_after(body: LET._Element, anchor: str, xml: str) -> None:
    children = list(body)
    idx = None
    for i, child in enumerate(children):
        if child.tag == f"{{{NS['w']}}}p" and para_text(child).startswith(anchor):
            idx = i
            break
    if idx is None:
        raise ValueError(f"Anchor not found: {anchor}")
    for offset, el in enumerate(parse_fragments(xml), start=1):
        body.insert(idx + offset, el)


def build_shared_insertions(rids: dict[str, str]) -> tuple[str, str, str]:
    b = load_builder()

    def fig(filename: str, name: str, caption_text: str, width: float, height: float) -> str:
        return b.image_xml(rids[filename], name, width, height) + b.caption(caption_text)

    table1 = b.table_xml(
        [
            ["Reference", "Domain", "Method", "Training env.", "Model type", "Objective", "Key limitation", "How this paper differs"],
            ["Hou & Evins [17]", "Surrogate validation", "Reporting protocol", "Offline traces", "NN surrogate", "Predictive validity", "No RL utility test", "Extends protocol to closed-loop RL and transfer."],
            ["Gao et al. [18]", "HVAC DRL", "Predictive information", "Simulation", "GRU predictor", "Comfort-energy", "Predictive signal assumed useful", "Shows predictive fidelity can hurt as rollout backend."],
            ["Wang et al. [19]", "Safe DRL", "MPC filter", "Control loop", "Safety filter", "Safe actions", "Hard safety layer", "Tests soft physical regularization."],
            ["Liao et al. [21]", "HDRL HVAC", "Hierarchical RL", "Simulation", "Controller hierarchy", "Comfort/energy", "No surrogate-role audit", "Tests controller-family specificity."],
            ["Coraci et al. [23]", "Transfer", "Online transfer", "Target adaptation", "Controller adaptation", "Deployment", "Allows policy adaptation", "Separates surrogate transfer from frozen-controller transfer."],
            ["Offline RL survey [27]", "RL methodology", "Distribution shift", "Offline data", "Policy/data support", "OOD robustness", "Generic RL", "Shows surrogate-induced shift in HVAC control."],
        ],
        [1000, 1050, 1100, 1150, 1050, 1050, 1300, 2660],
        10,
    ) + b.caption("Table 1. Literature positioning and research gap. Detailed literature notes are reported in the supplementary material.")

    table2 = b.table_xml(
        [
            ["Surrogate/backend", "Architecture", "Input dim", "Output", "Physical structure", "Parameters", "Training corpus", "Calibration", "Role in RL"],
            ["v3", "Compact dual-head MLP", "8", "dT, HVAC power", "No explicit physics", "8,482", "hourly + matched 15-min check", "Supervised", "Primary rollout environment"],
            ["raw v3.5", "RC-NeuralODE + residual heads", "15-min prepared", "T_next, power", "C_zon backbone", "~50k", "10,744 rows", "None", "Architecture-only negative baseline"],
            ["calibrated v3.5", "RC-NeuralODE + residual heads", "15-min prepared", "T_next, power", "identified C_zon", "~50k", "10,744 rows", "Stage A/B/C", "Predictive twin and frozen teacher"],
            ["hybrid", "v3 rollout + frozen v3.5 teacher", "policy obs", "rollout + disagreement", "soft physical regularizer", "v3 + v3.5", "same source corpus", "lambda weights", "Canonical thermostatic backend"],
        ],
        [1150, 1350, 650, 950, 1200, 800, 1300, 950, 2010],
        10,
    ) + b.caption("Table 2. Surrogate architectures and calibration summary.")

    table4 = b.table_xml(
        [
            ["Component", "Definition used in main experiments", "Why it matters"],
            ["Observation", "17D TSup-style state: physical variables, cyclic time, ambient forecast, previous action/history", "MORL 5D failed; 17D recovers usable preference-conditioned control."],
            ["Action", "Continuous normalized action mapped to supply-temperature command 18-35 C plus fan/intensity channel", "Keeps controller compatible with bestest_air source testcase."],
            ["Reward", "Comfort + energy + smoothness; MORL scalarizes comfort/energy/safety weights", "Separates thermostatic, HDRL, and MORL objectives."],
            ["Thermostatic PPO", "PPO final-policy live BOPTEST evaluation; lambda_temp sweep", "Primary positive hybrid result."],
            ["HDRL", "Hierarchical PPO variant; lambda_temp sweep", "Tests controller-family specificity."],
            ["MORL", "Preference-conditioned pretrain/finetune; canonical N=5 seeds", "Tests Pareto trade-offs and seed variance."],
        ],
        [1550, 4550, 3260],
        11,
    ) + b.caption("Table 4. Controller training configuration, observation/action interface, and reward definition.")

    methodology_insert = fig(
        "block1_q1_fig01_pipeline.png",
        "overall_pipeline",
        "Figure 1. Overall experimental pipeline. Block 1 separates predictive fidelity from RL utility; Block 2 tests controller-family behaviour; Block 3 tests transferability under pre-registered hydronic target regimes.",
        6.4,
        2.9,
    ) + table2 + table4

    return table1, methodology_insert, ""


def build_results_sections(rids: dict[str, str]) -> dict[str, str]:
    b = load_builder()
    nums = b.paper_numbers()
    tables = b.main_key_tables()

    def fig(filename: str, name: str, caption_text: str, width: float, height: float) -> str:
        return b.image_xml(rids[filename], name, width, height) + b.caption(caption_text)

    table3 = b.table_xml(
        [
            ["Metric / variant", "Raw or baseline", "Calibrated / matched", "Absolute change", "Relative / interpretation"],
            ["1-step RMSE_T", "0.384 C", "0.235 C", "-0.149 C", "-38.9% after Stage A/B/C"],
            ["24h rollout RMSE_T", "1.466 C raw v3.5", "0.644 C calibrated v3.5", "-0.822 C", "-56.1% within v3.5 family"],
            ["Power MAE", "810 W", "482 W", "-328 W", "-40.5% after power-head refinement"],
            ["C_zon", "4.200e5 J/K prior", "4.413e5 J/K", "+2.13e4 J/K", "+5.1%; physically plausible update"],
            ["v3 hourly", "1.557 C", "0.876 C v3 15-min", "-0.681 C", "74.6% of v3-to-v3.5 gap is corpus shift"],
            ["v3 15-min to v3.5", "0.876 C", "0.644 C", "-0.232 C", "25.4% of gap is Stage A/B/C calibration"],
        ],
        [1700, 1800, 1800, 1400, 2660],
        11,
    ) + b.caption("Table 3. Block 1 calibration and matched-corpus metrics. Full per-episode and residual diagnostics are in the supplementary material.")

    table5 = b.table_xml(
        [
            ["Family / policy", "Best backend or variant", "Primary result", "m_s / variance", "Verdict"],
            ["Thermostatic PPO", "hybrid_l010", f"Peak/typical RMSE {nums['hybrid_peak_rmse']} / {nums['hybrid_typical_rmse']} C", f"m_s {nums['hybrid_peak_ms']} / {nums['hybrid_typical_ms']}", "Hybrid regularization supported"],
            ["Direct v3.5 PPO", "standalone calibrated v3.5", f"Live RMSE {nums['v35_peak_live']} / {nums['v35_typical_live']} C", "m_s > 1.0", "Negative control"],
            ["HDRL", "lambda_temp=0", "Temperature regularizer hurts hierarchy", "best at lambda=0", "Controller-family specificity"],
            ["MORL 17D", "power-only hybrid", "Pareto sweep usable after 17D interface", "canonical N=5 high variance", "Promising but not stable"],
            ["MORL N=5 test", "neutral/practical canonicals", "Replay deterministic; action-saturation hypothesis falsified", "sigma/mean > threshold", "Report with limitations"],
        ],
        [1500, 1650, 3050, 1550, 1610],
        11,
    ) + b.caption("Table 5. Block 2 controller-family and MORL summary. Detailed lambda sweeps, per-seed tables and monthly diagnostics are in the supplementary material.")

    table6 = b.table_xml(tables["transfer"], [1500, 550, 550, 650, 650, 850, 850, 850, 2960], 10) + b.caption(
        "Table 6. Block 3 transfer matrix, combining adapters, controller verdicts, surrogate gains, and C_zon re-identification."
    )

    table7 = b.table_xml(
        [
            ["Hypothesis", "Pre-registered claim", "Operational criterion", "Verdict", "Evidence"],
            ["H1 strong", "Frozen recipe transfers directly", "mode=none PASS on >=2/3 without severe KPI penalty", "Falsified", "Residential hydronic cases fail; commercial passes m_s but +35.3% energy."],
            ["H2 medium", "Partial surrogate recalibration is sufficient", "Stage C only improves controller verdict", "Falsified structurally", "Controller frozen, so live KPI cannot change from none."],
            ["H3 weak surrogate side", "Full recalibration gives useful target twin", "RMSE_T improves under full Stage A/B/C", "Supported", "60.2-87.8% RMSE_T improvement across N=3."],
            ["H3 weak controller side", "Full surrogate recalibration rescues frozen controller", "Controller PASS after full", "Falsified/split", "Surrogate succeeds, controller remains regime-dependent."],
            ["MORL action-saturation", "N=3 seasonal inversion persists at N=5", "Feb sigma <0.005 and winter ratio >20x", "Falsified", "Feb sigma rose and inversion collapsed at N=5."],
        ],
        [1250, 2400, 2200, 1250, 2260],
        10,
    ) + b.caption("Table 7. Hypothesis closure table. The audit trail maps each claim to the pre-registered protocol and post-result append-only records.")

    results1 = "".join(
        [
            b.p("5.1 Block 1 objective and evidence boundary", "Heading2"),
            b.p("Block 1 asks whether a higher-fidelity digital twin is also a better reinforcement-learning training environment. The answer is deliberately split. The physically informed v3.5 twin is the stronger predictor after Stage A/B/C inverse calibration, but direct PPO training on that twin is not the strongest live controller. This distinction is the first central result of the paper: predictive validity and RL utility are related but not interchangeable properties."),
            b.p("The control-oriented v3 surrogate is a compact dual-head model with separate temperature-increment and HVAC-power heads. Its purpose is not to be the most accurate 24-hour predictor; its purpose is to provide smooth, fast rollout dynamics for policy optimization. The calibrated v3.5 model, by contrast, is a physically informed RC-NeuralODE twin whose Stage B parameter is explicitly interpretable as the zone capacitance C_zon."),
            fig("main_fig2_stage_abc_czon.png", "stage_abc_czon", "Figure 2. Stage A/B/C inverse calibration and C_zon identification. Stage A aligns telemetry, Stage B identifies C_zon = 4.413e5 J/K, and Stage C refines residual temperature and power heads.", 6.4, 2.75),
            b.p("5.2 Stage A/B/C calibration result", "Heading2"),
            b.p("The calibrated v3.5 twin improves one-step and recursive temperature prediction while retaining physical interpretability. Stage B moves the capacitance from the 4.200e5 J/K prior to 4.413e5 J/K, a +5.1% update that is large enough to show data-driven identification but small enough to remain physically plausible. Stage C then reduces the temperature residual and the power-head error without moving the identified capacitance."),
            table3,
            b.p("5.3 Matched-corpus decomposition", "Heading2"),
            b.p("A direct v3-versus-v3.5 comparison would be misleading because the active v3.5 pipeline uses a 15-minute corpus while the legacy v3 benchmark was originally trained on an hourly workflow. The matched-corpus check resolves this confound. Most of the v3-to-v3.5 24-hour RMSE gain is explained by the data-resolution shift, while the remaining gain is attributable to Stage A/B/C calibration. This is reported as a reviewer-facing mitigation rather than hidden in the supplement."),
            fig("main_fig3_matched_corpus_decomposition.png", "matched_decomposition", "Figure 3. Corpus-controlled decomposition of the v3-to-v3.5 predictive-fidelity gain. The 15-minute corpus explains the larger share of the gain; Stage A/B/C calibration supplies the remaining physically interpretable improvement.", 6.4, 2.75),
            b.p("5.4 Fidelity-to-control gap", "Heading2"),
            b.p("The closed-loop result is the critical negative finding. Calibrated v3.5 is the most accurate predictive model, but a PPO controller trained directly on it produces poor live BOPTEST performance. The live failure is not a simulator artifact: replay audits confirmed deterministic BOPTEST responses, and transfer diagnostics show that the direct-v3.5 policy enters action regimes that do not survive the live RTE. Therefore, the successful role for v3.5 is not as the direct rollout environment, but as a frozen physical teacher in the hybrid backend."),
        ]
    )

    results2 = "".join(
        [
            b.p("6.1 Block 2 objective and controller families", "Heading2"),
            b.p("Block 2 tests whether the Block 1 surrogate-role separation translates into better closed-loop control. The experiments compare thermostatic PPO, HDRL and MORL under the same BOPTEST RTE evaluation discipline. The result is controller-family specific: the hybrid disagreement penalty helps the thermostatic PPO controller, hurts HDRL when copied naively, and yields promising but high-variance MORL behaviour."),
            fig("main_fig4_fidelity_control.png", "fidelity_control", "Figure 4. Predictive fidelity does not imply RL training utility. The calibrated v3.5 model improves predictive RMSE but direct PPO on v3.5 fails live control; the hybrid backend reconciles v3 rollout smoothness with v3.5 physical regularization.", 6.4, 2.75),
            b.p("6.2 Thermostatic PPO and HDRL", "Heading2"),
            b.p("For thermostatic PPO, the canonical hybrid setting lambda_temp = 0.10 is the main positive controller result. It improves the typical-window safety metric and maintains energy efficiency while avoiding the direct-v3.5 failure mode. HDRL reverses this conclusion: the same temperature disagreement penalty degrades performance, and lambda_temp = 0 is the best HDRL setting. This prevents the paper from claiming that physics-informed penalties are universally beneficial; they are backend- and controller-family-specific."),
            b.p("6.3 MORL, observation interface and seed variance", "Heading2"),
            b.p("MORL initially failed under a compact 5D observation interface. Expanding to the 17D TSup-style observation recovers a usable preference-conditioned controller, showing that the observation geometry is not an implementation detail but a primary determinant of success. The Pareto sweep then identifies neutral and practical canonical weight vectors, but the N=5 seed extension changes the scientific interpretation: aggregate high variance persists, the N=3 seasonal-inversion hypothesis is falsified, and MORL must be reported as promising but not deployment-stable without additional stabilization."),
            fig("main_fig5_morl_pareto_variance.png", "morl_summary", "Figure 5. MORL Pareto structure and seed-variance diagnostics. Non-canonical points are seed42-only; the two canonical points use N=5 summaries and show that preference-conditioned MORL remains high-variance.", 6.7, 2.65),
            table5,
            b.p("6.4 Seasonal variance heatmap interpretation", "Heading2"),
            b.p("The seasonal variance heatmap is retained as a falsification artifact, not as support for the original action-saturation mechanism. At N=3 the practical canonical appeared winter-stable and summer-unstable, motivating a pre-registered N=5 test. Seeds 45/46 falsified that mechanism: February variance increased sharply and the winter neutral/practical ratio collapsed. This is a methodologically useful result because it shows that mechanism-level interpretations from small-seed MORL seasonal patterns can be transient."),
        ]
    )

    results3 = "".join(
        [
            b.p("7.1 Block 3 objective and transfer protocol", "Heading2"),
            b.p("Block 3 evaluates whether the bestest_air recipe transfers to related hydronic BOPTEST testcases. Because the target actuators are not literal direct supply-temperature actuators, transfer is adapter-mediated and pre-registered before control runs. The tested regimes separate controller transfer from surrogate recalibration: mode=none deploys the frozen controller through the documented adapter, while mode=full re-runs Stage A/B/C on target telemetry but still keeps the controller frozen."),
            fig("main_fig5_block3_transfer_verdict_heatmap.png", "block3_transfer_heatmap", "Figure 6. Block 3 transferability matrix. Controller transfer is regime-dependent: residential hydronic cases fail comfort, while the commercial case passes the scalar threshold but with a large energy penalty.", 6.0, 2.35),
            b.p("7.2 Controller-side transfer", "Heading2"),
            b.p("Controller transfer is not deployment-ready under the frozen-controller scope. The two residential hydronic testcases fail the pre-registered m_s threshold, primarily through comfort degradation. The commercial hydronic testcase passes the scalar m_s threshold, but only with a +35.3% energy penalty relative to PI. This distinction matters: the commercial cell is a threshold PASS but not a deployment PASS under a two-axis comfort-energy interpretation."),
            b.p("7.3 Surrogate-side transfer", "Heading2"),
            b.p("The surrogate component transfers much more cleanly than the controller component. Full Stage A/B/C recalibration improves target-testcase RMSE_T by 60.2-87.8% across the three hydronic testcases. Even more importantly, the identified hydronic C_zon ratios cluster tightly around 1.9x the bestest_air value. This consistency is physical evidence that the inverse calibration pipeline recovers a stable family-level thermal-mass relationship rather than overfitting a single testcase."),
            fig("main_fig6_block3_czon_consistency.png", "block3_czon", "Figure 7. C_zon consistency across hydronic testcases. Full Stage A/B/C recalibration re-identifies the hydronic-family thermal capacitance at approximately 1.9x the bestest_air canonical value across N=3 target cases.", 5.8, 2.65),
            table6,
            b.p("7.4 Component-level transferability conclusion", "Heading2"),
            b.p("The Block 3 conclusion is therefore component-level rather than binary. The surrogate physics representation is transferable under full recalibration. The frozen controller is not robustly transferable through actuator adapters. The transferability boundary lies at the controller-adapter interface, and the natural next experiment is controller fine-tuning on the target-recalibrated surrogate. That experiment is explicitly outside the pre-registered scope of this paper."),
        ]
    )

    discussion_insert = fig(
        "main_fig8_audit_timeline.png",
        "audit_timeline",
        "Figure 8. Audit and pre-registration timeline. The MORL N=5 falsification and Block 3 transfer tests were committed before the corresponding result append commits.",
        6.4,
        2.0,
    ) + table7

    return {
        "5. Results I: Digital Twin Fidelity": results1,
        "6. Results II: Control Performance": results2,
        "7. Results III: Transferability": results3,
        "8. Discussion": discussion_insert,
    }


def main() -> None:
    if not DOCX.exists():
        raise FileNotFoundError(DOCX)
    if not BACKUP.exists():
        shutil.copy2(DOCX, BACKUP)

    image_names = [
        "block1_q1_fig01_pipeline.png",
        "main_fig2_stage_abc_czon.png",
        "main_fig3_matched_corpus_decomposition.png",
        "main_fig4_fidelity_control.png",
        "main_fig5_morl_pareto_variance.png",
        "main_fig5_block3_transfer_verdict_heatmap.png",
        "main_fig6_block3_czon_consistency.png",
        "main_fig8_audit_timeline.png",
    ]
    image_paths = [FIG_DIR / name for name in image_names]
    missing = [str(p) for p in image_paths if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing figures: " + ", ".join(missing))

    with zipfile.ZipFile(DOCX, "r") as zin:
        document_xml = zin.read("word/document.xml").decode("utf-8")
        rels_xml = zin.read("word/_rels/document.xml.rels").decode("utf-8")

        parser = LET.XMLParser(recover=True, huge_tree=True)
        doc_root = LET.fromstring(document_xml.encode("utf-8"), parser=parser)
        body = doc_root.find("w:body", NS)
        assert body is not None

        # Remove old/duplicated main-body figures, tables, and captions. Detailed
        # versions remain in supplementary_material.docx.
        for child in list(body):
            if child.tag == f"{{{NS['w']}}}tbl":
                body.remove(child)
            elif child.tag == f"{{{NS['w']}}}p" and (has_drawing(child) or is_caption_paragraph(child)):
                body.remove(child)

        rel_root = ET.fromstring(rels_xml)
        for rel in list(rel_root):
            typ = rel.attrib.get("Type", "")
            target = rel.attrib.get("Target", "")
            if typ.endswith("/image") or target.startswith("media/"):
                rel_root.remove(rel)

        rids: dict[str, str] = {}
        for i, name in enumerate(image_names, start=1100):
            rid = f"rId{i}"
            ET.SubElement(
                rel_root,
                "Relationship",
                {
                    "Id": rid,
                    "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
                    "Target": f"media/{name}",
                },
            )
            rids[name] = rid

        table1, methodology_insert, _ = build_shared_insertions(rids)
        insert_after(body, "2. Related Work", table1)
        insert_after(body, "3. Methodology", methodology_insert)

        sections = build_results_sections(rids)
        replace_section(body, "5. Results I: Digital Twin Fidelity", "6. Results II: Control Performance", sections["5. Results I: Digital Twin Fidelity"])
        replace_section(body, "6. Results II: Control Performance", "7. Results III: Transferability", sections["6. Results II: Control Performance"])
        replace_section(body, "7. Results III: Transferability", "8. Discussion", sections["7. Results III: Transferability"])
        insert_after(body, "8. Discussion", sections["8. Discussion"])

        new_doc_xml = LET.tostring(doc_root, encoding="utf-8", xml_declaration=True)
        new_rels_xml = ET.tostring(rel_root, encoding="utf-8", xml_declaration=True)

        tmp = DOCX.with_suffix(".tmp.docx")
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                elif item.filename == "word/_rels/document.xml.rels":
                    zout.writestr(item, new_rels_xml)
                elif item.filename.startswith("word/media/"):
                    continue
                else:
                    zout.writestr(item, zin.read(item.filename))
            for path in image_paths:
                zout.write(path, f"word/media/{path.name}")

    tmp.replace(DOCX)
    print(f"Assembled final Q1 paper results: {DOCX}")


if __name__ == "__main__":
    main()
