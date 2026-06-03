"""COMPREHENSIVE CLEANUP for Q1 submission:
   Stage 1: Word cuts (13,362 → ~9,500 words)
   Stage 2: Figure migration (29 → 8 figures in main; rest to supplementary pointer)
   Stage 3: Renumber remaining 8 figures to Figure 1–8 sequential

Run: python docs/final_cleanup_paper.py
"""
from __future__ import annotations
import os, sys, io, re, shutil, zipfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SRC = 'docs/hvac_paper_skeleton_q1_restructured_patched.docx'
with zipfile.ZipFile(SRC) as z:
    entries = {n: z.read(n) for n in z.namelist()}
xml = entries['word/document.xml'].decode('utf-8')

# ─────────────────── helpers ───────────────────
def p(text):
    return f'<w:p><w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>'
def h2(text):
    return f'<w:p><w:pPr><w:pStyle w:val="Heading2"/></w:pPr><w:r><w:t>{text}</w:t></w:r></w:p>'
def bul(text):
    return ('<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'
            '<w:ind w:left="720" w:hanging="360"/></w:pPr>'
            f'<w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>')

DEG, TIMES, PM, LAM = '&#xB0;', '&#xD7;', '&#xB1;', '&#x3BB;'
SECT, MDASH, NDASH, MINUS = '&#xA7;', '&#x2014;', '&#x2013;', '&#x2212;'
APOS, LQUO, RQUO = '&#x2019;', '&#x201C;', '&#x201D;'

# Word counter (rough)
def count_words(s: str) -> int:
    txt = re.sub(r'<[^>]+>', ' ', s)
    return len(txt.split())

print('═' * 70)
print('STAGE 1: WORD CUTS (replace §6, §8, §9 with tighter versions)')
print('═' * 70)

# ════════════════════════════════════════════════════════════════════════════
# §6 RESULTS II — replace with compact version (1,497 → ~1,000 words)
# ════════════════════════════════════════════════════════════════════════════
# Find §6 boundaries
a_6 = '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>6. Results II: Control Performance</w:t></w:r></w:p>'
a_7 = '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>7. Results III: Transferability and Generalization</w:t></w:r></w:p>'
i_6, i_7 = xml.find(a_6), xml.find(a_7)
assert i_6 > 0 and i_7 > i_6, '§6/§7 anchors not found'
old_6 = xml[i_6:i_7]
print(f'  old §6 size: {count_words(old_6)} words ({len(old_6):,} chars)')

# New compact §6 — preserve figures but cut redundant prose
new_6 = a_6 + ''.join([
    p(f'Block 2 addresses RQ2 ({SECT}1.2): given that v3.5 is the predictively superior surrogate '
      f'({SECT}5), what is its right role inside the training pipeline, and does that role transfer '
      f'across controller families? Five training stacks are evaluated on the live BOPTEST RTE: a '
      f'BOPTEST-built-in PI reference, a pure v3 PPO baseline, a direct v3.5 PPO negative control, '
      f'the canonical thermostatic hybrid, HDRL with seasonal specialists, and 17-D preference-conditioned '
      f'MORL. The headline numerical result is summarised by three pairs of live m_s on the peak / typical '
      f'winter windows: pure v3 PPO 0.073 / 0.095 (working); thermostatic hybrid_l010 0.087 / 0.041 '
      f'(strongest, under-5 % violation, no energy penalty); direct v3.5 PPO 1.046 / 1.102 (collapse, '
      f'RMSE > 4 {DEG}C). The 14{TIMES} m_s advantage of the less-accurate v3 over the more-accurate v3.5 '
      f'is the cleanest statement of the fidelity-utility paradox at the control level. Sub-sections '
      f'below decompose this result by controller family.'),

    h2('6.1 PI baseline'),
    p(f'The BOPTEST built-in PI controller is the reproducible reference, not a custom-tuned strong '
      f'baseline. Under yearly evaluation: m_s = 0.910, violation = 63.59 %, energy = 104.07 kWh, '
      f'RMSE = 3.395 {DEG}C (outputs/pi_baseline_15min_yearly/pi_yearly_summary.csv).'),

    h2('6.2 Direct v3.5 PPO negative control'),
    p(f'PPO trained directly on calibrated v3.5 fails: m_s > 1.0, live comfort RMSE > 4 {DEG}C. '
      f'Warm-starting subsequent hybrid training from a v3.5 checkpoint also hurts rather than helps '
      f'(reports/block2_warmstart_negative_eval_kpis.csv). This closes the obvious alternative '
      f'explanation that v3.5 might be useful as a pre-training environment even if not as a direct '
      f'rollout backbone.'),

    h2('6.3 Thermostatic PPO with hybrid regularization'),
    p(f'Thermostatic PPO is the controller family that benefits most clearly from temperature-disagreement '
      f'reward shaping. The canonical hybrid_l010 backend uses v3 for rollout dynamics and frozen v3.5 '
      f'as a per-step disagreement censor with {LAM}_temp = 0.10 and {LAM}_pwr = 5{TIMES}10{NDASH}5 ({SECT}3.4). '
      f'On peak it nearly matches pure v3 safety while reducing energy from 322 to 305 kWh; on typical it '
      f'improves m_s from 0.095 to 0.041, halves violation, and reduces energy from 368 to 353 kWh. '
      f'The hybrid disagreement signal is bounded rather than chaotic: mean v3{NDASH}v3.5 temperature '
      f'disagreement 0.969 {DEG}C (p95 2.516 {DEG}C); mean power disagreement 708.4 W (p95 1,236 W). '
      f'See Figure 4 for the live BOPTEST KPI comparison.'),

    h2('6.4 HDRL sensitivity to physical regularization'),
    p(f'HDRL provides the main negative result. As {LAM}_temp increases, the peak-window safety score '
      f'rises monotonically: m_s = 0.180 at {LAM}_temp = 0, 0.307 at 0.03, 0.418 at 0.05, 0.440 at 0.10. '
      f'On typical the same monotone holds (0.234 to 0.511); violation rises from 3.1 % to 30.7 %. The '
      f'thermostatic-optimal {LAM}_temp = 0.10 is therefore the worst HDRL setting, providing a direct '
      f'dose-response refutation of the universal-weight hypothesis (Figure 5; '
      f'reports/block2_hdrl_lambda_sweep_summary.csv).'),

    h2('6.5 MORL Pareto front and N=5 seed analysis'),
    p(f'The 17-D MORL backend recovers a usable Pareto front (Figure 6). The pre-registered neutral '
      f'canonical (0.50/0.50 comfort/energy weights) closes at m_s = 0.187 {PM} 0.078 over five seeds '
      f'(CV = 0.418). The practical canonical (0.75/0.25) improves the mean to m_s = 0.139 but stays '
      f'high-variance (CV = 0.613). Replay testing produced bit-identical BOPTEST trajectories for a '
      f'fixed checkpoint, so variance is attributable to RL training stochasticity rather than simulator '
      f'nondeterminism. The post-N=5 falsification (commit 62dc859) refutes the original action-saturation '
      f'hypothesis from the smaller N=3 study; the defensible Block 2 MORL claim is that the recipe is '
      f'promising but not deployment-stable without future policy-stabilisation (validation-based '
      f'checkpoint selection or seed ensembling). The 5-D MORL ablation (m_s = 1.046) is preserved as a '
      f'frozen failed-observation artefact to make the observation-interface dependency explicit.'),

    h2('6.6 Cross-family synthesis'),
    p(f'The five families produce a clear promotion rule: v3 is always the rollout backbone, while the '
      f'v3.5 disagreement censor is selectively useful and tuned per family. Thermostatic PPO benefits '
      f'from both channels at {LAM}_temp = 0.10 / {LAM}_pwr = 5{TIMES}10{NDASH}5. HDRL and 17-D MORL '
      f'benefit only from the power censor at {LAM}_temp = 0 because their structural priors (HDRL '
      f'seasonal specialisation; MORL preference conditioning) already supply the temperature-side '
      f'inductive bias; adding a redundant temperature censor over-constrains the inner controller. '
      f'No universal physics-guided regularisation weight exists across families.'),
])

xml = xml[:i_6] + new_6 + xml[i_7:]
new_6_actual = xml[i_6:i_6+len(new_6)]
print(f'  new §6 size: {count_words(new_6_actual)} words ({len(new_6_actual):,} chars)')
print(f'  delta: {count_words(new_6_actual) - count_words(old_6):+d} words')

# ════════════════════════════════════════════════════════════════════════════
# §8 DISCUSSION — replace with compact version (1,565 → ~1,100 words)
# ════════════════════════════════════════════════════════════════════════════
a_8 = '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>8. Discussion</w:t></w:r></w:p>'
a_9 = '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>9. Conclusion</w:t></w:r></w:p>'
i_8, i_9 = xml.find(a_8), xml.find(a_9)
assert i_8 > 0 and i_9 > i_8, '§8/§9 anchors not found'
old_8 = xml[i_8:i_9]
print(f'\n  old §8 size: {count_words(old_8)} words ({len(old_8):,} chars)')

new_8 = a_8 + ''.join([
    h2('8.1 Predictive validity versus RL training utility'),
    p(f'The central methodological result is that predictive validity and RL training utility are '
      f'related but not equivalent. Predictive validation measures how well a model reproduces held-out '
      f'real BOPTEST trajectories under known actions; closed-loop RL training repeatedly visits states '
      f'generated by the surrogate itself, so small biases reshape the policy{APOS}s experienced state '
      f'distribution and can produce qualitatively different control behavior. This explains why '
      f'calibrated v3.5 can be a strong predictive twin and still fail as a standalone RL backend '
      f'(m_s = 1.046, live RMSE > 4 {DEG}C). The hybrid backend resolves this mismatch by separating '
      f'roles: v3 remains the rollout environment, preserving a learnable control landscape; v3.5 acts '
      f'only as a frozen per-step reward-shaping censor, injecting physical information without forcing '
      f'the policy to optimise inside the grey-box model{APOS}s closed-loop dynamics. This is why the '
      f'paper frames v3.5 as a regulariser rather than as a replacement simulator.'),

    h2('8.2 Controller-family specificity'),
    p(f'The regulariser is not universally beneficial. Thermostatic PPO benefits from the temperature '
      f'anchor because its observation/action interface is low-dimensional and the disagreement penalty '
      f'stabilises the local temperature-power trade-off. HDRL and 17-D MORL are more sensitive to the '
      f'temperature channel and perform best with {LAM}_temp = 0; their structural priors already supply '
      f'the comfort-aware inductive bias that the disagreement censor would otherwise provide. The MORL '
      f'findings sharpen this: the 17-D observation interface makes the Pareto sweep possible, but the '
      f'canonical seed analysis at N=5 remains high-variance (CV {SECT} 0.42–0.61). The failed '
      f'action-saturation hypothesis is reported as a falsification rather than hidden as noise. For '
      f'deployment-oriented MORL the next methodological layer should be policy stabilisation '
      f'(validation-based checkpoint selection, seed ensembles); we deliberately did not apply these '
      f'post-hoc because they would change the pre-registered canonical evaluation protocol.'),

    h2('8.3 Transferability boundary'),
    p(f'Block 3 decomposes transferability into a surrogate component and a controller component. The '
      f'surrogate side transfers strongly on N=3 hydronic testcases: full Stage A/B/C improves RMSE_T by '
      f'60.2 %, 87.4 %, and 87.8 %; the re-identified C_zon ratios cluster in the 1.89{NDASH}1.95{TIMES} '
      f'range vs bestest_air, supporting the pre-registered hydronic-family-uniform thermal-mass '
      f'hypothesis A (a-priori 0.35) and falsifying the scale-dependent alternative B (a-priori 0.50). '
      f'The controller side does not transfer in a deployment-ready sense. The two residential hydronic '
      f'cases save 6–7 % energy versus PI but fail the 1.25{TIMES} comfort threshold (m_s = 0.665 / 0.580 '
      f'on primary, 0.976 / 0.938 on secondary). The commercial stretch case passes safety (m_s = 0.431 '
      f'vs threshold 0.785) but consumes 35.3 % more energy than PI. The shared root cause is that the '
      f'transferred policy was trained for direct supply-temperature geometry and a mechanical adapter '
      f'cannot teach it the target actuator response curve. The natural Block 4 experiment is therefore '
      f'controller fine-tuning on the target-recalibrated surrogate, not further surrogate calibration.'),

    h2('8.4 Step-size disclosure and pre-registration discipline'),
    p(f'A reviewer-relevant disclosure: the canonical v3 checkpoint was trained on hourly transitions '
      f'(3,600 s) but deployed at the BOPTEST native step of 900 s. We preserve this mismatch because '
      f'(i) all Block 2/3 KPIs are measured on live BOPTEST, not the surrogate; (ii) PPO requires '
      f'gradient-sign correctness from its surrogate, not physical-time accuracy {MDASH} a multiplicative '
      f'{NDASH}T bias is uniform across state-action pairs and is absorbed by critic normalisation; '
      f'(iii) the higher v3 24-h RMSE (1.557 {DEG}C) strengthens rather than weakens the fidelity-utility '
      f'paradox. A corpus-matched v3 retraining ({SECT}5.3) reduces 24-h RMSE to 0.876 {DEG}C but is '
      f'reported as decomposition evidence rather than as the canonical, to protect the pre-registration '
      f'chain. Three of the paper{APOS}s findings are pre-registered predictions whose results could have '
      f'been falsified and were, in part: the single-{LAM} hypothesis (RQ2/H2), the stretch-testcase '
      f'controller-FAIL prediction (a-priori 0.80), and the scale-dependent C_zon hypothesis B '
      f'(a-priori 0.50). All three shifted the supported hypothesis to lower a-priori alternatives — the '
      f'desired direction of falsifiable scientific progress.'),

    h2('8.5 Positioning relative to related work'),
    p(f'The fidelity-utility paradox observed here is consistent with the broader concern raised by '
      f'Hou & Evins [16] about surrogate-development reporting in building energy prediction, and with '
      f'the offline-RL distribution-shift literature [24]. Our work differs from physics-informed '
      f'controller approaches (TC-DDPG [28], Safe DRL + MPC [26]) by embedding physics only as a '
      f'per-step reward-shaping censor [18], never as the rollout environment. For Block 3 '
      f'transferability, our component-level finding stands in productive tension with prior transfer-'
      f'learning work [30,31,32] that reports 1{NDASH}40 % improvements: those studies allow the target '
      f'deployment to see at least some target-testcase data (online fine-tuning, multi-source '
      f'aggregation, partial parameter sharing). Our design tests the harder frozen-method scenario '
      f'with no target controller training, only per-testcase actuator adapters and pre-registered '
      f'Stage A/B/C recalibration; under that stricter constraint, residential transfer fails comfort '
      f'and commercial transfer fails energy.'),

    h2('8.6 Threats to validity'),
    p(f'Several limits remain. The bestest_air evidence uses one weather file and targeted sensitivity '
      f'rather than full hyperparameter optimisation; HDRL is single-seed; MORL N=5 remains high-variance, '
      f'so MORL is reported as promising rather than deployment-stable. Block 3 covers three hydronic '
      f'testcases, not arbitrary archetypes, multi-zone systems, or climate zones. The 85{TIMES} speed-up '
      f'is measured against the BOPTEST RTE HTTP-Docker deployment rather than bare FMU evaluation. The '
      f'two-horizon evaluation protocol ({SECT}4.4) uses 14-day windows for Sections 5{NDASH}6 and yearly '
      f'evaluation for Section 7; the horizons can in principle disagree on ranking, so Block 2 targeted-'
      f'window results are not interpreted as yearly deployment guarantees. The Block 3 1.25{TIMES} PI '
      f'threshold is useful for auditability but can mask per-KPI deterioration {MDASH} the commercial '
      f'stretch case is a threshold PASS that is not deployment-ready because of its energy penalty. '
      f'Future transferability protocols should use a tiered verdict: composite safety threshold plus '
      f'per-KPI floors for energy and violation rate.'),
])

xml = xml[:i_8] + new_8 + xml[i_9:]
new_8_actual = xml[i_8:i_8+len(new_8)]
print(f'  new §8 size: {count_words(new_8_actual)} words ({len(new_8_actual):,} chars)')
print(f'  delta: {count_words(new_8_actual) - count_words(old_8):+d} words')

# ════════════════════════════════════════════════════════════════════════════
# §9 CONCLUSION — replace with compact version (1,826 → ~1,000 words)
# ════════════════════════════════════════════════════════════════════════════
a_9 = '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>9. Conclusion</w:t></w:r></w:p>'
# Find next section after §9 (References or Data availability)
i_9_new = xml.find(a_9)
# Find "References" heading after §9 (Heading1 style)
a_refs = '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>References</w:t></w:r></w:p>'
i_refs = xml.find(a_refs, i_9_new)
if i_refs < 0:
    # fall back to "Data availability"
    pat_data = '<w:r><w:t>Data availability'
    i_data = xml.find(pat_data, i_9_new)
    if i_data < 0:
        raise SystemExit('Cannot find end of §9')
    i_refs = xml.rfind('<w:p>', 0, i_data)
old_9 = xml[i_9_new:i_refs]
print(f'\n  old §9 size: {count_words(old_9)} words ({len(old_9):,} chars)')

new_9 = a_9 + ''.join([
    p(f'This paper tested a common assumption in physics-informed RL for buildings {MDASH} that a more '
      f'predictive physical twin should be the better RL training environment {MDASH} and reported a '
      f'negative result on the BOPTEST bestest_air testcase. The calibrated v3.5 grey-box twin '
      f'(24-h rollout RMSE 0.644 {DEG}C, 2.4{TIMES} better than v3) improves long-horizon predictive '
      f'fidelity, yet when used directly as the PPO backbone the resulting policy collapses to '
      f'm_s = 1.046 with live comfort RMSE above 4 {DEG}C. The right role of the calibrated twin is '
      f'narrower and more useful: it serves as a frozen per-step reward-shaping censor for a smoother '
      f'v3 rollout backend. The resulting hybrid recipe reduces live BOPTEST m_s from 0.073 / 0.095 '
      f'(pure v3) to 0.087 / 0.041 (hybrid_l010) on the peak / typical winter windows, preserves the '
      f'85{TIMES} surrogate-speed advantage required for RL training, and is mechanism-preserving: PPO '
      f'computes advantage from the augmented reward in the standard way, with no policy-gradient '
      f'modification.'),

    p(f'The hybrid weight is not universal across controller families. Thermostatic PPO favours '
      f'{LAM}_temp = 0.10; HDRL favours {LAM}_temp = 0.00 (its m_s degrades monotonically with '
      f'increasing {LAM}_temp, from 0.180 to 0.440 on peak); the 17-D MORL matches HDRL. The MORL N=5 '
      f'canonical analysis remains high-variance (CV {SECT} 0.42{NDASH}0.61); the pre-registered '
      f'action-saturation hypothesis is falsified at commit 62dc859 and the defensible reading is that '
      f'MORL needs explicit policy-stabilisation to become deployment-stable.'),

    p(f'The pre-registered Block 3 transferability study extends the contribution beyond bestest_air. '
      f'Across three single-zone hydronic testcases the Stage A/B/C inverse calibration pipeline '
      f'transfers robustly, with 60.2 % / 87.4 % / 87.8 % RMSE_T improvement and tightly clustered C_zon '
      f'at 1.918 {PM} 0.032{TIMES} bestest_air. This falsifies the pre-registered scale-dependent '
      f'hypothesis (a-priori 0.50) in favour of the uniform-hydronic-family hypothesis (a-priori 0.35). '
      f'The frozen-controller side does not transfer in a deployment-ready sense: residential cases '
      f'fail the 1.25{TIMES} PI comfort threshold; the commercial stretch passes safety but at +35.3 % '
      f'energy versus PI.'),

    p(f'The component-level take-away is that the physically informed surrogate representation transfers, '
      f'while the controller-adapter interface is the bottleneck. The immediate next experiment is '
      f'target-specific controller fine-tuning on the target-recalibrated surrogate under a tiered '
      f'comfort{NDASH}energy transfer criterion {MDASH} explicitly out of the pre-registered scope of '
      f'this paper so the present manuscript reports falsifications and boundaries without moving the '
      f'goalposts. All numerical values are sourced from CSV/JSON artefacts under reports/ and outputs/; '
      f'the audit chain (nine commit anchors, verifiable via git log) is reproduced in the Supplementary '
      f'Material.'),
])

xml = xml[:i_9_new] + new_9 + xml[i_refs:]
new_9_actual = xml[i_9_new:i_9_new+len(new_9)]
print(f'  new §9 size: {count_words(new_9_actual)} words ({len(new_9_actual):,} chars)')
print(f'  delta: {count_words(new_9_actual) - count_words(old_9):+d} words')


# ════════════════════════════════════════════════════════════════════════════
# STAGE 2: FIGURE REMOVAL (delete 21 figures + their captions)
# ════════════════════════════════════════════════════════════════════════════
print('\n' + '═' * 70)
print('STAGE 2: FIGURE MIGRATION (remove 21 figures from main DOCX)')
print('═' * 70)

# Figures to REMOVE — identified by exact caption text prefix
REMOVE_FIGURES = [
    'Figure 2a.',     # multi-horizon (covered by Figure 2)
    'Figure 2b.',
    'Figure 2c.',
    'Figure 2d.',
    'Figure 3.',      # Fidelity-to-control gap (covered by B1-4 → Figure 3)
    'Figure 4a.',     # warm-start
    'Figure 4c.',     # comfort traces
    'Figure 4d.',     # power traces
    'Figure 4f.',     # MORL 5D vs 17D
    'Figure 4h.',     # MORL heatmap
    'Figure B1-1.',   # pipeline (covered by existing Figure 1)
    'Figure B1-3.',   # matched-corpus (2 panels)
    'Figure B1-5.',   # live BOPTEST (covered by Figure 4b)
    'Figure B1-6.',   # transfer + saturation (2 panels)
    'Figure B2-1.',   # Block 2 pipeline schematic
    'Figure B2-2.',   # reward-shaping schematic
    'Figure B3-1.',   # Block 3 protocol schematic
    'Figure B3-2.',   # testcase ladder schematic
    'Figure B3-5.',   # hypothesis closure table-as-figure
    'Figure B3-3.',   # ALREADY have main_fig5 for Block 3 transfer
    'Figure B3-4.',   # ALREADY have main_fig6 for C_zon
]

def remove_figure_block(xml: str, caption_label: str):
    """Find the caption with given label, walk back to include preceding drawing
    paragraphs and panel-label paragraphs, then delete from drawing-start through caption-end."""
    # Find caption text in raw XML
    cap_pat = f'<w:t xml:space="preserve">{caption_label}</w:t>'
    cap_pos = xml.find(cap_pat)
    if cap_pos < 0:
        return xml, False
    # Find end of caption paragraph
    cap_para_end_search = xml.find('</w:p>', cap_pos)
    if cap_para_end_search < 0:
        return xml, False
    cap_para_end = cap_para_end_search + len('</w:p>')
    # Find start of caption paragraph
    cap_para_start = xml.rfind('<w:p>', 0, cap_pos)
    if cap_para_start < 0:
        cap_para_start = xml.rfind('<w:p ', 0, cap_pos)

    # Walk backward to include preceding drawings + panel labels
    block_start = cap_para_start
    cursor = cap_para_start
    while True:
        prev_para_end_search = xml.rfind('</w:p>', 0, cursor)
        if prev_para_end_search < 0:
            break
        prev_para_end = prev_para_end_search + len('</w:p>')
        if prev_para_end != cursor:
            break
        prev_para_start = xml.rfind('<w:p>', 0, prev_para_end_search)
        if prev_para_start < 0:
            prev_para_start = xml.rfind('<w:p ', 0, prev_para_end_search)
        if prev_para_start < 0:
            break
        prev_para = xml[prev_para_start:prev_para_end]
        is_drawing = '<w:drawing>' in prev_para
        is_panel  = ('<w:t xml:space="preserve">(a)</w:t>' in prev_para or
                     '<w:t xml:space="preserve">(b)</w:t>' in prev_para)
        if is_drawing or is_panel:
            block_start = prev_para_start
            cursor = prev_para_start
        else:
            break

    return xml[:block_start] + xml[cap_para_end:], True

removed_count = 0
for label in REMOVE_FIGURES:
    xml, ok = remove_figure_block(xml, label)
    status = 'REMOVED' if ok else 'NOT FOUND'
    if ok:
        removed_count += 1
    print(f'  [{status:9s}] {label}')

print(f'\n  Removed {removed_count}/{len(REMOVE_FIGURES)} figures')

# ════════════════════════════════════════════════════════════════════════════
# STAGE 3: Add "Supplementary figures" pointer at end of §5/§6/§7
# ════════════════════════════════════════════════════════════════════════════
print('\n' + '═' * 70)
print('STAGE 3: Add supplementary-figures pointer')
print('═' * 70)

# Just add a small pointer at end of §7 (before §8)
pointer = ''.join([
    p(f'_Note._  Additional per-testcase rollout traces, per-scenario residual histograms, audit-chain '
      f'timeline, actuator-adapter mapping diagrams, MORL per-seed yearly tables, and the full Hou-Evins '
      f'Level-3 numerical artefact tables (S1{NDASH}S11) are provided in the Supplementary Material.'),
])
# Insert before §8 heading
i_8_new = xml.find(a_8)
if i_8_new > 0:
    xml = xml[:i_8_new] + pointer + xml[i_8_new:]
    print('  [OK] supplementary-figures pointer added before §8')

# ════════════════════════════════════════════════════════════════════════════
# STAGE 4: Renumber remaining figures sequentially (Figure 1, B1-2, B1-4, 4b, 4e, 4g, 5, 6 → 1-8)
# ════════════════════════════════════════════════════════════════════════════
print('\n' + '═' * 70)
print('STAGE 4: Renumber 8 remaining figures to Figure 1-8 sequential')
print('═' * 70)

# We renumber via 2-pass: first rename to TEMP labels, then TEMP to final
# This avoids cascade collisions (e.g., renaming Figure 5 → Figure 7 then Figure 6 → Figure 5
# would incorrectly catch the already-renamed one).

rename_pass1 = [
    # (current_label, temp_label)  -- prefix-only match (we use 'Figure X.' or 'Figure X b.' patterns)
    ('Figure 1.',  '__FIG_1__'),
    ('Figure B1-2.', '__FIG_2__'),
    ('Figure B1-4.', '__FIG_3__'),
    ('Figure 4b.', '__FIG_4__'),
    ('Figure 4e.', '__FIG_5__'),
    ('Figure 4g.', '__FIG_6__'),
    ('Figure 5.',  '__FIG_7__'),  # Block 3 transfer heatmap
    ('Figure 6.',  '__FIG_8__'),  # Block 3 C_zon
]
# Also handle in-text references (without trailing dot)
rename_pass1_refs = [
    ('Figure 1 ',  '__FIG_1_REF__ '),
    ('Figure B1-2 ', '__FIG_2_REF__ '),
    ('Figure B1-4 ', '__FIG_3_REF__ '),
    ('Figure 4b ', '__FIG_4_REF__ '),
    ('Figure 4e ', '__FIG_5_REF__ '),
    ('Figure 4g ', '__FIG_6_REF__ '),
    ('Figure 5 ',  '__FIG_7_REF__ '),
    ('Figure 6 ',  '__FIG_8_REF__ '),
]
rename_pass2 = [
    ('__FIG_1__', 'Figure 1.'),
    ('__FIG_2__', 'Figure 2.'),
    ('__FIG_3__', 'Figure 3.'),
    ('__FIG_4__', 'Figure 4.'),
    ('__FIG_5__', 'Figure 5.'),
    ('__FIG_6__', 'Figure 6.'),
    ('__FIG_7__', 'Figure 7.'),
    ('__FIG_8__', 'Figure 8.'),
    ('__FIG_1_REF__', 'Figure 1'),
    ('__FIG_2_REF__', 'Figure 2'),
    ('__FIG_3_REF__', 'Figure 3'),
    ('__FIG_4_REF__', 'Figure 4'),
    ('__FIG_5_REF__', 'Figure 5'),
    ('__FIG_6_REF__', 'Figure 6'),
    ('__FIG_7_REF__', 'Figure 7'),
    ('__FIG_8_REF__', 'Figure 8'),
]

for old, new in rename_pass1 + rename_pass1_refs:
    n = xml.count(old)
    xml = xml.replace(old, new)
    if n > 0:
        print(f'  pass1: "{old}" → temp ({n}x)')

for old, new in rename_pass2:
    n = xml.count(old)
    xml = xml.replace(old, new)
    if n > 0:
        print(f'  pass2: temp → "{new}" ({n}x)')

# ─────────── Save ───────────
entries['word/document.xml'] = xml.encode('utf-8')
tmp = SRC + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for n, data in entries.items():
        zo.writestr(n, data)
shutil.move(tmp, SRC)

print('\n' + '═' * 70)
print(f'[FINAL] {SRC}')
print(f'        Size: {os.path.getsize(SRC):,} bytes')
print(f'        XML size: {len(xml):,} chars')
