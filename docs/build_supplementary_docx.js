// Comprehensive supplementary material in Word format
//
// Contents:
//   S0   Cover + intro
//   S1   Block 1 supplementary figures (8 figures)
//   S2   Block 2 supplementary figures (10 figures)
//   S3   Block 3 supplementary figures (5 figures)
//   S4   Hou-Evins tables S4.1–S4.11 (Reporting Level-3 compliance)
//   S5   Pre-registration audit chain timeline (9 commits)
//   S6   Per-seed MORL detail tables
//
// Output: docs/supplementary_material.docx
//
// Run: node docs/build_supplementary_docx.js

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, Footer, AlignmentType, HeadingLevel, BorderStyle,
  WidthType, ShadingType, PageNumber, PageBreak, LevelFormat,
} = require("docx");

// ─────────────────────── Style ───────────────────────
const PAGE_WIDTH_DXA = 12240;  // US Letter
const PAGE_HEIGHT_DXA = 15840;
const MARGIN_DXA = 1080;       // 0.75"
const CONTENT_WIDTH = PAGE_WIDTH_DXA - 2 * MARGIN_DXA;

const C_HEAD = "1F3864";  // dark blue
const C_SUB = "2E75B6";
const C_NEUTRAL = "606060";
const C_RULE = "2E75B6";

const BORDER = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };
const CELL_MARGINS = { top: 60, bottom: 60, left: 100, right: 100 };
const HEAD_SHADE = { fill: "D5E8F0", type: ShadingType.CLEAR };

// ─────────────────────── Helpers ───────────────────────
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    pageBreakBefore: true,
    spacing: { before: 0, after: 200 },
    children: [new TextRun({ text, bold: true, font: "Arial", size: 32, color: C_HEAD })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 140 },
    children: [new TextRun({ text, bold: true, font: "Arial", size: 24, color: C_SUB })],
  });
}
function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 100 },
    children: [new TextRun({ text, bold: true, italic: true, font: "Arial", size: 20, color: "404040" })],
  });
}
function para(text, opts = {}) {
  const { size = 20, spaceBefore = 100, spaceAfter = 100, italic = false } = opts;
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { before: spaceBefore, after: spaceAfter },
    children: [new TextRun({ text, italic, font: "Arial", size })],
  });
}
function caption(label, text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 80, after: 240 },
    children: [
      new TextRun({ text: label + " ", bold: true, font: "Arial", size: 18 }),
      new TextRun({ text, italic: true, font: "Arial", size: 18 }),
    ],
  });
}
function divider() {
  return new Paragraph({
    spacing: { before: 200, after: 200 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C_RULE, space: 1 } },
    children: [],
  });
}

function imageBlock(imgPath, captionLabel, captionText, width = 5800000, height = 2800000) {
  const fullPath = path.resolve(imgPath);
  if (!fs.existsSync(fullPath)) {
    return [para(`[figure missing: ${imgPath}]`, { italic: true })];
  }
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 160, after: 80 },
      children: [new ImageRun({
        type: "png",
        data: fs.readFileSync(fullPath),
        transformation: { width: width / 9525, height: height / 9525 },
        altText: { title: captionLabel, description: captionText, name: path.basename(imgPath) },
      })],
    }),
    caption(captionLabel, captionText),
  ];
}

function tableCell(text, opts = {}) {
  const { bold = false, header = false, width = null, size = 18, align = AlignmentType.LEFT } = opts;
  return new TableCell({
    borders: BORDERS,
    margins: CELL_MARGINS,
    shading: header ? HEAD_SHADE : undefined,
    width: width ? { size: width, type: WidthType.DXA } : undefined,
    children: [new Paragraph({
      alignment: align,
      children: [new TextRun({ text, bold: bold || header, font: "Arial", size })],
    })],
  });
}

function buildTable(rows, colWidths) {
  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: rows.map((row, i) =>
      new TableRow({
        children: row.map((text, j) =>
          tableCell(text, {
            width: colWidths[j],
            header: i === 0,
            bold: i === 0 || j === 0,
            align: j === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
          })
        ),
      })
    ),
  });
}

// CSV reader (no dependencies)
function readCSV(filePath) {
  const text = fs.readFileSync(filePath, "utf-8");
  const lines = text.split(/\r?\n/).filter(l => l.trim().length > 0);
  return lines.map(line => {
    // Simple split — assumes no embedded commas in quoted strings
    return line.split(",").map(c => c.trim());
  });
}

function csvToTable(filePath, maxCols = null, decimals = 4) {
  const rows = readCSV(filePath);
  if (rows.length === 0) return null;
  // Truncate columns to keep table readable
  let truncated = rows;
  if (maxCols && rows[0].length > maxCols) {
    truncated = rows.map(r => r.slice(0, maxCols));
  }
  // Round numeric cells
  const data = truncated.map((row, i) => {
    if (i === 0) return row.map(c => c.replace(/_/g, " "));
    return row.map(c => {
      const n = parseFloat(c);
      if (!isNaN(n) && c.indexOf("e") === -1 && c.indexOf(".") !== -1) {
        return n.toFixed(decimals);
      }
      return c;
    });
  });
  // Compute equal column widths
  const ncols = data[0].length;
  const colWidth = Math.floor(CONTENT_WIDTH / ncols);
  const colWidths = Array(ncols).fill(colWidth);
  return buildTable(data, colWidths);
}

// ─────────────────────── Content ───────────────────────
const children = [];

// ═══════════════════════ S0 Cover ═══════════════════════
children.push(
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 1200, after: 240 },
    children: [new TextRun({ text: "Supplementary Material", bold: true, font: "Arial", size: 48, color: C_HEAD })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 480 },
    children: [new TextRun({
      text: "Deep Reinforcement Learning for Energy-Efficient Consumption Management in Smart Buildings: " +
            "A Calibrated Physical Twin as Soft Regularizer for HVAC Control",
      italic: true, font: "Arial", size: 24, color: C_SUB,
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 360 },
    children: [new TextRun({ text: "Almaz Sapargali", font: "Arial", size: 22 })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 480 },
    children: [new TextRun({
      text: "Target journal: Results in Engineering (Elsevier, Q1)",
      italic: true, font: "Arial", size: 20, color: C_NEUTRAL,
    })],
  }),
  divider(),
  para(
    "This supplementary document accompanies the main manuscript and contains six categories of " +
    "additional material that did not fit within the main paper page budget: " +
    "(S1) Block 1 supplementary figures covering surrogate fidelity diagnostics; " +
    "(S2) Block 2 supplementary figures covering controller-side validation traces, " +
    "MORL seed variance, and HDRL tracking detail; " +
    "(S3) Block 3 supplementary figures covering pre-registration protocol schematics and " +
    "hypothesis closure tables; " +
    "(S4) the eleven Hou-and-Evins Reporting-Level-3 numerical-justification tables (S4.1–S4.11); " +
    "(S5) the full pre-registration audit chain with verbatim git commit messages; " +
    "(S6) per-seed MORL yearly metrics for the N=5 falsification test. " +
    "All numerical values trace to CSV/JSON artifacts under reports/ and outputs/ in the project " +
    "GitHub repository (https://github.com/Almaz-2001/HVAC_DRL_MORL.git).",
    { size: 20 }
  ),
);

// ═══════════════════════ S1 Block 1 figures ═══════════════════════
children.push(h1("S1.  Block 1 supplementary figures"));
children.push(para(
  "These figures support the surrogate-fidelity analysis in Section 5 of the main paper. They include " +
  "architecture diagrams (S1.1, S1.2), the Stage B C_zon inverse-identification trajectory (S1.3), " +
  "per-episode rollout RMSE distributions (S1.4–S1.5), runtime benchmarks (S1.6), action-saturation " +
  "diagnostics (S1.7), and a positioning map relative to related surrogate-modelling work (S1.8)."
));

const S1_FIGS = [
  ["reports/figures/article_real/block1_q1_fig02_v3_dual_head.png",          "Figure S1.1.",
   " v3 dual-head architecture (temperature + power heads; 8,482 total parameters; 7,105 temp head, 1,377 power head)."],
  ["reports/figures/article_real/block1_q1_fig04_czon_identification.png",   "Figure S1.2.",
   " Stage B C_zon inverse identification trajectory. The 120-epoch solve converges from the 4.200×10⁵ J/K prior to the identified 4.413×10⁵ J/K (+5.06%)."],
  ["reports/figures/article_real/block1_q1_fig09_backend_speed.png",         "Figure S1.3.",
   " Backend speed benchmark across surrogate variants. The hybrid backend sustains 1,786.8 environment steps/s on a single CPU thread (85.0× the live BOPTEST RTE)."],
  ["reports/figures/article_real/block1_q1_fig12_per_episode_rmse.png",      "Figure S1.4.",
   " Per-episode rollout RMSE distributions for v3, raw v3.5, calibrated v3.5, and corpus-matched v3."],
  ["reports/figures/article_real/block1_q1_fig13_residual_distributions.png","Figure S1.5.",
   " Temperature residual distributions across the four surrogate variants."],
  ["reports/figures/article_real/block1_stage_abc_calibration_diagnostics.png","Figure S1.6.",
   " Stage A/B/C calibration diagnostics, including telemetry-preprocessing artefacts and per-stage RMSE deltas."],
  ["reports/figures/article_real/block1_q1_fig11_action_saturation.png",     "Figure S1.7.",
   " Action-saturation diagnostic. Direct v3.5 PPO drives the actuator into saturation early; hybrid_l010 holds policy fidelity through step 16 on the typical winter window."],
  ["reports/figures/article_real/block1_q1_fig15_literature_positioning.png","Figure S1.8.",
   " Literature positioning map. Our work occupies the (low predictive fidelity + high RL utility) quadrant via deliberate role separation; existing physics-constrained surrogate work targets the (high fidelity + unknown RL utility) corner."],
];
for (const [p, l, t] of S1_FIGS) children.push(...imageBlock(p, l, t));

// ═══════════════════════ S2 Block 2 figures ═══════════════════════
children.push(h1("S2.  Block 2 supplementary figures"));
children.push(para(
  "These figures support the controller-side analysis in Section 6. They include conceptual pipeline " +
  "schematics (S2.1, S2.2), live BOPTEST traces (S2.3–S2.6), MORL observation-interface ablation " +
  "(S2.7–S2.9), hybrid-disagreement bounds (S2.10), HDRL tracking detail (S2.11), and three-panel " +
  "hybrid-vs-PI comparison (S2.12)."
));

const S2_FIGS = [
  ["reports/figures/article_real/main_block23/fig_block2_pipeline.png",       "Figure S2.1.",
   " Block 2 controller-side validation pipeline: three surrogate backends feed five training stacks; all controller KPIs measured on live BOPTEST RTE."],
  ["reports/figures/article_real/main_block23/fig_block2_reward_shaping.png", "Figure S2.2.",
   " Hybrid backend reward-shaping mechanism. v3 supplies rollout dynamics; v3.5 contributes per-step disagreement penalties subtracted from the comfort+energy reward."],
  ["reports/figures/hybrid_boptest_comfort_traces.png",                       "Figure S2.3.",
   " Hybrid_l010 live BOPTEST comfort traces on peak and typical winter windows. The hybrid policy stays close to the 21–24 °C comfort band."],
  ["reports/figures/hybrid_boptest_power_energy_traces.png",                  "Figure S2.4.",
   " Hybrid_l010 power and cumulative-energy traces. Energy advantage over pure v3 is comparable; the hybrid achieves better comfort at no energy cost."],
  ["reports/figures/article_real/block2_warmstart_negative_eval_kpis.png",    "Figure S2.5.",
   " Direct v3.5 warm-start negative control. Pre-training from v3.5 hurts subsequent hybrid training compared to scratch initialisation."],
  ["reports/figures/article_real/block2_morl_5d_vs_17d_radar.png",            "Figure S2.6.",
   " MORL 5D vs 17D observation-interface ablation. The 5D path collapses (m_s = 1.046); the 17D path recovers a usable MORL policy (m_s = 0.099)."],
  ["reports/figures/article_real/block2_morl_17d_seasonal_heatmap.png",       "Figure S2.7.",
   " MORL 17D monthly seasonal performance heatmap. Performance varies across the calendar year but stays within the pre-registered safety band."],
  ["reports/figures/article_real/block2_morl_seasonal_variance_inversion.png","Figure S2.8.",
   " MORL seasonal seed-variance heatmap after the N=5 falsification test. The original N=3 seasonal-inversion mechanism does not survive."],
  ["reports/figures/hybrid_disagreement_summary.png",                         "Figure S2.9.",
   " Hybrid disagreement bounds: mean v3–v3.5 temperature disagreement 0.969 °C (p95 2.516 °C); mean power 708.4 W (p95 1,236 W). Bounded rather than chaotic divergence."],
  ["reports/figures/article_real/block2_hdrl_l000_winter_tracking.png",       "Figure S2.10.",
   " HDRL l000 representative winter trace. The hierarchical winter specialist tracks the lower edge of the comfort band closely with low energy expenditure."],
  ["reports/figures/hybrid_transfer_gap_comparison.png",                      "Figure S2.11.",
   " Surrogate-to-live transfer-gap comparison across pure v3, hybrid_l010, and direct v3.5. The hybrid narrows the surrogate→live ms_gap from |gap| ≈ 0.9–1.0 to ≈ 0.02."],
  ["reports/figures/hybrid_vs_pi_ms.png",                                     "Figure S2.12a.",
   " Hybrid_l010 vs PI baseline — m_s comparison."],
  ["reports/figures/hybrid_vs_pi_violation.png",                              "Figure S2.12b.",
   " Hybrid_l010 vs PI baseline — setpoint violation percentage comparison."],
  ["reports/figures/hybrid_vs_pi_energy.png",                                 "Figure S2.12c.",
   " Hybrid_l010 vs PI baseline — energy consumption comparison."],
];
for (const [p, l, t] of S2_FIGS) children.push(...imageBlock(p, l, t));

// ═══════════════════════ S3 Block 3 figures ═══════════════════════
children.push(h1("S3.  Block 3 supplementary figures"));
children.push(para(
  "These figures support the transferability analysis in Section 7. They include the pre-registered " +
  "protocol schematic (S3.1), the testcase difficulty ladder (S3.2), the controller transfer verdict " +
  "heatmap (S3.3), the full Stage A/B/C gain bar chart (S3.4), and the pre-registered predictions " +
  "vs observed outcomes table (S3.5)."
));

const S3_FIGS = [
  ["reports/figures/article_real/main_block23/fig_block3_protocol.png",            "Figure S3.1.",
   " Pre-registered Block 3 transferability protocol with the 9-commit audit chain timeline. Bit-identical pre-registration block verifiable via `git diff 1861e48..7ada793`."],
  ["reports/figures/article_real/main_block23/fig_block3_testcase_ladder.png",     "Figure S3.2.",
   " Block 3 testcase difficulty ladder: source (bestest_air) → primary (bestest_hydronic_heat_pump) → secondary (bestest_hydronic) → stretch (singlezone_commercial_hydronic), each with its pre-registered actuator adapter."],
  ["reports/figures/article_real/main_block23/fig_block3_rl_vs_pi.png",            "Figure S3.3.",
   " Frozen-controller transfer: m_s_RL vs 1.25× PI threshold and energy delta versus PI. Residential cases save energy but fail comfort; commercial passes safety but at +35.3% energy."],
  ["reports/figures/article_real/main_block23/fig_block3_stage_abc_gain.png",      "Figure S3.4.",
   " Full Stage A/B/C surrogate recalibration improves RMSE_T by 60.2 / 87.4 / 87.8 % on the three hydronic testcases; power-head MAE improvements are large on residential cases and marginal on commercial."],
  ["reports/figures/article_real/main_block23/fig_block3_hypothesis_closure.png",  "Figure S3.5.",
   " Pre-registered predictions vs observed outcomes (stretch testcase). Two predictions FALSIFIED (controller verdict; scale-dependent C_zon B); three CONFIRMED (RMSE gain; uniform C_zon A; pipeline convergence)."],
];
for (const [p, l, t] of S3_FIGS) children.push(...imageBlock(p, l, t));

// ═══════════════════════ S4 Hou-Evins tables ═══════════════════════
children.push(h1("S4.  Hou-and-Evins Reporting-Level-3 numerical-justification tables"));
children.push(para(
  "Eleven tables (S4.1–S4.11) cover the Hou-and-Evins Section-5 reporting requirements: sample-generation " +
  "provenance, sample-size justification, Stage A telemetry preprocessing, feature significance, input " +
  "independence, split representativeness, channel scaling, training hyperparameters, architecture " +
  "justification, targeted sensitivity, and replicative/predictive validity. Each table is reproduced " +
  "verbatim from the corresponding CSV under paper/supplementary/. Per the compliance review, fifteen " +
  "of the seventeen Hou-and-Evins Level-3 items are covered; the two not covered are physical " +
  "co-simulation across independent Modelica engines and grid-tied multi-agent coordination, both " +
  "out of scope for the single-zone testbed used here."
));

const HE_TABLES = [
  ["paper/supplementary/hou_evins_sample_generation_table.csv",            "Table S4.1.",
   " Sample-generation provenance — origin, parameter ranges, and physical justification of each transition corpus.", 6],
  ["paper/supplementary/hou_evins_sample_size_justification_table.csv",    "Table S4.2.",
   " Sample-size justification — numerical evidence for the chosen corpus sizes including learning-curve checks.", 5],
  ["paper/supplementary/hou_evins_stage_a_processing_table.csv",           "Table S4.3.",
   " Stage A telemetry preprocessing — latency compensation, bias removal, normalisation, denoise, causal delta.", 5],
  ["paper/supplementary/hou_evins_feature_justification_table.csv",        "Table S4.4.",
   " Feature significance — per-feature retention rationale with quantitative selection criteria.", 5],
  ["paper/supplementary/hou_evins_input_independence_table.csv",           "Table S4.5.",
   " Input independence — Pearson and mutual-information independence checks across input channels.", 5],
  ["paper/supplementary/hou_evins_split_representativeness_table.csv",     "Table S4.6.",
   " Train/validation/test split representativeness — distributional checks between corpus partitions.", 5],
  ["paper/supplementary/hou_evins_scaling_table.csv",                      "Table S4.7.",
   " Per-channel scaling and reverse-scaling logic — standardisation parameters reused at inference time.", 5],
  ["paper/supplementary/hou_evins_training_hyperparams_table.csv",         "Table S4.8.",
   " Training hyperparameters — optimiser, learning rate, batch size, regularisation, and stopping criteria.", 5],
  ["paper/supplementary/hou_evins_architecture_justification_table.csv",   "Table S4.9.",
   " Architecture justification — layer widths, depths, activations, and ablation evidence.", 5],
  ["paper/supplementary/hou_evins_targeted_sensitivity_table.csv",         "Table S4.10.",
   " Targeted sensitivity analysis — per-hyperparameter sweep results including the λ_temp scan.", 5],
  ["paper/supplementary/hou_evins_predictive_validity_table.csv",          "Table S4.11.",
   " Replicative and predictive validity — one-step and multi-horizon rollout RMSE across all variants including the v3_15min_matched and raw_v35 reviewer-mitigation rows.", 7],
];

for (const [csvPath, label, text, maxCols] of HE_TABLES) {
  children.push(h3(label.replace(/\.$/, "")));
  children.push(para(text, { size: 18, italic: true, spaceBefore: 60, spaceAfter: 120 }));
  const tbl = csvToTable(csvPath, maxCols);
  if (tbl) {
    children.push(tbl);
  } else {
    children.push(para(`[table missing: ${csvPath}]`, { italic: true }));
  }
  children.push(new Paragraph({ spacing: { before: 0, after: 240 }, children: [] }));
}

// ═══════════════════════ S5 Audit chain timeline ═══════════════════════
children.push(h1("S5.  Pre-registration audit chain (verbatim git commit messages)"));
children.push(para(
  "The Block 2 and Block 3 results in the main manuscript rely on a nine-commit pre-registration chain. " +
  "Each commit SHA below is verifiable via `git log -1 <SHA>` against the project repository " +
  "(https://github.com/Almaz-2001/HVAC_DRL_MORL.git). Reviewers can confirm the bit-identical " +
  "pre-registration block by diffing 1861e48..7ada793 against the manifest body in " +
  "configs/block3_testcase_manifest.yaml. The three falsified pre-registered predictions are the " +
  "single-λ controller-family hypothesis (RQ2/H2), the stretch-testcase controller-FAIL prediction " +
  "(a-priori probability 0.80), and the scale-dependent C_zon hypothesis B (a-priori 0.50)."
));

const AUDIT = [
  ["93df9b3", "MORL pre-registration", "pre-registration: seed45/46 falsification predictions for practical canonical"],
  ["62dc859", "MORL post-N=5 result",  "post-N5 result: action-saturation hypothesis falsified"],
  ["1861e48", "Block 3 manifest",      "Block 3 pre-registration: transferability testcase manifest"],
  ["2f9d596", "Block 3 audit-pre",     "Block 3 audit: record pre-registration commit SHA"],
  ["eb7091e", "Hydronic adapter",      "Block 3 pre-registration: hydronic heat-pump actuator adapter"],
  ["46fbaa9", "Secondary adapter",     "Block 3 pre-registration: bestest_hydronic direct supply adapter"],
  ["645626e", "Stretch predictions",   "Block 3 pre-registration: stretch testcase predictions and commercial hydronic adapter"],
  ["7ada793", "Block 3 close",         "Block 3 audit: record close commit SHA"],
  ["cb7025f", "Block 3 interpretation","Block 3 interpretation: component-level transferability and threshold-pass caveat"],
];
const audit_rows = [["SHA", "Role", "Verbatim commit message"]];
for (const a of AUDIT) audit_rows.push(a);
children.push(buildTable(audit_rows, [1280, 2080, 6000]));

// ═══════════════════════ S6 Per-seed MORL detail ═══════════════════════
children.push(h1("S6.  Per-seed MORL yearly metrics (N=5 falsification result)"));
children.push(para(
  "Table S6.1 reports the full per-seed yearly evaluation for the two pre-registered MORL canonical " +
  "weight pairs (50/50 neutral and 75/25 practical). The N=5 sample for each weight pair was " +
  "pre-registered at audit anchor 93df9b3 before seeds 45 and 46 were trained; the falsification result " +
  "is documented at audit anchor 62dc859. The high coefficient of variation (CV ≈ 0.42–0.61) is the " +
  "core empirical evidence that the MORL canonical is promising but not deployment-stable at N=5 without " +
  "explicit policy stabilisation (validation-based checkpoint selection or seed ensembling). Source: " +
  "reports/morl_canonical_seedfix_yearly_per_seed.csv."
));

const morl_data = readCSV("reports/morl_canonical_seedfix_yearly_per_seed.csv");
// Keep first 7 columns: canonical, seed, rmse_mean, mae_mean, within_1c_pct_mean, within_05c_pct_mean, violation_pct_mean, energy_kwh_sum, ms_mean
const morl_header = ["weight pair", "seed", "RMSE_T mean", "MAE_T mean", "Within 1°C %", "Violation %", "Energy kWh", "m_s mean"];
const morl_rows = [morl_header];
for (let i = 1; i < morl_data.length; i++) {
  const r = morl_data[i];
  morl_rows.push([
    r[0].replace(/comfort_/g, "").replace(/_energy_/, "/"),
    r[1],
    parseFloat(r[2]).toFixed(3),
    parseFloat(r[3]).toFixed(3),
    parseFloat(r[4]).toFixed(2),
    parseFloat(r[6]).toFixed(2),
    parseFloat(r[7]).toFixed(1),
    parseFloat(r[8]).toFixed(3),
  ]);
}
children.push(h3("Table S6.1"));
children.push(para(" Per-seed yearly MORL metrics across the two pre-registered canonical weight pairs.", { italic: true, size: 18 }));
children.push(buildTable(morl_rows, [1600, 800, 1200, 1200, 1200, 1200, 1200, 960]));

// Aggregate stats
children.push(new Paragraph({ spacing: { before: 240 }, children: [] }));
children.push(h3("Table S6.2 — N=5 aggregate statistics"));
children.push(para(" Summary across the per-seed values in Table S6.1.", { italic: true, size: 18 }));
const agg = [
  ["Weight pair", "RMSE_T mean ± std", "Violation % mean ± std", "m_s mean ± std", "m_s CV", "m_s min", "m_s max"],
  ["50/50 neutral",  "0.893 ± 0.081", "13.01 ± 6.62", "0.187 ± 0.078", "0.418", "0.103", "0.310"],
  ["75/25 practical","0.799 ± 0.100", " 9.23 ± 6.67", "0.139 ± 0.085", "0.613", "0.057", "0.276"],
];
children.push(buildTable(agg, [1600, 1800, 1700, 1700, 800, 800, 960]));

// ═══════════════════════ Final footer ═══════════════════════
children.push(divider());
children.push(para(
  "End of Supplementary Material. For raw data files, training scripts, and full reproducibility " +
  "instructions, see the project repository at https://github.com/Almaz-2001/HVAC_DRL_MORL.git.",
  { italic: true, size: 18 }
));

// ─────────────────────── Document assembly ───────────────────────
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 20 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: C_HEAD },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: C_SUB },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 20, bold: true, italic: true, font: "Arial", color: "404040" },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 } },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: PAGE_WIDTH_DXA, height: PAGE_HEIGHT_DXA },
        margin: { top: MARGIN_DXA, right: MARGIN_DXA, bottom: MARGIN_DXA, left: MARGIN_DXA },
      },
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "Supplementary Material — Page ", font: "Arial", size: 16, color: C_NEUTRAL }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: C_NEUTRAL }),
          ],
        })],
      }),
    },
    children,
  }],
});

const OUT = "docs/supplementary_material.docx";
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  const kb = Math.round(buf.length / 1024);
  console.log(`[OK] ${OUT}  (${kb.toLocaleString()} KB)`);
}).catch((err) => {
  console.error("[ERR]", err);
  process.exit(1);
});
