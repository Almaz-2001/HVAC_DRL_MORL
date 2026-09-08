// Body of the NPU title-selection report. Split from the builder so prose and
// formatting can be edited independently.

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, AlignmentType, Table, TableRow,
  WidthType, PageBreak,
} = require("docx");
const B = require("./build_proposal_docx.js");
const { f, p, h, cell, txt, FULL, DXA, HERE, BLANK, refs,
        bbH, bbM, gb, hyb, spd, m5, m17, rough, transfer, hdrl, band } = B;

const TITLE = "Surrogate Model Selection for Reinforcement-Learning Control of "
  + "Building HVAC Systems: A Step-Size Criterion and a Role-Separated Hybrid "
  + "Architecture";

const body = [];

// ------------------------------------------------------------- header table
function hdrRow(cnLabel, enLabel, value, span) {
  return new TableRow({
    children: [
      cell([cnLabel, enLabel], { width: 2600, bold: true, size: 20 }),
      cell(value, { width: 6700, size: 21 }),
    ],
  });
}

body.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 80 },
  children: [txt("西北工业大学研究生学位论文选题报告表", { bold: true, size: 28 })],
}));
body.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 40 },
  children: [txt("Northwestern Polytechnical University", { size: 22 })],
}));
body.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 240 },
  children: [txt("Graduate Degree Dissertation Title Selection Report Form",
                 { bold: true, size: 24 })],
}));

body.push(new Table({
  width: { size: FULL, type: DXA },
  columnWidths: [2600, 6700],
  rows: [
    hdrRow("学    号", "Student No.", BLANK),
    hdrRow("学    院", "School", "计算机学院  School of Computer Science"),
    hdrRow("学科、专业", "Discipline / Specialty",
           "计算机科学与技术  Computer Science and Technology"),
    hdrRow("姓    名", "Name", "SAPARGALI ALMAZ"),
    hdrRow("学位级别", "Degree", "硕士  Master"),
    hdrRow("导    师", "Supervisor", BLANK),
    hdrRow("培养类别", "Category", "留学研究生  Overseas Postgraduates"),
    hdrRow("报告日期", "Date of Report", "2026 年 9 月  /  September 2026"),
  ],
}));

body.push(new Paragraph({ spacing: { after: 200 }, children: [] }));

// -------------------------------------------------------------- title table
body.push(new Table({
  width: { size: FULL, type: DXA },
  columnWidths: [2600, 6700],
  rows: [
    new TableRow({ children: [
      cell(["论文题目", "Dissertation Title"], { width: 2600, bold: true, size: 20 }),
      cell(TITLE, { width: 6700, size: 21 }),
    ]}),
  ],
}));

body.push(new Paragraph({ spacing: { after: 160 }, children: [] }));

body.push(new Table({
  width: { size: FULL, type: DXA },
  columnWidths: [2600, 1675, 1675, 1675, 1675],
  rows: [
    new TableRow({ children: [
      cell(["论文类型", "Dissertation Type", "(在有关项目下作记号 √)"],
           { width: 2600, bold: true, size: 20 }),
      cell(["基础研究", "Fundamental Research"], { width: 1675, size: 19, align: AlignmentType.CENTER }),
      cell(["应用研究", "Application Research"], { width: 1675, size: 19, align: AlignmentType.CENTER }),
      cell(["工程技术", "Engineering Technology"], { width: 1675, size: 19, align: AlignmentType.CENTER }),
      cell(["跨学科研究", "Research Cross Discipline"], { width: 1675, size: 19, align: AlignmentType.CENTER }),
    ]}),
    new TableRow({ children: [
      cell("", { width: 2600 }),
      cell("", { width: 1675, align: AlignmentType.CENTER }),
      cell("√", { width: 1675, bold: true, size: 26, align: AlignmentType.CENTER }),
      cell("", { width: 1675, align: AlignmentType.CENTER }),
      cell("", { width: 1675, align: AlignmentType.CENTER }),
    ]}),
  ],
}));

body.push(new Paragraph({ children: [new PageBreak()] }));

// ================================================================== 1
body.push(h("1. Research Background", 1));

body.push(p("Buildings account for roughly one third of global final energy use, and "
 + "heating, ventilation and air conditioning (HVAC) equipment is the largest single "
 + "consumer within them. Improving how this equipment is controlled is therefore one "
 + "of the few interventions that can reduce energy demand at scale without replacing "
 + "physical infrastructure. Reinforcement learning (RL) is attractive for this task "
 + "because it learns a control policy directly from interaction, without requiring an "
 + "explicit analytical model of the building, and can in principle balance thermal "
 + "comfort against energy cost in a way that fixed rule-based logic cannot."));

body.push(p("A practical obstacle stands in the way. Training an RL controller requires "
 + "millions of environment interactions. A high-fidelity building emulator written in "
 + "Modelica advances at approximately "
 + f(spd("boptest_rte_http").env_steps_per_sec, 0) + " simulation steps per second on "
 + "ordinary hardware, which places direct training far beyond any practical time "
 + "budget. The response adopted across essentially the whole HVAC RL literature is to "
 + "fit a fast learned surrogate of the building, train the policy against that "
 + "surrogate, and only then evaluate the resulting controller on the emulator or the "
 + "real building. The surrogate plays the role of a digital twin used as a training "
 + "environment."));

body.push(p("This makes one design decision unavoidable: among several candidate "
 + "surrogates, which one should be used for training? In current practice the answer "
 + "is decided by predictive error. Papers on building surrogates report multi-step "
 + "rollout error, error distributions and calibration statistics, and the model with "
 + "the lowest error is carried forward. The heuristic is intuitive and, to the best of "
 + "our knowledge, universal in the building-energy literature. It is also untested. "
 + "Predictive error is measured on held-out trajectories generated by some other "
 + "controller, whereas a training environment is used as a closed-loop transition "
 + "function on states that the learning policy itself induces. Nothing guarantees that "
 + "the two orderings agree."));

body.push(p("Preliminary work carried out for this dissertation shows that they do not. "
 + "On the open BOPTEST benchmark, a physically calibrated grey-box twin predicts far "
 + "better than a compact black-box network — a 24-hour rollout error of "
 + f(gb.rmse_24h_c, 3) + " °C against " + f(bbH.rmse_24h_c, 3) + " °C — yet the policy "
 + "trained on the accurate twin leaves the comfort band for more than 77 % of the "
 + "evaluation horizon on every random seed, while the policy trained on the less "
 + "accurate network is the only single-model controller in the study that is usable. "
 + "Retraining the same black-box architecture on a finer-resolution corpus makes it "
 + "strictly more accurate (" + f(bbM.rmse_24h_c, 3) + " °C) and equally unusable, which "
 + "rules out model class as the explanation."));

body.push(p("The research problem addressed by this dissertation follows directly. If "
 + "predictive accuracy does not predict whether a surrogate will train a usable "
 + "controller, then what property does? The question matters beyond a single case "
 + "study: any project that trains a controller against a learned model of a physical "
 + "system faces the same selection decision, and currently makes it on a criterion that "
 + "has not been validated for that purpose."));

// ------------------------------------------------------------------- 1.1
body.push(h("1.1 Proposed Research Content of the Paper", 2));

body.push(p("The dissertation develops and validates a selection criterion for "
 + "surrogate training environments, together with an architecture that acts on that "
 + "criterion. The work is organised into three connected parts."));

body.push(p("The first part characterises the surrogates themselves. Two families are "
 + "constructed for the same building: a compact black-box neural predictor of the "
 + "temperature and power increments, and a physics-informed grey-box model built on a "
 + "lumped-capacity resistance–capacitance (RC) balance whose unmodelled heat flow is "
 + "supplied by a neural residual term and whose parameters are identified from "
 + "telemetry by a staged inverse procedure. Predictive fidelity is measured over "
 + "multiple horizons, and the corpus resolution is varied so that model class and "
 + "temporal resolution can be separated as explanatory factors."));

body.push(p("The second part measures control utility rather than predictive accuracy. "
 + "The same controller architecture, reward function, training budget and evaluation "
 + "protocol are applied to every surrogate, so that the only variable is the training "
 + "environment. Controllers are then evaluated zero-shot on the live emulator over two "
 + "fourteen-day windows, a peak-heating window and a typical window, using a "
 + "maintenance score that combines time spent outside the comfort band with the "
 + "severity of the excursions. This part also identifies the property that does predict "
 + "utility — the magnitude of the surrogate's per-step state increment, expressed as a "
 + "scale-free roughness of the action-response surface — and isolates it causally with "
 + "a rescaling control that changes the integration step while holding that roughness "
 + "fixed."));

body.push(p("The third part concerns generalisation. Two boundary tests are performed. "
 + "The first asks whether the effect is specific to policy-gradient learning by "
 + "replacing the learned controller with a receding-horizon model predictive control "
 + "(MPC) planner that solves an optimisation at every step. The second asks whether the "
 + "methodology transfers to buildings other than the one it was developed on, using "
 + "three independent hydronic test cases that differ in heat source, heat-transfer "
 + "medium and scale."));

body.push(p("Alongside these, the dissertation develops the control layer itself in a "
 + "multi-objective formulation, so that the trade-off between occupant comfort and "
 + "energy use is exposed as an operator-adjustable preference at run time rather than "
 + "fixed before training, and a role-separated hybrid architecture that resolves the "
 + "conflict between smoothness and fidelity by assigning the two requirements to "
 + "different models instead of compromising within one."));

// ------------------------------------------------------------------- 1.2
body.push(h("1.2 Feasibility of the Research Plan and Implementation of Research Conditions", 2));

body.push(p("The plan is feasible on three grounds: the experimental platform is already "
 + "in place, the computational requirements are modest and measured rather than "
 + "estimated, and a substantial portion of the work has already been completed and "
 + "externally submitted."));

body.push(p("All experiments run on BOPTEST, the open building-emulator benchmark "
 + "developed under IBPSA Project 1. This choice is deliberate: BOPTEST supplies "
 + "Modelica emulators, a built-in reference controller and a fixed set of key "
 + "performance indicators, so results can be reproduced and contested by other groups "
 + "rather than resting on a proprietary building model. The benchmark is deployed "
 + "locally as a containerised service, and the training code runs in its own container "
 + "on the same network, an arrangement that is already operational."));

body.push(p("Computational requirements have been measured, not assumed. The emulator "
 + "advances at " + f(spd("boptest_rte_http").env_steps_per_sec, 0) + " steps per second, "
 + "whereas the black-box surrogate reaches "
 + f(spd("v3_surrogate").env_steps_per_sec, 0) + " and the hybrid environment "
 + f(spd("hybrid_v3_v35_surrogate").env_steps_per_sec, 0) + ", giving speed-ups of "
 + f(spd("v3_surrogate").speedup_vs_boptest_rte, 0) + " and "
 + f(spd("hybrid_v3_v35_surrogate").speedup_vs_boptest_rte, 0) + " times respectively. "
 + "These figures were obtained on a six-core laptop-class processor with 32 GiB of "
 + "memory and no graphics accelerator. A full training cycle that would require "
 + "approximately 66 hours of emulator time completes in well under an hour on the "
 + "surrogate. No specialised hardware is therefore required, which removes the most "
 + "common source of schedule risk in deep-learning projects."));

body.push(p("The software stack consists of Python 3.11, PyTorch and Stable-Baselines3, "
 + "all mature and openly available. The full experimental codebase, the trained "
 + "surrogate checkpoints and the derived evidence artifacts already exist in a version-"
 + "controlled repository, together with a documented reproduction procedure at three "
 + "levels: inspection of committed artifacts, regeneration of every figure and table "
 + "without the emulator, and full re-execution of the experiments. Every numerical "
 + "value reported in this proposal is read from that evidence rather than restated from "
 + "memory."));

body.push(p("Finally, the risk that the topic proves unproductive is low, because the "
 + "central result has already been obtained, replicated across random seeds and written "
 + "up. A manuscript covering the core of the work has been submitted to IEEE Access "
 + "(manuscript ID Access-2026-42535). The remaining work is extension and consolidation "
 + "rather than open-ended exploration."));

// ================================================================== 2
body.push(h("2. Research Status", 1));

body.push(h("2.1 Physics-Based and Grey-Box Building Models", 2));

body.push(p("Reduced-order thermal models of buildings have a long history in control "
 + "engineering. Resistance–capacitance networks represent the building envelope as a "
 + "small set of thermal resistances and capacitances whose parameters are identified "
 + "from measured data. Their appeal is interpretability and data efficiency: the "
 + "identified parameters correspond to physical quantities, and the structure "
 + "constrains extrapolation. Recent work extends these models with learned residual "
 + "terms, neural ordinary differential equations and physics-informed neural networks, "
 + "combining physical structure with the flexibility of learned components. This line "
 + "of work is evaluated almost exclusively on predictive accuracy, which is the "
 + "assumption the present research examines."));

body.push(h("2.2 Learned Surrogates and Deep Learning for Building Dynamics", 2));

body.push(p("Purely learned surrogates trade interpretability for speed and modelling "
 + "capacity. Protocols have been proposed for developing and evaluating neural-network "
 + "surrogates of building simulations, covering sample generation, feature selection, "
 + "architecture choice and validation. Hardware-accelerated implementations push "
 + "inference latency low enough for real-time use. Across this literature, the "
 + "evaluation criterion remains predictive: the surrogate is judged by how closely it "
 + "reproduces held-out simulation output. The possibility that a surrogate might be "
 + "accurate and simultaneously unsuitable as a training environment is not addressed."));

body.push(h("2.3 Reinforcement Learning for HVAC Control", 2));

body.push(p("Reinforcement learning for building control has grown rapidly, with "
 + "surveys documenting applications to setpoint scheduling, supply-temperature control "
 + "and multi-zone coordination. Reported work spans single-agent and multi-agent "
 + "formulations, hierarchical decomposition across timescales, safety-constrained "
 + "learning, and the use of forecast information in the observation vector. Multi-"
 + "objective formulations condition the policy on a preference vector so that a single "
 + "trained policy can serve a range of comfort–energy trade-offs. Almost all of this "
 + "work trains against a simulator or a learned surrogate; the choice of that training "
 + "environment is typically reported as an implementation detail rather than "
 + "investigated as a design variable."));

body.push(h("2.4 Limitations of Current Research", 2));

body.push(p("Four gaps motivate the present work. First, the criterion used to select a "
 + "training surrogate has never been validated against the outcome it is meant to "
 + "predict, namely the quality of the resulting controller. Second, the failure modes of "
 + "a surrogate used in closed loop are poorly characterised: predictive metrics are "
 + "computed on off-policy trajectories and are blind to defects that a controller will "
 + "actively seek out, including a model whose response to a control command has the "
 + "wrong sign. Third, transfer studies usually report whether a method works on a new "
 + "building without separating which component transferred — the model, the calibration "
 + "procedure or the policy — so the boundary of applicability remains unclear. Fourth, "
 + "results are frequently reported for a single random seed, which for policy-gradient "
 + "methods is insufficient to distinguish an effect from initialisation noise."));

// ================================================================== 3
body.push(h("3. Methodology and Roadmap", 1));

body.push(p("The methodology is organised as three experimental blocks with a common "
 + "evaluation protocol, followed by two boundary tests. A discipline of pre-registration "
 + "runs through all of them: each hypothesis, its pass criterion and the actuator "
 + "adapters are written down and committed to version control before the corresponding "
 + "runs are executed, and the commit identifier serves as an audit anchor. This prevents "
 + "the criterion from being adjusted after the outcome is known, which is the principal "
 + "threat to validity in a study whose central claim is negative."));

body.push(p("Block 1 establishes predictive fidelity. Both surrogate families are trained "
 + "on telemetry collected from the emulator, and their multi-horizon rollout error, "
 + "residual distributions and physical consistency are measured. The grey-box model is "
 + "calibrated by a three-stage inverse procedure that aligns telemetry, identifies the "
 + "zone capacitance and fits the residual heads. The corpus resolution is treated as an "
 + "explicit experimental factor so that the effect of temporal resolution can be "
 + "separated from the effect of model class."));

body.push(p("Block 2 measures control utility. A thermostatic proximal-policy-"
 + "optimisation controller is trained on each surrogate under identical conditions and "
 + "evaluated zero-shot on the live emulator over the two seasonal windows. The "
 + "maintenance score combines the fraction of time outside the comfort band with the "
 + "severity of excursions; a value above one marks a controller that cannot be placed in "
 + "service. This block also contains the mechanism experiment: the action-response "
 + "surface of each surrogate is swept, its curvature-to-slope ratio computed, and a "
 + "rescaling control applied that alters the integration step while preserving that "
 + "ratio, so that step size and surface roughness are decoupled."));

body.push(p("Block 3 addresses transfer. The complete pipeline is applied to three "
 + "hydronic test cases that were not used during development. Transfer is decomposed "
 + "into two independent mechanisms and reported separately: whether the calibration "
 + "procedure transfers, measured by the reduction in rollout error after recalibration, "
 + "and whether a frozen controller transfers without retraining, measured against a "
 + "case-specific reference controller."));

body.push(p("Two boundary tests complete the design. The first replaces the learned "
 + "controller with a receding-horizon MPC planner, which never performs gradient ascent "
 + "on policy parameters, in order to test whether the effect is specific to policy-"
 + "gradient learning. The second is a directional-validity audit that samples states and "
 + "asks, for each actuated input separately, whether increasing the command moves the "
 + "zone temperature in the physically correct direction."));

body.push(h("3.2 Technical Implementation Strategy", 2));

body.push(p("The experimental platform is a containerised BOPTEST service exposing the "
 + "emulator through an HTTP interface, with the training code in a separate container on "
 + "the same network. Every environment backend — the emulator itself and each surrogate "
 + "— is placed behind one common interface, so that switching the training environment "
 + "changes a single configuration entry and nothing else in the training code. This is "
 + "what makes the central comparison clean: the controller, reward, budget and "
 + "evaluation are provably identical across backends."));

body.push(p("The black-box surrogate is a compact dual-head network predicting the zone-"
 + "temperature increment and the electrical power draw. The grey-box surrogate combines "
 + "a lumped-capacity balance with a neural residual head and is calibrated in three "
 + "stages against telemetry. The hybrid environment couples them by role: the black-box "
 + "model supplies the rollout dynamics, and the frozen grey-box model is evaluated "
 + "forward-only on the same state–action pair and contributes a penalty proportional to "
 + "the disagreement between the two predictions. The grey-box model never participates in "
 + "the rollout and never enters the policy loss, which is what distinguishes this "
 + "architecture from model ensembling."));

body.push(p("Controllers are trained with proximal policy optimisation. The multi-"
 + "objective variant conditions the policy on a preference vector supplied as part of the "
 + "observation, so a single trained policy covers the whole comfort–energy trade-off and "
 + "the operating point can be moved at run time without retraining. All central "
 + "comparisons are replicated over at least three random seeds, and the censor-weight "
 + "sweep is replicated at every swept value, so that reported differences can be compared "
 + "against seed dispersion rather than asserted."));

body.push(p("The roadmap proceeds in three phases. The first, already largely complete, "
 + "covers surrogate construction, the fidelity–utility comparison and the mechanism "
 + "experiment. The second covers the boundary tests, the multi-objective control layer "
 + "and the seed replication programme. The third covers consolidation: the remaining "
 + "experiments identified below, the dissertation text, and the defence."));

// ================================================================== 4
body.push(h("4. Innovations and Challenges", 1));

body.push(h("4.1 Key Innovations", 2));

body.push(p("The first contribution is a negative result with a constructive replacement. "
 + "The dissertation demonstrates that predictive error, the criterion universally used to "
 + "select a surrogate training environment, is not merely uninformative for that purpose "
 + "but inverted over part of the range, and it identifies a criterion that does work. The "
 + "operative property is the magnitude of the surrogate's per-step state increment, "
 + "expressed as the scale-free roughness of its action-response surface. The measured "
 + "value for the usable surrogate is " + f(rough[0].rel_roughness, 3) + ", against "
 + (Number(rough[1].rel_roughness) / Number(rough[0].rel_roughness)).toFixed(1) + " and "
 + (Number(rough[2].rel_roughness) / Number(rough[0].rel_roughness)).toFixed(1)
 + " times that value for the two surrogates that fail. Crucially, this quantity is "
 + "measured on the surrogate alone, before any controller is trained, which makes it "
 + "usable as a selection criterion rather than a post-hoc explanation."));

body.push(p("The second contribution is the role-separated hybrid architecture. Existing "
 + "practice treats smoothness and fidelity as a trade-off to be resolved within a single "
 + "model. The proposed architecture assigns them to different models: the black-box "
 + "surrogate supplies smooth rollout dynamics, while the frozen physics-informed twin "
 + "acts solely as a forward-only model-disagreement reward censor. This yields the best "
 + "worst-window result in the study, a maintenance score of " + f(hyb.m_s_typ, 3)
 + " on the typical window against " + f(gb.m_s_typ, 3) + " for the accurate twin used "
 + "directly, while retaining a speed-up of "
 + f(spd("hybrid_v3_v35_surrogate").speedup_vs_boptest_rte, 0)
 + " times over the live emulator."));

body.push(p("The third contribution is a diagnostic that predictive metrics cannot "
 + "provide. The directional-validity audit checks, for each actuated input separately, "
 + "whether the surrogate's response to a control command has the correct sign. Applied to "
 + "the finer-resolution surrogate it reveals that the model is inverted in roughly nine "
 + "sampled states out of ten — a hotter supply-temperature command predicting a colder "
 + "zone — reproducibly across four independent training draws, while its rollout error "
 + "improves in every one of them. A monotonicity constraint added to training restores "
 + "the sign on the constrained channel at a still lower rollout error but relocates the "
 + "defect to the fan channel, which establishes that such an audit must be performed per "
 + "input and before controller training."));

body.push(p("The fourth contribution is methodological. Hypotheses and their pass criteria "
 + "are pre-registered with version-control anchors before execution, and outcomes are "
 + "reported as they occur. Of five pre-specified hypotheses, three are falsified, "
 + "including two predictions made by the authors themselves. One planned experiment was "
 + "executed and then invalidated by a defect found in our own planner; that run is "
 + "retained in the record rather than discarded, because deleting it and quietly "
 + "re-running would leave the pre-registration looking untouched when a completed run had "
 + "already been observed. This standard of evidence is uncommon in the applied building-"
 + "control literature and is itself a contribution of the dissertation."));

body.push(h("4.2 Technical Challenges", 2));

body.push(p("The principal difficulty is that the central claim is negative, and negative "
 + "claims are easy to produce by accident. A result showing that an accurate model trains "
 + "a poor controller could equally be explained by a bug in the training pipeline, an "
 + "unlucky seed, or an unfair comparison. The design answers this with three "
 + "countermeasures: a single common interface behind which every backend sits, so that "
 + "nothing but the environment differs; replication across random seeds with dispersion "
 + "reported alongside every headline number; and pre-registered pass criteria. The "
 + "negative control is part of the design rather than an afterthought — a planner running "
 + "on a knowingly sign-inverted model is required to fail, and does."));

body.push(p("A second challenge is disentangling confounded factors. Temporal resolution, "
 + "model class and response-surface roughness co-vary in the natural experiment, so "
 + "observing that a finer-resolution model fails does not by itself identify the cause. "
 + "The rescaling control is the instrument that separates them, and constructing it "
 + "correctly — changing the integration step while provably preserving scale-free "
 + "roughness — is the most delicate part of the experimental design."));

body.push(p("A third challenge is the fragility of the evaluation itself. During the work "
 + "an MPC run produced identical results across three different surrogates, which is "
 + "impossible unless the planner is ignoring them; the cause was a saturation defect in "
 + "our own planner rather than a property of the models. Detecting such failures requires "
 + "sanity checks that are independent of the quantity being measured, and building them "
 + "into the harness is an ongoing requirement rather than a one-off task."));

body.push(p("A fourth challenge concerns the multi-objective layer. The preference-"
 + "conditioned controller is functional but not yet reproducible to the standard the "
 + "dissertation sets elsewhere: extending replication to five seeds gives a maintenance "
 + "score of 0.187 ± 0.078 at the neutral preference point, which fails a pre-specified "
 + "stability test. Establishing whether this reflects an inherent difficulty of "
 + "preference-conditioned training or a correctable defect in the training procedure is a "
 + "specific open task for the remaining period."));

// ================================================================== 5
body.push(h("5. Current Progress", 1));

body.push(p("Substantial preliminary results have already been obtained, and they are the "
 + "basis on which this topic is proposed."));

body.push(p("The experimental platform is complete and operational: a containerised "
 + "BOPTEST deployment, both surrogate families implemented and calibrated, the hybrid "
 + "environment, and a common backend interface behind which they all sit. Performance has "
 + "been benchmarked and is reported above."));

body.push(p("The central comparison is complete. Four training environments were compared "
 + "under identical conditions, with the results shown below. All values are live "
 + "closed-loop measurements on the emulator, averaged over the two seasonal windows, with "
 + "the controllers replicated over three random seeds."));

const T = (rows, headers, widths) => {
  const tot = widths.reduce((a, b) => a + b, 0);
  const w = widths.map((x) => Math.round((x / tot) * FULL));
  return new Table({
    width: { size: FULL, type: DXA },
    columnWidths: w,
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((x, i) =>
        cell(x, { width: w[i], bold: true, shade: "EDF2F7", size: 19,
                  align: AlignmentType.CENTER })) }),
      ...rows.map((r) => new TableRow({ children: r.map((v, i) =>
        cell(String(v), { width: w[i], size: 19,
                          align: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER })) })),
    ],
  });
};

const NAME = {
  "v3 (hourly)": "Black-box surrogate, 1 h step",
  "matched v3 (15-min)": "Black-box surrogate, 15 min step",
  "v3.5 (calibrated)": "Grey-box twin, calibrated",
  "hybrid (v3 rollout + v3.5 censor)": "Role-separated hybrid",
};

body.push(new Paragraph({ spacing: { before: 100, after: 60 },
  indent: { firstLine: 0 },
  children: [txt("Table 1 — Predictive fidelity against control utility.", { size: 20, italics: true })] }));

body.push(T(
  B.scatter.map((r) => [
    NAME[r.controller] ?? r.controller,
    f(r.rmse_24h_c, 3),
    f(r.m_s_peak, 3),
    f(r.m_s_typ, 3),
    Number(r.m_s_typ) < 1 ? "usable" : "not usable",
  ]),
  ["Training environment", "24 h rollout error, °C", "Score, peak window",
   "Score, typical window", "Verdict"],
  [30, 18, 17, 17, 18]));

body.push(new Paragraph({ spacing: { after: 160 }, children: [] }));

body.push(p("The mechanism has been measured rather than hypothesised. The relative "
 + "roughness of the action-response surface is " + f(rough[0].rel_roughness, 3)
 + " for the usable surrogate and " + f(rough[1].rel_roughness, 3) + " and "
 + f(rough[2].rel_roughness, 3) + " for the two that fail, and the rescaling control "
 + "reproduces the collapse while holding roughness fixed, establishing the relationship "
 + "as causal rather than correlational."));

body.push(p("Both boundary tests have been executed. The MPC planner reproduces the same "
 + "inverted ordering as the learned controllers, which falsifies our own pre-registered "
 + "prediction that the effect would be specific to policy-gradient search and widens the "
 + "scope of the finding to optimisation through a surrogate in general. On the transfer "
 + "side, recalibration reduces rollout error by "
 + transfer.map((r) => f(r.rmse_improvement_pct, 1)).join(", ") + " % on the three "
 + "hydronic cases, and the re-identified zone capacitance is consistently 1.89 to 1.95 "
 + "times the baseline value, which is physically consistent with the greater thermal "
 + "inertia of a water circuit. Frozen-policy transfer, by contrast, succeeds on only one "
 + "of the three cases. Transfer therefore resolves into a component-level boundary: the "
 + "calibration pipeline transfers, the policy does not."));

body.push(p("The multi-objective control layer is implemented and evaluated. Widening the "
 + "observation interface from five instantaneous features to seventeen forecast-augmented "
 + "features moves the controller from unusable to usable — rollout error falls from "
 + f(m5.rmse_c, 2) + " to " + f(m17.rmse_c, 2) + " °C, comfort violation from "
 + f(m5.violation_pct, 1) + " % to " + f(m17.violation_pct, 1) + " %, and the maintenance "
 + "score from " + f(m5.m_s, 3) + " to " + f(m17.m_s, 3) + ". This identifies observability, "
 + "not reward shaping, as the binding constraint in that formulation."));

body.push(p("Finally, a manuscript covering the core of this work has been submitted to "
 + "IEEE Access (Access-2026-42535), and earlier results were presented as a conference "
 + "talk at the WCCM–ECCOMAS Congress 2026 in Munich. A reproduction package containing "
 + "the code, the trained checkpoints and the derived evidence has been assembled and "
 + "verified from a clean checkout."));

// ================================================================== 6
body.push(h("6. Dissertation Plan", 1));

body.push(p("October 2026 – December 2026: Chapters 1 and 2 (Problem formulation, "
 + "surrogate construction and predictive fidelity). Consolidate the literature review "
 + "with emphasis on the selection criterion used in prior surrogate work. Write up the "
 + "construction and calibration of both surrogate families, the staged inverse "
 + "identification procedure, and the multi-horizon fidelity evaluation. Complete the "
 + "sensitivity analysis of the calibration stages that is currently only partially "
 + "documented. Milestone: Chapters 1 and 2 drafted; the fidelity evaluation reproducible "
 + "end-to-end from committed artifacts."));

body.push(p("January 2027 – February 2027: Chapter 3 (Control utility and mechanism). "
 + "Write up the central fidelity–utility comparison, the mechanism experiment and the "
 + "rescaling control. Extend the directional-validity audit to the grey-box family, which "
 + "has so far been audited only as an admission gate for the planner. Complete the "
 + "derivative-free planner experiment identified as the natural follow-up to the MPC "
 + "result: the current planner is itself a first-order method through a differentiable "
 + "surrogate, so it separates gradient-based optimisation from other synthesis routes "
 + "rather than separating planning from learning. Milestone: Chapter 3 drafted; the "
 + "derivative-free planner result obtained and reported whichever way it comes out."));

body.push(p("March 2027 – April 2027: Chapter 4 (Architecture, multi-objective control and "
 + "transfer). Write up the role-separated hybrid architecture and the censor-weight "
 + "sensitivity study. Address the open reproducibility issue in the multi-objective layer "
 + "by extending seed replication and investigating whether the dispersion at the neutral "
 + "preference point is inherent or correctable. Write up the three-case transfer study "
 + "and the component-level boundary. Milestone: Chapter 4 drafted; the multi-objective "
 + "stability question resolved and reported."));

body.push(p("May 2027 – June 2027: Chapter 5 and defence. Integrate the chapters, write "
 + "the discussion of threats to validity and the limitations statement, and complete the "
 + "conclusions. Prepare the defence presentation and conduct practice sessions. Submit "
 + "the final dissertation and defend. Milestone: complete dissertation submitted and "
 + "successfully defended by the end of June 2027."));

body.push(p("Two publication milestones run alongside the writing. The IEEE Access "
 + "manuscript is currently under review and any revision required by the reviewers will "
 + "be handled within the first phase. A second manuscript covering the transfer study and "
 + "the directional-validity diagnostic is planned for submission during the third phase."));

// ================================================================== 7
body.push(h("7. References", 1));

const chosen = [
  "Blum2021BOPTEST", "HouEvins2024", "AlSayed2024Review", "Nguyen2024Modelling",
  "Wang2025SafeDRL", "Gao2024Predictive", "Liao2025HDRL", "Savino2025ASHRAE",
  "Hou2024MultiSource", "Byeon2025MaxMinMORL", "RiahiSamani2026OOD",
  "Deng2025MultiAgent", "Alotaibi2025ContextAware", "Mshragi2026FastML",
  "Radac2025OnlineRL", "Mayor2025Parallelized",
];
const picked = chosen.map((k) => refs.find((r) => r.key === k)).filter(Boolean);
const rest = refs.filter((r) => !chosen.includes(r.key)).slice(0, 24 - picked.length);

[...picked, ...rest].forEach((r, i) => {
  const bits = [r.author, "(" + r.year + ")", r.title + ".", r.venue];
  if (r.volume) bits.push(r.volume);
  if (r.pages) bits.push(r.pages);
  body.push(new Paragraph({
    spacing: { after: 60 }, indent: { left: 340, hanging: 340 },
    alignment: AlignmentType.LEFT,
    children: [txt("[" + (i + 1) + "] " + bits.filter(Boolean).join(". ").replace(/\.\./g, ".") + ".",
                   { size: 19 })],
  }));
});

// -------------------------------------------------------------------- output
const doc = new Document({
  styles: { default: { document: { run: { font: "Times New Roman", size: 22 } } } },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1134, right: 1134, bottom: 1134, left: 1418 },
      },
    },
    children: body,
  }],
});

const out = path.join(HERE, "Dissertation_Title_Selection_Report_SAPARGALI.docx");
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(out, buf);
  const words = body.filter((x) => x instanceof Paragraph).length;
  console.log("wrote", path.basename(out), (buf.length / 1024).toFixed(0) + " KB");
});
