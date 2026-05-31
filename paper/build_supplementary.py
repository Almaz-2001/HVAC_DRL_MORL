"""
Compile the eleven Hou-and-Evins compliance CSV tables into a single
LaTeX supplementary document.

  Input:  paper/supplementary/hou_evins_*.csv  (11 files)
  Output: paper/supplementary/supplementary.tex  (compilable on its own)

Run:  python paper/build_supplementary.py
Then: pdflatex paper/supplementary/supplementary.tex (twice)
"""

from __future__ import annotations

import csv
from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parent
SUPP_DIR = PAPER_DIR / "supplementary"

# Order S1..S11 — matches Hou-and-Evins Section 5 Reporting Levels 1-3
TABLES = [
    ("S1", "hou_evins_sample_generation_table.csv",
     "Sample-generation provenance.",
     "Origin, parameter ranges, and physical justification of each transition corpus."),
    ("S2", "hou_evins_sample_size_justification_table.csv",
     "Sample-size justification.",
     "Numerical evidence for the chosen corpus sizes including learning-curve checks."),
    ("S3", "hou_evins_stage_a_processing_table.csv",
     "Stage A telemetry preprocessing.",
     "Latency compensation, bias removal, normalisation, denoise, and causal delta."),
    ("S4", "hou_evins_feature_justification_table.csv",
     "Feature significance.",
     "Per-feature retention rationale with quantitative selection criteria."),
    ("S5", "hou_evins_input_independence_table.csv",
     "Input independence.",
     "Pearson and mutual-information independence checks across input channels."),
    ("S6", "hou_evins_split_representativeness_table.csv",
     "Train/validation/test split representativeness.",
     "Distributional checks between corpus partitions."),
    ("S7", "hou_evins_scaling_table.csv",
     "Per-channel scaling and reverse-scaling logic.",
     "Standardisation parameters reused at inference time."),
    ("S8", "hou_evins_training_hyperparams_table.csv",
     "Training hyperparameters.",
     "Optimiser, learning rate, batch size, regularisation, and stopping criteria."),
    ("S9", "hou_evins_architecture_justification_table.csv",
     "Architecture justification.",
     "Layer widths, depths, activations, and ablation evidence."),
    ("S10", "hou_evins_targeted_sensitivity_table.csv",
     "Targeted sensitivity analysis.",
     "Per-hyperparameter sweep results, lambda-temp scan included."),
    ("S11", "hou_evins_predictive_validity_table.csv",
     "Replicative and predictive validity.",
     "One-step and multi-horizon rollout RMSE across all variants."),
]


HEADER = r"""\documentclass[11pt,a4paper]{article}

\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[margin=2.0cm]{geometry}
\usepackage{microtype}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{ragged2e}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{siunitx}

\hypersetup{colorlinks=true, linkcolor=blue!60!black, citecolor=blue!60!black,
            urlcolor=blue!50!black}

% Make long table cells wrap on word boundaries.
\renewcommand{\arraystretch}{1.1}
\newcolumntype{L}[1]{>{\RaggedRight\arraybackslash}p{#1}}

\title{Supplementary Material \\[0.3em]
       \large When Predictive Surrogates Fail as RL Environments:
       A Calibrated Physical Twin as Soft Regularizer for HVAC Control}
\author{Almaz Sapargali}
\date{\today}

\begin{document}
\maketitle

\section*{Overview}

This document contains the eleven supplementary tables (S1--S11)
referenced in the main manuscript. They cover the Hou-and-Evins
\emph{Reporting Level 3} requirements for surrogate-development
disclosure: sample generation and sizing, preprocessing, feature
significance, input independence, split representativeness, scaling,
training hyperparameters, architecture justification, targeted
sensitivity, and replicative/predictive validity.

Each table is reproduced verbatim from the corresponding CSV in
\texttt{paper/supplementary/}. All numerical values are taken without
modification from the Block~1, Block~2, and Block~3 evaluation
pipelines. Compliance status against the seventeen Reporting-Level-3
items is summarised after the tables.

\tableofcontents

"""

FOOTER = r"""
\section*{Compliance summary}

Of the seventeen Hou-and-Evins Reporting-Level-3 items, fifteen are
covered with quantitative evidence by tables S1--S11. The two
uncovered items are
(i)~physical co-simulation between two independent Modelica engines
(only one engine is used here through the BOPTEST FMU) and
(ii)~grid-tied multi-agent coordination
(out of scope for the single-zone testbed used in the main study).

\section*{Audit-anchor cross-references}

\begin{itemize}
  \item MORL canonical selection pre-registration:
        commit \texttt{93df9b3}.
  \item MORL post-$N{=}5$ canonical falsification:
        commit \texttt{62dc859}.
  \item Block~3 transferability pre-registration:
        manifest field \texttt{audit.pre\_registration\_commit\_sha} in
        \texttt{configs/block3\_testcase\_manifest.yaml}.
  \item Block~3 closure:
        manifest field \texttt{audit.block3\_close\_commit\_sha}.
\end{itemize}

\end{document}
"""


def _escape(value: str) -> str:
    """Minimal LaTeX escape suitable for short CSV cell text.

    Also replaces common Unicode characters that pdflatex (T1 + lmodern)
    cannot render directly. Math-like symbols are wrapped in inline
    math mode so they survive longtable cells.
    """
    if value is None:
        return ""
    out = str(value)
    # Unicode -> LaTeX (do BEFORE escaping LaTeX specials, otherwise the
    # math wrappers introduce $ that would be re-escaped).
    unicode_map = {
        "≈": r"$\approx$",      # ≈
        "≤": r"$\leq$",          # ≤
        "≥": r"$\geq$",          # ≥
        "×": r"$\times$",        # ×
        "±": r"$\pm$",           # ±
        "→": r"$\rightarrow$",   # →
        "←": r"$\leftarrow$",    # ←
        "↔": r"$\leftrightarrow$",  # ↔
        "…": r"\ldots{}",        # …
        "–": "--",               # – en dash
        "—": "---",              # — em dash
        "‘": "`",                # ‘
        "’": "'",                # ’
        "“": "``",               # “
        "”": "''",               # ”
        "°": r"$^{\circ}$",      # °
        "µ": r"$\mu$",           # µ
        "μ": r"$\mu$",           # μ
        "λ": r"$\lambda$",       # λ
        "α": r"$\alpha$",        # α
        "β": r"$\beta$",         # β
        "γ": r"$\gamma$",        # γ
        "δ": r"$\delta$",        # δ
        "θ": r"$\theta$",        # θ
        "σ": r"$\sigma$",        # σ
        "Σ": r"$\Sigma$",        # Σ
        "²": r"$^{2}$",          # ²
        "³": r"$^{3}$",          # ³
    }
    for k, v in unicode_map.items():
        out = out.replace(k, v)

    # Strip any remaining non-ASCII to avoid pdflatex U+ errors.
    out = "".join(ch if ord(ch) < 128 else "?" for ch in out)

    # Replace LaTeX specials. Backslash first.
    repl = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        # Do NOT escape $ here; we may have introduced math mode above.
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]
    # Escape backslash first, then process $ carefully (preserve our math).
    out = out.replace("\\", r"\textbackslash{}")
    # Build a list of segments split by $...$ so we don't escape inside math.
    parts = out.split("$")
    cleaned = []
    for idx, seg in enumerate(parts):
        if idx % 2 == 1:
            # inside math: keep as-is
            cleaned.append(seg)
        else:
            # outside math: escape LaTeX specials except backslash (already done).
            for k, v in repl[1:]:
                seg = seg.replace(k, v)
            cleaned.append(seg)
    # Re-join with literal $
    return "$".join(cleaned)


def _column_widths(n_cols: int) -> str:
    """Pick column widths for booktabs longtable.

    A4 with 2 cm margins gives ~17 cm usable width. Divide.
    """
    total_cm = 16.5
    each = total_cm / n_cols
    cols = " ".join([f"L{{{each:.2f}cm}}" for _ in range(n_cols)])
    return cols


def render_csv_table(path: Path, label: str, caption: str) -> str:
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        rows = list(reader)
    if not rows:
        return f"% empty: {path.name}"
    header = rows[0]
    body = rows[1:]
    n_cols = len(header)
    col_spec = _column_widths(n_cols)
    out = []
    out.append(r"\begin{small}")
    out.append(r"\begin{longtable}{" + col_spec + r"}")
    out.append(r"\caption{" + _escape(caption) + r"\label{tab:" + label + r"}}\\")
    out.append(r"\toprule")
    out.append(" & ".join(r"\textbf{" + _escape(h) + r"}" for h in header) + r" \\")
    out.append(r"\midrule")
    out.append(r"\endfirsthead")
    out.append(r"\multicolumn{" + str(n_cols) + r"}{l}{\itshape (continued from previous page)}\\")
    out.append(r"\toprule")
    out.append(" & ".join(r"\textbf{" + _escape(h) + r"}" for h in header) + r" \\")
    out.append(r"\midrule")
    out.append(r"\endhead")
    out.append(r"\midrule")
    out.append(r"\multicolumn{" + str(n_cols) + r"}{r}{\itshape (continued on next page)}\\")
    out.append(r"\endfoot")
    out.append(r"\bottomrule")
    out.append(r"\endlastfoot")
    for row in body:
        # pad to n_cols
        cells = row + [""] * (n_cols - len(row))
        cells = cells[:n_cols]
        out.append(" & ".join(_escape(c) for c in cells) + r" \\")
    out.append(r"\end{longtable}")
    out.append(r"\end{small}")
    return "\n".join(out)


def main() -> None:
    sections = []
    for label, csv_name, short, descr in TABLES:
        csv_path = SUPP_DIR / csv_name
        if not csv_path.exists():
            print(f"[warn] missing {csv_path.name}")
            continue
        sections.append(r"\section*{Table " + label + r":  " + short + r"}")
        sections.append(_escape(descr))
        sections.append("")
        sections.append(render_csv_table(csv_path, label, f"Table {label}.  {short}"))
        sections.append("")
        print(f"[OK]  rendered {label}  ({csv_name})")

    out = HEADER + "\n".join(sections) + FOOTER
    target = SUPP_DIR / "supplementary.tex"
    target.write_text(out, encoding="utf-8")
    print(f"[done] wrote {target}")


if __name__ == "__main__":
    main()
