"""Build the IEEE Access submission from the shared manuscript source.

Design, same as build_energies.py: Related work, Materials and methods and
Results and discussion are sliced VERBATIM out of ../paper_asej/manuscript.tex
so there is one source of truth for the science. Title, abstract, introduction,
conclusions, author block and biographies are hand-written in
ieee_access_hvac.tex, because those are the parts a target journal actually
changes.

Why IEEE Access at all: RINENG and ASEJ desk-rejected on novelty, and Energies
returned the paper at technical pre-check as out of scope for an energy journal
-- explicitly not on quality. The contribution is methodological (which
surrogate to train an RL controller on), demonstrated on an HVAC case study, and
IEEE Access states that it welcomes multidisciplinary, applications-oriented and
negative results that do not fit the traditional journals.

Class file caveat
-----------------
The official IEEE Access template ships `ieeeaccess.cls` in the IEEE Author
Center ZIP; it is not on CTAN and is not installed here. This build uses stock
`IEEEtran.cls` with the `journal` option, which gives the same two-column body,
fonts, float and reference style. What it does not give is the Access-specific
first-page furniture (open-access banner, DOI line, CC-BY footer) -- production
material that IEEE fills in anyway. Drop the finished body into the official
template before submitting; see SUBMISSION_NOTES.md.

Run:  python docs/ieee_access/build_ieee.py
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "paper_asej"

BODY_SLICES = [
    ("body_related.tex", r"\section{Related work}", r"\section{Materials and methods}"),
    ("body_methods.tex", r"\section{Materials and methods}", r"\section{Results and discussion}"),
    ("body_results.tex", r"\section{Results and discussion}", r"\section{Conclusions}"),
]

# The ASEJ manuscript is anonymised for double-blind review. IEEE Access is
# single-blind, so the body may name the authors' own prior work; nothing in the
# sliced sections currently does, but the check below fails loudly if a future
# edit introduces an "Author et al." placeholder that would read as a gap.
ANON_MARKERS = ["[ANONYMIZED]", "[ANON]", "Anonymous et al", "the authors' prior work"]


def retarget(tex: str) -> str:
    """elsarticle 5p -> IEEEtran journal. Both are two-column, so float widths
    carry over unchanged; only float placement and table caption position move."""
    # IEEE style puts table captions above the tabular and figure captions below.
    tex = lift_table_captions(tex)
    # elsarticle tolerates [h]; IEEEtran's narrow column does not, and a stuck
    # float silently reorders the results section.
    tex = re.sub(r"\\begin\{(figure|table)\}\[[^\]]*\]", r"\\begin{\1}[!t]", tex)
    tex = re.sub(r"\\begin\{(figure|table)\*\}\[[^\]]*\]", r"\\begin{\1*}[!t]", tex)
    return tex


def _match_brace(s: str, open_idx: int) -> int:
    """Index just past the '}' matching the '{' at open_idx. Captions nest
    braces (\\emph{...}, $\\ms>1$), so a non-greedy regex truncates them and
    leaves an unbalanced argument behind."""
    depth = 0
    i = open_idx
    while i < len(s):
        if s[i] == "\\":            # skip an escaped brace
            i += 2
            continue
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError("unbalanced braces in caption")


def lift_table_captions(tex: str) -> str:
    """Move \\caption{...} from below the tabular to directly after \\begin{table}."""
    out = []
    for block in re.split(r"(\\begin\{table\*?\}.*?\\end\{table\*?\})", tex, flags=re.S):
        if not block.startswith(r"\begin{table"):
            out.append(block)
            continue
        cap_start = block.find(r"\caption{")
        tab_start = block.find(r"\begin{tabular")
        if cap_start == -1 or (tab_start != -1 and cap_start < tab_start):
            out.append(block)          # no caption, or already above the tabular
            continue
        cap_end = _match_brace(block, cap_start + len(r"\caption"))
        cap = block[cap_start:cap_end]
        rest = block[:cap_start].rstrip() + "\n" + block[cap_end:].lstrip("\n")
        head = re.match(r"(\\begin\{table\*?\}(?:\[[^\]]*\])?\s*\n(?:\s*\\centering\s*\n)?)", rest)
        insert = head.end() if head else rest.index("\n") + 1
        out.append(rest[:insert] + cap + "\n" + rest[insert:])
    return "".join(out)


# The supplement is a standalone article-class document, so it carries over
# without a class change. Only the parent-paper references need retargeting.
SUPP_SUBS = [
    (r"""\title{Supplementary Material for\\[2pt]
\emph{Predictive fidelity versus training utility in surrogate-based reinforcement
learning for HVAC control: a role-separated hybrid remedy}}""",
     r"""\title{Supplementary Material for\\[2pt]
\emph{Surrogate Selection for Reinforcement-Learning HVAC Control: Step Size,
Not Predictive Accuracy, Predicts Control Utility}}"""),

    (r"""The main article is a short-format paper: it reports every numerical value needed to evaluate the central fidelity--utility claim, but it cannot carry the reproduction detail. This Supplement carries that detail.""",
     r"""The main article reports every numerical value needed to evaluate the surrogate-selection claim and the role-separated architecture, but not the reproduction detail behind them. This Supplement carries that detail."""),
]


def build_supplement() -> set[str]:
    src = (SRC / "supplementary.tex").read_text(encoding="utf-8")
    for old, new in SUPP_SUBS:
        if old not in src:
            sys.exit("!! supplement substitution no longer matches:\n    " + old[:90])
        src = src.replace(old, new, 1)
    (HERE / "supplementary.tex").write_text(src, encoding="utf-8")
    print("[derive] supplementary.tex")
    flat = re.sub(r"\\detokenize\{([^}]*)\}", r"\1", src)
    return set(re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", flat))


def slice_body(src: str, start: str, end: str) -> str:
    a = src.index(start)
    b = src.index(end, a)
    return src[a:b].rstrip() + "\n"


def main() -> None:
    manuscript = (SRC / "manuscript.tex").read_text(encoding="utf-8")

    for name, start, end in BODY_SLICES:
        body = slice_body(manuscript, start, end)
        hits = [m for m in ANON_MARKERS if m in body]
        if hits:
            sys.exit(f"!! {name} still carries anonymisation placeholders: {hits}")
        (HERE / name).write_text(retarget(body), encoding="utf-8")
        print(f"[slice] {name}")

    shutil.copy(SRC / "references_asej.bib", HERE / "references.bib")
    print("[copy]  references.bib")

    figdir = HERE / "figures"
    figdir.mkdir(exist_ok=True)
    body = "".join((HERE / n).read_text(encoding="utf-8") for n, _, _ in BODY_SLICES)
    body += (HERE / "ieee_access_hvac.tex").read_text(encoding="utf-8")
    flat = re.sub(r"\\detokenize\{([^}]*)\}", r"\1", body)
    wanted = set(re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", flat))
    wanted |= build_supplement()      # the supplement pulls ~30 figures of its own
    missing = []
    for f in sorted(wanted):
        s = SRC / "figures" / f
        if s.exists():
            shutil.copy(s, figdir / s.name)
        else:
            missing.append(f)
    print(f"[figs]  {len(wanted) - len(missing)} copied")
    if missing:
        sys.exit(f"!! missing figures: {missing}")

    stem = "ieee_access_hvac"
    pdf = HERE / f"{stem}.pdf"
    before = pdf.stat().st_mtime if pdf.exists() else None

    for cmd in (["pdflatex", "-interaction=nonstopmode", "--disable-installer", f"{stem}.tex"],
                ["bibtex", stem],
                ["pdflatex", "-interaction=nonstopmode", "--disable-installer", f"{stem}.tex"],
                ["pdflatex", "-interaction=nonstopmode", "--disable-installer", f"{stem}.tex"]):
        print("  $", " ".join(cmd))
        subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)

    if not pdf.exists():
        sys.exit(f"!! {stem}.pdf was not produced -- read {stem}.log")
    if before is not None and pdf.stat().st_mtime == before:
        sys.exit(f"!! {stem}.pdf was NOT rewritten (stale). Close it in any viewer and re-run")

    pages = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    n = next((l.split()[-1] for l in pages.splitlines() if l.startswith("Pages")), "?")
    print(f"[build] {stem}.pdf = {n} pages")

    log = (HERE / f"{stem}.log").read_text(encoding="utf-8", errors="ignore")
    undefined = sorted(set(re.findall(r"Citation `([^']+)' undefined", log)))
    if undefined:
        print(f"!! undefined citations: {undefined}")
    if "There were undefined references" in log:
        print("!! undefined references remain -- check \\ref targets")
    overfull = len(re.findall(r"Overfull \\hbox", log))
    print(f"[check] {overfull} overfull hboxes")

    for cmd in (["pdflatex", "-interaction=nonstopmode", "--disable-installer", "supplementary.tex"],
                ["bibtex", "supplementary"],
                ["pdflatex", "-interaction=nonstopmode", "--disable-installer", "supplementary.tex"],
                ["pdflatex", "-interaction=nonstopmode", "--disable-installer", "supplementary.tex"]):
        subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
    supp = HERE / "supplementary.pdf"
    if supp.exists():
        pages = subprocess.run(["pdfinfo", str(supp)], capture_output=True, text=True).stdout
        n = next((l.split()[-1] for l in pages.splitlines() if l.startswith("Pages")), "?")
        print(f"[build] supplementary.pdf = {n} pages")
    else:
        print("!! supplementary.pdf was not produced -- read supplementary.log")

    flatten()


def flatten() -> None:
    """Write ieee_access_hvac_onefile.tex with the body files spliced in.

    Regenerated on every build so it cannot go stale. Journals want one source
    file, and shipping four invites the wrong one being picked as the main
    document.
    """
    src = (HERE / "ieee_access_hvac.tex").read_text(encoding="utf-8")
    for name, _, _ in BODY_SLICES:
        marker = "\\input{" + name + "}"
        if marker not in src:
            sys.exit(f"!! cannot flatten: {marker} not found in ieee_access_hvac.tex")
        body = (HERE / name).read_text(encoding="utf-8").rstrip()
        src = src.replace(
            marker,
            f"% ---- begin {name} (spliced by build_ieee.py; edit the source, not here)\n"
            f"{body}\n"
            f"% ---- end {name}",
            1,
        )
    out = HERE / "ieee_access_hvac_onefile.tex"
    out.write_text(src, encoding="utf-8")
    n = len(src.splitlines())
    print(f"[flat]  {out.name} = {n} lines, no \\input remaining")


if __name__ == "__main__":
    main()
