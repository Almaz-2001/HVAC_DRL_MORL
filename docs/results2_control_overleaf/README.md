# Results II Controller Learning - Overleaf package

Upload the whole folder `results2_control_overleaf` to Overleaf and compile
`main.tex`.

Recommended compiler:

- `pdfLaTeX`

Contents:

- `main.tex` - standalone, expanded Block 2 / Results II LaTeX section.
- `figures/` - PDF figures referenced by `main.tex`.

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

All numeric claims are taken from the project artifacts:

- `docs/block2_complete_results.txt`
- `reports/hybrid_transfer_comparison.csv`
- `reports/block2_hdrl_lambda_sweep_summary.csv`
- `reports/block2_morl_comparison_summary.csv`
- `reports/morl_pareto_front_table.csv`
- `reports/morl_canonical_seedfix_yearly_per_seed.csv`
- `reports/morl_canonical_seedfix_yearly_summary.csv`
- `reports/morl_seasonal_variance_inversion_table.csv`
- `reports/hybrid_disagreement_summary.csv`

Structural check should verify that every `\includegraphics` reference resolves
inside the local `figures/` directory before upload.
