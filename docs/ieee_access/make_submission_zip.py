"""Assemble the archives uploaded to the IEEE Access author portal.

The portal is explicit about the split:

  "Your Main Manuscript document ... may include embedded figures and tables,
   but should not include any supplementary materials. You may bundle LaTeX
   manuscript files in a single archive including all LaTeX files, BibTeX
   files, figures, tables, all LaTeX classes and packages, and any other
   material that belongs to your main manuscript."

So two archives, not one. The figures are the part that actually matters: the
build copies the union of both documents' figures into one folder, and 30 of
the 39 belong to the supplement alone. Bundling those with the main manuscript
would be shipping supplementary material inside it.

The main bundle is verified by compiling it in an isolated copy of ONLY its own
packed files, which also proves the figure split is right -- a figure assigned
to the wrong archive shows up as a missing-file error rather than silently.

Run:  python docs/ieee_access/make_submission_zip.py
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCS = HERE.parent

MAIN_TEX, MAIN_PDF = "ieee_access_hvac_onefile.tex", "ieee_access_hvac_onefile.pdf"
SUPP_TEX, SUPP_PDF = "supplementary.tex", "supplementary.pdf"

MAIN_ZIP = DOCS / "ieee_access_main_manuscript.zip"
SUPP_ZIP = DOCS / "ieee_access_supplementary.zip"

# Class machinery the journal's compiler needs: the official template ships
# these and they are not on CTAN. The supplement is a plain article-class
# document with no bibliography, so it needs none of them.
SUPPORT = ["ieeeaccess.cls", "spotcolor.sty", "IEEEtran.bst", "references.bib",
           "logo.png", "notaglinelogo.png", "bullet.png"]
FONT_GLOBS = ["t1-*.pfb", "t1-*.tfm", "t1-*.map", "t1*.fd"]

INCLUDE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")


def figures_used_by(tex: str) -> set[str]:
    """Figure file names actually drawn by this document."""
    txt = (HERE / tex).read_text(encoding="utf-8")
    txt = "\n".join(l for l in txt.splitlines() if not l.lstrip().startswith("%"))
    txt = re.sub(r"\\detokenize\{([^}]*)\}", r"\1", txt)
    on_disk = {p.name: p for p in (HERE / "figures").glob("*")}
    out = set()
    for name in INCLUDE.findall(txt):
        if name in on_disk:
            out.add(name)
        else:                       # the .tex may omit the extension
            out.update(f for f in on_disk if Path(f).stem == Path(name).stem)
    return out


def run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def pdf_text(p: Path) -> str:
    return subprocess.run(["pdftotext", str(p), "-"], capture_output=True,
                          text=True).stdout


def verify_main(figs: set[str]) -> None:
    """Compile the main bundle from its own files alone, then adopt that PDF."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for name in [MAIN_TEX] + SUPPORT:
            shutil.copy2(HERE / name, tmp / name)
        for pat in FONT_GLOBS:
            for f in HERE.glob(pat):
                shutil.copy2(f, tmp / f.name)
        (tmp / "figures").mkdir()
        for f in figs:
            shutil.copy2(HERE / "figures" / f, tmp / "figures" / f)

        stem = Path(MAIN_TEX).stem
        run(["pdflatex", "-interaction=nonstopmode", "--disable-installer", MAIN_TEX], tmp)
        run(["bibtex", stem], tmp)
        for _ in range(2):
            run(["pdflatex", "-interaction=nonstopmode", "--disable-installer", MAIN_TEX], tmp)

        built = tmp / f"{stem}.pdf"
        if not built.exists():
            sys.exit(f"!! {MAIN_TEX} does not compile from the packed files alone")

        log = (tmp / f"{stem}.log").read_text(encoding="utf-8", errors="ignore")
        errors = [l for l in log.splitlines() if l.startswith("! ")]
        if errors:
            sys.exit(f"!! {len(errors)} LaTeX error(s) from a clean extraction:\n"
                     + "\n".join(errors[:3]))
        missing = re.findall(r"File `([^']+)' not found", log)
        if missing:
            sys.exit(f"!! files missing from the main bundle: {missing[:5]}")

        # build_ieee.py compiles ieee_access_hvac.tex but only WRITES the
        # flattened source, so the two can drift. Compare, then adopt the PDF
        # this compile produced: the packed source then reproduces the packed
        # PDF by construction.
        reference = HERE / "ieee_access_hvac.pdf"
        if reference.exists() and pdf_text(built) != pdf_text(reference):
            sys.exit("!! the flattened source and ieee_access_hvac.tex disagree; "
                     "re-run build_ieee.py")
        shutil.copy2(built, HERE / MAIN_PDF)

        pages = subprocess.run(["pdfinfo", str(built)], capture_output=True,
                               text=True).stdout
        n = next((l.split()[-1] for l in pages.splitlines() if l.startswith("Pages")), "?")
        print(f"[verify] main compiles from its own {len(figs)} figures alone, "
              f"0 errors, {n} pages")


def write_zip(path: Path, members: list[Path], figs: set[str]) -> None:
    if path.exists():
        path.unlink()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in members:
            z.write(p, p.name)
        for f in sorted(figs):
            z.write(HERE / "figures" / f, f"figures/{f}")
    n = len(members) + len(figs)
    print(f"[zip]    {path.name}: {n} files, {path.stat().st_size/1e6:.1f} MB")


def main() -> None:
    sys.path.insert(0, str(HERE))
    import build_ieee
    build_ieee.check_biographies()

    main_figs = figures_used_by(MAIN_TEX)
    supp_figs = figures_used_by(SUPP_TEX)
    on_disk = {p.name for p in (HERE / "figures").glob("*")}
    stray = on_disk - main_figs - supp_figs
    if stray:
        print(f"[figs]   {len(stray)} figure(s) used by neither document: "
              f"{sorted(stray)[:3]}")
    print(f"[figs]   main {len(main_figs)}, supplement {len(supp_figs)}, "
          f"shared {len(main_figs & supp_figs)}")

    verify_main(main_figs)

    members = []
    for name in [MAIN_TEX, MAIN_PDF] + SUPPORT:
        p = HERE / name
        if not p.exists():
            sys.exit(f"!! missing from the main manuscript set: {name}")
        members.append(p)
    for pat in FONT_GLOBS:
        members.extend(sorted(HERE.glob(pat)))
    write_zip(MAIN_ZIP, members, main_figs)

    write_zip(SUPP_ZIP, [HERE / SUPP_TEX, HERE / SUPP_PDF], supp_figs)

    # The old combined archive violates the portal's rule; remove it so it
    # cannot be uploaded by mistake.
    old = DOCS / "ieee_access_submission.zip"
    if old.exists():
        old.unlink()
        print(f"[clean]  removed {old.name} (carried the supplement inside the "
              f"main manuscript)")

    print(f"\nUpload: {MAIN_ZIP.name} as the Main Manuscript")
    print(f"        {SUPP_PDF} (or {SUPP_ZIP.name}) as Supplementary Material")
    print( "        cover_letter_ieee_access.pdf separately")


if __name__ == "__main__":
    main()
