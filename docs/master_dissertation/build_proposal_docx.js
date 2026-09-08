// NPU Graduate Degree Dissertation Title Selection Report, filled in for the
// surrogate-selection topic. Follows the structure of the supplied template
// (which ships a worked example by another student): header table, dissertation
// type table, then the numbered body the form requires at no less than 3500
// words, then references.
//
// Every quantitative claim is read from the committed CSVs in reports/ rather
// than typed in, so the proposal agrees with the article and the report by
// construction.
//
// Build:  NODE_PATH=../current_tasks/node_modules node build_proposal_docx.js

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, PageBreak,
} = require("docx");

const HERE = __dirname;
const ROOT = path.resolve(HERE, "..", "..");
const REP = path.join(ROOT, "reports");

// ------------------------------------------------------------- data plumbing
function splitRow(line) {
  const out = [];
  let cur = "", q = false;
  for (const ch of line) {
    if (ch === '"') q = !q;
    else if (ch === "," && !q) { out.push(cur); cur = ""; }
    else cur += ch;
  }
  out.push(cur);
  return out.map((s) => s.trim());
}

function loadCsv(name) {
  const raw = fs.readFileSync(path.join(REP, name), "utf8").replace(/^﻿/, "");
  const lines = raw.split(/\r?\n/).filter((l) => l.trim().length);
  const head = splitRow(lines[0]);
  return lines.slice(1).map((l) => {
    const c = splitRow(l);
    return Object.fromEntries(head.map((h, i) => [h, c[i] ?? ""]));
  });
}

const f = (v, d = 2) => Number(v).toFixed(d);

const scatter = loadCsv("block2_fidelity_utility_scatter.csv");
const rough = loadCsv("block2_mechanism_surface_sharpness.csv");
const speed = loadCsv("speed_benchmark_table.csv");
const transfer = loadCsv("block3_transfer_matrix.csv");
const morl = loadCsv("block2_morl_comparison_summary.csv");
const hdrl = loadCsv("block2_hdrl_lambda_sweep_seed_band.csv");
const band = loadCsv("block2_thermostatic_seed_band.csv");
const refs = JSON.parse(fs.readFileSync(path.join(HERE, "refs.json"), "utf8"));

const S = (name) => scatter.find((r) => r.controller === name);
const bbH = S("v3 (hourly)");
const bbM = S("matched v3 (15-min)");
const gb = S("v3.5 (calibrated)");
const hyb = scatter.find((r) => r.controller.startsWith("hybrid"));
const spd = (b) => speed.find((r) => r.backend === b);
const m5 = morl.find((r) => r.variant === "MORL_5D_basic");
const m17 = morl.find((r) => r.variant === "MORL_17D_power_only");

// ------------------------------------------------------------ docx utilities
const DXA = WidthType.DXA;
const FULL = 9300;

function txt(text, o = {}) {
  return new TextRun({ text, font: "Times New Roman", size: o.size ?? 22,
                       bold: o.bold, italics: o.italics, color: o.color });
}

function p(text, o = {}) {
  return new Paragraph({
    spacing: { after: o.after ?? 120, line: 276 },
    alignment: o.align ?? AlignmentType.JUSTIFIED,
    indent: o.indent ?? { firstLine: 425 },
    children: [txt(text, o)],
  });
}

function h(text, level) {
  return new Paragraph({
    spacing: { before: level === 1 ? 300 : 220, after: 140 },
    alignment: AlignmentType.LEFT,
    indent: { firstLine: 0 },
    children: [txt(text, { bold: true, size: level === 1 ? 26 : 23 })],
  });
}

function cell(children, o = {}) {
  return new TableCell({
    width: { size: o.width, type: DXA },
    columnSpan: o.span,
    shading: o.shade ? { type: ShadingType.CLEAR, color: "auto", fill: o.shade } : undefined,
    margins: { top: 70, bottom: 70, left: 100, right: 100 },
    verticalAlign: "center",
    children: (Array.isArray(children) ? children : [children]).map((c) =>
      typeof c === "string"
        ? new Paragraph({
            alignment: o.align ?? AlignmentType.LEFT,
            indent: { firstLine: 0 }, spacing: { after: 0 },
            children: [txt(c, { bold: o.bold, size: o.size ?? 21 })],
          })
        : c),
  });
}

// A blank the student must fill in. Made visible on purpose: this is a form,
// and an unfilled field has to be obvious rather than quietly plausible.
const BLANK = "__________________";

module.exports = { loadCsv, f, p, h, cell, txt, FULL, DXA, HERE, BLANK,
                   scatter, rough, speed, transfer, morl, hdrl, band, refs,
                   bbH, bbM, gb, hyb, spd, m5, m17 };

if (require.main === module) require("./proposal_content.js");
