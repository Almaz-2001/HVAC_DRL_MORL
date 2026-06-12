# Cover letter — Results in Engineering

*(Paste into the Editorial Manager "Cover Letter" field or upload as PDF.
Replace the bracketed placeholders before submitting.)*

---

Dear Editor,

We are pleased to submit our manuscript, **"The Fidelity–Utility Paradox in
Surrogate-Based Reinforcement Learning for HVAC Control"**, for consideration in
*Results in Engineering*.

Deep reinforcement-learning HVAC controllers are usually trained on fast neural
surrogates under an assumption so common it is rarely stated: that a more accurate
surrogate is a better training environment. Our manuscript tests this assumption
directly on the BOPTEST `bestest_air` benchmark and reports a verified negative
result — the **fidelity–utility paradox**: the surrogate with the lower predictive
error can be the *worse* environment for policy-gradient training. A calibrated
grey-box twin (24 h rollout RMSE 0.644 °C) trains an unusable controller, while a
weaker black-box surrogate (1.557 °C) trains a usable one. Crucially, we close the
obvious confound with a matched-configuration control experiment: retraining the
*same* black-box architecture at the finer control resolution makes it strictly
more accurate yet collapses downstream control, isolating a fidelity/smoothing
trade-off rather than a model-class effect. We then show one engineering resolution
— a role-separating hybrid (black-box rollout dynamics plus a frozen physical twin
as a reward-shaping censor) that achieves sub-5 % comfort violation at ~85× live
simulator throughput — and a component-level transferability boundary on three
hydronic testcases (the inverse-calibration pipeline transfers; the frozen policy
does not transfer uniformly).

We believe the work fits *Results in Engineering* well: it is a rigorous,
application-grounded engineering result whose value lies in correcting a working
assumption that current surrogate-building protocols optimise for, and in
providing actionable design guidance (evaluate surrogates by downstream control
utility, not predictive accuracy alone). The manuscript is organised as a
self-contained main text carrying the scientific argument and key evidence, with
the full parameterisation, diagnostics, and per-artifact provenance placed in the
accompanying supplementary material.

A methodological feature we wish to highlight is the verifiability of the evidence
chain. All claims are version-locked: hypotheses and pass/fail rules were committed
to source control *before* the corresponding runs, and the audit anchors are
published as Git tags in the open repository accompanying the paper
(https://github.com/Almaz-2001/HVAC_fidelity-utility-paradox), together with the
code, configurations, trained controller checkpoints, and per-figure provenance
maps that regenerate every number, figure, and table in the manuscript. The use of
a generative-AI writing assistant is disclosed in the manuscript in accordance
with Elsevier policy; all experiments, data, and scientific claims are the
authors' own.

This manuscript is original, has not been published previously, and is not under
consideration by any other journal. All authors have approved the submission and
declare no competing interests.

Thank you for your consideration. We look forward to the reviewers' feedback.

Sincerely,

[Corresponding Author Name]
[Affiliation, City, Country]
[email] · ORCID: [xxxx-xxxx-xxxx-xxxx]
On behalf of all authors
