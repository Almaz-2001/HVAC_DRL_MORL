"""Add a concise Block 1 conclusion subsection to Results I."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from lxml import etree as LET


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "docs" / "hvac_paper_final_q1.docx"
BACKUP = ROOT / "docs" / "hvac_paper_final_q1_before_results1_conclusion.docx"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def para_text(el: LET._Element) -> str:
    return "".join(t.text or "" for t in el.findall(".//w:t", NS)).strip()


def p_xml(text: str, style: str | None = None) -> LET._Element:
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    style_xml = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    xml = f'<w:p xmlns:w="{NS["w"]}">{style_xml}<w:r><w:t>{escaped}</w:t></w:r></w:p>'
    return LET.fromstring(xml.encode("utf-8"))


def find_idx(body: LET._Element, startswith: str) -> int:
    for i, child in enumerate(list(body)):
        if child.tag == f"{{{NS['w']}}}p" and para_text(child).startswith(startswith):
            return i
    raise ValueError(startswith)


def main() -> None:
    if not BACKUP.exists():
        shutil.copy2(DOCX, BACKUP)
    with zipfile.ZipFile(DOCX, "r") as zin:
        xml = zin.read("word/document.xml").decode("utf-8")
        root = LET.fromstring(xml.encode("utf-8"), parser=LET.XMLParser(recover=True, huge_tree=True))
        body = root.find("w:body", NS)
        assert body is not None
        full = "\n".join(para_text(p) for p in body.findall("w:p", NS))
        if "5.5 Block 1 conclusion" not in full:
            idx = find_idx(body, "6. Results II")
            paragraphs = [
                p_xml("5.5 Block 1 conclusion", "Heading2"),
                p_xml("Block 1 closes with a deliberately asymmetric conclusion. As a predictive digital twin, calibrated v3.5 is supported: Stage A/B/C reduces 24 h rollout RMSE_T from 1.466 C to 0.644 C, reduces power MAE from 810 W to 482 W, and identifies a physically plausible C_zon = 4.413e5 J/K. The residual distribution, error CDF, and Stage-B convergence diagnostics show that this is not a single-metric artifact."),
                p_xml("As a direct RL rollout environment, however, calibrated v3.5 is rejected. PPO trained directly on v3.5 enters saturated action regimes and fails live BOPTEST validation despite the model's stronger offline predictive fidelity. This falsifies the simple assumption that the most accurate surrogate is automatically the best policy-training environment."),
                p_xml("The constructive outcome is role separation. The v3 surrogate remains the rollout backend because it provides smooth and computationally cheap dynamics for PPO; calibrated v3.5 is retained as a frozen physical teacher through disagreement regularization. This conclusion is the dependency passed to Block 2: controller validation must test the hybrid role assignment, not merely compare surrogate RMSE values."),
            ]
            for offset, el in enumerate(paragraphs):
                body.insert(idx + offset, el)
        new_xml = LET.tostring(root, encoding="utf-8", xml_declaration=True)
        tmp = DOCX.with_suffix(".tmp.docx")
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, new_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))
    tmp.replace(DOCX)
    print("Added Results I conclusion")


if __name__ == "__main__":
    main()
