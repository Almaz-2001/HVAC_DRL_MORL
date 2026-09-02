# Cover letter — Results in Engineering

*(Paste into the Editorial Manager "Cover Letter" field or upload as PDF.
Replace the bracketed placeholders before submitting.)*

---

Dear Editor,

We are pleased to submit our manuscript, **"The Fidelity–Utility Paradox in Surrogate-Based Reinforcement Learning: A Role-Separated Hybrid Methodology in an HVAC Control Case Study"**, for consideration in
*Results in Engineering*.

Deep reinforcement-learning HVAC controllers are usually trained on fast neural
surrogates under an assumption so common it is rarely stated: that a more accurate
surrogate is a better training environment. Our manuscript tests this assumption
directly on the BOPTEST `bestest_air` benchmark and reports a verified negative
result, the **fidelity–utility paradox**: the surrogate with the lower predictive
error can be the *worse* environment for policy-gradient training. A calibrated
grey-box twin (24 h rollout RMSE 0.644 °C) trains an unusable controller, while a
weaker black-box surrogate (1.557 °C) trains a usable one. Crucially, we close the
obvious confound with a matched-configuration control experiment: retraining the
*same* black-box architecture at the finer control resolution makes it strictly
more accurate yet collapses downstream control, isolating the surrogate's coarse
per-step increment (temporal coarseness), not its model class, as the driver. We then show one engineering resolution:
a role-separating hybrid (black-box rollout dynamics plus a frozen physical twin as a model-disagreement reward censor) that achieves sub-5 % comfort violation at ~85× live
simulator throughput, and a component-level transferability boundary on three
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
chain. The transferability hypotheses and their pass/fail thresholds were
pre-specified before the corresponding runs, and the supplementary material
provides content-to-artefact provenance maps that trace every reported number,
figure, and table back to its source. A complete reproducibility package (the
code, configurations, trained controller checkpoints, and the per-figure provenance
maps that regenerate all results without a live simulator) is available to the
editor and reviewers on reasonable request; the full project codebase is not
publicly released at this stage. The use of a generative-AI writing assistant is
disclosed in the manuscript in accordance with Elsevier policy; all experiments,
data, and scientific claims are the authors' own.

This manuscript is original, has not been published previously, and is not under
consideration by any other journal. All authors have approved the submission and
declare no competing interests. This research was funded by the Committee of Science
of the Ministry of Science and Higher Education of the Republic of Kazakhstan
(Grant No. AP23488794).

Thank you for your consideration. We look forward to the reviewers' feedback.

Sincerely,

Almaz Sapargali (corresponding author)
LLP Digit Alem, Almaty, Kazakhstan; Al-Farabi Kazakh National University, Almaty, Kazakhstan
almaz.sapargali2001@gmail.com · ORCID: 0009-0003-1521-7149
On behalf of all authors
