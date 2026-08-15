"""
Assemble a SELF-CONTAINED Results in Engineering (Elsevier cas-sc) submission
copy of the main article from docs/paper_combined/, baking every \\suppref{label}
into its literal supplementary S-number (read from the freshly compiled
supplementary.aux). The submitted main.tex then has NO xr / external-.aux
compile-order dependency -- the failure mode that otherwise renders every
\\suppref as "??" if a typesetter compiles the main before the supplement.

The development source (main_paper.tex + results{1,2,3}_body.tex) keeps the xr
mechanism for convenient editing; this script never modifies it. RINENG and MDPI
number their supplements independently, so the S-numbers are always read from
THIS directory's supplementary.aux, never shared.

Run (from docs/paper_combined/):
    pdflatex supplementary.tex                 # writes supplementary.aux (S-numbers)
    python build_rineng.py                     # writes rineng_submission/
    cd rineng_submission
    pdflatex main_paper.tex && bibtex main_paper && pdflatex main_paper && pdflatex main_paper
"""
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "rineng_submission"
BODIES = ["results1_body.tex", "results2_body.tex", "results3_body.tex"]
SUPPORT = ["references.bib", "cas-sc.cls", "cas-common.sty", "cas-model2-names.bst"]

# The exact xr preamble block in main_paper.tex to replace with a passthrough.
XR_BLOCK = (
    "% IMPORTANT build order: compile supplementary.tex FIRST (it writes supplementary.aux),\n"
    "% then compile this file. \\suppref{label} resolves supplementary S-numbers via xr's\n"
    "% externaldocument; the supp- prefix keeps supplement labels out of the main namespace\n"
    "% (avoids the tab:testcases collision). If main is compiled without supplementary.aux,\n"
    "% every \\suppref renders as \"??\".\n"
    "\\usepackage{xr}\n"
    "\\externaldocument[supp-]{supplementary}\n"
    "\\newcommand{\\suppref}[1]{\\ref{supp-#1}}\n"
)
PASSTHROUGH = (
    "% Self-contained RINENG submission build (build_rineng.py): supplementary\n"
    "% S-numbers are baked in below, so \\suppref is a plain passthrough and there is\n"
    "% no xr / supplementary.aux compile-order dependency.\n"
    "\\newcommand{\\suppref}[1]{#1}\n"
)


def supp_labelmap():
    aux = HERE / "supplementary.aux"
    if not aux.exists():
        raise SystemExit(
            "!! supplementary.aux not found -- compile supplementary.tex FIRST so "
            "\\suppref{label} can be baked into self-contained S-numbers.")
    m = {}
    for lab, num in re.findall(
            r"\\newlabel\{((?:tab|fig):[A-Za-z0-9_:-]+)\}\{\{(S\d+)\}",
            aux.read_text(encoding="utf-8")):
        m[lab] = num
    return m


_LABELMAP = None
_UNRESOLVED = set()


def bake_suppref(text: str) -> str:
    global _LABELMAP
    if _LABELMAP is None:
        _LABELMAP = supp_labelmap()

    def rep(mo):
        key = mo.group(1)
        if re.fullmatch(r"S\d+", key):
            return mo.group(0)
        if key in _LABELMAP:
            return "\\suppref{%s}" % _LABELMAP[key]
        _UNRESOLVED.add(key)
        return mo.group(0)

    return re.sub(r"\\suppref\{([^}]+)\}", rep, text)


OUT.mkdir(exist_ok=True)

# bodies: bake supp references only (nothing else changes for cas-sc)
for name in BODIES:
    (OUT / name).write_text(
        bake_suppref((HERE / name).read_text(encoding="utf-8")), encoding="utf-8")

# main: strip xr wiring -> passthrough, then bake supp references
main = (HERE / "main_paper.tex").read_text(encoding="utf-8")
if XR_BLOCK not in main:
    raise SystemExit("!! xr preamble block not found verbatim in main_paper.tex -- "
                     "it may have changed; update XR_BLOCK in build_rineng.py.")
main = main.replace(XR_BLOCK, PASSTHROUGH)
main = bake_suppref(main)
(OUT / "main_paper.tex").write_text(main, encoding="utf-8")

# support files
for name in SUPPORT:
    src = HERE / name
    if src.exists():
        shutil.copy(src, OUT / name)
    else:
        print("  !! missing support file:", name)

# cas-sc corresponding-author / social icons (thumbnails/cas-email.jpeg etc.)
thumb_src = HERE / "thumbnails"
if thumb_src.is_dir():
    shutil.copytree(thumb_src, OUT / "thumbnails", dirs_exist_ok=True)

# only the figures actually cited by main + bodies (+ the graphical abstract)
alltex = main + "".join((OUT / b).read_text(encoding="utf-8") for b in BODIES)
# unwrap \includegraphics{\detokenize{name}} -> \includegraphics{name} for name extraction
alltex_names = re.sub(r"\\detokenize\{([^}]*)\}", r"\1", alltex)
cited = set()
for mo in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", alltex_names):
    cited.add(mo.group(1).strip())

figdst = OUT / "figures"
figdst.mkdir(exist_ok=True)
copied, missing = 0, []
for base in sorted(cited):
    src = HERE / "figures" / base
    if src.suffix == "":
        src = src.with_suffix(".pdf")
    if src.exists():
        shutil.copy(src, figdst / src.name)
        copied += 1
    else:
        missing.append(base)

print(f"supp labels mapped : {len(_LABELMAP)}")
print(f"bodies baked       : {len(BODIES)}")
print(f"figures cited      : {len(cited)}  copied: {copied}")
if missing:
    print("  !! MISSING figures:", ", ".join(missing))
if _UNRESOLVED:
    print("  !! UNRESOLVED \\suppref labels:", ", ".join(sorted(_UNRESOLVED)))
else:
    print("all \\suppref labels resolved to S-numbers")
print(f"output dir         : {OUT}")
