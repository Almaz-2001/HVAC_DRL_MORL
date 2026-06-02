# Speed Benchmark Interpretation

## Purpose

This benchmark provides the computational justification for using the local surrogate backend as the reinforcement-learning training environment. The comparison is intentionally conservative: the local surrogates are compared against the same live BOPTEST RTE HTTP loop used for closed-loop validation, not against a bare FMU or an optimized simulator API.

The benchmark measures environment-step throughput, not full PPO wall-clock training time. Therefore, the result should be reported as an environment stepping speed-up. A separate training wall-clock benchmark would be required to claim that policy training itself is 85.0x faster.

## Protocol

- Testcase: `bestest_air`
- Control step: `900 s` / `15 min`
- Budget: `100 episodes x 96 steps = 9600 environment steps`
- Hardware mode: CPU, single PyTorch thread
- BOPTEST endpoint: `http://web:8000`
- BOPTEST metric includes: testcase selection, step setup, initialization, HTTP advances, and stop calls in the amortized episode timing
- Surrogate metric includes: in-process Python rollout with model inference; model loading and warmup are excluded

## Results

| Backend | Status | Steps | Total time (s) | Steps/s | Mean raw step (ms) | P95 raw step (ms) | Mean episode time (s) | Speed-up vs BOPTEST RTE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BOPTEST RTE HTTP | ok | 9600 | 456.856 | 21.013 | 15.335 | 19.251 | 4.569 | 1.0x |
| v3 surrogate | ok | 9600 | 2.075 | 4626.350 | 0.187 | 0.273 | 0.021 | 220.2x |
| v3.5 calibrated surrogate | ok | 9600 | 4.001 | 2399.530 | 0.386 | 0.495 | 0.040 | 114.2x |
| hybrid v3 + v3.5 surrogate | ok | 9600 | 5.373 | 1786.798 | 0.527 | 0.648 | 0.054 | 85.0x |

Source table: `reports/speed_benchmark_table.csv`.

## Interpretation

The v3 surrogate is the fastest backend because it evaluates only the smooth data-driven dynamics. The calibrated v3.5 surrogate is slower because it evaluates the physical-twin structure. The hybrid backend is the slowest local surrogate because it evaluates the v3 dynamics and the frozen calibrated v3.5 model to compute disagreement signals. This extra cost is expected and is part of the physical-regularization mechanism.

Even with that extra computation, the canonical hybrid backend executes `1786.8` environment steps per second, which is `85.0x` faster than the live BOPTEST RTE HTTP loop under the same 15 min control protocol.

## Recommended Abstract Sentence

The calibrated hybrid backend executed `1786.8` environment steps per second on a single CPU thread, corresponding to an `85.0x` environment-step speed-up over the live BOPTEST RTE HTTP loop under the same 15 min control protocol.

## Recommended Methods Wording

We benchmarked the computational throughput of the live BOPTEST RTE HTTP loop and the local surrogate backends under an identical 15 min control protocol. Each backend was evaluated for 100 episodes of 96 steps, corresponding to 9600 environment transitions. The live BOPTEST timing includes HTTP calls and testcase lifecycle overhead, while surrogate timing measures in-process model stepping after model loading and warmup. We report this as environment-step throughput rather than full policy-training wall-clock time.

## Limitations

- This benchmark does not measure full PPO wall-clock training time, which also includes rollout storage, policy inference, gradient updates, logging, checkpointing, and vectorized-environment overhead.
- The BOPTEST row measures the RTE HTTP workflow used in this project. It should not be interpreted as the maximum possible FMU stepping speed.
- The surrogate rows exclude model loading and warmup because those costs are paid once per training process, not once per environment step.
- The hybrid surrogate speed-up is lower than the v3 speed-up because the hybrid backend computes both the primary v3 transition and the calibrated v3.5 disagreement channel.

## Claim Boundary

Allowed claim:

> The hybrid surrogate provides an 85.0x environment-step throughput speed-up over the live BOPTEST RTE HTTP loop.

Do not claim without an additional benchmark:

> The hybrid surrogate reduces total PPO training wall-clock time by 85.0x.
