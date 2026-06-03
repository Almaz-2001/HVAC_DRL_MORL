"""Remove embedded S1-S11 supplementary tables from main DOCX.

The supplementary tables are between "Supplementary Material..." header and "References"
section. They are duplicated in paper/supplementary/supplementary.pdf which is the
proper Elsevier-format supplementary file.

After removal:
  - Main paper: ~22-25 pages instead of 38
  - Supplementary tables: only in paper/supplementary/supplementary.pdf

Run: python docs/remove_supplementary_from_main.py
"""
from __future__ import annotations
import os, sys, io, re, shutil, zipfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SRC = 'docs/hvac_paper_skeleton_q1_restructured_patched.docx'

# Backup before destructive operation
backup = SRC.replace('.docx', '_BEFORE_supp_removal.docx')
shutil.copy(SRC, backup)
print(f'[backup] {backup}')

with zipfile.ZipFile(SRC) as z:
    entries = {n: z.read(n) for n in z.namelist()}
xml = entries['word/document.xml'].decode('utf-8')

# ─── Locate boundaries ───
# The supplementary section starts with a heading like "Supplementary Material"
# or "Supplementary" followed by S1-S11 tables.
# It ends just before "References" heading.

# Find the "Supplementary Material" header — look for the actual heading paragraph
# Try multiple patterns since the heading text varies
sup_patterns = [
    'Supplementary Material: Hou and Evins',
    'Supplementary Material',
    'Supplementary',
]
sup_pos = -1
for pat in sup_patterns:
    # find in raw XML
    idx = xml.find(f'<w:t>{pat}')
    if idx < 0:
        idx = xml.find(f'<w:t xml:space="preserve">{pat}')
    if idx >= 0:
        sup_pos = idx
        print(f'[locate] Supplementary header found via pattern: "{pat}" @ {idx}')
        break

if sup_pos < 0:
    raise SystemExit('Supplementary header not found in main DOCX')

# Find the start of the paragraph containing the supplementary header
sup_para_start = xml.rfind('<w:p>', 0, sup_pos)
if sup_para_start < 0:
    sup_para_start = xml.rfind('<w:p ', 0, sup_pos)
print(f'[locate] Supplementary section paragraph starts @ {sup_para_start}')

# Find the References heading AFTER the supplementary content
refs_h1 = '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>References</w:t></w:r></w:p>'
refs_pos = xml.find(refs_h1, sup_pos)
if refs_pos < 0:
    # Try alternative format
    for variant in ['<w:r><w:t>References</w:t></w:r>',
                     '<w:r><w:t xml:space="preserve">References</w:t></w:r>']:
        refs_pos = xml.find(variant, sup_pos)
        if refs_pos > 0:
            refs_pos = xml.rfind('<w:p', 0, refs_pos)
            break

if refs_pos < 0:
    raise SystemExit('References section not found after supplementary')
print(f'[locate] References section starts @ {refs_pos}')

# Compute removal range and size
removed_xml = xml[sup_para_start:refs_pos]
removed_size = len(removed_xml)
print(f'[remove] Range: {sup_para_start} → {refs_pos} ({removed_size:,} chars)')

# Count tables and word count in removed block
table_count_removed = removed_xml.count('<w:tbl>')
removed_text = re.sub(r'<[^>]+>', ' ', removed_xml)
removed_text = re.sub(r'&#x[0-9a-fA-F]+;', '', removed_text)
removed_words = len(removed_text.split())
print(f'[remove] {table_count_removed} tables, {removed_words:,} words')

# Build replacement: a single short paragraph pointing to the supplementary PDF
def p(text, italic=False):
    rpr = '<w:rPr><w:i/><w:iCs/></w:rPr>' if italic else ''
    return f'<w:p><w:r>{rpr}<w:t xml:space="preserve">{text}</w:t></w:r></w:p>'

def h1(text):
    return f'<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>{text}</w:t></w:r></w:p>'

replacement = (
    h1('Supplementary Material') +
    p('Eleven Hou-and-Evins Reporting-Level-3 numerical-justification tables (S1–S11) covering '
      'sample-generation provenance, sample-size justification, Stage\xa0A telemetry preprocessing, '
      'feature significance, input independence, split representativeness, channel scaling, training '
      'hyperparameters, architecture justification, targeted sensitivity, and replicative/predictive '
      'validity are provided in a separate supplementary document '
      '(paper/supplementary/supplementary.pdf, available as Online Supplement to this manuscript). '
      'Each table is reproduced verbatim from the corresponding CSV file under paper/supplementary/ '
      'and is auditable against the per-section claims in the main text.')
)

# Apply the replacement
xml = xml[:sup_para_start] + replacement + xml[refs_pos:]
print(f'[OK] Replaced {removed_size:,} chars with {len(replacement):,} chars '
      f'(saved {removed_size - len(replacement):,} chars)')

# Save
entries['word/document.xml'] = xml.encode('utf-8')
tmp = SRC + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for n, data in entries.items():
        zo.writestr(n, data)
shutil.move(tmp, SRC)

# Final stats
txt_final = re.sub(r'<[^>]+>', ' ', xml)
txt_final = re.sub(r'&#x[0-9a-fA-F]+;', '', txt_final)
words_final = len(txt_final.split())
print(f'\n[FINAL] {SRC}: {os.path.getsize(SRC):,} bytes')
print(f'        Total words in document: {words_final:,}')
print(f'        XML size: {len(xml):,} chars')
print(f'        Tables: {xml.count("<w:tbl>")}')
print(f'        Drawings: {xml.count("<w:drawing>")}')
