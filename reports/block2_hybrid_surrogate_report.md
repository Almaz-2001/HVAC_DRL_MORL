# Block 2 Hybrid Surrogate Snapshot

Date: 2026-04-28

## Canonical Hybrid Setup

- training dynamics: `v3`
- physics regularizer: `v3.5 disagreement penalty`
- controller family: `thermostatic PPO`
- comfort band: `21-24 C`
- step size: `900 s`
- `lambda_temp_disagree = 0.10`
- `lambda_power_disagree = 5e-5`

Literature-review alignment:

- This result is the Block 2 numerical-justification step for the hybrid controller branch, following the Hou-and-Evins requirement that modeling choices be justified by comparison rather than discussion alone.
- It should be read together with [literature_review_alignment_block1_block2.md](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/literature_review_alignment_block1_block2.md) and [hou_evins_predictive_validity_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_predictive_validity_table.csv).
- Important claim boundary: `hybrid_l010` is not claimed as the best free-run predictor; its value is downstream control regularization using calibrated `v3.5` as a physical censor.

## Main Result

The canonical hybrid branch uses `lambda_temp_disagree = 0.10`.

It is materially better than the failed direct `v3.5` warm-start path, and it gives the best overall tradeoff among the tested hybrid penalty values.

### Hybrid thermostatic on live BOPTEST

| scenario | m_s | violation_pct | rmse_center_c | energy_kwh |
| --- | ---: | ---: | ---: | ---: |
| peak_heat_window | 0.0866 | 4.69 | 0.795 | 305.3 |
| typical_heat_window | 0.0411 | 2.38 | 0.633 | 352.8 |

### Context against pure `v3` thermostatic

| scenario | v3 m_s | hybrid m_s | hybrid delta | v3 energy_kwh | hybrid energy_kwh |
| --- | ---: | ---: | ---: | ---: | ---: |
| peak_heat_window | 0.0725 | 0.0866 | 0.0141 | 322.2 | 305.3 |
| typical_heat_window | 0.0947 | 0.0411 | -0.0536 | 368.3 | 352.8 |

### Context against failed direct `v3.5` warm-start

| scenario | warm-start m_s | hybrid m_s | relative improvement |
| --- | ---: | ---: | ---: |
| peak_heat_window | 1.2701 | 0.0866 | 93.2% |
| typical_heat_window | 1.2888 | 0.0411 | 96.8% |

### Canonical interpretation of `lambda = 0.10`

- On `peak_heat_window`, the hybrid nearly matches pure `v3` comfort while using less energy.
- On `typical_heat_window`, the hybrid is better than pure `v3` on `m_s`, violation, and energy, with only a small RMSE penalty.
- Therefore `lambda = 0.10` is the current default hybrid setting for transfer to the next controller family.

## Interpretation

- The hybrid regularizer is useful: it rescues the `v3.5` branch from catastrophic Block 2 performance.
- The `0.10` setting is the current best compromise, not just a proof of concept.
- The downstream promotion has now been measured: `HDRL` rejects temperature disagreement regularization, while `MORL` succeeds only on the 17D power-only hybrid branch.
- The next research question is Block 3 cross-case transferability, not more thermostatic tuning.

## Figures

![Hybrid comfort traces](figures/hybrid_boptest_comfort_traces.png)

![Hybrid power and cumulative energy](figures/hybrid_boptest_power_energy_traces.png)

![Hybrid vs PI m_s](figures/hybrid_vs_pi_ms.png)

![Hybrid vs PI violation](figures/hybrid_vs_pi_violation.png)

![Hybrid vs PI energy](figures/hybrid_vs_pi_energy.png)
