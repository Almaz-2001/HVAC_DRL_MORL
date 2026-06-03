"""Add a concise front-matter map to supplementary_material.docx."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from lxml import etree as LET


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "docs" / "supplementary_material.docx"
BACKUP = ROOT / "docs" / "supplementary_material_before_block_map.docx"

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def p(text: str, style: str | None = None) -> str:
    style_xml = ""
    if style:
        style_xml = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return f"<w:p>{style_xml}<w:r><w:t>{escaped}</w:t></w:r></w:p>"


def parse(xml: str) -> list[LET._Element]:
    wrapper = f'<root xmlns:w="{NS["w"]}">{xml}</root>'
    return list(LET.fromstring(wrapper.encode("utf-8")))


def para_text(el: LET._Element) -> str:
    return "".join(t.text or "" for t in el.findall(".//w:t", NS)).strip()


def main() -> None:
    if not DOCX.exists():
        raise FileNotFoundError(DOCX)
    if not BACKUP.exists():
        shutil.copy2(DOCX, BACKUP)

    with zipfile.ZipFile(DOCX, "r") as zin:
        xml = zin.read("word/document.xml").decode("utf-8")
        root = LET.fromstring(xml.encode("utf-8"), parser=LET.XMLParser(recover=True, huge_tree=True))
        body = root.find("w:body", NS)
        assert body is not None

        existing = "\n".join(para_text(p_el) for p_el in body.findall("w:p", NS)[:20])
        if "Supplementary organization map" not in existing:
            front = "".join(
                [
                    p("Supplementary organization map", "Heading1"),
                    p("This supplementary file holds detailed numerical artifacts that were intentionally removed from the main Q1 paper to keep the main body within a compact figure/table budget. The main paper keeps only eight high-impact figures and seven consolidated tables; detailed per-block tables, traces, variance diagnostics, and supporting figures remain here."),
                    p("S1. Block 1 detailed surrogate-fidelity evidence", "Heading2"),
                    p("Includes v3 dual-head architecture details, C_zon Stage-B trajectory, backend speed benchmark, per-episode 24h rollout RMSE, residual distributions, action-saturation diagnostics, and literature-positioning graphics. These support Results I without duplicating the main-paper figures."),
                    p("S2. Block 2 detailed control and MORL evidence", "Heading2"),
                    p("Includes thermostatic hybrid traces, direct-v3.5 negative-control details, HDRL lambda sweep, MORL 5D vs 17D ablation, MORL seasonal and seed-variance diagnostics, Pareto sweep details, and surrogate-to-live transfer-gap tables. These support Results II."),
                    p("S3. Block 3 detailed transferability evidence", "Heading2"),
                    p("Includes testcase selection, actuator-adapter checks, recalibration-regime definitions, per-testcase transfer summaries, hydronic C_zon re-identification details, stretch-testcase prediction closure, and hypothesis-status audit records. These support Results III."),
                    p("Traceability note", "Heading2"),
                    p("The standalone block result documents remain preserved as docs/block1_complete_results.docx, docs/block2_complete_results.docx, and docs/block3_complete_results.docx. The main document docs/hvac_paper_final_q1.docx now references only the compact main-paper subset; this supplementary file retains the detailed artifacts."),
                ]
            )
            elems = parse(front)
            insert_at = 1 if len(body) > 1 else 0
            for offset, el in enumerate(elems):
                body.insert(insert_at + offset, el)

        new_xml = LET.tostring(root, encoding="utf-8", xml_declaration=True)
        tmp = DOCX.with_suffix(".tmp.docx")
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, new_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))

    tmp.replace(DOCX)
    print(f"Updated supplementary map: {DOCX}")


if __name__ == "__main__":
    main()
