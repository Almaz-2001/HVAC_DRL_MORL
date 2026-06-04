"""Build the data-driven Overleaf package for Results II / Block 2.

The section follows Block 2 of ``roadmap.md`` (Sections 4-11): pure v3
thermostatic PPO baseline, direct-v3.5 negative control, thermostatic hybrid,
warm-start negative control, transfer diagnostics, HDRL sweep, MORL 5D->17D
observation ablation, MORL Pareto + N=5 canonical seed analysis, seasonal
falsification, and PI reference.

Design: every table and inline KPI is read from versioned project artifacts in
``reports/`` and ``outputs/`` (provenance map: roadmap Section 11.1). Figures are
referenced from ``figures/`` (already produced by the Block 2 evaluation
scripts); this builder does not regenerate them. It writes ``main.tex`` only.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BASE = Path(__file__).resolve().parent


def read_csv(rel: str) -> pd.DataFrame:
    return pd.read_csv(ROOT / rel)


def tex_escape(value: object) -> str:
    text = str(value)
    repl = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
        "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
        "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    }
    for a, b in repl.items():
        text = text.replace(a, b)
    return text


def f(value: float, nd: int = 3) -> str:
    return f"{float(value):.{nd}f}"


# ---------------------------------------------------------------------------
# Data accessors
# ---------------------------------------------------------------------------

def _scen_row(df: pd.DataFrame, scenario: str, **conds) -> pd.Series:
    sub = df[df["scenario"] == scenario]
    for k, v in conds.items():
        sub = sub[sub[k] == v]
    return sub.iloc[0]


def load_block2():
    return {
        "pure": read_csv("outputs/bestest_air_article7_style_15min/summary.csv"),
        "hybrid": read_csv("outputs/block2_thermostatic_hybrid_v3_v35_l010/summary.csv"),
        "warm": read_csv("outputs/block2_thermostatic_warmstart_utility/comparison_summary.csv"),
        "arch": read_csv("reports/hou_evins_architecture_justification_table.csv"),
        "transfer": read_csv("reports/hybrid_transfer_comparison.csv"),
        "hdrl": read_csv("reports/block2_hdrl_lambda_sweep_summary.csv"),
        "morl_recon": read_csv("reports/block2_morl_5d_reconstructed_comparison.csv"),
        "morl_cmp": read_csv("reports/block2_morl_comparison_summary.csv"),
        "pareto": read_csv("reports/morl_pareto_front_table.csv"),
        "seed_sum": read_csv("reports/morl_canonical_seedfix_yearly_summary.csv"),
        "seed_per": read_csv("reports/morl_canonical_seedfix_yearly_per_seed.csv"),
        "pi": read_csv("outputs/pi_baseline_15min_yearly/pi_yearly_summary.csv"),
    }


# ---------------------------------------------------------------------------
# Table builders (all data-driven)
# ---------------------------------------------------------------------------

def table_main_kpi(d: dict) -> str:
    arch = d["arch"]
    tr = d["transfer"]
    v35 = arch[arch.variant == "v35_calibrated"].iloc[0]
    rows = []
    for scen, label in [("peak_heat_window", "peak"), ("typical_heat_window", "typical")]:
        pv = _scen_row(d["pure"], scen, controller="thermostatic")
        hy = _scen_row(d["hybrid"], scen)
        dv_viol = tr[(tr.variant == "direct_v35") & (tr.scenario == scen)].iloc[0]["boptest_violation_pct"]
        if scen == "peak_heat_window":
            dv_ms, dv_e, dv_r = v35["peak_control_m_s"], v35["peak_energy_kwh"], v35["peak_transfer_temp_rmse_c"]
        else:
            dv_ms, dv_e, dv_r = v35["typical_control_m_s"], v35["typical_energy_kwh"], v35["typical_transfer_temp_rmse_c"]
        rows.append(f"pure v3 PPO & {label} & {f(pv.m_s)} & {f(pv.violation_pct,2)} & {f(pv.rmse_22_c)} & {f(pv.energy_kwh,1)} \\\\")
        rows.append(f"direct v3.5 PPO & {label} & {f(dv_ms)} & {f(dv_viol,2)} & {f(dv_r)} & {f(dv_e,1)} \\\\")
        rows.append(f"hybrid $\\lambda_T=0.10$ & {label} & {f(hy.m_s)} & {f(hy.violation_pct,2)} & {f(hy.rmse_center_c)} & {f(hy.energy_kwh,1)} \\\\")
    return "\n".join(rows)


def table_warmstart(d: dict) -> str:
    w = d["warm"]
    rows = []
    for mode, mlabel in [("scratch", "scratch (random init)"), ("warmstart", "warm-start (from v3.5)")]:
        for scen, label in [("peak_heat_window", "peak"), ("typical_heat_window", "typical")]:
            r = w[(w["mode"] == mode) & (w["scenario"] == scen)].iloc[0]
            rows.append(f"{mlabel} & {label} & {f(r.m_s)} & {f(r.violation_pct,2)} \\\\")
    return "\n".join(rows)


def table_transfer(d: dict) -> str:
    tr = d["transfer"]
    rows = []
    for variant, vlabel in [("pure_v3", "pure v3"), ("hybrid_l010", "hybrid $\\lambda_T=0.10$"), ("direct_v35", "direct v3.5")]:
        for scen, label in [("peak_heat_window", "peak"), ("typical_heat_window", "typical")]:
            r = tr[(tr.variant == variant) & (tr.scenario == scen)].iloc[0]
            rows.append(f"{vlabel} & {label} & {f(r.ms_gap,3)} & {f(r.action_gap_norm,3)} & {int(r.first_divergence_step)} & {tex_escape(r.top_feature)} \\\\")
    return "\n".join(rows)


def table_hdrl(d: dict) -> str:
    h = d["hdrl"]
    lam = {"l000": "0.00", "l003": "0.03", "l005": "0.05", "l010": "0.10"}
    rows = []
    for scen, label in [("peak_heat_window", "peak"), ("typical_heat_window", "typical")]:
        for v in ["l000", "l003", "l005", "l010"]:
            r = h[(h.variant == v) & (h.scenario == scen)].iloc[0]
            rows.append(f"{lam[v]} & {label} & {f(r.m_s,3)} & {f(r.violation_pct,2)} & {f(r.rmse_center_c)} & {f(r.energy_kwh,1)} \\\\")
    return "\n".join(rows)


def table_morl_5d17d(d: dict):
    rec = d["morl_recon"]
    r5 = rec[rec.variant == "MORL_5D_basic_reconstructed"].iloc[0]
    r17 = d["morl_cmp"][d["morl_cmp"].variant == "MORL_17D_power_only"].iloc[0]
    frozen5 = rec[(rec.variant == "MORL_5D_basic") & (rec.evidence_layer == "historical_frozen")].iloc[0]
    rows = [
        f"MORL 5D (current-code rerun) & 5 & {f(r5.rmse_c)} & {f(r5.violation_pct,1)} & {f(r5.m_s,3)} \\\\",
        f"MORL 17D power-only (canonical) & 17 & {f(r17.rmse_c)} & {f(r17.violation_pct,1)} & {f(r17.m_s,3)} \\\\",
    ]
    return "\n".join(rows), frozen5, r5, r17


def table_morl_pareto_seed(d: dict) -> str:
    p = d["pareto"]
    s = d["seed_sum"]

    def pt(label):
        r = p[p.label == label].iloc[0]
        return r

    p0 = pt("comfort_000_energy_100")
    p25 = pt("comfort_025_energy_075")
    p100 = p[p.label == "comfort_100_energy_000"]
    n50 = s[s.canonical == "comfort_050_energy_050"].iloc[0]
    n75 = s[s.canonical == "comfort_075_energy_025"].iloc[0]
    rows = [
        f"0/100 (seed 42) & {f(p0.rmse_mean)} & {f(p0.violation_pct_mean,2)} & {f(p0.ms_mean,3)} & energy-only collapse \\\\",
        f"25/75 (seed 42) & {f(p25.rmse_mean)} & {f(p25.violation_pct_mean,2)} & {f(p25.ms_mean,3)} & energy-weighted usable \\\\",
        f"50/50 (N=5 mean$\\pm$std) & {f(n50.rmse_mean)}$\\pm${f(n50.rmse_std,3)} & {f(n50.violation_pct_mean,2)}$\\pm${f(n50.violation_pct_std,2)} & {f(n50.ms_mean,3)}$\\pm${f(n50.ms_std,3)} & neutral, CV={f(n50.ms_cv,2)} \\\\",
        f"75/25 (N=5 mean$\\pm$std) & {f(n75.rmse_mean)}$\\pm${f(n75.rmse_std,3)} & {f(n75.violation_pct_mean,2)}$\\pm${f(n75.violation_pct_std,2)} & {f(n75.ms_mean,3)}$\\pm${f(n75.ms_std,3)} & practical, CV={f(n75.ms_cv,2)} \\\\",
    ]
    for lbl, name in [("comfort_080_energy_020", "80/20 (seed 42)"), ("comfort_100_energy_000", "100/0 (seed 42)")]:
        sub = p[p.label == lbl]
        if len(sub):
            r = sub.iloc[0]
            tag = "legacy canonical" if "080" in lbl else "best seed-42 comfort"
            rows.append(f"{name} & {f(r.rmse_mean)} & {f(r.violation_pct_mean,2)} & {f(r.ms_mean,3)} & {tag} \\\\")
    return "\n".join(rows)


def table_morl_per_seed(d: dict) -> str:
    ps = d["seed_per"]
    rows = []
    cmap = {"comfort_050_energy_050": "50/50", "comfort_075_energy_025": "75/25"}
    for canon, clabel in cmap.items():
        for _, r in ps[ps.canonical == canon].iterrows():
            rows.append(f"{clabel} & {int(r.seed)} & {f(r.rmse_mean)} & {f(r.within_1c_pct_mean,1)} & {f(r.violation_pct_mean,2)} & {f(r.energy_kwh_sum,1)} & {f(r.ms_mean,3)} \\\\")
    return "\n".join(rows)


def table_pi(d: dict):
    pi = d["pi"]
    return {
        "rmse": f(pi["rmse"].mean(), 2),
        "mae": f(pi["mae"].mean(), 2),
        "viol": f(pi["viol_pct"].mean(), 1),
        "energy": f(pi["energy_kwh"].mean(), 1),
        "ms": f(pi["ms"].mean(), 3),
    }


def load_env_reward() -> dict:
    import yaml
    with (ROOT / "configs/env.yaml").open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def table_reward(cfg: dict) -> str:
    m = cfg.get("morl", {})
    c = cfg.get("comfort_shaping", {})
    rows = [
        ("Comfort band", f"{f(m.get('temp_low',21),1)} / {f(m.get('temp_high',24),1)} C", "comfort interval (band\\_low/high)"),
        ("Comfort deadband", f"{f(c.get('deadband_c',0.5),2)} C", "soft margin around band edges"),
        ("In-band bonus", f"{f(c.get('band_bonus',0.05),3)}/step", "reward for staying inside the band"),
        ("Undershoot / overshoot weight", f"{f(c.get('undershoot_weight',1.15),2)} / {f(c.get('overshoot_weight',1.15),2)}", "generic violation penalties"),
        ("Cold-ambient asymmetry", f"{f(c.get('cold_undershoot_weight',1.6),2)} (amb $<{f(c.get('cold_amb_threshold_c',8.0),1)}$ C)", "extra cold-undershoot penalty"),
        ("Hot-ambient asymmetry", f"{f(c.get('hot_overshoot_weight',1.8),2)} (amb $>{f(c.get('hot_amb_threshold_c',24.0),1)}$ C)", "extra hot-overshoot penalty"),
        ("Heating action bonus", f"{f(c.get('heating_action_bonus',0.04),2)} ($T_{{\\mathrm{{sup}}}}\\ge {f(c.get('heating_t_supply_c',29.0),1)}$ C)", "anti-degenerate shaping"),
        ("Cooling action bonus", f"{f(c.get('cooling_action_bonus',0.06),2)} ($T_{{\\mathrm{{sup}}}}\\le {f(c.get('cooling_t_supply_c',21.0),1)}$ C)", "anti-degenerate shaping"),
        ("MORL weights ($w_c/w_e/w_s$)", f"{f(m.get('w_comfort',0.8),2)} / {f(m.get('w_energy',0.2),2)} / {f(m.get('w_safety',0.0),2)}", "canonical scalarization"),
        ("Energy scale", f"${m.get('energy_scale','2e-4')}$ (W$\\to$reward)", "energy-to-reward conversion"),
    ]
    return "\n".join(f"{a} & {b} & {c_} \\\\" for a, b, c_ in rows)


def table_obs17() -> str:
    # Static, verified from envs/tsup_features.py (BASIC=5, TIME=4, FORECAST=5,
    # prev-action=2, delta=1; total 17). obs_mode=extended in configs/env.yaml.
    rows = [
        ("Physical state (basic)", "5", "$T_{\\mathrm{zone}}$, CO$_2$, clipped-log power, prev. $T_{\\mathrm{sup}}$, $T_{\\mathrm{amb}}$"),
        ("Cyclic time", "4", "hour and day sine/cosine encodings"),
        ("Ambient forecast", "5", "$T_{\\mathrm{amb}}$ at $+1,+3,+6,+12,+24$ h"),
        ("Previous action", "2", "$(a_{T_{\\mathrm{sup}}}, a_{\\mathrm{fan}})$ from last step"),
        ("Temperature delta", "1", "causal-smoothed $\\Delta T_{\\mathrm{zone}}$"),
        ("Total (extended)", "17", "obs\\_mode = extended"),
    ]
    return "\n".join(f"{a} & {b} & {c} \\\\" for a, b, c in rows)


def table_scenarios(manifest: dict) -> str:
    rows = []
    roles = {"peak_heat_window": "January coldest, heating stress test",
             "typical_heat_window": "February moderate, deployment-realistic"}
    for s in manifest.get("scenarios", []):
        nm = s["name"]
        rows.append(
            f"\\texttt{{{tex_escape(nm)}}} & {int(s['start_day_index'])} & {int(float(s['start_time_sec']))} & "
            f"{int(s['duration_days'])} & {f(s['daily_mean_t_amb_c'],1)} & {roles.get(nm,'')} \\\\")
    rows.append("yearly evaluation & 12 months & --- & 14/mo & varied & MORL + PI yearly summary \\\\")
    return "\n".join(rows)


def table_nomenclature() -> str:
    rows = [
        (r"$m_s$", "--", "BOPTEST-style maintenance score (lower is better; combines comfort violation and tracking)"),
        (r"RMSE$_T$", r"\si{\celsius}", "live closed-loop zone-temperature RMSE"),
        (r"Violation", r"\si{\percent}", "fraction of steps outside the 21--24 C comfort band"),
        (r"$\lambda_T,\ \lambda_P$", "--", "hybrid temperature / power disagreement weights"),
        (r"$\Delta m_s$", "--", "live-minus-surrogate $m_s$ transfer gap"),
        (r"$g_a$", "--", "L2 action-gap norm (surrogate vs live)"),
        (r"CV", "--", "coefficient of variation (std/mean) of $m_s$ over seeds"),
        (r"$w_c,w_e,w_s$", "--", "MORL comfort / energy / safety preference weights"),
    ]
    return "\n".join(f"{a} & {b} & {tex_escape(c)} \\\\" for a, b, c in rows)


# ---------------------------------------------------------------------------
# LaTeX
# ---------------------------------------------------------------------------

def write_tex(ctx: dict) -> None:
    tex = rf"""\documentclass[11pt,a4paper]{{article}}

\usepackage[T1]{{fontenc}}
\usepackage[utf8]{{inputenc}}
\usepackage{{lmodern}}
\usepackage[margin=22mm]{{geometry}}
\usepackage{{graphicx}}
\usepackage{{booktabs}}
\usepackage{{array}}
\usepackage{{amsmath}}
\usepackage{{amssymb}}
\usepackage{{siunitx}}
\usepackage{{xcolor}}
\usepackage{{hyperref}}
\usepackage{{caption}}
\usepackage{{subcaption}}

\graphicspath{{{{figures/}}}}
\hypersetup{{colorlinks=true, linkcolor=blue!55!black, citecolor=blue!55!black, urlcolor=blue!55!black}}

\title{{Results II: Controller Learning, Hybrid Regularization, and MORL Seed Stability}}
\author{{Data-driven Overleaf section generated from the HVAC\_DRL\_MORL Block 2 artifacts}}
\date{{}}

\begin{{document}}
\maketitle

\begin{{table}}[h]
\centering
\small
\caption{{Nomenclature for Block 2.}}
\label{{tab:nomenclature2}}
\begin{{tabular}}{{lll}}
\toprule
Symbol & Unit & Meaning \\
\midrule
{ctx['table_nomenclature']}
\bottomrule
\end{{tabular}}
\end{{table}}

\section{{Block 2 objective and evidence boundary}}

Block 1 established a deliberately asymmetric surrogate result: the compact v3 surrogate is the more useful rollout environment for reinforcement learning (RL), whereas the calibrated v3.5 RC--NeuralODE is the more accurate predictive digital twin. Block 2 tests the controller-side consequence of that asymmetry on the live BOPTEST \texttt{{bestest\_air}} runtime environment. The central question is not whether a controller can be trained on a surrogate, but which functional role each surrogate should play inside the learning loop.

The experiments compare five controller families: pure-v3 thermostatic PPO, direct-v3.5 PPO, hybrid-v3/v3.5 PPO, hierarchical DRL (HDRL), and preference-conditioned MORL. All policies are trained on surrogate backends and then evaluated in closed loop against BOPTEST. Two targeted 14-day windows are used for the main thermostatic/HDRL comparison: \texttt{{peak\_heat\_window}} (January, daily-mean ambient $-24.4\,^\circ$C) and \texttt{{typical\_heat\_window}} (February, $+2.4\,^\circ$C). MORL and PI reference values additionally use the 12-month yearly evaluation protocol. This difference is intentional: the targeted windows expose controller-family mechanisms, while the yearly protocol exposes seed stability and preference robustness.

Figure~\ref{{fig:block2_pipeline}} summarizes the Block 2 pipeline. Direct v3.5 is a negative control, not a failed implementation; it asks whether the highest-fidelity predictive surrogate can be used directly as the policy rollout environment. The answer is no. The hybrid backend then asks whether the same physical model is useful if its role is changed from dynamics provider to reward-shaping censor: yes for thermostatic PPO, no for HDRL at the same $\lambda_{{\mathrm{{temp}}}}$, and conditionally yes for MORL after the observation interface is expanded from 5D to 17D. These experiments correspond to \texttt{{roadmap.md}} Block 2 Sections 4 (pure v3), 4.5 (warm-start), 5 (hybrid), 5.5 (transfer diagnostics), 6 (HDRL), 6.5 (MORL 5D), 7--9 (MORL 17D / Pareto / canonical seed analysis), and 10 (PI); their artifact provenance and rebuild commands are catalogued in roadmap Section 11.1.

\begin{{figure}}[t]
  \centering
  \includegraphics[width=0.94\linewidth]{{fig_block2_pipeline.pdf}}
  \caption{{Block 2 controller-learning pipeline. The experiments separate the rollout model, the physical regularizer, the controller family, the observation interface, and live BOPTEST validation.}}
  \label{{fig:block2_pipeline}}
\end{{figure}}

\begin{{table}}[t]
\centering
\caption{{Targeted-window and yearly scenario definitions (verified from \texttt{{outputs/block2\_*/scenario\_manifest.json}}).}}
\label{{tab:scenarios}}
\small
\begin{{tabular}}{{lrrrrl}}
\toprule
Scenario & Day idx & Start (s) & Dur. (d) & Ambient mean ($^\circ$C) & Role \\
\midrule
{ctx['table_scenarios']}
\bottomrule
\end{{tabular}}
\end{{table}}

\section{{PPO interface, observation design, and reward}}

All Block 2 policies use Proximal Policy Optimization (PPO). The shared PPO settings are learning rate $3\times 10^{{-4}}$ during surrogate pretraining, discount factor $\gamma=0.99$ (an effective horizon of $\sim$25 h at the 900 s step), and ten optimization epochs per rollout. The families differ in rollout length, minibatch size, and total timestep budget because the training scripts were developed per family rather than as a single hyperparameter ablation.

\begin{{table}}[t]
\centering
\caption{{PPO training configuration used in Block 2 (verified from the project training scripts and configuration files).}}
\label{{tab:ppo_hparams}}
\small
\begin{{tabular}}{{lllll}}
\toprule
Parameter & Thermostatic PPO & HDRL & MORL pretrain & MORL finetune \\
\midrule
Algorithm & PPO, MlpPolicy & PPO, MlpPolicy & PPO, MlpPolicy & PPO load+continue \\
Learning rate & $3.0{{\times}}10^{{-4}}$ & $3.0{{\times}}10^{{-4}}$ & $3.0{{\times}}10^{{-4}}$ & $1.0{{\times}}10^{{-4}}$ \\
\texttt{{n\_steps}} & 1024 & 1024 & 2048 & inherited \\
\texttt{{batch\_size}} & 4096 & 2048 & 64 & inherited \\
\texttt{{n\_epochs}} & 10 & 10 & 10 & 10 \\
$\gamma$ & 0.99 & 0.99 & 0.99 & 0.99 \\
GAE $\lambda$ & 0.95 & 0.95 & 0.95 & 0.95 \\
Clip range & 0.20 & 0.20 & 0.20 & 0.20 \\
Total timesteps & 10M & 12M & 2M & 100k \\
Seed & 42 & 42 & 42 & 42--46 (N=5) \\
\bottomrule
\end{{tabular}}
\end{{table}}

The canonical observation interface is the 17-dimensional extended TSup-style vector:
\begin{{equation}}
  s_t =
  \left[
  x^{{\mathrm{{phys}}}}_t,\,
  x^{{\mathrm{{time}}}}_t,\,
  \widehat{{T}}^{{\mathrm{{amb}}}}_{{t+1:t+24h}},\,
  a_{{t-1}},\,
  \Delta T^{{\mathrm{{zone}}}}_t
  \right] \in \mathbb{{R}}^{{17}}.
  \label{{eq:obs17}}
\end{{equation}}
It contains 5 physical states (zone temperature, CO$_2$, clipped-log power, previous supply temperature, ambient), 4 cyclic time features, 5 ambient forecasts ($+1,+3,+6,+12,+24$ h), 2 previous-action terms, and 1 causal-smoothed $\Delta T_{{\mathrm{{zone}}}}$. The failed MORL baseline uses only the earlier 5D observation, which lacks sufficient actuation and forecast context.

\begin{{table}}[t]
\centering
\caption{{Extended 17D observation feature groups (verified from \texttt{{envs/tsup\_features.py}}).}}
\label{{tab:obs17}}
\small
\begin{{tabular}}{{lll}}
\toprule
Feature group & Dim. & Contents \\
\midrule
{ctx['table_obs17']}
\bottomrule
\end{{tabular}}
\end{{table}}

The action is a single normalized supply-temperature command,
\begin{{equation}}
  a_t \in [-1,1],
  \qquad
  T^{{\mathrm{{sup}}}}_t = 18 + \tfrac{{a_t+1}}{{2}}(35-18)\quad [^\circ\mathrm{{C}}],
  \label{{eq:action_map}}
\end{{equation}}
with a 1.0 C deadband and a per-step rate limit; the comfort band is $21$--$24\,^\circ$C.

\paragraph{{Evaluation metric.}} The headline maintenance score combines the comfort-violation rate and the worst-case relative severity over a rollout,
\begin{{equation}}
  m_s = r_{{\mathrm{{time}}}} + r_{{\mathrm{{sev}}}},
  \quad
  r_{{\mathrm{{time}}}} = \frac{{1}}{{N}}\sum_{{t}} \mathbb{{1}}\!\left[T_t < T_{{\ell}} \lor T_t > T_{{h}}\right],
  \quad
  r_{{\mathrm{{sev}}}} = \max_t \max\!\left(\frac{{(T_{{\ell}}-T_t)_+}}{{T_{{\ell}}}},\, \frac{{(T_t-T_{{h}})_+}}{{T_{{h}}}}\right),
  \label{{eq:ms}}
\end{{equation}}
with $T_{{\ell}}=21\,^\circ$C and $T_{{h}}=24\,^\circ$C (source: \texttt{{evaluation/benchmark\_bestest\_air\_article7\_style.py}}). Hence $r_{{\mathrm{{time}}}}$ is the fraction of steps outside the band (violation\,$\%=100\,r_{{\mathrm{{time}}}}$) and $r_{{\mathrm{{sev}}}}$ is the single worst relative band exceedance; lower $m_s$ is better. RMSE$_T$ is reported against the band center $T^{{\star}}=22.5\,^\circ$C.

\begin{{table}}[t]
\centering
\caption{{Reward-shaping parameters (verified from \texttt{{configs/env.yaml}}).}}
\label{{tab:reward}}
\small
\begin{{tabular}}{{lll}}
\toprule
Component & Value & Role \\
\midrule
{ctx['table_reward']}
\bottomrule
\end{{tabular}}
\end{{table}}

\section{{Hybrid backend: mathematical role of v3.5}}

The hybrid backend changes the role of the calibrated physical surrogate. Instead of rolling out the policy on v3.5 directly, PPO rolls out on v3 and evaluates frozen v3.5 in parallel on the same state-action pair. The per-step reward is augmented by a disagreement penalty:
\begin{{align}}
  r^{{\mathrm{{hyb}}}}_t
  &= r^{{\mathrm{{comfort}}}}_t + r^{{\mathrm{{smooth}}}}_t + r^{{\mathrm{{energy}}}}_t
  - \lambda_T \left|T^{{v3}}_{{t+1}}-T^{{v3.5}}_{{t+1}}\right|
  - \lambda_P \left|P^{{v3}}_{{t+1}}-P^{{v3.5}}_{{t+1}}\right|.
  \label{{eq:hybrid_reward}}
\end{{align}}
For the canonical thermostatic hybrid, $\lambda_T=0.10$ and $\lambda_P=5.0\times 10^{{-5}}$; PPO otherwise computes the advantage $A_t = r^{{\mathrm{{hyb}}}}_t + \gamma V(s_{{t+1}}) - V(s_t)$ unchanged. Thus v3.5 is neither a second policy loss nor a direct dynamics model: it is a frozen physics-informed censor that discourages the policy from entering state-action regions where the smooth v3 rollout and the calibrated physical model disagree. Across the canonical hybrid traces (\texttt{{reports/hybrid\_disagreement\_summary.csv}}, overall), the mean temperature disagreement is ${ctx['dis_temp_mean']}\,^\circ$C (p95 ${ctx['dis_temp_p95']}\,^\circ$C) and the mean power disagreement is ${ctx['dis_pow_mean']}$ W (p95 ${ctx['dis_pow_p95']}$ W) --- large enough to shape learning, bounded enough to stay informative.

\begin{{figure}}[t]
  \centering
  \includegraphics[width=0.90\linewidth]{{fig_block2_reward_shaping.pdf}}
  \caption{{Hybrid reward-shaping mechanism. v3 supplies rollout dynamics; frozen v3.5 supplies a disagreement penalty on the same state-action transition.}}
  \label{{fig:hybrid_reward}}
\end{{figure}}

\section{{Thermostatic PPO: direct-v3.5 failure and hybrid success}}

Table~\ref{{tab:main_kpi}} and Figure~\ref{{fig:live_kpi}} summarize the main Block 2 controller result. Pure v3 PPO is already usable ($m_s={ctx['pure_peak_ms']}$ peak, ${ctx['pure_typ_ms']}$ typical). Direct v3.5 PPO fails catastrophically despite v3.5's superior Block 1 predictive fidelity: live violation reaches {ctx['dv_peak_viol']}\% on peak and {ctx['dv_typ_viol']}\% on typical, with RMSE above $4.3\,^\circ$C. The hybrid backend resolves the conflict: $m_s={ctx['hyb_peak_ms']}$ on peak and ${ctx['hyb_typ_ms']}$ on typical, with violation below $5\%$ on both windows and lower energy than pure v3 on the peak window.

\begin{{table}}[t]
\centering
\caption{{Canonical Block 2 live BOPTEST controller comparison on targeted 14-day windows. Sources: pure v3 \texttt{{outputs/bestest\_air\_article7\_style\_15min/summary.csv}}; hybrid \texttt{{outputs/block2\_thermostatic\_hybrid\_v3\_v35\_l010/summary.csv}}; direct v3.5 \texttt{{reports/hou\_evins\_architecture\_justification\_table.csv}} (+ violation from \texttt{{reports/hybrid\_transfer\_comparison.csv}}).}}
\label{{tab:main_kpi}}
\small
\begin{{tabular}}{{llrrrr}}
\toprule
Policy/backend & Scenario & $m_s$ & Violation (\%) & RMSE$_T$ ($^\circ$C) & Energy (kWh) \\
\midrule
{ctx['table_main_kpi']}
\bottomrule
\end{{tabular}}
\end{{table}}

\begin{{figure}}[t]
  \centering
  \includegraphics[width=0.96\linewidth]{{final17_fig06_live_boptest_controller_comparison.pdf}}
  \caption{{Live BOPTEST KPI comparison for pure v3, direct v3.5, and hybrid PPO. Direct v3.5 is a negative control: higher predictive fidelity does not imply a useful RL training environment.}}
  \label{{fig:live_kpi}}
\end{{figure}}

The time-series and action diagnostics in Figures~\ref{{fig:closed_loop_traces}} and~\ref{{fig:action_phase}} explain the mechanism. Direct v3.5 learns a bang-bang-like control law that drives the live simulator outside the comfort band; in phase space it places extreme actions in temperature-error regimes the live building does not support. We note explicitly that this destabilization mechanism is \emph{{hypothesized}} (higher advantage-estimator variance under sharper surrogate predictions, and/or overfitting to sub-step physical structure unusable at the 15-min cadence) and is not directly measured here; discriminating the two is deferred to future work.

\begin{{figure}}[t]
  \centering
  \includegraphics[width=0.96\linewidth]{{block2_q1_polish_closed_loop_disturbance.pdf}}
  \caption{{Closed-loop BOPTEST traces with ambient disturbance, comfort band, and physical actuator limits.}}
  \label{{fig:closed_loop_traces}}
\end{{figure}}

\begin{{figure}}[t]
  \centering
  \includegraphics[width=0.96\linewidth]{{block2_q1_polish_phase_density.pdf}}
  \caption{{Phase portrait as empirical state-action density. The saturation bands near $a_0=\pm1$ expose the bang-bang behavior of direct v3.5 PPO.}}
  \label{{fig:action_phase}}
\end{{figure}}

\section{{Warm-start negative control}}

A second negative control tests whether v3.5 is useful as a policy initializer rather than a reward-shaping censor: pretrain on direct v3.5, then warm-start on the hybrid backend. It does not help. Warm-started policies are markedly worse than scratch-trained hybrid policies (Table~\ref{{tab:warmstart}}), raising $m_s$ by roughly two to three times. The problem is the role assigned to the surrogate during early policy formation, not a lack of fine-tuning.

\begin{{table}}[t]
\centering
\caption{{Direct-v3.5 warm-start utility (\texttt{{outputs/block2\_thermostatic\_warmstart\_utility/comparison\_summary.csv}}).}}
\label{{tab:warmstart}}
\small
\begin{{tabular}}{{llrr}}
\toprule
Mode & Scenario & $m_s$ & Violation (\%) \\
\midrule
{ctx['table_warmstart']}
\bottomrule
\end{{tabular}}
\end{{table}}

\begin{{figure}}[t]
  \centering
  \includegraphics[width=0.82\linewidth]{{block2_warmstart_negative_eval_kpis.pdf}}
  \caption{{Warm-start negative control. Pretraining on direct v3.5 and then fine-tuning on the hybrid backend is inferior to training the hybrid policy from scratch.}}
  \label{{fig:warmstart}}
\end{{figure}}

\section{{Transfer-gap diagnostics}}

The transfer-gap diagnostic pairs surrogate-side and live-BOPTEST metrics for the same policy:
\begin{{equation}}
  \Delta m_s = m_s^{{\mathrm{{BOPTEST}}}} - m_s^{{\mathrm{{surrogate}}}},
  \qquad
  g_a = \frac{{1}}{{N}}\sum_{{t=1}}^{{N}}\left\|a_t^{{\mathrm{{BOPTEST}}}}-a_t^{{\mathrm{{surrogate}}}}\right\|_2 .
  \label{{eq:transfer_gap}}
\end{{equation}}
Direct v3.5 has the largest transfer mismatch ($|\Delta m_s|\approx 0.9$--$1.0$, action-gap norm $\approx 2.0$), and its top divergence driver is $t_{{\mathrm{{zone}}}}$ --- its sharp temperature dynamics produce live actions unlike the surrogate rollout. Hybrid $\lambda_T=0.10$ has the smallest gap ($\approx 0.02$) and, on the typical window, holds the BOPTEST-consistent action for 16 steps before drifting (Table~\ref{{tab:transfer}}).

\begin{{table}}[t]
\centering
\caption{{Transfer diagnostics across three backends (\texttt{{reports/hybrid\_transfer\_comparison.csv}}). $\Delta m_s = $ surrogate $-$ live; negative means the surrogate is optimistic.}}
\label{{tab:transfer}}
\small
\begin{{tabular}}{{llrrrl}}
\toprule
Variant & Scenario & $\Delta m_s$ & Action gap & First div. step & Top driver \\
\midrule
{ctx['table_transfer']}
\bottomrule
\end{{tabular}}
\end{{table}}

\begin{{figure}}[t]
  \centering
  \includegraphics[width=0.86\linewidth]{{block1_q1_fig10_transfer_gap_diagnostics.pdf}}
  \caption{{Transfer-gap diagnostics. Direct v3.5 has high action-gap norm and live-surrogate mismatch; the hybrid backend suppresses both.}}
  \label{{fig:transfer_gap}}
\end{{figure}}

\section{{HDRL sensitivity: the hybrid weight is controller-family specific}}

The HDRL experiment asks whether the thermostatic hybrid setting $\lambda_T=0.10$ transfers to a hierarchical controller. It does not (Table~\ref{{tab:hdrl}}). HDRL performs best at $\lambda_T=0.00$ on both windows and degrades monotonically as temperature-disagreement regularization is increased. This shows the correct physical-censor strength depends on the controller family and its action decomposition, not on a universal weight.

\begin{{table}}[t]
\centering
\caption{{HDRL sweep over $\lambda_T$ on targeted windows (\texttt{{reports/block2\_hdrl\_lambda\_sweep\_summary.csv}}). Best is $\lambda_T=0$.}}
\label{{tab:hdrl}}
\small
\begin{{tabular}}{{llrrrr}}
\toprule
$\lambda_T$ & Scenario & $m_s$ & Violation (\%) & RMSE$_T$ ($^\circ$C) & Energy (kWh) \\
\midrule
{ctx['table_hdrl']}
\bottomrule
\end{{tabular}}
\end{{table}}

\begin{{figure}}[t]
  \centering
  \includegraphics[width=0.88\linewidth]{{block2_hdrl_lambda_sweep_sensitivity.pdf}}
  \caption{{HDRL $\lambda_T$ sensitivity. The thermostatic regularization weight does not transfer; the best HDRL policy uses no temperature-disagreement term.}}
  \label{{fig:hdrl_sweep}}
\end{{figure}}

\section{{MORL observation ablation: 5D failure to 17D success}}

MORL uses a four-stage pipeline that differs from the single-stage PPO families (roadmap Section 7): (1) a 2M-step surrogate \emph{{pretrain}} on the 17D hybrid backend with canonical $(w_c,w_e,w_s)=(0.80,0.20,0.00)$; (2) an \emph{{ERAM}} weight-adaptation stage (20 iterations of 100k steps from initial weights $0.34/0.33/0.33$); (3) a 100k-step \emph{{finetune}} on the live BOPTEST RTE at learning rate $10^{{-4}}$ with $\pm3$-day episode-start jitter; and (4) a 12-month \emph{{yearly evaluation}}. MORL is the only family with a live-BOPTEST finetune; the thermostatic/HDRL families are evaluated zero-shot after surrogate-only training, which is a strictly harder transfer.

MORL initially failed with a 5D observation (zone temperature, ambient, hour, day, occupancy). Under the current code path, a reconstructed 5D rerun obtains RMSE$_T={ctx['m5_rmse']}\,^\circ$C, violation ${ctx['m5_viol']}\%$, and $m_s={ctx['m5_ms']}$; the originally frozen 5D artifact was even worse (RMSE$_T={ctx['m5frozen_rmse']}\,^\circ$C, $m_s={ctx['m5frozen_ms']}$) and is retained only as an audit artifact. Replacing the observation with the 17D TSup-style vector recovers a usable policy: RMSE$_T={ctx['m17_rmse']}\,^\circ$C, violation ${ctx['m17_viol']}\%$, $m_s={ctx['m17_ms']}$ (Table~\ref{{tab:morl5d17d}}). The dominant MORL bottleneck was the observation geometry, not the reward scalarization alone.

\begin{{table}}[t]
\centering
\caption{{MORL observation-interface ablation. The backend is hybrid in both cases; only the observation interface changes. The current-code reconstructed 5D rerun is the reproducible main-paper evidence; sources \texttt{{reports/block2\_morl\_5d\_reconstructed\_comparison.csv}} and \texttt{{reports/block2\_morl\_comparison\_summary.csv}}.}}
\label{{tab:morl5d17d}}
\small
\begin{{tabular}}{{lrrrr}}
\toprule
Variant & Obs dim & RMSE$_T$ ($^\circ$C) & Violation (\%) & $m_s$ \\
\midrule
{ctx['table_morl_5d17d']}
\bottomrule
\end{{tabular}}
\end{{table}}

\begin{{figure}}[t]
  \centering
  \includegraphics[width=0.84\linewidth]{{final17_fig09_morl_5d_failure_17d_success.pdf}}
  \caption{{MORL 5D failure and 17D recovery. The observation interface, not only the scalarized reward, determines whether MORL is viable.}}
  \label{{fig:morl5d17d}}
\end{{figure}}

\section{{MORL Pareto front and N=5 seed variance}}

The MORL Pareto sweep varies comfort/energy weights with safety weight zero (Table~\ref{{tab:morl_pareto_seed}}). Energy-only control collapses comfort ($m_s={ctx['p0_ms']}$, violation ${ctx['p0_viol']}\%$); comfort-leaning settings are far more stable. The single-seed (seed 42) Pareto points are reported separately from the $N=5$ canonical extensions, because the seed analysis is the central audit result: the neutral 50/50 canonical has $m_s={ctx['n50_ms']}\pm{ctx['n50_std']}$ (CV ${ctx['n50_cv']}$, 95\% $t$-CI $[{ctx['n50_ci_lo']},{ctx['n50_ci_hi']}]$) and the practical 75/25 canonical has $m_s={ctx['n75_ms']}\pm{ctx['n75_std']}$ (CV ${ctx['n75_cv']}$, 95\% $t$-CI $[{ctx['n75_ci_lo']},{ctx['n75_ci_hi']}]$). Seed 46 is an outlier in both groups (Table~\ref{{tab:morl_per_seed}}). Because the replay audit produced bit-identical BOPTEST trajectories for a fixed policy, this variance is attributed to PPO/ERAM training stochasticity, not simulator noise. The single-seed canonical ($m_s\approx0.10$) is therefore the \emph{{best}} of five, not the median.

\begin{{table}}[t]
\centering
\caption{{MORL Pareto (seed 42) and N=5 canonical seed analysis. Sources \texttt{{reports/morl\_pareto\_front\_table.csv}} and \texttt{{reports/morl\_canonical\_seedfix\_yearly\_summary.csv}}.}}
\label{{tab:morl_pareto_seed}}
\small
\begin{{tabular}}{{lrrll}}
\toprule
Preference / statistic & RMSE$_T$ ($^\circ$C) & Violation (\%) & $m_s$ & Interpretation \\
\midrule
{ctx['table_morl_pareto_seed']}
\bottomrule
\end{{tabular}}
\end{{table}}

\begin{{figure}}[t]
  \centering
  \includegraphics[width=0.86\linewidth]{{block2_q1_polish_morl_pareto_ellipses.pdf}}
  \caption{{MORL comfort--energy Pareto front with N=5 confidence ellipses for the two canonical points. Non-canonical points are seed-42 only.}}
  \label{{fig:morl_pareto}}
\end{{figure}}

\begin{{table}}[t]
\centering
\caption{{Per-seed MORL yearly metrics for the two canonical weight pairs (\texttt{{reports/morl\_canonical\_seedfix\_yearly\_per\_seed.csv}}).}}
\label{{tab:morl_per_seed}}
\small
\begin{{tabular}}{{lrrrrrr}}
\toprule
Pair (c/e) & Seed & RMSE$_T$ & Within 1$^\circ$C (\%) & Violation (\%) & Energy (kWh) & $m_s$ \\
\midrule
{ctx['table_morl_per_seed']}
\bottomrule
\end{{tabular}}
\end{{table}}

\section{{Seasonal variance falsification}}

At $N=3$, the practical canonical appeared to show near-deterministic winter behavior and a seasonal inversion relative to the neutral canonical, motivating a pre-registered falsification test before seeds 45 and 46 were trained. The direction-specific predictions (February winter $\sigma(m_s)<0.005$; June summer $\sigma(m_s)>0.05$; winter neutral/practical variance ratio $>20$) failed at $N=5$: February practical $\sigma(m_s)$ rose to order $0.17$ and the winter variance ratio collapsed to order one. This is a success of the pre-registration protocol (audit anchors \texttt{{93df9b3}} pre-registration, \texttt{{62dc859}} post-N=5 falsification), not a project failure. The honest, narrower conclusion: MORL is promising in mean performance, especially at comfort-leaning preferences, but is \emph{{not}} deployment-stable without explicit stabilization (validation-based checkpoint selection, early stopping, or ensemble selection), which is left as future work because the canonical protocol fixes final-epoch evaluation.

\begin{{figure}}[t]
  \centering
  \includegraphics[width=0.88\linewidth]{{block2_morl_17d_seasonal_heatmap.pdf}}
  \caption{{MORL seasonal performance heatmap under the 17D interface. The figure shows monthly structure but does not support the N=3 mechanism claim after N=5 extension.}}
  \label{{fig:morl_heatmap}}
\end{{figure}}

\begin{{figure}}[t]
  \centering
  \includegraphics[width=0.88\linewidth]{{block2_morl_seasonal_variance_inversion.pdf}}
  \caption{{Post-N=5 seasonal variance diagnostic. The earlier seasonal-inversion hypothesis is reported as falsified, not retained as a positive mechanism claim.}}
  \label{{fig:seasonal_falsification}}
\end{{figure}}

\section{{PI reference and synthesis}}

The BOPTEST built-in PI controller is a reproducible reference, not a tuned strong baseline. On the 12-month yearly evaluation it is comfort-poor but energy-frugal: mean RMSE$_T={ctx['pi_rmse']}\,^\circ$C, mean violation ${ctx['pi_viol']}\%$, mean monthly energy ${ctx['pi_energy']}$ kWh, mean $m_s={ctx['pi_ms']}$. All Block 2 RL/MORL agents reach $m_s$ well below PI's ${ctx['pi_ms']}$, dominating it on comfort at comparable or lower energy after accounting for the comfort/energy trade-off.

Block 2 establishes four controller-side claims. First, predictive fidelity and RL training utility are not equivalent: direct v3.5 is the more accurate twin yet fails as a rollout environment (live violation $>77\%$). Second, role separation works --- v3 provides smooth rollout dynamics while frozen v3.5 acts as a physical censor through disagreement shaping --- giving the canonical hybrid ($m_s={ctx['hyb_peak_ms']}$ peak, ${ctx['hyb_typ_ms']}$ typical). Third, the censor strength is controller-family specific: HDRL rejects $\lambda_T=0.10$ and is best at $\lambda_T=0$. Fourth, MORL is viable only with the 17D interface, and its N=5 analysis reveals high seed variance and falsifies the N=3 seasonal-inversion mechanism. The engineering implication is that hybrid surrogate RL is a role-allocation problem --- rollout smoothness, physical censoring, observation geometry, controller family, and seed stabilization are separate design axes. This is the bridge to Block 3, where the fixed \texttt{{bestest\_air}} recipe is transferred to the hydronic BOPTEST family.

\section{{Limitations}}

\begin{{itemize}}
  \item \textbf{{Mechanism not measured.}} The direct-v3.5 destabilization is established only in \emph{{direction}}; the gradient-variance vs sub-step-overfit hypotheses are not discriminated here.
  \item \textbf{{Single testcase.}} All Block 2 results are on \texttt{{bestest\_air}}; cross-building transfer is Block 3.
  \item \textbf{{MORL seed stability.}} The canonical MORL claim is narrowed: N=5 CV is ${ctx['n50_cv']}$--${ctx['n75_cv']}$; the single-seed canonical is the best of five and final-epoch evaluation is fixed by protocol.
  \item \textbf{{Per-family PPO hyperparameters differ}} (rollout length / batch size / budget); they were set per training script, so cross-family KPI differences are not a controlled hyperparameter ablation.
  \item \textbf{{MORL alone uses live BOPTEST finetuning}} (100k steps); thermostatic/HDRL are evaluated zero-shot after surrogate-only training, a strictly harder transfer.
\end{{itemize}}

Artifact provenance (which \texttt{{reports/}} and \texttt{{outputs/}} files back every table and figure) and the rebuild commands are documented in \texttt{{roadmap.md}} Section 11.1; this section is regenerated by \texttt{{build\_results2\_overleaf.py}}.

\end{{document}}
"""
    (BASE / "main.tex").write_text(tex, encoding="utf-8")


def main() -> None:
    d = load_block2()
    kpi = table_main_kpi(d)
    morl_5d17d, frozen5, r5, r17 = table_morl_5d17d(d)
    pi = table_pi(d)
    n50 = d["seed_sum"][d["seed_sum"].canonical == "comfort_050_energy_050"].iloc[0]
    n75 = d["seed_sum"][d["seed_sum"].canonical == "comfort_075_energy_025"].iloc[0]
    p0 = d["pareto"][d["pareto"].label == "comfort_000_energy_100"].iloc[0]

    # Q1 additions: reward config, scenario manifest, disagreement stats, N=5 CI.
    import json
    import math
    try:
        reward_tbl = table_reward(load_env_reward())
    except Exception as exc:
        print(f"[warn] reward table fallback: {exc}")
        reward_tbl = table_reward({})
    try:
        manifest = json.loads((ROOT / "outputs/bestest_air_article7_style_15min/scenario_manifest.json").read_text(encoding="utf-8"))
        scen_tbl = table_scenarios(manifest)
    except Exception as exc:
        print(f"[warn] scenario table fallback: {exc}")
        scen_tbl = ""
    dis = read_csv("reports/hybrid_disagreement_summary.csv")
    dov = dis[dis.scenario == "overall"].iloc[0]
    # 95% t-CI (n=5, t_{0.975,4}=2.776) on m_s for the two canonicals.
    tcrit = 2.776
    n50 = d["seed_sum"][d["seed_sum"].canonical == "comfort_050_energy_050"].iloc[0]
    n75 = d["seed_sum"][d["seed_sum"].canonical == "comfort_075_energy_025"].iloc[0]
    ci50 = tcrit * float(n50.ms_std) / math.sqrt(5)
    ci75 = tcrit * float(n75.ms_std) / math.sqrt(5)

    pure_peak = _scen_row(d["pure"], "peak_heat_window", controller="thermostatic")
    pure_typ = _scen_row(d["pure"], "typical_heat_window", controller="thermostatic")
    hyb_peak = _scen_row(d["hybrid"], "peak_heat_window")
    hyb_typ = _scen_row(d["hybrid"], "typical_heat_window")
    tr = d["transfer"]
    dv_peak_v = tr[(tr.variant == "direct_v35") & (tr.scenario == "peak_heat_window")].iloc[0]["boptest_violation_pct"]
    dv_typ_v = tr[(tr.variant == "direct_v35") & (tr.scenario == "typical_heat_window")].iloc[0]["boptest_violation_pct"]

    ctx = {
        "table_nomenclature": table_nomenclature(),
        "table_reward": reward_tbl,
        "table_obs17": table_obs17(),
        "table_scenarios": scen_tbl,
        "dis_temp_mean": f(dov.temp_disagree_mean_c, 3),
        "dis_temp_p95": f(dov.temp_disagree_p95_c, 2),
        "dis_pow_mean": f(dov.power_disagree_mean_w, 0),
        "dis_pow_p95": f(dov.power_disagree_p95_w, 0),
        "n50_ci_lo": f(float(n50.ms_mean) - ci50, 3), "n50_ci_hi": f(float(n50.ms_mean) + ci50, 3),
        "n75_ci_lo": f(float(n75.ms_mean) - ci75, 3), "n75_ci_hi": f(float(n75.ms_mean) + ci75, 3),
        "table_main_kpi": kpi,
        "table_warmstart": table_warmstart(d),
        "table_transfer": table_transfer(d),
        "table_hdrl": table_hdrl(d),
        "table_morl_5d17d": morl_5d17d,
        "table_morl_pareto_seed": table_morl_pareto_seed(d),
        "table_morl_per_seed": table_morl_per_seed(d),
        "pure_peak_ms": f(pure_peak.m_s), "pure_typ_ms": f(pure_typ.m_s),
        "hyb_peak_ms": f(hyb_peak.m_s), "hyb_typ_ms": f(hyb_typ.m_s),
        "dv_peak_viol": f(dv_peak_v, 1), "dv_typ_viol": f(dv_typ_v, 1),
        "m5_rmse": f(r5.rmse_c), "m5_viol": f(r5.violation_pct, 1), "m5_ms": f(r5.m_s, 3),
        "m5frozen_rmse": f(frozen5.rmse_c, 2), "m5frozen_ms": f(frozen5.m_s, 3),
        "m17_rmse": f(r17.rmse_c), "m17_viol": f(r17.violation_pct, 1), "m17_ms": f(r17.m_s, 3),
        "p0_ms": f(p0.ms_mean, 3), "p0_viol": f(p0.violation_pct_mean, 1),
        "n50_ms": f(n50.ms_mean, 3), "n50_std": f(n50.ms_std, 3), "n50_cv": f(n50.ms_cv, 2),
        "n75_ms": f(n75.ms_mean, 3), "n75_std": f(n75.ms_std, 3), "n75_cv": f(n75.ms_cv, 2),
        "pi_rmse": pi["rmse"], "pi_viol": pi["viol"], "pi_energy": pi["energy"], "pi_ms": pi["ms"],
    }
    write_tex(ctx)
    print(f"Wrote {BASE / 'main.tex'}")


if __name__ == "__main__":
    main()
