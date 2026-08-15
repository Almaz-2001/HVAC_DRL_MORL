"""Charts for the funder-facing progress report.

These are deliberately NOT the manuscript figures. The manuscript's figures assume
the reader knows what a maintenance score, a rollout RMSE or a policy-gradient
method is. A funding body does not, so each chart here carries at most one idea,
labels it in plain words, and states the conclusion on the chart itself.

Numbers are the same ones used in the report text and trace to reports/*.csv in the
project repository.

Run with the project venv:  .venv/Scripts/python.exe docs/current_tasks/make_report_figures.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
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


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", name + ".png")


# ---------------------------------------------------------------- Figure 1 ----
def fig_concept():
    """What the project builds, in four boxes."""
    fig, ax = plt.subplots(figsize=(11, 3.9))
    ax.set_xlim(0, 11); ax.set_ylim(0, 3.9); ax.axis("off")

    boxes = [
        (0.20, "Real building", "sensor data:\ntemperature, weather,\nenergy use", NEUTRAL),
        (3.00, "Digital twin", "a fast software copy\nof the building", ACCENT),
        (5.80, "Control software", "learns by practising\non the twin", ACCENT),
        (8.60, "Building, controlled", "less energy,\nstable comfort", GOOD),
    ]
    for x, title, sub, colour in boxes:
        ax.add_patch(FancyBboxPatch((x, 1.60), 2.20, 1.50, boxstyle="round,pad=0.06",
                                    linewidth=1.6, edgecolor=colour, facecolor=colour + "18"))
        ax.text(x + 1.10, 2.76, title, ha="center", va="center", fontsize=11, fontweight="bold")
        ax.text(x + 1.10, 2.12, sub, ha="center", va="center", fontsize=9.2, color="#33414a")

    for x in (2.44, 5.24, 8.04):
        ax.add_patch(FancyArrowPatch((x, 2.35), (x + 0.50, 2.35), arrowstyle="-|>",
                                     mutation_scale=15, linewidth=1.6, color="#5a6b73"))

    # the feedback path runs UNDER the row of boxes; routing it through them made the
    # first version unreadable
    ax.plot([9.70, 9.70, 1.30, 1.30], [1.60, 0.95, 0.95, 1.40], color="#5a6b73",
            linewidth=1.3, linestyle=(0, (4, 3)))
    ax.add_patch(FancyArrowPatch((1.30, 1.40), (1.30, 1.58), arrowstyle="-|>",
                                 mutation_scale=13, linewidth=1.3, color="#5a6b73"))
    ax.text(5.50, 0.64, "measurements feed back and keep the twin up to date",
            ha="center", fontsize=9.2, style="italic", color="#5a6b73")

    ax.text(5.50, 3.60, "Why a twin is needed: the control software needs millions of practice "
                        "attempts.\nOn a real building that would take decades and would make "
                        "occupants uncomfortable.",
            ha="center", fontsize=9.6, color="#33414a")
    save(fig, "fig1_concept")


# ---------------------------------------------------------------- Figure 2 ----
def fig_main_finding():
    """The headline result: model accuracy does not predict control performance."""
    names = ["Simple model\n(least accurate)", "Refined model", "Detailed physics model\n(most accurate)"]
    err = [1.557, 0.876, 0.644]              # 24 h prediction error, deg C
    fail = [4.4, 91.4, 82.4]                 # % of time outside comfort band, typical window
    cols = [GOOD, BAD, BAD]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.1))

    a1.bar(range(3), err, color=cols, width=0.55)
    a1.set_xticks(range(3)); a1.set_xticklabels(names, fontsize=9.3)
    a1.set_ylabel("Prediction error (°C)")
    a1.set_title("How accurately each model\npredicts the building", fontsize=11)
    for i, v in enumerate(err):
        a1.text(i, v + 0.04, f"{v:.2f}", ha="center", fontsize=10, fontweight="bold")
    a1.set_ylim(0, 1.85)
    a1.text(0.5, 0.94, "lower is better", transform=a1.transAxes, ha="center",
            fontsize=9, style="italic", color="#5a6b73")

    a2.bar(range(3), fail, color=cols, width=0.55)
    a2.set_xticks(range(3)); a2.set_xticklabels(names, fontsize=9.3)
    a2.set_ylabel("Time outside comfort range (%)")
    a2.set_title("How well the controller it produced\nactually ran the building", fontsize=11)
    for i, v in enumerate(fail):
        a2.text(i, v + 2, f"{v:.0f}%", ha="center", fontsize=10, fontweight="bold")
    a2.set_ylim(0, 108)
    a2.text(0.5, 0.94, "lower is better", transform=a2.transAxes, ha="center",
            fontsize=9, style="italic", color="#5a6b73")

    fig.suptitle("The central discovery: the two most accurate models failed, the least accurate one worked",
                 fontsize=12.5, fontweight="bold", y=1.02)
    fig.text(0.5, -0.06,
             "Choosing a model by prediction accuracy — what the field does today — picks the wrong "
             "one.\nThe simple model on the left is the only one of the three that produced a "
             "usable controller.",
             ha="center", fontsize=9.6, color="#33414a")
    fig.tight_layout()
    save(fig, "fig2_main_finding")


# ---------------------------------------------------------------- Figure 3 ----
def fig_outcome():
    """What the resulting controller delivers, against the controller in use today."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.9))

    labels = ["Standard controller\nin use today", "Our controller"]
    viol = [63.6, 2.4]
    a1.barh(labels, viol, color=[NEUTRAL, GOOD], height=0.5)
    for i, v in enumerate(viol):
        a1.text(v + 1.5, i, f"{v:.1f}%", va="center", fontsize=11, fontweight="bold")
    a1.set_xlim(0, 78)
    a1.set_xlabel("Time outside the comfort range (%)")
    a1.set_title("Occupant comfort", fontsize=11)
    a1.invert_yaxis()

    labels2 = ["Training on the\nreal simulator", "Training on\nour digital twin"]
    hours = [66, 0.78]
    a2.barh(labels2, hours, color=[NEUTRAL, GOOD], height=0.5)
    a2.text(hours[0] + 1.5, 0, "66 hours", va="center", fontsize=11, fontweight="bold")
    a2.text(hours[1] + 1.5, 1, "47 minutes", va="center", fontsize=11, fontweight="bold")
    a2.set_xlim(0, 82)
    a2.set_xlabel("Time to train one controller")
    a2.set_title("Development cost", fontsize=11)
    a2.invert_yaxis()

    fig.suptitle("What the resulting system delivers", fontsize=12.5, fontweight="bold", y=1.03)
    fig.tight_layout()
    save(fig, "fig3_outcome")


# ---------------------------------------------------------------- Figure 4 ----
def fig_transfer():
    """The twin-building method applied to four buildings of very different size."""
    bldg = ["Office\n48 m²\n(original)", "Flat, boiler\n48 m²", "House, heat pump\n192 m²",
            "Commercial\n8 500 m²"]
    before = [1.466, 2.666, 1.421, 1.952]
    after = [0.644, 0.335, 0.565, 0.238]
    gain = [56.1, 87.4, 60.2, 87.8]

    fig, ax = plt.subplots(figsize=(10, 4.0))
    x = range(4); w = 0.36
    ax.bar([i - w / 2 for i in x], before, w, label="before tuning to the building", color=NEUTRAL)
    ax.bar([i + w / 2 for i in x], after, w, label="after tuning", color=GOOD)
    for i in x:
        ax.text(i + w / 2, after[i] + 0.06, f"-{gain[i]:.0f}%", ha="center",
                fontsize=10, fontweight="bold", color=GOOD)
    ax.set_xticks(list(x)); ax.set_xticklabels(bldg, fontsize=9.3)
    ax.set_ylabel("Prediction error (°C)")
    ax.set_ylim(0, 3.1)
    ax.legend(frameon=False, fontsize=9.5, loc="upper right")
    ax.set_title("The same twin-building method works across buildings of very different size",
                 fontsize=12.5, pad=12)
    fig.text(0.5, -0.05,
             "Floor area varies by a factor of 175 between the smallest and largest building, and "
             "the heating equipment differs in every case.\nThe tuning procedure reduced the error "
             "on every one of them.",
             ha="center", fontsize=9.6, color="#33414a")
    fig.tight_layout()
    save(fig, "fig4_transfer")


if __name__ == "__main__":
    fig_concept()
    fig_main_finding()
    fig_outcome()
    fig_transfer()
    print("figures in", OUT)
