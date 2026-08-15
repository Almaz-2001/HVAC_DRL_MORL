# ASEJ submission set — status and remaining actions

Journal: *Ain Shams Engineering Journal* (Elsevier, gold open access, APC USD 1 800 excl. tax).
Review model: **double anonymized**.

Rebuild everything with:

```bash
python docs/paper_asej/build_asej.py
```

The script fails loudly if the manuscript exceeds 12 pages or if any identifying string leaks into
`manuscript.tex` or `supplementary.tex`.

## The format decision — read this before changing anything

The guide says the manuscript file is limited to **10 pages, font 12, single spaced**. Taken
literally that is impossible, and the journal's own output proves it. A recent accepted Full Length
Article (`docs/example_article_ASEJ.pdf`, received 29 March 2026, accepted 14 June 2026) runs
**10 409 words with 9 figures and 7 tables**. Reformatted to 12 pt single-column single-spaced, that
article would be about 26 pages — nearly three times the stated limit.

The only reading that makes the two consistent is that the page count refers to the journal's own
two-column layout, where a full-length article of that size lands at 10–12 pages. So we submit in
**`elsarticle` `5p`**, Elsevier's two-column house style, and hold the page count instead of the
font instruction.

Where that leaves us against the journal's own norm:

| | Example ASEJ article | This manuscript |
|---|---|---|
| Words (incl. references) | 10 409 | 9 675 |
| Figures | 9 | 9 |
| Tables | 7 | 5 |
| References | 32 | 55 |
| Pages | 11 (published typesetting) | 12 (elsarticle 5p) |

An earlier 10-page single-column version exists as `manuscript_10p_singlecol.tex.bak`. It complies
with the guide to the letter but carries only 3 figures and ~3 000 words, which would read as a
short communication in this journal. Keep it only as a fallback if the editorial office explicitly
demands the 12 pt single-column format.

## The Supplement

The journal does not require supplementary material and has no research-data or code-availability
policy at all — the guide never mentions repositories, data statements or GitHub. We attach one
anyway, and it is outside the page budget.

It is **not** the long-format supplement from `docs/paper_combined/`; it is built here and was
re-slimmed once the manuscript went back to full length, so that no figure appears in both files:

| Section | Content |
|---|---|
| §1 | Map from each main-article section to the supplementary items supporting it |
| §2 | Pre-specified hypotheses H1–H4 with verdicts, and the CL1–CL5 ledger linkage |
| §3 | Full limitations statement (the manuscript carries an abridged one) |
| §4 | Supporting figures and tables: corpora, architectures, Stage A/B/C, seed bands, λ sweeps, MORL/HDRL detail, transfer adapters and regimes |
| §5–§7 | BOPTEST RTE control loop, implementation formulas, additional tables |

Note the journal publishes supplementary items *exactly as received* — nobody copy-edits or
typesets them, so what builds here is what appears online.

## Mapping to the portal's "Attach Files" slots

The submission form lists item types the guide never mentions, in particular **Author biography**
and **Author photo**:

| Portal slot | File to upload |
|---|---|
| Title page with author details | `title_page.pdf` |
| Manuscript without author details | `manuscript.pdf` |
| Author biography | `author_biographies.md` → export once filled in; collect the facts with `author_bio_form.md` |
| Author photo | six photographs, one per author — **not yet collected** |
| Declaration of competing interests | `declaration_of_competing_interests.pdf` |

Two slots the form did not show but the guide does describe — **Supplementary material** and
**Highlights** — are usually further down the item-type dropdown. Check the full list before
submitting; if there is genuinely no supplementary slot, ask the editorial office rather than
folding the Supplement into the manuscript.

## Files ready

| File | Purpose | Status |
|---|---|---|
| `manuscript.pdf` / `.tex` | anonymized manuscript | ✔ 12 pages, 9 figures, 5 tables, 55 refs |
| `title_page.pdf` / `.tex` | authors, affiliations, CRediT, funding, interest statement | ✔ 1 page |
| `supplementary.pdf` / `.tex` | reproduction detail | ✔ 28 pages, anonymized |
| `figure_files/Fig1–Fig9.pdf` | separate figure files, numbered in citation order | ✔ |
| `figure_captions.txt` | figure and table captions supplied separately | ✔ |
| `highlights.txt` | 5 bullets, each ≤ 85 characters | ✔ |
| `declaration_of_competing_interests.pdf` / `.tex` | standalone portal file, official Elsevier wording | ✔ 1 page |
| `author_biographies.md`, `author_bio_form.md` | biography skeletons and the questionnaire | ⚠ placeholders only |
| `cover_letter_ASEJ.pdf` / `.tex` / `.md` | cover letter, incl. a paragraph justifying the two-column format | ✔ 2 pages |
| `references_asej.bib` | 55 refs, ISO4-abbreviated, doi/url stripped — **generated**, do not hand-edit | ✔ |

## What still needs a human

1. **Author biographies** — every `<<placeholder>>` in `author_biographies.md` is a fact only the
   author knows. A wrong degree in a published biography needs a corrigendum.
2. **Author photos** — six files, 300 dpi minimum. The submission cannot be completed without them.
3. **Title page postal addresses** — three `<<...>>` placeholders in `title_page.tex`. Also verify
   the two addresses that were filled in from public sources (Al-Farabi KazNU, ISEL).
4. **Suggested reviewers** — the letter no longer proposes any. The guide asks for them but the
   editor decides whom to invite, so this is a request rather than a requirement. If Editorial
   Manager makes the field mandatory at submission time, names will have to be entered there.
5. **Declaration of Interest form** in the submission system, matching the title page word for word.
6. **Subject area at submission** — Mechanical, or Electrical/Control Engineering, so the paper
   reaches an editor who reads control and building-energy work.
7. **APC** — confirm budget or waiver eligibility *before* submitting.

## Known deviations

- **12 pt single spacing.** Not used; see the format decision above. If the editorial office pushes
  back, `manuscript_10p_singlecol.tex.bak` is the compliant fallback.
- **12 pages, not 10.** Two over the stated number even in two-column, and still one page shorter
  than the example article's published length.
- **Figure fonts.** The journal *aims* for Arial / Times New Roman / Courier / Symbol in artwork;
  the TikZ/pgfplots figures use Computer Modern. This is a preference, not a rule, and all fonts are
  embedded in vector PDFs. If production objects, regenerate the nine figures with `mathptmx` or
  `helvet` in the standalone preamble.
- **`--disable-installer` in the build.** Not cosmetic: elsarticle probes for `txfonts.sty`, which
  is missing here, and MiKTeX's interactive installer hangs the build with no error message.

## Spelling

American English throughout (`modeling`, `analyze`, `artifact`, `normalization`, `behavior`). The
journal accepts either variant but forbids mixing, and requires American spelling in the keywords.
