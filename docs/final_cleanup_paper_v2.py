"""SAFE comprehensive cleanup for Q1 submission:
   Stage 1: Word cuts (replace §6, §8, §9 prose ONLY — preserve Data availability + Supplementary)
   Stage 2: Figure removal (remove unwanted drawings + captions)
   Stage 3: Renumber remaining figures to Figure 1-8 sequential

Critical fixes vs v1:
   - §9 cut now stops at "Data availability" paragraph, preserving everything after
   - Figure removal also covers §5 Results I figures (Figure 2a-2d, Figure 4a-4h)
"""
from __future__ import annotations
import os, sys, io, re, shutil, zipfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SRC = 'docs/hvac_paper_skeleton_q1_restructured_patched.docx'
with zipfile.ZipFile(SRC) as z:
    entries = {n: z.read(n) for n in z.namelist()}
xml = entries['word/document.xml'].decode('utf-8')

def p(t): return f'<w:p><w:r><w:t xml:space="preserve">{t}</w:t></w:r></w:p>'
def h2(t): return f'<w:p><w:pPr><w:pStyle w:val="Heading2"/></w:pPr><w:r><w:t>{t}</w:t></w:r></w:p>'

DEG, TIMES, PM, LAM = '&#xB0;', '&#xD7;', '&#xB1;', '&#x3BB;'
SECT, MDASH, NDASH, MINUS = '&#xA7;', '&#x2014;', '&#x2013;', '&#x2212;'
APOS = '&#x2019;'; LQUO, RQUO = '&#x201C;', '&#x201D;'

def wc(s):
    return len(re.sub(r'<[^>]+>', ' ', s).split())

print('═' * 70 + '\nSTAGE 1: Word cuts (preserve Data availability + Supplementary)\n' + '═' * 70)

# ─── §6 replacement (same as v1) ───
a_6 = '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>6. Results II: Control Performance</w:t></w:r></w:p>'
a_7 = '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>7. Results III: Transferability and Generalization</w:t></w:r></w:p>'
i_6, i_7 = xml.find(a_6), xml.find(a_7)
old_6 = xml[i_6:i_7]
print(f'§6 OLD: {wc(old_6)} words')

new_6 = a_6 + ''.join([
    p(f'Block 2 addresses RQ2 ({SECT}1.2): given that v3.5 is the predictively superior surrogate, what '
      f'is its right role inside the training pipeline, and does that role transfer across controller '
      f'families? Five training stacks are evaluated on the live BOPTEST RTE: a built-in PI reference, '
      f'a pure v3 PPO baseline, a direct v3.5 PPO negative control, the canonical thermostatic hybrid, '
      f'HDRL with seasonal specialists, and 17-D preference-conditioned MORL. The headline result is '
      f'summarised by three pairs of live m_s on peak / typical winter windows: pure v3 PPO 0.073 / 0.095 '
      f'(working baseline); thermostatic hybrid_l010 0.087 / 0.041 (strongest, under-5 % violation, no '
      f'energy penalty); direct v3.5 PPO 1.046 / 1.102 (collapse, RMSE > 4 {DEG}C). The 14{TIMES} m_s '
      f'advantage of the less-accurate v3 over the more-accurate v3.5 is the cleanest statement of the '
      f'fidelity-utility paradox at the control level.'),
    h2('6.1 PI baseline'),
    p(f'The BOPTEST built-in PI controller is the reproducible reference, not a custom-tuned strong '
      f'baseline. Under yearly evaluation: m_s = 0.910, violation = 63.59 %, energy = 104.07 kWh, '
      f'RMSE = 3.395 {DEG}C.'),
    h2('6.2 Direct v3.5 PPO negative control'),
    p(f'PPO trained directly on calibrated v3.5 fails: m_s > 1.0, live comfort RMSE > 4 {DEG}C. '
      f'Warm-starting subsequent hybrid training from a v3.5 checkpoint also hurts rather than helps, '
      f'closing the alternative explanation that v3.5 might be useful as a pre-training environment.'),
    h2('6.3 Thermostatic PPO with hybrid regularization'),
    p(f'Thermostatic PPO is the controller family that benefits most clearly from temperature-disagreement '
      f'reward shaping. The canonical hybrid_l010 backend uses v3 for rollout dynamics and frozen v3.5 '
      f'as a per-step disagreement censor with {LAM}_temp = 0.10 and {LAM}_pwr = 5{TIMES}10{NDASH}5 ({SECT}3.4). '
      f'On peak it nearly matches pure v3 safety while reducing energy from 322 to 305 kWh; on typical '
      f'it improves m_s from 0.095 to 0.041, halves violation, and reduces energy from 368 to 353 kWh. '
      f'The disagreement signal is bounded: mean v3{NDASH}v3.5 temperature disagreement 0.969 {DEG}C '
      f'(p95 2.516 {DEG}C); mean power disagreement 708.4 W (p95 1,236 W). See Figure 4 for live BOPTEST KPIs.'),
    h2('6.4 HDRL sensitivity to physical regularization'),
    p(f'HDRL provides the main negative result. As {LAM}_temp increases, peak m_s rises monotonically: '
      f'0.180 at {LAM}_temp = 0, 0.307 at 0.03, 0.418 at 0.05, 0.440 at 0.10. On typical the same monotone '
      f'holds (0.234 to 0.511); violation rises from 3.1 % to 30.7 %. The thermostatic-optimal '
      f'{LAM}_temp = 0.10 is the worst HDRL setting, providing dose-response refutation of the '
      f'universal-weight hypothesis (Figure 5).'),
    h2('6.5 MORL Pareto front and N=5 seed analysis'),
    p(f'The 17-D MORL backend recovers a usable Pareto front (Figure 6). The pre-registered neutral '
      f'canonical (0.50/0.50) closes at m_s = 0.187 {PM} 0.078 over five seeds (CV = 0.418). The '
      f'practical canonical (0.75/0.25) improves the mean to m_s = 0.139 but stays high-variance '
      f'(CV = 0.613). Replay produced bit-identical BOPTEST trajectories for fixed checkpoints, so '
      f'variance is attributable to RL training stochasticity. The post-N=5 falsification (commit 62dc859) '
      f'refutes the original action-saturation hypothesis from N=3; the defensible Block 2 MORL claim '
      f'is that the recipe is promising but not deployment-stable without policy stabilisation. The 5-D '
      f'MORL ablation (m_s = 1.046) is preserved as a frozen failed-observation artefact.'),
    h2('6.6 Cross-family synthesis'),
    p(f'The five families produce a clear promotion rule: v3 is always the rollout backbone; the v3.5 '
      f'disagreement censor is selectively useful per family. Thermostatic PPO benefits from both '
      f'channels at {LAM}_temp = 0.10 / {LAM}_pwr = 5{TIMES}10{NDASH}5. HDRL and 17-D MORL benefit only '
      f'from the power censor at {LAM}_temp = 0 because their structural priors already supply the '
      f'temperature-side inductive bias. No universal physics-guided regularisation weight exists across '
      f'families.'),
])
xml = xml[:i_6] + new_6 + xml[i_7:]
print(f'§6 NEW: {wc(new_6)} words ({wc(new_6) - wc(old_6):+d})')

# ─── §8 replacement (same as v1) ───
a_8 = '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>8. Discussion</w:t></w:r></w:p>'
a_9 = '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>9. Conclusion</w:t></w:r></w:p>'
i_8, i_9 = xml.find(a_8), xml.find(a_9)
old_8 = xml[i_8:i_9]
print(f'\n§8 OLD: {wc(old_8)} words')

new_8 = a_8 + ''.join([
    h2('8.1 Predictive validity versus RL training utility'),
    p(f'The central methodological result is that predictive validity and RL training utility are '
      f'related but not equivalent. Predictive validation measures how well a model reproduces held-out '
      f'BOPTEST trajectories under known actions; closed-loop RL training repeatedly visits states '
      f'generated by the surrogate itself, so small biases reshape the policy{APOS}s experienced state '
      f'distribution and can produce qualitatively different behavior. This explains why calibrated v3.5 '
      f'is a strong predictive twin yet fails as a standalone RL backend (m_s = 1.046, live RMSE > 4 {DEG}C). '
      f'The hybrid backend resolves this by separating roles: v3 remains the rollout environment, '
      f'preserving a learnable control landscape; v3.5 acts only as a frozen per-step reward-shaping '
      f'censor, injecting physical information without forcing the policy to optimise inside the '
      f'grey-box closed-loop dynamics.'),
    h2('8.2 Controller-family specificity'),
    p(f'The regulariser is not universally beneficial. Thermostatic PPO benefits from the temperature '
      f'anchor because the disagreement penalty stabilises the local temperature-power trade-off. HDRL '
      f'and 17-D MORL are more sensitive to the temperature channel and perform best with {LAM}_temp = 0; '
      f'their structural priors already supply the comfort-aware inductive bias. The MORL canonical '
      f'seed analysis at N=5 remains high-variance (CV {SECT} 0.42{NDASH}0.61). The failed action-saturation '
      f'hypothesis is reported as a falsification rather than hidden as noise. For deployment-oriented '
      f'MORL the next methodological layer should be policy stabilisation (validation-based checkpoint '
      f'selection, seed ensembles); we deliberately did not apply these post-hoc because they would '
      f'change the pre-registered evaluation protocol.'),
    h2('8.3 Transferability boundary'),
    p(f'Block 3 decomposes transferability into a surrogate component and a controller component. The '
      f'surrogate side transfers strongly on N=3 hydronic testcases: full Stage A/B/C improves RMSE_T '
      f'by 60.2 %, 87.4 %, and 87.8 %; the re-identified C_zon clusters in 1.89{NDASH}1.95{TIMES} bestest_air, '
      f'supporting the pre-registered uniform-hydronic-family hypothesis A (a-priori 0.35) and '
      f'falsifying scale-dependent alternative B (a-priori 0.50). The controller side does not transfer '
      f'in a deployment-ready sense: residential cases save 6{NDASH}7 % energy versus PI but fail the '
      f'1.25{TIMES} comfort threshold; the commercial stretch passes safety (m_s = 0.431 vs threshold '
      f'0.785) but consumes 35.3 % more energy than PI. The shared root cause is that the transferred '
      f'policy was trained for direct supply-temperature geometry and a mechanical adapter cannot teach '
      f'it the target actuator response curve. The natural Block 4 experiment is controller fine-tuning '
      f'on the target-recalibrated surrogate, not further surrogate calibration.'),
    h2('8.4 Step-size disclosure and pre-registration discipline'),
    p(f'A reviewer-relevant disclosure: the canonical v3 checkpoint was trained on hourly transitions '
      f'(3,600 s) but deployed at the BOPTEST native step of 900 s. We preserve this mismatch because '
      f'(i) all Block 2/3 KPIs are measured on live BOPTEST, not the surrogate; (ii) PPO requires '
      f'gradient-sign correctness from its surrogate, not physical-time accuracy {MDASH} a multiplicative '
      f'{NDASH}T bias is absorbed by critic normalisation; (iii) the higher v3 24-h RMSE (1.557 {DEG}C) '
      f'strengthens the fidelity-utility paradox. A corpus-matched v3 retraining ({SECT}5.3) reduces 24-h '
      f'RMSE to 0.876 {DEG}C but is reported as decomposition evidence, not as the canonical, to protect '
      f'the pre-registration chain. Three findings are pre-registered predictions whose results could have '
      f'been falsified and were: the single-{LAM} hypothesis (RQ2/H2), the stretch-testcase controller-FAIL '
      f'prediction (a-priori 0.80), and the scale-dependent C_zon hypothesis (a-priori 0.50). All three '
      f'shifted the supported hypothesis to lower a-priori alternatives.'),
    h2('8.5 Positioning relative to related work'),
    p(f'Our fidelity-utility paradox is consistent with surrogate-development reporting gaps highlighted '
      f'by Hou & Evins [16] and with the offline-RL distribution-shift literature [24]. We differ from '
      f'physics-informed controller approaches (TC-DDPG [28], Safe DRL + MPC [26]) by embedding physics '
      f'only as a per-step reward-shaping censor [18], never as the rollout environment. For Block 3 '
      f'transferability, our component-level finding stands in productive tension with prior transfer-'
      f'learning work [30,31,32] that reports 1{NDASH}40 % improvements: those studies allow the target '
      f'deployment to see some target data (online fine-tuning, multi-source aggregation, partial '
      f'parameter sharing). Our design tests the harder frozen-method scenario with no target controller '
      f'training, only per-testcase actuator adapters and pre-registered Stage A/B/C recalibration; '
      f'under that stricter constraint, residential transfer fails comfort and commercial transfer fails '
      f'energy.'),
    h2('8.6 Threats to validity'),
    p(f'The bestest_air evidence uses one weather file and targeted sensitivity rather than full '
      f'hyperparameter optimisation. HDRL is single-seed. MORL N=5 remains high-variance, so MORL is '
      f'reported as promising rather than deployment-stable. Block 3 covers three hydronic testcases, '
      f'not arbitrary archetypes or multi-zone systems. The 85{TIMES} speed-up is measured against the '
      f'BOPTEST RTE HTTP-Docker deployment, not bare FMU evaluation. The two-horizon evaluation protocol '
      f'({SECT}4.4) uses 14-day windows for Sections 5{NDASH}6 and yearly evaluation for Section 7; '
      f'Block 2 targeted-window results should not be interpreted as yearly deployment guarantees. '
      f'The Block 3 1.25{TIMES} PI threshold can mask per-KPI deterioration {MDASH} the commercial stretch '
      f'case is a threshold PASS that is not deployment-ready because of its energy penalty. Future '
      f'protocols should use a tiered verdict with per-KPI floors for energy and violation rate.'),
])
xml = xml[:i_8] + new_8 + xml[i_9:]
print(f'§8 NEW: {wc(new_8)} words ({wc(new_8) - wc(old_8):+d})')

# ─── §9 replacement — SAFE: stop at Data availability heading ───
a_9 = '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>9. Conclusion</w:t></w:r></w:p>'
i_9 = xml.find(a_9)

# Find "Data availability" - it could be plain text or a heading
pat_data = '<w:r><w:t>Data availability'
pat_data2 = '<w:r><w:t xml:space="preserve">Data availability'
i_data = xml.find(pat_data, i_9)
if i_data < 0:
    i_data = xml.find(pat_data2, i_9)
if i_data < 0:
    raise SystemExit('Data availability not found after §9')
# Find paragraph start containing Data availability
i_data_para = xml.rfind('<w:p>', 0, i_data)
if i_data_para < 0:
    i_data_para = xml.rfind('<w:p ', 0, i_data)
print(f'\n§9 OLD: {wc(xml[i_9:i_data_para])} words (cut from {i_9} to {i_data_para})')
old_9 = xml[i_9:i_data_para]

new_9 = a_9 + ''.join([
    p(f'This paper tested a common assumption in physics-informed RL for buildings {MDASH} that a more '
      f'predictive physical twin should be the better RL training environment {MDASH} and reported a '
      f'negative result on the BOPTEST bestest_air testcase. The calibrated v3.5 grey-box twin '
      f'(24-h rollout RMSE 0.644 {DEG}C, 2.4{TIMES} better than v3) improves long-horizon predictive '
      f'fidelity, yet when used directly as the PPO backbone the resulting policy collapses to '
      f'm_s = 1.046 with live comfort RMSE above 4 {DEG}C. The right role of the calibrated twin is '
      f'narrower and more useful: it serves as a frozen per-step reward-shaping censor for a smoother '
      f'v3 rollout backend. The resulting hybrid recipe reduces live BOPTEST m_s from 0.073 / 0.095 '
      f'(pure v3) to 0.087 / 0.041 (hybrid_l010) on peak / typical winter windows, preserves the '
      f'85{TIMES} surrogate-speed advantage required for RL training, and is mechanism-preserving: PPO '
      f'computes advantage from the augmented reward in the standard way with no policy-gradient '
      f'modification.'),
    p(f'The hybrid weight is not universal across controller families. Thermostatic PPO favours '
      f'{LAM}_temp = 0.10; HDRL favours {LAM}_temp = 0.00 (its m_s degrades monotonically with '
      f'increasing {LAM}_temp from 0.180 to 0.440 on peak); the 17-D MORL matches HDRL. The MORL N=5 '
      f'canonical analysis remains high-variance (CV {SECT} 0.42{NDASH}0.61); the pre-registered action-'
      f'saturation hypothesis is falsified at commit 62dc859 and the defensible reading is that MORL '
      f'needs explicit policy-stabilisation to become deployment-stable.'),
    p(f'The pre-registered Block 3 transferability study extends the contribution beyond bestest_air. '
      f'Across three single-zone hydronic testcases the Stage A/B/C inverse calibration pipeline '
      f'transfers robustly, with 60.2 % / 87.4 % / 87.8 % RMSE_T improvement and tightly clustered '
      f'C_zon at 1.918 {PM} 0.032{TIMES} bestest_air. This falsifies the pre-registered scale-dependent '
      f'hypothesis (a-priori 0.50) in favour of the uniform-hydronic-family hypothesis (a-priori 0.35). '
      f'The frozen-controller side does not transfer in a deployment-ready sense: residential cases fail '
      f'the 1.25{TIMES} PI comfort threshold; the commercial stretch passes safety but at +35.3 % energy '
      f'versus PI.'),
    p(f'The component-level take-away is that the physically informed surrogate representation transfers, '
      f'while the controller-adapter interface is the bottleneck. The immediate next experiment is '
      f'target-specific controller fine-tuning on the target-recalibrated surrogate under a tiered '
      f'comfort{NDASH}energy transfer criterion {MDASH} explicitly out of the pre-registered scope of this '
      f'paper so the present manuscript reports falsifications and boundaries without moving the goalposts. '
      f'All numerical values are sourced from CSV/JSON artefacts under reports/ and outputs/; the audit '
      f'chain (nine commit anchors verifiable via git log) is reproduced in the Supplementary Material.'),
])
xml = xml[:i_9] + new_9 + xml[i_data_para:]
print(f'§9 NEW: {wc(new_9)} words ({wc(new_9) - wc(old_9):+d})')

# ─── Stage 2: Figure removal ───
print('\n' + '═' * 70 + '\nSTAGE 2: Figure removal\n' + '═' * 70)

REMOVE = [
    'Figure 2a.', 'Figure 2b.', 'Figure 2c.', 'Figure 2d.', 'Figure 3.',
    'Figure 4a.', 'Figure 4c.', 'Figure 4d.', 'Figure 4f.', 'Figure 4h.',
    'Figure B1-1.', 'Figure B1-3.', 'Figure B1-5.', 'Figure B1-6.',
    'Figure B2-1.', 'Figure B2-2.',
    'Figure B3-1.', 'Figure B3-2.', 'Figure B3-3.', 'Figure B3-4.', 'Figure B3-5.',
]

def remove_fig(xml, label):
    cap_pat = f'<w:t xml:space="preserve">{label}</w:t>'
    cap_pos = xml.find(cap_pat)
    if cap_pos < 0:
        return xml, False
    cap_end = xml.find('</w:p>', cap_pos) + len('</w:p>')
    cap_start = xml.rfind('<w:p>', 0, cap_pos)
    if cap_start < 0: cap_start = xml.rfind('<w:p ', 0, cap_pos)
    block_start = cap_start
    cursor = cap_start
    while True:
        prev_end = xml.rfind('</w:p>', 0, cursor) + len('</w:p>')
        if prev_end <= len('</w:p>') or prev_end != cursor: break
        prev_start = xml.rfind('<w:p>', 0, prev_end-len('</w:p>'))
        if prev_start < 0: prev_start = xml.rfind('<w:p ', 0, prev_end-len('</w:p>'))
        if prev_start < 0: break
        prev_para = xml[prev_start:prev_end]
        if '<w:drawing>' in prev_para or '<w:t xml:space="preserve">(a)</w:t>' in prev_para or '<w:t xml:space="preserve">(b)</w:t>' in prev_para:
            block_start = prev_start
            cursor = prev_start
        else:
            break
    return xml[:block_start] + xml[cap_end:], True

removed = 0
for lbl in REMOVE:
    xml, ok = remove_fig(xml, lbl)
    if ok:
        removed += 1
        print(f'  [REMOVED] {lbl}')
    else:
        print(f'  [skip   ] {lbl} (not found)')
print(f'\nTotal removed: {removed}/{len(REMOVE)}')

# ─── Stage 3: Renumber remaining captions to Figure 1-8 ───
print('\n' + '═' * 70 + '\nSTAGE 3: Renumber to Figure 1-8 sequential\n' + '═' * 70)

rename_pairs = [
    ('Figure 1.',    '__F1__'),
    ('Figure B1-2.', '__F2__'),
    ('Figure B1-4.', '__F3__'),
    ('Figure 4b.',   '__F4__'),
    ('Figure 4e.',   '__F5__'),
    ('Figure 4g.',   '__F6__'),
    ('Figure 5.',    '__F7__'),
    ('Figure 6.',    '__F8__'),
]
final_pairs = [
    ('__F1__', 'Figure 1.'),  ('__F2__', 'Figure 2.'),
    ('__F3__', 'Figure 3.'),  ('__F4__', 'Figure 4.'),
    ('__F5__', 'Figure 5.'),  ('__F6__', 'Figure 6.'),
    ('__F7__', 'Figure 7.'),  ('__F8__', 'Figure 8.'),
]
for old, new in rename_pairs:
    n = xml.count(old)
    if n: xml = xml.replace(old, new); print(f'  pass1: {old} → temp ({n}x)')
for old, new in final_pairs:
    n = xml.count(old)
    if n: xml = xml.replace(old, new); print(f'  pass2: → {new} ({n}x)')

# ─── Save ───
entries['word/document.xml'] = xml.encode('utf-8')
tmp = SRC + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for n, data in entries.items():
        zo.writestr(n, data)
shutil.move(tmp, SRC)
print(f'\n[OK] {SRC}: {os.path.getsize(SRC):,} bytes')
