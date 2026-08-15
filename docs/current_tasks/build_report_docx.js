/*
 * Funder-facing progress report for work packages 10 and 11, as .docx.
 *
 * Audience note: the readers are the grant awarding body, not HVAC or machine
 * learning specialists. So every technical term is defined at first use, results
 * are given in units a non-specialist can judge (percent of time uncomfortable,
 * hours of computing, degrees of error), and each chart states its conclusion on
 * the chart itself. The separate LaTeX report in this folder is the technical
 * version and keeps the domain vocabulary.
 *
 * Two families of figure are used. Charts named fig*.png are drawn specifically
 * for this report by make_report_figures*.py. Diagrams named paper_*.png are the
 * architecture and test-case schematics from the submitted manuscript, rendered
 * from docs/paper_asej/figures; they carry technical notation, so every one of
 * them is preceded by a paragraph that says how to read it.
 *
 * Run:  node docs/current_tasks/build_report_docx.js
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  ImageRun, PageBreak, LevelFormat, convertInchesToTwip,
  Header, Footer, PageNumber,
} = require("docx");

const HERE = __dirname;
const FIG = path.join(HERE, "report_figures");
const CONTENT_W = 9360;                 // A4 minus 1" margins, in DXA

const INK = "1a1a1a", MUTED = "555f66", GOOD = "2e7d5b", BAD = "b4442e",
      WARN = "a8741a", RULE = "c9d1d4", BRAND = "1e4a5f";

const p = (text, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 140, line: 276 },
  alignment: o.align,
  children: [new TextRun({ text, bold: o.bold, italics: o.italics, size: o.size ?? 21,
                           color: o.color ?? INK })],
});

const runs = (parts, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 140, line: 276 },
  alignment: o.align,
  children: parts.map(x => typeof x === "string"
    ? new TextRun({ text: x, size: o.size ?? 21, color: INK })
    : new TextRun({ text: x.t, bold: x.b, italics: x.i, size: o.size ?? 21, color: x.c ?? INK })),
});

const h1 = t => new Paragraph({ text: t, heading: HeadingLevel.HEADING_1,
                                spacing: { before: 340, after: 160 } });
const h2 = t => new Paragraph({ text: t, heading: HeadingLevel.HEADING_2,
                                spacing: { before: 260, after: 120 } });
const h3 = t => new Paragraph({ text: t, heading: HeadingLevel.HEADING_3,
                                spacing: { before: 200, after: 100 } });

const bullet = (t, o = {}) => new Paragraph({
  numbering: { reference: "dots", level: 0 },
  spacing: { after: 90, line: 276 },
  children: typeof t === "string"
    ? [new TextRun({ text: t, size: 21, color: INK })]
    : t.map(x => typeof x === "string"
        ? new TextRun({ text: x, size: 21, color: INK })
        : new TextRun({ text: x.t, bold: x.b, italics: x.i, size: 21, color: x.c ?? INK })),
});

// `instance` restarts the count: without it every numbered list in the document
// continues the previous one, so Section 7 opened at "7."
const num = (t, instance = 0) => new Paragraph({
  numbering: { reference: "steps", level: 0, instance },
  spacing: { after: 90, line: 276 },
  children: typeof t === "string"
    ? [new TextRun({ text: t, size: 21, color: INK })]
    : t.map(x => typeof x === "string"
        ? new TextRun({ text: x, size: 21, color: INK })
        : new TextRun({ text: x.t, bold: x.b, italics: x.i, size: 21, color: x.c ?? INK })),
});

const pageBreak = () => new Paragraph({ children: [new PageBreak()] });

// --- figures -----------------------------------------------------------------
// The aspect ratio is read from the PNG header rather than hard-coded, because
// matplotlib's bbox_inches="tight" makes the saved size differ from the figsize.
function pngSize(buf) {
  return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
}

let figNo = 0;
function figure(file, caption, opts = {}) {
  const img = fs.readFileSync(path.join(FIG, file));
  const { w: pw, h: ph } = pngSize(img);
  const w = opts.width ?? 600;
  figNo += 1;
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { before: 180, after: 60 },
      keepNext: true,
      children: [new ImageRun({ type: "png", data: img,
                                transformation: { width: w, height: Math.round(w * ph / pw) } })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 240 },
      children: [
        new TextRun({ text: `Figure ${figNo}. `, size: 18, bold: true, color: MUTED }),
        new TextRun({ text: caption, size: 18, italics: true, color: MUTED }),
      ],
    }),
  ];
}

// A note that a diagram is reproduced from the scientific manuscript, plus a
// plain-language reading key. Placed immediately before the figure.
const readingKey = text => new Paragraph({
  spacing: { before: 60, after: 60, line: 260 },
  indent: { left: 240, right: 240 },
  border: { left: { style: BorderStyle.SINGLE, size: 12, color: "9fb4bd", space: 10 } },
  keepNext: true,
  children: [
    new TextRun({ text: "How to read it. ", size: 19, bold: true, color: BRAND }),
    new TextRun({ text, size: 19, color: MUTED }),
  ],
});

// --- tables ------------------------------------------------------------------
function table(headers, rows, widths, opts = {}) {
  const cell = (text, o = {}) => new TableCell({
    width: { size: o.w, type: WidthType.DXA },
    shading: o.head ? { type: ShadingType.CLEAR, fill: "eef2f3" }
                    : (o.fill ? { type: ShadingType.CLEAR, fill: o.fill } : undefined),
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({
      spacing: { after: 0, line: 260 },
      alignment: o.align,
      children: [new TextRun({ text, bold: o.head || o.bold, italics: o.i, size: o.size ?? 19,
                               color: o.color ?? INK })],
    })],
  });
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: widths,
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: RULE },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE },
      left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: RULE },
      insideVertical: { style: BorderStyle.NONE },
    },
    rows: [
      new TableRow({ tableHeader: true,
        children: headers.map((t, i) => cell(t, { head: true, w: widths[i],
                                                  align: opts.alignHead?.[i] })) }),
      ...rows.map(r => new TableRow({
        children: r.map((c, i) => typeof c === "string"
          ? cell(c, { w: widths[i], align: opts.align?.[i] })
          : cell(c.t, { w: widths[i], bold: c.b, italics: c.i, color: c.c, fill: c.fill,
                        align: c.align ?? opts.align?.[i] })),
      })),
    ],
  });
}

let tabNo = 0;
const tableCaption = text => {
  tabNo += 1;
  return new Paragraph({
    spacing: { before: 160, after: 80 }, keepNext: true,
    children: [
      new TextRun({ text: `Table ${tabNo}. `, size: 18, bold: true, color: MUTED }),
      new TextRun({ text, size: 18, italics: true, color: MUTED }),
    ],
  });
};

const source = text => new Paragraph({
  spacing: { before: 60, after: 200 },
  children: [new TextRun({ text: "Source: " + text, size: 16, italics: true, color: MUTED })],
});

// A shaded callout box for the things a busy reader must not miss.
function callout(title, lines, colour = BRAND) {
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [CONTENT_W],
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: colour },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: colour },
      left: { style: BorderStyle.SINGLE, size: 18, color: colour },
      right: { style: BorderStyle.SINGLE, size: 4, color: colour },
      insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE },
    },
    rows: [new TableRow({
      children: [new TableCell({
        width: { size: CONTENT_W, type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, fill: "f4f7f8" },
        margins: { top: 160, bottom: 160, left: 200, right: 200 },
        children: [
          new Paragraph({ spacing: { after: 100 },
            children: [new TextRun({ text: title, bold: true, size: 22, color: colour })] }),
          ...lines.map((l, i) => new Paragraph({
            spacing: { after: i === lines.length - 1 ? 0 : 90, line: 270 },
            children: typeof l === "string"
              ? [new TextRun({ text: l, size: 20, color: INK })]
              : l.map(x => typeof x === "string"
                  ? new TextRun({ text: x, size: 20, color: INK })
                  : new TextRun({ text: x.t, bold: x.b, italics: x.i, size: 20, color: x.c ?? INK })),
          })),
        ],
      })],
    })],
  });
}

// =============================================================================
const doc = new Document({
  numbering: {
    config: [
      { reference: "dots",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
                   alignment: AlignmentType.LEFT,
                   style: { paragraph: { indent: { left: 360, hanging: 220 } } } }] },
      { reference: "steps",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.",
                   alignment: AlignmentType.LEFT,
                   style: { paragraph: { indent: { left: 400, hanging: 260 } } } }] },
    ],
  },
  styles: {
    default: { document: { run: { font: "Calibri", size: 21, color: INK } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Calibri", size: 30, bold: true, color: BRAND } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Calibri", size: 24, bold: true, color: "2f6f8f" } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Calibri", size: 21, bold: true, color: "3f5a66" } },
    ],
  },
  sections: [{
    properties: { page: { margin: { top: convertInchesToTwip(1), bottom: convertInchesToTwip(0.9),
                                    left: convertInchesToTwip(1), right: convertInchesToTwip(1) } } },
    headers: {
      default: new Header({ children: [new Paragraph({
        alignment: AlignmentType.RIGHT,
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE, space: 6 } },
        children: [new TextRun({ text: "Progress report – work packages 10 and 11",
                                 size: 16, color: MUTED })] })] }),
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ children: ["Page ", PageNumber.CURRENT, " of ",
                                            PageNumber.TOTAL_PAGES], size: 16, color: MUTED })] })] }),
    },
    children: [
      // ======================================================== title block ==
      new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { before: 200, after: 100 },
        children: [new TextRun({ text: "Progress Report for the Funding Body",
                                 bold: true, size: 38, color: BRAND })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { after: 200 },
        children: [new TextRun({
          text: "Data-driven results for work packages 10 and 11",
          size: 26, color: "2f6f8f" })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { after: 60 },
        children: [new TextRun({
          text: "Work Package 10   —   Digital twins for each building, and integration with edge computing",
          size: 21, color: MUTED })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { after: 220 },
        children: [new TextRun({
          text: "Work Package 11   —   Feedback control with continuous learning for self-optimizing buildings",
          size: 21, color: MUTED })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { after: 300 },
        border: { top: { style: BorderStyle.SINGLE, size: 6, color: RULE, space: 10 },
                  bottom: { style: BorderStyle.SINGLE, size: 6, color: RULE, space: 10 } },
        children: [new TextRun({
          text: "Reporting period: January – December 2026          Prepared: 12 August 2026",
          size: 19, color: MUTED })],
      }),

      callout("What this report says, in five sentences", [
        ["Buildings spend most of their energy on heating and cooling, and better control software " +
         "can cut that bill without any building work. Such software has to learn its job by trial " +
         "and error, so it practises on a ", { t: "digital twin", b: true },
         " — a fast software copy of the building."],
        ["This year the project found that the property everyone in the field optimises when " +
         "building such a copy — how accurately it predicts the building — ",
         { t: "does not predict whether the copy is any good for training a controller", b: true },
         ". We measured this, explained why it happens, and designed an architecture that works " +
         "around it."],
        ["The resulting controller keeps the building outside its comfort range 2.4 per cent of the " +
         "time, against 63.6 per cent for the control system in standard use, and it can be trained " +
         "in 47 minutes instead of 66 hours."],
        ["The twin-building procedure was repeated on four buildings from a 48 m² flat to an " +
         "8 500 m² commercial building and reduced prediction error on every one of them."],
        [{ t: "Two of the four stated objectives were not fully reached", b: true, c: BAD },
         " — edge hardware integration and the continuous online learning loop — and are " +
         "reported here as they stand, with what was achieved towards each."],
      ]),

      pageBreak(),

      // =========================================================== contents ==
      h1("What is in this report"),
      p("The report is written for readers who are not specialists in building services or in " +
        "machine learning. Section 1 explains the problem and the vocabulary. Section 2 describes " +
        "how the work was carried out and how success was measured. Sections 3 and 4 report the " +
        "results for work packages 10 and 11 respectively. Section 5 gives the practical " +
        "implications, Section 6 the honest status against each promised deliverable, Section 7 the " +
        "recommended priorities, and Section 8 the outputs produced. Two appendices hold a glossary " +
        "and the complete set of numbers with their sources."),
      p("Diagrams marked as reproduced from the scientific manuscript use technical notation, " +
        "because they are the same diagrams that the journal reviewers see. Each one is preceded by " +
        "a short reading key in plain language, so no diagram requires prior knowledge."),
      runs([{ t: "A note on the numbers. ", b: true },
             "Every figure quoted in this report comes from a stored result file produced by the " +
             "experiments, not from an estimate or a projection. Appendix B names the file behind " +
             "each number. Where a result rests on a small number of cases, the report says so " +
             "rather than presenting it as established."]),

      // ============================================================ part 1 ===
      h1("1. The problem, and why this work is needed"),

      h2("1.1 Where the energy goes"),
      p("Heating, cooling and ventilation are the largest single consumer of energy in almost every " +
        "building. The equipment that provides them — boilers, heat pumps, chillers, fans, " +
        "radiators — is controlled by a small piece of software that decides, minute by minute, " +
        "how hard to run it. That software is usually a simple rule that reacts to the current " +
        "temperature: if the room is too cold, heat harder."),
      p("A simple reacting rule is robust but wasteful. It cannot anticipate. It does not know that " +
        "the sun will come out in two hours, that the building will empty at six o'clock, or that " +
        "electricity will be cheaper tonight. A controller that could anticipate would use less " +
        "energy for the same comfort, and it would do so without replacing a single piece of " +
        "equipment. That is the prize: a software upgrade with the effect of a hardware upgrade."),

      h2("1.2 Why anticipating controllers are hard to build"),
      p("The most capable way known to build an anticipating controller is to let software learn the " +
        "job by trial and error, the same family of methods that learned to play board games and to " +
        "fly stratospheric balloons. The method works, but it is expensive in one specific way: it " +
        "needs to try things. Millions of times. A learning controller for a building typically needs " +
        "several million practice decisions before it is competent."),
      p("Those attempts cannot be made on a real building. At one decision every fifteen minutes, " +
        "five million attempts would take more than a century, and the occupants would spend that " +
        "century being used as test subjects. So the practice has to happen somewhere else."),

      h2("1.3 The digital twin, and the question this project asks"),
      p("The accepted answer is a digital twin: a software copy of the building that runs far faster " +
        "than real time, on which the controller can make its millions of mistakes harmlessly. The " +
        "controller learns on the copy and is then installed on the real building."),
      p("This raises a question that the field has largely treated as settled: how good does the copy " +
        "have to be? The intuitive answer, and the one the literature acts on, is that the copy should " +
        "be as accurate as possible — the closer it is to the real building, the better the " +
        "controller trained on it. Most published work therefore measures a twin by its prediction " +
        "accuracy and selects the most accurate one available."),
      runs([{ t: "The central result of this reporting period is that this reasoning is wrong, and " +
              "measurably so.", b: true },
             " The rest of the report sets out the evidence."]),

      ...figure("fig1_concept.png",
        "The four parts of the system and how they connect. The project is responsible for the two " +
        "middle elements: building the copy, and building the control software that learns on it."),

      h2("1.4 The vocabulary used in this report"),
      p("Five terms recur throughout. They are defined here and used consistently; Appendix A gives " +
        "the full glossary."),

      tableCaption("The five terms needed to read this report."),
      table(
        ["Term", "What it means in this report"],
        [
          [{ t: "Digital twin", b: true },
           "A software copy of a building that predicts how its temperature responds to the heating " +
           "and cooling it receives. Also called a surrogate. Runs hundreds of times faster than the " +
           "building itself."],
          [{ t: "Prediction error", b: true },
           "How far the twin's predicted temperature drifts from the true temperature over a full " +
           "day of operation, in degrees Celsius. Lower is better. This is the quantity the field " +
           "normally optimises."],
          [{ t: "Comfort violation", b: true },
           "The percentage of time the building is outside the temperature range considered " +
           "acceptable for its occupants. Lower is better. This is what a building manager actually " +
           "cares about."],
          [{ t: "Discomfort score", b: true },
           "A single number combining how long the building was uncomfortable with how badly. A " +
           "score above 1.0 marks a controller that is unusable in practice; the standard controller " +
           "in the benchmark scores 0.910."],
          [{ t: "Learning controller", b: true },
           "Control software that improves by trial and error rather than by being programmed with " +
           "fixed rules. Needs a digital twin to practise on."],
        ],
        [2200, 7160]),
      source("Definitions as used in the submitted manuscript; the discomfort score is the " +
             "duration-and-severity maintenance score of the BOPTEST benchmark."),

      pageBreak(),

      // ============================================================ part 2 ===
      h1("2. How the work was carried out"),

      h2("2.1 The test bed: a shared international benchmark, not our own building"),
      p("A recurring weakness in this research area is that groups evaluate their methods on their " +
        "own private building models, which makes results impossible to compare and easy to " +
        "flatter. This project deliberately avoided that. All experiments were run on BOPTEST, an " +
        "open benchmark developed under the International Energy Agency's building-research " +
        "programme and used internationally to compare building-control methods on equal terms."),
      p("BOPTEST provides detailed physical simulations of real building types, each with its own " +
        "weather data, occupancy patterns and equipment, together with a reference controller of the " +
        "conventional kind to compare against. Using it means that the numbers in this report can be " +
        "reproduced and challenged by other groups, which is a precondition for the results being " +
        "taken seriously and, eventually, for them being adopted."),
      p("The simulation runs inside a sealed software container and is addressed over a network " +
        "interface, exactly as a real building management system would be addressed. Our controller " +
        "has no access to the internals of the simulated building: it sees only what a real " +
        "controller would see through sensors, and it can change only what a real controller would " +
        "be allowed to change."),

      readingKey(
        "The left box is our control software; the right box is the simulated building, running as a " +
        "sealed service. Once every 15 minutes the controller sends one instruction — how warm " +
        "the air supplied to the room should be — and receives back the sensor readings and a " +
        "short weather forecast. Nothing else passes between them. The mathematics in the arrow is " +
        "simply the formula converting the controller's output, a number between minus one and one, " +
        "into a temperature between 15 and 40 °C."),
      ...figure("paper_control_loop.png",
        "The control loop, reproduced from the scientific manuscript. Our controller and the " +
        "simulated building exchange one instruction and one set of measurements every 15 minutes, " +
        "over the same kind of interface a real building management system uses."),

      h2("2.2 The four buildings"),
      p("Four buildings were used. One is the main study case, an office zone; the other three were " +
        "used to test whether the methods transfer to buildings they were not designed for. They " +
        "differ in every way that matters: floor area spans a factor of 175, the heat source is a " +
        "gas boiler in one case, an electric heat pump in another, and a district heating connection " +
        "in the third, and the way heat reaches the room differs in each."),

      tableCaption("The four buildings used in the study."),
      table(
        ["Building", "Floor area", "How it is heated", "Role in the study"],
        [
          [{ t: "Office zone", b: true }, "48 m²",
           "Gas boiler and chiller, air supplied through a fan coil", "Main study case"],
          [{ t: "Flat", b: true }, "48 m²",
           "Gas water heater, 5 kW, radiator with a thermostatic valve", "Transfer target"],
          [{ t: "Detached house", b: true }, "192 m²",
           "Air-to-water heat pump, 15 kW, underfloor heating", "Transfer target"],
          [{ t: "Commercial building", b: true }, "8 500 m²",
           "District heating at 65 °C, air handling unit and radiators", "Transfer target"],
        ],
        [2300, 1250, 3410, 2400]),
      source("BOPTEST test cases bestest_air, bestest_hydronic, bestest_hydronic_heat_pump and " +
             "singlezone_commercial_hydronic."),

      readingKey(
        "Each of the four panels is one building. The blue box on the left is its heat source; the " +
        "box next to it is how heat reaches the room; the large central box is the room itself. The " +
        "red arrow entering from the right is the one instruction our controller is allowed to send, " +
        "and it is a different kind of instruction in each building — a supply-water " +
        "temperature here, a heat-pump modulation signal there. The formulas inside the central box " +
        "are the standard heat-balance equations; they say that the room's temperature changes " +
        "according to the heat put into it, the heat lost through the walls, and the sun. The line " +
        "beginning 'sensors' lists what the controller is allowed to measure."),
      ...figure("paper_testcases.png",
        "The four buildings, reproduced from the scientific manuscript. They differ in size, in " +
        "heat source, in how heat is delivered to the room, in climate, and in the kind of " +
        "instruction the controller can issue."),

      h2("2.3 How success was measured"),
      p("Three quantities are reported throughout, and it matters that they are kept separate, " +
        "because the main finding of the year is precisely that they do not move together."),
      bullet([{ t: "Prediction error", b: true },
               " measures the twin, not the controller. The twin is asked to predict a full day of " +
               "the building's temperature from a standing start, and the error is the average " +
               "distance between its prediction and the truth. A day-long prediction is used rather " +
               "than the next-quarter-hour, because a controller in training runs the twin forward " +
               "for long stretches, and a model can be excellent at one step and useless over a day."]),
      bullet([{ t: "Comfort violation", b: true },
               " measures the controller. It is the share of the evaluated period during which the " +
               "building was outside its acceptable temperature range."]),
      bullet([{ t: "The discomfort score", b: true },
               " also measures the controller, and combines duration with severity: being one degree " +
               "too cold for an hour counts for less than being five degrees too cold for the same " +
               "hour. A score above 1.0 is the benchmark's marker of a controller that could not be " +
               "put into service."]),
      p("Energy consumption is also recorded in every experiment and is reported wherever a comfort " +
        "result would otherwise be misleading — it is always possible to make a building " +
        "comfortable by burning more fuel, and one of the transfer results in Section 4.9 does " +
        "exactly that."),

      h2("2.4 The discipline imposed on the experiments"),
      p("Because the central claim of this work contradicts a common assumption, the evidence had to " +
        "be organised so that it could not be the product of favourable choices made after seeing " +
        "the results. Three measures were used."),
      num([{ t: "The hypotheses and the pass marks were written down before the experiments ran", b: true },
           " and recorded in the project's version history with a timestamp. Of the four hypotheses " +
           "registered at the start of the period, one was confirmed, one was refuted, one was not " +
           "supported, and one was partly supported. They are reported as they came out."]),
      num([{ t: "Every experiment was repeated with different random starting conditions", b: true },
           ". Learning controllers are sensitive to the random seed they start from, and a single " +
           "lucky run proves nothing. The main comparisons were run three times over and the spread " +
           "between the runs is reported alongside the average."]),
      num([{ t: "Every number traces to a stored file", b: true },
           ". Appendix B lists them. Nothing in this report was typed in by hand from a screen."]),

      readingKey(
        "This shows the order in which each transfer test was carried out. The point of the diagram " +
        "is the first box and the last: the list of test cases, the pass marks and the hypotheses " +
        "were fixed and version-stamped before anything was run, and the verdict at the end was " +
        "recorded against those pre-set marks. The pass mark itself — written in the last box " +
        "as 1.25 times the score of the building's own conventional controller — means that a " +
        "transferred controller had to come within 25 per cent of the comfort achieved by the " +
        "controller already installed."),
      ...figure("paper_protocol.png",
        "The evaluation protocol, reproduced from the scientific manuscript. Pass marks were fixed " +
        "and recorded before any result was seen, so the verdicts could not be adjusted afterwards.",
        { width: 560 }),

      pageBreak(),

      // ============================================================ part 3 ===
      h1("3. Work Package 10: a digital twin for each building"),

      callout("What this work package promised, and where it stands", [
        [{ t: "Promised: ", b: true }, "digital twins developed for each building, and integration " +
         "with edge computing infrastructure."],
        [{ t: "Twins for each building: delivered. ", b: true, c: GOOD },
         "Two twin designs were built and validated for the main building, and the procedure for " +
         "building one was then applied to three further buildings, reducing prediction error by " +
         "between 56 and 88 per cent on every one of them."],
        [{ t: "Edge computing integration: not delivered. ", b: true, c: BAD },
         "No deployment onto edge hardware took place. What the period produced instead is the " +
         "measurement that decides whether such a deployment is feasible, and it is favourable. " +
         "Section 3.8 gives the detail."],
      ]),

      h2("3.1 Two different kinds of twin, and why both were built"),
      p("There are two established ways to build a software copy of a building, and they pull in " +
        "opposite directions. One learns the building's behaviour purely from recorded measurements " +
        "and knows no physics; it is fast and needs no engineering information, but it cannot be " +
        "inspected or explained, which matters when a building owner asks why the system did " +
        "something. The other starts from a simplified physical model of how heat flows, and learns " +
        "only a small correction on top; it can be inspected, and its main internal number is a real " +
        "physical property of the building that can be checked against reality."),
      p("The project built both, for the same building, and measured them the same way. Keeping both " +
        "turned out to be the right decision, though not for the reason expected at the outset."),

      ...figure("fig5_two_twins.png",
        "The two twin designs. Design A learns from data alone; Design B starts from physics and " +
        "learns a correction. Both were built for the same building and judged by the same test."),

      h2("3.2 How accurate each twin is"),
      p("Four twins were produced in total: the data-driven design trained on two different " +
        "qualities of recorded data, and the physics design before and after being tuned to the " +
        "specific building. Each was asked to predict a full day of the building's temperature."),

      tableCaption("Prediction accuracy of the four twins built for the main building. Lower is better."),
      table(
        ["Twin", "What it is", "Day-long prediction error"],
        [
          ["Data-driven, hourly data",
           "Learns from measurements recorded once an hour", { t: "1.557 °C", align: AlignmentType.RIGHT }],
          ["Data-driven, 15-minute data",
           "Same design, learning from four times as much detail", { t: "0.876 °C", align: AlignmentType.RIGHT }],
          ["Physics-based, untuned",
           "Physical model with generic parameter values", { t: "1.466 °C", align: AlignmentType.RIGHT }],
          [{ t: "Physics-based, tuned", b: true },
           { t: "Same model after being fitted to this building", b: true },
           { t: "0.644 °C", b: true, c: GOOD, align: AlignmentType.RIGHT }],
        ],
        [2600, 4460, 2300]),
      source("block1_corpus_matched_comparison.csv. The error is the average deviation over a " +
             "24-hour prediction started from a known state."),
      p("The tuned physics twin is the most accurate of the four, by a wide margin: it more than " +
        "halves the error of the hourly data-driven twin. On the criterion the field normally uses, " +
        "this is the twin one would select. Section 4 reports what happened when we did."),

      h2("3.3 Tuning a twin to a specific building"),
      p("The tuning procedure is the reusable asset of this work package, so it is worth describing. " +
        "It works in three stages, each fixing a different kind of mismatch between the generic " +
        "physical model and the particular building."),
      num("The first stage fits how the building loses heat to the outside, using only periods when " +
          "the heating is off, so that the heating system cannot confuse the measurement.", 1),
      num("The second stage fits the building's thermal mass — how much heat the structure " +
          "stores, which determines how quickly it responds. This is the parameter that carries " +
          "physical meaning.", 1),
      num("The third stage corrects the residual offset between the model's temperatures and the " +
          "measured ones, which reduced the remaining misalignment from 0.374 °C to " +
          "0.232 °C, an improvement of 38 per cent.", 1),

      readingKey(
        "Three panels. The left one shows the tuning procedure searching for the building's thermal " +
        "mass: the green line is the search, and it settles inside the shaded band, which is the " +
        "range engineering judgement says the answer should lie in. The middle panel is the headline " +
        "of the procedure — prediction error falling from 1.466 to 0.644 degrees, a 56 per cent " +
        "reduction. The right panel compares the pattern of remaining mistakes before and after: the " +
        "red shape is narrower and more centred than the orange one, meaning the tuned twin's errors " +
        "are both smaller and less biased."),
      ...figure("paper_calibration.png",
        "The three-stage tuning procedure, reproduced from the scientific manuscript. The recovered " +
        "thermal mass lands inside the physically expected range, prediction error falls by 56 per " +
        "cent, and the remaining errors become smaller and less biased."),

      h2("3.4 Checking that the twin is physically believable, not merely accurate"),
      p("An accurate model can still be nonsense internally: it can reproduce the right temperatures " +
        "by means of numbers that correspond to nothing real, and such a model will fail the moment " +
        "it is asked about a situation it has not seen. Three checks were run to confirm the twin is " +
        "not of that kind."),
      bullet([{ t: "The thermal mass is physically plausible. ", b: true },
              "The tuning recovered a value 5.1 per cent above the value engineering judgement would " +
              "have assigned in advance, and within the statistical uncertainty of the measurement. " +
              "In physical terms it corresponds to roughly 439 kilograms of air, which is the right " +
              "order of magnitude for a room of 48 square metres."]),
      bullet([{ t: "The twin responds in the right direction, always. ", b: true },
              "The twin was asked, from 400 different building states, what would happen if the " +
              "heating were turned up. It answered correctly, in the physically right direction, in " +
              "100 per cent of the 400 cases. A model that is merely curve-fitted typically fails " +
              "this test somewhere."]),
      bullet([{ t: "The twin was judged on day-long predictions, not single steps. ", b: true },
              "This is a deliberately harder test than the one commonly reported, and it is the one " +
              "that matches how a twin is actually used during training."]),

      h2("3.5 Where the accuracy improvement actually came from"),
      p("The total improvement, from the weakest twin to the best, is 0.913 °C. It is tempting " +
        "to attribute all of it to the tuning procedure, since that is the part of the work the " +
        "project contributed. That would be misleading, and the report does not do it."),
      p("The improvement can be accounted for in two equally defensible orders, and they give " +
        "different answers: counting the effect of better measurement data first credits the tuning " +
        "with 25 per cent of the gain, while counting the change of model design first credits it " +
        "with 90 per cent. The two disagree because the changes interact. We therefore report the " +
        "contribution of the tuning procedure as a range of 25 to 90 per cent rather than choosing " +
        "the flattering end of it."),

      ...figure("fig6_where_accuracy.png",
        "Two defensible accountings of the same 0.913 °C improvement. The contribution of the " +
        "tuning procedure is reported as a range because the two accountings disagree."),

      h2("3.6 A twin for each building: does the procedure transfer?"),
      p("The work package promises a twin per building, which is only meaningful if the procedure " +
        "for building one can be applied to a building it was not designed around. This was tested " +
        "on the three further buildings, which between them change the heat source, the way heat " +
        "reaches the room, and the scale of the building by a factor of 175."),

      readingKey(
        "The grey box on the left is the building the method was developed on. The three boxes on " +
        "the right are the buildings it was carried across to, labelled with their heat source and " +
        "how heat reaches the room. The quantity written as C-zon in each box is the building's " +
        "thermal mass, expressed as a multiple of the original building's. The observation the " +
        "diagram makes is that all three came out close to the same multiple, near 1.9, despite the " +
        "buildings being wildly different in size."),
      ...figure("paper_topology.png",
        "Carrying the twin-building procedure to three further buildings, reproduced from the " +
        "scientific manuscript. All three re-identified thermal masses landed close to the same " +
        "multiple of the original building's.", { width: 520 }),

      p("The procedure worked on all three. Prediction error fell on every building, by between 60 " +
        "and 88 per cent, and the twin's prediction of how much power the heating equipment draws " +
        "improved as well."),

      tableCaption("Applying the twin-building procedure to three buildings it was not designed for."),
      table(
        ["Building", "Error before", "Error after", "Improvement", "Power prediction error"],
        [
          ["House, heat pump, 192 m²", "1.421 °C", "0.565 °C",
           { t: "−60.2 %", c: GOOD, b: true }, "2 921 W → 1 767 W"],
          ["Flat, gas boiler, 48 m²", "2.666 °C", "0.335 °C",
           { t: "−87.4 %", c: GOOD, b: true }, "784 W → 85 W"],
          ["Commercial, district heat, 8 500 m²", "1.952 °C", "0.238 °C",
           { t: "−87.8 %", c: GOOD, b: true }, "not measured"],
        ],
        [2900, 1420, 1420, 1420, 2200],
        { align: [undefined, AlignmentType.RIGHT, AlignmentType.RIGHT, AlignmentType.RIGHT, undefined] }),
      source("block3_hydronic_family_n2_summary.csv, block3_transfer_matrix.csv."),

      ...figure("fig4_transfer.png",
        "Prediction error before and after tuning, on all four buildings. The procedure reduced the " +
        "error on every one of them, across a 175-fold range of floor area."),

      p("One further observation is worth recording, with a caution attached. The thermal mass " +
        "identified for the three new buildings came out at a consistent 1.92 times the value of the " +
        "original building, varying by only about 1.7 per cent between them, despite the enormous " +
        "difference in their sizes. If this regularity held generally it would be practically " +
        "useful, because it would let a usable twin be produced for a new building of this family " +
        "with far less measurement. We report it as an observed regularity across three buildings " +
        "and explicitly not as a general law: three cases are too few to claim one, and testing it " +
        "properly is on the list of priorities for the next period."),

      h2("3.7 How fast the twin runs"),
      p("Speed is the reason a twin exists at all. The twins were benchmarked against the real " +
        "simulation under identical conditions, on a single processor core with no graphics card, " +
        "which is a deliberately modest configuration."),

      tableCaption("Speed of each twin against the real simulation, on one processor core."),
      table(
        ["Running on", "Decisions per second", "Time per decision", "Speed-up"],
        [
          ["The real building simulation", "21", "15.33 ms", "1×"],
          ["The data-driven twin", "4 626", "0.19 ms", { t: "220×", b: true, c: GOOD }],
          ["The tuned physics twin", "—", "—", { t: "114×", b: true, c: GOOD }],
          ["The combined architecture of Section 4.5", "—", "—",
           { t: "85×", b: true, c: GOOD }],
        ],
        [3600, 2100, 1830, 1830],
        { align: [undefined, AlignmentType.RIGHT, AlignmentType.RIGHT, AlignmentType.RIGHT] }),
      source("speed_benchmark_table.csv. Single CPU thread, no GPU."),
      p("In practical terms: training one controller takes about 66 hours of computing against the " +
        "real simulation, and about 47 minutes against the twin. That is the difference between an " +
        "experiment one can run three times to check it, and an experiment one runs once and hopes."),

      h2("3.8 Edge computing integration: not delivered in this period"),
      runs([{ t: "This part of the objective was not reached. ", b: true, c: BAD },
             "All work was carried out on a laptop-class workstation with a six-core processor and " +
             "32 GB of memory, with the building simulation running in a software container on the " +
             "same machine. No deployment onto edge hardware installed in a building took place, and " +
             "no edge management software was integrated."]),
      p("What the period did produce is the measurement that determines whether such a deployment is " +
        "feasible at all, and it is favourable. The twin contains 8 482 adjustable numbers — " +
        "small, by the standards of modern software models — and executes one control decision " +
        "in 0.19 milliseconds using a single processor core and no graphics card. For comparison, " +
        "the control decision is only needed once every fifteen minutes. The computational demand is " +
        "therefore some six orders of magnitude below the available budget, which is comfortably " +
        "within what inexpensive edge hardware provides."),
      p("The consequence is that the remaining work is engineering and installation rather than " +
        "research: porting the twin to the target hardware, measuring memory use and thermal " +
        "behaviour under sustained operation, and confirming the timing on the real device rather " +
        "than inferring it. It should be confirmed on real hardware rather than assumed, and it is " +
        "the first recommended priority in Section 7."),

      pageBreak(),

      // ============================================================ part 4 ===
      h1("4. Work Package 11: feedback control with continuous learning"),

      callout("What this work package promised, and where it stands", [
        [{ t: "Promised: ", b: true }, "feedback control strategies deployed, with continuous " +
         "learning for self-optimizing buildings."],
        [{ t: "Feedback control: delivered. ", b: true, c: GOOD },
         "Three different families of learning controller were built and run in closed loop against " +
         "the live simulated building. The best configuration keeps the building outside its comfort " +
         "range 2.4 per cent of the time."],
        [{ t: "Continuous learning: partly delivered. ", b: true, c: WARN },
         "The adaptation machinery exists and has been run offline and against the live simulation, " +
         "and the transfer experiments have established quantitatively what the adaptation must act " +
         "on. A controller that adapts continuously while a building is in service has not been " +
         "deployed. Section 4.9 gives the detail."],
        [{ t: "Additionally: ", b: true }, "this work package produced the project's principal " +
         "scientific result, described in Section 4.3."],
      ]),

      h2("4.1 What was built and tested"),
      p("Feedback control means the controller observes the building and reacts, continuously, in a " +
        "closed loop. Every fifteen minutes the controller reads the sensors and a short weather " +
        "forecast, and issues one instruction. It is not allowed to reach inside the building's own " +
        "equipment controls; it operates through the same narrow interface a real retrofit " +
        "controller would have."),
      p("The experiments of this work package divide into a central test and three boundary checks. " +
        "The central test asks which kind of twin produces the best controller. The boundary checks " +
        "ask whether the answer still holds when the controller is built differently, when it is " +
        "given different information, and when it is moved to another building."),

      readingKey(
        "The top half is the central experiment. The grey box on the left lists the four twins that " +
        "controllers were trained on; the middle box is the controller; the purple box on the right " +
        "is the live simulated building it was then tested on. The sentence in bold underneath is " +
        "the finding, and the notation 'm-s greater than 1' simply means the resulting controller " +
        "was unusable. The dashed box below holds the three boundary checks, which are the subject " +
        "of Sections 4.7 to 4.9."),
      ...figure("paper_study_design.png",
        "The design of the control experiments, reproduced from the scientific manuscript. The upper " +
        "block is the central test; the lower block holds the three checks on how far its conclusion " +
        "extends.", { width: 470 }),

      h2("4.2 What a controller trained on each twin achieved"),
      p("The same learning method, with the same settings, was trained separately on each twin and " +
        "then installed on the live simulated building. Every configuration was run three times from " +
        "different random starting points."),

      tableCaption("Controllers trained on each twin, tested on the live building. Above 1.0 is unusable."),
      table(
        ["Trained on", "Twin's prediction error", "Discomfort score", "Time outside comfort range"],
        [
          [{ t: "Data-driven twin, hourly", b: true }, "1.557 °C (worst)",
           { t: "0.095", b: true, c: GOOD }, { t: "4.4 %", c: GOOD }],
          ["Data-driven twin, 15-minute", "0.876 °C",
           { t: "1.211", b: true, c: BAD }, { t: "91.4 %", c: BAD }],
          ["Tuned physics twin", "0.644 °C (best)",
           { t: "1.102", b: true, c: BAD }, { t: "82.4 %", c: BAD }],
          [{ t: "The combined architecture (Section 4.5)", b: true }, "—",
           { t: "0.041", b: true, c: GOOD }, { t: "2.4 %", b: true, c: GOOD }],
          [{ t: "Conventional controller in standard use", i: true }, { t: "—", i: true },
           { t: "0.910", i: true }, { t: "63.6 %", i: true }],
        ],
        [2900, 2200, 2000, 2260],
        { align: [undefined, AlignmentType.RIGHT, AlignmentType.RIGHT, AlignmentType.RIGHT] }),
      source("block2_fidelity_utility_scatter.csv, block2_thermostatic_seed_band.csv. Scores are " +
             "for a representative two-week evaluation window; the conventional controller's figures " +
             "are its published twelve-month result, so the comparison indicates the scale of the " +
             "difference rather than a like-for-like margin."),

      h2("4.3 The central discovery"),
      p("Read the first three rows of that table in order. The twin with the worst prediction error " +
        "produced the only usable controller. The twin with the best prediction error produced a " +
        "controller that left the building uncomfortable 82 per cent of the time. And the middle " +
        "row is the sharpest version of the result: it is the same twin as the first row, differing " +
        "only in having been trained on more finely sampled data. Making that twin more accurate " +
        "moved the controller it produces from working to failing."),
      runs([{ t: "Prediction accuracy is therefore not a valid criterion for choosing a twin to " +
              "train a controller on.", b: true },
             " This is the principal scientific result of the reporting period. It matters " +
             "practically as well as scientifically, because effort spent making a twin more " +
             "accurate is effort that may be making the eventual controller worse, and there is a " +
             "great deal of such effort being spent internationally."]),

      ...figure("fig2_main_finding.png",
        "The central discovery. The left panel ranks the three twins by accuracy; the right panel " +
        "shows how the controllers trained on them actually performed. The order is reversed."),

      h2("4.4 Why it happens"),
      p("A result of this kind is not useful until it is explained, because until then it might be " +
        "an accident of the particular twins we built. The explanation was pinned down with a " +
        "dedicated experiment."),
      p("A learning controller improves by making a small change and observing whether things got " +
        "better. What it needs from its practice environment is not that the environment be " +
        "correct, but that the connection between a change and its consequence be visible. The more " +
        "finely detailed twins change by a smaller amount at each step, and this makes the picture " +
        "the learning algorithm sees far bumpier: small changes produce erratic swings that swamp " +
        "the real trend, and the learner cannot tell which way is uphill."),
      p("This bumpiness was measured directly rather than assumed. On a scale-free measure, it is " +
        "0.169 for the twin that produced a working controller, and roughly nine times and eight " +
        "times that for the two twins that failed. A further control experiment held everything " +
        "else fixed and changed only the size of the twin's time step, and it reproduced the " +
        "failure — which isolates the step size, rather than the accuracy, as the property " +
        "actually responsible."),

      ...figure("fig7_mechanism.png",
        "Why the more accurate twin produced the worse controller. The learner needs to see which " +
        "way is downhill; the finer-grained twin gives it a picture in which that is invisible."),

      h2("4.5 The control architecture that resolves the conflict"),
      p("The finding leaves a genuine dilemma. The data-driven twin is the one a controller can " +
        "learn on, but it is the less accurate of the two and cannot be inspected. The physics twin " +
        "is accurate and inspectable but ruins the controller trained on it. Discarding either loses " +
        "something valuable."),
      p("The architecture adopted resolves this by giving the two twins different jobs instead of " +
        "making them compete for the same one. The data-driven twin is the practice environment: the " +
        "controller acts in it, and it alone determines what happens next. The physics twin never " +
        "takes part in the practice. It is frozen, and consulted only as a second opinion: at each " +
        "step it is asked what it would have predicted, and where the two twins disagree strongly, " +
        "the controller's score for that step is reduced."),
      p("The effect is a controller that learns on the environment it can learn from, while being " +
        "steered away from the regions where that environment is least trustworthy. It is a simple " +
        "arrangement, and the fact that a simple arrangement was enough is itself part of the " +
        "result."),

      readingKey(
        "Follow the arrows from the left. The controller's action goes into the green box, the " +
        "practice twin, which decides what happens next. The same action also goes into the orange " +
        "box, the frozen physics twin, which does not affect what happens but records what it would " +
        "have expected. The middle box measures how far apart the two answers are, in degrees and in " +
        "watts. The box on the right combines the ordinary score for the step with a penalty " +
        "proportional to that disagreement. The word 'frozen' matters: the physics twin is never " +
        "changed and never drives the simulation."),
      ...figure("paper_hybrid.png",
        "The combined architecture, reproduced from the scientific manuscript. The practice twin " +
        "drives the simulation; the physics twin only issues a second opinion that penalises steps " +
        "where the two disagree.", { width: 520 }),

      p("Averaged over three independent runs, this architecture beats the best single-twin " +
        "alternative on both evaluation periods — 0.060 against 0.072 on the demanding period " +
        "and 0.014 against 0.046 on the typical one — while running 85 times faster than the " +
        "real simulation. The average disagreement between the two twins across these runs is about " +
        "one degree and around 700 watts, which is the quantity the penalty acts on."),

      h2("4.6 What the resulting system delivers"),
      p("Two outcomes matter to anyone deciding whether to fund the next stage: how well the " +
        "building is run, and what it costs to produce a controller."),

      ...figure("fig3_outcome.png",
        "Occupant comfort and development cost, against the conventional controller and against " +
        "training on the real simulation."),

      p("On comfort, the controller holds the building inside its acceptable range for 97.6 per cent " +
        "of the evaluated period, against 36.4 per cent for the conventional controller. This " +
        "comparison should be read as an indication of scale rather than a precise margin: the " +
        "conventional controller's figure is its published twelve-month result, while ours is " +
        "measured over representative two-week periods. A full twelve-month evaluation of our " +
        "controller is planned for the next period."),
      p("On cost, a controller that took 66 hours of computing to train now takes 47 minutes. The " +
        "practical significance is not the saving in electricity but the change in what is possible: " +
        "at 66 hours per attempt, an experiment is run once. At 47 minutes it can be run three times " +
        "with different random starts to check that the result is real, which is exactly the " +
        "discipline described in Section 2.4 and the reason this project could catch a result that " +
        "contradicts a widespread assumption."),

      h2("4.7 Does the finding hold for other kinds of controller?"),
      p("A conclusion drawn from one controller design is worth little, so the same question was put " +
        "to a second, more elaborate design: a two-level controller in which a supervisor decides " +
        "whether the building is in a heating or a cooling regime and hands over to a specialist " +
        "for that season."),

      readingKey(
        "The controller reads the building's state on the left. The middle box is the supervisor, " +
        "which decides which season the building is in and routes the decision to one of the two " +
        "specialists on the right, one for heating and one for cooling. The chosen specialist then " +
        "issues the instruction to the building."),
      ...figure("paper_hdrl.png",
        "The two-level controller, reproduced from the scientific manuscript. A supervisor routes " +
        "each decision to a heating or a cooling specialist.", { width: 540 }),

      p("The result is a genuine limitation of the architecture of Section 4.5, and it is reported " +
        "as such. The second-opinion penalty, which is what makes the simpler controller work, makes " +
        "this one steadily worse: as the penalty is strengthened, the share of time outside the " +
        "comfort range rises from 6.3 to 24.4 per cent, and the strength that is best for " +
        "the simple controller is among the worst for this one."),
      p("The practical conclusion is that the penalty strength is a property of the controller " +
        "design and not a universal constant, so it must be re-tuned whenever the controller " +
        "architecture changes and must never be quoted without naming the design it belongs to."),
      runs([{ t: "This result was the weakest piece of evidence in the project and has since been " +
              "closed. ", b: true },
             "It originally rested on a single training run per setting. The whole experiment was " +
             "repeated from scratch three times over, at all four penalty strengths — twelve " +
             "training runs, thirty hours of computing — and the finding survived: the effect is " +
             "ten times larger than the variation between repeats on the demanding evaluation " +
             "period and six times larger on the typical one. One nuance the repeats exposed is " +
             "that the damage stops growing above a moderate penalty: the difference between the " +
             "two strongest settings is smaller than the run-to-run variation, so those two cannot " +
             "be ranked against each other. That has been written into the scientific article as " +
             "stated rather than smoothed over."]),

      h2("4.8 What information the controller needs"),
      p("A third controller family was built to handle a trade-off explicitly: it can be asked at " +
        "run time to lean towards saving energy or towards protecting comfort, without retraining. " +
        "Testing it produced the most immediately actionable result of the year."),

      readingKey(
        "Two rows, the same controller in both. In the top row it is told only the building's " +
        "current state, and the outcome, in the red box, is that it fails. In the bottom row it is " +
        "additionally told what the weather and the building's use will be over the next few hours, " +
        "and the outcome, in the green box, is that it works. Nothing else differs between the rows."),
      ...figure("paper_morl.png",
        "The effect of what the controller is told, reproduced from the scientific manuscript. The " +
        "same controller fails when it sees only the present moment and works when it sees a few " +
        "hours ahead.", { width: 520 }),

      p("Widening what the controller can see — from the current state alone to the current " +
        "state plus a short forecast — moves it from unusable to usable. Prediction error falls " +
        "from 4.96 to 0.72 degrees, time outside the comfort range from 74.5 to 4.9 per cent, and " +
        "the discomfort score from 1.046 to 0.099."),

      ...figure("fig9_forecast_effect.png",
        "The effect of giving the controller a short forecast. The controller, its goals and its " +
        "twin are identical in both cases."),

      p("The finding is that the binding constraint was the information available to the controller, " +
        "not the sophistication of its decision-making. This is good news for deployment, because " +
        "weather forecasts are free and occupancy schedules are usually already in the building's " +
        "management system, whereas more sophisticated decision-making is expensive to develop and " +
        "hard to certify."),
      runs([{ t: "One caution attaches to this controller family. ", b: true },
             "Across five repeated runs its average performance is comfortably in the usable range, " +
             "at a discomfort score of 0.187, but the spread between runs is wide — the worst " +
             "run is three times the best. It fails a stability test that was set in advance, so " +
             "this controller is not yet ready for deployment even though its average result looks " +
             "good. Reporting the average alone would have concealed that."]),

      h2("4.9 The continuous learning objective: what the evidence shows"),
      p("The continuous learning objective exists to relax an assumption: that a controller can be " +
        "trained once and installed everywhere. Three results from this period bear directly on " +
        "whether that assumption holds, and together they establish that it does not."),

      h3("Result 1: a finished controller does not simply move to another building"),
      p("The controller trained on the office was frozen and installed, unchanged, on the three " +
        "other buildings. Because the buildings have different equipment, each needs a small " +
        "translation layer that converts the controller's instruction into the instruction that " +
        "building's equipment understands."),

      readingKey(
        "The frozen controller on the left issues a single number, a target temperature. The green " +
        "box in the middle is the translation layer, which rescales and clips that number into " +
        "whatever the target building's equipment accepts — a heat pump modulation signal, a " +
        "radiator valve position, or a coil setting, as listed on the right. Only the translation is " +
        "adjusted per building; the controller itself is untouched."),
      ...figure("paper_adapter.png",
        "How a finished controller is carried to a different building, reproduced from the " +
        "scientific manuscript. Only the translation layer changes; the controller is frozen.",
        { width: 540 }),

      p("The outcome was negative on two of the three buildings, against pass marks that had been " +
        "set before the tests were run. Both residential buildings saved energy — 7.3 and 5.8 " +
        "per cent — but missed their comfort targets. The commercial building met its comfort " +
        "target comfortably, but consumed 35.3 per cent more energy than the controller already " +
        "installed there, which makes it a pass on the letter of the test and not a result anyone " +
        "would deploy."),

      ...figure("fig8_transfer_verdicts.png",
        "Transferring the finished controller to three other buildings. Two missed the comfort " +
        "target; the third met it by using a third more energy. None is deployment-ready."),

      h3("Result 2: what does transfer is the procedure, not the controller"),
      p("Set this against Section 3.6, where the twin-building procedure was carried to the same " +
        "three buildings and succeeded on all three. The two results together say something more " +
        "useful than either alone: the transferable asset of this project is the method for " +
        "identifying a building, not the finished control law. Adaptation should therefore act on " +
        "the model of the building, and it is not worth investing in ways to carry finished " +
        "controllers between buildings."),

      h3("Result 3: starting from the physics twin makes things worse, not better"),
      p("A natural strategy for adaptation is to pre-train on the accurate physics twin and then " +
        "fine-tune on the real building, on the assumption that a head start must help. It was " +
        "tested and it does the opposite: the discomfort score ends up two to three times worse than " +
        "starting from scratch. This is a useful negative result, because it rules out the obvious " +
        "first thing one would try in the next period, before any effort is spent on it."),

      h3("Status of the objective"),
      runs([{ t: "Continuous learning is partly delivered. ", b: true, c: WARN },
             "Feedback control is deployed and evaluated in closed loop, and the adaptation " +
             "machinery exists, including a stage that fine-tunes a controller against the live " +
             "simulation. What does not yet exist is a controller that adapts continuously while a " +
             "building is in service. The three results above establish the requirement " +
             "quantitatively and, importantly, identify what the adaptation must act on: the " +
             "identified model of the building, not the transferred controller weights."]),

      pageBreak(),

      // ============================================================ part 5 ===
      h1("5. What this means in practice"),

      h2("5.1 For the research field"),
      p("The standard practice of selecting a training environment by its predictive accuracy is not " +
        "supported by the evidence, and effort invested in making such environments more accurate " +
        "may be counterproductive. The project has supplied not only the observation but a measured " +
        "mechanism and a control experiment isolating the responsible property, which is what turns " +
        "a curiosity into something other groups can act on. The role-separated architecture is a " +
        "concrete way to act on it without discarding the accurate model."),

      h2("5.2 For building operators"),
      p("Three findings have direct operational value, even before the remaining work is done."),
      bullet([{ t: "Forecast information is the cheapest available improvement. ", b: true },
              "Giving the controller a few hours of weather and occupancy look-ahead moved it from " +
              "unusable to usable. Forecasts cost nothing and occupancy schedules are usually " +
              "already in the building's management system."]),
      bullet([{ t: "The computational requirement is small. ", b: true },
              "One control decision costs 0.19 milliseconds on a single processor core, and is " +
              "needed once every fifteen minutes. There is no need for expensive hardware in the " +
              "building, and no need to send the building's data to a remote service."]),
      bullet([{ t: "Each building will need its own tuning, and that is affordable. ", b: true },
              "A finished controller cannot simply be copied from one building to another, but the " +
              "tuning procedure ports readily and worked on every building tried, including one 175 " +
              "times the size of the original."]),

      h2("5.3 What has not been shown"),
      p("Three limits should be stated plainly, so that the results are not read as claiming more " +
        "than they do."),
      bullet("All results are on simulated buildings, albeit standard, physically detailed, " +
             "internationally used ones. No result in this report has been demonstrated on a " +
             "physical building."),
      bullet("The comparison baseline is the simulation's own built-in conventional controller, " +
             "which is a weak reference. A properly tuned conventional controller would be a harder " +
             "and more informative comparison, and adding one is a priority for the next period."),
      bullet("The regularity observed in the thermal masses of the three buildings rests on three " +
             "cases and is reported as an observation, not a law."),

      // ============================================================ part 6 ===
      h1("6. Status against the stated deliverables"),

      ...figure("fig10_status.png",
        "Status of the four stated deliverables at the end of the reporting period."),

      tableCaption("Detailed status of each deliverable, with the evidence behind it."),
      table(
        ["Deliverable", "Status", "Evidence"],
        [
          ["Digital twins developed for each building",
           { t: "Delivered", b: true, c: GOOD },
           "Two twin designs built and validated on the main building; the tuning procedure then " +
           "applied to three further buildings, reducing prediction error by 60 to 88 per cent on " +
           "each, across a 175-fold range of floor area"],
          ["Integration with edge computing infrastructure",
           { t: "Not delivered", b: true, c: BAD },
           "No deployment to edge hardware. The computational requirement was established " +
           "(0.19 ms per decision, one processor core, 8 482 parameters), which shows the " +
           "deployment to be feasible; the deployment itself remains outstanding"],
          ["Feedback control strategies deployed",
           { t: "Delivered", b: true, c: GOOD },
           "Closed-loop control on the live simulation across three controller families; the best " +
           "configuration reaches a discomfort score of 0.041 with comfort violation below 5 per " +
           "cent, at 85 times real-time speed"],
          ["Continuous learning for self-optimization",
           { t: "Partly delivered", b: true, c: WARN },
           "Offline and live fine-tuning stages implemented; the transfer study quantifies the need " +
           "for local adaptation and identifies what it must act on; no continuously adapting loop " +
           "is in operation"],
        ],
        [2700, 1700, 4960]),

      // ============================================================ part 7 ===
      h1("7. Recommended priorities for the next period"),
      p("The four priorities below follow from what this period established, in order of how much " +
        "they matter to the project's stated objectives."),
      num([{ t: "Put the twin onto edge hardware and measure it there. ", b: true },
           "This closes the one objective that was not delivered at all. The single-core benchmark " +
           "indicates the demand is well within reach, so what is needed is to port the twin to the " +
           "target device and measure step timing, memory use and thermal behaviour under sustained " +
           "operation, rather than to infer them."], 2),
      num([{ t: "Build adaptation that acts on the model of the building, not on the controller. ", b: true },
           "Section 4.9 establishes both halves of this: carrying finished controllers between " +
           "buildings does not work, and starting from the physics twin makes matters worse, while " +
           "the model-identification procedure ports reliably. This is the route to the " +
           "continuous-learning objective."], 2),
      num([{ t: "Complete the remaining seed replication. ", b: true },
           "The two-level controller experiment has now been repeated across three random starts at " +
           "every penalty strength, which closes what was the weakest link in the evidence. The " +
           "same treatment is still owed to the multi-objective controller, whose spread across " +
           "repeats is wide enough that its average result alone is not a safe basis for " +
           "deployment (Section 4.8)."], 2),
      num([{ t: "Add a stronger comparison baseline, and a full-year evaluation. ", b: true },
           "Present comparisons are against the simulation's built-in conventional controller. A " +
           "properly tuned conventional or predictive controller, evaluated over a full twelve " +
           "months on the same twin, would put the reported gains on much firmer ground and is what " +
           "reviewers of the eventual publications will ask for."], 2),

      // ============================================================ part 8 ===
      h1("8. Outputs produced in this period"),
      runs([{ t: "Journal submission. ", b: true },
             "A full research article covering the core of both work packages was submitted to the " +
             "journal ", { t: "Energies", i: true }, ", manuscript number energies-4523055, on " +
             "9 August 2026. It is currently under editorial assessment. The article reports the " +
             "central discovery of Section 4.3, the measured mechanism of Section 4.4, the " +
             "architecture of Section 4.5, and the transfer study of Sections 3.6 and 4.9."]),
      runs([{ t: "Conference presentation. ", b: true },
             "Results from this work were presented at the WCCM–ECCOMAS congress in Munich, " +
             "19–24 July 2026."]),
      runs([{ t: "Research artifacts. ", b: true },
             "The project maintains the complete set of trained twins, controllers, evaluation " +
             "traces and result files, with each number in the publications linked to the file that " +
             "produced it. On the advice of the scientific supervisor these are not being released " +
             "publicly at this stage; they are available to the journal's editors and reviewers on " +
             "request, and to the funding body at any time."]),
      runs([{ t: "Reusable methods. ", b: true },
             "Two components are reusable beyond this project: the three-stage procedure for tuning " +
             "a physical building model to measured data, which worked on every building tried, and " +
             "the role-separated control architecture, which is independent of the particular " +
             "building and of the particular learning method."]),

      pageBreak(),

      // =========================================================== appendix ==
      h1("Appendix A. Glossary"),
      table(
        ["Term", "Plain-language meaning"],
        [
          ["Benchmark (BOPTEST)",
           "A shared, open set of realistic building simulations that research groups use to compare " +
           "their control methods on equal terms, instead of each testing on its own private model."],
          ["Closed loop",
           "The controller continuously observes the building and reacts to what it sees, rather " +
           "than following a fixed schedule."],
          ["Comfort violation",
           "The share of time the building spends outside the temperature range considered " +
           "acceptable for its occupants."],
          ["Digital twin (surrogate)",
           "A software copy of a building that predicts how its temperature responds to heating and " +
           "cooling, and runs far faster than real time."],
          ["Discomfort score",
           "A single number combining how long the building was uncomfortable with how far outside " +
           "the acceptable range it went. Above 1.0 means unusable in practice."],
          ["Edge computing",
           "Running software on a small computer installed in the building itself, rather than in a " +
           "remote data centre. Keeps the building's data local and works without a network " +
           "connection."],
          ["Learning controller",
           "Control software that improves by trial and error rather than by being programmed with " +
           "fixed rules."],
          ["Prediction error",
           "How far the twin's predicted temperature drifts from the true temperature over a full " +
           "day, in degrees Celsius."],
          ["Random seed",
           "The starting point of the random choices a learning method makes. Different seeds give " +
           "different controllers, which is why experiments are repeated."],
          ["Role separation",
           "The architecture adopted in this project: one twin is used as the practice environment, " +
           "a second is used only to flag disagreement, and neither does the other's job."],
          ["Thermal mass",
           "How much heat a building's structure stores, which determines how quickly its " +
           "temperature responds to heating. A physical property that can be measured and checked."],
          ["Transfer",
           "Taking something developed for one building and using it on another."],
        ],
        [2300, 7060]),

      h1("Appendix B. Complete results with their sources"),
      p("Every quantity in this report comes from a stored result file. The table below names the " +
        "file behind each group of numbers, so that any figure can be traced and checked."),

      tableCaption("Provenance of the numbers quoted in this report."),
      table(
        ["Reported in", "Quantities", "Result file"],
        [
          ["Section 3.2, Table 2", "Prediction error of the four twins",
           "block1_corpus_matched_comparison.csv"],
          ["Sections 3.3 and 3.4", "Thermal mass, alignment improvement, directional checks",
           "block1_surrogate_final_metrics.csv"],
          ["Section 3.5", "Attribution of the accuracy improvement",
           "block1_corpus_matched_comparison.csv"],
          ["Section 3.6, Table 4", "Transfer of the tuning procedure to three buildings",
           "block3_hydronic_family_n2_summary.csv, block3_transfer_matrix.csv"],
          ["Section 3.7, Table 5", "Speed benchmark",
           "speed_benchmark_table.csv"],
          ["Section 4.2, Table 6", "Controller results per training twin",
           "block2_fidelity_utility_scatter.csv, block2_thermostatic_seed_band.csv"],
          ["Section 4.4", "Measured bumpiness of the response surface",
           "block2_mechanism_surface_sharpness.csv"],
          ["Section 4.5", "Disagreement between the two twins",
           "hybrid_disagreement_summary.csv"],
          ["Section 4.7", "Two-level controller, penalty-strength sweep across three repeats",
           "block2_hdrl_lambda_sweep_seed_band.csv"],
          ["Section 4.8", "Effect of the forecast; stability across five runs",
           "block2_morl_comparison_summary.csv, morl_canonical_seedfix_yearly_summary.csv"],
          ["Section 4.9", "Transfer verdicts against pre-set targets",
           "block3_transfer_matrix.csv"],
        ],
        [2300, 3700, 3360]),

      new Paragraph({
        spacing: { before: 300 },
        border: { top: { style: BorderStyle.SINGLE, size: 4, color: RULE, space: 8 } },
        children: [new TextRun({
          text: "All quantities in this report are reproducible from stored result files. Figures " +
                "and tables in the submitted manuscript are linked to the same files through " +
                "provenance maps in its supplementary materials. Diagrams marked as reproduced from " +
                "the scientific manuscript are the figures submitted to the journal.",
          size: 17, italics: true, color: MUTED })],
      }),
    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  const out = path.join(HERE, "Progress_report_WP10_WP11.docx");
  fs.writeFileSync(out, buf);
  console.log("wrote", out, (buf.length / 1024).toFixed(0) + " KB",
              "|", figNo, "figures,", tabNo, "captioned tables");
});
