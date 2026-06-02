# Paper Artifacts

Canonical paper-facing artifact directory for the HVAC DRL/MORL Q1 article.

## Structure

- `figures/main/`: final main-paper figures selected from `reports/final_q1_12_engineering_figures_manifest.csv`.
- `figures/supplementary/`: retained diagnostic figures not selected for the main paper.
- `tables/main/`: main-paper tables exported from `docs/hvac_paper_final_q1.docx`.
- `csv/reports/`: report-level CSV evidence used to build tables and figures.
- `manifests/`: figure manifests and the generated artifact inventory.

Large training outputs, raw corpora, model checkpoints, and BOPTEST binaries remain outside this directory and are ignored by Git according to `.gitignore`.
