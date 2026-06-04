# Results I Digital Twin Fidelity - Overleaf Package

Upload the whole folder `results1_digital_twin_overleaf` to Overleaf and compile
`main.tex`.

Recommended compiler:

- `pdfLaTeX`

## Purpose

This folder is a standalone, roadmap-derived LaTeX package for Section 4:
**Digital-Twin Fidelity and the RL-Utility Paradox**. It follows Block 1 in
`roadmap.md` and stops at the same evidence boundary:

- v3 direct-TSup surrogate training and architecture
- v3.5 Stage A/B/C inverse calibration
- corpus-matched v3 retraining for reviewer mitigation
- Hou-and-Evins reporting completeness
- runtime feasibility / speed benchmark

It intentionally does **not** include Block 2-only claims such as direct-v3.5
controller failure, hybrid PPO training, live BOPTEST transfer-gap diagnostics,
or action saturation. Those require trained policies and live transfer, so they
belong to Results II / Block 2.

## Reproducible Builder

Regenerate the section and figures from current project artifacts:

```bash
python docs/results1_digital_twin_overleaf/build_results1_overleaf.py
```

The builder reads real roadmap-facing artifacts, including:

- `reports/hou_evins_sample_generation_table.csv`
- `reports/hou_evins_training_hyperparams_table.csv`
- `reports/hou_evins_scaling_table.csv`
- `reports/block1_corpus_matched_comparison.csv`
- `reports/block1_corpus_matched_comparison.json`
- `reports/speed_benchmark_table.csv`
- `outputs/surrogate_v35_inverse_boptest_15min_episodeaware/calibration_summary_boptest_v35.json`
- `outputs/surrogate_v35_inverse_boptest_15min_power_head_only/calibration_summary_boptest_v35.json`
- `outputs/*/window_errors.csv`
- `outputs/*/all_full_rollouts.csv`
- `outputs/*/episode_summary.csv`
- `outputs/surrogate_v35_inverse_boptest_15min_episodeaware/stage_b_history_v35.csv`

## Contents

- `main.tex` - standalone Block 1 / Results I LaTeX section.
- `build_results1_overleaf.py` - reproducible generator for `main.tex` and figures.
- `figures/` - PDF and PNG figures referenced by `main.tex`.

## Figure Set

The current roadmap-consistent figure set is:

- `rie_fig01_block1_artifact_chain` - roadmap-derived Block 1 artifact chain with real row counts, 24 h RMSE values, `C_zon`, and speed-up.
- `rie_fig02_surrogate_design` - v3/v3.5 role separation with v3 parameter counts and Stage A/B/C structure.
- `rie_fig03_stage_abc_diagnostics` - two-panel Stage B `C_zon` convergence plus before/after calibration metrics.
- `rie_fig04_predictive_validity` - multi-horizon rollout RMSE with bootstrap confidence bands plus engineering tolerance CDF.
- `rie_fig05_matched_corpus_attribution` - four-variant matched-corpus RMSE comparison and attribution waterfall.
- `rie_fig06_runtime_feasibility` - BOPTEST RTE versus surrogate runtime feasibility on a log-scale throughput plot.
- `rie_fig07_episode_replicability` - per-episode RMSE across the eight held-out BOPTEST rollouts used for replicative validity.
- `rie_fig08_v3_learning_curve` - v3 supervised train/validation learning curves with the early-stop epoch marked (overfitting check).

## Scientific Scope

This package supports the following Block 1 claims:

- v3 is a compact, fast, control-oriented surrogate with an 8D input and
  dual-head temperature/power outputs.
- v3.5 is validated as a physically interpretable predictive twin through
  Stage A/B/C calibration and `C_zon` identification.
- Stage B uses excitation filtering, preventing quasi-steady samples from
  dominating physical-parameter identification.
- Multi-horizon RMSE and absolute-error CDF diagnostics show predictive
  behavior beyond a single scalar RMSE.
- The matched-corpus experiment bounds the calibration claim: improvement is
  partly due to the 15-minute corpus and partly due to Stage A/B/C calibration.
- Runtime benchmarks show surrogate stepping is feasible for downstream policy
  training, while controller utility remains a Block 2 question.

## Boundary Statement

Results I ends at digital-twin fidelity, matched-corpus attribution, and
runtime feasibility. The next executable section in `roadmap.md` is Block 2:
pure-v3 thermostatic PPO baseline, then direct-v3.5 negative control, then
hybrid PPO evaluation.

## Section Structure

The generated `main.tex` uses `\setcounter{section}{3}` so the standalone
Overleaf file compiles as Section 4:

- 4.1 Direct Supply-Temperature Control Interface - the direct-`T_sup` control
  parameterization (action-to-setpoint map, common surrogate signature shared by
  all four backends, and a modelling-assumptions table)
- 4.2 Control-Oriented Surrogate Architecture (v3) - dual-head transition model,
  the multi-horizon + physical-penalty training objective, and the v3 supervised
  training trajectory (early-stop epoch and held-out one-step `R^2`)
- 4.3 Physics-Informed Twin and Inverse Calibration (v3.5) - the lumped-capacity
  ODE backbone, explicit-Euler discretization, positive `C_zon`
  reparameterization, a Stage A telemetry-alignment table, the Stage B MAP
  inverse-problem statement with the excitation-identifiability argument, and the
  Stage B `C_zon` identification table
- 4.4 Multi-Step Validation and Matched-Corpus Ablation - metric definitions
  (rollout RMSE, `R^2`, P95), the Hou-and-Evins multi-horizon rollout table (with
  the diagnostic negative 24 h v3 `R^2`), and the additive attribution
  decomposition with both paths (matched-architecture and raw-v3.5)
- 4.5 Runtime Feasibility - backend throughput table with median and P95 step
  latency plus a wall-clock feasibility extrapolation
- 4.6 Step-Size Design Disclosure - reviewer disclosure of the 3600 s vs 900 s
  step mismatch, the explicit-`dt` consistency of v3.5 vs v3, and the audit-chain
  rationale for preserving it
- 4.7 Limitations - temperature-scoped validation, the disclosed power-channel
  ASHRAE-G14 shortfall, and single-testcase/single-seed limitations
- 4.8 Block 1 Conclusion

Artifact provenance (which `outputs/` and `reports/` files back every figure and
table) is documented in `roadmap.md`, Section 3.2, not inside the manuscript
section.

A nomenclature/SI table opens the section, the v3 subsection includes a
supervised learning-curve figure and a design-rationale table, the validation
subsection adds a model-free persistence baseline, and the v3.5 subsection
reports a `C_zon` convergence-stability band plus an equivalent-thermal-mass
physical interpretation.
