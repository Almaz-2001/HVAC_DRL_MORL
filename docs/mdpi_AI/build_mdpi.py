"""
Assemble a self-contained MDPI *AI* (Definitions/mdpi.cls) submission from the
Elsevier cas-sc source in docs/paper_combined/, reusing the identical prose,
equations, figures, tables and bibliography. Only the class-specific
frontmatter/backmatter (handled in ai_hvac_paradox.tex) and the cas-sc float
placement keys are adapted -- the scientific content is unchanged.

Run:  python build_mdpi.py     (from docs/mdpi_AI/)

Outputs, all next to Definitions/ and ai_hvac_paradox.tex:
  references.bib        copied verbatim from paper_combined
  figures/*.pdf         only the figures actually \includegraphics'd
  results1_body.tex     cas [pos={...}] -> MDPI float [H]
  results2_body.tex
  results3_body.tex
  body_content.tex      Nomenclature .. end of Conclusion, sliced from main_paper.tex
"""
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "paper_combined"


def _supp_labelmap():
    """label -> 'S<n>' from the freshly-compiled supplementary.aux (both counters)."""
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


def resolve_suppref(text: str) -> str:
    """Bake \\suppref{label} -> \\suppref{S<n>} so the article is self-contained
    (no xr / external-.aux dependency at journal-submission compile time)."""
    global _LABELMAP
    if _LABELMAP is None:
        _LABELMAP = _supp_labelmap()

    def rep(mo):
        key = mo.group(1)
        if re.fullmatch(r"S\d+", key):
            return mo.group(0)            # already a number
        if key in _LABELMAP:
            return "\\suppref{%s}" % _LABELMAP[key]
        print("  !! UNRESOLVED \\suppref{%s} (label not in supplementary.aux)" % key)
        return mo.group(0)

    return re.sub(r"\\suppref\{([^}]+)\}", rep, text)


def adapt(text: str) -> str:
    """Adapt cas-sc-isms to the MDPI class + bake supp references to numbers.

    * cas key-value float option [pos={!ht}] / [pos={t}] -> MDPI float [H]
    * \\includegraphics{\\detokenize{name}} -> {name} (MDPI graphicx reads the
      underscore filename verbatim, and \\detokenize is not always defined).
    * \\suppref{label} -> \\suppref{S<n>} resolved from supplementary.aux.
    """
    text = re.sub(r"\[pos=\{[^}]*\}\]", "[H]", text)
    text = re.sub(r"\\detokenize\{([^}]*)\}", r"\1", text)
    text = resolve_suppref(text)
    return text


bodies = ["results1_body.tex", "results2_body.tex", "results3_body.tex"]
for name in bodies:
    (HERE / name).write_text(
        adapt((SRC / name).read_text(encoding="utf-8")), encoding="utf-8"
    )

main = (SRC / "main_paper.tex").read_text(encoding="utf-8")
start = main.index(r"\section*{Nomenclature}")
end = main.index(r"\section*{CRediT authorship contribution statement}")
content = adapt(main[start:end]).rstrip() + "\n"
(HERE / "body_content.tex").write_text(content, encoding="utf-8")

shutil.copy(SRC / "references.bib", HERE / "references.bib")

alltex = content + "".join(
    (HERE / b).read_text(encoding="utf-8") for b in bodies
)
cited = set()
for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", alltex):
    base = m.group(1).strip()
    if base.lower().startswith("definitions/"):
        continue
    cited.add(base)

figdst = HERE / "figures"
figdst.mkdir(exist_ok=True)
copied, missing = 0, []
for base in sorted(cited):
    src = SRC / "figures" / base
    if src.suffix == "":
        src = src.with_suffix(".pdf")
    if src.exists():
        shutil.copy(src, figdst / src.name)
        copied += 1
    else:
        missing.append(base)

ga = SRC / "graphical_abstract.pdf"
if ga.exists():
    shutil.copy(ga, HERE / "graphical_abstract.pdf")

print(f"bodies adapted : {len(bodies)}")
print(f"content sliced : {len(content)} chars")
print(f"figures cited  : {len(cited)}  copied: {copied}")
if missing:
    print("  !! MISSING figures:", ", ".join(missing))
print(f"graphical abstract copied: {ga.exists()}")
