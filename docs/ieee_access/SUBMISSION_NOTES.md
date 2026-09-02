# IEEE Access submission — status

Build: `python docs/ieee_access/build_ieee.py`
Produces `ieee_access_hvac.pdf` (14 pp) and `supplementary.pdf` (28 pp).

## Why this journal

| Journal | Outcome | Stated reason |
| --- | --- | --- |
| Results in Engineering | desk reject | generic |
| Ain Shams Eng. J. | desk reject | "lack of sufficient novelty" |
| Energies (MDPI) | returned at technical pre-check | **scope**, explicitly *not* quality |

The Energies outcome is the informative one: the contribution is methodological
(which surrogate to train an RL controller on), demonstrated on a building.
IEEE Access states that it welcomes multidisciplinary work, applications-oriented
articles and negative results that do not fit the traditional journals.

## The structural risk

IEEE Access allows **exactly one** revision, and the decision is accept or reject.
There is no second round to absorb a request for more experiments. That is why the
following were run before submission rather than promised in a response letter:

- the censor-weight sweep, seed-replicated over {42,43,44} at all four settings;
- the directional-validity audit of every surrogate on both actuated inputs;
- the pre-registered MPC baseline, which answers the "your baseline is weak"
  objection (`reports/block2_mpc_baseline_report.md`).

## Ready

- Official `ieeeaccess.cls` from the supplied template, with its fonts, spot
  colour and logos. **0 LaTeX errors.**
- Overfull boxes: 31 total, of which 29 are the class's own page-output artifact
  and 2 come from `\maketitle`. IEEE's own sample document emits the identical
  505.12 pt warning 17 times plus 4 genuine ones; we contribute **none**.
- Abstract 247 words, one paragraph, no citations (limit 250).
- Index Terms: six, alphabetical.
- Funding in the first-page footnote in IEEE's form; `\corresp` set.
- `IEEEtran.bst` numbered references, no undefined citations.
- 14 pages, inside the 8–20 norm.
- Supplementary builds as a separate 28-page PDF.

## Two class gotchas, recorded so they are not rediscovered

1. **siunitx `detect-all` is incompatible with this class.** It probes the current
   font; the Formata/Giovanni setup breaks the probe and every `\SI` expands to
   `\???` — 15 errors, all of them mystifying until traced. The option is off.
2. The frontmatter uses the class's own commands, not IEEEtran's: `\history`,
   `\doi`, `\authorrefmark` with `\address`, `\tfootnote`, `\corresp`,
   `\titlepgskip`, `\PARstart` (not `\IEEEPARstart`), and `\EOD` before
   `\end{document}`.

## Closed since

- **Biographies removed entirely.** Author biographies and photographs are
  optional for IEEE Access. `bios.tex` held five skeletons whose `[bracketed]`
  placeholders printed verbatim — 30 of them reached a compiled PDF before this
  was caught. The file is out of the tree (`_archive/old_bundles/`); the cover
  letter says biographies can be supplied if the article proceeds.
- **Supplementary synced line by line** against the sign-audit and MPC revisions
  to the main text.
- **AI-use disclosure** added, in the wording the corresponding author supplied.
- **"Training Utility" retitled "Control Utility"** throughout.
- **Cover letter date** is generated from `\today` at build time, so it cannot
  go stale between rebuilds. It did once.

## Open

- **Language.** The text has not been read by a native speaker. IEEE Access
  requires standard English; grammar is sound but this is not the same assurance.
- **ORCID** for the corresponding author, required by the submission system:
  0009-0003-1521-7149.
- **Data-availability statement.** Not currently present. Confirm against the
  official IEEE Access checklist whether one is mandatory; if so, the agreed
  wording is that the codebase is not publicly released at this stage and is
  available to editors and reviewers on request.
- **CrossCheck.** The WCCM–ECCOMAS talk is an acceptable prior presentation; if
  its abstract appears in published proceedings, say so in the cover letter.

## What gets uploaded

`../ieee_access_submission.zip` (91 files, 11.6 MB) is the archive as submitted:
`ieee_access_hvac_onefile.tex` as the main document, `supplementary.tex`, the
class and font files, `references.bib`, `IEEEtran.bst`, and `figures/`. It is
tracked deliberately — no script rebuilds it, so it is the only record of
exactly what the journal received. The cover letter is uploaded separately.

Form fields for the file-upload step (label ≤ 30 chars, description ≤ 1000):
label `LaTeX source and figures`, description naming the build order
(pdflatex, bibtex, pdflatex, pdflatex) and the expected 14 / 28 page counts, so
the editorial office can tell a compilation mismatch from a source problem.

## Source of truth

Related work, Materials and methods, and Results and discussion are sliced
verbatim from `../paper_asej/manuscript.tex` by `build_ieee.py`. Edit the science
there, not in `body_*.tex` — those are regenerated on every build and local edits
are lost. Title, abstract, introduction, conclusion, author block and biographies
are owned by this directory.
