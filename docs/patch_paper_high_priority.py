"""Patch paper DOCX:
   - Remove duplicate §1.1 (Claude's old version)
   - Add new §1.2 Research questions
   - Fix Abstract typos (fields→yields, 4.4413→4.413, Neverthless, the the)
   - Fix math notation (R–2 → R², 10–5 → 10⁵ or 10⁻⁵)
   - Add Hou-Evins citation
   - Add inline citations to §1.3-§1.5
   - Move references to standalone References section

Run: python docs/patch_paper_high_priority.py
"""
import zipfile, shutil, re, os, sys, io
# Force UTF-8 console output (Windows cp1251 chokes on → arrows)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

src = 'docs/hvac_paper_skeleton_q1_restructured_patched.docx'
with zipfile.ZipFile(src) as z:
    entries = {n: z.read(n) for n in z.namelist()}
xml = entries['word/document.xml'].decode('utf-8')

# ════════════════════════ TIER 1: Remove duplicate §1.1 ════════════════════════
# First §1.1 (Claude's old version) is at @8882; second §1.1 (user's literature version) is at @10911
# Strip the entire paragraph block from the first §1.1 heading paragraph up to (but not including)
# the second §1.1 heading paragraph.

first_h2 = '<w:r><w:t>1.1 Problem and motivation</w:t></w:r>'
positions = [m.start() for m in re.finditer(re.escape(first_h2), xml)]
assert len(positions) == 2, f'Expected 2 §1.1 occurrences, found {len(positions)}'

# For the FIRST occurrence, find the enclosing <w:p> start (its containing paragraph)
first_para_start = xml.rfind('<w:p>', 0, positions[0])
if first_para_start < 0:
    first_para_start = xml.rfind('<w:p ', 0, positions[0])

# For the SECOND occurrence, find the enclosing <w:p> start (its containing paragraph)
second_para_start = xml.rfind('<w:p>', 0, positions[1])
if second_para_start < 0:
    second_para_start = xml.rfind('<w:p ', 0, positions[1])

print(f'[strip-dup] first §1.1 paragraph starts at {first_para_start}')
print(f'[strip-dup] second §1.1 paragraph starts at {second_para_start}')
removed_bytes = second_para_start - first_para_start
print(f'[strip-dup] removing {removed_bytes:,} bytes between first and second §1.1')

xml = xml[:first_para_start] + xml[second_para_start:]

# Sanity: now only ONE §1.1 should remain
remaining_h2 = len(list(re.finditer(re.escape(first_h2), xml)))
assert remaining_h2 == 1, f'expected 1 §1.1 after strip, got {remaining_h2}'
print(f'[strip-dup] OK — now {remaining_h2} §1.1 in document.')

# ════════════════════════ TIER 2: Abstract typo fixes ════════════════════════
abstract_fixes = [
    ('fields a more effective training environment',
     'yields a more effective training environment'),
    ('v3 surrogate fields a highly functional policy',
     'v3 surrogate yields a highly functional policy'),
    # Czon notation in Abstract (4.4413 → 4.413; "x 10^5" → "× 10⁵")
    ('Czon= 4.4413 x 10^5 J/K',
     'C_zon = 4.413 × 10⁵ J/K'),
    # Neverthless → Nevertheless
    ('Neverthless,', 'Nevertheless,'),
    # the the → the (with possible extra spaces)
    ('relative to the  the baseline', 'relative to the baseline'),
    ('relative to the the baseline', 'relative to the baseline'),
]
for old, new in abstract_fixes:
    n_before = xml.count(old)
    xml = xml.replace(old, new)
    n_after = xml.count(old)
    if n_before > 0:
        print(f'[abstract-fix] "{old[:50]}..." → "{new[:50]}...": {n_before} replacement(s)')
    else:
        print(f'[abstract-fix] WARN — "{old[:50]}..." not found in XML')

# ════════════════════════ TIER 3: Math notation fixes in §1.3 ════════════════════════
math_fixes = [
    # Negative exponent ×10–5 → ×10⁻⁵ (where en-dash is mistake for minus-superscript)
    ('5×10–5', '5×10⁻⁵'),  # 5×10⁻⁵
    # Positive exponent C_zon = 4.413×10–5 J/K → 4.413×10⁵ J/K
    ('C_zon = 4.413×10–5 J/K', 'C_zon = 4.413×10⁵ J/K'),
    ('4.200×10–5 J/K', '4.200×10⁵ J/K'),
    # R–2 in contributions (R² coefficient of determination)
    ('R–2 = –1.41', 'R² = −1.41'),  # R² = −1.41
    ('R–2 = 0.979', 'R² = 0.979'),
    ('negative R–2', 'negative R²'),
]
for old, new in math_fixes:
    n_before = xml.count(old)
    xml = xml.replace(old, new)
    if n_before > 0:
        print(f'[math-fix] "{old[:40]}" → "{new[:40]}": {n_before} replacement(s)')

# ════════════════════════ TIER 4: Add §1.2 Research questions ════════════════════════
# Insert §1.2 right BEFORE §1.3 Contributions
# Anchor: the heading paragraph for "1.3 Contributions"
c3_heading_run = '<w:r><w:t>1.3 Contributions</w:t></w:r>'
c3_para_start = xml.rfind('<w:p ', 0, xml.find(c3_heading_run))
if c3_para_start < 0:
    c3_para_start = xml.rfind('<w:p>', 0, xml.find(c3_heading_run))
print(f'[add-12] §1.3 heading paragraph starts at {c3_para_start}')

# Build §1.2 XML using the existing Heading2 style
def p(text): return f'<w:p><w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>'
def h2(text): return f'<w:p><w:pPr><w:pStyle w:val="Heading2"/></w:pPr><w:r><w:t>{text}</w:t></w:r></w:p>'
def bul(text):
    return ('<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'
            '<w:ind w:left="720" w:hanging="360"/></w:pPr>'
            f'<w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>')

section_12 = ''.join([
    h2('1.2 Research questions'),
    p('Three nested falsifiable questions structure the empirical contributions reported in Sections '
      '5–7 and the discussion in Section 8:'),
    bul('**RQ1 (Section 5 + Section 6.2):** does the physically calibrated grey-box surrogate '
        '(v3.5, 24-h rollout RMSE 0.644 °C) outperform the control-oriented black-box surrogate '
        '(v3, 24-h rollout RMSE 1.557 °C) when used directly as the PPO rollout environment?'),
    bul('**RQ2 (Section 6.3–6.5):** if the physically calibrated surrogate is not the right rollout '
        'environment, what is its right role inside the training pipeline, and does that role transfer '
        'across controller families (thermostatic PPO, Hierarchical Deep RL, and 17-D Multi-Objective RL)?'),
    bul('**RQ3 (Section 7):** does the recipe transfer to BOPTEST testcases other than the source '
        'bestest_air case? Specifically, does the inverse surrogate-calibration pipeline transfer across '
        'a single-zone hydronic family, and does the frozen controller transfer through a per-testcase '
        'actuator adapter under the pre-registered 1.25× PI comfort threshold?'),
    p('Each RQ is mapped to a specific set of pre-registered numerical artifacts and a specific commit '
      'anchor (Section 1.4); each is answered with a verdict (supported / falsified / regime-dependent) '
      'in Section 8.'),
])

xml = xml[:c3_para_start] + section_12 + xml[c3_para_start:]
print('[add-12] §1.2 Research questions inserted.')

# ════════════════════════ TIER 5: Hou-Evins citation in (C6) ════════════════════════
# In (C6) the text mentions "Hou-and-Evins-style numerical audit". Replace this once with a cite [16].
hou_old = 'A reproducible Hou-and-Evins-style numerical audit.'
hou_new = 'A reproducible Hou-and-Evins-style numerical audit [16].'
n = xml.count(hou_old)
xml = xml.replace(hou_old, hou_new)
print(f'[hou-cite] "{hou_old}" → "{hou_new}": {n} replacement')

# ════════════════════════ TIER 6: Inline citations to §1.3-§1.5 ════════════════════════
# These additions are kept conservative — only where citations are clearly warranted.
inline_cites = [
    # (C1) PPO — cite Schulman 2017
    ('high-throughput PPO rollout generation.',
     'high-throughput PPO [17] rollout generation.'),
    # (C2) grey-box ID — cite existing [3] Arroyo 2020 (already in bibliography)
    ('three-stage inverse-calibration pipeline.',
     'three-stage inverse-calibration pipeline [3].'),
    # (C3) reward shaping — cite Ng & Russell 1999
    ('acts as a **per-step reward-shaping censor**.',
     'acts as a **per-step reward-shaping censor** [18].'),
    # (C4) MORL — cite Roijers et al. 2013
    ('17-D Multi-Objective Reinforcement Learning (MORL)',
     '17-D Multi-Objective Reinforcement Learning (MORL) [19]'),
    # (C5) pre-registration — cite Nosek et al. 2018
    ('A pre-registered transferability analysis',
     'A pre-registered [20] transferability analysis'),
]
for old, new in inline_cites:
    n = xml.count(old)
    if n:
        xml = xml.replace(old, new)
        print(f'[inline-cite] {old[:40]:42s} → cited ({n}x)')
    else:
        print(f'[inline-cite] WARN — "{old[:40]}" not found')

# ════════════════════════ TIER 7: Move references to a standalone References section ════════════════════════
# Strategy:
#   1. Find the "Literature for Introduction part:" marker
#   2. Cut everything from that marker until the next Heading1 (which should be "2. Related Work")
#   3. Append the bibliography as a standalone References section AFTER §9 Conclusion (before/after Data availability appendix)

lit_marker = 'Literature for Introduction part:'
lit_pos = xml.find(lit_marker)
print(f'[bib-move] Literature marker found at {lit_pos}')

# Find the paragraph containing the marker (this is where we start cutting)
lit_para_start = xml.rfind('<w:p ', 0, lit_pos)
if lit_para_start < 0:
    lit_para_start = xml.rfind('<w:p>', 0, lit_pos)

# Find next Heading1 paragraph after the marker
related_h1 = '<w:r><w:t>2. Related Work</w:t></w:r>'
related_pos = xml.find(related_h1, lit_pos)
related_para_start = xml.rfind('<w:p ', 0, related_pos)
if related_para_start < 0:
    related_para_start = xml.rfind('<w:p>', 0, related_pos)

# Extract the bibliography raw XML (between lit_para_start and related_para_start)
bib_raw = xml[lit_para_start:related_para_start]
print(f'[bib-move] Extracted {len(bib_raw):,} bytes of bibliography from Introduction')

# Remove the bibliography from its current position
xml = xml[:lit_para_start] + xml[related_para_start:]
print('[bib-move] Bibliography removed from end of Introduction.')

# Build the standalone References section (Heading1) plus the bib content
# Add §16 reference for Hou-Evins, §17 Schulman, §18 Ng-Russell, §19 Roijers, §20 Nosek
new_refs = ''.join([
    p('[16] Hou J, Evins R. A protocol for reporting numerical justification of machine-learning surrogates '
      'in the built environment. (Verification level 1–3 reporting framework). [TODO: verify exact reference details].'),
    p('[17] Schulman J, Wolski F, Dhariwal P, Radford A, Klimov O. Proximal Policy Optimization Algorithms. '
      'arXiv [Preprint]. 2017; arXiv:1707.06347.'),
    p('[18] Ng AY, Harada D, Russell S. Policy invariance under reward transformations: Theory and '
      'application to reward shaping. In: Proceedings of the 16th International Conference on Machine '
      'Learning (ICML); 1999; Bled, Slovenia: 278–287.'),
    p('[19] Roijers DM, Vamplew P, Whiteson S, Dazeley R. A Survey of Multi-Objective Sequential '
      'Decision-Making. Journal of Artificial Intelligence Research. 2013;48:67–113. doi:10.1613/jair.3987.'),
    p('[20] Nosek BA, Ebersole CR, DeHaven AC, Mellor DT. The preregistration revolution. Proceedings of '
      'the National Academy of Sciences. 2018;115(11):2600–2606. doi:10.1073/pnas.1708274114.'),
])

# Build References heading + content
references_heading = '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>References</w:t></w:r></w:p>'
references_section = references_heading + bib_raw + new_refs

# Insert References section BEFORE "Data availability" section (after §9 Conclusion ends)
data_avail_marker = 'Data availability'
data_pos = xml.find(data_avail_marker)
data_para_start = xml.rfind('<w:p ', 0, data_pos)
if data_para_start < 0:
    data_para_start = xml.rfind('<w:p>', 0, data_pos)
print(f'[bib-move] Inserting References section before "Data availability" at {data_para_start}')

xml = xml[:data_para_start] + references_section + xml[data_para_start:]
print('[bib-move] References section inserted after §9 Conclusion.')

# ════════════════════════ Write back ════════════════════════
entries['word/document.xml'] = xml.encode('utf-8')
tmp = src + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for n, data in entries.items():
        zo.writestr(n, data)
shutil.move(tmp, src)

print(f'\n[OK] Patched {src} ({os.path.getsize(src):,} bytes)')
print(f'    Final XML size: {len(xml):,} chars')
