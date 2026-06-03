"""Insert existing Block 1 figures (Figure 1-6) into §5 Results I of the paper DOCX.

Figure 1 (Pipeline) is already embedded as main_fig1_pipeline_schematic.png.
We insert 6 new figures with proper captions at natural §5 anchors.

For Figure 6 (Transfer + saturation), we insert TWO PNGs as panels (a) and (b)
under a single caption.

Run: python docs/insert_figures_block1.py
"""
from __future__ import annotations
import os, sys, io, re, shutil, zipfile
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SRC = 'docs/hvac_paper_skeleton_q1_restructured_patched.docx'
FIG_DIR = Path('reports/figures/article_real')

# ─── Each entry: (list of image filenames, caption_label, caption_text, anchor_text) ───
# Single-panel figures have a 1-element list; multi-panel have multiple.
FIGURES = [
    (
        ['block1_q1_fig01_pipeline.png'],
        'Figure 1.',
        ' Experimental pipeline and hybrid backend concept. The v3 control-oriented '
        'black-box surrogate supplies rollout dynamics for PPO; the calibrated v3.5 '
        'physical twin acts as a frozen per-step reward-shaping censor. All controller '
        'KPIs are measured on the live BOPTEST RTE (Docker, EnergyPlus, 15-min step).',
        '5. Results I: Digital Twin Fidelity',
    ),
    (
        ['block1_q1_fig03_stage_abc_improvement.png'],
        'Figure 2.',
        ' Stage A/B/C calibration improves predictive fidelity. Stage A (telemetry '
        'preprocessing), Stage B (inverse C_zon = 4.413×10⁵ J/K identification), and '
        'Stage C (residual head calibration over 60 + 80 epochs) jointly reduce 24-h '
        'rollout RMSE_T from 1.466 °C (raw v3.5) to 0.644 °C (calibrated v3.5), '
        'a 56 % reduction relative to the uncalibrated baseline.',
        '5.2 Stage A/B/C inverse calibration',
    ),
    (
        ['block1_q1_fig05_matched_corpus_rmse.png', 'block1_q1_fig06_fidelity_gain_waterfall.png'],
        'Figure 3.',
        ' Matched-corpus RMSE decomposition. (a) 24-h rollout RMSE_T comparison across '
        'four surrogate variants on the same 15-min held-out rollouts: v3 hourly '
        '(1.557 °C), corpus-matched v3 (0.876 °C), raw v3.5 (1.466 °C), calibrated v3.5 '
        '(0.644 °C). (b) Decomposition waterfall: 74.6 % of the v3-to-calibrated-v3.5 '
        'gap is attributable to corpus shift; 25.4 % to Stage A/B/C calibration. Source: '
        'reports/block1_corpus_matched_comparison.csv.',
        '5.3 Predictive validity',
    ),
    (
        ['block1_q1_fig07_fidelity_vs_rl_utility.png'],
        'Figure 4.',
        ' The predictive fidelity vs live RL utility paradox. Despite v3.5 outperforming '
        'v3 by 2.4× on 24-h rollout RMSE (0.644 °C vs 1.557 °C), direct v3.5 PPO '
        'collapses to m_s = 1.046 with live BOPTEST RMSE > 4 °C, while pure v3 PPO '
        'yields m_s = 0.073 / 0.095 on peak / typical winter windows. The fidelity '
        '(x-axis) and utility (y-axis) axes are anti-correlated in this regime.',
        '5.5 Fidelity-to-control gap',
    ),
    (
        ['block1_q1_fig08_live_boptest_performance.png'],
        'Figure 5.',
        ' Live BOPTEST performance comparison across all surrogate × controller '
        'combinations. The thermostatic hybrid (v3 dynamics + v3.5 reward-shaping '
        'censor with λ_temp = 0.10, λ_pwr = 5×10⁻⁵) is the strongest single configuration: '
        'm_s = 0.087 (peak) and 0.041 (typical) with under-5 % setpoint violation. '
        'Source: outputs/block13_closed_loop_transfer_*/summary.csv.',
        '5.5 Fidelity-to-control gap',
    ),
    (
        ['block1_q1_fig10_transfer_gap_diagnostics.png', 'block1_q1_fig11_action_saturation.png'],
        'Figure 6.',
        ' Transfer diagnostics and bang-bang saturation mechanism. (a) Surrogate-to-live '
        'ms_gap across pure v3, hybrid_l010, and direct v3.5: hybrid narrows the '
        'surrogate-to-live transfer gap from |gap| ≈ 0.9–1.0 (direct v3.5) to ≈ 0.02 '
        '(hybrid_l010). (b) Action-saturation mechanism: direct v3.5 PPO drives the '
        'actuator into saturation early, producing first-divergence step = 1, while '
        'hybrid_l010 holds policy fidelity through step 16 on the typical window. '
        'Source: reports/hybrid_transfer_comparison.csv.',
        '5.5 Fidelity-to-control gap',
    ),
]

# ─── Read DOCX ───
with zipfile.ZipFile(SRC) as z:
    entries = {n: z.read(n) for n in z.namelist()}

xml = entries['word/document.xml'].decode('utf-8')
rels_xml = entries['word/_rels/document.xml.rels'].decode('utf-8')

# Compute next rId and image_N
existing_rids = [int(m.group(1)) for m in re.finditer(r'Id="rId(\d+)"', rels_xml)]
next_rid = max(existing_rids) + 1
existing_images = [int(m.group(1)) for m in re.finditer(r'word/media/image(\d+)\.', '\n'.join(entries.keys()))]
next_img = max(existing_images) + 1
print(f'[init] next rId={next_rid}, next image={next_img}')

# ─── Helpers ───
def make_drawing(rid: str, name: str = 'Figure',
                 cx_emu: int = 5486400, cy_emu: int = 2743200):
    """Inline drawing XML. cx/cy in EMU (914400 EMU = 1 inch).
    Default: 6.0" × 3.0"."""
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
                    f'<pic:nvPicPr><pic:cNvPr id="{pic_id}" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr>'
                    '<pic:blipFill>'
                      f'<a:blip xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="{rid}"/>'
                      '<a:stretch><a:fillRect/></a:stretch>'
                    '</pic:blipFill>'
                    '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{0}" cy="{1}"/></a:xfrm>'.format(cx_emu, cy_emu) +
                      '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
                  '</pic:pic>'
                '</a:graphicData>'
              '</a:graphic>'
            '</wp:inline>'
          '</w:drawing></w:r>'
        '</w:p>'
    )

def make_caption(label: str, text: str):
    return (
        '<w:p>'
          '<w:pPr><w:jc w:val="center"/><w:spacing w:before="80" w:after="240"/></w:pPr>'
          f'<w:r><w:rPr><w:b/><w:bCs/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve">{label}</w:t></w:r>'
          f'<w:r><w:rPr><w:i/><w:iCs/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve">{text}</w:t></w:r>'
        '</w:p>'
    )

def make_panel_label(text: str):
    """Small italic label between sub-panels of a multi-panel figure."""
    return (
        '<w:p>'
          '<w:pPr><w:jc w:val="center"/><w:spacing w:before="40" w:after="40"/></w:pPr>'
          f'<w:r><w:rPr><w:i/><w:iCs/><w:sz w:val="16"/></w:rPr><w:t xml:space="preserve">{text}</w:t></w:r>'
        '</w:p>'
    )

# ─── Process each figure ───
new_rels_entries = []
anchor_use_count = {}  # for figures with same anchor — insert after Nth occurrence

for img_names, caption_label, caption_text, anchor_text in FIGURES:
    print(f'\n[fig] {caption_label} — anchor: "{anchor_text[:50]}"')

    # Build XML for all panels
    all_xml = ''
    for k, img_filename in enumerate(img_names):
        img_path = FIG_DIR / img_filename
        if not img_path.exists():
            print(f'  [!] missing image: {img_path}')
            continue
        img_bytes = img_path.read_bytes()
        img_name = f'image{next_img}.png'
        rid = f'rId{next_rid}'
        entries[f'word/media/{img_name}'] = img_bytes
        new_rels_entries.append(
            f'<Relationship Id="{rid}" '
            f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
            f'Target="media/{img_name}"/>'
        )
        print(f'  panel {k+1}: {img_filename} → {img_name} ({rid}, {len(img_bytes):,} B)')

        # Multi-panel separator label
        if len(img_names) > 1:
            panel_label = f'({chr(97+k)})'  # (a), (b), (c)
            all_xml += make_panel_label(panel_label)

        all_xml += make_drawing(rid, name=img_filename, cx_emu=5486400, cy_emu=2400000)
        next_rid += 1
        next_img += 1

    # Final caption
    all_xml += make_caption(caption_label, caption_text)

    # Find anchor in xml. For repeated anchors (e.g. "5.5 Fidelity-to-control gap"
    # used 3 times), insert at successive occurrences.
    occurrences = [m.start() for m in re.finditer(re.escape(anchor_text), xml)]
    if not occurrences:
        print(f'  [!] anchor not found: "{anchor_text}"')
        continue

    use_n = anchor_use_count.get(anchor_text, 0)
    if use_n >= len(occurrences):
        # If we ran out of fresh anchors, use the last one
        use_n = len(occurrences) - 1
    anchor_pos = occurrences[use_n]
    anchor_use_count[anchor_text] = use_n + 1

    # Find end of paragraph containing the anchor
    para_end = xml.find('</w:p>', anchor_pos) + len('</w:p>')
    if para_end <= len('</w:p>'):
        print(f'  [!] </w:p> not found after anchor')
        continue

    xml = xml[:para_end] + all_xml + xml[para_end:]
    print(f'  [ins] inserted at offset {para_end} (anchor use #{use_n+1} of {len(occurrences)})')

# ─── Splice new relationships ───
rels_xml = rels_xml.replace('</Relationships>', ''.join(new_rels_entries) + '</Relationships>')

entries['word/document.xml'] = xml.encode('utf-8')
entries['word/_rels/document.xml.rels'] = rels_xml.encode('utf-8')

tmp = SRC + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for n, data in entries.items():
        zo.writestr(n, data)
shutil.move(tmp, SRC)

print(f'\n[OK] {SRC} ({os.path.getsize(SRC):,} bytes)')
print(f'    Added {len(new_rels_entries)} new image relationships')
