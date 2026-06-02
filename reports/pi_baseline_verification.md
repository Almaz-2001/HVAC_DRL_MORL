# PI Baseline Verification

## Status

The yearly PI baseline in `outputs/pi_baseline_15min_yearly/pi_yearly_summary.csv` is matched to the MORL yearly-validation protocol used in `evaluation/yearly_validation_morl.py`.

## Matched Items

| Item | PI yearly | MORL yearly | Status |
|---|---|---|---|
| BOPTEST URL | `http://web:8000` | `http://web:8000` | matched |
| Testcase | `bestest_air` | `bestest_air` | matched |
| Control step | `900 s` | `900 s` | matched |
| Scenario length | `14 days` | `14 days` | matched |
| Scenario starts | Jan-Dec monthly starts | Jan-Dec monthly starts | matched |
| Comfort lower bound | `21 C` | `21 C` | matched |
| Comfort upper bound | `24 C` | `24 C` | matched |
| RMSE target | `22 C` | `22 C` | matched |
| Energy integration | `sum(power) * step_sec / 3600 / 1000` | same | matched |
| Safety metric | `r_time + max(r_severity)` | same | matched |

## PI Control Path

The yearly PI script sends an empty action dictionary to BOPTEST:

```text
advance(testid, {})
```

This is the same control path used by `PIController` in `evaluation/benchmark_bestest_air_article7_style.py`, where `PIController.act(...)` returns `None` and the benchmark sends `{}` to `/advance`.

Therefore, the yearly PI result should be interpreted as the built-in/default BOPTEST control reference, not as a custom-retuned PI controller.

## Result

| Baseline | RMSE | Violation | Energy | m_s |
|---|---:|---:|---:|---:|
| PI yearly mean | 3.395 | 63.59% | 104.07 kWh | 0.9102 |

## Interpretation Boundary

This PI baseline is weak over the 12 seasonal 14-day yearly windows. The paper should not overstate the result as proof that RL universally dominates tuned PI control. A defensible phrasing is:

> The built-in BOPTEST PI controller is retained as the standard rule-based reference. Over the yearly seasonal windows it provides low energy use but poor comfort tracking, indicating that it is not a strong custom-tuned baseline for this protocol.

If reviewers ask for a stronger rule-based baseline, the response should be to add a custom-tuned PI/MPC baseline rather than to reinterpret this built-in PI result.
