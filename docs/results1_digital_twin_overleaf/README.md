# Results I Digital Twin Fidelity - Overleaf package

Upload the whole folder `results1_digital_twin_overleaf` to Overleaf and compile
`main.tex`.

Recommended compiler:

- `pdfLaTeX`

Contents:

- `main.tex` - standalone, expanded Block 1 / Results I LaTeX section.
- `figures/` - all PDF figures referenced by `main.tex`.

Scientific scope covered in this package:

- v3 control-oriented surrogate architecture, feature vector, dual-head design,
  parameter count, and training role.
- v3.5 physics-informed surrogate and the Stage A/B/C inverse-calibration
  protocol.
- Stage B excitation filtering and physical identification of `C_zon`.
- Multi-horizon predictive validation, residual diagnostics, and error CDF.
- Matched-corpus control experiment separating data-resolution effects from
  calibration effects.
- Q1-polished Block 1 diagnostics:
  - Stage B `C_zon` trajectory with a +/-10% physical prior band.
  - Multi-horizon rollout RMSE with 95% bootstrap CI from real
    `window_errors.csv` distributions.
  - Residual distribution, engineering tolerance CDF, and calibrated-v3.5 Q-Q
    inset from real `all_full_rollouts.csv` residuals.
  - Matched-corpus waterfall with explicit corpus-shift and Stage A/B/C
    calibration deltas.
- Backend runtime benchmark and feasibility of surrogate-based PPO training.
- Hybrid backend architecture and mathematical reward-shaping formulation.
- Fidelity-to-RL utility gap.
- Transfer-gap diagnostics and action-saturation mechanism.

Structural check at generation time:

- Figures referenced: 14
- Missing figure files: 0
- Tables: 5
- Equation blocks: 12

This folder is intended as an editable Overleaf source for polishing the
Results I section before reintegration into the main Q1 manuscript.
