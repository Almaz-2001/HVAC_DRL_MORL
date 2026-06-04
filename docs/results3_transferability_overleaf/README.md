# Results III Transferability - Overleaf package

Upload the whole folder `results3_transferability_overleaf` to Overleaf and
compile `main.tex`.

Recommended compiler:

- `pdfLaTeX`

Contents:

- `main.tex` - standalone Block 3 / Results III LaTeX section (generated).
- `build_results3_overleaf.py` - data-driven generator: regenerates `main.tex`
  with every numeric table and inline KPI read from `reports/` artifacts. Run
  from the repository root with the project Python environment:
  `python docs/results3_transferability_overleaf/build_results3_overleaf.py`.
- `figures/` - PDF/PNG figures referenced by `main.tex` (produced by the Block 3
  evaluation scripts; this builder references them and does not regenerate them).

The builder also generates one self-contained schematic,
`fig_block3_adapter`, showing the adapter-mediated transfer (one frozen
controller -> per-testcase adapter `A_k` -> three actuator interfaces) with
data-driven per-testcase controller verdicts; all other figures are referenced
from `figures/` (Block 3 evaluation scripts).

An actuator-adapter mapping table specifies, per testcase, the concrete BOPTEST
override variables and `T_sup`-to-override formulas (heat-intensity
`h = clip((T_sup-18)/17,0,1)`), verified from
`configs/block3_actuator_mapping_*.yaml`. A data-provenance note in Limitations
states which values are data-driven from `reports/block3_*` CSVs versus verified
literals from the audit-frozen manifest/adapter configs, plus the single-run /
N=3 statistical scope of the `C_zon`-uniformity finding.

Layout matches Results I/II exactly: no `\maketitle`; one `\section`
(Results III = Section 6) with subsections 6.1-6.13; `float`/`placeins` with
`[H]` floats; nomenclature table after the protocol figure; clean captions
(provenance lives in roadmap Section 15); a Limitations subsection and a
dedicated "Results III conclusion". Pre-registered hypotheses, predictions, and
audit anchors are verified literals from the manifest; all numeric values are
data-driven from `reports/block3_*` CSVs.

Scientific scope covered in this package:

- Block 3 pre-registration and audit anchors.
- Target testcase ladder and actuator adapter rationale.
- Recalibration regimes: none, partial, full.
- Controller-side pass/fail formulas using `m_s_RL <= 1.25 * m_s_PI`.
- Energy penalty formula and distinction between threshold PASS and
  deployment-ready PASS.
- Surrogate-side RMSE improvement formula.
- `C_zon` ratio and hydronic-family consistency analysis.
- Q1-polished transfer diagnostics:
  - Comfort-energy deployment plane with interpreted quadrants.
  - Horizontal `C_zon` box/point diagnostic over pre-registered Hypothesis A
    and Hypothesis B intervals.
  - Transfer-profile radar chart combining surrogate RMSE gain,
    threshold-normalized comfort pass score, and energy parity.
- Primary, secondary, and stretch testcase results.
- Hypothesis closure for H1, H2, H3 surrogate-side, H3 controller-side, and
  hierarchy consistency.
- Pre-registered stretch predictions versus observed outcomes.

All numeric claims are taken from the project artifacts:

- `docs/block3_complete_results.txt`
- `configs/block3_testcase_manifest.yaml`
- `configs/block3_actuator_mapping_bestest_hydronic_heat_pump.yaml`
- `configs/block3_actuator_mapping_bestest_hydronic.yaml`
- `configs/block3_actuator_mapping_singlezone_commercial_hydronic.yaml`
- `reports/block3_transfer_matrix.csv`
- `reports/block3_bestest_hydronic_heat_pump_transfer_summary.csv`
- `reports/block3_bestest_hydronic_transfer_summary.csv`
- `reports/block3_singlezone_commercial_hydronic_transfer_summary.csv`
- `reports/block3_*_adapter_smoke_summary.csv`

Structural check should verify that every `\includegraphics` reference resolves
inside the local `figures/` directory before upload.
