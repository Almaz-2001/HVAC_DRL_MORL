# Results II Controller Learning - Overleaf package

Upload the whole folder `results2_control_overleaf` to Overleaf and compile
`main.tex`.

Recommended compiler:

- `pdfLaTeX`

Contents:

- `main.tex` - standalone Block 2 / Results II LaTeX section (generated).
- `build_results2_overleaf.py` - data-driven generator: regenerates `main.tex`
  with every table and inline KPI read from `reports/`/`outputs/` artifacts.
  Run from the repository root with the project Python environment:
  `python docs/results2_control_overleaf/build_results2_overleaf.py`.
- `figures/` - PDF/PNG figures referenced by `main.tex` (produced by the Block 2
  evaluation scripts; this builder references them and does not regenerate them).

Scientific scope covered in this package:

- PPO training configuration across thermostatic PPO, HDRL, MORL pretrain, and
  MORL finetune.
- 17D TSup-style observation interface, action mapping, and reward definition.
- Hybrid backend mathematics: v3 rollout dynamics plus frozen-v3.5 disagreement
  reward shaping.
- Direct-v3.5 negative control and warm-start negative control.
- Live BOPTEST closed-loop controller comparison for pure v3, direct v3.5, and
  hybrid PPO.
- Transfer-gap diagnostics and action-saturation mechanism.
- Q1-polished controller diagnostics:
  - Closed-loop traces with ambient-temperature disturbance, comfort band, and
    actuator range. Solar irradiance is not drawn because it is not present in
    the stored trace CSVs.
  - Empirical phase-density portraits of normalized action versus temperature
    error. These use observed state-action density rather than an invented
    reward-gradient field.
  - MORL Pareto front with N=5 confidence ellipses for 50/50 and 75/25
    canonical preference points, plus empirical Pareto envelope.
- HDRL lambda sweep and controller-family-specific regularization limit.
- MORL 5D failure, 17D recovery, Pareto sweep, N=5 seed variance, and seasonal
  variance falsification.

All numeric claims are read directly from project artifacts by the builder
(provenance map: `roadmap.md` Section 11.1):

- `outputs/bestest_air_article7_style_15min/summary.csv` (pure v3 PPO)
- `outputs/block2_thermostatic_hybrid_v3_v35_l010/summary.csv` (hybrid)
- `outputs/block2_thermostatic_warmstart_utility/comparison_summary.csv`
- `reports/hou_evins_architecture_justification_table.csv` (direct v3.5 KPIs)
- `reports/hybrid_transfer_comparison.csv` (transfer-gap)
- `reports/block2_hdrl_lambda_sweep_summary.csv`
- `reports/block2_morl_5d_reconstructed_comparison.csv` (current-code 5D rerun)
- `reports/block2_morl_comparison_summary.csv` (17D canonical)
- `reports/morl_pareto_front_table.csv`
- `reports/morl_canonical_seedfix_yearly_summary.csv` and `..._per_seed.csv`
- `outputs/pi_baseline_15min_yearly/pi_yearly_summary.csv` (PI yearly means)

Note: the MORL 5D ablation uses the current-code **reconstructed** 5D rerun
(`m_s = 0.680`), per roadmap Section 6.5; the originally frozen 5D artifact
(`m_s = 1.046`) is retained only as an audit reference and is reported as such.

Structural check: every `\includegraphics` reference resolves inside the local
`figures/` directory, and the section compiles with pdfLaTeX (11 pages,
0 undefined references).
