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

## Returned to draft, 02 Sep 2026 — Access-2026-42535

One issue: *"we require a biography from each author on the manuscript."*

**Biographies are not optional for IEEE Access.** The presence of
`\IEEEbiographynophoto` in the class means a biography may omit the
*photograph*, not that the biography itself can be omitted. That misreading is
what cost this submission a cycle: the file was deleted in August because its
five skeletons printed `[bracketed]` placeholders into the PDF, and deletion was
the wrong fix for that problem.

`bios.tex` is back, with real text for five of six authors, sourced from what
each author wrote about themselves — Mukhanbet, Daribayev and Trigo verbatim
from their own IEEE Access biographies in `docs/biography info/`, Shinassylov
converted from the first-person CV in the same file, Sapargali as supplied.

`build_ieee.py` now refuses to build unless every name in `\author{}` has a
biography and no `[bracketed]` placeholder survives. Both halves of that check
correspond to a real failure. `--draft-bios` builds a preview anyway and says
loudly that the result is not submittable.

- **Photographs.** Not requested by the editorial office, so every entry uses
  `\IEEEbiographynophoto`. Portraits do exist in the supplied file but Word
  downscaled them to 102–216 dpi against IEEE's 300 dpi minimum; originals would
  be needed.
- **Supplementary synced line by line** against the sign-audit and MPC revisions
  to the main text.
- **AI-use disclosure** added, in the wording the corresponding author supplied.
- **"Training Utility" retitled "Control Utility"** throughout.
- **Cover letter date** is generated from `\today` at build time, so it cannot
  go stale between rebuilds. It did once.

## Open

- **BLOCKER: biography for Serik Aibagarov.** The only thing between the
  manuscript and resubmission. Request form: `bio_request_aibagarov.md`. Do not
  write it from inference — a wrong degree or institution in a published
  biography is corrected only by corrigendum.
- **Name spelling, Shona Shinassylov.** The paper, `CITATION.cff` and the author
  block all use *Shinassylov*; the CV he supplied is headed *Shonazilov Shona
  Zhoaraevich*. The biography follows the paper. He should confirm which
  transliteration he wants published.
- **University name in the same biography.** His CV names "Kazakh National
  Technical University named after K.I. Satybaldin". The institution in Almaty
  is named after K.I. Satpayev, so this looks like a slip. The biography says
  "Kazakh National Technical University, Almaty" with no eponym rather than
  print a name that may be wrong; he should supply the correct full form.
- **Language.** The return letter asks for a grammar review. A mechanical pass
  was run over the flattened source: doubled words, a/an agreement, spacing
  before punctuation — no real defects (the apparent ones were `\uppercase`
  markup and "a usable"/"an RL", both correct). 12 British spellings that were
  *mixed* with their American forms were normalized (optimise→optimize,
  behaviour→behavior, penalise→penalize, favourable→favorable,
  programme→program). `grey-box` is left as is: it is a term of art, used
  consistently, and the GB abbreviation derives from it. This is not a
  native-speaker read, and that assurance is still missing.
- **ORCID** for the corresponding author, required by the submission system:
  0009-0003-1521-7149.
- **Data-availability statement.** Not currently present. Confirm against the
  official IEEE Access checklist whether one is mandatory; if so, the agreed
  wording is that the codebase is not publicly released at this stage and is
  available to editors and reviewers on request.
- **CrossCheck.** The WCCM–ECCOMAS talk is an acceptable prior presentation; if
  its abstract appears in published proceedings, say so in the cover letter.

## What gets uploaded

Build both archives with `python docs/ieee_access/make_submission_zip.py`.

| File | Portal slot |
| --- | --- |
| `../ieee_access_main_manuscript.zip` (58 files, 4.1 MB) | Main Manuscript |
| `supplementary.pdf`, or `../ieee_access_supplementary.zip` (32 files, 6.2 MB) | Supplementary Material |
| `cover_letter_ieee_access.pdf` | Cover Letter |

**Two archives, not one.** The portal states that the Main Manuscript "should
not include any supplementary materials". The build copies the union of both
documents' figures into one `figures/` folder, and 30 of the 39 are the
supplement's alone — so the earlier single archive was shipping supplementary
material inside the main manuscript, and was 10.3 MB instead of 4.1 MB.

The split is verified, not assumed: the packaging script compiles the main
bundle in an isolated copy of only its own packed files, so a figure filed under
the wrong archive fails as a missing-file error instead of passing quietly. That
compile's PDF is the one packed, which is how the `.tex` and `.pdf` are kept
identical in content as checklist item 1 requires.

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
