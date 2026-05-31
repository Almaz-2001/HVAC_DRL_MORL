# Figures

This directory holds the PDF figures referenced from the LaTeX skeleton.
All non-schematic figures are **auto-generated** from CSVs in `reports/`
via `paper/build_paper_figures.py` — there is no hand-edited PDF here.

## Current figures

| File | Section | Generator | Source CSVs |
|------|---------|-----------|-------------|
| `fig_block1_surrogates.pdf` | §5 Results I | `build_paper_figures.py::build_fig_block1` | `reports/hou_evins_predictive_validity_table.csv` |
| `fig_block2_pareto_vs_pi.pdf` | §6 Results II | `build_paper_figures.py::build_fig_block2` | `reports/morl_pareto_front_table.csv`, `reports/pi_baseline_yearly_table.csv` |
| `pipeline_overview.pdf` *(pending)* | §3 Methodology | manual schematic, not auto-generated | — |

## Regeneration workflow

After any new experiment whose CSV changes:

```powershell
.\.venv\Scripts\python.exe paper\build_paper_figures.py
```

This rewrites the PDFs in place. Compile order:

```powershell
cd paper
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

Figures are picked up automatically; nothing in `main.tex` needs editing.

## Figure design conventions

- **Format:** PDF (vector). Never raster except for screenshots.
- **Color palette:** consistent across both figures (see `COLORS` dict in
  `build_paper_figures.py`). Calibrated v3.5 is always red, hybrid_l010 is
  always green, PI baseline is gray, the pre-registered canonical is blue,
  the practical-deployment canonical is orange.
- **Fonts:** matplotlib default `DejaVu Sans` for figures; `\caption` uses
  the document font (Times via `elsarticle`).
- **Width:** `0.95\linewidth` for full-width figures.

## Pending schematic figure

`pipeline_overview.pdf` (§3 Methodology) is the surrogate-controller
information-flow schematic. It is **not** auto-generated because it is a
diagram, not a plot. To create it:

1. Recommended tool: TikZ inside the document, or draw.io / Inkscape
   exported to PDF.
2. The key visual point: `v3.5` enters only the training loss
   (Eq.~\ref{eq:hybrid_loss}), never the policy's forward pass.
3. Suggested layout:
   ```
   data ─► v3 (FFN, two heads) ─► policy.forward(s) ─► action
                                       │
                                       └─► loss ◄─── λ·‖T_v3 − T_v3.5‖²
                                                              ▲
                                       (frozen) ──► v3.5 ─────┘
   ```

When ready, drop the PDF as `figures/pipeline_overview.pdf` and the
LaTeX in §3.5 will pick it up automatically (the `\includegraphics` line
is already in `paper/sections/03_methodology.tex`, currently commented
out next to the placeholder).

## What each figure shows

### `fig_block1_surrogates.pdf` — Block 1 visual

**Panel (a):** Multi-horizon predictive validity. Line plot of
temperature RMSE over rollout horizons {1, 4, 8, 24} hours, comparing
the uncalibrated `raw_v35` baseline with the calibrated `v35` after the
Stage A/B/C pipeline. The take-away is the ~56% RMSE reduction at every
horizon plus the flatness of the calibrated curve (no error
accumulation).

**Panel (b):** Fidelity-to-RL gap. Grouped bars for v3, v3.5 calibrated,
and hybrid\_l010, comparing held-out 24-hour predictive RMSE (red) with
mean live-BOPTEST transfer RMSE (blue). The visual headline: v3.5 has
the best predictive RMSE but the worst transfer RMSE — a ~6× gap. This
motivates the hybrid construction.

### `fig_block2_pareto_vs_pi.pdf` — Block 2 visual

A single scatter plot in (yearly violation %, yearly energy kWh) space:

- **5 MORL Pareto points**, colored by canonical designation.
- **Pre-registered canonical** `w=(0.50, 0.50)` and **practical
  canonical** `w=(0.75, 0.25)` rendered as starred markers.
- **BOPTEST PI baseline** as a separate cross marker.
- **Vertical dashed red line at 5% violation** — the pre-registered
  deployment threshold.
- **Gray dashed curve** through admissible Pareto points (excluding
  the energy-collapse endpoint).
- **Log scale on x-axis** because violation spans 1.49% → 86.76%.

Once seeds 43 and 44 complete, the two starred canonicals will gain
error bars; everything else stays single-seed.
