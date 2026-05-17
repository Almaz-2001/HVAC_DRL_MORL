# Next Steps

Date: 2026-05-11

## Literature-Review Alignment

This file follows the current article-facing methodology map:

- [literature_review_alignment_block1_block2.md](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/literature_review_alignment_block1_block2.md)
- [hou_evins_compliance_matrix.md](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_compliance_matrix.md)

## Current State Before Block 3

Block 1 is closed for the current paper scope:

- calibrated `v3.5` has explicit `C_zon`
- predictive validity is reported at 1h, 4h, 8h, and 24h
- sample generation, preprocessing, scaling, hyperparameters, feature significance, and input independence are now article-facing artifacts

Block 2 is closed for the current paper scope:

- thermostatic PPO: canonical `hybrid_l010`
- HDRL: canonical `lambda_temp_disagree = 0.00`
- MORL: canonical 17D power-only hybrid path with `lambda_temp_disagree = 0.00` and `lambda_power_disagree = 5e-5`

## Block 3 Entry Condition

Do not reopen surrogate architecture before Block 3 unless a reproducibility bug is found.

Block 3 should test transferability of the already justified method across related BOPTEST cases.

## Block 3 Planning Target

The next plan should define:

1. which related testcases are selected
2. which controller family is promoted first
3. whether the transferred backend uses full recalibration, partial recalibration, or no recalibration
4. which metrics decide transfer success

The minimum Block 3 success table should include:

- testcase
- controller family
- surrogate backend
- recalibration mode
- `m_s`
- violation percentage
- energy
- rollout/predictive validity metric
- transfer gap metric

## Claim Boundary

Block 3 can support transferability only if it compares against alternatives.

Do not claim universal surrogate transfer from a single additional testcase. The defensible target is narrower:

**The hybrid physical-regularization recipe can transfer across related HVAC/building dynamics when recalibration and controller-interface assumptions are made explicit.**
