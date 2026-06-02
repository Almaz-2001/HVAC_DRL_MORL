# Hou and Evins Compliance Matrix

Date: 2026-05-11

## Purpose

This document maps the current project state to the Hou and Evins methodology requirements for NN-based surrogate models in buildings.

Literature-review source:

- [main_Article/_lit_review.txt](C:/Users/user/Desktop/HVAC_DRL_MORL/main_Article/_lit_review.txt)
- [literature_review_alignment_block1_block2.md](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/literature_review_alignment_block1_block2.md)

Status labels:

- `closed`: evidenced by explicit numerical artifacts or frozen reports
- `partial`: engineering work exists, but article-facing evidence is incomplete
- `open`: still missing as a paper requirement

## 1. Sample Generation

| requirement | status | current project state | what is still missing |
| --- | --- | --- | --- |
| Explicit description of sample-generation pipelines | closed | The pipelines are frozen in [hou_evins_sample_generation_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_sample_generation_table.csv), covering the hourly `v3` direct-TSup corpus, prepared 15-minute bootstrap corpus, and collected 15-minute exploration corpus. | Nothing essential beyond article prose. |
| Range and distribution reporting | closed | [hou_evins_sample_generation_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_sample_generation_table.csv) reports rows, episodes, step size, controller/policy mix, scenario/season mix, and temperature/power ranges. | Optional figure only. |
| Significance and independence of inputs | closed | Significance is supported by [hou_evins_feature_justification_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_feature_justification_table.csv). Independence is now supported separately by [hou_evins_input_independence_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_input_independence_table.csv), which reports pairwise Pearson correlation and normalized mutual information over the canonical prepared 15-minute BOPTEST corpus. The expected `day_sin`/`day_cos` dependency is explained in [hou_evins_q1_gap_closure.md](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_q1_gap_closure.md). | Nothing essential for the current surrogate paper package. |
| Sample-size justification | closed | The cost-vs-accuracy dataset choice is explicit in [hou_evins_sample_size_justification_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_sample_size_justification_table.csv). | Nothing essential beyond article prose. |
| Excitation-window logic | closed | The inverse-calibration excitation-window rationale is now stated in [hou_evins_q1_gap_closure.md](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_q1_gap_closure.md), with the canonical excitation statistics from `outputs/surrogate_v35_inverse_boptest_15min_power_head_only/excitation_summary.json`. | Nothing essential beyond carrying the paragraph into the paper method section. |
| Scenario-stratified sampling versus LHS | closed | [hou_evins_q1_gap_closure.md](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_q1_gap_closure.md) explicitly justifies scenario-stratified BOPTEST sampling instead of Latin hypercube sampling for a control-oriented closed-loop surrogate. | Nothing essential unless reviewers request a formal LHS baseline. |

## 2. Data Processing

| requirement | status | current project state | what is still missing |
| --- | --- | --- | --- |
| Stage A preprocessing documented | closed | Stage A is documented in [hou_evins_stage_a_processing_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_stage_a_processing_table.csv), including latency search, temperature bias removal, power affine normalization, rolling denoise, and causal delta recomputation. | Nothing essential beyond method-section prose. |
| Feature encoding justified numerically | closed | The ablation and encoding decisions are summarized in [hou_evins_feature_justification_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_feature_justification_table.csv). | Nothing essential for the current surrogate package. |
| Scaling and normalization reported | closed | Scaling is now explicit in [hou_evins_scaling_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_scaling_table.csv), covering surrogate inputs, controller observations, power clipping/log transform, delta-temperature encoding, and positive `C_zon` parameterization. | Nothing essential. |
| Train/val/test split strategy | closed | Split logic is frozen in [hou_evins_split_representativeness_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_split_representativeness_table.csv), including contiguous split for legacy `v3`, episode-aware split for canonical `v3.5`, and external BOPTEST testing for downstream control claims. | Nothing essential beyond article prose. |
| Representativeness of splits | closed | [hou_evins_split_representativeness_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_split_representativeness_table.csv) states where coverage is broad, where it is limited, and how external rollout/transfer benchmarks compensate. | Nothing essential for the current branch. |

## 3. NN-Based Surrogate Training

| requirement | status | current project state | what is still missing |
| --- | --- | --- | --- |
| Training hyperparameters reported | closed | [hou_evins_training_hyperparams_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_training_hyperparams_table.csv) reports the active v3 training entrypoint, learning rate, batch size, optimizer, weight decay, epoch budget, early stopping, scheduler, checkpoint metric, gradient clipping, and loss weights. | Nothing essential. |
| Numerical justification for architecture | closed | [hou_evins_architecture_justification_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_architecture_justification_table.csv) compares `v3`, `v3.5`, and `hybrid_l010` across fidelity, transfer behavior, and downstream control KPI. | Nothing essential beyond article prose. |
| Formal HPO | closed by explicit non-claim | [hou_evins_final_open_items_closure.md](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_final_open_items_closure.md) and [hou_evins_targeted_sensitivity_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_targeted_sensitivity_table.csv) state that the paper claims targeted sensitivity analysis, not formal HPO. | Keep this claim boundary explicit in the paper. |
| Stage B/C training rationale | closed | The staged `v3.5` calibration identifies `C_zon` first and then calibrates heads, preventing the flexible network from absorbing physical mismatch without interpretable structure. | Method prose only. |
| Prevention of network cheating | closed | The move from black-box `v3` to structured `v3.5` and then to `hybrid_l010` is documented as the main anti-cheating mechanism. | Method prose only. |

## 4. Surrogate Validation

| requirement | status | current project state | what is still missing |
| --- | --- | --- | --- |
| Replicative validity: one-step accuracy | closed | One-step calibration metrics are reported in `outputs/surrogate_v35_inverse_boptest_15min_power_head_only/calibration_summary_boptest_v35.json` and summarized in [hou_evins_q1_gap_closure.md](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_q1_gap_closure.md). | Nothing major beyond table formatting in the paper. |
| Predictive validity: rollout realism | closed with explicit claim boundary | [hou_evins_predictive_validity_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_predictive_validity_table.csv) now compares `v3`, `v3.5_calibrated`, and `hybrid_l010` at 1h, 4h, 8h, and 24h using `RMSE_T`, `MAE_T`, `R2_T`, `RMSE_P`, and `MAE_P`. Important boundary: `hybrid_l010` uses `v3` as primary rollout dynamics, so its free-run predictive metrics intentionally match `v3`; the `v3.5` component acts as a physical regularizer during control training, not as the primary rollout model. | Nothing essential. Do not claim that `hybrid_l010` is a better free-run predictor than calibrated `v3.5`; claim improved control tradeoff under physical regularization. |
| Transfer validity: `first_divergence_step`, `action_gap_norm` | closed for thermostatic | Transfer evidence is in [hybrid_transfer_comparison.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hybrid_transfer_comparison.csv). | Repeat the same reporting standard for `HDRL` and `MORL` as separate branches. |
| Physical validity: `C_zon` correctness | closed | Canonical Block 1 `C_zon` result is stable at approximately `4.413e5 J/K`, documented in v3.5 calibration outputs and reports. | Final article presentation only. |
| Disagreement summary for hybrid | closed | [hybrid_disagreement_summary.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hybrid_disagreement_summary.csv) documents the disagreement behavior of the hybrid regularizer. | Nothing essential for the thermostatic branch. |

## Strongest Current Claim

The surrogate-method package now satisfies the core Hou-and-Evins article-facing requirements for the current branch: sample generation, preprocessing, feature significance, input independence, scaling, training hyperparameters, architecture comparison, physical validity, predictive validity, transfer validity, and targeted sensitivity analysis.

The scientifically correct claim is:

**The calibrated `v3.5` layer improves physical and predictive validity, while `hybrid_l010` uses that layer as a soft physical regularizer to improve downstream control tradeoffs without replacing the `v3` rollout dynamics.**

## Remaining Work

The remaining work is not another surrogate. It is promotion of this same compliance standard to controller-family branches:

1. create an HDRL compliance matrix and controller-facing numerical artifacts
2. create a MORL compliance matrix and controller-facing numerical artifacts
3. keep the formal-HPO boundary explicit unless a reviewer forces an Optuna/Bayesian-search supplement
