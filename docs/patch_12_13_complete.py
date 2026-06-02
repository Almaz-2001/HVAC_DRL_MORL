"""Replace §1.2 Research Questions and §1.3 Contributions with proper OOXML formatting.
   - Fix markdown asterisks → proper Word bold
   - Add explicit H1/H2/H3 hypotheses to §1.2
   - Strengthen C1-C6 with full numerical evidence
   - Add closing summary paragraph

Run: python docs/patch_12_13_complete.py
"""
import zipfile, shutil, os, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

src = 'docs/hvac_paper_skeleton_q1_restructured_patched.docx'
with zipfile.ZipFile(src) as z:
    entries = {n: z.read(n) for n in z.namelist()}
xml = entries['word/document.xml'].decode('utf-8')

# ─────────────────── OOXML helpers ───────────────────
def t_run(text, bold=False, italic=False):
    """Plain text run. Use for inline mixed-format paragraphs."""
    rpr = ''
    if bold or italic:
        rpr = '<w:rPr>'
        if bold: rpr += '<w:b/><w:bCs/>'
        if italic: rpr += '<w:i/><w:iCs/>'
        rpr += '</w:rPr>'
    return f'<w:r>{rpr}<w:t xml:space="preserve">{text}</w:t></w:r>'

def para_mixed(runs):
    """Paragraph with multiple runs (some bold, some normal)."""
    return '<w:p>' + ''.join(runs) + '</w:p>'

def para_plain(text):
    """Simple plain paragraph."""
    return f'<w:p><w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>'

def h2(text):
    return f'<w:p><w:pPr><w:pStyle w:val="Heading2"/></w:pPr><w:r><w:t>{text}</w:t></w:r></w:p>'

def bul_mixed(runs):
    """Bullet paragraph with mixed-format runs."""
    return ('<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'
            '<w:ind w:left="720" w:hanging="360"/></w:pPr>' + ''.join(runs) + '</w:p>')

# XML entities
DEG  = '&#xB0;'    # °
TIMES= '&#xD7;'    # ×
PM   = '&#xB1;'    # ±
LAM  = '&#x3BB;'   # λ
LE   = '&#x2264;'  # ≤
SECT = '&#xA7;'    # §
MDASH= '&#x2014;'  # —
NDASH= '&#x2013;'  # –
APOS = '&#x2019;'  # '
LQUO = '&#x201C;'  # "
RQUO = '&#x201D;'  # "
MINUS= '&#x2212;'  # − (true minus)
SUP5 = '&#x2075;'  # ⁵
SUP_MINUS5 = '&#x207B;&#x2075;'  # ⁻⁵
SQ2  = '&#xB2;'    # ²

# ═══════════════════════════ Build new §1.2 ═══════════════════════════
section_12 = ''.join([
    h2('1.2 Research questions and hypotheses'),

    para_plain(
        f'Three nested falsifiable research questions structure the empirical contributions reported in '
        f'Sections 5{NDASH}7, together with three explicit predictions that the experiments could have '
        f'falsified. Each prediction is committed to a pre-registration audit anchor before the corresponding '
        f'experiment was executed; the verdicts are reported in Section 8.'
    ),

    bul_mixed([
        t_run('RQ1 (Section 5 + Section 6.2). ', bold=True),
        t_run(
            f'Does the physically calibrated grey-box surrogate (v3.5, 24-h rollout RMSE 0.644 {DEG}C) '
            f'outperform the control-oriented black-box surrogate (v3, 24-h rollout RMSE 1.557 {DEG}C) when '
            f'used directly as the PPO rollout environment? '
        ),
        t_run('Prediction H1: ', italic=True),
        t_run(
            f'a higher-fidelity surrogate yields a lower live-BOPTEST m_s. Verdict: '
        ),
        t_run('falsified', bold=True),
        t_run(
            f' {MDASH} v3.5 collapses to m_s = 1.046 with comfort violation above 77 %, while v3 yields '
            f'm_s = 0.073 / 0.095.'
        ),
    ]),

    bul_mixed([
        t_run('RQ2 (Section 6.3-6.5). ', bold=True),
        t_run(
            f'If the calibrated surrogate is not the right rollout environment, what is its right role inside '
            f'the training pipeline, and does that role transfer across controller families (thermostatic PPO, '
            f'Hierarchical Deep RL, 17-dimensional Multi-Objective RL)? '
        ),
        t_run('Prediction H2: ', italic=True),
        t_run(
            f'a single optimal physics-disagreement weight {LAM}_temp exists across all three families. Verdict: '
        ),
        t_run('falsified', bold=True),
        t_run(
            f' {MDASH} thermostatic PPO best at {LAM}_temp = 0.10, HDRL and MORL best at {LAM}_temp = 0.00. The '
            f'role of v3.5 is family-specific, not universal.'
        ),
    ]),

    bul_mixed([
        t_run('RQ3 (Section 7). ', bold=True),
        t_run(
            f'Does the v3 + v3.5 hybrid recipe transfer to BOPTEST testcases other than the source bestest_air '
            f'case? Specifically, does the inverse surrogate-calibration pipeline transfer across the hydronic '
            f'family, and does the frozen bestest_air controller transfer through a per-testcase actuator adapter '
            f'under the pre-registered 1.25{TIMES} PI comfort threshold? '
        ),
        t_run('Prediction H3: ', italic=True),
        t_run(
            f'both the surrogate calibration and the frozen controller transfer cleanly. Verdict: '
        ),
        t_run('component-level', bold=True),
        t_run(
            f' {MDASH} the surrogate side transfers (60.2 / 87.4 / 87.8 % RMSE_T improvement; C_zon uniform at '
            f'1.918 {PM} 0.032{TIMES} bestest_air), but frozen controller transfer fails in a regime-dependent '
            f'way (residential hydronic fails comfort; commercial stretch passes safety with a +35.3 % energy penalty).'
        ),
    ]),

    para_plain(
        f'Each RQ is mapped to a specific set of pre-registered numerical artifacts (CSV/JSON outputs under '
        f'reports/ and outputs/) and to a specific git commit anchor in the audit chain summarised in Section 1.4. '
        f'The mapping from RQ to evidence to verdict is reproduced verbatim in Sections 5-8, so that each '
        f'falsifiable claim is traceable from the introduction through to the underlying data file.'
    ),
])

# ═══════════════════════════ Build new §1.3 ═══════════════════════════
section_13 = ''.join([
    h2('1.3 Contributions'),
    para_plain(
        f'The paper makes six contributions, each tied to a falsifiable hypothesis and a specific set of '
        f'pre-registered numerical artifacts. Together they form a closed-loop methodological argument: a '
        f'low-fidelity black-box surrogate (C1), a physically informed twin (C2), a hybrid mechanism that '
        f'reconciles them (C3), evidence that the mechanism is controller-family specific (C4), a pre-registered '
        f'transferability study across three hydronic testcases (C5), and a fully reproducible numerical '
        f'audit trail (C6).'
    ),

    bul_mixed([
        t_run('(C1) A control-oriented v3 surrogate.', bold=True),
        t_run(
            f' A direct supply-temperature neural surrogate with 8,482 parameters (7,105 for the temperature head, '
            f'1,377 for the power head) trained on 51,200 hourly BOPTEST transitions. The frozen checkpoint reaches '
            f'a validation one-step RMSE of 0.6255 {DEG}C and R{SQ2} = 0.979, but a 24-h closed-loop rollout RMSE '
            f'of 1.557 {DEG}C with R{SQ2} = {MINUS}1.41 (Block 1 Table 1.3). v3 is therefore deliberately retained as '
            f'a high-throughput PPO [17] rollout generator and explicitly not claimed as a long-horizon predictor.'
        ),
    ]),

    bul_mixed([
        t_run('(C2) A physically informed v3.5 grey-box surrogate.', bold=True),
        t_run(
            f' A neural ODE backbone with explicit zone thermal capacitance C_zon = 4.413{TIMES}10{SUP5} J/K '
            f'(+5.1 % vs the 4.200{TIMES}10{SUP5} J/K Bayesian prior), identified through the three-stage inverse '
            f'pipeline [3]: Stage A (telemetry preprocessing on 10,744 fifteen-minute transitions), Stage B '
            f'(120-epoch inverse C_zon solve), and Stage C (60-epoch temperature-head + 80-epoch power-head '
            f'calibration). Calibrated v3.5 achieves a 24-h rollout RMSE of 0.644 {DEG}C, a 2.4{TIMES} reduction '
            f'relative to v3, and confirms v3.5 as the predictively superior model.'
        ),
    ]),

    bul_mixed([
        t_run('(C3) A hybrid backend with reward-shaping disagreement censoring.', bold=True),
        t_run(
            f' v3 supplies the smooth rollout dynamics; calibrated v3.5 acts as a frozen per-step reward-shaping '
            f'censor [18]. The augmented reward is r_t = r_comfort + r_smooth + r_energy {MINUS} {LAM}_temp '
            f'|t_v3 {MINUS} t_v3.5| {MINUS} {LAM}_power |p_v3 {MINUS} p_v3.5|, after which PPO computes the '
            f'advantage in the standard way (envs/backends/surrogate_backend.py lines 343{NDASH}350; '
            f'training/train_thermostatic.py line 436). The canonical thermostatic hybrid '
            f'({LAM}_temp = 0.10, {LAM}_pwr = 5{TIMES}10{SUP_MINUS5}) achieves live BOPTEST '
            f'm_s = 0.087 (peak) and 0.041 (typical), versus 1.046 / 1.102 for direct v3.5 PPO and '
            f'0.073 / 0.095 for pure v3 PPO. The backend sustains 1,786.8 environment steps/s on a single '
            f'CPU thread, an 85.0{TIMES} acceleration relative to the live BOPTEST loop under the same '
            f'15-minute control protocol.'
        ),
    ]),

    bul_mixed([
        t_run('(C4) Controller-family-specific evidence.', bold=True),
        t_run(
            f' A {LAM}_temp sweep across HDRL ({LAM}_temp in {{0.00, 0.03, 0.05, 0.10}}) shows monotonic degradation '
            f'of HDRL m_s with increasing {LAM}_temp: on the peak window m_s rises from 0.180 (l000) through '
            f'0.307, 0.418, to 0.440 (l010); on the typical window from 0.234 to 0.511. The thermostatic-optimal '
            f'{LAM}_temp = 0.10 is therefore the worst HDRL setting. The 17-D MORL backend '
            f'(linear-scalarisation MORL [19]) matches HDRL{APOS}s {LAM}_temp = 0.00 / {LAM}_pwr = 5{TIMES}10{SUP_MINUS5} '
            f'preference, with the MORL 5-D variant collapsing to m_s = 1.046 in a frozen failed-observation '
            f'ablation. No universal physics-guided regularisation weight exists across the three families; the '
            f'role of v3.5 is family-specific, not universal.'
        ),
    ]),

    bul_mixed([
        t_run('(C5) A pre-registered transferability analysis across three hydronic testcases.', bold=True),
        t_run(
            f' The Block 3 manifest (configs/block3_testcase_manifest.yaml) was committed at git anchor 1861e48 '
            f'BEFORE any non-bestest_air BOPTEST episode was executed. Stage A/B/C recalibration improves RMSE_T '
            f'by 60.2 % on bestest_hydronic_heat_pump (primary), 87.4 % on bestest_hydronic (secondary), and 87.8 % '
            f'on singlezone_commercial_hydronic (stretch), and re-identifies C_zon at 1.892{TIMES} / 1.954{TIMES} / '
            f'1.909{TIMES} the bestest_air value (mean 1.918 {PM} 0.032{TIMES}). The tight clustering across an '
            f'order-of-magnitude span in zone volume supports the pre-registered hydronic-family-uniform thermal-mass '
            f'hypothesis (a-priori probability 0.35) and falsifies the scale-dependent alternative (a-priori 0.50). '
            f'Frozen controller transfer is regime-dependent and not deployment-ready: residential hydronic cases '
            f'fail the pre-registered 1.25{TIMES} PI comfort threshold (m_s_RL / pass-bound = 0.665 / 0.580 on '
            f'primary, 0.976 / 0.938 on secondary); the commercial stretch case passes the safety bound '
            f'(0.431 / 0.785) but at +35.3 % energy versus PI.'
        ),
    ]),

    bul_mixed([
        t_run('(C6) A reproducible Hou-and-Evins-style numerical audit trail.', bold=True),
        t_run(
            f' Eleven supplementary tables (S1{NDASH}S11) [16] cover sample generation, sample-size justification, '
            f'Stage A telemetry preprocessing, feature significance, input independence, split representativeness, '
            f'channel scaling, training hyperparameters, architecture justification, targeted sensitivity, and '
            f'replicative / predictive validity. All numerical values trace to CSV/JSON artifacts under '
            f'reports/ and outputs/ and to nine pre-registration audit anchors verifiable via git log: '
            f'93df9b3 (MORL seed-45/46 predictions), 62dc859 (post-N=5 falsification), 1861e48 (Block 3 manifest), '
            f'2f9d596 (Block 3 audit-pre), eb7091e (hydronic adapter pre-reg), 46fbaa9 (secondary adapter pre-reg), '
            f'645626e (stretch predictions pre-reg), 7ada793 (Block 3 close), cb7025f (Block 3 interpretation). '
            f'Each pre-registered prediction is reported with its a-priori probability and observed outcome, so '
            f'reviewers can distinguish confirmations from falsifications at a glance.'
        ),
    ]),

    para_plain(
        f'Read together, the six contributions constitute a single methodological narrative: a low-fidelity '
        f'surrogate is sufficient for control-policy training, a high-fidelity physical twin earns its place as '
        f'a soft regulariser rather than as a rollout environment, the resulting hybrid recipe is family-specific '
        f'in its weight choice, and the inverse-calibration pipeline transfers across the hydronic family even '
        f'when the trained controller does not. The negative findings (RQ1 falsified, single-{LAM} hypothesis '
        f'falsified, frozen-controller transfer falsified) are reported in Section 8 with the same numerical '
        f'discipline as the positive findings, so that the boundary of the proposed method is explicit.'
    ),
])

# ═══════════════════════════ Locate and replace ═══════════════════════════
# Find the span from §1.2 heading paragraph to §1.4 heading paragraph
h2_12_run = '<w:r><w:t>1.2 Research questions</w:t></w:r>'
h2_14_run = '<w:r><w:t>1.4 Pre-registration discipline</w:t></w:r>'

# Find the §1.2 heading paragraph start (the one containing the run)
pos_12 = xml.find(h2_12_run)
para_12_start = xml.rfind('<w:p ', 0, pos_12)
if para_12_start < 0:
    para_12_start = xml.rfind('<w:p>', 0, pos_12)
print(f'[locate] §1.2 paragraph starts at {para_12_start}')

# Find the §1.4 heading paragraph start
pos_14 = xml.find(h2_14_run)
para_14_start = xml.rfind('<w:p ', 0, pos_14)
if para_14_start < 0:
    para_14_start = xml.rfind('<w:p>', 0, pos_14)
print(f'[locate] §1.4 paragraph starts at {para_14_start}')

# Compute size of replacement span
old_span_bytes = para_14_start - para_12_start
new_content = section_12 + section_13
print(f'[replace] old §1.2 + §1.3 span = {old_span_bytes:,} bytes')
print(f'[replace] new §1.2 + §1.3 span = {len(new_content):,} bytes')

xml = xml[:para_12_start] + new_content + xml[para_14_start:]

# ═══════════════════════════ Save ═══════════════════════════
entries['word/document.xml'] = xml.encode('utf-8')
tmp = src + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for n, data in entries.items():
        zo.writestr(n, data)
shutil.move(tmp, src)

print(f'\n[OK] Patched {src} ({os.path.getsize(src):,} bytes)')
print(f'    Final XML size: {len(xml):,} chars')
