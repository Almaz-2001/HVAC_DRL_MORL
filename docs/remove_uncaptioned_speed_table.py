"""Remove the uncaptioned speed table from the main DOCX.

Runtime feasibility is now reported in prose in Results I. The detailed speed
benchmark belongs in supplementary/artifacts, so the main paper keeps seven
captioned tables.
"""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from lxml import etree as LET


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "docs" / "hvac_paper_final_q1.docx"
BACKUP = ROOT / "docs" / "hvac_paper_final_q1_before_remove_uncaptioned_speed_table.docx"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def text(el: LET._Element) -> str:
    return " ".join("".join(p.itertext()).strip() for p in el.xpath(".//w:p", namespaces=NS))


def main() -> None:
    if not BACKUP.exists():
        shutil.copy2(DOCX, BACKUP)
    with zipfile.ZipFile(DOCX, "r") as zin:
        xml = zin.read("word/document.xml").decode("utf-8")
        root = LET.fromstring(xml.encode("utf-8"), parser=LET.XMLParser(recover=True, huge_tree=True))
        body = root.find("w:body", NS)
        assert body is not None
        removed = 0
        for tbl in root.xpath(".//w:tbl", namespaces=NS):
            tbl_text = text(tbl)
            if tbl_text.startswith("Backend Steps/s Median ms Speed-up Role"):
                parent = tbl.getparent()
                parent.remove(tbl)
                removed += 1
        new_xml = LET.tostring(root, encoding="utf-8", xml_declaration=True)
        tmp = DOCX.with_suffix(".tmp.docx")
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, new_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))
    tmp.replace(DOCX)
    print(f"Removed {removed} uncaptioned speed table(s)")


if __name__ == "__main__":
    main()
