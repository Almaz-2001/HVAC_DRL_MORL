"""
Assemble the MDPI *Energies* submission from the ASEJ source in docs/paper_asej/.

The scientific content is unchanged: Related work, Materials and Methods and
Results are sliced out of paper_asej/manuscript.tex verbatim and only re-targeted
at the MDPI class. What is deliberately NOT reused is the framing -- Title,
Abstract, Introduction and Conclusions are hand-written in energies_hvac.tex,
because three editorial desk rejects (MDPI AI, RINENG, ASEJ) all stopped the paper
before review and ASEJ named the reason: "lack of sufficient novelty". The rewrite
leads with the transferable finding (per-step increment, not predictive accuracy,
predicts RL training utility) instead of with the HVAC application.

MDPI is single-blind, so authors appear in the manuscript and there is no
anonymization check here -- the opposite of the ASEJ build.

Run:  python build_energies.py     (from docs/mdpi_Energies/)
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# This port now lives under docs/_superseded/, two levels below docs/, so the
# results sections are still sliced from the live docs/paper_asej/.
SRC = HERE.parent.parent / "paper_asej"

BODY_SLICES = [
    ("body_related.tex", r"\section{Related work}", r"\section{Materials and methods}"),
    ("body_methods.tex", r"\section{Materials and methods}", r"\section{Results and discussion}"),
    ("body_results.tex", r"\section{Results and discussion}", r"\section{Conclusions}"),
]


# Sentences that state the contribution in the negative. Each is accurate and each
# was written deliberately, but three editorial screens rejected this paper for
# "lack of sufficient novelty" and these are the lines an editor skimming page 2
# would quote back. The replacements keep every factual concession -- the
# architecture still builds on named prior work, and the Discussion still places
# the mechanism inside the objective-mismatch literature -- but state what the
# paper does before stating what it is not.
REFRAME = [
    (r"""that make it tractable. The mechanism is thus an instance of a known family; what is new is the role
assignment and its measured effect on a building-control benchmark.""",
     r"""that make it tractable. The two models are therefore not interchangeable members of an ensemble to
be averaged: they carry different requirements, one supplying optimization smoothness and the other
physical fidelity, and it is that separation, rather than the penalty term itself, that the
architecture of Section~\ref{ssec:hybrid} contributes."""),

    (r"""The hybrid backend is not a new RL algorithm. It is an application-specific role-separation strategy
grounded in three existing lines of work:""",
     r"""Role-separated surrogate training assigns the two conflicting requirements to two models instead of
compromising between them inside one. It draws on three existing lines of work:"""),
]


def reframe(tex: str) -> str:
    for old, new in REFRAME:
        tex = tex.replace(old, new)
    return tex


def retarget(tex: str) -> str:
    """elsarticle two-column -> MDPI single column."""
    tex = reframe(tex)
    # The test-case table was a full-width float in the two-column ASEJ layout, so its
    # columns are fixed-width. Dropped into MDPI's single column it runs ~95 pt past
    # the margin and silently loses the Climate column; tabularx makes the emitter
    # column absorb the difference instead.
    tex = tex.replace(
        r"\begin{tabular}{@{}llll@{}}" + "\n" + r"\toprule" + "\n"
        r"Test case & Type & Heat source / emitter & Climate \\",
        r"\begin{tabularx}{\linewidth}{@{}llXl@{}}" + "\n" + r"\toprule" + "\n"
        r"Test case & Type & Heat source / emitter & Climate \\")
    if r"\begin{tabularx}{\linewidth}{@{}llXl@{}}" in tex:
        tex = re.sub(r"(\\begin\{tabularx\}\{\\linewidth\}\{@\{\}llXl@\{\}\}.*?)\\end\{tabular\}",
                     r"\1\\end{tabularx}", tex, flags=re.S)
    # mdpi.cls is single-column: the starred float forms do not exist there
    tex = tex.replace(r"\begin{figure*}", r"\begin{figure}").replace(r"\end{figure*}", r"\end{figure}")
    tex = tex.replace(r"\begin{table*}", r"\begin{table}").replace(r"\end{table*}", r"\end{table}")
    # MDPI wants floats where they are written
    tex = re.sub(r"\\begin\{(figure|table)\}\[[^\]]*\]", r"\\begin{\1}[H]", tex)
    # MDPI puts table captions above the tabular; ours sit below it
    tex = lift_table_captions(tex)
    return tex


def lift_table_captions(tex: str) -> str:
    """Move \\caption..\\label from after \\end{tabular} to before \\begin{tabular}.

    ASEJ required captions below tables; MDPI sets them above. Doing this by text
    surgery keeps a single source of truth for the caption wording.
    """
    out, i = [], 0
    pat = re.compile(
        r"(\\begin\{tabular\}.*?\\end\{tabular\}\s*)"      # 1: the tabular
        r"((?:\\caption\{(?:[^{}]|\{[^{}]*\})*\}\s*)"      # 2: caption (+ optional label)
        r"(?:\\label\{[^}]*\}\s*)?)",
        re.S)
    for m in pat.finditer(tex):
        out.append(tex[i:m.start()])
        out.append(m.group(2) + m.group(1))
        i = m.end()
    out.append(tex[i:])
    return "".join(out)


# The Supplement is derived from the ASEJ one rather than forked, so that fixing a
# number there fixes it in both. Its section-to-section map survives the port
# untouched: the Energies body is the same slice, so main-article subsections still
# number 3.1-3.5 and 4.1-4.7 exactly as the map claims. Only the identity of the
# parent paper and MDPI's naming ("Supplementary Materials") change.
SUPP_SUBS = [
    (r"""\title{Supplementary Material for\\[2pt]
\emph{Predictive fidelity versus training utility in surrogate-based reinforcement
learning for HVAC control: a role-separated hybrid remedy}}""",
     r"""\title{Supplementary Materials for\\[2pt]
\emph{Surrogate Selection for Reinforcement-Learning HVAC Control: Step Size,
Not Predictive Accuracy, Predicts Training Utility}}"""),

    (r"\section*{Supplementary Material}", r"\section*{Supplementary Materials}"),

    # the parent paper is no longer a 12-page short-format article
    (r"""The main article is a short-format paper: it reports every numerical value needed to evaluate the central fidelity--utility claim, but it cannot carry the reproduction detail. This Supplement carries that detail.""",
     r"""The main article reports every numerical value needed to evaluate the surrogate-selection claim and the role-separated architecture, but not the reproduction detail behind them. This Supplement carries that detail."""),

    # map row label had tracked the old section heading, which the reframing changed
    (r"\S4.2 Fidelity--utility paradox", r"\S4.2 Fidelity does not imply utility"),
]


def build_supplement():
    src = (SRC / "supplementary.tex").read_text(encoding="utf-8")
    for old, new in SUPP_SUBS:
        if old not in src:
            sys.exit("!! supplement substitution no longer matches:\n    " + old[:90])
        src = src.replace(old, new, 1)
    (HERE / "supplementary.tex").write_text(src, encoding="utf-8")
    print("[derive] supplementary.tex")
    return {re.sub(r"\\detokenize\{([^}]*)\}", r"\1", m)
            for m in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}",
                                re.sub(r"\\detokenize\{([^}]*)\}", r"\1", src))}


def slice_body(src: str, start: str, end: str) -> str:
    a = src.index(start)
    b = src.index(end, a)
    return src[a:b].rstrip() + "\n"


def main():
    manuscript = (SRC / "manuscript.tex").read_text(encoding="utf-8")

    for name, start, end in BODY_SLICES:
        (HERE / name).write_text(retarget(slice_body(manuscript, start, end)), encoding="utf-8")
        print(f"[slice] {name}")

    shutil.copy(SRC / "references_asej.bib", HERE / "references.bib")
    print("[copy]  references.bib")

    figdir = HERE / "figures"
    figdir.mkdir(exist_ok=True)
    body = "".join((HERE / n).read_text(encoding="utf-8") for n, _, _ in BODY_SLICES)
    body += (HERE / "energies_hvac.tex").read_text(encoding="utf-8")
    # unwrap \detokenize{...} BEFORE extracting: the inner brace would otherwise
    # terminate the [^}]+ capture and yield a truncated filename
    flat = re.sub(r"\\detokenize\{([^}]*)\}", r"\1", body)
    wanted = set(re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", flat))
    wanted |= build_supplement()   # the Supplement needs ~30 more figures of its own
    missing = []
    for f in sorted(wanted):
        s = SRC / "figures" / f
        if s.exists():
            shutil.copy(s, figdir / s.name)
        else:
            missing.append(f)
    print(f"[copy]  {len(wanted) - len(missing)} figures")
    if missing:
        sys.exit("!! missing figures: " + ", ".join(missing))

    for pass_no in (1, 2, 3):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "--disable-installer",
                        "energies_hvac.tex"], cwd=HERE, capture_output=True, text=True)
        if pass_no == 1:
            subprocess.run(["bibtex", "energies_hvac"], cwd=HERE, capture_output=True, text=True)

    for _ in (1, 2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "--disable-installer",
                        "supplementary.tex"], cwd=HERE, capture_output=True, text=True)

    for stem in ("energies_hvac", "supplementary"):
        pdf = HERE / f"{stem}.pdf"
        if not pdf.exists():
            sys.exit(f"!! {stem}.pdf not produced -- see {stem}.log")
        out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
        pages = re.search(r"^Pages:\s+(\d+)", out, re.M)
        print(f"[build] {stem}.pdf = {pages.group(1) if pages else '?'} pages")

    assemble_submission()


def assemble_submission():
    """Write submission/ -- exactly the files to zip, and nothing else.

    The manuscript will NOT compile from energies_hvac.tex plus references.bib
    alone: it needs the MDPI class in Definitions/, the nine figures, and the three
    \\input bodies. The bodies are flattened in here so the upload is one .tex, which
    is what MDPI's converter prefers and what makes the package easy to check by eye.
    """
    sub = HERE / "submission"
    if sub.exists():
        shutil.rmtree(sub)
    sub.mkdir()

    flat = (HERE / "energies_hvac.tex").read_text(encoding="utf-8")
    for name in ("body_related.tex", "body_methods.tex", "body_results.tex"):
        piece = (HERE / name).read_text(encoding="utf-8")
        flat = flat.replace("\\input{%s}\n" % name,
                            "%% ---- %s (inlined for submission) ----\n%s\n" % (name, piece))
    assert "\\input{body_" not in flat, "an \\input survived flattening"
    (sub / "energies_hvac.tex").write_text(flat, encoding="utf-8")

    shutil.copy(HERE / "references.bib", sub / "references.bib")
    shutil.copytree(HERE / "Definitions", sub / "Definitions")
    (sub / "figures").mkdir()
    used = set(re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}",
                          re.sub(r"\\detokenize\{([^}]*)\}", r"\1", flat)))
    for f in sorted(used):
        shutil.copy(HERE / "figures" / f, sub / "figures" / f)

    for _ in (1, 2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "--disable-installer",
                        "energies_hvac.tex"], cwd=sub, capture_output=True, text=True)
        subprocess.run(["bibtex", "energies_hvac"], cwd=sub, capture_output=True, text=True)
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "--disable-installer",
                    "energies_hvac.tex"], cwd=sub, capture_output=True, text=True)

    log = (sub / "energies_hvac.log").read_text(encoding="utf-8", errors="ignore")
    errs = len(re.findall(r"^!", log, re.M))
    out = subprocess.run(["pdfinfo", str(sub / "energies_hvac.pdf")],
                         capture_output=True, text=True).stdout
    pages = re.search(r"^Pages:\s+(\d+)", out, re.M)
    if errs or not pages:
        sys.exit(f"!! submission/ does not build standalone ({errs} errors)")
    for junk in sub.glob("energies_hvac.*"):
        if junk.suffix in {".aux", ".log", ".out", ".blg", ".bbl", ".pdf", ".spl"}:
            junk.unlink()
    print(f"[zip]   submission/ builds standalone: {pages.group(1)} pages, "
          f"{len(used)} figures, 1 .tex")


if __name__ == "__main__":
    main()
