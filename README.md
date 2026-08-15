# HVAC_DRL_MORL

Surrogate selection for reinforcement-learning HVAC control, evaluated on the
open [BOPTEST](https://github.com/ibpsa/project1-boptest) benchmark.

## What this project found

A digital twin used as a training environment for a learning controller is
normally selected by predictive accuracy. **That criterion does not predict
whether the twin produces a usable controller.** On `bestest_air`, the least
accurate surrogate trains the only single-model controller that works, and
making that same surrogate *more* accurate by refining its corpus resolution
moves it from the usable regime into failure:

| Training backend | 24 h rollout RMSE | live `m_s` (typical) | comfort violation |
| --- | ---: | ---: | ---: |
| BB, hourly | 1.557 °C (worst) | **0.095** | 4.4 % |
| BB, 15-min matched | 0.876 °C | 1.211 | 91.4 % |
| GB, calibrated | 0.644 °C (best) | 1.102 | 82.4 % |
| Role-separated hybrid | — | **0.041** | 2.4 % |
| BOPTEST built-in PI | — | 0.910 | 63.6 % |

`m_s > 1` marks a controller that cannot be put into service.

The operative property is the surrogate's **per-step increment magnitude**, not
its accuracy: a Δt-rescaling control that holds scale-free response-surface
roughness fixed reproduces the collapse. Measured relative roughness is 0.169
for the usable hourly BB against 9.4× and 7.9× that for the two failing
backends.

The resolution is **role separation**: the black-box surrogate supplies the
rollout dynamics, and the frozen calibrated grey-box twin acts only as a
forward-only model-disagreement reward censor — never in the rollout, never in
the policy loss.

## Repository layout

```text
envs/          BOPTEST + surrogate backends behind one HTTP contract
surrogate/     BB (black-box) and GB (grey-box RC + neural residual) twins
training/      thermostatic PPO, HDRL, MORL trainers
evaluation/    benchmarks, block runners, figure builders
configs/       training configs and pre-registration manifests (audit anchors)
reports/       compact computed evidence: *.csv, *.json, *.md  (tracked)
paper_artifacts/  canonical paper-facing figures, tables, manifests (tracked)
outputs/       raw run artifacts (gitignored, large)
models/        checkpoints (gitignored, large)
docs/          manuscript sources per target journal
```

`reports/*.csv` is the audit trail: every number in the manuscript traces to a
file there. Bulk `outputs/` and `models/` are regenerable from code + configs
and are deliberately not tracked.

## Reproducing the article state

`roadmap.md` is the command-level path, block by block. Run it inside the
project container (`/app`) with BOPTEST RTE reachable at `http://web:8000`.

```bash
python3 -B evaluation/run_block1.py    # surrogate fidelity
python3 -B evaluation/run_block2.py    # control on bestest_air
python3 -B evaluation/run_block3_surrogate_recalibration.py   # hydronic transfer
```

Seed-replicated HDRL censor-weight sweep (12 cells, ~30 h; resumable):

```bash
python3 -B evaluation/run_hdrl_seed_sweep.py --stage train     --skip-existing
python3 -B evaluation/run_hdrl_seed_sweep.py --stage benchmark --skip-existing
python3 -B evaluation/build_hdrl_seed_band.py
```

Protocol and cost breakdown: `reports/hdrl_seed_sweep_runbook.md`.

## MORL pipeline

The preference-conditioned multi-objective line has its own runner and artifact
layout:

```bash
python training/run_morl_surrogate_pipeline.py --config-dir configs/morl_surrogate_ppo --mode full --seed 42
```

Stages are `pretrain -> finetune -> eval` (`full`), with an adversarial-weight
variant `full_eram`. Artifacts land per seed under
`outputs/morl_surrogate_ppo/seed<N>/`, each with its own `pipeline_manifest.json`.
Command-level detail is in `roadmap.md` §7–§9.

The headline MORL result is an **observation-interface** finding, not a reward
one: widening the observation from 5D instantaneous to 17D forecast-augmented
moves the controller from unusable to usable (RMSE 4.96 → 0.72 °C, violation
74.5 → 4.9 %). Across five seeds the neutral preference point averages
`m_s = 0.187 ± 0.078`, which fails a pre-specified stability test, so this
controller is not yet deployment-stable.

## Evidence discipline

- Hypotheses, pass thresholds and adapters were fixed **before** the
  corresponding runs and committed. The audit anchor chain is in `roadmap.md`
  §16, cross-referenced from `configs/block3_testcase_manifest.yaml` and
  `configs/morl_canonical_selection_log.yaml`. **Those commits must remain
  untouched.**
- Verdicts are reported as they came out: of H1–H4, one is falsified, one
  supported, one falsified on seed-replicated evidence, one partly supported.
- Canonical KPI tables use seed 42; the four central backends, the HDRL sweep
  and MORL additionally carry seed-replication bands.

## Publication status

A full article covering the core of this work was submitted to *Energies*
(MDPI), manuscript `energies-4523055`, and was returned at technical pre-check
as out of scope for that journal rather than on quality. The work is being
ported to *IEEE Access*, whose scope explicitly covers multidisciplinary and
negative results. Per-journal manuscript sources live under `docs/`.

The project codebase is not publicly released at this stage; it is available to
editors and reviewers on request.
