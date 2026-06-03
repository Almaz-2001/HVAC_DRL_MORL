"""Apply compact main-paper visual/table policy without deleting prose.

This script operates directly on the existing full DOCX:
- removes existing figure drawings, figure captions, tables, and table captions
- inserts the agreed 8 main figures and 7 consolidated main tables
- keeps all ordinary paragraphs, sections, literature, discussion, and references
"""

from __future__ import annotations

import importlib.util
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from lxml import etree as LET


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "docs" / "hvac_paper_skeleton_q1_restructured_patched.docx"
PRE_POLICY_BACKUP = ROOT / "docs" / "hvac_paper_skeleton_q1_restructured_patched_FULL_TEXT_before_visual_policy.docx"
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


def para_text(el: ET.Element) -> str:
    return "".join(t.text or "" for t in el.findall(".//w:t", NS))


def has_drawing(el: ET.Element) -> bool:
    return el.find(".//w:drawing", NS) is not None


def is_caption_paragraph(el: ET.Element) -> bool:
    text = para_text(el).strip()
    return text.startswith("Figure ") or text.startswith("Table ")


def parse_fragments(xml: str) -> list[LET._Element]:
    wrapper = (
        f'<root xmlns:w="{NS["w"]}" xmlns:r="{NS["r"]}" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f"{xml}</root>"
    )
    root = LET.fromstring(wrapper.encode("utf-8"))
    return list(root)


def insert_after(body: LET._Element, anchor: str, xml: str) -> None:
    children = list(body)
    idx = None
    for i, child in enumerate(children):
        if anchor in para_text(child):
            idx = i
            break
    if idx is None:
        idx = len(children) - 1
    for offset, el in enumerate(parse_fragments(xml), start=1):
        body.insert(idx + offset, el)


def build_insertions(rids: dict[str, str]) -> dict[str, str]:
    b = load_builder()
    nums = b.paper_numbers()
    tables = b.main_key_tables()

    def fig(filename: str, name: str, caption_text: str, width: float, height: float) -> str:
        return b.image_xml(rids[filename], name, width, height) + b.caption(caption_text)

    table1 = b.table_xml([
        ["Reference", "Domain", "Method", "Training env.", "Model type", "Objective", "Key limitation", "How this paper differs"],
        ["Hou & Evins [17]", "Surrogate validation", "Reporting protocol", "Offline traces", "NN surrogate", "Predictive validity", "No RL utility test", "Extends protocol to closed-loop RL and transfer."],
        ["Gao et al. [18]", "HVAC DRL", "Predictive information", "Simulation", "GRU predictor", "Comfort-energy", "Predictive signal assumed useful", "Shows predictive fidelity can hurt as rollout backend."],
        ["Wang et al. [19]", "Safe DRL", "MPC filter", "Control loop", "Safety filter", "Safe actions", "Hard safety layer", "Tests soft physical regularization."],
        ["Liao et al. [21]", "HDRL HVAC", "Hierarchical RL", "Simulation", "Controller hierarchy", "Comfort/energy", "No surrogate-role audit", "Tests controller-family specificity."],
        ["Coraci et al. [23]", "Transfer", "Online transfer", "Target adaptation", "Controller adaptation", "Deployment", "Allows policy adaptation", "Separates surrogate transfer from frozen-controller transfer."],
        ["Offline RL survey [27]", "RL methodology", "Distribution shift", "Offline data", "Policy/data support", "OOD robustness", "Generic RL", "Shows surrogate-induced shift in HVAC control."],
    ], [1000, 1050, 1100, 1150, 1050, 1050, 1300, 2660], 10) + b.caption("Table 1. Literature positioning and research gap.")

    table2 = b.table_xml([
        ["Surrogate/backend", "Architecture", "Input dim", "Output", "Physical structure", "Parameters", "Training corpus", "Calibration", "Role in RL"],
        ["v3", "Compact dual-head MLP", "8", "dT, HVAC power", "No explicit physics", "8,482", "hourly + matched 15-min check", "Supervised", "Primary rollout environment"],
        ["raw v3.5", "RC-NeuralODE + residual heads", "15-min prepared", "T_next, power", "C_zon backbone", "~50k", "10,744 rows", "None", "Architecture-only negative baseline"],
        ["calibrated v3.5", "RC-NeuralODE + residual heads", "15-min prepared", "T_next, power", "identified C_zon", "~50k", "10,744 rows", "Stage A/B/C", "Predictive twin and frozen teacher"],
        ["hybrid", "v3 rollout + frozen v3.5 teacher", "policy obs", "rollout + disagreement", "soft physical regularizer", "v3 + v3.5", "same source corpus", "lambda weights", "Canonical thermostatic backend"],
    ], [1150, 1350, 650, 950, 1200, 800, 1300, 950, 2010], 10) + b.caption("Table 2. Surrogate architectures and calibration summary.")

    table3 = b.table_xml([
        ["Metric / variant", "Raw or baseline", "Calibrated / matched", "Absolute change", "Relative / interpretation"],
        ["1-step RMSE_T", "0.384 C", "0.235 C", "-0.149 C", "-38.9% after Stage A/B/C"],
        ["24h rollout RMSE_T", "1.466 C raw v3.5", "0.644 C calibrated v3.5", "-0.822 C", "-56.1% within v3.5 family"],
        ["Power MAE", "810 W", "482 W", "-328 W", "-40.5% after power-head refinement"],
        ["C_zon", "4.200e5 J/K prior", "4.413e5 J/K", "+2.13e4 J/K", "+5.1%; physically plausible update"],
        ["v3 hourly", "1.557 C", "0.876 C v3 15-min", "-0.681 C", "74.6% of v3-to-v3.5 gap is corpus shift"],
        ["v3 15-min to v3.5", "0.876 C", "0.644 C", "-0.232 C", "25.4% of gap is Stage A/B/C calibration"],
    ], [1700, 1800, 1800, 1400, 2660], 11) + b.caption("Table 3. Stage A/B/C and matched-corpus calibration metrics.")

    table4 = b.table_xml([
        ["Component", "Definition used in main experiments", "Why it matters"],
        ["Observation", "17D TSup-style state: physical variables, cyclic time, ambient forecast, previous action/history", "MORL 5D failed; 17D recovers usable preference-conditioned control."],
        ["Action", "Continuous normalized action mapped to supply-temperature command 18-35 C plus fan/intensity channel", "Keeps controller compatible with bestest_air source testcase."],
        ["Reward", "Comfort + energy + smoothness; MORL scalarizes comfort/energy/safety weights", "Separates thermostatic, HDRL, and MORL objectives."],
        ["Thermostatic PPO", "PPO, final-policy live BOPTEST evaluation, lambda_temp sweep", "Primary positive hybrid result."],
        ["HDRL", "Hierarchical PPO variant, lambda_temp sweep", "Tests controller-family specificity."],
        ["MORL", "Preference-conditioned pretrain/finetune; canonical N=5 seeds", "Tests Pareto trade-offs and seed variance."],
    ], [1550, 4550, 3260], 11) + b.caption("Table 4. Controller training configuration, observation/action interface, and reward definition.")

    table5 = b.table_xml([
        ["Family / policy", "Best backend or variant", "Primary result", "m_s / variance", "Verdict"],
        ["Thermostatic PPO", "hybrid_l010", f"Peak/typical RMSE {nums['hybrid_peak_rmse']} / {nums['hybrid_typical_rmse']} C", f"m_s {nums['hybrid_peak_ms']} / {nums['hybrid_typical_ms']}", "Hybrid regularization supported"],
        ["Direct v3.5 PPO", "standalone calibrated v3.5", f"Live RMSE {nums['v35_peak_live']} / {nums['v35_typical_live']} C", "m_s > 1.0", "Negative control"],
        ["HDRL", "lambda_temp=0", "Temperature regularizer hurts hierarchy", "best at lambda=0", "Controller-family specificity"],
        ["MORL 17D", "power-only hybrid", "Pareto sweep usable after 17D interface", "canonical N=5 high variance", "Promising but not stable"],
        ["MORL N=5 test", "neutral/practical canonicals", "Replay deterministic; action-saturation hypothesis falsified", "sigma/mean > threshold", "Report with limitations"],
    ], [1500, 1650, 3050, 1550, 1610], 11) + b.caption("Table 5. Block 2 main controller and MORL summary.")

    table6 = b.table_xml(tables["transfer"], [1500, 550, 550, 650, 650, 850, 850, 850, 2960], 10) + b.caption("Table 6. Block 3 transfer matrix, combining adapters, controller verdicts, surrogate gains, and C_zon re-identification.")

    table7 = b.table_xml([
        ["Hypothesis", "Pre-registered claim", "Operational criterion", "Verdict", "Evidence"],
        ["H1 strong", "Frozen recipe transfers directly", "mode=none PASS on >=2/3 without severe KPI penalty", "Falsified", "Residential hydronic cases fail; commercial passes m_s but +35.3% energy."],
        ["H2 medium", "Partial surrogate recalibration is sufficient", "Stage C only improves controller verdict", "Falsified structurally", "Controller frozen, so live KPI cannot change from none."],
        ["H3 weak surrogate side", "Full recalibration gives useful target twin", "RMSE_T improves under full Stage A/B/C", "Supported", "60.2-87.8% RMSE_T improvement across N=3."],
        ["H3 weak controller side", "Full surrogate recalibration rescues frozen controller", "Controller PASS after full", "Falsified/split", "Surrogate succeeds, controller remains regime-dependent."],
        ["MORL action-saturation", "N=3 seasonal inversion persists at N=5", "Feb sigma <0.005 and winter ratio >20x", "Falsified", "Feb sigma rose and inversion collapsed at N=5."],
    ], [1250, 2400, 2200, 1250, 2260], 10) + b.caption("Table 7. Hypothesis closure table.")

    return {
        "2. Related Work": table1,
        "3. Methodology": fig("block1_q1_fig01_pipeline.png", "overall_pipeline", "Figure 1. Overall experimental pipeline.", 6.4, 2.9) + table2 + table4,
        "5. Results I": fig("main_fig2_stage_abc_czon.png", "stage_abc_czon", "Figure 2. Stage A/B/C calibration and C_zon identification.", 6.4, 2.75) + fig("main_fig3_matched_corpus_decomposition.png", "matched_decomposition", "Figure 3. Matched-corpus decomposition of predictive-fidelity gain.", 6.4, 2.75) + table3,
        "6. Results II": fig("main_fig4_fidelity_control.png", "fidelity_control", "Figure 4. Predictive fidelity does not imply RL training utility.", 6.4, 2.75) + fig("main_fig5_morl_pareto_variance.png", "morl_summary", "Figure 5. MORL Pareto structure and seed-variance diagnostics.", 6.7, 2.65) + table5,
        "7. Results III": fig("main_fig5_block3_transfer_verdict_heatmap.png", "block3_transfer_heatmap", "Figure 6. Block 3 transferability matrix.", 6.0, 2.35) + fig("main_fig6_block3_czon_consistency.png", "block3_czon", "Figure 7. C_zon consistency across hydronic testcases.", 5.8, 2.65) + table6,
        "8. Discussion": fig("main_fig8_audit_timeline.png", "audit_timeline", "Figure 8. Audit/pre-registration timeline.", 6.4, 2.0) + table7,
    }


def main() -> None:
    if not PRE_POLICY_BACKUP.exists():
        shutil.copyfile(DOCX, PRE_POLICY_BACKUP)

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
    image_paths = [FIG_DIR / n for n in image_names]
    missing = [str(p) for p in image_paths if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing figures: " + ", ".join(missing))

    with zipfile.ZipFile(DOCX, "r") as zin:
        document_xml = zin.read("word/document.xml").decode("utf-8")
        rels_xml = zin.read("word/_rels/document.xml.rels").decode("utf-8")
        content_types = zin.read("[Content_Types].xml").decode("utf-8")

        parser = LET.XMLParser(recover=True, huge_tree=True)
        doc_root = LET.fromstring(document_xml.encode("utf-8"), parser=parser)
        body = doc_root.find("w:body", NS)
        assert body is not None

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
        for i, name in enumerate(image_names, start=1000):
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

        for anchor, xml in build_insertions(rids).items():
            insert_after(body, anchor, xml)

        new_doc_xml = LET.tostring(doc_root, encoding="utf-8", xml_declaration=True)
        new_rels_xml = ET.tostring(rel_root, encoding="utf-8", xml_declaration=True)

        with zipfile.ZipFile(DOCX.with_suffix(".tmp.docx"), "w", zipfile.ZIP_DEFLATED) as zout:
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

    tmp = DOCX.with_suffix(".tmp.docx")
    tmp.replace(DOCX)
    print(f"Applied visual policy to {DOCX}")


if __name__ == "__main__":
    main()
