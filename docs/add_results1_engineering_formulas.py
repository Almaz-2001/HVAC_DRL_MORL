"""Add engineering formulas and metric derivations to Results I."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from lxml import etree as LET


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "docs" / "hvac_paper_final_q1.docx"
BACKUP = ROOT / "docs" / "hvac_paper_final_q1_before_results1_formulas.docx"
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


def insert_after(body: LET._Element, anchor: str, paragraphs: list[LET._Element]) -> None:
    idx = find_idx(body, anchor)
    for offset, el in enumerate(paragraphs, start=1):
        body.insert(idx + offset, el)


def main() -> None:
    if not BACKUP.exists():
        shutil.copy2(DOCX, BACKUP)
    with zipfile.ZipFile(DOCX, "r") as zin:
        xml = zin.read("word/document.xml").decode("utf-8")
        root = LET.fromstring(xml.encode("utf-8"), parser=LET.XMLParser(recover=True, huge_tree=True))
        body = root.find("w:body", NS)
        assert body is not None
        full = "\n".join(para_text(p) for p in body.findall("w:p", NS))

        if "5.1.1 Engineering metric definitions" not in full:
            insert_after(
                body,
                "The control-oriented v3 surrogate is a compact dual-head model",
                [
                    p_xml("5.1.1 Engineering metric definitions", "Heading3"),
                    p_xml("The Block 1 validation metrics are defined on recursive rollout trajectories rather than only on one-step supervised predictions. For a horizon h and N evaluated samples, the temperature rollout error is e_T,i(h) = T_hat_i(t+h) - T_i(t+h), and the reported horizon error is RMSE_T(h) = sqrt((1/N) sum_i e_T,i(h)^2). Figure 3 therefore measures accumulated closed-loop prediction error over 1 h, 4 h, 8 h, and 24 h horizons."),
                    p_xml("The residual-distribution diagnostic in Figure 4 uses the signed residual e_T = T_hat - T_BOPTEST and the absolute-error empirical CDF F_abs(epsilon) = P(|e_T| <= epsilon). The vertical engineering tolerances epsilon = 0.5, 1.0, and 1.5 C convert a statistical error distribution into a directly interpretable HVAC tolerance statement: they report what fraction of predictions stay within each temperature-error band."),
                    p_xml("The live-control utility comparison is deliberately separate from predictive RMSE. We define a live-utility gap for a training backend b as G_RL(b) = RMSE_live,T(b) - RMSE_rollout,T(b). A small or negative predictive RMSE alone is not sufficient; the backend is useful only if the learned policy also remains stable when transferred to the BOPTEST RTE."),
                ],
            )

        if "eta_C = (C_zon,final - C_zon,prior)" not in full:
            insert_after(
                body,
                "Stage B used an excitation-filtered subset of the telemetry rather than all quasi-steady samples.",
                [
                    p_xml("The physical-parameter update can be written as eta_C = (C_zon,final - C_zon,prior) / C_zon,prior. With C_zon,prior = 4.200e5 J/K and C_zon,final = 4.413e5 J/K, eta_C = 0.0507, i.e. approximately 5.1%. This bounded update is important: it is large enough to demonstrate data-driven identification, but small enough to keep the calibrated twin physically plausible."),
                ],
            )

        if "Delta_total = 1.557 - 0.644" not in full:
            insert_after(
                body,
                "This decomposition bounds the calibration claim.",
                [
                    p_xml("Numerically, the total apparent 24 h gain from legacy v3 to calibrated v3.5 is Delta_total = 1.557 - 0.644 = 0.913 C. The corpus-resolution term is Delta_corpus = 1.557 - 0.876 = 0.681 C, while the calibrated-physics term is Delta_cal = 0.876 - 0.644 = 0.232 C. The attribution ratios are Delta_corpus / Delta_total = 74.6% and Delta_cal / Delta_total = 25.4%. This is why the paper describes Stage A/B/C as a real but bounded calibration contribution rather than the sole source of the fidelity gain."),
                ],
            )

        if "r_hybrid = r_comfort + r_smooth + r_energy" not in full:
            insert_after(
                body,
                "The action distribution and phase portrait in Figure 9 provide the mechanism-level explanation.",
                [
                    p_xml("The resulting hybrid reward can be summarized as r_hybrid = r_comfort + r_smooth + r_energy - lambda_T |T_v3 - T_v35| - lambda_P |P_v3 - P_v35|. This expression makes the engineering role separation explicit: the policy state transition is still generated by v3, while v3.5 contributes a physical consistency cost but does not define the rollout dynamics."),
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
    print("Added Results I engineering formulas")


if __name__ == "__main__":
    main()
