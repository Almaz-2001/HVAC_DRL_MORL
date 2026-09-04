"""Figures for section 3 of the three-year iQUAT report.

Every value is read from the committed CSVs in reports/, never typed in: the
report has to trace to the same artifacts the article does. Labels are Russian,
so usetex stays off and matplotlib's default DejaVu font (which has Cyrillic)
is used.

Run:  python docs/report/make_report_figures.py
"""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
REP = ROOT / "reports"
OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(exist_ok=True)

V3, ACCURATE, MATCHED = "#1b7837", "#b2182b", "#d6604d"
HYBRID, PI, NEUTRAL, EDGE = "#2166ac", "#737373", "#6f4e7c", "#222222"

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 200, "savefig.bbox": "tight",
})


def load(name):
    with open(REP / name, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def save(fig, stem):
    for ext in ("png", "pdf"):
        fig.savefig(OUT / (stem + "." + ext))
    plt.close(fig)
    print("  wrote", stem)


# --- Fig 7: MORL Pareto front, comfort vs energy ----------------------------
allrows = load("morl_pareto_front_table.csv")
rows = [r for r in allrows if r["kind"] == "morl_pareto" and r["ms_mean"]]
pts = {}
for r in rows:
    pts.setdefault(r["label"], []).append(
        (float(r["energy_kwh_mean"]), float(r["violation_pct_mean"])))

order = ["comfort_000_energy_100", "comfort_025_energy_075",
         "comfort_050_energy_050", "comfort_075_energy_025",
         "comfort_100_energy_000"]
names = ["0.00 / 1.00", "0.25 / 0.75", "0.50 / 0.50", "0.75 / 0.25", "1.00 / 0.00"]
# Label directions chosen per point: the operating cluster is tight.
zoom_off = {"comfort_025_energy_075": (0, -20), "comfort_050_energy_050": (0, 14),
            "comfort_075_energy_025": (0, -22), "comfort_100_energy_000": (-6, 12)}

agg = {}
for lab in order:
    if lab in pts:
        e = np.array([p[0] for p in pts[lab]])
        v = np.array([p[1] for p in pts[lab]])
        agg[lab] = (e.mean(), v.mean(),
                    e.std() if len(e) > 1 else 0.0,
                    v.std() if len(v) > 1 else 0.0)

pi = [r for r in allrows if r["label"] == "pi_yearly_builtin"]
px = float(pi[0]["energy_kwh_mean"]) if pi else None
py = float(pi[0]["violation_pct_mean"]) if pi else None

fig, (axl, axr) = plt.subplots(1, 2, figsize=(9.2, 3.9))

for lab, nm in zip(order, names):
    if lab not in agg:
        continue
    e, v, es, vs = agg[lab]
    axl.errorbar(e, v, xerr=es or None, yerr=vs or None, fmt="o", ms=7,
                 color=HYBRID, ecolor=HYBRID, capsize=3, zorder=3)
axl.annotate("0.00 / 1.00\n(вырожденная точка:\nэнергия не расходуется)",
             agg["comfort_000_energy_100"][:2], textcoords="offset points",
             xytext=(12, -6), fontsize=8, color=EDGE, va="top")
if px is not None:
    axl.plot(px, py, "s", ms=8, color=PI, zorder=3)
    axl.annotate("встроенный\nПИ-регулятор", (px, py), textcoords="offset points",
                 xytext=(12, -2), fontsize=8, color=PI, va="center")
axl.add_patch(plt.Rectangle((205, -2), 70, 22, fill=False, ls="--", lw=1,
                            ec=NEUTRAL, zorder=4))
axl.annotate("см. панель (б)", (240, 20), textcoords="offset points",
             xytext=(0, 6), ha="center", fontsize=8, color=NEUTRAL)
axl.axhline(5.0, ls="--", lw=1, color=NEUTRAL)
axl.set_xlabel("Годовое потребление энергии, кВт" + chr(0x00B7) + "ч")
axl.set_ylabel("Доля времени вне зоны комфорта, %")
axl.set_title("(а) весь диапазон предпочтений", fontsize=9.5)
axl.set_ylim(-6, 100)
axl.grid(alpha=0.25, lw=0.6)

for lab, nm in zip(order, names):
    if lab not in agg or lab == "comfort_000_energy_100":
        continue
    e, v, es, vs = agg[lab]
    axr.errorbar(e, v, xerr=es or None, yerr=vs or None, fmt="o", ms=8,
                 color=HYBRID, ecolor=HYBRID, capsize=3, zorder=3)
    axr.annotate(nm, (e, v), textcoords="offset points",
                 xytext=zoom_off.get(lab, (0, 12)), ha="center", fontsize=8.5,
                 color=EDGE)
axr.axhline(5.0, ls="--", lw=1, color=NEUTRAL)
axr.text(0.99, 5.6, "инженерный порог 5 %", ha="right", fontsize=8,
         color=NEUTRAL, transform=axr.get_yaxis_transform())
axr.set_xlabel("Годовое потребление энергии, кВт" + chr(0x00B7) + "ч")
axr.set_title("(б) рабочая область, увеличено", fontsize=9.5)
axr.set_xlim(205, 275)
axr.set_ylim(-3, 22)
axr.grid(alpha=0.25, lw=0.6)

fig.suptitle("Фронт Парето MORL: веса предпочтений «комфорт / энергия», "
             "полосы " + chr(0x00B1) + "1 СКО по 5 зёрнам", y=1.02, fontsize=10)
save(fig, "fig07_morl_pareto")


# --- Fig 8: 5D vs 17D observation interface ---------------------------------
m = {r["variant"]: r for r in load("block2_morl_comparison_summary.csv")}
a, b = m["MORL_5D_basic"], m["MORL_17D_power_only"]
metrics = ["RMSE, °C", "Нарушение комфорта, %", "Оценка обслуживаемости"]
v5 = [float(a["rmse_c"]), float(a["violation_pct"]), float(a["m_s"])]
v17 = [float(b["rmse_c"]), float(b["violation_pct"]), float(b["m_s"])]

fig, axes = plt.subplots(1, 3, figsize=(7.6, 3.2))
for ax, name, x5, x17 in zip(axes, metrics, v5, v17):
    bars = ax.bar([0, 1], [x5, x17], color=[ACCURATE, HYBRID], width=0.6)
    for rect, val in zip(bars, [x5, x17]):
        ax.text(rect.get_x() + rect.get_width() / 2, val, format(val, "g"),
                ha="center", va="bottom", fontsize=8.5)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["5 призн.", "17 призн."])
    ax.set_title(name, fontsize=9)
    ax.set_ylim(0, max(x5, x17) * 1.30)
    ax.grid(axis="y", alpha=0.25, lw=0.6)
axes[2].axhline(1.0, ls="--", lw=1, color=EDGE)
axes[2].text(0.5, 1.03, "порог непригодности", ha="center", fontsize=7.5)
fig.suptitle("Влияние интерфейса наблюдений на управляемость (MORL)", y=1.03)
save(fig, "fig08_morl_5d_17d")


# --- Fig 9: fidelity vs utility ---------------------------------------------
sc = load("block2_fidelity_utility_scatter.csv")
colors = {"v3 (hourly)": V3, "matched v3 (15-min)": MATCHED,
          "v3.5 (calibrated)": ACCURATE}
labels = {"v3 (hourly)": "чёрный ящик, шаг 1 ч",
          "matched v3 (15-min)": "чёрный ящик, шаг 15 мин",
          "v3.5 (calibrated)": "серый ящик, калиброванный",
          "hybrid (v3 rollout + v3.5 censor)": "гибрид с разделением ролей"}
# The hourly BB and the hybrid share an x (same rollout model), so their
# labels are pushed apart vertically rather than left to collide.
# Four points in two tight clusters, so each label gets an explicit direction
# rather than a shared offset: the two collapsing models sit close together
# above the threshold, and the two usable ones share an x almost exactly.
offs = {"v3 (hourly)": (0, -20), "matched v3 (15-min)": (0, 13),
        "v3.5 (calibrated)": (10, -6),
        "hybrid (v3 rollout + v3.5 censor)": (0, 15)}
has = {"v3 (hourly)": "center", "matched v3 (15-min)": "center",
       "v3.5 (calibrated)": "left",
       "hybrid (v3 rollout + v3.5 censor)": "center"}

fig, ax = plt.subplots(figsize=(6.6, 4.4))
for r in sc:
    c = colors.get(r["controller"], HYBRID)
    x, y = float(r["rmse_24h_c"]), float(r["m_s_mean"])
    ax.errorbar(x, y, yerr=float(r["std_typ"] or 0), fmt="o", ms=10,
                color=c, ecolor=c, capsize=3, zorder=3)
    ax.annotate(labels.get(r["controller"], r["controller"]), (x, y),
                textcoords="offset points",
                xytext=offs.get(r["controller"], (0, 14)), fontsize=8.5,
                ha=has.get(r["controller"], "center"))
ax.axhline(1.0, ls="--", lw=1.2, color=EDGE)
ax.text(1.30, 0.90, "выше линии регулятор" + chr(10) + "непригоден к эксплуатации",
        fontsize=8, color=EDGE, ha="center", va="top")
ax.set_xlim(0.52, 1.80)
ax.set_ylim(-0.14, 1.44)
ax.set_xlabel("Ошибка прогноза за 24 ч (RMSE), °C   —   точнее влево")
ax.set_ylabel("Оценка обслуживаемости m_s   —   лучше ниже")
ax.set_title("Точность прогноза не предсказывает пригодность для обучения")
ax.grid(alpha=0.25, lw=0.6)
save(fig, "fig09_fidelity_utility")


# --- Fig 10: HDRL censor weight sweep ---------------------------------------
hd = load("block2_hdrl_lambda_sweep_seed_band.csv")
fig, ax = plt.subplots(figsize=(6.2, 3.8))
for window, color, nm in (("peak", ACCURATE, "пиковое окно (январь)"),
                          ("typical", HYBRID, "типовое окно (февраль)")):
    rs = sorted([r for r in hd if r["window"] == window],
                key=lambda r: float(r["lambda_temp_disagree"]))
    x = [float(r["lambda_temp_disagree"]) for r in rs]
    y = np.array([float(r["m_s_mean"]) for r in rs])
    s = np.array([float(r["m_s_std"]) for r in rs])
    ax.plot(x, y, "o-", color=color, label=nm, zorder=3)
    ax.fill_between(x, y - s, y + s, color=color, alpha=0.18, lw=0)
ax.set_xlabel("Вес цензора рассогласования моделей")
ax.set_ylabel("Оценка обслуживаемости m_s")
ax.set_title("Устойчивость эффекта: 3 зерна инициализации на каждой точке")
ax.legend(frameon=False, fontsize=8.5, title="полоса " + chr(0x00B1) + "1 СКО")
ax.grid(alpha=0.25, lw=0.6)
save(fig, "fig10_hdrl_lambda")


# --- Fig 11: computational efficiency ---------------------------------------
nm = {"boptest_rte_http": "эмулятор BOPTEST\n(эталон)",
      "v3_surrogate": "суррогат\nчёрного ящика",
      "v35_calibrated_surrogate": "суррогат\nсерого ящика",
      "hybrid_v3_v35_surrogate": "гибридная\nсреда"}
col = {"boptest_rte_http": PI, "v3_surrogate": V3,
       "v35_calibrated_surrogate": ACCURATE, "hybrid_v3_v35_surrogate": HYBRID}
sp = [r for r in load("speed_benchmark_table.csv") if r["backend"] in nm]

fig, ax = plt.subplots(figsize=(6.6, 3.8))
xs = np.arange(len(sp))
vals = [float(r["env_steps_per_sec"]) for r in sp]
bars = ax.bar(xs, vals, color=[col[r["backend"]] for r in sp], width=0.62)
for rect, r in zip(bars, sp):
    v = float(r["env_steps_per_sec"])
    sup = float(r["speedup_vs_boptest_rte"])
    tag = format(v, ".0f") + " шаг/с"
    if sup > 1.5:
        tag = tag + "\nускорение " + chr(0x00D7) + format(sup, ".0f")
    ax.text(rect.get_x() + rect.get_width() / 2, v * 1.15, tag,
            ha="center", fontsize=8)
ax.set_yscale("log")
ax.set_ylim(10, 20000)
ax.set_xticks(xs)
ax.set_xticklabels([nm[r["backend"]] for r in sp], fontsize=8.5)
ax.set_ylabel("Шагов среды в секунду (лог. шкала)")
ax.set_title("Вычислительная производительность обучающих сред")
ax.grid(axis="y", alpha=0.25, lw=0.6)
save(fig, "fig11_speed")


# --- Fig 12: transfer to the hydronic family --------------------------------
tm = load("block3_transfer_matrix.csv")
short = {"bestest_hydronic": "жилое здание,\nводяное отопление",
         "bestest_hydronic_heat_pump": "жилое здание,\nтепловой насос",
         "singlezone_commercial_hydronic": "коммерческое\nздание"}
fig, ax = plt.subplots(figsize=(6.6, 3.8))
xs = np.arange(len(tm))
raw = [float(r["raw_rmse_t_c"]) for r in tm]
cal = [float(r["full_rmse_t_c"]) for r in tm]
ax.bar(xs - 0.19, raw, 0.36, label="до рекалибровки", color=ACCURATE)
ax.bar(xs + 0.19, cal, 0.36, label="после рекалибровки (этапы A/B/C)", color=V3)
for i, r in enumerate(tm):
    ax.text(i, max(raw[i], cal[i]) * 1.06,
            chr(0x2212) + format(float(r["rmse_improvement_pct"]), ".0f") + " %",
            ha="center", fontsize=9)
ax.set_xticks(xs)
ax.set_xticklabels([short.get(r["testcase"], r["testcase"]) for r in tm],
                   fontsize=8.5)
ax.set_ylim(0, max(raw) * 1.38)
ax.set_ylabel("Ошибка прогноза RMSE, °C")
ax.set_title("Переносимость методики на три независимых объекта")
ax.legend(frameon=False, fontsize=8.5, loc="upper left", ncol=2)
ax.grid(axis="y", alpha=0.25, lw=0.6)
save(fig, "fig12_transfer")

print("done")
