"""Insert the 17 main-paper figures into hvac_paper_final_q1.docx.

This replaces only figure drawings and figure captions. It keeps the final
paper prose and the seven consolidated main tables intact.
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
BACKUP = ROOT / "docs" / "hvac_paper_final_q1_before_17_figures.docx"
FIG_DIR = ROOT / "reports" / "figures" / "article_real"

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


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


def is_figure_caption(el: LET._Element) -> bool:
    return para_text(el).startswith("Figure ")


def parse_fragments(xml: str) -> list[LET._Element]:
    wrapper = (
        f'<root xmlns:w="{NS["w"]}" xmlns:r="{NS["r"]}" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f"{xml}</root>"
    )
    return list(LET.fromstring(wrapper.encode("utf-8")))


def find_anchor(body: LET._Element, anchor: str) -> int:
    for i, child in enumerate(list(body)):
        if child.tag == f"{{{NS['w']}}}p" and para_text(child).startswith(anchor):
            return i
    raise ValueError(f"Anchor not found: {anchor}")


def insert_after(body: LET._Element, anchor: str, xml: str) -> None:
    idx = find_anchor(body, anchor)
    for offset, el in enumerate(parse_fragments(xml), start=1):
        body.insert(idx + offset, el)


FIGURES = [
    (
        "3. Methodology",
        "final17_fig01_overall_study_architecture.png",
        "final17_fig01",
        "Figure 1. Overall study architecture. The study starts from BOPTEST data, separates v3 and v3.5 surrogate roles, combines them in the hybrid backend, and validates the resulting recipe through Block 1 surrogate fidelity, Block 2 controller validation, and Block 3 transferability.",
        6.7,
        2.7,
    ),
    (
        "3.2 Surrogate roles",
        "final17_fig02_backend_architecture.png",
        "final17_fig02",
        "Figure 2. v3 / v3.5 / hybrid backend architecture. v3 is the smooth control-oriented dual-head rollout surrogate; v3.5 is the calibrated physics-informed twin; the hybrid backend uses v3 for rollout dynamics and frozen v3.5 for disagreement regularization.",
        6.7,
        2.9,
    ),
    (
        "5.2 Stage A/B/C calibration result",
        "final17_fig03_stage_abc_calibration_improvement.png",
        "final17_fig03",
        "Figure 3. Stage A/B/C calibration improvement. Raw v3.5 and calibrated v3.5 are compared on one-step temperature RMSE, 24h rollout temperature RMSE, and power MAE using project calibration artifacts.",
        6.2,
        2.9,
    ),
    (
        "5.3 Matched-corpus decomposition",
        "final17_fig04_matched_corpus_decomposition.png",
        "final17_fig04",
        "Figure 4. Matched-corpus predictive-fidelity decomposition. The v3 hourly, v3 15-min matched, raw v3.5, and calibrated v3.5 rows come from the matched-corpus CSV; the plot separates corpus contribution from Stage A/B/C contribution.",
        6.3,
        3.0,
    ),
    (
        "5.4 Fidelity-to-control gap",
        "final17_fig05_fidelity_vs_rl_utility.png",
        "final17_fig05",
        "Figure 5. Predictive fidelity vs RL training utility. The calibrated v3.5 twin is the strongest offline predictor but the weakest direct RL rollout backend, while the hybrid backend recovers live control utility.",
        5.8,
        3.4,
    ),
    (
        "6.2 Thermostatic PPO and HDRL",
        "final17_fig06_live_boptest_controller_comparison.png",
        "final17_fig06",
        "Figure 6. Live BOPTEST controller comparison. Pure v3 PPO, direct-v3.5 PPO, and hybrid_l010 PPO are compared on m_s, violation percentage, RMSE_T, and energy for peak and typical heat windows.",
        6.7,
        4.2,
    ),
    (
        "6.2 Thermostatic PPO and HDRL",
        "final17_fig07_hybrid_reward_shaping_mechanism.png",
        "final17_fig07",
        "Figure 7. Hybrid reward-shaping mechanism. The policy rolls out through v3 dynamics, while the same state-action pair is evaluated by frozen v3.5 to produce temperature and power disagreement penalties.",
        6.7,
        2.8,
    ),
    (
        "6.2 Thermostatic PPO and HDRL",
        "final17_fig08_hdrl_lambda_temp_sweep.png",
        "final17_fig08",
        "Figure 8. HDRL lambda_temp sweep. HDRL achieves its best result at lambda_temp = 0.00; the thermostatic-optimal value lambda_temp = 0.10 over-regularizes the hierarchy.",
        6.7,
        2.5,
    ),
    (
        "6.3 MORL, observation interface",
        "final17_fig09_morl_5d_failure_17d_success.png",
        "final17_fig09",
        "Figure 9. MORL 5D failure to 17D success. The compact 5D observation interface collapses, whereas the 17D TSup-style interface recovers a usable MORL controller.",
        6.7,
        2.4,
    ),
    (
        "6.3 MORL, observation interface",
        "final17_fig10_morl_comfort_energy_pareto.png",
        "final17_fig10",
        "Figure 10. MORL comfort-energy Pareto front. Energy-only scalarization collapses, comfort-only achieves the lowest m_s, and the practical 75/25 canonical is a compromise but remains seed-sensitive.",
        5.8,
        3.5,
    ),
    (
        "7.1 Block 3 objective",
        "final17_fig11_block3_transferability_protocol.png",
        "final17_fig11",
        "Figure 11. Block 3 transferability protocol. Frozen Block 2 controllers are evaluated on three target BOPTEST testcases under none, partial, and full recalibration regimes with a pre-registered m_s_RL <= 1.25 x m_s_PI criterion.",
        6.7,
        2.8,
    ),
    (
        "7.1 Block 3 objective",
        "final17_fig12_target_testcase_ladder_adapters.png",
        "final17_fig12",
        "Figure 12. Target testcase ladder and actuator adapters. Transfer to hydronic-family testcases is adapter-mediated because target actuator interfaces differ from the bestest_air direct supply-temperature interface.",
        6.7,
        2.8,
    ),
    (
        "7.2 Controller-side transfer",
        "final17_fig13_block3_controller_transfer_heatmap.png",
        "final17_fig13",
        "Figure 13. Block 3 controller transfer verdict heatmap. Residential hydronic target cases fail the frozen-controller threshold, while the commercial target is a threshold pass but remains deployment-limited by energy penalty.",
        5.8,
        3.2,
    ),
    (
        "7.2 Controller-side transfer",
        "final17_fig14_rl_vs_pi_threshold_energy_penalty.png",
        "final17_fig14",
        "Figure 14. RL vs PI threshold and energy penalty. The commercial case passes the scalar m_s threshold but consumes substantially more energy than PI, motivating the paper's distinction between threshold pass and deployment pass.",
        6.7,
        3.1,
    ),
    (
        "7.3 Surrogate-side transfer",
        "final17_fig15_full_stage_transfer_rmse_improvement.png",
        "final17_fig15",
        "Figure 15. Full Stage A/B/C transfer RMSE improvement. Full target recalibration improves surrogate RMSE_T on all three hydronic-family testcases.",
        5.8,
        3.2,
    ),
    (
        "7.3 Surrogate-side transfer",
        "final17_fig16_hydronic_czon_consistency.png",
        "final17_fig16",
        "Figure 16. Hydronic-family C_zon consistency. Full Stage A/B/C re-identifies the hydronic-family capacitance at approximately 1.92 x the bestest_air value across N=3 target cases.",
        5.8,
        3.2,
    ),
    (
        "8. Discussion",
        "final17_fig17_hypothesis_closure_matrix.png",
        "final17_fig17",
        "Figure 17. Hypothesis closure and pre-registered predictions vs observed outcomes. The matrix separates falsified controller-transfer claims from supported surrogate-transfer claims and records the stretch-testcase prediction updates.",
        6.7,
        2.9,
    ),
]


def main() -> None:
    if not DOCX.exists():
        raise FileNotFoundError(DOCX)
    if not BACKUP.exists():
        shutil.copy2(DOCX, BACKUP)

    missing = [name for _, name, *_ in FIGURES if not (FIG_DIR / name).exists()]
    if missing:
        raise FileNotFoundError("Missing figures: " + ", ".join(missing))

    b = load_builder()
    with zipfile.ZipFile(DOCX, "r") as zin:
        document_xml = zin.read("word/document.xml").decode("utf-8")
        rels_xml = zin.read("word/_rels/document.xml.rels").decode("utf-8")
        root = LET.fromstring(document_xml.encode("utf-8"), parser=LET.XMLParser(recover=True, huge_tree=True))
        body = root.find("w:body", NS)
        assert body is not None

        for child in list(body):
            if child.tag == f"{{{NS['w']}}}p" and (has_drawing(child) or is_figure_caption(child)):
                body.remove(child)

        rel_root = ET.fromstring(rels_xml)
        for rel in list(rel_root):
            typ = rel.attrib.get("Type", "")
            target = rel.attrib.get("Target", "")
            if typ.endswith("/image") or target.startswith("media/"):
                rel_root.remove(rel)

        rids: dict[str, str] = {}
        for i, (_, filename, *_rest) in enumerate(FIGURES, start=1300):
            rid = f"rId{i}"
            ET.SubElement(
                rel_root,
                "Relationship",
                {
                    "Id": rid,
                    "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
                    "Target": f"media/{filename}",
                },
            )
            rids[filename] = rid

        # Insert in reverse order so repeated anchors keep the requested visual order.
        for anchor, filename, name, caption, width, height in reversed(FIGURES):
            xml = b.image_xml(rids[filename], name, width, height) + b.caption(caption)
            insert_after(body, anchor, xml)

        new_doc_xml = LET.tostring(root, encoding="utf-8", xml_declaration=True)
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
            for _, filename, *_ in FIGURES:
                zout.write(FIG_DIR / filename, f"word/media/{filename}")

    tmp.replace(DOCX)
    print(f"Inserted {len(FIGURES)} main-paper figures into {DOCX}")


if __name__ == "__main__":
    main()
