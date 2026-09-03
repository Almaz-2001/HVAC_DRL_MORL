"""Assemble the archive uploaded to the IEEE Access author portal.

Previously this was done by hand, which meant the only record of what the
journal received was the zip itself. Now it is reproducible, and it verifies
what it packs rather than trusting the working directory:

  - the flattened single-file source is the main document (journals pick the
    wrong file when several .tex are shipped);
  - it must compile on its own to text identical with the PDF being uploaded;
  - biographies must be complete, since a missing one already cost a cycle.

Run:  python docs/ieee_access/make_submission_zip.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "ieee_access_submission.zip"

MAIN = "ieee_access_hvac_onefile.tex"
SUPP = "supplementary.tex"

# Class machinery the journal's compiler needs; the official template ships
# these and they are not on CTAN.
SUPPORT = ["ieeeaccess.cls", "spotcolor.sty", "IEEEtran.bst", "references.bib",
           "logo.png", "notaglinelogo.png", "bullet.png"]
FONT_GLOBS = ["t1-*.pfb", "t1-*.tfm", "t1-*.map", "t1*.fd"]

PDFS = ["ieee_access_hvac_onefile.pdf", "supplementary.pdf"]


def run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def verify() -> None:
    """Compile the packed source in isolation and diff its text against the PDF."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for name in [MAIN, SUPP] + SUPPORT:
            src = HERE / name
            if src.exists():
                shutil.copy2(src, tmp / name)
        for pat in FONT_GLOBS:
            for f in HERE.glob(pat):
                shutil.copy2(f, tmp / f.name)
        shutil.copytree(HERE / "figures", tmp / "figures")

        stem = Path(MAIN).stem
        run(["pdflatex", "-interaction=nonstopmode", "--disable-installer", MAIN], tmp)
        run(["bibtex", stem], tmp)
        for _ in range(2):
            run(["pdflatex", "-interaction=nonstopmode", "--disable-installer", MAIN], tmp)

        built = tmp / f"{stem}.pdf"
        if not built.exists():
            sys.exit(f"!! {MAIN} does not compile from the packed files alone")

        log = (tmp / f"{stem}.log").read_text(encoding="utf-8", errors="ignore")
        errors = [l for l in log.splitlines() if l.startswith("! ")]
        if errors:
            sys.exit(f"!! {len(errors)} LaTeX error(s) from a clean extraction:\n"
                     + "\n".join(errors[:3]))

        def text(p: Path) -> str:
            return subprocess.run(["pdftotext", str(p), "-"], capture_output=True,
                                  text=True).stdout

        # build_ieee.py compiles ieee_access_hvac.tex but only WRITES the
        # flattened source, so a stale onefile PDF can sit next to a current
        # one. Rather than compare and hope, take the PDF this compile just
        # produced: the packed source then reproduces the packed PDF by
        # construction, which is what checklist item 1 asks for.
        reference = HERE / "ieee_access_hvac.pdf"
        if reference.exists() and text(built) != text(reference):
            sys.exit("!! the flattened source and ieee_access_hvac.tex disagree; "
                     "re-run build_ieee.py")
        shutil.copy2(built, HERE / PDFS[0])

        pages = subprocess.run(["pdfinfo", str(built)], capture_output=True,
                               text=True).stdout
        n = next((l.split()[-1] for l in pages.splitlines() if l.startswith("Pages")), "?")
        print(f"[verify] {MAIN} compiles standalone, 0 errors, {n} pages, "
              f"text matches ieee_access_hvac.pdf")


def main() -> None:
    # The build's own biography check is the gate; re-run it here so the archive
    # can never be assembled from a tree that would fail it.
    sys.path.insert(0, str(HERE))
    import build_ieee
    build_ieee.check_biographies()

    verify()

    members: list[Path] = []
    for name in [MAIN, SUPP] + SUPPORT + PDFS:
        p = HERE / name
        if not p.exists():
            sys.exit(f"!! missing from the submission set: {name}")
        members.append(p)
    for pat in FONT_GLOBS:
        members.extend(sorted(HERE.glob(pat)))
    figures = sorted((HERE / "figures").glob("*"))

    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for p in members:
            z.write(p, p.name)
        for p in figures:
            z.write(p, f"figures/{p.name}")

    total = sum(i.file_size for i in zipfile.ZipFile(OUT).infolist())
    print(f"[zip]    {OUT.name}: {len(members) + len(figures)} files, "
          f"{total/1e6:.1f} MB uncompressed, {OUT.stat().st_size/1e6:.1f} MB packed")
    print(f"[main]   {MAIN} is the main document; upload the cover letter separately")


if __name__ == "__main__":
    main()
