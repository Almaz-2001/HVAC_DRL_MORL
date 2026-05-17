# Hou and Evins Q1 Gap Closure Notes

Date: 2026-05-11

## Excitation-Window Rationale

The v3.5 inverse task is not trained on uniformly sampled state-action space. It uses scenario-stratified BOPTEST trajectories and then selects the high-information part of the trajectory for Stage B/C calibration. In the canonical 15-minute branch, the excitation selector used mode `dt_only`, quantile `0.95`, threshold `0.17591008724402604`, and retained `403` excitation rows from `8058` training rows.

This is deliberate: `C_zon` is identifiable only when the zone temperature is moving enough for the heat-balance residual to carry signal. Low-dynamics comfort-holding periods are useful for controller evaluation, but they are weak evidence for inverse thermal-capacitance estimation. The selected rows had mean excitation score `0.23963650405419015` versus `0.06923519485638069` over the full training split.

## Scenario Stratification Instead Of LHS

Hou and Evins recommend space-filling designs such as Latin hypercube sampling when the surrogate is meant to approximate a broad static input-output map. This project uses a control-oriented surrogate: the relevant distribution is the closed-loop distribution induced by feasible HVAC policies, not a uniform distribution over all mathematical inputs. Therefore, the current sampling is scenario-stratified by BOPTEST operating windows and controller families. This preserves physically reachable state-action transitions and makes the supervised data closer to the RL deployment distribution.

## Input Independence Check

The independence check is reported in `reports/hou_evins_input_independence_table.csv`. The only pair flagged as `high_dependency_review_required` is `day_sin` versus `day_cos`. This is expected for a restricted seasonal subset: sine and cosine are both deterministic encodings of the same calendar variable, and a narrow day-of-year range can make them strongly correlated. They are retained because the pair is needed to avoid a seasonal discontinuity in the full annual representation.

## Replicative Versus Predictive Validity Boundary

Replicative validity is reported through one-step calibration metrics in `calibration_summary_boptest_v35.json`: calibrated temperature RMSE `0.23325452208518982` C and calibrated power MAE `482.0337829589844` W.

Predictive validity is now reported separately in `reports/hou_evins_predictive_validity_table.csv` at 1h, 4h, 8h, and 24h horizons for `v3`, `v3.5_calibrated`, and `hybrid_l010`.
