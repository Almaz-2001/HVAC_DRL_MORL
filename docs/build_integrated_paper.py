"""Assemble the three standalone Results sections into one Q1 manuscript skeleton.

It (1) strips each section's standalone scaffolding so it can be \\input into a
single paper without duplicating the global front/back matter, and (2) writes a
master ``paper_combined/main_paper.tex`` skeleton with placeholders for the
non-Results sections.

Stripping per section (the unambiguous duplicates of the global manuscript):
  - the document wrapper (preamble, \\begin/\\end{document}) and \\setcounter,
  - the per-section Nomenclature table  -> one global Nomenclature instead,
  - the per-section Limitations subsection -> global Discussion 8.6,
  - the per-section Conclusion subsection  -> global Conclusion (section 9).

NOT auto-removed: the method-bearing subsections (surrogate math, PPO interface,
metrics, adapter spec). Those are woven into the results prose, so relocating
them into the global Methodology (section 3) / Experimental Setup (section 4) is
left as a manual editorial step; see the TODO markers in the master file.

Usage:
    python docs/build_integrated_paper.py
Each generator also accepts ``--integrated`` to (re)write only its own body.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

DOCS = Path(__file__).resolve().parent
SECTIONS = [
    ("results1_digital_twin_overleaf", "Results I body (Block 1, digital-twin fidelity)"),
    ("results2_control_overleaf", "Results II body (Block 2, control utility)"),
    ("results3_transferability_overleaf", "Results III body (Block 3, transferability)"),
]

# Figures and tables relocated from the main text into the Supplementary Material
# to keep the article focused (target <= 40 pp). Matched by \label, which travels
# with the float so in-text \ref calls still resolve (to Figure S / Table S numbers).
# Only self-contained floats may be moved: anything whose caption \ref/\eqref's a
# label that STAYS in the main text would break the standalone supplementary build
# (e.g. tab:tsup-assumptions is deliberately NOT moved).
SUPP_MOVE_LABELS = {
    # --- parameter / configuration tables ---
    "tab:v3-config", "tab:v3-scaling", "tab:ppo_hparams", "tab:obs17",
    "tab:reward", "tab:adapters",
    # --- Block 1: schematic + calibration-diagnostic floats ---
    # (tab:design-rationale stays: it \ref's ssec:block1-limitations in the main text)
    "fig:v3-learning-curve",
    "fig:physics", "fig:predictive-validity", "fig:episode-replicability",
    "tab:stage-a", "tab:stage-b",
    # --- Block 1: page-trim pass (setup / technical detail) ---
    # (tab:tsup-assumptions stays: it \eqref's eq:tsup-signature in the main text)
    "tab:block1-corpora", "tab:architecture-summary",
    "tab:czon", "tab:multi-horizon", "tab:physics",   # secondary Block-1 detail -> supplementary
    "tab:stage-abc", "fig:speed", "tab:speed",
    # --- Block 2: schematic + diagnostic floats ---
    # fig:hybrid_reward (reward-shaping schematic) demoted to supplementary: the main text
    # now carries the runtime-fidelity feasibility figure (fig:runtime_feasibility) instead.
    "fig:block2_pipeline", "fig:morl_pipeline", 
    # fig:action_phase promoted to MAIN: it is the policy-side "effect" that completes
    # the cause->effect pairing with the surrogate-side mechanism (fig:surface_curves).
    "fig:morl_heatmap", "fig:seasonal_falsification", "fig:transfer_gap",
    "tab:hybrid_sweep", "tab:warmstart", "tab:morl_per_seed",
    # --- Block 2: page-trim pass (scenario detail / diagnostics / HDRL / MORL detail) ---
    "tab:scenarios", "fig:closed_loop_traces", "fig:hdrl_arch", "fig:hdrl_sweep",
    "tab:morl_pareto_seed", "fig:ms_decomp", "tab:hdrl", "fig:morl_pareto",
    "fig:morl5d17d", "tab:transfer", "tab:seed_band", "fig:seed_band",
    # fig:surface_curves promoted to MAIN (the measured mechanism is a headline result);
    # fig:live_kpi (per-metric KPI bars) demoted to supplementary -- the paradox is now
    # carried in main by the fidelity-utility scatter (fig:paradox_scatter).
    "fig:live_kpi",
    # fig:warmstart demoted: warm-start is an auxiliary negative control, not a headline
    # result (the thesis is carried by fig:paradox_scatter + fig:surface_curves + Tables 8/9).
    "fig:warmstart",
    # --- Block 3: schematic + per-regime detail floats ---
    # fig:topology demoted to supplementary (its caption no longer \eqref's the main-text
    # balance, so the standalone supplementary build stays self-contained).
    "fig:topology",
    "fig:protocol", "fig:adapter", "fig:regime_progression", "fig:czon_hypothesis",
    "tab:testcases", "tab:regimes", "tab:primary", "tab:predictions",
    # --- Block 3: page-trim pass (secondary diagnostic figures) ---
    "fig:controller_bar", "fig:stage_abc_gain",
    # fig:heatmap (PASS/FAIL verdict grid) and fig:hypothesis_closure (text-as-image
    # matrix) demoted: the engineering comfort-energy deployment plane (fig:deployment_plane)
    # and the closure table carry these in the main text more rigorously.
    "fig:heatmap", "fig:hypothesis_closure",
}


def extract_supp_tables(body: str):
    """Pull the SUPP_MOVE_LABELS figure/table environments out of a section body.
    Returns (reduced_body, [moved_float_blocks]) preserving in-body order."""
    moved = []

    def repl(m):
        blk = m.group(0)
        lab = re.search(r"\\label\{([^}]+)\}", blk)
        if lab and lab.group(1) in SUPP_MOVE_LABELS:
            moved.append(blk)
            return ""
        return blk

    for env in ("figure", "table"):
        body = re.sub(r"\\begin\{" + env + r"\}.*?\\end\{" + env + r"\}",
                      repl, body, flags=re.DOTALL)
    return body, moved


# Per-figure raw-data provenance, printed as a small line under each figure
# caption ("Data: <path>"). Paths point into the released reports//outputs/ trees
# (file where unambiguous, directory/glob where a figure aggregates several runs).
# None marks a hand-drawn schematic with no underlying dataset.
FIG_DATA = {
    # ---- Block 1 ----
    "fig:block1-chain": None,
    "fig:surrogate-design": None,
    "fig:v3-learning-curve": "outputs/surrogate_v2/train_history_v2.csv",
    "fig:physics": "outputs/surrogate_v35_rollout_prepared_15min_power_head_only/calibrated_v35/all_full_rollouts.csv",
    "fig:stage-abc": "outputs/surrogate_v35_inverse_boptest_15min_episodeaware/stage_b_history_v35.csv",
    "fig:predictive-validity": "outputs/surrogate_v35_rollout_prepared_15min_episodeaware/calibrated_v35/window_errors.csv",
    "fig:episode-replicability": "outputs/surrogate_v35_rollout_prepared_15min_episodeaware/calibrated_v35/episode_summary.csv",
    "fig:matched": "reports/block1_corpus_matched_comparison.csv",
    "fig:speed": "reports/speed_benchmark_table.csv",
    # ---- Block 2 ----
    "fig:block2_pipeline": None,
    "fig:hybrid_reward": None,
    "fig:hdrl_arch": None,
    "fig:morl_pipeline": None,
    "fig:live_kpi": "outputs/block2_*/summary.csv",
    "fig:runtime_feasibility": "reports/speed_benchmark_table.csv",
    "fig:lambda_specificity": "reports/block2_hdrl_lambda_sweep_summary.csv",
    "fig:seed_band": "reports/block2_thermostatic_seed_band.csv",
    "fig:ms_decomp": "outputs/block2_*/summary.csv",
    "fig:closed_loop_traces": "outputs/block2_thermostatic_hybrid_v3_v35_l010/",
    "fig:action_phase": "outputs/block2_thermostatic_hybrid_v3_v35_l010/",
    "fig:warmstart": "outputs/block2_thermostatic_warmstart_utility/comparison_summary.csv",
    "fig:transfer_gap": "reports/hybrid_transfer_comparison.csv",
    "fig:hdrl_sweep": "reports/block2_hdrl_lambda_sweep_summary.csv",
    "fig:morl5d17d": "reports/block2_morl_5d_reconstructed_comparison.csv",
    "fig:morl_pareto": "reports/morl_pareto_front_table.csv",
    "fig:morl_heatmap": "reports/morl_canonical_seedfix_yearly_summary.csv",
    "fig:seasonal_falsification": "reports/morl_canonical_seedfix_yearly_per_seed.csv",
    # ---- Block 3 ----
    "fig:protocol": None,
    "fig:adapter": None,
    "fig:topology": None,
    "fig:heatmap": "reports/block3_transfer_matrix.csv",
    "fig:deployment_plane": "reports/block3_transfer_matrix.csv",
    "fig:controller_bar": "reports/block3_transfer_matrix.csv",
    "fig:regime_progression": "reports/block3_bestest_hydronic_heat_pump_transfer_summary.csv",
    "fig:stage_abc_gain": "reports/block3_transfer_matrix.csv",
    "fig:czon_hypothesis": "reports/block3_transfer_matrix.csv",
    "fig:hypothesis_closure": "reports/block3_transfer_matrix.csv",
}


def annotate_figures(text: str) -> str:
    """Insert a small 'Data: <path>' provenance line under each figure caption."""

    def repl(m):
        blk = m.group(0)
        lab = re.search(r"\\label\{([^}]+)\}", blk)
        if not lab or lab.group(1) not in FIG_DATA:
            return blk
        src = FIG_DATA[lab.group(1)]
        if src:
            note = r"{\footnotesize\itshape Data: " + _artefact_cell(src) + "}"
        else:
            note = r"{\footnotesize\itshape Schematic; not derived from a dataset.}"
        return blk.replace(r"\end{figure}", "\n" + note + "\n\\end{figure}")

    return re.sub(r"\\begin\{figure\}.*?\\end\{figure\}", repl, text, flags=re.DOTALL)


def build_supplementary_tables(relocated) -> str:
    if not relocated:
        return ""
    parts = [
        r"\subsection*{Supplementary figures and tables}",
        r"The following figures and tables provide supporting schematics, "
        r"calibration and controller diagnostics, and detailed per-regime and "
        r"per-seed breakdowns. They are cited from Results~I--III (as Figure~S/"
        r"Table~S references) but are not required to follow the main argument.",
    ]
    parts.extend(relocated)
    return "\n\n".join(parts)


def strip_to_body(tex: str) -> str:
    """Return an \\input-able body: section content only, with the standalone
    nomenclature/limitations/conclusion scaffolding and the document wrapper /
    \\setcounter removed."""
    # 1. keep only what is between \begin{document} and \end{document}
    body = tex.split(r"\begin{document}", 1)[1].split(r"\end{document}", 1)[0]
    # 2. drop the standalone section-counter offset (master controls numbering)
    body = re.sub(r"\\setcounter\{section\}\{\d+\}\s*", "", body)
    # 3. drop the per-section Nomenclature table (first table; unique caption)
    body = re.sub(
        r"\\begin\{table\}\[[A-Za-z!]+\]\s*\\centering\s*\\small\s*\\caption\{Nomenclature.*?\\end\{table\}\s*",
        "", body, flags=re.DOTALL,
    )
    # 4. drop the per-section Limitations subsection (up to the next subsection)
    body = re.sub(r"\\subsection\{Limitations\}.*?(?=\\subsection\{)", "", body, flags=re.DOTALL)
    # 5. drop the per-section Conclusion subsection (to the end of the body)
    body = re.sub(r"\\subsection\{[^}]*[Cc]onclusion\}.*\Z", "", body, flags=re.DOTALL)
    return body.strip() + "\n"


def write_body(section_dir: str) -> Path:
    d = DOCS / section_dir
    tex = (d / "main.tex").read_text(encoding="utf-8")
    out = d / "section_body.tex"
    header = (
        "% Auto-generated by docs/build_integrated_paper.py -- do not edit by hand.\n"
        "% Standalone scaffolding (preamble, nomenclature, limitations, conclusion,\n"
        "% \\setcounter) stripped for \\input into the combined manuscript.\n"
    )
    out.write_text(header + strip_to_body(tex), encoding="utf-8")
    return out


MASTER = r"""\documentclass[a4paper,fleqn]{cas-sc}

% cas-sc already loads amsmath, amssymb, array, booktabs, graphicx, hyperref,
% xcolor, etc.; only the extra packages our bodies need are added here.
\usepackage[numbers,sort&compress]{natbib}
\usepackage{siunitx}
\usepackage{tabularx}
\usepackage{longtable}
\usepackage{enumitem}
% NB: do NOT load the float package here. The CAS class redefines the figure/table
% environments via expl3 and parses the optional [...] as a key-value list; loading
% float on top hijacks \@float and forces every float to the document end. Placement
% is controlled through the CAS pos key instead (see [pos={!ht}] in the bodies).
\usepackage{placeins}
\graphicspath{{figures/}}

% Macros shared by all three Results bodies (their own \newcommand lines were
% stripped with the section preambles).
\newcommand{\RMSE}{\ensuremath{\mathrm{RMSE}}}
\newcommand{\MAE}{\ensuremath{\mathrm{MAE}}}
\newcommand{\Czon}{\ensuremath{C_{\mathrm{zon}}}}
\newcommand{\Tsupply}{\ensuremath{T_{\mathrm{sup}}}}
\newcommand{\That}{\ensuremath{\widehat{T}}}
% fixed pointer to a float in the separate Supplementary Material PDF
\newcommand{\suppref}[1]{#1}

\begin{document}
\let\WriteBookmarks\relax

\shorttitle{The Fidelity--Utility Paradox in Surrogate-Based RL for HVAC Control}
\shortauthors{Sapargali et~al.}   % TODO: adjust if author order/corresponding author differs

\title[mode=title]{The Fidelity--Utility Paradox in Surrogate-Based Reinforcement Learning for HVAC Control}

% ============================ AUTHORS — FILL IN ============================
% Replace <...> with real data. Add one \author{} block per co-author (and a
% matching \affiliation[n]{} if their institution differs). The \cormark/\cortext
% mark the corresponding author. Keep this consistent with CITATION.cff and the
% CRediT statement near the end of the file.
\author[1]{Almaz Sapargali}[orcid=<XXXX-XXXX-XXXX-XXXX>]
\cormark[1]
\ead{<corresponding.email@institution>}
\credit{Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Data curation, Writing -- original draft, Writing -- review and editing, Visualization}
% --- co-author template (uncomment and duplicate as needed) ---
% \author[1]{<Co-author Name>}[orcid=<XXXX-XXXX-XXXX-XXXX>]
% \credit{Supervision, Conceptualization, Writing -- review and editing}
\affiliation[1]{organization={<Department, University/Institution>},
                city={<City>},
                postcode={<00000>},
                country={<Country>}}
\cortext[cor1]{Corresponding author}
% ===========================================================================

\begin{abstract}
Deep reinforcement-learning (RL) controllers for HVAC systems are usually trained against fast neural-network surrogates, on the assumption that a more accurate surrogate is a better training environment. Testing this on the BOPTEST \texttt{bestest\_air} testcase, we report a negative result --- the \emph{fidelity--utility paradox}: the surrogate with the lower predictive error can be the worse environment for policy-gradient search. A grey-box resistance--capacitance surrogate with a neural residual heat-flow head (v3.5) attains a 24-hour rollout RMSE of $0.644\,^{\circ}$C versus $1.557\,^{\circ}$C for a black-box surrogate (v3); yet used directly for training it collapses on the live runtime (maintenance score $m_s = 1.046$, comfort violation $>77\%$), whereas the weaker v3 trains a usable controller ($m_s = 0.073$/$0.095$ on peak/typical windows). Retraining the black-box surrogate at finer resolution makes it \emph{more} accurate yet unusable for training ($m_s > 1.1$), so the paradox tracks a fidelity/smoothing trade-off, not model class alone. We resolve the paradox with a role-separating hybrid: v3 supplies smooth rollout dynamics while a frozen v3.5 acts as a per-step reward-shaping censor. The hybrid provides the best cross-window robustness --- sub-$5\%$ comfort violation on both windows and the lowest typical-window score ($m_s = 0.041$), at ${\sim}85\times$ live-simulator throughput --- and the optimal censor weight is controller-family specific. A transferability study on three hydronic testcases shows the inverse-calibration pipeline generalizes ($60.2$--$87.8\%$ rollout-RMSE reduction; effective zone capacitance re-identified at $1.918\pm0.032\times$ the baseline), whereas frozen-policy transfer is regime-dependent. The contribution is a precise, component-level transferability boundary, not a universal generalization claim.
\end{abstract}

\begin{highlights}
\item A more accurate building surrogate can be a worse RL training environment.
\item Temporal coarse-graining, not black-box structure alone, makes a surrogate useful.
\item A hybrid (black-box rollouts + frozen-twin reward censor) recovers control.
\item The optimal physics-censor weight is controller-family specific.
\item Calibration transfers across testcases; frozen-policy transfer is regime-bound.
\end{highlights}

\begin{keywords}
reinforcement learning \sep HVAC control \sep surrogate model \sep digital twin \sep physics-informed calibration \sep transfer learning \sep BOPTEST
\end{keywords}

\maketitle

\section*{Nomenclature}
\renewcommand{\arraystretch}{1.15}
\begin{longtable}{@{}l l p{0.62\linewidth}@{}}
\textbf{Symbol} & \textbf{Unit} & \textbf{Meaning} \\
\midrule
\endfirsthead
\textbf{Symbol} & \textbf{Unit} & \textbf{Meaning} \\
\midrule
\endhead
\multicolumn{3}{@{}l}{\emph{Thermophysical quantities}}\\
$T_{\mathrm{zone}}$ & \si{\celsius} & zone air temperature \\
$T_{\mathrm{amb}}$ & \si{\celsius} & ambient air temperature \\
$\Tsupply$ & \si{\celsius} & supply-air temperature command \\
$\Czon$ & \si{\joule\per\kelvin} & zone thermal capacitance \\
$R$ & \si{\kelvin\per\watt} & lumped envelope thermal resistance \\
$\eta$ & -- & heating power conversion efficiency \\
$\dot{Q}$ & \si{\watt} & net zone heat flow \\
$P$ & \si{\watt} & total HVAC electrical power \\
$\Delta t$ & \si{\second} & control / integration step (\SI{900}{\second}) \\[2pt]
\multicolumn{3}{@{}l}{\emph{Reinforcement-learning formulation}}\\
$s_t,\,a_t,\,o_t,\,d_t$ & -- & state, action, observation, disturbance at step $t$ \\
$\Phi$ & -- & one-step plant (emulator) transition map \\
$f_\theta,\,g_\phi$ & -- & black-box surrogate (v3) and frozen physical twin (v3.5) \\
$r_t$ & -- & per-step (shaped) reward \\
$\tilde{r}_t$ & -- & hybrid reward with disagreement censor \\
$J(\pi)$ & -- & expected discounted return \\
$\gamma$ & -- & discount factor \\
$w_c,\,w_e,\,w_s$ & -- & comfort / energy / safety preference weights \\
$\hat{A}_t$ & -- & generalized advantage estimate \\
$\rho_t$ & -- & PPO probability ratio \\
$\epsilon$ & -- & PPO clipping parameter \\
$\delta$ & -- & surrogate--twin disagreement penalty \\
$\lambda_T,\,\lambda_P$ & -- & hybrid temperature / power censor weights \\[2pt]
\multicolumn{3}{@{}l}{\emph{Evaluation metrics}}\\
$m_s$ & -- & BOPTEST maintenance score (lower is better) \\
$r_{\mathrm{time}},\,r_{\mathrm{sev}}$ & -- & time-in-violation and severity components of $m_s$ \\
$m_{s,\mathrm{RL}},\,m_{s,\mathrm{PI}}$ & -- & maintenance score of the RL and built-in PI controller \\
$\RMSE_T$ & \si{\celsius} & live closed-loop zone-temperature RMSE \\
CV(\RMSE) & \si{\percent} & coefficient of variation of the RMSE \\
NMBE & \si{\percent} & normalized mean bias error \\
$R^2$ & -- & coefficient of determination \\
Violation & \si{\percent} & fraction of steps outside the comfort band \\
CV & -- & coefficient of variation (std/mean) over seeds \\
$g_a$ & -- & $L_2$ action-gap norm (surrogate vs live) \\
$\Delta m_s$ & -- & live-minus-surrogate $m_s$ transfer gap \\[2pt]
\multicolumn{3}{@{}l}{\emph{Transferability (testcase $k$)}}\\
$\tau_k$ & -- & pre-specified pass threshold $1.25\,m_{s,\mathrm{PI},k}$ \\
$\Delta E_k$ & \si{\percent} & energy change of the RL controller vs PI \\
$G^{\mathrm{RMSE}}_k$ & \si{\percent} & rollout-RMSE improvement after Stage~A/B/C recalibration \\
$\rho_{C,k}$ & -- & re-identified $\Czon$ ratio vs the \texttt{bestest\_air} baseline \\
$\mathcal{A}_k$ & -- & pre-specified actuator adapter \\[2pt]
\multicolumn{3}{@{}l}{\emph{Abbreviations}}\\
BOPTEST & -- & Building Optimization Testing Framework \\
RTE & -- & (BOPTEST) Run-Time Environment \\
DRL / PPO & -- & deep RL / proximal policy optimization \\
GAE & -- & generalized advantage estimation \\
HDRL & -- & hierarchical deep reinforcement learning \\
MORL & -- & multi-objective reinforcement learning \\
POMDP & -- & partially observable Markov decision process \\
RC / ODE & -- & resistance--capacitance / ordinary differential equation \\
PI / RBC / MPC & -- & proportional--integral / rule-based / model predictive control \\
\bottomrule
\end{longtable}

% Introduction -- citations resolved from docs/introduction/ PDFs and wired
% via natbib (\citep) against references.bib; all placeholders resolved.
\section{Introduction}

People spend up to 90\% of their time indoors, and buildings account for roughly one third of global final energy use; within them, heating, ventilation, and air-conditioning (HVAC) systems are the single largest consumer~\citep{AlSayed2024Review,Nguyen2024Modelling}. Improving HVAC control is therefore one of the highest-leverage interventions available for building decarbonization, yet it is intrinsically difficult: zone thermodynamics are nonlinear and coupled, and they are driven by time-varying occupancy, weather, and equipment constraints. The controllers used in practice --- proportional--integral (PID) loops and rule-based control (RBC) --- are robust and interpretable but cannot exploit this structure, leaving substantial comfort and energy gains unrealized~\citep{Savino2025ASHRAE,Gao2024Predictive}. Model predictive control (MPC) can exploit it in principle, but it requires an accurate, continuously maintained physical model of each building, which is expensive to identify and brittle under model mismatch~\citep{Hou2024MultiSource}.

Deep reinforcement learning (DRL) is an attractive alternative because it learns a control policy directly from interaction, without an explicit model, and standardized runtime environments such as BOPTEST now make such controllers reproducibly comparable~\citep{Blum2021BOPTEST,AlSayed2024Review}. The obstacle is the sim-to-real deployment gap: policy-gradient algorithms consume millions of environment steps, so training on a live building --- or on a high-fidelity physics simulator stepped through an HTTP interface --- is prohibitively slow and risks sustained comfort violations during exploration~\citep{Wang2025SafeDRL,Hou2024MultiSource}. The community's response is to train the policy against a fast neural-network surrogate of the building, increasingly a physics-informed digital twin (e.g.\ resistance--capacitance or Neural Ordinary Differential Equation models) that generates state transitions orders of magnitude faster than real time~\citep{HouEvins2024,Mshragi2026FastML}. This paradigm rests on an unstated assumption, which we make explicit and test in this work: that a surrogate with higher predictive fidelity is automatically a better environment in which to train a controller.

We find that this assumption can fail, and we name the phenomenon the \emph{fidelity--utility paradox} (quantified as a measured contradiction across the evidence chain in Fig.~\ref{fig:concept}): the surrogate with the lowest multi-step rollout error can be the worst environment for policy-gradient search. When a controller is trained directly on the high-fidelity physical twin, the policy converges to a near bang-bang law (a surrogate-to-live action-gap norm of $2.0$) and fails on the live BOPTEST runtime environment ($m_s>1$, comfort violation above $77\%$), even though that twin is the more accurate offline predictor. We \emph{observe} this action saturation directly, and we \emph{measure} its surrogate-side cause: the higher-fidelity surrogates expose an action$\to$next-temperature response surface that is $7.9$--$9.4\times$ rougher (in a scale-free, step-length-independent sense) than the usable one, so policy-gradient optimizers such as PPO saturate into a near bang-bang law that does not survive the distribution shift to the live simulator~\citep{RiahiSamani2026OOD}. A full loss-landscape analysis along the training trajectory remains future work, but the mechanism is no longer established only in direction. Establishing the paradox cleanly is itself non-trivial: two surrogates of different fidelity also differ in their training corpus and time resolution, so any naive fidelity-versus-utility comparison is confounded and must be separated by a controlled decomposition.

\begin{figure}[pos={!ht}]
  \centering
  \includegraphics[width=\linewidth]{block2_system_overview.pdf}
  \caption{\textbf{The proposed surrogate-to-control framework} (schematic). Surrogate training backends (v3 coarse black-box, v3.5 calibrated RC+Neural-ODE, hybrid) $\to$ controller families (thermostatic PPO, HDRL, MORL) $\to$ live BOPTEST evaluation on \texttt{bestest\_air} (Blocks~1--2) and the hydronic family (Block~3). Backends are trained surrogate-only and transferred zero-shot (MORL adds a short live finetune); the hybrid uses v3 for rollout dynamics and a frozen v3.5 as a per-step reward censor.}
  \label{fig:system_overview}
\end{figure}

\begin{figure}[pos={!ht}]
  \centering
  \includegraphics[width=\linewidth]{block2_paper_organization.pdf}
  \caption{Organization of the paper: Introduction $\to$ Related Work $\to$ Proposed Work $\to$ Experimental Results (digital-twin fidelity, control utility, transferability) $\to$ Conclusion.}
  \label{fig:paper_org}
\end{figure}

\begin{figure}[pos={!ht}]
  \centering
  \includegraphics[width=0.98\linewidth]{block2_conceptual_overview.pdf}
  \caption{Quantified evidence chain for the fidelity--utility paradox. Each row is a training backend (v3 hourly, matched-resolution v3, direct v3.5, hybrid) and each column reports one \emph{measured} link of the chain from predictive fidelity to live utility: \textbf{(A)} 24\,h rollout RMSE$_T$ ($^\circ$C), \textbf{(B)} the scale-free relative action-surface roughness ($\times$ the usable v3), \textbf{(C)} the closed-loop policy saturation ($|a_0|\geq0.9$, \% of steps), and \textbf{(D)} the live BOPTEST maintenance score $m_s$ with the $m_s=1$ collapse line and the usable band ($m_s<0.1$). The paradox is the \emph{measured contradiction} between columns A and D: the RMSE$_T$ order (v3.5 $<$ matched-v3 $<$ v3) reverses in live $m_s$ --- the least accurate hourly v3 is the only usable single-model environment, while the two more accurate backends collapse. The hybrid inherits v3's rollout fidelity and surface (hatched, marked $\ast$) because it rolls out on v3, with the frozen v3.5 acting only as a reward censor, and lands in the usable band. Every value is loaded from the committed artefacts established in Sections~\ref{sec:results1-digital-twin}--\ref{sec:results2-control} (the per-figure source CSVs are listed in the supplementary provenance map).}
  \label{fig:concept}
\end{figure}

A second, orthogonal gap concerns the observation interface and the controller family. HVAC control is a partially observable Markov decision process (POMDP): a small ($5$-dimensional) observation of the instantaneous state is insufficient for preference-conditioned multi-objective control (MORL)~\citep{Byeon2025MaxMinMORL}, which needs forecast and actuation context to disambiguate heating demand~\citep{Gao2024Predictive}. It is also unclear whether a single physics-regularization recipe is universal across controller families, since thermostatic, hierarchical, and multi-objective agents have different loss-surface geometries, so a censor that helps one may over-constrain another. Existing studies seldom separate surrogate predictive fidelity from downstream controller utility, rarely audit the observation interface, and almost never pre-specify cross-testcase transfer hypotheses --- which is precisely the methodological gap this paper addresses.

We propose a hybrid, role-separating architecture that decouples prediction from training (Fig.~\ref{fig:system_overview}). A compact control-oriented black-box surrogate (v3) supplies smooth, control-friendly Markov rollout dynamics, while an inverse-calibrated physics-informed twin (v3.5), whose zone thermal capacitance $\Czon$ is identified from telemetry, acts as a \emph{frozen per-step reward-shaping censor}: it adds a disagreement penalty to the reward, not a term to the policy loss, so the smooth v3 gradient field is preserved while physically implausible state--action regions are discouraged. To address the POMDP we widen the interface to a $17$-dimensional, forecast-augmented direct-supply-temperature observation, and we evaluate the recipe across three controller families --- thermostatic proximal policy optimization (PPO), hierarchical DRL (HDRL)~\citep{Liao2025HDRL}, and preference-conditioned MORL~\citep{Byeon2025MaxMinMORL}. Finally, the resulting frozen policies are subjected to a pre-specified transferability study on a hydronic family of BOPTEST testcases.

We organize the investigation around four pre-specified, falsifiable hypotheses:
\begin{enumerate}[label=\textbf{H\arabic*.},leftmargin=2.6em]
  \item \emph{Fidelity--utility:} a surrogate with higher predictive fidelity is a better RL training environment.
  \item \emph{Role separation:} using the physical twin as a frozen reward-shaping censor over a smooth black-box rollout recovers the control utility that direct use of the twin destroys.
  \item \emph{Censor-weight universality:} a single physical-censor weight is sufficient (transfers) across controller families. (Falsification of this hypothesis is what establishes controller-family specificity.)
  \item \emph{Transferability:} the inverse-calibration pipeline and the frozen controller transfer to related hydronic testcases under documented recalibration.
\end{enumerate}
As reported below, H1 and H3 are \emph{falsified}, H2 is supported, and H4 resolves into a component-level boundary --- the calibration pipeline transfers while frozen-controller transfer does not. Each hypothesis and its verdict are bound to a versioned audit anchor, so that every outcome was predictable but not predicted before the corresponding runs.

This paper makes three commit-anchored, version-locked contributions, organized as the project's three evidence blocks:
\begin{enumerate}
  \item \textbf{Inverse-calibration pipeline and a matched-corpus decomposition (Block 1).} A Stage~A/B/C inverse-calibration protocol for the physical twin, with a controlled experiment attributing the predictive-fidelity gain to a $74.6\%$ data-resolution component and a $25.4\%$ physical-calibration component, so the calibration claim is real but bounded.
  \item \textbf{The fidelity--utility paradox and its hybrid resolution (Block 2).} Empirical evidence that a higher-fidelity physical surrogate is the worse direct RL training environment, resolved by a hybrid role assignment (v3 dynamics + frozen-v3.5 reward-shaping censor); the censor strength is shown to be controller-family specific, and the MORL controller beats the built-in PI baseline in mean (with the $N=5$ seed variance reported honestly).
  \item \textbf{A commit-anchored, version-locked transferability study (Block 3).} Across a hydronic family of testcases, the identified zone capacitance $\Czon$ transfers as a near-uniform structural invariant (rollout-RMSE improvement up to $88\%$), while zero-shot transfer of the frozen controller fails or passes only with an energy penalty --- establishing a precise component-level transferability boundary rather than a universal generalization claim.
\end{enumerate}

The paper is organized as summarized in Fig.~\r\ref{fig:paper_org}.

\section{Related Work}\label{sec:related}
\textbf{DRL and multi-objective control for HVAC.} Deep RL is an increasingly studied alternative to PID/MPC for building HVAC, benchmarked against ASHRAE Guideline~36 sequences \citep{Savino2025ASHRAE} and extended to multi-agent and chance-constrained settings \citep{Deng2025MultiAgent,Alotaibi2025ContextAware}. Because comfort and energy compete, the problem is naturally multi-objective: hierarchical DRL decomposes it across timescales \citep{Liao2025HDRL} and preference-conditioned MORL studies trade-off policies \citep{Byeon2025MaxMinMORL,Nguyen2024Modelling}. What this work does not isolate is whether one training recipe holds \emph{across} controller families, or how the training \emph{environment} --- not the algorithm --- shapes the policy.

\textbf{Surrogate and physics-informed models.} Since high-fidelity simulators are too slow for the millions of interactions DRL needs, controllers are trained on learned surrogates spanning a fidelity spectrum from black-box networks to physics-informed RC / Neural-ODE twins. \citet{HouEvins2024} formalize surrogate development into a reproducible protocol (adopted here as an audit standard), and fast surrogates reach extreme throughput \citep{Mshragi2026FastML}; in parallel, RL work studies how simulator data should be \emph{collected} \citep{Mayor2025Parallelized,Radac2025OnlineRL}. Crucially, this literature optimizes the surrogate along predictive accuracy and throughput and treats its \emph{use} as downstream --- never asking whether a more accurate predictor is thereby a better training environment, which we answer in the negative (Section~\ref{sec:results2-control}).

\textbf{Distribution shift and transfer.} Policies degrade off their training distribution: forecast augmentation improves cost and comfort \citep{Gao2024Predictive}, the out-of-distribution problem is catalogued for offline RL \citep{RiahiSamani2026OOD}, and transfer across zones/weather cuts training cost but is neither automatic nor uniformly beneficial \citep{Hou2024MultiSource}. We therefore treat cross-testcase transfer as a \emph{tested} hypothesis (Section~\ref{sec:results3-transfer}) and, across all three strands, isolate the rarely-explicit assumption that a higher-fidelity model --- or a recipe tuned on one controller/testcase --- carries over.

\section{Proposed Work}\label{sec:methodology}
This section gives the formal, self-contained statement of the control problem,
the three surrogate models, the controller families, and the evaluation protocol.
The detailed numerical instantiation of every quantity defined here --- network
sizes, calibrated parameters, hyperparameters, and measured scores --- is reported
with the corresponding evidence in Sections~\ref{sec:results1-digital-twin}--\ref{sec:results3-transfer};
here we fix notation and cite the methods on which the design rests.

\subsection{Reference environment}\label{ssec:m-env}
The plant is a single-zone building emulator with electric heating, drawn from the
BOPTEST family of Modelica-based test cases \citep{Blum2021BOPTEST,Wetter2014Modelica}
and served to the controller through BOPTEST's uniform HTTP interface
\citep{Arroyo2021GymBOPTEST}. Formally the emulator is a continuous-time
dynamical system whose latent thermal state evolves under a scalar heating command
$a_t\in[0,1]$ and an exogenous disturbance stream $d_t$ (ambient weather,
solar gain, occupancy, and time-varying comfort set-points). We interact with it
at a fixed control period $\Delta t = \SI{900}{\second}$ (15 minutes), yielding the
discrete-time transition $s_{t+1}=\Phi(s_t,a_t,d_t)$ that all surrogates are trained
to approximate. The primary test case is \texttt{bestest\_air}; a hydronic family of
related test cases is held out for the transferability study (Section~\ref{sec:results3-transfer}).

\subsection{Problem formulation}\label{ssec:m-pomdp}
Because the controller never observes the full latent state, control is a partially
observable Markov decision process (POMDP)
$\langle \mathcal{S},\mathcal{A},\mathcal{O},\Phi,R,\gamma\rangle$, where the agent
receives an observation $o_t=h(s_t,d_t)\in\mathcal{O}$ and selects $a_t\sim\pi(\cdot\mid o_t)$
so as to maximise the expected discounted return
\begin{equation}
J(\pi)=\mathbb{E}_{\pi}\!\left[\sum_{t=0}^{T-1}\gamma^{t}\,r_t\right],
\qquad
r_t = -\big(w_{\mathrm{c}}\,c_t + w_{\mathrm{e}}\,e_t\big),
\label{eq:m-return}
\end{equation}
with $c_t$ a thermal-discomfort term, $e_t$ the heating energy over the step, and
$w_{\mathrm{c}},w_{\mathrm{e}}$ trade-off weights. Partial observability is the
methodological reason a five-dimensional instantaneous observation is insufficient
and a forecast-augmented observation is required \citep{Gao2024Predictive}; the
exact channel sets are given in Section~\ref{sec:results2-control}. For
\emph{evaluation} (as opposed to training) we score deployed controllers with the
duration-and-severity maintenance score
\begin{equation}
m_s = r_{\mathrm{time}} + r_{\mathrm{sev}},
\label{eq:m-ms}
\end{equation}
the time-in-violation plus violation-severity metric of \citet{Wang2025SafeDRL};
lower is better and $m_s>1$ marks an unacceptable controller. This separation of a
shaped training reward~\eqref{eq:m-return} from an unshaped safety score~\eqref{eq:m-ms}
follows standard practice in safe reinforcement learning \citep{Garcia2015SafeRL}.

\subsection{Surrogate model design}\label{ssec:m-surrogate}
All three surrogates are fast approximations of $\Phi$ used as the training
environment in place of the slow emulator, in the model-based / Dyna tradition of
learning a model and planning or training a policy against it
\citep{Sutton1991Dyna,Hafner2025Dreamer}. They differ in how much building physics
is hard-wired into their structure.

\subsubsection{Control-oriented surrogate v3}
v3 is a compact black-box neural one-step predictor
$\hat{s}_{t+1}=f_\theta(s_t,a_t,d_t)$, trained by supervised minimisation of a
multi-step rollout error so that long-horizon trajectories --- not just one-step
residuals --- stay accurate. Its design goal is not maximal predictive accuracy but
a \emph{smooth, well-conditioned} response surface for policy-gradient search; the
architecture and parameter count are reported in Section~\ref{sec:results1-digital-twin}.

\subsubsection{Physically informed surrogate v3.5 and Stage A/B/C calibration}
v3.5 replaces the black box with a grey-box resistance--capacitance (RC) thermal
network whose unmodelled heat flow is supplied by a neural residual head. It is an
ODE-structured grey-box surrogate --- a continuous-time RC balance, in the spirit
of Neural ODEs \citep{Chen2018NeuralODE} and classical RC building identification
\citep{Bunning2020RC,Berthou2014RC,Bacher2011RCIdentification,Picard2017WhiteBox},
but integrated discretely by an explicit Euler step at the control period
$\Delta t$ rather than by an adaptive ODE solver. Writing the zone capacitance as
$\Czon$ and a lumped envelope resistance as $R$, the core balance is
\begin{equation}
\Czon\,\frac{\mathrm{d}T}{\mathrm{d}t}
= \frac{T_{\mathrm{amb}}-T}{R} + \eta\,a_t\,\dot{Q}_{\max} + q_d,
\label{eq:m-rc}
\end{equation}
with $\eta\,a_t\,\dot{Q}_{\max}$ the delivered heating power and $q_d$ aggregated
disturbance gains (the neural residual head). Embedding this conservation law in the
network makes it physics-informed in the sense of
\citet{Raissi2019PINN,Karpatne2017TheoryGuided,Willard2022PIML}, so its parameters
are physically interpretable; we nonetheless treat $\Czon$ as an \emph{effective}
thermal capacitance under the chosen surrogate structure --- a lumped parameter
that may absorb unmodelled fast dynamics --- rather than a direct measurement of
zone air capacitance. The parameters are recovered by a staged inverse calibration
(Stages~A/B/C) in the spirit of staged grey-box calibration
\citep{Bacher2011RCIdentification}, and the identifiability of $\Czon$ is checked
with a Fisher/Laplace confidence interval; the staged protocol and the resulting
calibrated values are detailed in Section~\ref{sec:results1-digital-twin}.

\subsubsection{Hybrid surrogate and reward-shaping censor}
The hybrid backend assigns the two models orthogonal roles: v3 supplies the smooth
rollout dynamics, while a \emph{frozen} v3.5 acts as a per-step reward-shaping
censor. Training uses the shaped reward
\begin{equation}
\tilde{r}_t = r_t - \lambda_T\,\delta^{T}_t - \lambda_P\,\delta^{P}_t,
\label{eq:m-hybrid}
\end{equation}
where the disagreement terms are the per-step $L_1$ (absolute) distances between the
one-step predictions of the rollout surrogate $f_\theta$ (v3) and the frozen twin
$g_\phi$ (v3.5), separately for the zone temperature and the HVAC power channel,
\begin{equation}
\delta^{T}_t = \big|\, f^{T}_\theta(s_t,a_t,d_t) - g^{T}_\phi(s_t,a_t,d_t)\,\big|\ [\si{\celsius}],
\qquad
\delta^{P}_t = \big|\, f^{P}_\theta(s_t,a_t,d_t) - g^{P}_\phi(s_t,a_t,d_t)\,\big|\ [\si{\watt}],
\label{eq:m-delta}
\end{equation}
with no squaring, normalisation, or clipping. The two censor weights differ in scale
because they multiply a temperature residual (in \si{\celsius}) and a power residual
(in \si{\watt}); for the thermostatic controller $\lambda_T = 0.10$ and
$\lambda_P = 5\times10^{-5}$. Crucially, $g_\phi$ is evaluated \emph{forward only}
and its outputs are detached, so the censor enters the \emph{reward}, never the
policy loss or the surrogate gradient: the well-conditioned v3 gradient field of
Section~\ref{ssec:m-surrogate} is preserved while physically implausible
state--action regions are discouraged --- a model-based shaping that keeps the
benefits of Dyna-style training \citep{Sutton1991Dyna} without inheriting the
sharp gradients of the physical twin. The swept values of $\lambda_T$ per
controller family are given in Section~\ref{sec:results2-control}.

\subsection{Controller families}\label{ssec:m-controllers}
All policies are optimised with proximal policy optimization (PPO)
\citep{Schulman2017PPO} using generalized advantage estimation
\citep{Schulman2016GAE} and the Stable-Baselines3 implementation
\citep{Raffin2021SB3}; PPO maximises the clipped surrogate objective
\begin{equation}
L^{\mathrm{CLIP}}(\theta)=\mathbb{E}_t\!\left[\min\!\big(\rho_t(\theta)\,\hat{A}_t,\;
\operatorname{clip}(\rho_t(\theta),1-\epsilon,1+\epsilon)\,\hat{A}_t\big)\right],
\qquad \rho_t(\theta)=\frac{\pi_\theta(a_t\mid o_t)}{\pi_{\theta_{\mathrm{old}}}(a_t\mid o_t)},
\label{eq:m-ppo}
\end{equation}
with $\hat{A}_t$ the GAE advantage. We evaluate the surrogate recipe across three
controller families of increasing structure: (i) a \emph{thermostatic} PPO agent on
a compact observation; (ii) a \emph{hierarchical} DRL controller (HDRL) that
decomposes control across timescales, in the options/feudal tradition
\citep{Bacon2017Options,Nachum2018HIRO} as recently applied to year-round HVAC
operation \citep{Liao2025HDRL}; and (iii) a \emph{preference-conditioned}
multi-objective controller (MORL) that conditions on a comfort--energy preference
vector \citep{Yang2019MORL,Roijers2013MOSurvey,Hayes2022MOSurvey,Byeon2025MaxMinMORL}
and acts on the forecast-augmented observation. The exact observation and action
spaces of each family are specified in Section~\ref{sec:results2-control}.

\subsection{Evaluation protocol and transferability methodology}\label{ssec:m-eval}
Surrogate predictive fidelity is reported with the ASHRAE-style calibration
statistics CV(\RMSE) and NMBE over multi-step rollouts, the standard accuracy
measures for calibrated building models \citep{Bacher2011RCIdentification}.
Downstream control utility is reported with the maintenance score~\eqref{eq:m-ms}
\citep{Wang2025SafeDRL}, the comfort-violation fraction, and heating energy,
each benchmarked against BOPTEST's built-in baseline controller. Because a policy
trained on a surrogate is deployed on a different (live) system, the central
methodological risk is dataset/distribution shift \citep{Quinonero2009DatasetShift};
we therefore always report the \emph{live}-emulator score, never only the
surrogate-internal score. For transferability we adopt a commit-anchored, version-locked
protocol: each hypothesis (H1--H4 of Section~\ref{sec:related}), pass threshold, and
recalibration adapter is fixed in a version-locked source-control commit
\emph{before} the corresponding runs, and these commits are publicly available in
the open-source repository,
providing timestamped, immutable verifiability of the analysis plan in lieu of
formal pre-registration on an external registry. Cross-test-case transfer is realised through a light recalibration adapter
rather than assumed zero-shot, following the evidence that transfer is
source-dependent \citep{Hou2024MultiSource}. Controller scores are reported with
seed statistics wherever repeated-seed runs are available: MORL is evaluated over
the five fixed seeds $\{42,43,44,45,46\}$, whereas the thermostatic PPO and HDRL
targeted-window experiments are deterministic single-seed mechanistic comparisons,
a limitation stated explicitly in Section~\ref{ssec:b3lim}. The full statistical
and audit protocol is given in Section~\ref{sec:setup} and the results in
Sections~\ref{sec:results1-digital-twin}--\ref{sec:results3-transfer}.

\subsection{Implementation and protocol}\label{sec:setup}\label{ssec:s-testbed}\label{ssec:s-data}\label{ssec:s-train}\label{ssec:s-audit}
All controllers are evaluated on BOPTEST \citep{Blum2021BOPTEST,Wetter2014Modelica,Arroyo2021GymBOPTEST}, using \texttt{bestest\_air} as the primary testcase and a \texttt{bestest\_hydronic} family for transfer (Section~\ref{sec:results3-transfer}), at a fixed \SI{15}{\minute} control period through one HTTP contract behind which four interchangeable backends sit (live BOPTEST, v3, v3.5, hybrid) --- so only the dynamics backend changes across the surrogate-versus-live comparison, and the surrogate backends run \numrange{85.0}{114.2}$\times$ faster than the live loop, making GPU-free policy-gradient training tractable. Surrogates use three corpora generated by scripted excitation: a canonical v3 corpus ($51{,}200$ at \SI{1}{\hour}), a $15$-minute exploration corpus ($48{,}384$ at \SI{900}{\second}), and a v3.5 calibration corpus ($10{,}744$ at \SI{900}{\second}); the deliberate one-hour/fifteen-minute pairing is the instrument behind the matched-corpus ablation. v3 ($8{,}482$ parameters) is fit by multi-step rollout regression; v3.5 is identified by the Stage~A/B/C inverse calibration of Section~\ref{ssec:m-surrogate} \citep{Bacher2011RCIdentification}, yielding $\Czon=\SI{4.413e5}{\joule\per\kelvin}$ ($+5.1\%$ over the physical prior). All controllers are trained with PPO \citep{Schulman2017PPO} in Stable-Baselines3~2.1.0 \citep{Raffin2021SB3} under Python~3.11; the hybrid loads the frozen v3.5 as the censor of Eq.~\eqref{eq:m-hybrid}. MORL is evaluated over $N=5$ fixed seeds with stated variance; thermostatic-PPO/HDRL targeted-window runs are deterministic single-seed (seed~42); all are benchmarked against BOPTEST's built-in PI \citep{Wang2025SafeDRL}. Each hypothesis (H1--H4) is bound to a versioned audit anchor committed \emph{before} its runs, and the released repository pins package versions, checkpoints, configs, and seeds so every result reproduces from the archived artefacts (provenance in Supplementary Tables~S1--S3).

% ===== Results sections (auto-generated bodies; sections 5, 6, 7) =====
\input{results1_body.tex}
\input{results2_body.tex}
\input{results3_body.tex}

\section{Discussion}\label{sec:discussion}

\textbf{Predictive fidelity and training utility are distinct, and over part of the range opposed.} The calibrated twin v3.5 is the far better predictor (24\,h rollout \RMSE{} $0.644$ vs $1.557\,^{\circ}$C) yet, used directly as the training environment, yields an unusable controller ($m_s=1.046$, $>77\%$ violation), while the weaker v3 yields a usable one ($m_s=0.073$/$0.095$). A matched-resolution closed-loop ablation settles the obvious confound: the \emph{same} black-box v3 retrained at $15$ minutes is strictly \emph{more accurate} ($0.876\,^{\circ}$C) yet also collapses ($m_s=1.14$/$1.21$; Table~\ref{tab:coarse_graining}), so the operative variable is the fidelity/smoothing trade-off induced by temporal resolution, not the model class --- and the matched-corpus decomposition shows the fidelity gain itself is only $25.4\%$ physical calibration against $74.6\%$ resolution. We read this as a distribution-shift effect \citep{Quinonero2009DatasetShift,RiahiSamani2026OOD}: the sharper response surface of the high-fidelity backends ($7.9$--$9.4\times$ rougher; Table~\ref{tab:surface_sharpness}) is exploited by policy-gradient search into a near bang-bang law that does not survive transfer. Separating the two roles --- v3 for smooth dynamics, a frozen v3.5 as a reward-shaping censor --- recovers the best cross-window robustness ($m_s=0.087$/$0.041$, sub-$5\%$ violation on both windows) at an $85\times$ training speed-up.

\textbf{The physics-regularisation recipe is controller-family specific, and transfer resolves into a component-level boundary.} The optimal censor weight is $\lambda_{\mathrm{temp}}=0.10$ for thermostatic PPO but $0$ for the hierarchical and $17$D MORL agents, which already encode enough forecast/structural context that an external censor over-constrains them \citep{Liao2025HDRL,Byeon2025MaxMinMORL} --- so a single ``best'' regularisation strength cannot be reported without naming its controller family. For transfer, the calibration \emph{pipeline} ports (rollout \RMSE{} down $60.2$--$87.8\%$ on the hydronic family; $\Czon$ re-identifies as a near-uniform $1.918\pm0.032\times$ invariant across an order-of-magnitude volume change), whereas the frozen \emph{policy} does not transfer uniformly: the commercial case passes the $1.25\times$-PI comfort threshold but at a $35.3\%$ energy penalty, while the residential cases fail it zero-shot. The contribution is thus less a new controller than a corrected, quantified account of \emph{why} surrogate-trained controllers succeed or fail, under a commit-anchored protocol that lets H1/H3 be stated as \emph{falsified} rather than quietly dropped.

\subsection{Limitations}\label{ssec:block1-limitations}\label{ssec:b3lim}
Evaluation is simulation-only on a single-zone \texttt{bestest\_air} emulator (multi-zone and richer topologies untested; transfer limited to a hydronic family), and the surrogate power channel is reproduced less accurately than temperature. The paradox mechanism is \emph{measured} statically on each surrogate's one-step action map and corroborated by the matched-resolution ablation, but a loss-landscape analysis along the PPO trajectory --- and generality to off-policy algorithms (SAC~\citep{Haarnoja2018SAC}, TD3) --- remains open. Statistical support varies by family (MORL $N=5$, neutral $m_s=0.187\pm0.078$ with CI far below the PI $0.910$; the two headline thermostatic controllers $N=3$, every seed sub-$5\%$ violation; HDRL single-seed), the only baseline is BOPTEST's built-in PI, the MORL censor weight is adopted by analogy with the HDRL sweep, and the backend$\times$observation grid is only partially crossed.

\section{Conclusion}\label{sec:conclusion}
We asked whether a surrogate with higher predictive fidelity is automatically a
better environment in which to train a reinforcement-learning HVAC controller, and
tested the question across three controller families and a hydronic family of
transfer testcases under a commit-anchored, version-locked protocol. The answer is
no. Only the temporally coarse, hourly-trained black-box surrogate (v3) trains a
usable controller: the most accurate physical twin (v3.5; $0.644\,^{\circ}$C 24-hour
rollout \RMSE) collapses ($m_s = 1.046$, comfort violation above $77\%$), and the
\emph{same} black-box architecture retrained at the finer $900$\,s resolution becomes
a \emph{more} accurate predictor ($0.876\,^{\circ}$C) yet also fails as a training
environment ($m_s = 1.14$/$1.21$, violation above $85\%$) --- a fidelity--utility
paradox (H1 falsified) whose operative variable is the fidelity/smoothing trade-off
induced by temporal resolution, not the surrogate model class; a matched-corpus
attribution further splits the predictive gain into $74.6\%$ data-resolution and only
$25.4\%$ physical calibration. Separating the two roles resolves it: using the
black-box surrogate for smooth rollout dynamics and a frozen physical twin as a
reward-shaping censor (H2 supported) recovers the best cross-window robustness of the
study ($m_s = 0.041$ typical, violation below $5\%$) at an $85\times$ training
speed-up. The censor strength is controller-family specific
($\lambda_{\mathrm{temp}}=0.10$ for thermostatic PPO, $0$ for the hierarchical and
MORL agents; H3 falsified), and transferability resolves into a component-level
boundary (H4): the inverse-calibration pipeline transfers --- rollout \RMSE{} falls
by $60.2$--$87.8\%$ and the zone capacitance re-identifies as a near-uniform
invariant ($1.918\pm0.032\times$ the source) --- whereas the frozen control policy
does not transfer zero-shot. The contribution is therefore less a new controller
than a corrected, quantified account of why surrogate-trained controllers succeed
or fail, together with a reusable role-separating recipe.

Several directions (the project's Block~4) follow directly from the limitations of
Section~\ref{ssec:b3lim}: extending the study from a single zone to multi-zone and
mixed-topology buildings; extending the now-measured static response-surface
roughness (Table~\ref{tab:surface_sharpness}) to a formal loss-landscape analysis
along the full PPO training trajectory;
improving the heating-power channel of the surrogate so it is a validated rather
than an auxiliary output; broadening transfer beyond the hydronic family and
pairing the transferable calibration pipeline with light policy adaptation instead
of zero-shot reuse; and, ultimately, closing the remaining sim-to-real gap through
deployment on a physical building.

\section*{CRediT authorship contribution statement}
% TODO: list every author with their CRediT roles; add one \textbf{Name:} line per co-author.
\textbf{Almaz Sapargali:} Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Data curation, Writing -- original draft, Writing -- review and editing, Visualization.
% \textbf{<Co-author Name>:} Supervision, Conceptualization, Writing -- review and editing.

\section*{Declaration of competing interest}
The authors declare that they have no known competing financial interests or
personal relationships that could have appeared to influence the work reported in
this paper.

\section*{Funding}
This research did not receive any specific grant from funding agencies in the
public, commercial, or not-for-profit sectors. % TODO: replace if any funding applies.

\section*{Supplementary material}
Every figure, table, and inline number in Results~I--III is read directly from the
versioned \texttt{reports/} and \texttt{outputs/} artefacts. The separate
Supplementary Material document provides the complete content-to-artefact
provenance maps for the three evidence blocks (Supplementary Tables~S1--S3) together
with the parameter, configuration, and interface tables referenced from the main
text (Supplementary Tables~S4--S9).

\section*{Declaration of generative AI and AI-assisted technologies in the manuscript preparation process}
During the preparation of this work, the author(s) used Claude (Anthropic) to
assist with language editing, improving the readability and clarity of the text,
and with \LaTeX{} formatting and reference-list preparation. After using this tool,
the author(s) reviewed and edited the content as needed and take full responsibility
for the content of the published article. No generative AI tool was used to generate,
analyse, or interpret the research data, or to produce the scientific findings and
conclusions, which are the work of the author(s).

\section*{Acknowledgements}
% TODO: add any people/institutions to thank, or state "None.".
The authors thank the developers of the open-source BOPTEST framework. % adjust as needed.

\bibliographystyle{unsrtnat}
\bibliography{references}

\end{document}
"""


def _tex_escape(s: str) -> str:
    for a, b in (("\\", ""), ("{", r"\{"), ("}", r"\}"), ("&", r"\&"),
                 ("%", r"\%"), ("#", r"\#"), ("_", r"\_"), ("$", r"\$"),
                 ("^", r"\textasciicircum{}"), ("~", r"\textasciitilde{}")):
        s = s.replace(a, b)
    return s


def _artefact_cell(s: str) -> str:
    """Escape an artefact path/command and allow line breaks at / and _."""
    esc = _tex_escape(s).replace("/", r"/\allowbreak ").replace(r"\_", r"\_\allowbreak ")
    return r"\texttt{" + esc + "}"


def _provenance_block(header_prefix: str):
    """Parse the first ```text fenced provenance map after a roadmap header into
    a list of (content, artefact) rows (continuation lines are appended)."""
    lines = (DOCS.parent / "roadmap.md").read_text(encoding="utf-8").splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith(header_prefix))
    j = next(k for k in range(i, len(lines)) if lines[k].strip().startswith("```text"))
    end = next(k for k in range(j + 1, len(lines)) if lines[k].strip() == "```")
    rows = []
    for raw in lines[j + 1:end]:
        if not raw.strip() or set(raw.strip()) <= {"-", " "}:
            continue
        if "->" in raw:
            content, art = raw.split("->", 1)
            content, art = content.strip(), art.strip()
            if content.lower().endswith("content") and "source" in art.lower():
                continue  # header row
            rows.append([content, art])
        elif rows:  # continuation of the previous artefact
            rows[-1][1] += " " + raw.strip()
    return rows


def build_provenance_supplementary() -> str:
    blocks = [
        ("### 3.2", "Results~I", "tab:prov-r1",
         r"python3 -B docs/results1\_digital\_twin\_overleaf/build\_results1\_overleaf.py"),
        ("### 11.1", "Results~II", "tab:prov-r2",
         r"python3 -B evaluation/run\_block2.py build-reports"),
        ("### 15.7", "Results~III", "tab:prov-r3",
         r"Block~3 evaluation scripts (see manifests below)"),
    ]
    out = [r"\renewcommand{\thetable}{S\arabic{table}}", r"\setcounter{table}{0}"]
    for hdr, label, tabid, cmd in blocks:
        rows = _provenance_block(hdr)
        out.append("")
        out.append(r"\footnotesize")
        out.append(r"\begin{longtable}{@{}p{0.40\linewidth} p{0.52\linewidth}@{}}")
        out.append(r"\caption{%s content-to-artefact provenance map (rebuild: \texttt{%s}).}\label{%s}\\"
                    % (label, cmd, tabid))
        head = r"\textbf{Content} & \textbf{Source artefact}\\ \midrule"
        out.append(head + r" \endfirsthead")
        out.append(head + r" \endhead")
        for content, art in rows:
            out.append(_tex_escape(content) + " & " + _artefact_cell(art) + r" \\")
        out.append(r"\bottomrule")
        out.append(r"\end{longtable}")
        out.append(r"\normalsize")
    return "\n".join(out)


SUPP_DOC = r"""\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage{geometry}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{array}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{siunitx}
\usepackage{longtable}
\usepackage{float}
\usepackage{subcaption}
\usepackage{xcolor}
\usepackage{caption}
\usepackage{hyperref}
\geometry{margin=2.0cm}
\graphicspath{{figures/}}
\captionsetup{font=small,labelfont=bf}
\newcommand{\RMSE}{\ensuremath{\mathrm{RMSE}}}
\newcommand{\MAE}{\ensuremath{\mathrm{MAE}}}
\newcommand{\Czon}{\ensuremath{C_{\mathrm{zon}}}}
\newcommand{\Tsupply}{\ensuremath{T_{\mathrm{sup}}}}
\newcommand{\That}{\ensuremath{\widehat{T}}}
\renewcommand{\thetable}{S\arabic{table}}
\renewcommand{\thefigure}{S\arabic{figure}}
\title{Supplementary Material for\\[2pt]
\emph{The Fidelity--Utility Paradox in Surrogate-Based
Reinforcement Learning for HVAC Control}}
\author{}
\date{}

\begin{document}
\maketitle

\noindent This document is the Supplementary Material for the above manuscript. It
provides the complete content-to-artefact provenance maps for the three evidence
blocks (Supplementary Tables~S1--S3) and the parameter, configuration, and
interface tables referenced from the main text (Supplementary Tables~S4--S9).
Every figure, table, and inline number in the main text can be traced through these
maps to the exact versioned source file in the project's \texttt{reports/} and
\texttt{outputs/} trees.

%%SUPP_BODY%%

\end{document}
"""


def build_supplementary_document(relocated) -> str:
    body = build_provenance_supplementary() + "\n\n" + build_supplementary_tables(relocated)
    # Relocated floats carry the CAS [pos={!ht}] key from the main bodies; the
    # supplementary is article-class (float package loaded), which does not parse the
    # CAS key, so map it back to the float-package [H] for clean, valid placement.
    body = body.replace("[pos={!ht}]", "[H]")
    return SUPP_DOC.replace("%%SUPP_BODY%%", body)


def main() -> None:
    paper_dir = DOCS / "paper_combined"
    figdir = paper_dir / "figures"
    paper_dir.mkdir(exist_ok=True)
    figdir.mkdir(exist_ok=True)
    header = (
        "% Auto-generated by docs/build_integrated_paper.py -- do not edit by hand.\n"
        "% Standalone scaffolding (preamble, nomenclature, limitations, conclusion,\n"
        "% \\setcounter) stripped for \\input into the combined manuscript.\n"
    )
    n_fig = 0
    relocated = []
    combined = []  # (index, reduced_body)
    # Pass 1: strip each section, write the full standalone copy, and pull the
    # auxiliary parameter/config tables out for the separate Supplementary PDF.
    for i, (section_dir, _) in enumerate(SECTIONS, start=1):
        d = DOCS / section_dir
        body = header + strip_to_body((d / "main.tex").read_text(encoding="utf-8"))
        # The CAS class redefines figure/table via expl3 and reads the optional
        # [...] as a key-value list, so the float package's [H] is meaningless and
        # (with float loaded) every float is pushed to the document end, which also
        # broke the "Page x of y" total. Drive CAS's own placement key instead:
        # pos={!ht} -> fps@figure/@table = "!ht" (here/top, fraction limits relaxed),
        # keeping figures/tables next to their text and pagination stable.
        body = body.replace(r"\begin{figure}[H]", r"\begin{figure}[pos={!ht}]")
        body = body.replace(r"\begin{table}[H]", r"\begin{table}[pos={!ht}]")
        # In case an earlier run already rewrote [H] to the interim [!ht] form.
        body = body.replace(r"\begin{figure}[!ht]", r"\begin{figure}[pos={!ht}]")
        body = body.replace(r"\begin{table}[!ht]", r"\begin{table}[pos={!ht}]")
        body = annotate_figures(body)  # add 'Data: <path>' provenance under figures
        (d / "section_body.tex").write_text(body, encoding="utf-8")  # full copy
        body_combined, moved = extract_supp_tables(body)
        relocated.extend(moved)
        combined.append((i, body_combined))
        for pattern in ("*.pdf", "*.png"):
            for fig in (d / "figures").glob(pattern):
                shutil.copy2(fig, figdir / fig.name)
                n_fig += 1
    # Map each relocated float's \label to its fixed Supplementary number. The
    # supplement renders 3 provenance tables (Table S1--S3) first, so moved tables
    # continue at S4; moved figures use an independent figure counter (Figure S1+).
    # We replay the relocation order to assign numbers per counter.
    label2num = {}
    fig_n, tab_n = 0, 3
    for blk in relocated:
        m = re.search(r"\\label\{([^}]+)\}", blk)
        if not m:
            continue
        if blk.lstrip().startswith(r"\begin{figure}"):
            fig_n += 1
            label2num[m.group(1)] = f"S{fig_n}"
        else:
            tab_n += 1
            label2num[m.group(1)] = f"S{tab_n}"
    # Pass 2: rewrite the now-dangling \ref to relocated floats as fixed \suppref
    # pointers (Figure~\suppref{Sk} / Table~\suppref{Sk}), then write the bodies.
    for i, body_combined in combined:
        for label, num in label2num.items():
            body_combined = body_combined.replace(r"\ref{" + label + "}", r"\suppref{" + num + "}")
        (paper_dir / f"results{i}_body.tex").write_text(body_combined, encoding="utf-8")
        print(f"Wrote results{i}_body.tex")
    (paper_dir / "main_paper.tex").write_text(MASTER, encoding="utf-8")
    (paper_dir / "supplementary.tex").write_text(
        build_supplementary_document(relocated), encoding="utf-8")
    print(f"Wrote main_paper.tex + supplementary.tex (self-contained; {n_fig} figure "
          f"files copied; {len(relocated)} floats -> supplementary)")


if __name__ == "__main__":
    main()
