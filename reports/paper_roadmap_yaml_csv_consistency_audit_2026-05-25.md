# Paper / Roadmap / YAML / CSV Consistency Audit

Date: 2026-05-25

Scope:

- Paper DOCX: `docs/hvac_paper_skeleton_q1_restructured.docx`
- Paper generator: `docs/build_hvac_paper_docx.py`
- Roadmap: `roadmap.md`
- MORL audit YAML: `configs/morl_canonical_selection_log.yaml`
- Block 3 audit YAML: `configs/block3_testcase_manifest.yaml`
- Canonical CSV sources under `reports/` and `outputs/`

## Corrections Applied

1. Paper abstract wording for Block 2 hybrid RMSE was corrected.
   - Previous wording: "restores live closed-loop RMSE below 0.65 C"
   - Problem: the Block 2 hybrid RMSE is 0.795 C on `peak_heat_window` and 0.633 C on `typical_heat_window`.
   - Corrected wording: "restores live closed-loop RMSE to 0.795 C on the peak window and 0.633 C on the typical window."
   - Source: `outputs/block2_thermostatic_hybrid_v3_v35_l010/summary.csv`, reflected in Table 4 of the DOCX.

2. Roadmap commercial hydronic C_zon value was corrected.
   - Previous: `8.429e+05 J/K`
   - Corrected: `8.425e+05 J/K`
   - Source: `reports/block3_singlezone_commercial_hydronic_transfer_summary.csv` and `configs/block3_testcase_manifest.yaml`.

## Verified Consistent Values

### Runtime Benchmark

- Hybrid backend speed: `1,786.8` env-steps/s
- Speed-up vs BOPTEST RTE HTTP: `85.0x`
- Source: `reports/speed_benchmark_table.csv`
- Status: consistent in DOCX and `roadmap.md`.

### Block 1 Predictive Validity

- v3 24h RMSE_T: `1.558 C` in Table 3 / S11.
- calibrated v3.5 24h RMSE_T: `0.644 C` in Table 3 / S11.
- calibrated v3.5 24h MAE_T: `0.482 C`.
- Source: `reports/hou_evins_predictive_validity_table.csv`.
- Status: consistent in DOCX supplementary tables.

### Block 2 Thermostatic Hybrid

- `hybrid_l010` peak: `m_s=0.087`, violation `4.69%`, energy `305.3 kWh`, RMSE center `0.795 C`.
- `hybrid_l010` typical: `m_s=0.041`, violation `2.38%`, energy `352.8 kWh`, RMSE center `0.633 C`.
- Source: `outputs/block2_thermostatic_hybrid_v3_v35_l010/summary.csv`.
- Status: consistent after abstract correction.

### Block 2 HDRL Sweep

- `l000` is best among reported HDRL lambda settings.
- Peak `l000`: `m_s=0.180`, violation `6.10%`, energy `329.6 kWh`, RMSE center `0.751 C`.
- Typical `l000`: `m_s=0.234`, violation `3.12%`, energy `385.1 kWh`, RMSE center `0.691 C`.
- Source: `reports/block2_hdrl_lambda_sweep_summary.csv`.
- Status: consistent in DOCX Table 5.

### Block 2 MORL Canonical N=5

- Neutral canonical: `m_s=0.187 +/- 0.078`, `sigma/mean=0.418`.
- Practical canonical: `m_s=0.139 +/- 0.085`, `sigma/mean=0.613`.
- Source: `reports/morl_canonical_seedfix_yearly_summary.csv` and `configs/morl_canonical_selection_log.yaml`.
- Status: consistent in `roadmap.md`; DOCX text reports the mean and high-variance conclusion without the practical sigma number.

### Block 3 Transferability

- `bestest_hydronic_heat_pump`: `m_s_RL=0.665`, `m_s_PI=0.464`, threshold `0.579`, energy delta `-7.3%`, full RMSE improvement `60.2%`, C_zon ratio `1.89x`.
- `bestest_hydronic`: `m_s_RL=0.976`, `m_s_PI=0.750`, threshold `0.938`, energy delta `-5.8%`, full RMSE improvement `87.4%`, C_zon ratio `1.95x`.
- `singlezone_commercial_hydronic`: `m_s_RL=0.431`, `m_s_PI=0.628`, threshold `0.785`, energy delta `+35.3%`, full RMSE improvement `87.8%`, C_zon ratio `1.91x`.
- Sources: `reports/block3_transfer_matrix.csv`, per-testcase transfer summaries, and `configs/block3_testcase_manifest.yaml`.
- Status: consistent in DOCX, roadmap, YAML, and CSV after C_zon roadmap correction.

## Remaining Methodological Notes

- The DOCX intentionally keeps Table 4b as a sanity-check yearly output from the universal evaluator and explicitly states that it does not replace the frozen Block 2 targeted-window KPI table.
- The paper correctly distinguishes 14-day peak/typical windows for Block 2 from yearly transferability evaluation in Block 3.
- The commercial hydronic case remains a threshold PASS but not a deployment-ready PASS because energy increases by `35.3%` versus PI.

## Files Updated By This Audit

- `docs/build_hvac_paper_docx.py`
- `docs/hvac_paper_skeleton_q1_restructured.docx`
- `roadmap.md`
- `reports/paper_roadmap_yaml_csv_consistency_audit_2026-05-25.md`

