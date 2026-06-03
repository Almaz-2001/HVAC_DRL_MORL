"""Insert the engineering-focused main-paper figure set.

This version intentionally reduces presentation-style diagrams and promotes
diagnostic evidence figures. It keeps tables intact and replaces only figure
drawings/captions in docs/hvac_paper_final_q1.docx.
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
BACKUP = ROOT / "docs" / "hvac_paper_final_q1_before_engineering_figures.docx"
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
        "engineering_fig01",
        "Figure 1. Overall experimental pipeline. The study separates surrogate calibration, live controller validation, and transferability testing rather than treating digital-twin accuracy as a single scalar property.",
        6.7,
        2.7,
    ),
    (
        "3.2 Surrogate roles",
        "final17_fig02_backend_architecture.png",
        "engineering_fig02",
        "Figure 2. v3 / v3.5 / hybrid backend architecture. v3 is the smooth dual-head rollout surrogate; v3.5 is the calibrated physics-informed twin; the hybrid backend uses frozen-v3.5 disagreement as a soft physical censor.",
        6.7,
        2.9,
    ),
    (
        "5.2 Stage A/B/C calibration result",
        "block1_predictive_validity_horizon_lines.png",
        "engineering_fig03",
        "Figure 3. Multi-horizon rollout RMSE curves. The curves are generated from the real horizon_metrics.csv artifacts and show how recursive temperature error grows from 1h to 24h for v3, raw v3.5, and calibrated v3.5.",
        6.4,
        3.1,
    ),
    (
        "5.2 Stage A/B/C calibration result",
        "block1_temperature_residual_histograms.png",
        "engineering_fig04",
        "Figure 4. Temperature residual distributions before and after calibration. Residual shape, not only mean RMSE, confirms that calibrated v3.5 reduces the spread of prediction errors.",
        6.4,
        3.0,
    ),
    (
        "5.2 Stage A/B/C calibration result",
        "block1_stage_abc_calibration_diagnostics.png",
        "engineering_fig05",
        "Figure 5. C_zon Stage-B identification and Stage-C residual-head diagnostics. The figure is generated from Stage-B and Stage-C calibration histories and documents physical-parameter convergence.",
        6.4,
        3.2,
    ),
    (
        "5.3 Matched-corpus decomposition",
        "final17_fig04_matched_corpus_decomposition.png",
        "engineering_fig06",
        "Figure 6. Matched-corpus predictive-fidelity decomposition. The plot separates the 15-minute corpus contribution from the additional Stage A/B/C calibration contribution.",
        6.2,
        3.0,
    ),
    (
        "5.4 Fidelity-to-control gap",
        "final17_fig05_fidelity_vs_rl_utility.png",
        "engineering_fig07",
        "Figure 7. Predictive fidelity vs live control utility. Calibrated v3.5 is the strongest offline predictor but the weakest direct RL rollout backend; hybrid role separation recovers live utility.",
        5.8,
        3.4,
    ),
    (
        "5.4 Fidelity-to-control gap",
        "block1_q1_fig11_action_saturation.png",
        "engineering_fig08",
        "Figure 8. Action distribution and bang-bang saturation diagnostic. Direct v3.5 PPO enters saturated action regimes that do not survive live BOPTEST validation.",
        6.2,
        3.0,
    ),
    (
        "5.4 Fidelity-to-control gap",
        "block1_q1_fig10_transfer_gap_diagnostics.png",
        "engineering_fig09",
        "Figure 9. Transfer-gap diagnostics. The figure compares live/surrogate m_s gap, action-gap norm, and divergence behaviour across pure v3, direct v3.5, and hybrid backends.",
        6.2,
        3.0,
    ),
    (
        "6.2 Thermostatic PPO and HDRL",
        "final17_fig06_live_boptest_controller_comparison.png",
        "engineering_fig10",
        "Figure 10. Live BOPTEST KPI comparison. Pure v3 PPO, direct-v3.5 PPO, and hybrid_l010 PPO are compared on m_s, violation percentage, RMSE_T, and energy for peak and typical heat windows.",
        6.7,
        4.2,
    ),
    (
        "6.2 Thermostatic PPO and HDRL",
        "final17_fig08_hdrl_lambda_temp_sweep.png",
        "engineering_fig11",
        "Figure 11. HDRL lambda_temp sensitivity. The best HDRL setting is lambda_temp = 0.00; the thermostatic-optimal lambda_temp = 0.10 over-regularizes the hierarchy.",
        6.7,
        2.5,
    ),
    (
        "6.3 MORL, observation interface",
        "final17_fig10_morl_comfort_energy_pareto.png",
        "engineering_fig12",
        "Figure 12. MORL comfort-energy Pareto front with canonical seed-variance information. Energy-only scalarization collapses, comfort-only has the lowest m_s, and practical 75/25 remains seed-sensitive.",
        5.8,
        3.5,
    ),
    (
        "7.2 Controller-side transfer",
        "final17_fig14_rl_vs_pi_threshold_energy_penalty.png",
        "engineering_fig13",
        "Figure 13. Block 3 threshold-normalized transfer and energy penalty. Residential hydronic cases fail the m_s threshold; the commercial case passes the threshold but pays a +35.3% energy penalty.",
        6.7,
        3.1,
    ),
    (
        "7.3 Surrogate-side transfer",
        "final17_fig16_hydronic_czon_consistency.png",
        "engineering_fig14",
        "Figure 14. Hydronic-family C_zon consistency with hypothesis interval. Full Stage A/B/C re-identifies hydronic target capacitance near 1.92 x the bestest_air value across all three target cases.",
        5.8,
        3.2,
    ),
]


def main() -> None:
    if not DOCX.exists():
        raise FileNotFoundError(DOCX)
    if not BACKUP.exists():
        shutil.copy2(DOCX, BACKUP)

    missing = [filename for _, filename, *_ in FIGURES if not (FIG_DIR / filename).exists()]
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
        for i, (_, filename, *_rest) in enumerate(FIGURES, start=1500):
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
    print(f"Inserted {len(FIGURES)} engineering main-paper figures into {DOCX}")


if __name__ == "__main__":
    main()
