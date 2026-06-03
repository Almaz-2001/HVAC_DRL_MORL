"""Insert the last missing Figure B3-5 after §7.6 Hypothesis closure."""
import zipfile, shutil, os, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pathlib import Path

SRC = 'docs/hvac_paper_skeleton_q1_restructured_patched.docx'
IMG = Path('reports/figures/article_real/main_block23/fig_block3_hypothesis_closure.png')

with zipfile.ZipFile(SRC) as z:
    entries = {n: z.read(n) for n in z.namelist()}

xml = entries['word/document.xml'].decode('utf-8')
rels_xml = entries['word/_rels/document.xml.rels'].decode('utf-8')

# Compute next rId and image_N
existing_rids = [int(m.group(1)) for m in re.finditer(r'Id="rId(\d+)"', rels_xml)]
next_rid = max(existing_rids) + 1
existing_images = [int(m.group(1)) for m in re.finditer(r'word/media/image(\d+)\.', '\n'.join(entries.keys()))]
next_img = max(existing_images) + 1

img_bytes = IMG.read_bytes()
img_name = f'image{next_img}.png'
rid = f'rId{next_rid}'

entries[f'word/media/{img_name}'] = img_bytes

new_rel = (f'<Relationship Id="{rid}" '
           f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
           f'Target="media/{img_name}"/>')
rels_xml = rels_xml.replace('</Relationships>', new_rel + '</Relationships>')

drawing_xml = (
    '<w:p>'
      '<w:pPr><w:jc w:val="center"/></w:pPr>'
      '<w:r><w:drawing>'
        '<wp:inline distT="0" distB="0" distL="0" distR="0" '
                   'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">'
          '<wp:extent cx="5486400" cy="2743200"/>'
          '<wp:effectExtent l="0" t="0" r="0" b="0"/>'
          f'<wp:docPr id="{next_rid}" name="Figure B3-5"/>'
          '<wp:cNvGraphicFramePr><a:graphicFrameLocks '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
          '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
              '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
                f'<pic:nvPicPr><pic:cNvPr id="{next_rid}" name="Figure B3-5"/><pic:cNvPicPr/></pic:nvPicPr>'
                '<pic:blipFill>'
                  f'<a:blip xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="{rid}"/>'
                  '<a:stretch><a:fillRect/></a:stretch>'
                '</pic:blipFill>'
                '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="5486400" cy="2743200"/></a:xfrm>'
                  '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
              '</pic:pic>'
            '</a:graphicData>'
          '</a:graphic>'
        '</wp:inline>'
      '</w:drawing></w:r>'
    '</w:p>'
)
caption_xml = (
    '<w:p>'
      '<w:pPr><w:jc w:val="center"/><w:spacing w:before="80" w:after="240"/></w:pPr>'
      '<w:r><w:rPr><w:b/><w:bCs/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve">Figure B3-5.</w:t></w:r>'
      '<w:r><w:rPr><w:i/><w:iCs/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve">'
      ' Pre-registered predictions vs observed outcomes (stretch testcase). '
      'Two predictions are FALSIFIED (mode=none controller verdict; scale-dependent C_zon hypothesis B); '
      'three are CONFIRMED (RMSE gain inside [50, 90] %; uniform hydronic-family C_zon hypothesis A; '
      'pipeline convergence). Both surprises shifted support to LOWER a-priori alternatives — the desired '
      'direction of Popperian falsifiability. Source: configs/block3_testcase_manifest.yaml '
      '`stretch_testcase_predictions` block + aggregated_results.'
      '</w:t></w:r>'
    '</w:p>'
)

# Insert after §7.6 paragraph. Find the §7.6 heading text and find next §8 heading.
anchor_76 = '7.6 Hypothesis closure and threshold caveat'
anchor_8  = '8. Discussion'
pos_76 = xml.find(anchor_76)
pos_8  = xml.find(anchor_8)
assert pos_76 > 0 and pos_8 > pos_76, f'anchors not found: 7.6@{pos_76}, 8@{pos_8}'

# Find paragraph end right BEFORE §8 (i.e., the last paragraph of §7.6 body)
para_end_before_8 = xml.rfind('</w:p>', pos_76, pos_8) + len('</w:p>')

xml = xml[:para_end_before_8] + drawing_xml + caption_xml + xml[para_end_before_8:]
print(f'[ins] Figure B3-5 inserted at offset {para_end_before_8}')

entries['word/document.xml'] = xml.encode('utf-8')
entries['word/_rels/document.xml.rels'] = rels_xml.encode('utf-8')

tmp = SRC + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for n, data in entries.items():
        zo.writestr(n, data)
shutil.move(tmp, SRC)
print(f'[OK] {SRC} ({os.path.getsize(SRC):,} bytes)')
