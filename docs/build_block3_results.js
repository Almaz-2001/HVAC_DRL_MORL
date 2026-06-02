// Block 3 Complete Results Document — full scientific narrative for the
// transferability-side of the HVAC DRL/MORL paper. Mirrors the depth of
// build_block1_results.js and build_block2_results.js.
// All numbers are sourced from project artifacts (CSV/JSON/YAML in outputs/, reports/, configs/).
// Run: node docs/build_block3_results.js

const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, PageBreak, LevelFormat
} = require("docx");

// ──────────────────────── DATA FROM PROJECT ARTIFACTS ────────────────────────
// Cross-checked 2026-05-28 against:
//   configs/block3_testcase_manifest.yaml         (pre-registration manifest, 42 KB)
//   configs/block3_actuator_mapping_*.yaml        (3 adapter configs)
//   reports/block3_transfer_matrix.csv            (top-level transfer verdict matrix)
//   reports/block3_hydronic_family_n2_summary.csv (primary + secondary aggregate)
//   reports/block3_bestest_hydronic_heat_pump_transfer_summary.csv  (primary detail)
//   reports/block3_bestest_hydronic_transfer_summary.csv            (secondary detail)
//   reports/block3_singlezone_commercial_hydronic_transfer_summary.csv (stretch detail)
//   reports/block3_bestest_hydronic_heat_pump_none_comparison.csv   (primary mode=none vs PI)
//   outputs/block3_*/pi_baseline_15min_yearly/pi_yearly_summary.csv (per-testcase PI yearly)
//   outputs/block3_*/thermostatic_hybrid_l010_adapter_none/         (frozen-controller yearly)
const DATA = {
  // ────────── Pre-registration anchors (verified via `git log`) ──────────
  anchors: {
    morl_prereg:        { sha: "93df9b3", msg: "pre-registration: seed45/46 falsification predictions for practical canonical" },
    morl_n5:            { sha: "62dc859", msg: "post-N5 result: action-saturation hypothesis falsified" },
    block3_manifest:    { sha: "1861e48", msg: "Block 3 pre-registration: transferability testcase manifest" },
    block3_audit_pre:   { sha: "2f9d596", msg: "Block 3 audit: record pre-registration commit SHA" },
    block3_hydronic:    { sha: "eb7091e", msg: "Block 3 pre-registration: hydronic heat-pump actuator adapter" },
    block3_secondary:   { sha: "46fbaa9", msg: "Block 3 pre-registration: bestest_hydronic direct supply adapter" },
    block3_stretch_pre: { sha: "645626e", msg: "Block 3 pre-registration: stretch testcase predictions and commercial hydronic adapter" },
    block3_close:       { sha: "7ada793", msg: "Block 3 audit: record close commit SHA" },
    block3_interp:      { sha: "cb7025f", msg: "Block 3 interpretation: component-level transferability and threshold-pass caveat" },
  },
  manifest_path: "configs/block3_testcase_manifest.yaml",
  protocol: "block3_transferability_v1",
  manifest_logged_at: "2026-05-18",
  source_testcase: "bestest_air",
  source_canonical: { ckpt: "models/ppo_thermostatic_hybrid_v3_v35_l010.zip", c_zon_j_per_k: 441269.4, lambda_temp: 0.10, lambda_pwr: 5e-5 },
  pass_threshold_factor: 1.25, // m_s_RL ≤ 1.25 × m_s_PI to PASS

  // ────────── Testcases (pre-registered selection) ──────────
  testcases: {
    primary: {
      label: "bestest_hydronic_heat_pump",
      role: "PRIMARY (closest neighbour of bestest_air)",
      structural_diff: "Hydronic loop driven by a heat pump (not air supply).",
      adapter_config: "configs/block3_actuator_mapping_bestest_hydronic_heat_pump.yaml",
      adapter_name: "hydronic_t_supply_to_setpoint_v1",
      anchor: "eb7091e",
    },
    secondary: {
      label: "bestest_hydronic",
      role: "SECONDARY (mid-difficulty hydronic; boiler/radiator)",
      structural_diff: "Hydronic distribution with boiler/radiator heat source instead of heat pump.",
      adapter_config: "configs/block3_actuator_mapping_bestest_hydronic.yaml",
      adapter_name: "hydronic_direct_supply_setpoint_adapter_v1",
      anchor: "46fbaa9",
    },
    stretch: {
      label: "singlezone_commercial_hydronic",
      role: "STRETCH (deliberately hard falsification probe)",
      structural_diff: "Substantially larger commercial zone volume; C_zon expected order-of-magnitude different a priori.",
      adapter_config: "configs/block3_actuator_mapping_singlezone_commercial_hydronic.yaml",
      adapter_name: "commercial_hydronic_supply_valve_adapter_v1",
      anchor: "645626e",
    },
  },

  // ────────── Recalibration regimes (pre-registered) ──────────
  regimes: {
    none: {
      description: "Frozen hybrid_l010 thermostatic checkpoint deployed directly on new testcase; no surrogate calibration re-run.",
      surrogate_action: "frozen from bestest_air canonical",
      controller_action: "frozen from Block 2 canonical (no fine-tune on new testcase)",
      compute_min: 30,
    },
    partial: {
      description: "Re-run Stage C residual head calibration on new corpus; keep C_zon and Stage A frozen.",
      surrogate_action: "Stage C only; Stage A and Stage B frozen",
      controller_action: "frozen from Block 2 canonical",
      compute_min: 90,
    },
    full: {
      description: "Re-run complete Stage A/B/C pipeline on new testcase.",
      surrogate_action: "Stage A + Stage B + Stage C from scratch",
      controller_action: "frozen from Block 2 canonical",
      compute_min: 240,
    },
    excluded: "controller re-fine-tune on new testcase (out of scope per manifest scope.deliberately_NOT_claimed)",
  },

  // ────────── Block 3 Transfer Matrix (from reports/block3_transfer_matrix.csv) ──────────
  transfer_matrix: [
    {
      testcase: "bestest_hydronic_heat_pump", role: "PRIMARY",
      adapter: "hydronic_t_supply_to_setpoint_v1",
      none_controller_verdict: "FAIL", full_controller_verdict: "FAIL",
      m_s_rl: 0.665, m_s_pi: 0.464, pass_threshold: 0.579,
      energy_delta_pct_vs_pi: -7.27,
      full_surrogate_verdict: "PASS",
      raw_rmse_t_c: 1.421, full_rmse_t_c: 0.565, rmse_improvement_pct: 60.21,
      c_zon_ratio_vs_bestest_air: 1.892,
      interpretation: "Residential hydronic heat-pump transfer fails on controller safety but succeeds on full surrogate recalibration.",
    },
    {
      testcase: "bestest_hydronic", role: "SECONDARY",
      adapter: "hydronic_direct_supply_setpoint_adapter_v1",
      none_controller_verdict: "FAIL", full_controller_verdict: "FAIL",
      m_s_rl: 0.976, m_s_pi: 0.750, pass_threshold: 0.938,
      energy_delta_pct_vs_pi: -5.84,
      full_surrogate_verdict: "PASS",
      raw_rmse_t_c: 2.666, full_rmse_t_c: 0.335, rmse_improvement_pct: 87.44,
      c_zon_ratio_vs_bestest_air: 1.954,
      interpretation: "Residential hydronic transfer replicates controller-side FAIL and surrogate-side PASS.",
    },
    {
      testcase: "singlezone_commercial_hydronic", role: "STRETCH",
      adapter: "commercial_hydronic_supply_valve_adapter_v1",
      none_controller_verdict: "PASS", full_controller_verdict: "PASS",
      m_s_rl: 0.431, m_s_pi: 0.628, pass_threshold: 0.785,
      energy_delta_pct_vs_pi: 35.33,
      full_surrogate_verdict: "PASS",
      raw_rmse_t_c: 1.952, full_rmse_t_c: 0.238, rmse_improvement_pct: 87.81,
      c_zon_ratio_vs_bestest_air: 1.909,
      interpretation: "Commercial stretch falsifies expected controller FAIL: safety passes but energy increases substantially.",
    },
  ],

  // ────────── Per-testcase detailed metrics ──────────
  primary_detail: {
    pi_yearly:    { m_s: 0.4636, violation_pct: 34.68, energy_kwh: 361.95 },
    none:         { m_s: 0.6652, violation_pct: 50.03, energy_kwh: 335.63, baseline_gap: 0.4350 },
    partial_top5: { rmse_t_c: 1.006, power_mae_w: 2335.8, m_s: 0.6652, status: "FAIL_CONTROL_DIAGNOSTIC_SURROGATE_FAIL" },
    partial_pwr:  { rmse_t_c: 0.977, power_mae_w: 1765.1, m_s: 0.6652, status: "FAIL_CONTROL_PARTIAL_POWER_SUCCESS" },
    partial_full: { rmse_t_c: 0.781, power_mae_w: 1767.8, m_s: 0.6652, status: "FAIL_CONTROL_CONDITIONAL_PASS_SURROGATE" },
    full:         { rmse_t_c: 0.565, power_mae_w: 1767.1, m_s: 0.6652, status: "FAIL_CONTROL_PASS_SURROGATE_FULL", c_zon_j_per_k: 834718, c_zon_ratio: 1.892, rmse_improvement_pct: 60.21, power_mae_improvement_pct: 39.51 },
  },
  secondary_detail: {
    pi_yearly:    { m_s: 0.7502, violation_pct: 44.89, energy_kwh: 231.42 },
    none:         { m_s: 0.9760, violation_pct: 68.00, energy_kwh: 217.91, baseline_gap: 0.3010 },
    full:         { rmse_t_c: 0.335, power_mae_w: 84.98, m_s: 0.9760, status: "FAIL_CONTROL_PASS_SURROGATE_FULL", c_zon_j_per_k: 862247, c_zon_ratio: 1.954, rmse_improvement_pct: 87.44, power_mae_improvement_pct: 89.16 },
  },
  stretch_detail: {
    pi_yearly:    { m_s: 0.6282, violation_pct: 51.51, energy_kwh: 13523.10 },
    none:         { m_s: 0.4315, violation_pct: 34.83, energy_kwh: 18301.42, baseline_gap: -0.3131, verdict: "PASS_SAFETY_FAIL_ENERGY" },
    full:         { rmse_t_c: 0.238, power_mae_w: 75652.5, m_s: 0.4315, status: "PASS_SURROGATE_FULL_RECALIBRATION", c_zon_j_per_k: 842505, c_zon_ratio: 1.909, rmse_improvement_pct: 87.81, power_mae_improvement_pct: 1.31 },
  },

  // ────────── Stretch pre-registered predictions (manifest line 774+) ──────────
  stretch_predictions: {
    date_logged: "2026-05-19",
    finalized_before_runs: true,
    none_controller: { expected: "FAIL", apriori: 0.80, actual: "PASS", outcome: "FALSIFIED" },
    full_rmse_improvement_pct: { expected_range: [50, 90], apriori_for_range: 0.70, actual: 87.81, outcome: "CONFIRMED" },
    c_zon: {
      hyp_a_uniform: { range: [1.7, 2.2], apriori: 0.35, actual: 1.909, outcome: "CONFIRMED" },
      hyp_b_scale:   { range: [3.0, 10.0], apriori: 0.50, outcome: "FALSIFIED" },
      hyp_c_fail:    { apriori: 0.15, outcome: "FALSIFIED" },
    },
  },

  // ────────── Hypothesis closure (manifest line 850+) ──────────
  hypotheses: [
    { id: "H1_strong",
      claim: "Frozen-recipe deployment at mode=none produces deployment-ready transfer on hydronic family",
      verdict: "FALSIFIED",
      evidence: "Frozen deployment FAILS pre-registered 1.25× PI safety threshold on N=2 of N=3 (primary + secondary). Stretch is a THRESHOLD PASS only — m_s_RL = 0.431 ≤ 0.785 — but uses 35.3% more energy than PI, so not deployment-ready.",
    },
    { id: "H2_medium",
      claim: "Partial Stage C recalibration is sufficient to recover controller transfer",
      verdict: "FALSIFIED_BY_STRUCTURAL_DEFINITION",
      evidence: "Partial regime recalibrates only surrogate Stage C; the controller is frozen by manifest scope. Therefore live controller KPI cannot change vs mode=none unless controller fine-tuning is added (explicitly excluded by scope.deliberately_NOT_claimed).",
    },
    { id: "H3_weak (surrogate side)",
      claim: "Full Stage A/B/C recalibration produces a usable surrogate on the new testcase",
      verdict: "SUPPORTED on N=3",
      evidence: "60.2% (primary) / 87.4% (secondary) / 87.8% (stretch) RMSE_T improvement under full recalibration. C_zon re-identified consistently in 1.89–1.95× range vs bestest_air. Inverse surrogate-calibration component transfers.",
    },
    { id: "H3_weak (controller side)",
      claim: "Frozen controller transfers given a valid actuator adapter",
      verdict: "FALSIFIED with regime-dependent failure modes",
      evidence: "Controller transfer is not universally reliable under the frozen-method scope. Residential hydronic (primary + secondary) fails comfort; commercial stretch passes safety but at large energy cost.",
    },
  ],

  // ────────── Block 3 hypotheses on C_zon scaling (manifest pre-reg + outcomes) ──────────
  c_zon_summary: {
    bestest_air_baseline_j_per_k: 441269.4,
    primary_full:    { j_per_k: 834718,  ratio: 1.892 },
    secondary_full:  { j_per_k: 862247,  ratio: 1.954 },
    stretch_full:    { j_per_k: 842505,  ratio: 1.909 },
    ratio_mean: 1.918, ratio_std: 0.032, ratio_range: "1.89 – 1.95",
    hypothesis_winner: "hydronic_family_uniform (apriori 0.35; actual ratios cluster within ±2% of 1.92×)",
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
function figure(path, w_emu, h_emu, captionTxt) {
  if (!fs.existsSync(path)) {
    return para(`[figure missing: ${path}]`);
  }
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 160, after: 80 },
      children: [new ImageRun({
        type: "png",
        data: fs.readFileSync(path),
        transformation: { width: w_emu / 9525, height: h_emu / 9525 },
        altText: { title: path.split("/").pop(), description: captionTxt, name: path.split("/").pop() },
      })],
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
function verdictShade(text) {
  if (text === "PASS" || text.startsWith("PASS")) return POS_SHADE;
  if (text === "FAIL" || text.startsWith("FAIL") || text === "FALSIFIED") return NEG_SHADE;
  if (text.includes("CONFIRMED") || text.includes("SUPPORTED")) return POS_SHADE;
  if (text.includes("THRESHOLD") || text.includes("CONDITIONAL")) return NEU_SHADE;
  return null;
}

// ──────────────────────── TABLES ─────────────────────────────────────────────
function tableTestcases() {
  const rows = [["Role", "Testcase", "Structural difference vs bestest_air", "Adapter config"]];
  const tcs = ["primary","secondary","stretch"];
  for (const k of tcs) {
    const t = DATA.testcases[k];
    rows.push([t.role.split(" ")[0], t.label, t.structural_diff, t.adapter_name]);
  }
  return buildTable(rows, [1200, 2480, 3800, 1880]);
}

function tableRegimes() {
  const rows = [["Regime", "Surrogate action", "Controller action", "Compute (min/testcase)"]];
  for (const k of ["none","partial","full"]) {
    const r = DATA.regimes[k];
    rows.push([k, r.surrogate_action, r.controller_action, "~" + r.compute_min]);
  }
  return buildTable(rows, [880, 3640, 3120, 1720]);
}

function tableTransferMatrix() {
  const rows = [["Testcase", "Adapter", "mode=none ctrl", "mode=full ctrl", "m_s RL", "m_s PI", "Pass threshold", "Energy Δ% vs PI", "Surrogate (full)", "Raw RMSE_T °C", "Full RMSE_T °C", "RMSE % gain", "C_zon ratio"]];
  for (const t of DATA.transfer_matrix) {
    rows.push([
      t.testcase, t.adapter,
      t.none_controller_verdict, t.full_controller_verdict,
      t.m_s_rl.toFixed(3), t.m_s_pi.toFixed(3), t.pass_threshold.toFixed(3),
      (t.energy_delta_pct_vs_pi >= 0 ? "+" : "") + t.energy_delta_pct_vs_pi.toFixed(2) + "%",
      t.full_surrogate_verdict,
      t.raw_rmse_t_c.toFixed(3), t.full_rmse_t_c.toFixed(3),
      t.rmse_improvement_pct.toFixed(2) + "%",
      t.c_zon_ratio_vs_bestest_air.toFixed(3) + "×",
    ]);
  }
  const shadeFn = (i, j, t) => {
    if (i === 0) return null;
    if (j === 2 || j === 3 || j === 8) return verdictShade(t);
    return null;
  };
  return buildTable(rows, [1800, 1480, 760, 760, 560, 560, 760, 760, 880, 760, 760, 640, 640], shadeFn);
}

function tableHypotheses() {
  const rows = [["Hypothesis", "Claim", "Verdict", "Evidence"]];
  for (const h of DATA.hypotheses) {
    rows.push([h.id, h.claim, h.verdict, h.evidence]);
  }
  const shadeFn = (i, j, t) => {
    if (j === 2 && i > 0) return verdictShade(t);
    return null;
  };
  return buildTable(rows, [1800, 2280, 2080, 3200], shadeFn);
}

function tablePredictions() {
  const P = DATA.stretch_predictions;
  const rows = [
    ["Prediction", "Pre-registered expectation", "A-priori probability", "Actual outcome", "Verdict"],
    ["mode=none controller verdict", P.none_controller.expected, P.none_controller.apriori.toFixed(2), P.none_controller.actual, P.none_controller.outcome],
    ["mode=full surrogate RMSE % gain", "[" + P.full_rmse_improvement_pct.expected_range.join(", ") + "] %", P.full_rmse_improvement_pct.apriori_for_range.toFixed(2), P.full_rmse_improvement_pct.actual.toFixed(2) + " %", P.full_rmse_improvement_pct.outcome],
    ["C_zon hypothesis A (uniform hydronic)", "[" + P.c_zon.hyp_a_uniform.range.join(", ") + "] ×", P.c_zon.hyp_a_uniform.apriori.toFixed(2), P.c_zon.hyp_a_uniform.actual.toFixed(3) + " ×", P.c_zon.hyp_a_uniform.outcome],
    ["C_zon hypothesis B (scale-dependent)",  "[" + P.c_zon.hyp_b_scale.range.join(", ") + "] ×", P.c_zon.hyp_b_scale.apriori.toFixed(2), "1.909 ×", P.c_zon.hyp_b_scale.outcome],
    ["C_zon hypothesis C (pipeline failure)", "Stage A/B/C fails to converge", P.c_zon.hyp_c_fail.apriori.toFixed(2), "Stage A/B/C converged in all 3", P.c_zon.hyp_c_fail.outcome],
  ];
  const shadeFn = (i, j, t) => {
    if (j === 4 && i > 0) return verdictShade(t);
    return null;
  };
  return buildTable(rows, [2400, 2200, 1480, 1880, 1400], shadeFn);
}

function tableCZon() {
  const C = DATA.c_zon_summary;
  const rows = [
    ["Testcase", "C_zon (J/K)", "Ratio vs bestest_air"],
    ["bestest_air (Block 1 §2.2)", C.bestest_air_baseline_j_per_k.toExponential(3) + " J/K", "1.000 × (baseline)"],
    ["bestest_hydronic_heat_pump (PRIMARY)", C.primary_full.j_per_k.toExponential(3) + " J/K", C.primary_full.ratio.toFixed(3) + " ×"],
    ["bestest_hydronic (SECONDARY)",         C.secondary_full.j_per_k.toExponential(3) + " J/K", C.secondary_full.ratio.toFixed(3) + " ×"],
    ["singlezone_commercial_hydronic (STRETCH)", C.stretch_full.j_per_k.toExponential(3) + " J/K", C.stretch_full.ratio.toFixed(3) + " ×"],
    ["Hydronic-family mean ± std",  `${(C.primary_full.j_per_k+C.secondary_full.j_per_k+C.stretch_full.j_per_k)/3 / 1e3 | 0} kJ/K`, `${C.ratio_mean.toFixed(3)} ± ${C.ratio_std.toFixed(3)} (range ${C.ratio_range})`],
  ];
  const shadeFn = (i, j, t) => i === 5 ? HEAD_SHADE : null;
  return buildTable(rows, [3200, 3080, 3080], shadeFn);
}

function tablePrimaryDetail() {
  const P = DATA.primary_detail;
  const rows = [
    ["Regime / artifact", "RMSE_T °C", "Power MAE W", "m_s", "Status"],
    ["PI baseline (yearly)",       "—",            "—",                     P.pi_yearly.m_s.toFixed(3),    "REFERENCE"],
    ["mode=none (frozen)",         "—",            "—",                     P.none.m_s.toFixed(3),         "FAIL_CONTROL"],
    ["partial: Stage C top-5%",    P.partial_top5.rmse_t_c.toFixed(3), P.partial_top5.power_mae_w.toFixed(0), P.partial_top5.m_s.toFixed(3), P.partial_top5.status],
    ["partial: Stage C all-rows / power-head", P.partial_pwr.rmse_t_c.toFixed(3), P.partial_pwr.power_mae_w.toFixed(0), P.partial_pwr.m_s.toFixed(3), P.partial_pwr.status],
    ["partial: Stage C all-rows / heads-only", P.partial_full.rmse_t_c.toFixed(3), P.partial_full.power_mae_w.toFixed(0), P.partial_full.m_s.toFixed(3), P.partial_full.status],
    ["full: Stage A/B/C all-rows", P.full.rmse_t_c.toFixed(3), P.full.power_mae_w.toFixed(0), P.full.m_s.toFixed(3), P.full.status],
  ];
  return buildTable(rows, [3120, 1200, 1480, 880, 2680]);
}

// ──────────────────────── DOCUMENT BODY ──────────────────────────────────────
const children = [
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 0, after: 240 },
    children: [new TextRun({ text: "Block 3 Complete Results", bold: true, font: "Arial", size: 36, color: "1F3864" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 0, after: 240 },
    children: [new TextRun({
      text: "Pre-registered transferability of the v3+v3.5 hybrid recipe to three BOPTEST hydronic-family testcases " +
            "(bestest_hydronic_heat_pump, bestest_hydronic, singlezone_commercial_hydronic) under three " +
            "pre-registered recalibration regimes (none / partial / full).",
      italic: true, font: "Arial", size: 22, color: "2E75B6",
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 0, after: 480 },
    children: [new TextRun({
      text: "All numbers cross-checked against project artifacts (CSV/JSON/YAML) and audit anchors on 2026-05-28.",
      italic: true, font: "Arial", size: 18, color: "808080",
    })],
  }),

  divider(),

  // ════════════════════════ §1 Methodology ════════════════════════
  h1("§1.  Methodology, pre-registration, and reading order"),

  h2("§1.1  Reading order"),
  para(
    "Block 1 established the surrogate-level claim: the v3 control-oriented surrogate and the calibrated v3.5 " +
    "physical twin offer complementary strengths. Block 2 established the controller-level claim on bestest_air: " +
    "the hybrid recipe (v3 dynamics + v3.5 disagreement reward-shaping) produces the strongest controller, with " +
    "controller-family-specific λ values fixed at λ_temp = 0.10, λ_pwr = 5×10⁻⁵ for thermostatic PPO. " +
    "**Block 3 asks: does this recipe transfer to BOPTEST testcases other than bestest_air?**"
  ),
  para("The Block 3 narrative follows the pre-registration / outcome / hypothesis closure structure:"),
  bullet("§2 Pre-registration protocol — manifest, testcases, regimes, controllers, audit anchors."),
  bullet("§3 Actuator-interface adaptation — three per-testcase adapter configs."),
  bullet("§4 Transfer matrix — the headline result across testcase × regime × KPI."),
  bullet("§5 Primary testcase (bestest_hydronic_heat_pump) — detailed per-regime breakdown."),
  bullet("§6 Secondary testcase (bestest_hydronic) — replication of the primary pattern."),
  bullet("§7 Stretch testcase (singlezone_commercial_hydronic) — pre-registered predictions and surprises."),
  bullet("§8 C_zon consistency analysis — the hydronic-family uniform-mass hypothesis."),
  bullet("§9 Hypothesis closure — H1_strong / H2_medium / H3_weak (surrogate, controller)."),
  bullet("§10 Pre-registered predictions vs observed outcomes — Popperian audit trail."),
  bullet("§11 Synthesis and Block 4 implications."),

  h2("§1.2  Pre-registration anchors (verified via git log)"),
  para(
    `Block 3 is **pre-registered**: the manifest \`${DATA.manifest_path}\` (4 KB pre-registration + 38 KB ` +
    "results append-only blocks) was committed BEFORE any non-bestest_air BOPTEST run was executed. " +
    `Pre-registration logged on **${DATA.manifest_logged_at}**; protocol identifier **${DATA.protocol}**. ` +
    "The full audit chain (commit messages verbatim from `git log --oneline`):"
  ),
  bullet(`**${DATA.anchors.morl_prereg.sha}** — ${DATA.anchors.morl_prereg.msg}`),
  bullet(`**${DATA.anchors.morl_n5.sha}** — ${DATA.anchors.morl_n5.msg}`),
  bullet(`**${DATA.anchors.block3_manifest.sha}** — ${DATA.anchors.block3_manifest.msg}  ← Block 3 pre-registration manifest`),
  bullet(`**${DATA.anchors.block3_audit_pre.sha}** — ${DATA.anchors.block3_audit_pre.msg}`),
  bullet(`**${DATA.anchors.block3_hydronic.sha}** — ${DATA.anchors.block3_hydronic.msg}`),
  bullet(`**${DATA.anchors.block3_secondary.sha}** — ${DATA.anchors.block3_secondary.msg}`),
  bullet(`**${DATA.anchors.block3_stretch_pre.sha}** — ${DATA.anchors.block3_stretch_pre.msg}  ← stretch predictions PRE-registered before runs`),
  bullet(`**${DATA.anchors.block3_close.sha}** — ${DATA.anchors.block3_close.msg}`),
  bullet(`**${DATA.anchors.block3_interp.sha}** — ${DATA.anchors.block3_interp.msg}`),
  para(
    "The pre-registration block in the manifest is **bit-identical** between its first commit (1861e48) and " +
    "the close (7ada793) — only the result-appendix sections are appended. Auditors verify against the parent " +
    "commit's diff. This protects the falsifiability of Block 3's hypotheses: any number reported below was " +
    "predictable but not predicted before the run."
  ),

  h2("§1.3  Claim boundary (manifest scope.deliberately_NOT_claimed)"),
  para("Block 3 deliberately does NOT claim:"),
  bullet("universal building generalisation"),
  bullet("cross-climate generalisation (single weather file source)"),
  bullet("transfer to fundamentally different HVAC topologies (e.g., VRF, radiant)"),
  bullet("continual learning across multiple buildings without forgetting"),
  para(
    "The intended claim is narrower: _the hybrid recipe transfers to closely related BOPTEST testcases under " +
    "explicitly stated recalibration conditions and controller-interface compatibility_."
  ),

  h2("§1.4  Testcase selection (pre-registered)"),
  para(
    "Three single-zone hydronic testcases were pre-selected to span an increasing difficulty gradient relative " +
    "to bestest_air. Selection criteria (fixed before inspecting any candidate response):"
  ),
  bullet("(a) single-zone or single-zone-like envelope"),
  bullet("(b) heating-capable HVAC (cooling optional)"),
  bullet("(c) actuator interface compatible with direct supply-temperature command OR overridable with documented mapping"),
  bullet("(d) at least one structural difference from bestest_air (actuator, source, envelope size, or climate) so transfer is non-trivial"),
  caption("Table 1 — Pre-registered testcase selection.",
          " From configs/block3_testcase_manifest.yaml testcase_candidates block."),
  tableTestcases(),

  h2("§1.5  Recalibration regimes (pre-registered)"),
  para(
    "Three regimes characterise the transferability gradient from \"frozen-everything\" to \"fully re-calibrated " +
    "surrogate, frozen controller\". The controller is **always frozen** by manifest scope; this isolates the " +
    "transferability of the calibration pipeline itself."
  ),
  caption("Table 2 — Recalibration regimes.",
          " From configs/block3_testcase_manifest.yaml recalibration_regimes block. " +
          "Excluded by manifest: controller re-fine-tune on new testcase."),
  tableRegimes(),

  h2("§1.6  Controller families and pass threshold"),
  para(
    "The thermostatic_hybrid family is the principal Block 3 controller: " +
    `frozen checkpoint \`${DATA.source_canonical.ckpt}\` (Block 2 canonical hybrid_l010, ` +
    `λ_temp = ${DATA.source_canonical.lambda_temp}, λ_pwr = ${DATA.source_canonical.lambda_pwr.toExponential(0)}) ` +
    "with no fine-tuning on the new testcase. The pass threshold is **m_s_RL ≤ 1.25 × m_s_PI** for the testcase's " +
    "BOPTEST built-in PI controller; threshold is computed per-testcase, not global, because PI's m_s varies by testcase. " +
    "The threshold value 1.25 was pre-registered in the manifest, not chosen post hoc to match results."
  ),

  // ════════════════════════ §2 The actuator adapter problem ════════════════════════
  divider(),
  h1("§2.  Actuator-interface adaptation"),
  para(
    "bestest_air exposes a **direct supply-temperature** actuation interface (the agent commands an air " +
    "supply setpoint in 18–35 °C). The three hydronic testcases expose **different actuator types**: " +
    "the heat pump testcase has a heat-pump setpoint-and-enable interface; the residential hydronic testcase " +
    "has a boiler/radiator direct supply-setpoint interface; and the commercial hydronic testcase has a " +
    "supply-valve interface. " +
    "Without adaptation, the bestest_air-trained policy's action output would land on undefined BOPTEST " +
    "actuator signals, and the comparison would not be a transfer test — it would be a programming error."
  ),
  para(
    "Each testcase gets a per-testcase **actuator adapter config** that maps the policy's continuous t_supply " +
    "action onto the testcase's actuator interface. These configs are pre-registered separately " +
    `(anchors ${DATA.anchors.block3_hydronic.sha} / ${DATA.anchors.block3_secondary.sha} / ${DATA.anchors.block3_stretch_pre.sha}) so the mapping cannot be tuned post-hoc.`
  ),
  bullet(`**${DATA.testcases.primary.label}**: adapter \`${DATA.testcases.primary.adapter_name}\` (config: ${DATA.testcases.primary.adapter_config})`),
  bullet(`**${DATA.testcases.secondary.label}**: adapter \`${DATA.testcases.secondary.adapter_name}\``),
  bullet(`**${DATA.testcases.stretch.label}**: adapter \`${DATA.testcases.stretch.adapter_name}\``),

  // ════════════════════════ §3 Transfer matrix ════════════════════════
  divider(),
  h1("§3.  Block 3 transfer matrix — the headline"),
  para(
    "The transfer matrix is the single-table summary of Block 3 across the three testcases. " +
    "Read row-by-row, each row tells the controller-side story (mode=none and mode=full verdicts; m_s_RL vs " +
    "m_s_PI; energy delta) and the surrogate-side story (full Stage A/B/C verdict; raw vs full RMSE_T; C_zon " +
    "ratio vs bestest_air)."
  ),
  caption("Table 3 — Block 3 transfer matrix.",
          " Source: reports/block3_transfer_matrix.csv. " +
          "Green = PASS; red = FAIL; yellow = threshold/conditional. " +
          "Pass threshold per row = 1.25 × m_s_PI for that testcase."),
  tableTransferMatrix(),

  // Heatmap figure
  ...figure(
    "reports/figures/article_real/main_fig5_block3_transfer_verdict_heatmap.png",
    5669280, 3000000,
    "Figure 1. Block 3 transfer verdict heatmap (m_s_RL vs threshold, colour-coded by verdict)."
  ),
  para(
    "_Figure 1. Block 3 transfer verdict heatmap across three testcases × {mode=none, mode=full} for the " +
    "thermostatic_hybrid controller and the corresponding surrogate. Cell colour encodes the pass-threshold " +
    "verdict against the pre-registered 1.25 × m_s_PI bound._",
    { size: 18 }
  ),

  // ════════════════════════ §4 Primary testcase ════════════════════════
  divider(),
  h1("§4.  Primary testcase — bestest_hydronic_heat_pump"),
  para(
    "**Predicted: easiest of the three** (closest neighbour to bestest_air; same envelope class but with " +
    `hydronic actuator + heat pump). PI yearly baseline: m_s = ${DATA.primary_detail.pi_yearly.m_s.toFixed(3)}; ` +
    `violation = ${DATA.primary_detail.pi_yearly.violation_pct.toFixed(1)}%; energy = ${DATA.primary_detail.pi_yearly.energy_kwh.toFixed(1)} kWh. ` +
    `Pass threshold: m_s_RL ≤ ${(1.25 * DATA.primary_detail.pi_yearly.m_s).toFixed(3)} ` +
    "(= 1.25 × m_s_PI)."
  ),
  para(
    `Mode=none (frozen recipe): m_s = ${DATA.primary_detail.none.m_s.toFixed(3)} ` +
    `(${(DATA.primary_detail.none.m_s/DATA.primary_detail.pi_yearly.m_s).toFixed(2)}× PI), ` +
    `violation = ${DATA.primary_detail.none.violation_pct.toFixed(1)}%, ` +
    `energy = ${DATA.primary_detail.none.energy_kwh.toFixed(1)} kWh ` +
    `(saves ${(100*(1-DATA.primary_detail.none.energy_kwh/DATA.primary_detail.pi_yearly.energy_kwh)).toFixed(1)}% over PI's ${DATA.primary_detail.pi_yearly.energy_kwh.toFixed(1)} kWh, but fails comfort). ` +
    `**Controller verdict: FAIL** (m_s_RL = ${DATA.primary_detail.none.m_s.toFixed(3)} > ${(1.25*DATA.primary_detail.pi_yearly.m_s).toFixed(3)}). ` +
    "The frozen bestest_air controller does NOT transfer comfort-safely to the heat-pump testcase."
  ),
  para(
    "**Partial regimes give surrogate-side signal but cannot rescue the controller.** " +
    "Three partial variants were tried in the surrogate-side falsification probe (Stage C top-5% excitation, " +
    "Stage C all-rows power-head-only, Stage C all-rows heads-only); they vary in surrogate fidelity gain but " +
    "all leave the live controller KPI unchanged (because the controller is frozen by manifest scope)."
  ),
  caption("Table 4 — Primary testcase per-regime detail (controller frozen across all rows).",
          " Source: reports/block3_bestest_hydronic_heat_pump_transfer_summary.csv. " +
          "m_s does not vary across rows because controller is frozen; what varies is surrogate fidelity."),
  tablePrimaryDetail(),
  para(
    `**Full Stage A/B/C re-calibration**: RMSE_T improves from ${DATA.primary_detail.full.rmse_t_c.toFixed(3)} °C ` +
    `to baseline-on-this-testcase, a ${DATA.primary_detail.full.rmse_improvement_pct.toFixed(1)}% reduction; ` +
    `power MAE improves by ${DATA.primary_detail.full.power_mae_improvement_pct.toFixed(1)}%. ` +
    `Re-identified C_zon = ${(DATA.primary_detail.full.c_zon_j_per_k/1000).toFixed(0)} kJ/K, ` +
    `or **${DATA.primary_detail.full.c_zon_ratio.toFixed(3)}×** the bestest_air value (4.413×10⁵ J/K). ` +
    "Surrogate verdict: **PASS**. Controller verdict: still FAIL (controller is frozen)."
  ),

  // ════════════════════════ §5 Secondary testcase ════════════════════════
  divider(),
  h1("§5.  Secondary testcase — bestest_hydronic"),
  para(
    "**Predicted: mid-difficulty** (hydronic distribution with boiler/radiator source instead of heat pump). " +
    `PI yearly: m_s = ${DATA.secondary_detail.pi_yearly.m_s.toFixed(3)}; violation = ${DATA.secondary_detail.pi_yearly.violation_pct.toFixed(1)}%; ` +
    `energy = ${DATA.secondary_detail.pi_yearly.energy_kwh.toFixed(1)} kWh. ` +
    `Pass threshold: m_s_RL ≤ ${(1.25*DATA.secondary_detail.pi_yearly.m_s).toFixed(3)}.`
  ),
  para(
    `Mode=none: m_s = ${DATA.secondary_detail.none.m_s.toFixed(3)} ` +
    `(${(DATA.secondary_detail.none.m_s/DATA.secondary_detail.pi_yearly.m_s).toFixed(2)}× PI), ` +
    `violation = ${DATA.secondary_detail.none.violation_pct.toFixed(1)}%, ` +
    `energy = ${DATA.secondary_detail.none.energy_kwh.toFixed(1)} kWh. ` +
    "**Controller verdict: FAIL** — m_s exceeds the pre-registered 1.25× PI threshold; the secondary testcase " +
    "**replicates the primary FAIL pattern**, confirming that the failure is not specific to heat-pump actuators."
  ),
  para(
    `**Full Stage A/B/C**: RMSE_T improves by **${DATA.secondary_detail.full.rmse_improvement_pct.toFixed(1)}%** ` +
    `(${DATA.transfer_matrix[1].raw_rmse_t_c.toFixed(2)} → ${DATA.secondary_detail.full.rmse_t_c.toFixed(3)} °C), ` +
    `power MAE by ${DATA.secondary_detail.full.power_mae_improvement_pct.toFixed(1)}%. ` +
    `C_zon = ${(DATA.secondary_detail.full.c_zon_j_per_k/1000).toFixed(0)} kJ/K = ` +
    `**${DATA.secondary_detail.full.c_zon_ratio.toFixed(3)}×** bestest_air. ` +
    "Surrogate verdict: **PASS**; controller verdict: still FAIL. " +
    "The N=2 evidence at this point: controller-FAIL + surrogate-PASS pattern replicates."
  ),

  // ════════════════════════ §6 Stretch testcase ════════════════════════
  divider(),
  h1("§6.  Stretch testcase — singlezone_commercial_hydronic"),
  para(
    "**Predicted: hardest of the three** (commercial zone volume an order of magnitude larger than bestest_air; " +
    "C_zon a priori expected to scale with volume → hypothesis B = scale-dependent C_zon, a-priori probability " +
    "0.50). The stretch testcase exists specifically to **probe the falsification boundary** — to find where the " +
    "hybrid recipe fails."
  ),
  para(
    `PI yearly: m_s = ${DATA.stretch_detail.pi_yearly.m_s.toFixed(3)}; violation = ${DATA.stretch_detail.pi_yearly.violation_pct.toFixed(1)}%; ` +
    `energy = ${DATA.stretch_detail.pi_yearly.energy_kwh.toFixed(1)} kWh (note the larger absolute energy of a commercial zone). ` +
    `Pass threshold: m_s_RL ≤ ${(1.25*DATA.stretch_detail.pi_yearly.m_s).toFixed(3)}.`
  ),
  para(
    `Mode=none: m_s = ${DATA.stretch_detail.none.m_s.toFixed(3)} ` +
    `(${(DATA.stretch_detail.none.m_s/DATA.stretch_detail.pi_yearly.m_s).toFixed(2)}× PI — i.e., the RL agent's ` +
    "comfort is *better* than PI's). " +
    "**Controller verdict: PASS** — but with two important caveats:"
  ),
  bullet(
    "**Energy: +35.3% over PI.** The RL agent achieves better comfort but consumes 18,301 kWh vs PI's 13,523 kWh. " +
    "Following the manifest's pre-registered interpretation, this is a **threshold-pass, not a deployment-ready pass**: " +
    "the m_s safety bound is satisfied but the energy footprint is not deployment-ready."
  ),
  bullet(
    "**This outcome falsifies a pre-registered prediction.** " +
    "Pre-registered (`645626e`) expectation for mode=none controller verdict was **FAIL** with a-priori probability " +
    "**0.80**, on the rationale that larger building dynamics would expose more controller misalignment. " +
    "The observed PASS-with-energy-penalty refutes this prediction. The manifest's hypothesis-resolution paragraph " +
    "(committed at audit anchor `7ada793`) reports this as the expected falsifiability behaviour."
  ),
  para(
    `**Full Stage A/B/C**: RMSE_T improves by **${DATA.stretch_detail.full.rmse_improvement_pct.toFixed(1)}%** ` +
    `(${DATA.transfer_matrix[2].raw_rmse_t_c.toFixed(2)} → ${DATA.stretch_detail.full.rmse_t_c.toFixed(3)} °C). ` +
    `C_zon = ${(DATA.stretch_detail.full.c_zon_j_per_k/1000).toFixed(0)} kJ/K = ` +
    `**${DATA.stretch_detail.full.c_zon_ratio.toFixed(3)}×** bestest_air. ` +
    "Surrogate verdict: PASS."
  ),
  para(
    "**The C_zon result is a major Popperian surprise.** A-priori, the manifest assigned probability **0.50** to " +
    "hypothesis B (commercial-scale C_zon 3–10× larger) and only **0.35** to hypothesis A (uniform hydronic-family " +
    "1.7–2.2× larger). The observed C_zon ratio = 1.909× falls **inside the lower-probability hypothesis A range**, " +
    "**falsifying** hypothesis B. The hydronic-family C_zon appears to be a property of the heating system type, " +
    "not of the zone volume. This is reported in §8 as the C_zon consistency analysis."
  ),

  // ════════════════════════ §7 C_zon consistency ════════════════════════
  divider(),
  h1("§7.  C_zon consistency — the hydronic-family uniform-mass hypothesis"),

  caption("Table 5 — C_zon re-identification across N=4 testcases (bestest_air baseline + 3 hydronic).",
          " Sources: reports/block3_transfer_matrix.csv c_zon_ratio_vs_bestest_air column; " +
          "Block 1 §2.2 for bestest_air baseline."),
  tableCZon(),

  para(
    `Across the three hydronic testcases, C_zon re-identification by Stage A/B/C falls within a tight ` +
    `**${DATA.c_zon_summary.ratio_range}** range — mean ${DATA.c_zon_summary.ratio_mean.toFixed(3)} ± ` +
    `${DATA.c_zon_summary.ratio_std.toFixed(3)} × bestest_air. ` +
    "This is the strongest single physical finding of Block 3: " +
    "the calibrated thermal capacitance of the hydronic-family single-zone testcases is approximately uniform, " +
    "and is approximately twice the bestest_air air-zone thermal capacitance."
  ),
  ...figure(
    "reports/figures/article_real/main_fig6_block3_czon_consistency.png",
    5669280, 3000000,
    "Figure 2. C_zon consistency across hydronic testcases."
  ),
  para(
    "_Figure 2. C_zon re-identified by full Stage A/B/C on each hydronic testcase, normalised by the bestest_air " +
    "baseline. The three hydronic ratios cluster within ±2% of 1.92×, despite testcase 3 having an order-of-magnitude " +
    "larger zone volume. Pre-registered hypothesis B (volume-dependent C_zon, a-priori 0.50) is falsified; " +
    "hypothesis A (uniform hydronic-family, a-priori 0.35) is confirmed._",
    { size: 18 }
  ),
  para(
    "**Why this matters scientifically**: the inverse calibration framework re-identifies a physically meaningful " +
    "parameter that is **transferable** across the hydronic family without scaling with the obvious zone-size " +
    "proxy. This generalises the calibration component of the v3.5 surrogate beyond a single building."
  ),

  // ════════════════════════ §8 Hypothesis closure ════════════════════════
  divider(),
  h1("§8.  Hypothesis closure"),
  para(
    "The manifest pre-registered four hypotheses with explicit operational definitions. Block 3 closes all four " +
    "with the verdicts below; the evidence column references the row(s) of the transfer matrix that drive each verdict."
  ),
  caption("Table 6 — Hypothesis closure.",
          " Source: configs/block3_testcase_manifest.yaml `aggregated_results.hypothesis_status_final` block " +
          "(appended after Block 3 close — audit anchor 7ada793)."),
  tableHypotheses(),
  para(
    "**Headline reading**: the surrogate-side (inverse calibration) of the v3.5 pipeline transfers to the hydronic " +
    "family with strong RMSE_T improvements (60–88%) and a near-uniform C_zon re-identification. " +
    "The controller-side (frozen bestest_air policy through a per-testcase actuator adapter) is **not universally** " +
    "deployment-ready: it fails comfort on residential hydronic cases and passes only conditionally on the " +
    "commercial case (with a +35% energy penalty).",
    { spaceBefore: 160 }
  ),

  // ════════════════════════ §9 Pre-registered predictions ════════════════════════
  divider(),
  h1("§9.  Pre-registered predictions vs observed outcomes — Popperian audit"),
  para(
    "The stretch testcase carried **specific numerical pre-registered predictions** with a-priori probabilities " +
    `(audit anchor ${DATA.anchors.block3_stretch_pre.sha}, logged ${DATA.stretch_predictions.date_logged}, ` +
    "before any singlezone_commercial_hydronic BOPTEST episode ran). " +
    "Reporting the predicted-vs-observed mapping is the central Popperian discipline of Block 3: if the predictions " +
    "had all been confirmed, that would be a much weaker result than mixed confirmation + falsification."
  ),
  caption("Table 7 — Stretch testcase pre-registered predictions vs observed outcomes.",
          " Source: configs/block3_testcase_manifest.yaml `stretch_testcase_predictions` block."),
  tablePredictions(),
  para(
    "**Two surprises were registered.** " +
    "(1) The pre-registered mode=none controller FAIL prediction (a-priori 0.80) was falsified: the stretch testcase " +
    "PASSED on comfort safety. This is mitigated by the +35% energy penalty, but it does refute the literal prediction. " +
    "(2) The pre-registered C_zon scale-dependent hypothesis B (a-priori 0.50) was falsified in favour of the " +
    "lower-probability uniform hypothesis A (a-priori 0.35). " +
    "**Two predictions were confirmed.** " +
    "(3) Full-recalibration surrogate RMSE improvement landed inside the pre-registered [50, 90]% range. " +
    "(4) C_zon hypothesis A range [1.7, 2.2]× contained the observed 1.909×.",
    { spaceBefore: 160 }
  ),
  para(
    "**Falsifiable physics**: both surprises shifted us toward hypotheses we had a-priori assigned lower probability. " +
    "This is the desired direction of scientific progress: pre-registered alternatives were genuinely competing, " +
    "and the evidence settled them without post-hoc rationalisation."
  ),

  // ════════════════════════ §10 Synthesis ════════════════════════
  divider(),
  h1("§10.  Synthesis and Block 4 implications"),

  h2("§10.1  What Block 3 establishes"),
  bullet(
    "**Surrogate-side transferability of v3.5 inverse calibration is supported on N=3** — Stage A/B/C produces " +
    "60–88% RMSE_T improvement on each new testcase, with consistent C_zon re-identification within a tight band."
  ),
  bullet(
    "**Hydronic-family uniform C_zon hypothesis is supported** (1.89–1.95× bestest_air, mean 1.92×, σ=0.032). " +
    "The C_zon does not scale with zone volume in the tested range."
  ),
  bullet(
    "**Controller-side frozen transfer is falsified on N=3** — residential hydronic fails comfort; commercial " +
    "stretch fails energy threshold (despite passing safety). Frozen-method transfer is not deployment-ready."
  ),
  bullet(
    "**Pre-registered claim boundary holds** — Block 3 deliberately did not claim universal building generalisation " +
    "or continual learning. The negative controller-side result is exactly the kind of result the manifest was " +
    "designed to surface honestly."
  ),

  h2("§10.2  Block 4 implications"),
  para(
    "The honest reading after Block 3 close points to four concrete future-work items, each falsifiable in its own right:"
  ),
  bullet(
    "**Controller fine-tuning on target testcase**: Block 3 deliberately froze controllers. Block 4 can ask whether " +
    "100k-step BOPTEST live-finetune (as in Block 2 MORL §1.7) recovers comfort on the residential hydronic cases."
  ),
  bullet(
    "**Hybrid-family-specific λ values**: the bestest_air-optimal λ_temp = 0.10 may not be optimal for the hydronic " +
    "actuator regime. A small λ sweep on the heat-pump testcase would parallel Block 2 §5 (HDRL sweep)."
  ),
  bullet(
    "**Extended N for C_zon uniformity**: N=3 hydronic suggests uniform C_zon × 1.92, but a wider sample (heat-pump " +
    "+ boiler-radiator + valve + radiant + VRF) would establish whether the uniformity is hydronic-family or HVAC-family-wide."
  ),
  bullet(
    "**Energy-aware reward augmentation for the stretch regime**: the commercial testcase's +35% energy penalty " +
    "suggests adding an energy term whose weight depends on the building scale, or a constraint-style energy " +
    "ceiling, would shift the threshold-pass into a deployment-ready pass."
  ),

  divider(),

  // Footer
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 160, after: 0 },
    children: [new TextRun({
      text: "Block 3 Complete Results — cross-checked 2026-05-28 against " +
            "configs/block3_testcase_manifest.yaml, " +
            "configs/block3_actuator_mapping_*.yaml, " +
            "reports/block3_transfer_matrix.csv, " +
            "reports/block3_*_transfer_summary.csv, " +
            "reports/block3_hydronic_family_n2_summary.csv, " +
            "outputs/block3_*/pi_baseline_15min_yearly/pi_yearly_summary.csv, " +
            "outputs/block3_*/thermostatic_hybrid_l010_adapter_none/, " +
            "and git log audit anchors 1861e48, 2f9d596, eb7091e, 46fbaa9, 645626e, 7ada793, cb7025f.",
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
            new TextRun({ text: "Block 3 Complete Results — Page ", font: "Arial", size: 16, color: "808080" }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: "808080" }),
          ],
        })],
      }),
    },
    children,
  }],
});

const OUT = "docs/block3_complete_results.docx";
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log(`[OK] ${OUT}  (${Math.round(buf.length / 1024)} KB)`);
}).catch((err) => {
  console.error("[ERR]", err);
  process.exit(1);
});
