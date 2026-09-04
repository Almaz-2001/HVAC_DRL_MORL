// Section 3 of the three-year iQUAT report, as a .docx to paste into the main
// document. Conventions follow the existing report: numbered headings, tables
// captioned "Таблица 3.x.y – ...", figures captioned "Рисунок N. ..." with the
// numbering continuing from 6, which is where section 2 ends.
//
// Every number quoted here is read from the committed CSVs in reports/ by
// collect.js below, not typed in, so the report traces to the same artifacts as
// the journal article.
//
// Build:  node docs/report/build_section3_docx.js

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  ImageRun,
} = require("docx");

const HERE = __dirname;
const ROOT = path.resolve(HERE, "..", "..");
const REP = path.join(ROOT, "reports");
const FIGS = path.join(HERE, "figures");

// ---------------------------------------------------------------- CSV loading
function loadCsv(name) {
  const raw = fs.readFileSync(path.join(REP, name), "utf8").replace(/^﻿/, "");
  const lines = raw.split(/\r?\n/).filter((l) => l.trim().length);
  const head = splitRow(lines[0]);
  return lines.slice(1).map((l) => {
    const cells = splitRow(l);
    return Object.fromEntries(head.map((h, i) => [h, cells[i] ?? ""]));
  });
}

// Several report CSVs carry quoted fields with embedded commas.
function splitRow(line) {
  const out = [];
  let cur = "";
  let q = false;
  for (const ch of line) {
    if (ch === '"') q = !q;
    else if (ch === "," && !q) { out.push(cur); cur = ""; }
    else cur += ch;
  }
  out.push(cur);
  return out.map((s) => s.trim());
}

const num = (v, d = 2) => (v === "" || v == null ? "—" : Number(v).toFixed(d));

// ------------------------------------------------------------------- building
const DXA = WidthType.DXA;
const FULL = 9360;               // usable width of an A4 page with 2 cm margins

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.after ?? 120, line: 276 },
    alignment: opts.align ?? AlignmentType.JUSTIFIED,
    indent: opts.indent ?? { firstLine: 567 },
    children: [new TextRun({ text, size: 24, font: "Times New Roman", ...opts.run })],
  });
}

function heading(text, level) {
  return new Paragraph({
    heading: level,
    spacing: { before: 280, after: 160 },
    children: [new TextRun({ text, bold: true, size: level === HeadingLevel.HEADING_1 ? 28 : 26,
                             font: "Times New Roman", color: "000000" })],
  });
}

function caption(text, opts = {}) {
  return new Paragraph({
    spacing: { before: opts.before ?? 60, after: opts.after ?? 160 },
    alignment: opts.align ?? AlignmentType.LEFT,
    indent: { firstLine: 0 },
    children: [new TextRun({ text, size: 22, font: "Times New Roman", italics: opts.italics })],
  });
}

function cell(text, { bold = false, shade = null, width, align } = {}) {
  return new TableCell({
    width: { size: width, type: DXA },
    shading: shade ? { type: ShadingType.CLEAR, color: "auto", fill: shade } : undefined,
    margins: { top: 60, bottom: 60, left: 90, right: 90 },
    children: [new Paragraph({
      alignment: align ?? AlignmentType.LEFT,
      indent: { firstLine: 0 },
      spacing: { after: 0 },
      children: [new TextRun({ text: String(text), bold, size: 20, font: "Times New Roman" })],
    })],
  });
}

function table(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const scaled = widths.map((w) => Math.round((w / total) * FULL));
  return new Table({
    width: { size: FULL, type: DXA },
    columnWidths: scaled,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((h, i) =>
          cell(h, { bold: true, shade: "EDF2F7", width: scaled[i], align: AlignmentType.CENTER })),
      }),
      ...rows.map((r) => new TableRow({
        children: r.map((v, i) =>
          cell(v, { width: scaled[i], align: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER })),
      })),
    ],
  });
}

function figure(file, widthPx, heightPx) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    indent: { firstLine: 0 },
    spacing: { before: 160, after: 40 },
    children: [new ImageRun({
      type: "png",
      data: fs.readFileSync(path.join(FIGS, file)),
      transformation: { width: widthPx, height: heightPx },
    })],
  });
}

// Keep the aspect ratio of the actual PNG rather than guessing it.
function figSize(file, targetWidth) {
  const buf = fs.readFileSync(path.join(FIGS, file));
  const w = buf.readUInt32BE(16);
  const h = buf.readUInt32BE(20);
  return [targetWidth, Math.round((h / w) * targetWidth)];
}

function fig(file, targetWidth = 560) {
  const [w, h] = figSize(file, targetWidth);
  return figure(file, w, h);
}

module.exports = { loadCsv, num, p, heading, caption, table, fig, HERE, FIGS };

if (require.main === module) {
  require("./section3_content.js");
}
