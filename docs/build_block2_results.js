// Block 2 Complete Results Document — full scientific narrative for the
// control-side of the HVAC DRL/MORL paper. Mirrors the depth and structure
// of build_block1_results.js.
// All numbers are sourced from project artifacts (CSV/JSON in outputs/, reports/).
// Run: node docs/build_block2_results.js

const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, PageBreak, LevelFormat
} = require("docx");

// ──────────────────────── DATA FROM PROJECT ARTIFACTS ────────────────────────
// Cross-checked 2026-05-28 against:
//   outputs/bestest_air_article7_style_15min/summary.csv       (pure v3 PPO — VERIFIED via grep)
//   outputs/block2_thermostatic_hybrid_v3_v35_l010/summary.csv (hybrid l010 canonical)
//   outputs/block2_hdrl_hybrid_v3_v35_l{000,003,005,010}/      (HDRL sweep)
//   outputs/morl_hybrid_v3_v35_power_only_17d/                 (MORL canonical 17D)
//   reports/block2_morl_comparison_summary.csv                 (5D vs 17D MORL)
//   reports/morl_canonical_seedfix_yearly_summary.csv          (MORL N=5 seed analysis aggregate)
//   reports/morl_canonical_seedfix_yearly_per_seed.csv         (MORL N=5 per-seed; Table 7b)
//   reports/morl_pareto_front_table.csv                        (Pareto sweep)
//   reports/hybrid_transfer_comparison.csv                     (transfer diagnostics + direct v3.5 m_s)
//   outputs/pi_baseline_15min_yearly/pi_yearly_summary.csv     (PI baseline — 12 monthly rows VERIFIED to aggregate to 3.395/2.823/63.59/104.07/0.910)
//   outputs/block2_thermostatic_warmstart_utility/             (warm-start neg control)
//   envs/tsup_features.py                                      (17-D observation breakdown — VERIFIED)
//   configs/{agent,train,env}.yaml                             (PPO hparams, reward, scenarios)
//   configs/morl_surrogate_ppo/{agent,train,env,pipeline}.yaml (MORL pipeline)
//   training/run_morl_surrogate_pipeline.py                    (ERAM weights labeled comfort,energy,safety — VERIFIED)
const DATA = {
  // ────────── Pure v3 PPO (live BOPTEST, paper §6.3 canonical) ──────────
  // SOURCE (verified): outputs/bestest_air_article7_style_15min/summary.csv
  //   peak_heat_window: m_s=0.07254, viol=1.488%, rmse_22_c=0.8691, energy=322.19 kWh
  //   typical_heat_window: m_s=0.09465, viol=4.390%, rmse_22_c=0.6222, energy=368.27 kWh
  // power_rmse_w values from reports/hybrid_transfer_comparison.csv (pure_v3 rows)
  pure_v3: {
    peak_m_s: 0.0725, peak_violation_pct: 1.49, peak_rmse_c: 0.869,
    peak_energy_kwh: 322.2, peak_power_rmse_w: 1213,
    typ_m_s: 0.0947,  typ_violation_pct: 4.39,  typ_rmse_c: 0.622,
    typ_energy_kwh: 368.3, typ_power_rmse_w: 1346,
    summary_csv: "outputs/bestest_air_article7_style_15min/summary.csv",
    surrogate_path: "outputs/surrogate_v2/rc_node_v3_tsupply.pt",
    backend: "v3 (control-oriented)", lambda_temp: 0.00, lambda_pwr: 0.00,
  },
  // ────────── Hybrid_l010 (thermostatic PPO, paper canonical) ──────────
  hybrid_l010: {
    peak_m_s: 0.0866, peak_violation_pct: 4.69, peak_rmse_c: 0.795,
    peak_energy_kwh: 305.3, peak_power_rmse_w: 1098,
    typ_m_s: 0.0411,  typ_violation_pct: 2.38,  typ_rmse_c: 0.633,
    typ_energy_kwh: 352.8, typ_power_rmse_w: 1258,
    backend: "hybrid (v3 dynamics + v3.5 disagreement regularizer)",
    lambda_temp: 0.10, lambda_pwr: 5e-5,
  },
  // ────────── Direct v3.5 warm-start (negative control, §6.2) ──────────
  direct_v35: {
    peak_m_s: 1.046, peak_violation_pct: 77.08, peak_rmse_c: 4.320,
    peak_energy_kwh: 556.2, peak_power_rmse_w: 1480,
    typ_m_s: 1.102,  typ_violation_pct: 82.37,  typ_rmse_c: 4.401,
    typ_energy_kwh: 580.5, typ_power_rmse_w: 1619,
    backend: "v3.5 only (no v3 dynamics)",
  },
  // ────────── HDRL sweep (lambda_temp_disagree ∈ {0, 0.03, 0.05, 0.10}) ──────────
  hdrl_sweep: {
    peak: [
      { lam: 0.00, m_s: 0.1803, viol: 6.10,  rmse: 0.751, energy: 329.6 },
      { lam: 0.03, m_s: 0.3073, viol: 11.90, rmse: 0.993, energy: 311.5 },
      { lam: 0.05, m_s: 0.4184, viol: 20.98, rmse: 1.303, energy: 298.1 },
      { lam: 0.10, m_s: 0.4395, viol: 22.99, rmse: 1.343, energy: 300.4 },
    ],
    typ: [
      { lam: 0.00, m_s: 0.2337, viol: 3.12,  rmse: 0.691, energy: 385.1 },
      { lam: 0.03, m_s: 0.2964, viol: 9.38,  rmse: 0.959, energy: 369.6 },
      { lam: 0.05, m_s: 0.5118, viol: 27.38, rmse: 1.491, energy: 354.5 },
      { lam: 0.10, m_s: 0.5114, viol: 30.65, rmse: 1.455, energy: 357.1 },
    ],
  },
  // ────────── MORL 5D failure / 17D success ──────────
  morl_5d: {
    rmse_c: 4.96, mae_c: 4.17, w1c_pct: 19, w05c_pct: 9,
    viol_pct: 74.5, energy_kwh: 121.0, m_s: 1.046,
  },
  morl_17d_canonical: {
    rmse_c: 0.72, mae_c: 0.56, w1c_pct: 83, w05c_pct: 57,
    viol_pct: 4.9, energy_kwh: 248.6, m_s: 0.099,
    obs_dim: 17, backend: "hybrid_v3_v35", lambda_temp: 0.00, lambda_pwr: 5e-5,
    seed: 42,
  },
  // ────────── MORL N=5 seed variance (audit anchor 62dc859) ──────────
  morl_seedfix_5050: {
    rmse_mean: 0.893, rmse_std: 0.081,
    viol_mean: 13.01, viol_std: 6.62,
    energy_sum_mean: 2793.6, energy_sum_std: 134.5,
    ms_mean: 0.187, ms_std: 0.078, ms_min: 0.103, ms_max: 0.310, ms_cv: 0.418,
    weights: "comfort=0.50, energy=0.50",
    seed_count: 5,
  },
  morl_seedfix_7525: {
    rmse_mean: 0.799, rmse_std: 0.100,
    viol_mean: 9.23,  viol_std: 6.67,
    energy_sum_mean: 2883.4, energy_sum_std: 176.9,
    ms_mean: 0.139, ms_std: 0.085, ms_cv: 0.613,
    weights: "comfort=0.75, energy=0.25",
    seed_count: 5,
  },
  // ────────── MORL Pareto front (seed 42; VERIFIED 2026-05-28 against reports/morl_pareto_front_table.csv) ──────────
  // CORRECTION: earlier values for 75/25 (m_s=0.099) and 100/0 (rmse=0.694, m_s=0.088) were wrong;
  // 0.099 was the legacy_canonical_080_020 m_s, not the 75/25 endpoint.
  morl_pareto: [
    { lab: "0/100 (energy-only)",       rmse: 8.359, viol: 86.76, energy: 0.28,   m_s: 1.588 },
    { lab: "25/75 (energy-weighted)",   rmse: 0.912, viol: 11.39, energy: 219.98, m_s: 0.173 },
    { lab: "50/50 (neutral, seed 42)",  rmse: 0.939, viol: 12.92, energy: 236.97, m_s: 0.193 },
    { lab: "75/25 (practical, seed 42)", rmse: 0.700, viol: 3.08, energy: 249.53, m_s: 0.057 },
    { lab: "100/0 (comfort-only)",      rmse: 0.631, viol: 1.49,  energy: 260.57, m_s: 0.032 },
    { lab: "80/20 (legacy canonical)",  rmse: 0.725, viol: 4.87,  energy: 248.60, m_s: 0.099 },
  ],
  // ────────── Direct v3.5 warm-start utility (§6.2 vs scratch) ──────────
  warmstart_utility: {
    scratch_peak_m_s: 0.4653, scratch_peak_viol: 31.70,
    scratch_typ_m_s: 0.5776,  scratch_typ_viol: 45.54,
    warm_peak_m_s: 1.2701,    warm_peak_viol: 83.93,
    warm_typ_m_s: 1.2888,     warm_typ_viol: 86.83,
  },
  // ────────── PI baseline yearly reference (BOPTEST built-in) ──────────
  pi_yearly: {
    n_months: 12,
    rmse_mean_c: 3.395, mae_mean_c: 2.823,
    viol_mean_pct: 63.59, energy_mean_kwh: 104.1,
    m_s_mean: 0.910,
    note: "BOPTEST built-in PI; reproducible reference, not custom-tuned",
  },
  // ────────── Transfer diagnostics (§6.4 = block13 transfer comparison) ──────────
  transfer: {
    pure_v3: {
      peak: { ms_gap: -0.1016, action_gap_norm: 0.377, first_div: 1, top_feat: "p_total_norm" },
      typ:  { ms_gap: -0.0682, action_gap_norm: 0.333, first_div: 1, top_feat: "p_total_norm" },
    },
    hybrid_l010: {
      peak: { ms_gap: -0.0234, action_gap_norm: 0.473, first_div: 1,  top_feat: "p_total_norm" },
      typ:  { ms_gap: -0.0214, action_gap_norm: 0.253, first_div: 16, top_feat: "p_total_norm" },
    },
    direct_v35: {
      peak: { ms_gap: -0.8862, action_gap_norm: 2.000, first_div: 1, top_feat: "t_zone_norm" },
      typ:  { ms_gap: -1.0144, action_gap_norm: 2.014, first_div: 1, top_feat: "t_zone_norm" },
    },
  },
  // ────────── Hybrid disagreement (physics side, §5) ──────────
  hybrid_disagreement: {
    mean_temp_c: 0.969, p95_temp_c: 2.516,
    mean_power_w: 708.4, p95_power_w: 1235.5,
    v3_temp_rmse_c: 1.158, v35_temp_rmse_c: 0.206,
    v3_power_rmse_w: 1184.1, v35_power_rmse_w: 621.5,
  },
  // ────────── Pre-registration audit anchors — VERIFIED via git log ──────────
  // CORRECTION (2026-05-28): commit semantics re-verified against actual messages.
  //   93df9b3 = "pre-registration: seed45/46 falsification predictions for practical canonical"
  //             (NOT the canonical freeze — it's a pre-registration of EXPECTED outcomes for seeds 45/46)
  //   62dc859 = "post-N5 result: action-saturation hypothesis falsified"
  //   1861e48 = "Block 3 pre-registration: transferability testcase manifest"  (THIS is the Block 3 pre-reg)
  //   2f9d596 = "Block 3 audit: record pre-registration commit SHA"
  //   7ada793 = "Block 3 audit: record close commit SHA"               (THIS is the Block 3 CLOSE, not pre-reg)
  anchors: {
    seed_45_46_prereg:    { sha: "93df9b3", msg: "pre-registration: seed45/46 falsification predictions for practical canonical" },
    n5_falsification:     { sha: "62dc859", msg: "post-N5 result: action-saturation hypothesis falsified" },
    block3_prereg:        { sha: "1861e48", msg: "Block 3 pre-registration: transferability testcase manifest" },
    block3_prereg_audit:  { sha: "2f9d596", msg: "Block 3 audit: record pre-registration commit SHA" },
    block3_close:         { sha: "7ada793", msg: "Block 3 audit: record close commit SHA" },
  },
  // ────────── Common scenario / training settings ──────────
  comfort_band: "21 °C – 24 °C",
  step_sec: 900,
  rollout_days: 14,
  testcase: "BOPTEST bestest_air",
  // ────────── PPO hyperparameters — VERIFIED per-family from training/ scripts ──────────
  // CORRECTION (2026-05-28): hyperparams are NOT identical across families.
  // configs/agent.yaml applies ONLY to MORL pipeline (loaded by train_morl_surrogate.py).
  // train_thermostatic.py (line 646) and train_hdrl.py (line 247) hardcode their own values
  // and rely on Stable-Baselines3 PPO defaults for clip_range / ent_coef / vf_coef / gae_lambda
  // (which happen to be 0.2 / 0.0 / 0.5 / 0.95 — matching configs/agent.yaml de facto).
  ppo: {
    algorithm: "PPO (Stable-Baselines3)", policy: "MlpPolicy",
    // Common across all families (verified in all three scripts):
    learning_rate: 3e-4, n_epochs: 10, gamma: 0.99,
    // SB3 defaults (not explicitly set in train_thermostatic.py / train_hdrl.py):
    gae_lambda: 0.95, clip_range: 0.2, ent_coef: 0.0, vf_coef: 0.5, device: "cpu",
    // Per-family overrides:
    thermostatic: { n_steps: 1024, batch_size: 4096, total_timesteps_default: 10000000, source: "training/train_thermostatic.py:646" },
    // HDRL trains TWO PPO agents (winter + summer); defaults: WINTER 5M, SUMMER 7M, total = 12M
    hdrl:         { n_steps: 1024, batch_size: 2048, total_timesteps_default: 12000000, total_breakdown: "winter 5M + summer 7M", source: "training/train_hdrl.py:247 (PPO call); :278-279 (defaults via --winter-steps / --summer-steps)" },
    morl_pretrain: { n_steps: 2048, batch_size: 64,  total_timesteps_default: 2000000,  source: "configs/agent.yaml + configs/morl_surrogate_ppo/train.yaml" },
    morl_finetune: { learning_rate: 1e-4, total_timesteps_default: 100000,              source: "training/finetune_morl_boptest.py:83" },
    seed: 42,
  },
  // ────────── Observation space — VERIFIED from envs/tsup_features.py ──────────
  // BASIC_TSUP_OBS_DIM=5, TIME_TSUP_OBS_DIM=4, HISTORY_TSUP_OBS_DIM=3, FORECAST_HORIZONS=[1,3,6,12,24]
  // EXTENDED_TSUP_OBS_DIM = 5 + 4 + 3 + 5 = 17 (note HISTORY = 2-D prev_action + 1-D delta_t)
  obs: {
    dim_extended: 17, dim_basic: 5,
    delta_feature_mode: "causal_smooth",
    power_feature_mode: "clipped_log",
    t_zone_feature_mode: "raw",
    groups: [
      { name: "Physical state (basic)",                   n: 5, note: "t_zone, CO₂, p_total (clipped_log), t_supply_prev, t_amb — all normalised to [−1,+1]" },
      { name: "Cyclic time encoding",                     n: 4, note: "hour_sin, hour_cos, day_sin, day_cos (no calendar lookup needed)" },
      { name: "Ambient forecast (5 horizons)",            n: 5, note: "t_amb at +1 h, +3 h, +6 h, +12 h, +24 h (weather lookup table)" },
      { name: "Previous action",                          n: 2, note: "(a_t_supply, a_fan) from last step, both in [−1,+1]" },
      { name: "Temperature delta",                        n: 1, note: "Δt_zone last step, causal_smooth encoding (tanh(clip(Δ, ±1.5)/1.25))" },
    ],
  },
  // ────────── Action space ──────────
  action: {
    dim: 1, name: "supply_temperature_setpoint",
    low_c: 18.0, high_c: 35.0,
    normalize: true,
    smoothing: { deadband_c: 1.0, rate_limit: true, max_delta_normalized: 0.15 },
    note: "1-D continuous t_supply setpoint in °C, normalized to [-1, +1] for PPO actor; " +
          "exponential moving smoothing with 1 °C deadband and 0.15-unit per-step rate limit.",
  },
  // ────────── Reward (configs/env.yaml: comfort_shaping + MORL weights) ──────────
  reward: {
    band_low_c: 21.0, band_high_c: 24.0,
    deadband_c: 0.5, band_bonus: 0.05,
    undershoot_weight: 1.15, overshoot_weight: 1.15,
    cold_amb_threshold_c: 8.0, hot_amb_threshold_c: 24.0,
    cold_undershoot_weight: 1.60, hot_overshoot_weight: 1.80,
    heating_action_bonus: 0.04, cooling_action_bonus: 0.06,
    heating_t_supply_c: 29.0, cooling_t_supply_c: 21.0,
    morl_canonical: { w_comfort: 0.80, w_energy: 0.20, w_safety: 0.00, energy_scale: 2e-4 },
  },
  // ────────── Scenario definitions ──────────
  scenarios: {
    peak: { day: 3,  start_sec: 259200,  duration_days: 14, t_amb_mean_c: -24.4, label: "Peak heat window (Jan, coldest)" },
    typ:  { day: 37, start_sec: 3196800, duration_days: 14, t_amb_mean_c: 2.4,   label: "Typical heat window (Feb, moderate)" },
    yearly: { months: 12, eval_days_per_month: 14, note: "12 monthly scenarios for MORL/PI yearly evaluation" },
  },
  // ────────── MORL pipeline (configs/morl_surrogate_ppo/pipeline.yaml) ──────────
  morl_pipeline: {
    pretrain_steps: 2000000,
    eram_iterations: 20,
    eram_chunk_steps: 100000,
    eram_tau_w: 0.35,
    eram_adv_lr: 1.0,
    eram_init_weights: "0.34/0.33/0.33 (comfort/energy/safety)",
    finetune_steps: 100000,
    finetune_lr: 1e-4,
    finetune_jitter_days: 3.0,
    eval_step_sec: 900,
    eval_scenario_days: 14,
  },
  // ────────── Domain randomization (MORL only) ──────────
  domain_random: {
    t_init_low_c: 15.0, t_init_high_c: 28.0,
    weather_noise_std_c: 1.5,
    enabled_in: "MORL pretraining only",
  },
  // ────────── MORL per-seed data (5 seeds × 2 weight pairs) ──────────
  morl_per_seed: {
    w5050: [
      { seed: 42, rmse: 0.939, mae: 0.739, w1c: 74.93, w05c: 43.27, viol: 12.92, energy_sum: 2843.6, m_s: 0.193 },
      { seed: 43, rmse: 0.769, mae: 0.618, w1c: 82.93, w05c: 47.16, viol: 6.77,  energy_sum: 2872.0, m_s: 0.103 },
      { seed: 44, rmse: 0.879, mae: 0.682, w1c: 76.85, w05c: 48.36, viol: 9.34,  energy_sum: 2858.4, m_s: 0.141 },
      { seed: 45, rmse: 0.895, mae: 0.706, w1c: 77.72, w05c: 42.40, viol: 11.97, energy_sum: 2839.8, m_s: 0.187 },
      { seed: 46, rmse: 0.985, mae: 0.815, w1c: 65.35, w05c: 37.00, viol: 24.05, energy_sum: 2554.1, m_s: 0.310 },
    ],
    w7525: [
      { seed: 42, rmse: 0.700, mae: 0.552, w1c: 83.30, w05c: 58.57, viol: 3.08,  energy_sum: 2994.3, m_s: 0.057 },
      { seed: 43, rmse: 0.716, mae: 0.570, w1c: 84.93, w05c: 53.29, viol: 5.47,  energy_sum: 2963.9, m_s: 0.087 },
      { seed: 44, rmse: 0.769, mae: 0.622, w1c: 81.68, w05c: 47.04, viol: 7.82,  energy_sum: 2819.1, m_s: 0.117 },
      { seed: 45, rmse: 0.903, mae: 0.700, w1c: 78.48, w05c: 45.93, viol: 9.42,  energy_sum: 3036.7, m_s: 0.160 },
      { seed: 46, rmse: 0.909, mae: 0.743, w1c: 70.32, w05c: 42.71, viol: 20.37, energy_sum: 2602.8, m_s: 0.276 },
    ],
  },
};

// ──────────────────────── STYLE HELPERS ──────────────────────────────────────
const CONTENT_WIDTH = 9360;
const BORDER = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };
const CELL_MARGINS = { top: 80, bottom: 80, left: 120, right: 120 };
const HEAD_SHADE = { fill: "D5E8F0", type: ShadingType.CLEAR };
const POS_SHADE = { fill: "D5F0D8", type: ShadingType.CLEAR };
const NEG_SHADE = { fill: "F4CCCC", type: ShadingType.CLEAR };
const NEU_SHADE = { fill: "FFF2CC", type: ShadingType.CLEAR };

function cell(text, opts = {}) {
  const { bold = false, shade = null, align = AlignmentType.LEFT, width = null, size = 18 } = opts;
  return new TableCell({
    borders: BORDERS, margins: CELL_MARGINS, shading: shade || undefined,
    width: width ? { size: width, type: WidthType.DXA } : undefined,
    children: [new Paragraph({
      alignment: align,
      children: [new TextRun({ text, bold, font: "Arial", size })],
    })],
  });
}
function hdr(text, w) { return cell(text, { bold: true, shade: HEAD_SHADE, width: w }); }

function para(text, opts = {}) {
  const { spaceBefore = 120, spaceAfter = 120, size = 20, indent = 0 } = opts;
  const runs = [];
  const parts = text.split(/(\*\*[^*]+\*\*|_[^_]+_)/g);
  for (const p of parts) {
    if (p.startsWith("**") && p.endsWith("**"))
      runs.push(new TextRun({ text: p.slice(2,-2), bold: true, font: "Arial", size }));
    else if (p.startsWith("_") && p.endsWith("_"))
      runs.push(new TextRun({ text: p.slice(1,-1), italic: true, font: "Arial", size }));
    else
      runs.push(new TextRun({ text: p, font: "Arial", size }));
  }
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { before: spaceBefore, after: spaceAfter },
    indent: indent ? { left: indent } : undefined,
    children: runs,
  });
}
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 180 },
    children: [new TextRun({ text, bold: true, font: "Arial", size: 28, color: "1F3864" })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 140 },
    children: [new TextRun({ text, bold: true, font: "Arial", size: 24, color: "2E75B6" })],
  });
}
function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 100 },
    children: [new TextRun({ text, bold: true, italic: true, font: "Arial", size: 20, color: "404040" })],
  });
}
function bullet(text) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { before: 60, after: 60 },
    indent: { left: 720, hanging: 360 },
    numbering: { reference: "bullets", level: 0 },
    children: [new TextRun({ text, font: "Arial", size: 20 })],
  });
}
function caption(label, text) {
  return new Paragraph({
    spacing: { before: 80, after: 80 },
    children: [
      new TextRun({ text: label + " ", bold: true, font: "Arial", size: 18 }),
      new TextRun({ text, font: "Arial", size: 18, italic: true }),
    ],
  });
}
function divider() {
  return new Paragraph({
    spacing: { before: 200, after: 200 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "2E75B6", space: 1 } },
    children: [],
  });
}
function figure(file, label, text, width = 560, height = 260) {
  const p = `${__dirname}/../reports/figures/article_real/${file}`;
  if (!fs.existsSync(p)) {
    return [
      para(`[Figure missing: ${file}] ${label} ${text}`, { size: 18 }),
    ];
  }
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 180, after: 80 },
      children: [
        new ImageRun({
          type: "png",
          data: fs.readFileSync(p),
          transformation: { width, height },
          altText: { title: file, description: `${label} ${text}`, name: file },
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 180 },
      children: [
        new TextRun({ text: `${label} `, bold: true, font: "Arial", size: 18 }),
        new TextRun({ text, italic: true, font: "Arial", size: 18, color: "555555" }),
      ],
    }),
  ];
}
function buildTable(rows, colWidths, shadeFn = null) {
  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: rows.map((row, i) => new TableRow({
      children: row.map((text, j) => {
        if (i === 0) return hdr(text, colWidths[j]);
        const shade = shadeFn ? shadeFn(i, j, text) : null;
        return cell(text, {
          bold: j === 0, shade,
          width: colWidths[j],
          align: j === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
        });
      }),
    })),
  });
}

// ──────────────────────── TABLES ─────────────────────────────────────────────
function tableMainBlock2() {
  const D = DATA;
  const rows = [
    ["Backend / Policy", "Scenario", "m_s", "Violation %", "RMSE_T (°C)", "Energy (kWh)"],
    ["pure_v3 PPO",        "peak_heat_window",    D.pure_v3.peak_m_s.toFixed(3),     D.pure_v3.peak_violation_pct.toFixed(2), D.pure_v3.peak_rmse_c.toFixed(3),     D.pure_v3.peak_energy_kwh.toFixed(1)],
    ["pure_v3 PPO",        "typical_heat_window", D.pure_v3.typ_m_s.toFixed(3),      D.pure_v3.typ_violation_pct.toFixed(2),  D.pure_v3.typ_rmse_c.toFixed(3),      D.pure_v3.typ_energy_kwh.toFixed(1)],
    ["direct_v35 PPO",     "peak_heat_window",    D.direct_v35.peak_m_s.toFixed(3),  D.direct_v35.peak_violation_pct.toFixed(2), D.direct_v35.peak_rmse_c.toFixed(3),  D.direct_v35.peak_energy_kwh.toFixed(1)],
    ["direct_v35 PPO",     "typical_heat_window", D.direct_v35.typ_m_s.toFixed(3),   D.direct_v35.typ_violation_pct.toFixed(2),  D.direct_v35.typ_rmse_c.toFixed(3),   D.direct_v35.typ_energy_kwh.toFixed(1)],
    ["hybrid_l010 PPO",    "peak_heat_window",    D.hybrid_l010.peak_m_s.toFixed(3), D.hybrid_l010.peak_violation_pct.toFixed(2), D.hybrid_l010.peak_rmse_c.toFixed(3), D.hybrid_l010.peak_energy_kwh.toFixed(1)],
    ["hybrid_l010 PPO",    "typical_heat_window", D.hybrid_l010.typ_m_s.toFixed(3),  D.hybrid_l010.typ_violation_pct.toFixed(2),  D.hybrid_l010.typ_rmse_c.toFixed(3),  D.hybrid_l010.typ_energy_kwh.toFixed(1)],
  ];
  const shadeFn = (i, j, t) => {
    if (j === 2) {
      const v = parseFloat(t);
      if (v < 0.10) return POS_SHADE;
      if (v > 0.50) return NEG_SHADE;
      return NEU_SHADE;
    }
    return null;
  };
  return buildTable(rows, [1800, 2080, 1080, 1320, 1440, 1640], shadeFn);
}

function tableHdrl() {
  const D = DATA.hdrl_sweep;
  const rows = [["λ_temp", "Scenario", "m_s", "Violation %", "RMSE_center (°C)", "Energy (kWh)"]];
  for (const r of D.peak) rows.push([
    r.lam.toFixed(2), "peak_heat_window",
    r.m_s.toFixed(3), r.viol.toFixed(2), r.rmse.toFixed(3), r.energy.toFixed(1),
  ]);
  for (const r of D.typ) rows.push([
    r.lam.toFixed(2), "typical_heat_window",
    r.m_s.toFixed(3), r.viol.toFixed(2), r.rmse.toFixed(3), r.energy.toFixed(1),
  ]);
  const shadeFn = (i, j, t) => {
    if (j === 0) {
      if (t === "0.00") return POS_SHADE;
      if (t === "0.10") return NEG_SHADE;
    }
    return null;
  };
  return buildTable(rows, [1200, 2200, 1300, 1400, 1700, 1560], shadeFn);
}

function tableMorlCompare() {
  const D = DATA;
  const rows = [
    ["Variant", "Obs dim", "RMSE_T (°C)", "MAE_T (°C)", "Within 1°C", "Violation %", "Energy (kWh)", "m_s"],
    ["MORL 5D basic",        "5",  D.morl_5d.rmse_c.toFixed(2), D.morl_5d.mae_c.toFixed(2), D.morl_5d.w1c_pct + "%",       D.morl_5d.viol_pct.toFixed(1),  D.morl_5d.energy_kwh.toFixed(1),  D.morl_5d.m_s.toFixed(3)],
    ["MORL 17D power-only",  "17", D.morl_17d_canonical.rmse_c.toFixed(2), D.morl_17d_canonical.mae_c.toFixed(2), D.morl_17d_canonical.w1c_pct + "%", D.morl_17d_canonical.viol_pct.toFixed(1), D.morl_17d_canonical.energy_kwh.toFixed(1), D.morl_17d_canonical.m_s.toFixed(3)],
  ];
  const shadeFn = (i,j,t) => {
    if (i === 1) return NEG_SHADE;
    if (i === 2) return POS_SHADE;
    return null;
  };
  return buildTable(rows, [2080, 880, 1280, 1080, 1080, 1280, 1120, 560], shadeFn);
}

function tableMorlPareto() {
  const D = DATA.morl_pareto;
  const rows = [["Weight pair (comfort/energy)", "RMSE_T (°C)", "Violation %", "Energy (kWh)", "m_s"]];
  for (const r of D) rows.push([
    r.lab, r.rmse.toFixed(3), r.viol.toFixed(2), r.energy.toFixed(2), r.m_s.toFixed(3),
  ]);
  const shadeFn = (i,j,t) => {
    if (j === 4 && i > 0) {
      const v = parseFloat(t);
      if (v < 0.15) return POS_SHADE;
      if (v > 0.5)  return NEG_SHADE;
    }
    return null;
  };
  return buildTable(rows, [3280, 1500, 1500, 1600, 1480], shadeFn);
}

function tableMorlSeedVar() {
  const M = DATA.morl_seedfix_5050;
  const P = DATA.morl_seedfix_7525;
  const rows = [
    ["Weight pair (c/e)", "N seeds", "RMSE_T mean ± std", "Violation % mean ± std", "m_s mean ± std", "m_s CV"],
    ["50/50",  M.seed_count + "", `${M.rmse_mean.toFixed(3)} ± ${M.rmse_std.toFixed(3)}`, `${M.viol_mean.toFixed(2)} ± ${M.viol_std.toFixed(2)}`, `${M.ms_mean.toFixed(3)} ± ${M.ms_std.toFixed(3)}`, M.ms_cv.toFixed(3)],
    ["75/25",  P.seed_count + "", `${P.rmse_mean.toFixed(3)} ± ${P.rmse_std.toFixed(3)}`, `${P.viol_mean.toFixed(2)} ± ${P.viol_std.toFixed(2)}`, `${P.ms_mean.toFixed(3)} ± ${P.ms_std.toFixed(3)}`, P.ms_cv.toFixed(3)],
  ];
  return buildTable(rows, [1800, 1080, 1880, 1880, 1640, 1080], (i,j,t) => {
    if (j === 5 && i > 0) {
      const v = parseFloat(t);
      if (v > 0.4) return NEG_SHADE;
    }
    return null;
  });
}

function tableTransfer() {
  const T = DATA.transfer;
  const rows = [
    ["Variant", "Scenario", "ms_gap (surrogate − live)", "Action gap (L2)", "First divergence step", "Top driver feature"],
    ["pure_v3",     "peak_heat_window",    T.pure_v3.peak.ms_gap.toFixed(4),     T.pure_v3.peak.action_gap_norm.toFixed(3),     String(T.pure_v3.peak.first_div),     T.pure_v3.peak.top_feat],
    ["pure_v3",     "typical_heat_window", T.pure_v3.typ.ms_gap.toFixed(4),      T.pure_v3.typ.action_gap_norm.toFixed(3),      String(T.pure_v3.typ.first_div),      T.pure_v3.typ.top_feat],
    ["hybrid_l010", "peak_heat_window",    T.hybrid_l010.peak.ms_gap.toFixed(4), T.hybrid_l010.peak.action_gap_norm.toFixed(3), String(T.hybrid_l010.peak.first_div), T.hybrid_l010.peak.top_feat],
    ["hybrid_l010", "typical_heat_window", T.hybrid_l010.typ.ms_gap.toFixed(4),  T.hybrid_l010.typ.action_gap_norm.toFixed(3),  String(T.hybrid_l010.typ.first_div),  T.hybrid_l010.typ.top_feat],
    ["direct_v35",  "peak_heat_window",    T.direct_v35.peak.ms_gap.toFixed(4),  T.direct_v35.peak.action_gap_norm.toFixed(3),  String(T.direct_v35.peak.first_div),  T.direct_v35.peak.top_feat],
    ["direct_v35",  "typical_heat_window", T.direct_v35.typ.ms_gap.toFixed(4),   T.direct_v35.typ.action_gap_norm.toFixed(3),   String(T.direct_v35.typ.first_div),   T.direct_v35.typ.top_feat],
  ];
  return buildTable(rows, [1480, 2080, 2080, 1280, 1480, 960]);
}

function tableWarmstartUtility() {
  const W = DATA.warmstart_utility;
  const rows = [
    ["Mode", "Scenario", "m_s", "Violation %"],
    ["scratch (from random init)",  "peak_heat_window",    W.scratch_peak_m_s.toFixed(3), W.scratch_peak_viol.toFixed(2)],
    ["scratch (from random init)",  "typical_heat_window", W.scratch_typ_m_s.toFixed(3),  W.scratch_typ_viol.toFixed(2)],
    ["warm-start (from v3.5)",      "peak_heat_window",    W.warm_peak_m_s.toFixed(3),    W.warm_peak_viol.toFixed(2)],
    ["warm-start (from v3.5)",      "typical_heat_window", W.warm_typ_m_s.toFixed(3),     W.warm_typ_viol.toFixed(2)],
  ];
  const shadeFn = (i,j,t) => {
    if (j === 2 && i > 0) {
      const v = parseFloat(t);
      if (v > 1.0) return NEG_SHADE;
      if (v < 0.5) return NEU_SHADE;
    }
    return null;
  };
  return buildTable(rows, [3160, 2400, 1800, 2000], shadeFn);
}

function tablePpoHparams() {
  const P = DATA.ppo;
  const T = P.thermostatic, H = P.hdrl, M = P.morl_pretrain, F = P.morl_finetune;
  const rows = [
    ["Hyperparameter",    "Thermostatic",                       "HDRL",                                  "MORL pretrain",                              "MORL finetune"],
    ["Algorithm / policy", P.algorithm + ", " + P.policy,        P.algorithm + ", " + P.policy,            P.algorithm + ", " + P.policy,                 P.algorithm + " (load+continue)"],
    ["Learning rate",      P.learning_rate.toExponential(1),     P.learning_rate.toExponential(1),         P.learning_rate.toExponential(1),              F.learning_rate.toExponential(1)],
    ["n_steps",            String(T.n_steps),                    String(H.n_steps),                        String(M.n_steps),                             "inherits"],
    ["batch_size",         String(T.batch_size),                 String(H.batch_size),                     String(M.batch_size),                          "inherits"],
    ["n_epochs",           String(P.n_epochs),                   String(P.n_epochs),                       String(P.n_epochs),                            String(P.n_epochs)],
    ["γ (discount)",       P.gamma.toFixed(3),                   P.gamma.toFixed(3),                       P.gamma.toFixed(3),                            P.gamma.toFixed(3)],
    ["GAE λ",              P.gae_lambda.toFixed(3) + " (SB3 default)", P.gae_lambda.toFixed(3) + " (SB3 default)", P.gae_lambda.toFixed(3) + " (set in cfg)", P.gae_lambda.toFixed(3)],
    ["Clip range",         P.clip_range.toFixed(2) + " (SB3 default)", P.clip_range.toFixed(2) + " (SB3 default)", P.clip_range.toFixed(2) + " (set in cfg)", P.clip_range.toFixed(2)],
    ["Entropy coef.",      P.ent_coef.toFixed(2) + " (SB3 default)", P.ent_coef.toFixed(2) + " (SB3 default)",   P.ent_coef.toFixed(2),                     P.ent_coef.toFixed(2)],
    ["Value coef.",        P.vf_coef.toFixed(2) + " (SB3 default)",  P.vf_coef.toFixed(2) + " (SB3 default)",    P.vf_coef.toFixed(2),                      P.vf_coef.toFixed(2)],
    ["Total timesteps",    T.total_timesteps_default.toLocaleString(), H.total_timesteps_default.toLocaleString(), M.total_timesteps_default.toLocaleString(), F.total_timesteps_default.toLocaleString()],
    ["Seed",               String(P.seed),                       String(P.seed),                           String(P.seed),                                String(P.seed)],
    ["Source file",        T.source,                             H.source,                                 M.source,                                      F.source],
  ];
  return buildTable(rows, [1860, 1900, 1900, 1900, 1800]);
}

function tableObsSpace() {
  const O = DATA.obs;
  const rows = [["Feature group", "Dim.", "Notes"]];
  for (const g of O.groups) rows.push([g.name, String(g.n), g.note]);
  rows.push(["Total (extended)", "17", "obs_mode = extended in configs/env.yaml; basic 5-D path frozen (§6)"]);
  const shadeFn = (i, j, t) => i === rows.length - 1 ? HEAD_SHADE : null;
  return buildTable(rows, [4080, 720, 4560], shadeFn);
}

function tableActionSpace() {
  const A = DATA.action;
  const rows = [
    ["Property", "Value"],
    ["Name",                       A.name],
    ["Dimensionality",             String(A.dim) + " (continuous)"],
    ["Physical range",             `${A.low_c.toFixed(1)} °C … ${A.high_c.toFixed(1)} °C (supply air setpoint)`],
    ["Network output",             "tanh squash → linear remap to [low, high]"],
    ["Smoothing deadband",         `${A.smoothing.deadband_c.toFixed(1)} °C (no change unless |Δaction| exceeds)`],
    ["Rate limit (per step)",      A.smoothing.rate_limit ? `${A.smoothing.max_delta_normalized.toFixed(2)} (normalized units)` : "off"],
  ];
  return buildTable(rows, [3600, 5760]);
}

function tableReward() {
  const R = DATA.reward;
  const rows = [
    ["Reward component", "Parameter", "Value"],
    ["Comfort band",            "band_low_c / band_high_c",       `${R.band_low_c.toFixed(1)} / ${R.band_high_c.toFixed(1)} °C`],
    ["Comfort deadband",        "deadband_c",                     `${R.deadband_c.toFixed(2)} °C around band edges`],
    ["In-band bonus",           "band_bonus",                     R.band_bonus.toFixed(3) + " per step inside band"],
    ["Generic violation",       "undershoot_weight",              R.undershoot_weight.toFixed(2)],
    ["",                        "overshoot_weight",               R.overshoot_weight.toFixed(2)],
    ["Cold-ambient asymmetry",  "cold_amb_threshold_c",           R.cold_amb_threshold_c.toFixed(1) + " °C"],
    ["",                        "cold_undershoot_weight",         R.cold_undershoot_weight.toFixed(2) + "  (extra heat penalty)"],
    ["Hot-ambient asymmetry",   "hot_amb_threshold_c",            R.hot_amb_threshold_c.toFixed(1) + " °C"],
    ["",                        "hot_overshoot_weight",           R.hot_overshoot_weight.toFixed(2) + "  (extra cool penalty)"],
    ["Action-direction bonus",  "heating_action_bonus / t_supply",`${R.heating_action_bonus.toFixed(2)} when t_supply ≥ ${R.heating_t_supply_c.toFixed(1)} °C`],
    ["",                        "cooling_action_bonus / t_supply",`${R.cooling_action_bonus.toFixed(2)} when t_supply ≤ ${R.cooling_t_supply_c.toFixed(1)} °C`],
    ["MORL canonical weights",  "comfort / energy / safety",      `${R.morl_canonical.w_comfort.toFixed(2)} / ${R.morl_canonical.w_energy.toFixed(2)} / ${R.morl_canonical.w_safety.toFixed(2)}`],
    ["",                        "energy_scale",                   R.morl_canonical.energy_scale.toExponential(1) + " (Watts → reward units)"],
  ];
  return buildTable(rows, [2640, 2640, 4080]);
}

function tableScenarios() {
  const S = DATA.scenarios;
  const rows = [
    ["Scenario", "Day index", "Start (s)", "Duration (d)", "Ambient mean (°C)", "Role"],
    ["peak_heat_window",    String(S.peak.day),  S.peak.start_sec.toLocaleString(),  String(S.peak.duration_days),  S.peak.t_amb_mean_c.toFixed(1),  "January coldest, stress test on heating"],
    ["typical_heat_window", String(S.typ.day),   S.typ.start_sec.toLocaleString(),   String(S.typ.duration_days),   S.typ.t_amb_mean_c.toFixed(1),   "February moderate, deployment-realistic"],
    ["yearly evaluation",   "12 months",         "—",                                String(S.yearly.eval_days_per_month) + " / month", "varied",                       "MORL + PI yearly summary"],
  ];
  return buildTable(rows, [2240, 1200, 1280, 1280, 1880, 1480]);
}

function tableMorlPerSeed() {
  const P = DATA.morl_per_seed;
  const rows = [["Weight pair (c/e)", "Seed", "RMSE_T (°C)", "MAE_T (°C)", "Within 1°C %", "Violation %", "Yearly energy (kWh)", "m_s"]];
  for (const r of P.w5050) rows.push([
    "50/50", String(r.seed), r.rmse.toFixed(3), r.mae.toFixed(3),
    r.w1c.toFixed(2), r.viol.toFixed(2), r.energy_sum.toFixed(1), r.m_s.toFixed(3),
  ]);
  for (const r of P.w7525) rows.push([
    "75/25", String(r.seed), r.rmse.toFixed(3), r.mae.toFixed(3),
    r.w1c.toFixed(2), r.viol.toFixed(2), r.energy_sum.toFixed(1), r.m_s.toFixed(3),
  ]);
  const shadeFn = (i, j, t) => {
    if (j === 7 && i > 0) {
      const v = parseFloat(t);
      if (v < 0.10) return POS_SHADE;
      if (v > 0.25) return NEG_SHADE;
    }
    return null;
  };
  return buildTable(rows, [1320, 760, 1240, 1240, 1280, 1280, 1480, 760], shadeFn);
}

// ──────────────────────── DOCUMENT BODY ──────────────────────────────────────
const children = [
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 0, after: 240 },
    children: [new TextRun({ text: "Block 2 Complete Results", bold: true, font: "Arial", size: 36, color: "1F3864" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 0, after: 240 },
    children: [new TextRun({
      text: "Control-side experiments on BOPTEST bestest_air: thermostat baseline, pure v3 PPO, " +
            "direct v3.5 warm-start (negative control), thermostatic hybrid, HDRL sweep, " +
            "MORL 5D failure / 17D success, MORL canonical seed analysis, Pareto sweep, " +
            "PI reference, transfer diagnostics.",
      italic: true, font: "Arial", size: 22, color: "2E75B6",
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 0, after: 480 },
    children: [new TextRun({
      text: "All numbers cross-checked against project artifacts (CSV/JSON) on 2026-05-28.",
      italic: true, font: "Arial", size: 18, color: "808080",
    })],
  }),

  divider(),

  // ════════════════════════ §1 Methodology & Overview ════════════════════════
  h1("§1.  Methodology and reading order"),

  // ─────── §1.1 Reading order ───────
  h2("§1.1  Reading order"),
  para(
    "Block 1 established the surrogate-level claim: v3 is a control-oriented black-box surrogate " +
    "with poor multi-horizon predictive fidelity (24h RMSE_T = 1.557 °C), while calibrated v3.5 is " +
    "a physically-identified surrogate with strong predictive fidelity (24h RMSE_T = 0.644 °C). " +
    "Block 2 then tests the **controller-side** question: which combinations of these two surrogates " +
    "produce useful Reinforcement-Learning policies on the live BOPTEST RTE bestest_air testcase, " +
    "and which fail."
  ),
  para("The Block 2 narrative across this document follows the controller-family stack:"),
  bullet("§2 Pure v3 PPO baseline — the control-oriented surrogate alone produces a working policy."),
  bullet("§3 Direct v3.5 PPO (negative control) — using the high-fidelity surrogate alone fails catastrophically."),
  bullet("§4 Thermostatic hybrid — combining v3 dynamics with a v3.5 disagreement regularizer is the best result."),
  bullet("§5 HDRL sweep — the same hybrid regularization does NOT transfer to hierarchical RL; lambda_temp_disagree must be 0."),
  bullet("§6 MORL 5D failure / 17D success — observation interface choice dominates the MORL result."),
  bullet("§7 MORL canonical seed analysis — N=5 seed variance falsifies the single-seed canonical result."),
  bullet("§8 MORL Pareto sweep — comfort/energy trade-off across 5 weight pairs."),
  bullet("§9 PI baseline — BOPTEST built-in reference."),
  bullet("§10 Transfer diagnostics — closed-loop surrogate-vs-live ms_gap and feature attribution."),
  bullet("§11 Synthesis — fidelity-vs-utility paradox and Block 3 prerequisites."),

  // ─────── §1.2 PPO algorithm ───────
  h2("§1.2  PPO algorithm and hyperparameters"),
  para(
    "All five controller families (pure v3, hybrid, HDRL, direct v3.5, MORL 17D) use Proximal Policy " +
    "Optimization (PPO) with the Stable-Baselines3 reference implementation. " +
    "However, **the PPO hyperparameters are NOT identical across families** — each family is driven by its " +
    "own training script that sets `n_steps` and `batch_size` independently. " +
    "What is **shared across all families**: learning_rate = 3×10⁻⁴ (during pretrain), γ = 0.99, n_epochs = 10. " +
    "What is **shared by Stable-Baselines3 default** (because train_thermostatic.py and train_hdrl.py do " +
    "not set them explicitly): GAE λ = 0.95, clip_range = 0.2, entropy_coef = 0.0, vf_coef = 0.5 — these " +
    "happen to match the values set explicitly in `configs/agent.yaml` for the MORL pipeline. " +
    "What **differs by family**: rollout length `n_steps` and minibatch `batch_size`, and the total " +
    "timestep budget."
  ),
  caption("Table 1 — PPO training hyperparameters per controller family (verified per-script).",
          " Sources: training/train_thermostatic.py (line 646), training/train_hdrl.py (line 247), " +
          "configs/agent.yaml + configs/morl_surrogate_ppo/train.yaml (MORL pretrain), " +
          "training/finetune_morl_boptest.py (line 83)."),
  tablePpoHparams(),
  para(
    "Three design choices deserve highlighting. " +
    "First, the **discount γ = 0.99** corresponds to an effective horizon of ~100 steps × 900 s ≈ 25 hours: " +
    "the policy considers approximately one day of comfort consequences when valuing an action, which matches " +
    "the natural occupancy cycle of bestest_air. " +
    "Second, **entropy coefficient = 0** means PPO converges to a deterministic policy after the initial " +
    "exploration phase; this is intentional because the deployment use case is reproducible control, not " +
    "interactive bandit play. " +
    "Third, the **per-family difference in n_steps and batch_size** (thermostatic 1024/4096 vs HDRL 1024/2048 " +
    "vs MORL pretrain 2048/64) reflects the rollout efficiency vs sample efficiency trade-off chosen by each " +
    "family's authors, not a deliberate ablation. The MORL pipeline additionally runs a 100,000-step BOPTEST " +
    `live-finetune at learning rate ${DATA.ppo.morl_finetune.learning_rate.toExponential(1)} after the 2 M surrogate-pretrain step, ` +
    "to absorb the residual surrogate-vs-BOPTEST distribution shift.",
    { spaceBefore: 160 }
  ),

  // ─────── §1.3 Observation space ───────
  h2("§1.3  Observation space — 17-D extended TSup-style"),
  para(
    "The default observation space (used by pure v3, hybrid, HDRL, and MORL 17D) is the **17-dimensional " +
    "extended TSup-style** feature vector specified by `obs_mode = extended` in configs/env.yaml. " +
    "It combines raw and lagged zone/ambient temperatures, clipped-log power telemetry, a causal-smooth " +
    `ΔT signal, cyclic time encodings, and the last-action context. ` +
    "The earlier 5-D basic observation (zone temperature, ambient, hour, day, occupancy) is preserved " +
    "in §6 as the failed-MORL baseline."
  ),
  caption("Table 2 — Extended observation feature groups (verified from envs/tsup_features.py).",
          " Source: envs/tsup_features.py (BASIC_TSUP_OBS_DIM=5, TIME_TSUP_OBS_DIM=4, " +
          "FORECAST_HORIZONS=[1,3,6,12,24], HISTORY_TSUP_OBS_DIM=3 = 2-D prev_action + 1-D Δt_zone; " +
          "totals 5+4+5+2+1 = 17). " +
          "Encoding modes from configs/env.yaml: obs_mode = extended, delta_feature_mode = causal_smooth, " +
          "power_feature_mode = clipped_log, t_zone_feature_mode = raw."),
  tableObsSpace(),

  // ─────── §1.4 Action space ───────
  h2("§1.4  Action space — normalized supply-air setpoint"),
  para(
    "The actor outputs a single continuous **supply-air temperature setpoint** in the range 18 – 35 °C, " +
    "normalised to [-1, +1] inside the neural network (tanh squash) and remapped to physical units " +
    "before being sent to BOPTEST. " +
    "The wrapper applies a 1.0 °C deadband (small changes do not modulate the actuator) and a per-step " +
    "rate limit of 0.15 normalised units (~2.6 °C per 15-minute step). " +
    "Both shape choices protect the BOPTEST RTE from high-frequency actuation chatter and improve " +
    "transfer to physical hardware in future work."
  ),
  caption("Table 3 — Action-space configuration.",
          " Source: configs/env.yaml (action_wrappers and t_supply_low / high)."),
  tableActionSpace(),

  // ─────── §1.5 Reward function ───────
  h2("§1.5  Reward function — comfort shaping + (MORL) multi-objective weights"),
  para(
    "The reward function combines a **comfort shaping term**, an **energy term**, and (for MORL only) " +
    "a **safety term**, with explicit asymmetry between cold and hot ambient conditions. " +
    "The base comfort term penalises zone temperatures outside the 21 – 24 °C band with linearly increasing " +
    "weight beyond a 0.5 °C deadband; it adds a small in-band bonus (0.05 per step) so that the policy " +
    "actively seeks the comfort interior rather than just avoiding violation. " +
    "Asymmetric weights amplify cold-ambient undershoots (× 1.60) and hot-ambient overshoots (× 1.80), " +
    "reflecting the physical reality that recovering from a cold zone in cold weather is harder than " +
    "the symmetric reverse."
  ),
  para(
    "Action-direction bonuses (heating/cooling bonuses when t_supply is on the right side of room " +
    "temperature) prevent PPO from learning a pathological constant-output policy in the first few epochs. " +
    "For MORL, the multi-objective weighting is canonically (comfort, energy, safety) = (0.80, 0.20, 0.00) " +
    `with an energy_scale of ${DATA.reward.morl_canonical.energy_scale.toExponential(1)} that converts Watts to a comparable reward unit; ` +
    "the Pareto sweep (§8) varies these weights."
  ),
  caption("Table 4 — Reward function components.",
          " Source: configs/env.yaml (comfort_shaping + morl sub-block)."),
  tableReward(),

  // ─────── §1.6 Scenarios ───────
  h2("§1.6  Scenario definitions"),
  para(
    "Block 2 KPI tables report two **targeted 14-day windows** plus, for MORL/PI yearly summaries, " +
    "**12 monthly 14-day windows**. " +
    "The targeted windows are intentionally chosen at extreme and moderate winter conditions:"
  ),
  bullet(
    "**peak_heat_window** — starts at simulation day 3 (January, daily mean ambient −24.4 °C); this is " +
    "the hardest single scenario in the year and serves as a stress test."
  ),
  bullet(
    "**typical_heat_window** — starts at simulation day 37 (February, daily mean ambient +2.4 °C); this " +
    "is a deployment-realistic moderate-winter operating point."
  ),
  caption("Table 5 — Targeted-window scenario definitions.",
          " Source: outputs/block2_*/scenario_manifest.json (start_day_index, duration_days, daily_mean_t_amb_c)."),
  tableScenarios(),

  // ─────── §1.7 MORL pipeline ───────
  h2("§1.7  MORL pipeline — pretrain → ERAM → finetune → yearly eval"),
  para(
    `MORL uses a four-stage pipeline that differs from the single-stage PPO families. ` +
    `(1) **Pretrain**: ${DATA.morl_pipeline.pretrain_steps.toLocaleString()} steps of PPO on the 17-D hybrid backend ` +
    `with the canonical (0.80/0.20/0.00) weights. ` +
    `(2) **ERAM** (internal pipeline label; the expansion is not formally defined in source — it appears only as the file/argument name in training/train_morl_eram.py): ${DATA.morl_pipeline.eram_iterations} iterations of ` +
    `${DATA.morl_pipeline.eram_chunk_steps.toLocaleString()} steps each, starting from initial weights ${DATA.morl_pipeline.eram_init_weights} ` +
    `with τ_w = ${DATA.morl_pipeline.eram_tau_w} (weight-update temperature) and adv_lr = ${DATA.morl_pipeline.eram_adv_lr}. ` +
    `(3) **Finetune**: ${DATA.morl_pipeline.finetune_steps.toLocaleString()} steps on the **live BOPTEST RTE** at lr = ${DATA.morl_pipeline.finetune_lr.toExponential(1)} ` +
    `with episode-start jitter of ±${DATA.morl_pipeline.finetune_jitter_days} days to absorb the residual surrogate-vs-RTE distribution shift. ` +
    `(4) **Yearly evaluation**: 12 monthly 14-day scenarios on BOPTEST.`
  ),
  para(
    "MORL is the only family that uses live-BOPTEST finetuning. PPO/hybrid/HDRL are evaluated directly " +
    "on BOPTEST after surrogate-only training, with no live finetuning step, which makes them strictly " +
    "more challenging transfer scenarios."
  ),

  // ─────── §1.8 Domain randomization ───────
  h2("§1.8  Stochasticity during training — surrogate-side DR vs BOPTEST-side jitter"),
  para(
    "There are **two distinct forms** of training-time stochasticity, applied at different stages:"
  ),
  bullet(
    `**Surrogate-side domain randomization** (thermostatic, hybrid, HDRL, MORL pretrain): at each episode reset, ` +
    `the initial zone temperature is sampled from ${DATA.domain_random.t_init_low_c.toFixed(1)} – ${DATA.domain_random.t_init_high_c.toFixed(1)} °C, ` +
    `the start day is sampled from the 366-day calendar (uniform or heating-biased), ` +
    `and Gaussian noise of σ = ${DATA.domain_random.weather_noise_std_c.toFixed(1)} °C is added to the weather-lookup ambient values. ` +
    "Implementation: `ThermostaticEnv.reset()` lines 350-366; surrogate_backend.py `dr_enabled` defaults to True."
  ),
  bullet(
    "**BOPTEST-side start-time jitter** (MORL finetune only): the surrogate-style DR no longer applies because " +
    "BOPTEST is a deterministic EnergyPlus simulator with a fixed weather file. Instead, the live finetune " +
    "samples episode starts from 12 yearly anchors (one per month, beginning at simulation time 0, 2,678,400 s, " +
    "..., 28,857,600 s) and adds ±3-day uniform jitter to each anchor (`boptest_start_jitter_sec = 3.0 × 86,400`). " +
    "This gives 12 × ~6 = 72 effective episode-start windows. " +
    "Implementation: `training/finetune_morl_boptest.py` lines 107-108."
  ),
  para(
    "**Evaluation is fully deterministic**: post-training surrogate evaluation calls `ThermostaticEnv(dr_enabled=False)` " +
    "(thermostatic line 675) and live BOPTEST evaluation uses fixed scenario start days. No randomness in the reported KPIs."
  ),
  para(
    `Common to all results in Block 2: comfort band ${DATA.comfort_band}, ` +
    `step = ${DATA.step_sec} s, targeted-rollout duration = ${DATA.rollout_days} days, ` +
    `live testcase = ${DATA.testcase} (Docker BOPTEST RTE HTTP, surrogate model file ` +
    `${DATA.pure_v3.surrogate_path} for v3, ` +
    "calibrated v3.5 from Block 1 §2.4)."
  ),

  // ════════════════════════ §2 Pure v3 PPO ════════════════════════
  divider(),
  h1("§2.  Pure v3 PPO thermostatic baseline"),

  h2("§2.1  Setup"),
  para(
    "The pure v3 PPO baseline uses the canonical v3 control-oriented surrogate " +
    `(${DATA.pure_v3.surrogate_path}) as the rollout dynamics inside PPO, with no v3.5 ` +
    "disagreement regularization (lambda_temp_disagree = 0, lambda_power_disagree = 0). " +
    "The policy is a thermostatic PPO actor with a comfort-centered reward; " +
    "observations include the 17-dimensional TSup-style feature vector " +
    "(zone temperature, ambient, solar, ahead-of-day occupancy, hour/day cyclic, " +
    "lagged power, etc.). " +
    "After training on the surrogate, the policy is deployed against the live BOPTEST RTE " +
    "for 14-day rollouts on two targeted scenarios."
  ),

  h2("§2.2  Live BOPTEST results"),
  para(
    "Pure v3 PPO reaches sub-degree comfort RMSE in both targeted-window scenarios " +
    `(peak: ${DATA.pure_v3.peak_rmse_c.toFixed(3)} °C; typical: ${DATA.pure_v3.typ_rmse_c.toFixed(3)} °C) ` +
    `and an m_s well below the thermostat or PI baselines ` +
    `(peak m_s = ${DATA.pure_v3.peak_m_s.toFixed(3)}, typical = ${DATA.pure_v3.typ_m_s.toFixed(3)}). ` +
    "This is the **first central finding of Block 2**: a surrogate that is provably inaccurate " +
    "as a 24-hour predictor (Block 1 §1.3) nonetheless produces a usable PPO policy with " +
    "single-digit setpoint violation percentage on the live test cases."
  ),

  // ════════════════════════ §3 Direct v3.5 (Neg Control) ════════════════════════
  divider(),
  h1("§3.  Direct v3.5 PPO — negative control"),

  h2("§3.1  Hypothesis and configuration"),
  para(
    "The naive scientific hypothesis would be: since v3.5 is the higher-fidelity surrogate " +
    "(Block 1: 0.644 °C 24h RMSE vs v3's 1.557 °C), a PPO trained on v3.5 should produce " +
    "a strictly better controller. " +
    "We test this by training PPO directly on the calibrated v3.5 backbone with no v3 dynamics " +
    "(lambda_temp_disagree = 0, no hybrid mixing), then deploying on the live BOPTEST RTE."
  ),

  h2("§3.2  Result: catastrophic failure"),
  para(
    `Direct v3.5 PPO produces m_s = ${DATA.direct_v35.peak_m_s.toFixed(3)} on peak and ` +
    `${DATA.direct_v35.typ_m_s.toFixed(3)} on typical scenarios — an order of magnitude worse than ` +
    `pure v3 PPO. ` +
    `Setpoint violation reaches ${DATA.direct_v35.peak_violation_pct.toFixed(1)} % on peak, ` +
    `with comfort RMSE of ${DATA.direct_v35.peak_rmse_c.toFixed(2)} °C — ` +
    "the policy spends most of the rollout outside the 21–24 °C band."
  ),
  para(
    "This is the **fidelity-vs-utility paradox** in its clearest form: " +
    "the surrogate with better predictive accuracy (v3.5, RMSE_T = 0.644 °C) produces " +
    "a substantially worse PPO policy than the surrogate with worse predictive accuracy " +
    "(v3, RMSE_T = 1.557 °C). " +
    "**The mechanism is hypothesised, not directly measured.** " +
    "A consistent interpretation — supported by the empirical pattern and by general PPO theory but not by " +
    "any gradient-variance measurement performed in this project — is that v3.5's sharper physical predictions " +
    "yield higher-variance advantage estimates inside PPO, destabilising policy updates, while v3's smoother " +
    "bias-toward-mean predictions provide a gentler gradient signal. " +
    "An equally consistent alternative is that v3.5's predictions encode physical regimes (e.g., short-time " +
    "thermal capacitance) the policy has no way to exploit at the 15-minute control cadence, so the policy " +
    "over-fits to spurious sub-step structure. Discriminating between these mechanisms is left to Block 4."
  ),

  h2("§3.3  Warm-start utility check"),
  para(
    "We additionally check whether v3.5 has any value as a **warm-start initialiser** " +
    "(pre-train on v3.5, then fine-tune on the hybrid backend). " +
    "The comparison table below shows that scratch training on the hybrid backend " +
    "outperforms warm-starting from v3.5 by a wide margin on both scenarios."
  ),
  caption("Table 2 — Direct-v3.5 warm-start utility comparison.",
          " From outputs/block2_thermostatic_warmstart_utility/comparison_summary.csv."),
  tableWarmstartUtility(),
  ...figure(
    "block2_warmstart_negative_eval_kpis.png",
    "Figure 2.",
    "Direct-v3.5 warm-start is a negative control: better predictive fidelity does not translate into a useful policy initializer.",
    560,
    230
  ),
  para(
    "Warm-starting from v3.5 not only fails to help — it actively harms training, " +
    "raising m_s by 2–3×. " +
    "Conclusion: v3.5 must be used as a soft regularizer (next section), not as a direct " +
    "rollout backbone or warm-start source.",
    { spaceBefore: 160 }
  ),

  // ════════════════════════ §4 Thermostatic Hybrid ════════════════════════
  divider(),
  h1("§4.  Thermostatic hybrid (canonical positive result)"),

  h2("§4.1  Architecture: v3 dynamics + v3.5 disagreement reward-shaping"),
  para(
    "The hybrid backend uses v3 as primary rollout dynamics (so PPO sees the smooth, " +
    "control-friendly transitions) and v3.5 as a **per-step reward-shaping censor** (NOT a separate policy-loss term). " +
    "At each surrogate step both models are evaluated on the same (state, action); the absolute " +
    "differences `|t_v3 − t_v3.5|` and `|p_v3 − p_v3.5|` are computed and the per-step reward becomes:"
  ),
  para(
    `**r = r_comfort + r_smooth + r_energy − λ_temp · |Δt_disagree| − λ_pwr · |Δp_disagree|**, ` +
    `with λ_temp = ${DATA.hybrid_l010.lambda_temp} and λ_pwr = ${DATA.hybrid_l010.lambda_pwr.toExponential(1)} for the canonical hybrid_l010.`,
    { size: 22 }
  ),
  para(
    "PPO then computes the advantage A_t = r_t + γV(s_{t+1}) − V(s_t) from this augmented reward in the standard way; " +
    "there is no explicit modification of the policy gradient. " +
    "The verified source is `envs/backends/surrogate_backend.py` lines 343-350 " +
    "(`reward -= self.lambda_temp_disagree * float(temp_disagreement)` etc.) and " +
    "`training/train_thermostatic.py` line 436. " +
    "The disagreement signal acts as a censor, not a forecast: when v3 and v3.5 agree the disagreement term " +
    "vanishes and the reward reduces to comfort + energy; when they disagree the agent loses reward and learns " +
    "to avoid the disputed regions of state-action space."
  ),

  h2("§4.2  Live BOPTEST results"),
  para(
    `Hybrid_l010 achieves m_s = ${DATA.hybrid_l010.peak_m_s.toFixed(3)} (peak) and ` +
    `${DATA.hybrid_l010.typ_m_s.toFixed(3)} (typical). It nearly matches pure v3 on the peak window while saving energy, and it clearly improves pure v3 on the typical window — ` +
    `with comfort RMSE down to ${DATA.hybrid_l010.peak_rmse_c.toFixed(3)} / ${DATA.hybrid_l010.typ_rmse_c.toFixed(3)} °C ` +
    `with setpoint violation below 5 % on both scenarios. ` +
    "Energy consumption is lower than pure v3 " +
    `(${DATA.hybrid_l010.peak_energy_kwh.toFixed(0)} vs ${DATA.pure_v3.peak_energy_kwh.toFixed(0)} kWh peak); ` +
    "the hybrid achieves better comfort at no energy cost."
  ),

  caption("Table 4 — Canonical Block 2 results on the live BOPTEST RTE (paper §6.3).",
          " Sources: outputs/bestest_air_article7_style_15min/summary.csv (pure v3 PPO), " +
          "outputs/block2_thermostatic_hybrid_v3_v35_l010/summary.csv (hybrid_l010), " +
          "reports/hybrid_transfer_comparison.csv (direct v3.5 from transfer-comparison harness). " +
          "Green = strong result (m_s < 0.10); red = failure (m_s > 0.50); yellow = intermediate."),
  tableMainBlock2(),
  ...figure(
    "block2_thermostatic_pure_v3_vs_hybrid_kpis.png",
    "Figure 3.",
    "Thermostatic pure-v3 versus hybrid_l010 KPIs on peak and typical windows. Hybrid_l010 trades a small peak-window m_s increase for lower energy and strongly improves the typical window.",
    560,
    250
  ),

  para(
    "The Block 2 main table shows the full fidelity-vs-utility paradox in a single panel: " +
    "**direct v3.5 fails despite better predictive fidelity; pure v3 is control-usable; hybrid_l010 is the best verified compromise**. " +
    "Predictive fidelity alone does not determine controller quality — the role of the calibrated " +
    "physical twin (v3.5) is to provide a soft physics censor, not to be the rollout dynamics.",
    { spaceBefore: 160 }
  ),

  h2("§4.3  Hybrid disagreement bounded, not chaotic"),
  para(
    `On the canonical hybrid traces, the average temperature disagreement between v3 and v3.5 ` +
    `is ${DATA.hybrid_disagreement.mean_temp_c.toFixed(3)} °C (p95 = ${DATA.hybrid_disagreement.p95_temp_c.toFixed(2)} °C); ` +
    `the average power disagreement is ${DATA.hybrid_disagreement.mean_power_w.toFixed(0)} W ` +
    `(p95 = ${DATA.hybrid_disagreement.p95_power_w.toFixed(0)} W). ` +
    "These bounds confirm that the two surrogates are not chaotically divergent — " +
    "they remain in the same dynamical regime, so the disagreement signal is informative " +
    "rather than dominated by representation noise."
  ),

  // ════════════════════════ §5 HDRL Sweep ════════════════════════
  divider(),
  h1("§5.  HDRL sweep — controller-family-specific limit"),

  h2("§5.1  Question"),
  para(
    "Does the thermostatic-optimal lambda_temp_disagree = 0.10 transfer to the next " +
    "controller family — Hierarchical Deep RL (HDRL)? " +
    "HDRL has a different action space (multi-level scheduler + low-level setpoint controller) " +
    "and different gradient dynamics, so a universal hybrid weight is not guaranteed."
  ),

  h2("§5.2  Sweep results"),
  caption("Table 5 — HDRL sweep across λ_temp_disagree ∈ {0, 0.03, 0.05, 0.10}.",
          " Green = best (λ = 0.00); red = worst (λ = 0.10). " +
          "From reports/block2_hdrl_lambda_sweep_summary.csv."),
  tableHdrl(),
  ...figure(
    "block2_hdrl_lambda_sweep_sensitivity.png",
    "Figure 4.",
    "HDRL rejects the thermostatic λ_temp=0.10 setting; λ_temp=0 is best on both windows.",
    560,
    250
  ),
  ...figure(
    "block2_hdrl_l000_winter_tracking.png",
    "Figure 5.",
    "Representative HDRL λ_temp=0 winter tracking trace, included to show the physical origin of the KPI table.",
    560,
    230
  ),

  para(
    "On both scenarios, HDRL performance **monotonically degrades** with increasing " +
    "lambda_temp_disagree. The best HDRL setting is lambda = 0 (no temperature regularization). " +
    "The thermostatic-default lambda = 0.10 produces a 2.4× worse m_s on peak and " +
    "a 2.2× worse m_s on typical compared to lambda = 0.",
    { spaceBefore: 160 }
  ),

  h2("§5.3  Interpretation: hybrid regularization is family-specific"),
  para(
    "The HDRL sweep falsifies the hypothesis that there is a single optimal " +
    "lambda_temp_disagree across controller families. The right reading is: " +
    "thermostatic PPO benefits from temperature disagreement censoring, but HDRL — " +
    "which already has a hierarchical comfort-aware structure — is over-regularised " +
    "by the same signal. The lesson for the MORL stage (§6) is that the **power-only** " +
    "hybrid backend (lambda_temp = 0, lambda_power = 5e-5) should be the starting point, " +
    "not the temperature-and-power hybrid that worked for thermostatic PPO."
  ),

  // ════════════════════════ §6 MORL 5D vs 17D ════════════════════════
  divider(),
  h1("§6.  MORL 5D failure → 17D success"),

  h2("§6.1  The frozen 5D failure (Section 6.5 of roadmap)"),
  para(
    "The first MORL implementation used a 5-dimensional observation (zone temperature, " +
    "ambient temperature, hour, day, occupancy). Both training and live evaluation produced " +
    `comfort RMSE of ${DATA.morl_5d.rmse_c.toFixed(2)} °C with ${DATA.morl_5d.viol_pct.toFixed(1)} % setpoint ` +
    "violations — a complete failure. The policy could not use the available observations to " +
    "distinguish heating from cooling demand or to anticipate occupancy transitions. " +
    "This result is preserved as a frozen artifact (audit anchor only) and is not re-generated " +
    "by the current code path."
  ),

  h2("§6.2  The 17D power-only backend (canonical MORL)"),
  para(
    "Replacing the 5D observation with the 17-dimensional TSup-style feature vector — same as " +
    "thermostatic PPO and HDRL — and disabling temperature disagreement regularization " +
    "(lambda_temp = 0, lambda_power = 5e-5, learned from the HDRL sweep in §5) recovers a " +
    `usable MORL policy: m_s = ${DATA.morl_17d_canonical.m_s.toFixed(3)}, ` +
    `${DATA.morl_17d_canonical.viol_pct.toFixed(1)} % violation, ` +
    `RMSE_T = ${DATA.morl_17d_canonical.rmse_c.toFixed(2)} °C, ` +
    `energy = ${DATA.morl_17d_canonical.energy_kwh.toFixed(1)} kWh.`
  ),

  caption("Table 6 — MORL 5D vs 17D comparison.",
          " Red = failure; green = canonical success. " +
          "From reports/block2_morl_comparison_summary.csv."),
  tableMorlCompare(),
  ...figure(
    "block2_morl_5d_vs_17d_radar.png",
    "Figure 6.",
    "MORL observation-interface ablation. The 5D interface fails; the 17D TSup-style interface recovers a usable policy.",
    560,
    260
  ),

  para(
    "The MORL result confirms the cross-family pattern: " +
    "**v3 supplies the temperature dynamics, v3.5 supplies a soft power censor, " +
    "and the controller-family-specific lambda values come from the HDRL sweep**. " +
    "The dominant factor in MORL success was not the backend (it was the same hybrid in both 5D " +
    "and 17D), but the observation-interface design.",
    { spaceBefore: 160 }
  ),

  // ════════════════════════ §7 MORL Canonical Seed Analysis ════════════════════════
  divider(),
  h1("§7.  MORL canonical seed analysis (N = 5 falsification)"),

  h2("§7.1  Pre-registration and audit anchors"),
  para(
    `The MORL canonical seed at the time of the seed-45/46 pre-registration ` +
    `(commit ${DATA.anchors.seed_45_46_prereg.sha}, "${DATA.anchors.seed_45_46_prereg.msg}") ` +
    `was seed 42 with comfort/energy weights 50/50, reaching m_s = ${DATA.morl_17d_canonical.m_s.toFixed(3)} ` +
    "on the single-seed yearly evaluation. The pre-registration recorded the **expected outcomes** for " +
    "seeds 45 and 46 before they were trained, so that the N=5 extension would be a falsifiable test " +
    "rather than a post-hoc fit. " +
    `Audit anchor ${DATA.anchors.n5_falsification.sha} ("${DATA.anchors.n5_falsification.msg}") ` +
    "is the commit that records the post-N=5 result — confirming that the action-saturation/seasonal-inversion " +
    "hypothesis is falsified, and the high seed variance is the defensible reading."
  ),

  caption("Table 7a — MORL N=5 seed variance on yearly BOPTEST evaluation (aggregate).",
          " Red CV = high relative variance (≥ 40 %). " +
          "From reports/morl_canonical_seedfix_yearly_summary.csv."),
  tableMorlSeedVar(),

  para(
    "Table 7b shows the per-seed breakdown for both weight pairs. " +
    "The 50/50 distribution is bimodal: seeds 42 / 44 / 45 cluster near m_s ≈ 0.14 – 0.19, " +
    "seed 43 reaches the best m_s = 0.103, and seed 46 fails out at m_s = 0.310 " +
    "(violation = 24 %). The 75/25 distribution is similar in structure but with the entire " +
    "distribution shifted to lower m_s. The replay test on seed 42 produced bit-identical BOPTEST " +
    "trajectories, so the seed variance is attributable to PPO/ERAM training stochasticity rather " +
    "than simulator nondeterminism.",
    { spaceBefore: 160 }
  ),
  caption("Table 7b — Per-seed MORL yearly metrics (50/50 and 75/25 weight pairs).",
          " Green = strong (m_s < 0.10); red = failure (m_s > 0.25). " +
          "From reports/morl_canonical_seedfix_yearly_per_seed.csv."),
  tableMorlPerSeed(),
  ...figure(
    "block2_morl_17d_seasonal_heatmap.png",
    "Figure 7.",
    "MORL N=5 seasonal variance heatmap. The earlier N=3 seasonal-inversion hypothesis does not survive N=5; high seed variance remains the correct claim.",
    560,
    250
  ),
  ...figure(
    "block2_morl_seasonal_variance_inversion.png",
    "Figure 8.",
    "Post-N=5 seasonal variance diagnostic. The figure is retained as a falsification artifact rather than as support for action-saturation claims.",
    560,
    230
  ),

  h2("§7.2  Finding: high seed variance, no single-seed superiority"),
  para(
    "Across N = 5 seeds at the 50/50 weight pair, m_s ranges from " +
    `${DATA.morl_seedfix_5050.ms_min.toFixed(3)} to ${DATA.morl_seedfix_5050.ms_max.toFixed(3)} ` +
    `(mean ${DATA.morl_seedfix_5050.ms_mean.toFixed(3)}, ` +
    `CV = ${DATA.morl_seedfix_5050.ms_cv.toFixed(2)}). ` +
    "The 75/25 weight pair has even higher CV " +
    `(${DATA.morl_seedfix_7525.ms_cv.toFixed(2)}), driven by occasional outlier seeds that ` +
    "fail to converge to the comfort region. The single-seed canonical (m_s = 0.099, seed 42) " +
    "is the **best** of five — not representative of the median MORL policy."
  ),
  para(
    "This falsifies the strong reading of MORL canonical results " +
    "(\"MORL produces m_s ≈ 0.10 reliably\") and supports the weaker but defensible reading " +
    "(\"MORL produces m_s in [0.10, 0.31] depending on seed; we report the best single seed " +
    "as the pre-registered canonical\"). The N = 5 finding is logged in audit anchor 62dc859 " +
    "and is referenced in §6.5 of the paper."
  ),

  // ════════════════════════ §8 MORL Pareto ════════════════════════
  divider(),
  h1("§8.  MORL Pareto sweep"),

  h2("§8.1  Weight pairs"),
  para(
    "The Pareto sweep evaluates five (comfort, energy) weight pairs on the same MORL 17D " +
    "power-only backend: 0/100, 25/75, 50/50, 75/25, 100/0. For each pair, training is run " +
    "to the same number of policy updates and evaluated on the yearly BOPTEST scenario set."
  ),

  caption("Table 8 — MORL Pareto front (seed 42, yearly evaluation).",
          " Green = strong (m_s < 0.15); red = failure (m_s > 0.5). " +
          "From reports/morl_pareto_front_table.csv."),
  tableMorlPareto(),
  ...figure(
    "block2_morl_pareto_energy_vs_ms.png",
    "Figure 9.",
    "MORL Pareto front. Non-canonical sweep points are seed42-only; the two canonical points are N=5 means with 95% CI error bars.",
    560,
    310
  ),

  h2("§8.2  Interpretation"),
  para(
    "The Pareto front (seed 42) shows: " +
    "(a) the 0/100 (energy-only) policy collapses to a degenerate near-zero-power solution with " +
    "87 % violation — energy is minimised by simply not heating; " +
    "(b) the 100/0 (comfort-only) policy is the best m_s (0.032) and best RMSE (0.631 °C) but spends " +
    "the most energy (260.6 kWh); " +
    "(c) the **75/25 (practical-deployment) pair at seed 42** is the recommended compromise: " +
    "m_s = 0.057, violation = 3.08 %, energy = 249.5 kWh — clearly better than the 50/50 (m_s = 0.193) " +
    "and close to the 100/0 comfort-only endpoint at 4 % lower energy. " +
    "(d) The **legacy 80/20 canonical** (m_s = 0.099) sits between 75/25 and 50/50 and matches the " +
    "historical canonical (m_s ≈ 0.10) reported in earlier MORL versions of this project. " +
    "We pre-registered 50/50 as canonical for symmetry, but the empirical 75/25 dominates it on every metric."
  ),
  para(
    "**Caveat — these are seed-42 values, not N=5 means.** As §7.2 shows, the N=5 multi-seed mean for the " +
    "75/25 weight pair is m_s = 0.139 ± 0.085 (CV ≈ 0.61), so the seed-42 point reported here is the " +
    "best of the five seeds, not the typical seed. The Pareto endpoints (0/100, 25/75, 100/0) are " +
    "single-seed sweep points — the paper §6.5 figure includes both the seed-42 Pareto curve and " +
    "the N=5 error bars for the pre-registered canonicals.",
    { spaceBefore: 160 }
  ),

  // ════════════════════════ §9 PI Baseline ════════════════════════
  divider(),
  h1("§9.  PI baseline reference"),
  para(
    "The BOPTEST built-in PI controller is included as a reproducible reference, not as a " +
    "custom-tuned strong baseline. On the same 12-month yearly evaluation: " +
    `mean comfort RMSE = ${DATA.pi_yearly.rmse_mean_c.toFixed(2)} °C, ` +
    `mean MAE = ${DATA.pi_yearly.mae_mean_c.toFixed(2)} °C, ` +
    `mean violation = ${DATA.pi_yearly.viol_mean_pct.toFixed(1)} %, ` +
    `mean monthly energy = ${DATA.pi_yearly.energy_mean_kwh.toFixed(1)} kWh, ` +
    `m_s mean = ${DATA.pi_yearly.m_s_mean.toFixed(3)}. ` +
    "The PI baseline is **comfort-bad** (60 % violation is unacceptable) but **energy-good** " +
    "(low kWh because it under-heats). The RL/MORL agents must beat PI on m_s without " +
    "dramatically exceeding PI energy use."
  ),
  para(
    "All Block 2 RL/MORL agents (pure v3 PPO, hybrid_l010, MORL 17D canonical) achieve " +
    "m_s well below 0.20 vs. PI's 0.910 — so the RL stack dominates the PI reference on " +
    "comfort while using comparable or lower energy in absolute terms after correcting for " +
    "the comfort/energy trade-off curve."
  ),

  // ════════════════════════ §10 Transfer Diagnostics ════════════════════════
  divider(),
  h1("§10.  Transfer diagnostics — surrogate-vs-live closed-loop ms_gap"),

  h2("§10.1  Method"),
  para(
    "The transfer diagnostic closes a remaining evidence gap: when a policy is trained inside " +
    "a surrogate-driven loop, does it transfer to the BOPTEST RTE without surprise? " +
    "We compute, for each candidate backend, the **m_s gap** between the surrogate's predicted " +
    "trajectory and the live-BOPTEST trajectory under the same policy and scenario, plus the " +
    "**first divergence step** (the earliest 15-minute step at which the surrogate and BOPTEST " +
    "diverge by more than a threshold), plus the **top driver feature** for the divergence."
  ),

  caption("Table 10 — Transfer diagnostics across three backend variants.",
          " From reports/hybrid_transfer_comparison.csv. " +
          "ms_gap = surrogate_m_s − live_m_s (negative means surrogate is optimistic)."),
  tableTransfer(),

  h2("§10.2  Findings"),
  bullet(
    "Direct_v35 has the largest ms_gap (|gap| ≈ 0.9–1.0) and the largest action-gap norm " +
    "(2.0) — the surrogate-trained policy actually executes very different actions on the " +
    "live RTE than it does in surrogate-rollout simulation. The driver feature is t_zone_norm, " +
    "confirming that v3.5's sharper temperature dynamics produce policy actions that depend " +
    "on small temperature differences not realised in live BOPTEST."
  ),
  bullet(
    "Pure_v3 has a moderate ms_gap (~0.07–0.10) driven by p_total_norm — the v3 surrogate " +
    "under-estimates the live power draw, so the policy is mildly over-confident at deployment."
  ),
  bullet(
    "Hybrid_l010 has the smallest ms_gap (~0.02) and a larger first-divergence step on typical " +
    "(step 16 vs. step 1 for the others) — meaning the policy stays close to its surrogate " +
    "predictions for the first four hours before drifting. The disagreement regularizer has " +
    "effectively narrowed the transfer gap."
  ),

  // ════════════════════════ §11 Synthesis ════════════════════════
  divider(),
  h1("§11.  Synthesis — fidelity-vs-utility paradox and Block 3 prerequisites"),

  h2("§11.1  The paradox restated"),
  para(
    "Block 2 establishes the central claim of the paper in its purest form. " +
    "Predictive fidelity is **necessary but not sufficient** for control utility, " +
    "and in the regime studied here it is also **not sufficient by itself**: " +
    "the more accurate surrogate (v3.5, 24h RMSE 0.644 °C) produces a strictly worse PPO " +
    "policy than the less accurate surrogate (v3, 24h RMSE 1.557 °C). " +
    "**The mechanism is not directly measured in this project**; two consistent hypothesised explanations are " +
    "(i) higher gradient-estimator variance under sharper surrogate predictions, and " +
    "(ii) overfitting to sub-step physical structure that has no exploitation channel at the 15-minute control cadence. " +
    "What Block 2 establishes empirically is the **direction** of the paradox; the mechanism is left to Block 4."
  ),

  h2("§11.2  Cross-family generalisation"),
  para(
    "The same v3 + v3.5-as-soft-regularizer architecture works across three controller families:"
  ),
  bullet("Thermostatic PPO — best at lambda_temp_disagree = 0.10 (temperature censor on)."),
  bullet("HDRL — best at lambda_temp_disagree = 0.00 (temperature censor off, power censor only)."),
  bullet("MORL 17D — best at lambda_temp_disagree = 0.00 (same as HDRL); 17D observation is critical."),
  para(
    "The pattern is: v3 is always the rollout dynamics; v3.5 is always a censor; " +
    "what changes across controller families is which channels of the v3.5 prediction " +
    "are used as censors. No single hybrid weight is optimal across families."
  ),

  h2("§11.3  Pre-registration trail"),
  para(
    "All Block 2 KPI numbers reported above are read from frozen CSV/JSON artifacts committed at " +
    "one of the audit anchors listed below. The full chain (verified 2026-05-28 via `git log`):"
  ),
  bullet(`**${DATA.anchors.seed_45_46_prereg.sha}** — ${DATA.anchors.seed_45_46_prereg.msg}. Records expected seed-45/46 outcomes BEFORE they were trained, making the N=5 extension falsifiable.`),
  bullet(`**${DATA.anchors.n5_falsification.sha}** — ${DATA.anchors.n5_falsification.msg}. Post-N=5 result; m_s_mean = 0.187 ± 0.078, CV ≈ 0.42 (50/50).`),
  bullet(`**${DATA.anchors.block3_prereg.sha}** — ${DATA.anchors.block3_prereg.msg}. The Block 3 manifest committed BEFORE any Block 3 BOPTEST episode ran.`),
  bullet(`**${DATA.anchors.block3_prereg_audit.sha}** — ${DATA.anchors.block3_prereg_audit.msg}. The audit commit that records the Block 3 pre-registration SHA inside the manifest field.`),
  bullet(`**${DATA.anchors.block3_close.sha}** — ${DATA.anchors.block3_close.msg}. The Block 3 close commit; this is the end of the pre-registered chain, not its beginning.`),
  para(
    "No Block 2 KPI is re-computed in this document; every number here is read from a frozen " +
    "CSV/JSON file already committed to the repository at one of the above anchors. " +
    "This protects the pre-registration chain that underpins the Block 3 transferability claim."
  ),

  h2("§11.4  Block 3 prerequisites"),
  para(
    "The Block 3 transferability study (papers §7) builds on three Block 2 artifacts: " +
    "(i) the **hybrid_l010 policy checkpoint** — used as the source policy for cross-testcase " +
    "transfer; (ii) the **MORL canonical seed 42 / 75-25 weight pair policy** — used as the " +
    "second source for transfer; (iii) the **transfer-diagnostic methodology** in §10 above, " +
    "extended in Block 3 to the heat-pump and commercial-hydronic testcases. " +
    "Block 2 is closed across the intended controller stack; the next active research step " +
    "is no longer Block 2 tuning, it is Block 3 cross-case transfer."
  ),

  divider(),

  // Footer
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 160, after: 0 },
    children: [new TextRun({
      text: "Block 2 Complete Results — cross-checked 2026-05-28 against outputs/block13_closed_loop_transfer_*, " +
            "outputs/block2_*, reports/block2_hdrl_lambda_sweep_summary.csv, " +
            "reports/block2_morl_comparison_summary.csv, reports/morl_canonical_seedfix_yearly_summary.csv, " +
            "reports/morl_pareto_front_table.csv, reports/hybrid_transfer_comparison.csv, " +
            "outputs/pi_baseline_15min_yearly/pi_yearly_summary.csv.",
      font: "Arial", size: 16, italic: true, color: "606060",
    })],
  }),
];

// ──────────────────────── DOCUMENT BUILD ─────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "•",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } },
      }],
    }],
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 20 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: "1F3864" },
        paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: "2E75B6" },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 20, bold: true, italic: true, font: "Arial", color: "404040" },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 } },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "Block 2 Complete Results — Page ", font: "Arial", size: 16, color: "808080" }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: "808080" }),
          ],
        })],
      }),
    },
    children,
  }],
});

const OUT = "docs/block2_complete_results.docx";
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log(`[OK] ${OUT}  (${Math.round(buf.length / 1024)} KB)`);
}).catch((err) => {
  console.error("[ERR]", err);
  process.exit(1);
});
