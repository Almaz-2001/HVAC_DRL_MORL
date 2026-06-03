"""Insert 7 main figures (Block 2 + Block 3) into the paper DOCX with captions.

Strategy:
  1. Read each PNG into bytes
  2. Add to word/media/ with unique image_N.png filenames
  3. Add <Relationship> for each in word/_rels/document.xml.rels
  4. Add <Default Extension="png" .../> to [Content_Types].xml if missing
  5. Build <w:drawing> XML and a caption paragraph
  6. Insert at anchor points using string replacement in word/document.xml

Run: python docs/insert_figures_b2_b3.py
"""
from __future__ import annotations
import os, sys, io, re, shutil, zipfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SRC = 'docs/hvac_paper_skeleton_q1_restructured_patched.docx'
FIG_DIR = Path('reports/figures/article_real/main_block23')

# ─── 7 figures + captions + insertion anchors ───
FIGURES = [
    # (image filename, caption_label, caption_text, anchor_text)
    (
        'fig_block2_pipeline.png',
        'Figure B2-1.',
        ' Block 2 controller-side validation pipeline. The three surrogate backends '
        '(v3, calibrated v3.5, hybrid) feed five PPO/HDRL/MORL training stacks, with all '
        'controller KPIs measured on the live BOPTEST RTE.',
        '6. Results II: Control Performance',
    ),
    (
        'fig_block2_reward_shaping.png',
        'Figure B2-2.',
        ' Hybrid backend reward-shaping mechanism. v3 supplies rollout dynamics; v3.5 acts '
        'as a per-step disagreement censor by subtracting λ_temp|t_v3 − t_v3.5| − '
        'λ_pwr|p_v3 − p_v3.5| from the comfort+energy reward. PPO computes the advantage '
        'in the standard way; no policy-loss modification is required. Source code: '
        'envs/backends/surrogate_backend.py lines 343–350.',
        '6.3 Thermostatic PPO with hybrid regularization',
    ),
    (
        'fig_block3_protocol.png',
        'Figure B3-1.',
        ' Pre-registered Block 3 transferability protocol. The manifest (anchor 1861e48, '
        'logged 2026-05-18) and the stretch-testcase predictions (anchor 645626e) were '
        'committed BEFORE any non-bestest_air BOPTEST episode ran. Reviewers can verify '
        'bit-identical pre-registration via `git diff 1861e48..7ada793`.',
        '7. Results III: Transferability and Generalization',
    ),
    (
        'fig_block3_testcase_ladder.png',
        'Figure B3-2.',
        ' Block 3 testcase difficulty ladder. Three single-zone hydronic testcases of '
        'increasing structural distance from the bestest_air source are paired with three '
        'pre-registered actuator adapters. The stretch testcase is deliberately included '
        'as a falsification probe.',
        '7.2 Actuator-interface adaptation',
    ),
    (
        'fig_block3_rl_vs_pi.png',
        'Figure B3-3.',
        ' Frozen-controller transfer verdict on N=3 hydronic testcases. Left: m_s_RL '
        'against the pre-registered 1.25× PI threshold per testcase. Right: energy delta '
        'against the testcase PI baseline. Residential cases save energy but FAIL the '
        'comfort threshold; the commercial stretch PASSES safety but pays a +35.3 % '
        'energy penalty. Source: reports/block3_transfer_matrix.csv.',
        '7.3 Transfer matrix',
    ),
    (
        'fig_block3_stage_abc_gain.png',
        'Figure B3-4.',
        ' Full Stage A/B/C surrogate recalibration improves RMSE_T by 60.2 % / 87.4 % / '
        '87.8 % on the three hydronic testcases. Power-head MAE improvements are large on '
        'the residential cases and marginal on the commercial stretch (different power '
        'magnitude). Source: reports/block3_transfer_matrix.csv.',
        '7.5 Aggregate finding',
    ),
    (
        'fig_block3_hypothesis_closure.png',
        'Figure B3-5.',
        ' Pre-registered predictions vs observed outcomes (stretch testcase). Two '
        'predictions are FALSIFIED (controller verdict; scale-dependent C_zon hypothesis B); '
        'three are CONFIRMED (full-recalibration RMSE gain inside [50, 90]%; uniform '
        'hydronic-family C_zon hypothesis A; pipeline convergence). Both surprises shifted '
        'support to LOWER a-priori alternatives — the desired direction of Popperian '
        'falsifiability.',
        '7.7 Pre-registered predictions',
    ),
]

# ─── Read DOCX ───
with zipfile.ZipFile(SRC) as z:
    entries = {n: z.read(n) for n in z.namelist()}

xml = entries['word/document.xml'].decode('utf-8')
rels_xml = entries['word/_rels/document.xml.rels'].decode('utf-8')
ct_xml = entries['[Content_Types].xml'].decode('utf-8')

# ─── Ensure PNG content type ───
if 'Extension="png"' not in ct_xml:
    ct_xml = ct_xml.replace(
        '<Default Extension="rels"',
        '<Default Extension="png" ContentType="image/png"/><Default Extension="rels"'
    )
    entries['[Content_Types].xml'] = ct_xml.encode('utf-8')
    print('[ct] added PNG content type')

# ─── Find max existing rId to avoid collisions ───
existing_rids = [int(m.group(1)) for m in re.finditer(r'Id="rId(\d+)"', rels_xml)]
next_rid = max(existing_rids) + 1 if existing_rids else 1
print(f'[rels] next rId will start at {next_rid}')

# ─── Find max existing image_N.png to avoid collisions ───
existing_images = [int(m.group(1)) for m in re.finditer(r'word/media/image(\d+)\.', '\n'.join(entries.keys()))]
next_img = max(existing_images) + 1 if existing_images else 1
print(f'[media] next image_N will start at {next_img}')

# ─── Helper functions ───
def make_drawing(rid: str, cx_emu: int = 5486400, cy_emu: int = 2743200, name: str = 'Figure'):
    """Build inline drawing XML for an image. cx/cy in EMU (914400 EMU = 1 inch).
    Default: 6.0" wide × 3.0" tall."""
    pic_id = rid.replace('rId', '')
    return (
        '<w:p>'
          '<w:pPr><w:jc w:val="center"/></w:pPr>'
          '<w:r><w:drawing>'
            '<wp:inline distT="0" distB="0" distL="0" distR="0" '
                       'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">'
              f'<wp:extent cx="{cx_emu}" cy="{cy_emu}"/>'
              '<wp:effectExtent l="0" t="0" r="0" b="0"/>'
              f'<wp:docPr id="{pic_id}" name="{name}"/>'
              '<wp:cNvGraphicFramePr><a:graphicFrameLocks '
                'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
              '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
                '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
                  '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
                    '<pic:nvPicPr>'
                      f'<pic:cNvPr id="{pic_id}" name="{name}"/>'
                      '<pic:cNvPicPr/>'
                    '</pic:nvPicPr>'
                    '<pic:blipFill>'
                      f'<a:blip xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="{rid}"/>'
                      '<a:stretch><a:fillRect/></a:stretch>'
                    '</pic:blipFill>'
                    '<pic:spPr>'
                      f'<a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx_emu}" cy="{cy_emu}"/></a:xfrm>'
                      '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
                    '</pic:spPr>'
                  '</pic:pic>'
                '</a:graphicData>'
              '</a:graphic>'
            '</wp:inline>'
          '</w:drawing></w:r>'
        '</w:p>'
    )

def make_caption(label: str, text: str):
    """Build a centered caption paragraph with bold label + italic text."""
    return (
        '<w:p>'
          '<w:pPr><w:jc w:val="center"/><w:spacing w:before="80" w:after="240"/></w:pPr>'
          f'<w:r><w:rPr><w:b/><w:bCs/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve">{label}</w:t></w:r>'
          f'<w:r><w:rPr><w:i/><w:iCs/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve">{text}</w:t></w:r>'
        '</w:p>'
    )

# ─── Process each figure ───
new_rels_entries = []
inserted_count = 0

for img_filename, caption_label, caption_text, anchor_text in FIGURES:
    img_path = FIG_DIR / img_filename
    if not img_path.exists():
        print(f'[!] missing image: {img_path}')
        continue

    # Read image bytes
    img_bytes = img_path.read_bytes()

    # Assign new image filename and rId
    img_name = f'image{next_img}.png'
    rid = f'rId{next_rid}'
    media_path = f'word/media/{img_name}'

    # Add image to entries
    entries[media_path] = img_bytes

    # Add relationship
    new_rel = (f'<Relationship Id="{rid}" '
               f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
               f'Target="media/{img_name}"/>')
    new_rels_entries.append(new_rel)
    print(f'[img] {img_filename} → {img_name} ({rid}, {len(img_bytes):,} bytes)')

    # Build figure + caption XML
    drawing_xml = make_drawing(rid, name=img_filename)
    caption_xml = make_caption(caption_label, caption_text)
    full_xml = drawing_xml + caption_xml

    # Find anchor in xml and insert figure AFTER the paragraph containing the anchor
    anchor_pos = xml.find(anchor_text)
    if anchor_pos < 0:
        print(f'[!] anchor not found: "{anchor_text}"')
        continue

    # Find the end of the paragraph that contains the anchor text
    para_end = xml.find('</w:p>', anchor_pos) + len('</w:p>')
    if para_end <= len('</w:p>'):
        print(f'[!] could not find </w:p> after anchor "{anchor_text}"')
        continue

    # Insert figure XML right after the anchor paragraph
    xml = xml[:para_end] + full_xml + xml[para_end:]
    inserted_count += 1
    print(f'[ins] inserted at offset {para_end} (after "{anchor_text[:50]}...")')

    # Advance counters
    next_rid += 1
    next_img += 1

# ─── Splice new relationships into rels XML ───
rels_xml = rels_xml.replace('</Relationships>', ''.join(new_rels_entries) + '</Relationships>')

# ─── Update entries and save ───
entries['word/document.xml'] = xml.encode('utf-8')
entries['word/_rels/document.xml.rels'] = rels_xml.encode('utf-8')

tmp = SRC + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for n, data in entries.items():
        zo.writestr(n, data)
shutil.move(tmp, SRC)

print(f'\n[OK] {SRC} ({os.path.getsize(SRC):,} bytes)')
print(f'    Inserted {inserted_count} of {len(FIGURES)} figures')
print(f'    Added {len(new_rels_entries)} new image relationships')
