"""Insert the final 12-figure engineering main-paper set.

The set prioritizes measured diagnostics over presentation-style diagrams:
pipeline, backend architecture, rollout RMSE, residual/CDF, C_zon convergence,
matched-corpus waterfall, fidelity-vs-control, live traces, action/phase
portrait, MORL Pareto, Block 3 deployment plane, and C_zon hypothesis interval.
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
BACKUP = ROOT / "docs" / "hvac_paper_final_q1_before_12_engineering_figures.docx"
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
    ("3. Methodology", "final17_fig01_overall_study_architecture.png", "q1eng_fig01", "Figure 1. Overall experimental pipeline. The study separates data generation, surrogate calibration, live controller validation, and transferability testing rather than treating digital-twin accuracy as a single scalar property.", 6.7, 2.7),
    ("3.2 Surrogate roles", "final17_fig02_backend_architecture.png", "q1eng_fig02", "Figure 2. v3 / v3.5 / hybrid backend architecture with tensor roles and parameter counts. v3 is the smooth dual-head rollout surrogate; v3.5 is the calibrated physics-informed twin; hybrid uses frozen-v3.5 disagreement as a soft physical censor.", 6.7, 2.9),
    ("5.2 Stage A/B/C calibration result", "block1_predictive_validity_horizon_lines.png", "q1eng_fig03", "Figure 3. Multi-horizon rollout RMSE curves. Real horizon_metrics.csv artifacts show how recursive temperature error accumulates from 1h to 24h for v3, raw v3.5, and calibrated v3.5.", 6.4, 3.1),
    ("5.2 Stage A/B/C calibration result", "final_eng_fig04_residual_distribution_error_cdf.png", "q1eng_fig04", "Figure 4. Residual distribution and absolute-error CDF. The figure reports bias, spread, P95 absolute error, and engineering tolerance thresholds at 0.5, 1.0, and 1.5 °C.", 6.7, 2.8),
    ("5.2 Stage A/B/C calibration result", "block1_stage_abc_calibration_diagnostics.png", "q1eng_fig05", "Figure 5. C_zon Stage-B identification and Stage-C residual-head diagnostics. The Stage-B trajectory documents physical-parameter convergence rather than manual tuning.", 6.4, 3.2),
    ("5.3 Matched-corpus decomposition", "final17_fig04_matched_corpus_decomposition.png", "q1eng_fig06", "Figure 6. Matched-corpus waterfall decomposition. The plot separates the 15-minute corpus contribution from the additional Stage A/B/C calibration contribution.", 6.2, 3.0),
    ("5.4 Fidelity-to-control gap", "final17_fig05_fidelity_vs_rl_utility.png", "q1eng_fig07", "Figure 7. Predictive fidelity vs live control utility. Calibrated v3.5 is the strongest offline predictor but the weakest direct RL rollout backend; hybrid role separation recovers live utility.", 5.8, 3.4),
    ("5.4 Fidelity-to-control gap", "final_eng_fig08_live_boptest_closed_loop_traces.png", "q1eng_fig08", "Figure 8. Live BOPTEST closed-loop traces for pure v3, direct v3.5, and hybrid_l010. The trace view shows the comfort-band behaviour, supply commands, and power response behind the aggregate KPIs.", 6.7, 4.6),
    ("5.4 Fidelity-to-control gap", "final_eng_fig09_action_distribution_phase_portrait.png", "q1eng_fig09", "Figure 9. Action distribution and phase portrait. Direct v3.5 PPO exhibits bang-bang action saturation and extreme action response relative to temperature error, explaining its live transfer failure.", 6.7, 3.0),
    ("6.3 MORL, observation interface", "final17_fig10_morl_comfort_energy_pareto.png", "q1eng_fig10", "Figure 10. MORL comfort-energy Pareto front with canonical seed-variance information. Energy-only scalarization collapses, comfort-only has the lowest m_s, and practical 75/25 remains seed-sensitive.", 5.8, 3.5),
    ("7.2 Controller-side transfer", "final_eng_fig11_block3_deployment_plane.png", "q1eng_fig11", "Figure 11. Block 3 comfort-energy deployment plane. Residential hydronic testcases fail the m_s threshold while saving energy; the commercial testcase passes the threshold but incurs a large energy penalty.", 5.8, 3.6),
    ("7.3 Surrogate-side transfer", "final_eng_fig12_czon_hypothesis_interval.png", "q1eng_fig12", "Figure 12. C_zon hypothesis interval test across hydronic testcases. Observed ratios support the 1.7–2.2× uniform hydronic-family hypothesis and falsify the 3–10× scale-dependent hypothesis for the tested cases.", 5.9, 3.6),
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
        for i, (_, filename, *_rest) in enumerate(FIGURES, start=1700):
            rid = f"rId{i}"
            ET.SubElement(rel_root, "Relationship", {"Id": rid, "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image", "Target": f"media/{filename}"})
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
    print(f"Inserted {len(FIGURES)} final engineering Q1 figures into {DOCX}")


if __name__ == "__main__":
    main()
