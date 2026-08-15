"""Additional lay-audience charts for the expanded funder report.

Same rules as make_report_figures.py: one idea per chart, plain-word labels, the
conclusion written on the chart itself. Numbers trace to reports/*.csv and are the
same ones used in progress_report_tasks_10_11.tex.

Run with the project venv:
    .venv/Scripts/python.exe docs/current_tasks/make_report_figures2.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from pathlib import Path

OUT = Path(__file__).resolve().parent / "report_figures"
OUT.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
})

GOOD, BAD, NEUTRAL, ACCENT = "#2e7d5b", "#b4442e", "#7a8b93", "#2f6f8f"
WARN = "#c98a1f"
INK = "#33414a"


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", name + ".png")


# ---------------------------------------------------------------- Figure 5 ----
def fig_two_twins():
    """The two competing twin designs, and what each is good at."""
    fig, ax = plt.subplots(figsize=(11, 5.3))
    ax.set_xlim(0, 11); ax.set_ylim(0, 5.3); ax.axis("off")

    panels = [
        (0.15, "Design A: the “observed behaviour” twin",
         ["Learns the building purely from",
          "recorded measurements.",
          "Knows no physics.",
          "8 482 adjustable numbers inside."],
         ["+  very fast to run", "+  needs no engineering drawings",
          "–  cannot be inspected or explained", "–  less accurate here"], ACCENT),
        (5.75, "Design B: the “physics” twin",
         ["A simplified physical model of heat",
          "flow, with a small learned correction.",
          "Its main parameter is a real physical",
          "quantity we can check against reality."],
         ["+  can be inspected and explained", "+  more accurate here",
          "–  slower to run", "–  needs tuning per building"], GOOD),
    ]

    for x, title, body, bullets, colour in panels:
        ax.add_patch(FancyBboxPatch((x, 1.05), 5.10, 3.95, boxstyle="round,pad=0.08",
                                    linewidth=1.6, edgecolor=colour, facecolor=colour + "10"))
        ax.text(x + 2.55, 4.65, title, ha="center", va="center",
                fontsize=11.5, fontweight="bold", color=colour)
        for i, line in enumerate(body):
            ax.text(x + 0.28, 4.17 - i * 0.30, line, ha="left", va="center",
                    fontsize=9.6, color=INK)
        for i, b in enumerate(bullets):
            ax.text(x + 0.28, 2.65 - i * 0.34, b, ha="left", va="center", fontsize=9.6,
                    color=GOOD if b.startswith("+") else "#8a5a4e")

    ax.text(5.50, 0.10,
            "Both twins were built for the same building and judged the same way: how far the "
            "temperature they predict\ndrifts from the real one over a full day of operation. "
            "The project kept both, and the reason why is the main finding of the year.",
            ha="center", va="bottom", fontsize=9.4, color=INK, style="italic")
    save(fig, "fig5_two_twins")


# ---------------------------------------------------------------- Figure 6 ----
def fig_where_accuracy():
    """Where the accuracy improvement came from - two honest accountings."""
    fig, ax = plt.subplots(figsize=(10.5, 3.9))

    # total improvement 1.557 -> 0.644 = 0.913 deg C, attributed two ways
    routes = [
        ("Accounting 1:\nvia the faster-sampled data",
         [("finer measurement data", 0.681, NEUTRAL), ("tuning to the building", 0.232, GOOD)]),
        ("Accounting 2:\nvia the physics model",
         [("different model design", 0.091, NEUTRAL), ("tuning to the building", 0.822, GOOD)]),
    ]

    for row, (label, parts) in enumerate(routes):
        left = 0.0
        for name, val, colour in parts:
            ax.barh(row, val, left=left, height=0.42, color=colour,
                    edgecolor="white", linewidth=1.2)
            pct = 100 * val / 0.913
            if val > 0.12:
                ax.text(left + val / 2, row, f"{name}\n{val:.3f} °C  ({pct:.0f} %)",
                        ha="center", va="center", fontsize=9.2, color="white",
                        fontweight="bold")
            else:
                ax.text(left + val / 2, row - 0.36, f"{name}\n{val:.3f} °C ({pct:.0f} %)",
                        ha="center", va="top", fontsize=8.8, color=INK)
            left += val

    ax.set_yticks([0, 1]); ax.set_yticklabels([r[0] for r in routes], fontsize=9.6)
    ax.set_xlabel("Reduction in prediction error (°C) — total improvement 0.913 °C")
    ax.set_xlim(0, 1.0)
    ax.set_ylim(-0.8, 1.5)
    ax.invert_yaxis()
    ax.set_title("Two defensible ways to attribute the same improvement",
                 fontsize=12.2, pad=14)
    fig.text(0.5, -0.12,
             "The same 0.913 °C gain can be credited mostly to better data or mostly to the "
             "tuning procedure, depending on the order in which\nthe two changes are counted. We "
             "report the tuning contribution as a range of 25–90 per cent rather than picking "
             "the flattering number.",
             ha="center", fontsize=9.4, color=INK)
    fig.tight_layout()
    save(fig, "fig6_where_accuracy")


# ---------------------------------------------------------------- Figure 7 ----
def fig_mechanism():
    """Why the more accurate twin trains a worse controller: a rough landscape."""
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0), sharey=True)
    x = np.linspace(0, 10, 900)
    rng = np.random.default_rng(7)
    base = 1.9 + 0.55 * np.cos(0.62 * x - 1.1) + 0.045 * x

    smooth = base
    rough = base + 0.30 * np.sin(9.5 * x) + 0.14 * np.sin(23.0 * x + 1.0) \
        + 0.06 * rng.standard_normal(x.size)

    for ax, y, title, colour, note in [
        (axes[0], smooth, "Twin A (less accurate, coarse time steps)", GOOD,
         "The learner can see which way is downhill.\nIt reaches the good setting."),
        (axes[1], rough, "Twin B (more accurate, fine time steps)", BAD,
         "Every small change looks like an improvement\nor a disaster. The learner cannot tell\n"
         "the real trend from the noise."),
    ]:
        ax.plot(x, y, color=colour, linewidth=1.7)
        ax.fill_between(x, y, y.max() + 0.5, color=colour, alpha=0.06)
        ax.set_xlabel("How the controller sets the heating")
        ax.set_title(title, fontsize=11)
        ax.set_xticks([]); ax.set_yticks([])
        ax.text(0.5, -0.20, note, transform=ax.transAxes, ha="center", va="top",
                fontsize=9.4, color=INK)

    imin = int(np.argmin(smooth))
    axes[0].plot(x[imin], smooth[imin], "o", color=GOOD, markersize=9)
    axes[0].annotate("best setting\nfound", (x[imin], smooth[imin]),
                     xytext=(x[imin] + 1.9, smooth[imin] + 0.85), fontsize=9,
                     color=GOOD, ha="center",
                     arrowprops=dict(arrowstyle="->", color=GOOD, linewidth=1.2))
    axes[1].plot(2.1, rough[np.argmin(np.abs(x - 2.1))], "o", color=BAD, markersize=9)
    axes[1].annotate("learner stops here", (2.1, rough[np.argmin(np.abs(x - 2.1))]),
                     xytext=(5.2, rough.max() - 0.15), fontsize=9, color=BAD, ha="center",
                     arrowprops=dict(arrowstyle="->", color=BAD, linewidth=1.2))

    axes[0].set_ylabel("How badly the building performs\n(lower is better)", fontsize=10)
    fig.suptitle("Why the more accurate twin produced the worse controller",
                 fontsize=12.5, fontweight="bold", y=1.02)
    fig.text(0.5, -0.23,
             "The finer-grained twin changes by a smaller amount at each step, which makes the "
             "picture the learning algorithm sees far bumpier.\nWe measured this bumpiness "
             "directly: it is about eight to nine times greater for the two twins that failed.",
             ha="center", fontsize=9.4, color=INK)
    fig.tight_layout()
    save(fig, "fig7_mechanism")


# ---------------------------------------------------------------- Figure 8 ----
def fig_transfer_verdicts():
    """Moving a finished controller to a new building: comfort and energy."""
    names = ["House, heat pump\n192 m²", "Flat, boiler\n48 m²",
             "Commercial building\n8 500 m²"]
    score = [0.665, 0.976, 0.431]
    thresh = [0.579, 0.938, 0.785]
    energy = [-7.3, -5.8, +35.3]
    passed = [False, False, True]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))

    xs = np.arange(3)
    a1.bar(xs, score, width=0.5, color=[GOOD if p else BAD for p in passed])
    for i in xs:
        a1.plot([i - 0.33, i + 0.33], [thresh[i]] * 2, color="black",
                linewidth=1.6, linestyle="--")
        a1.text(i, score[i] + 0.03, f"{score[i]:.2f}", ha="center", fontsize=10,
                fontweight="bold")
        a1.text(i, thresh[i] + 0.015, "target", ha="center", fontsize=8.2, color="black")
        a1.text(i, -0.10, "PASSED" if passed[i] else "MISSED", ha="center", fontsize=9.4,
                fontweight="bold", color=GOOD if passed[i] else BAD)
    a1.set_xticks(xs); a1.set_xticklabels(names, fontsize=9.3)
    a1.set_ylabel("Discomfort score (lower is better)")
    a1.set_ylim(-0.18, 1.15)
    a1.set_title("Comfort: did the transferred controller\nmeet the target set in advance?",
                 fontsize=11)

    cols = [GOOD if e < 0 else BAD for e in energy]
    a2.bar(xs, energy, width=0.5, color=cols)
    for i in xs:
        off = 1.8 if energy[i] > 0 else -4.2
        a2.text(i, energy[i] + off, f"{energy[i]:+.1f} %", ha="center", fontsize=10,
                fontweight="bold")
    a2.axhline(0, color="#5a6b73", linewidth=1.0)
    a2.set_xticks(xs); a2.set_xticklabels(names, fontsize=9.3)
    a2.set_ylabel("Change in energy use (%)")
    a2.set_ylim(-16, 46)
    a2.set_title("Energy: how much more or less the building\nused than with its own controller",
                 fontsize=11)

    fig.suptitle("A finished controller does not simply move to another building",
                 fontsize=12.5, fontweight="bold", y=1.03)
    fig.text(0.5, -0.07,
             "Two buildings saved energy but missed the comfort target. The third held comfort "
             "comfortably but used a third more energy.\nNone of the three is deployment-ready. "
             "This is the measured justification for the adaptation work planned next.",
             ha="center", fontsize=9.4, color=INK)
    fig.tight_layout()
    save(fig, "fig8_transfer_verdicts")


# ---------------------------------------------------------------- Figure 9 ----
def fig_forecast_effect():
    """Giving the controller a weather forecast is what makes it usable."""
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6))
    pairs = [
        ("Prediction error\n(°C)", 4.96, 0.72, "{:.2f}"),
        ("Time outside comfort\nrange (%)", 74.5, 4.9, "{:.1f}"),
        ("Overall discomfort\nscore", 1.046, 0.099, "{:.3f}"),
    ]
    for ax, (lab, before, after, fmt) in zip(axes, pairs):
        ax.bar([0, 1], [before, after], width=0.55, color=[BAD, GOOD])
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["without\nforecast", "with\nforecast"], fontsize=9.6)
        ax.set_title(lab, fontsize=10.5, fontweight="normal")
        ax.set_ylim(0, before * 1.28)
        for i, v in enumerate([before, after]):
            ax.text(i, v + before * 0.03, fmt.format(v), ha="center", fontsize=10,
                    fontweight="bold")
        ax.set_yticks([])
    fig.suptitle("Telling the controller what the weather will do changes it from unusable to usable",
                 fontsize=12.2, fontweight="bold", y=1.04)
    fig.text(0.5, -0.10,
             "The same controller, the same goals, the same twin. The only change is that it can "
             "see a few hours ahead instead of only the present moment.\nThis was the single most "
             "cost-effective improvement found during the year.",
             ha="center", fontsize=9.4, color=INK)
    fig.tight_layout()
    save(fig, "fig9_forecast_effect")


# --------------------------------------------------------------- Figure 10 ----
def fig_status():
    """Dashboard of the four stated deliverables."""
    fig, ax = plt.subplots(figsize=(10.8, 4.9))
    ax.set_xlim(0, 10.8); ax.set_ylim(0, 4.9); ax.axis("off")

    rows = [
        ("Digital twins built for each building", 1.00, GOOD, "Delivered",
         "4 buildings, error cut by 56–88 %"),
        ("Feedback control running in closed loop", 1.00, GOOD, "Delivered",
         "3 controller families on the live simulator"),
        ("Continuous learning for self-optimisation", 0.45, WARN, "Partly delivered",
         "adaptation stages built; no live online loop"),
        ("Integration with edge computing hardware", 0.15, BAD, "Not delivered",
         "speed requirement measured; no deployment"),
    ]

    y = 4.05
    ax.text(0.10, 4.70, "Deliverable", fontsize=10, fontweight="bold", color=INK)
    ax.text(4.95, 4.70, "Progress", fontsize=10, fontweight="bold", color=INK)
    ax.text(8.05, 4.70, "Status", fontsize=10, fontweight="bold", color=INK)
    ax.plot([0.10, 10.7], [4.56, 4.56], color="#c9d2d6", linewidth=1.0)

    for label, frac, colour, status, note in rows:
        ax.text(0.10, y + 0.10, label, fontsize=10.2, va="center", color=INK)
        ax.text(0.10, y - 0.28, note, fontsize=8.6, va="center", color="#6b7a82",
                style="italic")
        ax.add_patch(Rectangle((4.95, y - 0.10), 2.80, 0.34, facecolor="#e7ecee",
                               edgecolor="none"))
        ax.add_patch(Rectangle((4.95, y - 0.10), 2.80 * frac, 0.34, facecolor=colour,
                               edgecolor="none"))
        ax.text(8.05, y + 0.07, status, fontsize=10, va="center", color=colour,
                fontweight="bold")
        y -= 0.92

    ax.plot([0.10, 10.7], [0.62, 0.62], color="#c9d2d6", linewidth=1.0)
    ax.text(0.10, 0.05,
            "Two of the four objectives were not fully reached. Both are prerequisites for the "
            "next period,\nso they are reported as they stand: an accurate status is more useful "
            "to the schedule than a favourable one.",
            fontsize=9.4, color=INK, va="bottom")
    save(fig, "fig10_status")


if __name__ == "__main__":
    fig_two_twins()
    fig_where_accuracy()
    fig_mechanism()
    fig_transfer_verdicts()
    fig_forecast_effect()
    fig_status()
    print("figures in", OUT)
