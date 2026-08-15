"""
Build the Ain Shams Engineering Journal submission set from docs/paper_asej/.

Outputs (all written next to this script):
    manuscript.pdf    anonymized manuscript, two-column elsarticle 5p
    title_page.pdf    author/affiliation/funding page, uploaded separately
    supplementary.pdf reproduction detail; built HERE, not copied -- it diverges
                      from the long-format supplement in docs/paper_combined/
    declaration_of_competing_interests.pdf
    cover_letter_ASEJ.pdf
    author_biography.pdf

PAGE_LIMIT is 12, not the 10 stated in the guide. Recent accepted ASEJ articles run
~10 000 words with 9 figures and 7 tables, which cannot fit 10 pages in ANY layout,
so the guide's number is read as applying to the journal's own two-column format.
Twelve pages there is a normal full-length article; the guard exists to stop the
manuscript drifting well past that.

--disable-installer is not optional: without it, a missing package sends MiKTeX into
an interactive install dialog that hangs the build with no error.

Run:  python build_asej.py
"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGE_LIMIT = 12


def latex(cmd):
    print("  $", " ".join(cmd))
    r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
    if r.returncode != 0 and "pdflatex" in cmd[0]:
        # pdflatex returns non-zero on warnings too; only a missing PDF is fatal
        print(r.stdout[-2000:])
    return r


def build(stem, with_bib=False):
    print(f"[build] {stem}")
    pdf = HERE / f"{stem}.pdf"
    # An existing PDF open in a viewer makes pdflatex fail to write it, and a
    # stale-but-present file would otherwise sail through as if it had rebuilt.
    before = pdf.stat().st_mtime if pdf.exists() else None
    latex(["pdflatex", "-interaction=nonstopmode", "--disable-installer", f"{stem}.tex"])
    if with_bib:
        latex(["bibtex", stem])
        latex(["pdflatex", "-interaction=nonstopmode", "--disable-installer", f"{stem}.tex"])
    latex(["pdflatex", "-interaction=nonstopmode", "--disable-installer", f"{stem}.tex"])
    if not pdf.exists():
        sys.exit(f"!! {stem}.pdf was not produced -- see {stem}.log")
    if before is not None and pdf.stat().st_mtime == before:
        sys.exit(f"!! {stem}.pdf was NOT rewritten (stale). Close it in any PDF viewer "
                 f"and re-run; see {stem}.log")
    return pdf


def pages(pdf):
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    m = re.search(r"^Pages:\s+(\d+)", out, re.M)
    return int(m.group(1)) if m else -1


def check_anonymous(tex):
    """Double-anonymized review: nothing identifying may reach the manuscript file."""
    forbidden = ["Mukhanbet", "Sapargali", "Aibagarov", "Daribayev", "Shinassylov",
                 "Trigo", "Al-Farabi", "Digit Alem", "Shakarim", "Kazakhstan",
                 "ISEL", "AP23488794", "orcid", "gmail"]
    # strip LaTeX comments first: the file header legitimately names what must NOT
    # appear, and typesetters never see comments anyway
    text = re.sub(r"(?<!\\)%.*", "", tex.read_text(encoding="utf-8"))
    # match whole words only -- a bare substring test flags "preciSELy" for "ISEL"
    hits = [w for w in forbidden
            if re.search(r"(?<![A-Za-z])" + re.escape(w) + r"(?![A-Za-z])", text, re.I)]
    if hits:
        sys.exit(f"!! {tex.name} leaks identifying strings: {', '.join(hits)}")
    print(f"[check] {tex.name} is anonymous")


check_anonymous(HERE / "manuscript.tex")
check_anonymous(HERE / "supplementary.tex")  # reviewers see the supplement too

man = build("manuscript", with_bib=True)
n = pages(man)
print(f"[check] manuscript.pdf = {n} pages (limit {PAGE_LIMIT})")
if n > PAGE_LIMIT:
    sys.exit(f"!! OVER THE JOURNAL LIMIT by {n - PAGE_LIMIT} page(s) -- trim before submitting")

build("title_page")
build("declaration_of_competing_interests")
build("cover_letter_ASEJ")
build("author_biography")

# No page limit on the supplement, but it is published exactly as received, so a
# broken build ships as-is if nobody looks.
sup = build("supplementary")
print(f"[check] supplementary.pdf = {pages(sup)} pages")

print("\nSubmission set ready in", HERE)
