"""Fix Block 1 figure labels (rename Figure 1-6 → Figure B1-1...B1-6) and reorder.

Why: The previously-inserted Block 1 figures collide with pre-existing Figure 1
("Hybrid backend schematic" in §3.3), Figure 2a/b/Figure 3 referenced in body, etc.
Also Figures 4, 5, 6 ended up in reverse order because all three used the same
§5.5 anchor.

This script:
  1. Renames new captions: "Figure 1." → "Figure B1-1.", ..., "Figure 6." → "Figure B1-6."
     (only the new captions we added — old "Figure 1. Hybrid backend schematic" stays)
  2. Reorders Figures B1-4 / B1-5 / B1-6 to correct document order.

Run: python docs/fix_block1_figure_labels_and_order.py
"""
from __future__ import annotations
import zipfile, shutil, re, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SRC = 'docs/hvac_paper_skeleton_q1_restructured_patched.docx'

with zipfile.ZipFile(SRC) as z:
    entries = {n: z.read(n) for n in z.namelist()}
xml = entries['word/document.xml'].decode('utf-8')

# ─── Step 1: rename captions, but ONLY those we inserted (identifiable by next text) ───
# Each of our new captions has very specific following text. We use unique snippets
# that distinguish OUR captions from pre-existing ones with same labels.

rename_rules = [
    # (old_caption_run_pattern, new_caption_text)
    # Use the next words after "Figure N." as the disambiguator
    ('<w:t xml:space="preserve">Figure 1.</w:t></w:r><w:r><w:rPr><w:i/><w:iCs/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve"> Experimental pipeline',
     '<w:t xml:space="preserve">Figure B1-1.</w:t></w:r><w:r><w:rPr><w:i/><w:iCs/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve"> Experimental pipeline'),
    ('<w:t xml:space="preserve">Figure 2.</w:t></w:r><w:r><w:rPr><w:i/><w:iCs/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve"> Stage A/B/C calibration improves',
     '<w:t xml:space="preserve">Figure B1-2.</w:t></w:r><w:r><w:rPr><w:i/><w:iCs/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve"> Stage A/B/C calibration improves'),
    ('<w:t xml:space="preserve">Figure 3.</w:t></w:r><w:r><w:rPr><w:i/><w:iCs/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve"> Matched-corpus RMSE',
     '<w:t xml:space="preserve">Figure B1-3.</w:t></w:r><w:r><w:rPr><w:i/><w:iCs/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve"> Matched-corpus RMSE'),
    ('<w:t xml:space="preserve">Figure 4.</w:t></w:r><w:r><w:rPr><w:i/><w:iCs/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve"> The predictive fidelity vs live RL utility',
     '<w:t xml:space="preserve">Figure B1-4.</w:t></w:r><w:r><w:rPr><w:i/><w:iCs/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve"> The predictive fidelity vs live RL utility'),
    ('<w:t xml:space="preserve">Figure 5.</w:t></w:r><w:r><w:rPr><w:i/><w:iCs/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve"> Live BOPTEST performance comparison',
     '<w:t xml:space="preserve">Figure B1-5.</w:t></w:r><w:r><w:rPr><w:i/><w:iCs/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve"> Live BOPTEST performance comparison'),
    ('<w:t xml:space="preserve">Figure 6.</w:t></w:r><w:r><w:rPr><w:i/><w:iCs/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve"> Transfer diagnostics and bang-bang',
     '<w:t xml:space="preserve">Figure B1-6.</w:t></w:r><w:r><w:rPr><w:i/><w:iCs/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve"> Transfer diagnostics and bang-bang'),
]
for old, new in rename_rules:
    n = xml.count(old)
    if n:
        xml = xml.replace(old, new)
        # extract just the label-change for display
        old_label = old.split('</w:t>')[0].split('>')[-1]
        new_label = new.split('</w:t>')[0].split('>')[-1]
        print(f'[rename] {old_label} → {new_label}: {n} replacement(s)')
    else:
        print(f'[rename] WARN — pattern not found: ...{old[:80]}...')

# ─── Step 2: reorder Figures B1-4 / B1-5 / B1-6 ───
# Current document order is reversed: B1-6 → B1-5 → B1-4
# Need to find each figure block (drawing + caption) and re-arrange them.

# A "figure block" is identified by its caption paragraph containing
# "Figure B1-X." up to (and including) the closing </w:p> of the caption.
# The figure DRAWING is the IMMEDIATELY PRECEDING <w:p>...drawing...</w:p>.
# For multi-panel figures (B1-6 has 2 panels with (a)/(b) sub-labels), it's the
# preceding drawing + panel label + drawing + panel label.

def find_figure_block(label: str, xml: str):
    """Find the byte range [start, end) covering: leading drawings + panel labels + caption.
    Returns (start, end) such that xml[start:end] is the complete figure block."""
    # Locate caption paragraph
    cap_marker = f'<w:t xml:space="preserve">{label}</w:t>'
    cap_pos = xml.find(cap_marker)
    if cap_pos < 0:
        return None
    cap_para_start = xml.rfind('<w:p>', 0, cap_pos)
    if cap_para_start < 0:
        cap_para_start = xml.rfind('<w:p ', 0, cap_pos)
    cap_para_end_search = xml.find('</w:p>', cap_pos)
    cap_para_end = cap_para_end_search + len('</w:p>') if cap_para_end_search >= 0 else len(xml)

    # Walk backwards to include any preceding drawing+panel-label paragraphs
    # that belong to this figure.
    block_start = cap_para_start
    # Walk back paragraphs while they contain <w:drawing> or are a panel label "(a)" "(b)"
    # paragraph (small italic).
    cursor = cap_para_start
    while True:
        prev_end_search = xml.rfind('</w:p>', 0, cursor)
        if prev_end_search < 0:
            break
        prev_end = prev_end_search + len('</w:p>')
        prev_start = xml.rfind('<w:p>', 0, prev_end_search)
        if prev_start < 0:
            prev_start = xml.rfind('<w:p ', 0, prev_end_search)
        if prev_start < 0 or prev_end != cursor:
            break
        prev_para = xml[prev_start:prev_end]
        is_drawing  = '<w:drawing>' in prev_para
        is_panel_lbl = ('<w:t xml:space="preserve">(a)</w:t>' in prev_para or
                        '<w:t xml:space="preserve">(b)</w:t>' in prev_para or
                        '<w:t xml:space="preserve">(c)</w:t>' in prev_para)
        if is_drawing or is_panel_lbl:
            block_start = prev_start
            cursor = prev_start
        else:
            break
    return (block_start, cap_para_end)

# Find current positions of B1-4, B1-5, B1-6
ranges = {}
for lbl in ('Figure B1-4.', 'Figure B1-5.', 'Figure B1-6.'):
    r = find_figure_block(lbl, xml)
    if r is None:
        print(f'[!] {lbl} not found')
        continue
    ranges[lbl] = r
    print(f'[range] {lbl}: bytes {r[0]:>7}-{r[1]:>7} (size {r[1]-r[0]:,} B)')

# Verify all three are contiguous and in the same anchor zone
sorted_by_start = sorted(ranges.items(), key=lambda kv: kv[1][0])
print()
print('[current order]', ' → '.join(lbl for lbl, _ in sorted_by_start))

# Desired order: B1-4 first, then B1-5, then B1-6
desired = ['Figure B1-4.', 'Figure B1-5.', 'Figure B1-6.']
current = [lbl for lbl, _ in sorted_by_start]
if current == desired:
    print('[reorder] already in correct order; no-op')
else:
    # Extract each block, remove them in reverse, then re-insert in desired order
    # at the position of the FIRST original block start.
    insertion_point = sorted_by_start[0][1][0]
    blocks = {lbl: xml[r[0]:r[1]] for lbl, r in ranges.items()}
    # Remove blocks (reverse order so positions stay stable while removing)
    for lbl, (s, e) in sorted(ranges.items(), key=lambda kv: kv[1][0], reverse=True):
        xml = xml[:s] + xml[e:]
    # Insert in desired order at insertion_point (the original earliest start)
    new_block = ''.join(blocks[lbl] for lbl in desired)
    xml = xml[:insertion_point] + new_block + xml[insertion_point:]
    print(f'[reorder] OK — new order: {" → ".join(desired)}')

# ─── Save ───
entries['word/document.xml'] = xml.encode('utf-8')
tmp = SRC + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for n, data in entries.items():
        zo.writestr(n, data)
shutil.move(tmp, SRC)
print(f'\n[OK] {SRC} ({os.path.getsize(SRC):,} bytes)')
