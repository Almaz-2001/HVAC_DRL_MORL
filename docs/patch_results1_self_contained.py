"""Patch Results I in hvac_paper_final_q1.docx to be more self-contained.

Adds concise Q1-reviewer-facing prose:
- explicit numeric deltas
- Stage B excitation filtering
- matched-corpus bounded interpretation
- runtime feasibility
- mechanism interpretation for direct-v3.5 PPO failure
"""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from lxml import etree as LET


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "docs" / "hvac_paper_final_q1.docx"
BACKUP = ROOT / "docs" / "hvac_paper_final_q1_before_results1_self_contained_patch.docx"

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def para_text(el: LET._Element) -> str:
    return "".join(t.text or "" for t in el.findall(".//w:t", NS)).strip()


def p_xml(text: str) -> LET._Element:
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    xml = f'<w:p xmlns:w="{NS["w"]}"><w:r><w:t>{escaped}</w:t></w:r></w:p>'
    return LET.fromstring(xml.encode("utf-8"))


def find_para(body: LET._Element, startswith: str) -> int:
    for i, child in enumerate(list(body)):
        if child.tag == f"{{{NS['w']}}}p" and para_text(child).startswith(startswith):
            return i
    raise ValueError(f"Paragraph not found: {startswith}")


def insert_after(body: LET._Element, anchor: str, paragraphs: list[str]) -> None:
    idx = find_para(body, anchor)
    for offset, text in enumerate(paragraphs, start=1):
        body.insert(idx + offset, p_xml(text))


def already_patched(body: LET._Element) -> bool:
    full = "\n".join(para_text(p) for p in body.findall("w:p", NS))
    return "The quantitative Block 1 conclusion is therefore two-level" in full


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

        if not already_patched(body):
            insert_after(
                body,
                "Figure 3. Multi-horizon rollout RMSE curves.",
                [
                    "The quantitative Block 1 conclusion is therefore two-level. First, calibrated v3.5 is the best predictive twin: its 24 h rollout RMSE_T is 0.644 C, compared with 1.466 C for raw v3.5 and 1.557 C for the legacy v3 reference. The improvement is not confined to one-step alignment; it persists under recursive multi-horizon rollout, which is the relevant regime for controller training and validation.",
                    "Second, the raw physical architecture alone is not sufficient. Raw v3.5 remains close to the legacy v3 24 h error before inverse calibration, so the observed improvement must be attributed to the Stage A/B/C identification process rather than to adding a physics-inspired network topology by itself.",
                ],
            )

            insert_after(
                body,
                "The calibrated v3.5 twin improves one-step and recursive temperature prediction while retaining physical interpretability.",
                [
                    "Stage B used an excitation-filtered subset of the telemetry rather than all quasi-steady samples. Only the top-excitation rows were used for C_zon identification (403 of 8058 training rows), which prevents steady operating points from dominating a parameter that is identifiable primarily during transients. This filtering is important for interpreting C_zon as a physical parameter rather than as a residual fitting knob.",
                    "The final C_zon = 4.413e5 J/K is only 5.1% above the 4.200e5 J/K prior. This is the desired magnitude of update: large enough to show that the data modify the prior, but small enough to remain physically plausible and to avoid the appearance of unconstrained parameter fitting.",
                ],
            )

            insert_after(
                body,
                "A direct v3-versus-v3.5 comparison would be misleading because the active v3.5 pipeline uses a 15-minute corpus while the legacy v3 benchmark was originally trained on an hourly workflow.",
                [
                    "This decomposition bounds the calibration claim. The move from the legacy hourly v3 corpus to a matched 15 min v3 corpus reduces 24 h RMSE_T from 1.557 C to 0.876 C, explaining 74.6% of the original v3-to-v3.5 gap. Stage A/B/C then reduces the matched-corpus error further from 0.876 C to 0.644 C, explaining the remaining 25.4%. We therefore do not claim that physics alone explains the full improvement; the defensible claim is that corpus resolution and physical calibration jointly produce the final predictive-fidelity gain.",
                ],
            )

            insert_after(
                body,
                "The closed-loop result is the critical negative finding.",
                [
                    "The live-control deltas are large enough to rule out a minor tuning explanation. Direct-v3.5 PPO reaches approximately 4.32-4.40 C live RMSE_T with comfort violation around 77-82%, whereas the hybrid controller is around 0.61-0.63 C RMSE_T with low single-digit violation on the same targeted windows. Thus, the failure is not that v3.5 is an inaccurate predictor; it is that direct PPO training on v3.5 induces a brittle policy distribution.",
                    "The action distribution and phase portrait in Figure 9 provide the mechanism-level explanation. The direct-v3.5 policy enters saturated bang-bang action regimes and produces extreme actions for modest temperature errors. Hybridization avoids this by preserving v3 as the smooth rollout model while using frozen v3.5 only as a physical disagreement penalty.",
                    "The hybrid backend also remains computationally feasible for reinforcement learning. In the CPU speed benchmark it sustains approximately 1787 environment steps per second, about 85x faster than the live BOPTEST RTE HTTP-Docker loop used for validation. The hybrid result is therefore not only more stable in live control; it is also fast enough to remain a practical PPO training backend.",
                ],
            )

        new_xml = LET.tostring(root, encoding="utf-8", xml_declaration=True)
        tmp = DOCX.with_suffix(".tmp.docx")
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, new_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))

    tmp.replace(DOCX)
    print(f"Patched Results I in {DOCX}")


if __name__ == "__main__":
    main()
