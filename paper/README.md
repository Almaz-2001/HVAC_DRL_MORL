# Q1 paper skeleton — Results in Engineering submission

Target journal: **Results in Engineering** (Elsevier, Q1, open access).
Document class: `elsarticle` with `3p,review,authoryear,12pt` (single column
+ line numbers, the format Elsevier expects for first submission).

## Layout

```
paper/
├── main.tex                       # entry point; \input's every section
├── bibliography.bib               # references (expand during writing)
├── sections/
│   ├── 01_introduction.tex        # contributions block + outline
│   ├── 02_related_work.tex        # three streams + position-of-this-work
│   ├── 03_methodology.tex         # v3 / v3.5 / hybrid / controllers
│   ├── 04_experimental_setup.tex  # testbed, datasets, evaluation protocol
│   ├── 05_results_fidelity.tex    # Results I
│   ├── 06_results_control.tex     # Results II
│   ├── 07_results_transfer.tex    # Results III (optional; Block 3)
│   ├── 08_discussion.tex          # threats to validity included
│   └── 09_conclusion.tex          # claim boundary
├── tables/                        # auto-generated *.tex tables
│   ├── table1_architecture_comparison.tex
│   ├── table2_predictive_validity.tex
│   └── table3_controller_performance.tex
├── figures/                       # auto-supplied .pdf/.png
│   └── README.md                  # what to put where
├── build_paper_tables.py          # regenerates tables from CSVs
└── README.md                      # this file
```

## How numbers stay reproducible

Every number in Tables 1–3 is **regenerated** from the canonical CSVs in
`reports/` and the experiment summaries in `outputs/`. There is no
hand-edited value in the LaTeX tables — that is intentional.

### Update workflow

1. Re-run any underlying experiment whose output CSV changes.
2. Re-run the consolidation scripts so the canonical CSVs in `reports/`
   reflect the latest numbers:
   ```powershell
   .\.venv\Scripts\python.exe evaluation\build_hou_evins_appendix_tables.py
   .\.venv\Scripts\python.exe evaluation\build_hou_evins_open_items_closure.py
   .\.venv\Scripts\python.exe evaluation\build_hou_evins_compliance_closure.py
   ```
3. Re-run the paper-table builder AND the figure builder:
   ```powershell
   .\.venv\Scripts\python.exe paper\build_paper_tables.py
   .\.venv\Scripts\python.exe paper\build_paper_figures.py
   ```
   These rewrite `paper/tables/*.tex` and `paper/figures/*.pdf` in
   place. The LaTeX skeleton automatically picks up the new values
   and figures on the next `pdflatex` pass.
4. Compile:
   ```powershell
   cd paper
   pdflatex main
   bibtex main
   pdflatex main
   pdflatex main
   ```

The builder is safe to re-run any time. Missing CSV inputs become explicit
red TODO placeholders rather than silent zeros.

## What is finished, what is a placeholder

| Section | Status |
|---------|--------|
| §1 Introduction | structural placeholders + contributions block written |
| §2 Related Work | three-stream structure stubbed |
| §3 Methodology | hybrid loss equation written; v3/v3.5/Stage A-B-C stubbed |
| §4 Experimental Setup | evaluation protocol fully written; reproducibility stub |
| §5 Results I (Fidelity) | architecture/predictive numbers will populate automatically once Table 1–2 inputs are present; prose is stubbed |
| §6 Results II (Control) | PI/thermostatic/HDRL/MORL substructure; cross-controller table written; values are TODO until 3-seed validation |
| §7 Results III (Transfer) | activate only if Block 3 finishes |
| §8 Discussion | threats-to-validity already enumerated |
| §9 Conclusion | claim boundary written |
| Tables 1–3 | auto-generated; rerun `build_paper_tables.py` after new experiments |
| Figures 1–2 | red boxes; replace with real PDFs in `figures/` |

## Publication amplifiers still to add

These three numerically materialize during writing; they do not change the
structure:

1. **Speed benchmark** (`evaluation/build_speed_benchmark.py` to be added) —
   one-shot env-steps/sec comparison; goes into §4.6 and the Abstract.
2. **MORL Pareto front** (5 preference weights, yearly BOPTEST validation
   each) — populates Figure 2 in §6.5.
3. **3-seed canonical validation** for thermostatic hybrid\_l010, MORL 17-D,
   pure v3 — converts single-seed values in Table 3 to mean ± std.

When each amplifier completes, the corresponding TODO marker in the LaTeX
disappears and the table picks up the new value.

## What the paper does NOT claim

The skeleton was written with explicit claim boundaries:

- not a generic PINN paper (v3.5 is in the loss, not in the forward pass);
- not a multi-building generalization claim (only `bestest_air` unless §7
  is activated);
- not a full multi-objective optimization (single preference point unless
  the Pareto sweep is included);
- not a formal HPO study (the λ sweep is targeted sensitivity, framed as
  such following the protocol of Hou and Evins, 2024).

These boundaries are restated in §1 contributions, §6 results and §8
discussion. Do not weaken them while writing prose.
