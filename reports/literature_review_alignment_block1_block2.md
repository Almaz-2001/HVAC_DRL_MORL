# Literature Review Alignment for Block 1 and Block 2

Date: 2026-05-11

## Source

This note connects the current project results to the literature-review protocol stored in:

- [Literature review source text](C:/Users/user/Desktop/HVAC_DRL_MORL/main_Article/_lit_review.txt)
- [Literature review document](C:/Users/user/Desktop/HVAC_DRL_MORL/main_Article/Literature%20review.docx)

The relevant article is Hou and Evins (2024), which frames NN-based surrogate development as a four-stage process:

1. sample generation
2. data processing
3. NN-based surrogate training
4. surrogate validation

The same review also separates two quality axes:

- reporting level: whether enough implementation detail is provided for reproduction
- justification level: whether modeling choices are numerically justified rather than only discussed

## Block 1 Mapping: Surrogate Fidelity

Block 1 is our direct response to the surrogate-development protocol.

| Hou-Evins requirement | Our Block 1 artifact | Current status |
| --- | --- | --- |
| Output-variable selection | `T_zone_next` and `P_total` are the two supervised surrogate outputs. | Closed. These are the minimum variables needed for comfort and energy control. |
| Input-variable selection | `t_zone`, `t_amb`, time features, direct-TSup actions, power/history encodings. | Closed through ablation and independence artifacts. |
| Significance check | [hou_evins_feature_justification_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_feature_justification_table.csv) | Closed. |
| Independence check | [hou_evins_input_independence_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_input_independence_table.csv) | Closed. The expected `day_sin`/`day_cos` dependency is explained, not treated as a feature error. |
| Sample-generation ranges and distributions | [hou_evins_sample_generation_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_sample_generation_table.csv) | Closed. |
| Sample-size justification | [hou_evins_sample_size_justification_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_sample_size_justification_table.csv) | Closed. |
| Preprocessing | [hou_evins_stage_a_processing_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_stage_a_processing_table.csv) | Closed. |
| Scaling | [hou_evins_scaling_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_scaling_table.csv) | Closed. |
| Training hyperparameters | [hou_evins_training_hyperparams_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_training_hyperparams_table.csv) | Closed. |
| Architecture justification | [hou_evins_architecture_justification_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_architecture_justification_table.csv) | Closed by comparing `v3`, `v3.5`, and `hybrid_l010`. |
| Replicative validity | `calibration_summary_boptest_v35.json` and Block 1 report. | Closed. |
| Predictive validity | [hou_evins_predictive_validity_table.csv](C:/Users/user/Desktop/HVAC_DRL_MORL/reports/hou_evins_predictive_validity_table.csv) | Closed with explicit claim boundary. |

The strongest Block 1 result is not that every surrogate variant is good for control. The result is more precise:

**Calibrated `v3.5` is physically and predictively stronger than raw `v3.5` and pure `v3`, but it is not by itself a zero-shot closed-loop controller-training environment.**

That distinction follows the literature-review separation between predictive validity and downstream task validity.

## Block 2 Mapping: Controller Utility

Block 2 extends the literature-review logic from surrogate fidelity into downstream control utility.

| Controller family | Literature-review question | Result |
| --- | --- | --- |
| Thermostatic PPO | Does physical regularization numerically improve the control-oriented surrogate branch? | Yes. `hybrid_l010` is the canonical result. |
| HDRL | Does the same regularization transfer to a hierarchical controller? | No. HDRL rejects temperature disagreement regularization and performs best at `lambda_temp_disagree=0.00`. |
| MORL | Can the hybrid backend support the target multi-objective controller family? | Yes, but only after moving from the failed 5D observation path to the 17D TSup-style observation path. |

This produces the core Block 2 conclusion:

**Hybrid regularization is not universal across controller families. It is useful when calibrated to the controller interface and reward geometry.**

## Numerical Justification Now Available

The literature review emphasizes Level-3 numerical justification. The current project now has numerical artifacts for:

- feature significance
- input independence
- sample size
- split representativeness
- scaling
- training hyperparameters
- architecture comparison
- lambda sensitivity for thermostatic PPO
- lambda sensitivity for HDRL
- MORL observation-interface ablation
- predictive validity horizons at 1h, 4h, 8h, and 24h

Therefore the paper should avoid a vague claim like:

**"We designed a better surrogate."**

The defensible claim is:

**We show that a calibrated physical layer improves surrogate validity and can act as a useful soft regularizer for downstream HVAC control, but its benefit depends on the controller family and observation interface.**

## Current Claim Boundary Before Block 3

What we can claim now:

- `v3.5` closes the physical-validity gap through explicit `C_zon`.
- `v3.5_calibrated` is the best standalone predictive model in the current prepared rollout table.
- `hybrid_l010` is the canonical thermostatic control result.
- HDRL and MORL require `lambda_temp_disagree=0.00`, keeping only the soft power/energy regularization.
- MORL succeeds only with the 17D TSup-style observation path.

What we cannot claim yet:

- universal transfer across different buildings or HVAC testcases
- formal HPO
- that the hybrid is the best free-run predictor
- that a single `lambda_temp_disagree` value works for all controller families

## Implication For Block 3

Block 3 should not start by changing the surrogate again. It should test whether the already justified method transfers across related testcases.

The Block 3 plan should therefore freeze:

- Block 1 surrogate evidence standard
- Block 2 controller-family-specific settings
- Hou-Evins numerical reporting artifacts

Then Block 3 can vary the testcase/building dynamics and measure transferability.
