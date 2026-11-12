"""
results_charts.py — charts of the forecasting results, saved to reports/figures/.
Run after src/forecast.py:   python src/results_charts.py

  results_1_staples_history.png   two years of weekly prices, 8 staples (small multiples)
  results_2_error_by_horizon.png  average error (MAE) of each model, 1–4 weeks ahead, staples
  results_3_predictability.png    how much each item's price moves in a typical week
  results_4_range_coverage.png    how often the 80% price range contained the real price
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

FIG, OUT = Path("reports/figures"), Path("reports/model_outputs")
FIG.mkdir(parents=True, exist_ok=True)
INK, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
COL = {"naive": "#2a78d6", "linear_lags": "#eb6834", "xgboost_lags": "#1baf7a", "seasonal_naive": "#eda100"}
NAME = {"naive": "Naive", "linear_lags": "Linear regression", "xgboost_lags": "XGBoost",
        "seasonal_naive": "Seasonal naive"}
STAPLES = ["Onions", "Tomatoes", "Potatoes", "Sugar Refined", "Wheat Flour Bag",
           "Eggs Hen (Farm)", "Chicken Farm Broiler (Live)", "Pulse Masoor (Washed)"]
SRC = "Source: Pakistan Bureau of Statistics, Weekly SPI (national average, 17 cities)."
plt.rcParams.update({"font.size": 11, "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.facecolor": SURF,
                     "figure.facecolor": SURF, "axes.spines.top": False, "axes.spines.right": False})


def finish(fig, name, caption):
    fig.text(0.01, 0.01, caption, fontsize=9, color=MUTED)
    fig.savefig(FIG / name, dpi=150, bbox_inches="tight")
    plt.close(fig)


nat = pd.read_csv("data/clean/spi_national_weekly.csv", parse_dates=["week_ending"])

# 1. Two years of staple prices
fig, axes = plt.subplots(2, 4, figsize=(15, 6.5), sharex=True)
for ax, item in zip(axes.flat, STAPLES):
    s = nat[nat.item == item].sort_values("week_ending")
    ax.plot(s.week_ending, s.price_avg, color=INK, lw=2)
    first, last = s.price_avg.iloc[0], s.price_avg.iloc[-1]
    ax.set_title(f"{item}\nRs {first:,.0f} → Rs {last:,.0f} ({(last / first - 1) * 100:+.0f}%)",
                 fontsize=10, color=INK, loc="left")
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.tick_params(axis="x", labelrotation=45, labelsize=8)
    ax.set_ylabel(f"Rs per {s.unit.iloc[0]}", fontsize=8)
fig.suptitle("In two years potatoes halved, wheat flour rose 60%, and tomato prices spiked three times",
             fontsize=14, color=INK, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0.03, 1, 0.95))
finish(fig, "results_1_staples_history.png",
       f"Weekly national average prices, 24 Oct 2024 to 5 Nov 2026. {SRC}")

# 2. Error by horizon
s = pd.read_csv(OUT / "metrics_summary.csv")
s = s[s.scope == "8 staples"]
fig, ax = plt.subplots(figsize=(9, 5))
for m in ["naive", "linear_lags", "xgboost_lags"]:
    d = s[s.model == m].sort_values("h")
    ax.plot(d.h, d.MAE, color=COL[m], lw=2, marker="o", ms=8)
    ax.annotate(f"{NAME[m]}  Rs {d.MAE.iloc[-1]:.1f}", (d.h.iloc[-1], d.MAE.iloc[-1]),
                xytext=(8, 0), textcoords="offset points", va="center", color=INK, fontsize=10)
ax.set_xticks([1, 2, 3, 4], ["1 week", "2 weeks", "3 weeks", "4 weeks"])
ax.set_xlim(0.8, 5.2)
ax.set_ylabel("Average error, Rs per unit (MAE)")
ax.grid(axis="y", color=GRID, lw=0.8)
ax.set_title("Linear regression beats “same as last week” at every horizon, but only by 2–6%",
             fontsize=13, color=INK, loc="left")
sn = s[(s.model == "seasonal_naive") & (s.h == 1)].MAE.iloc[0]
finish(fig, "results_2_error_by_horizon.png",
       f"8 staples, rolling-origin backtest, 43 test weeks (Jan–Nov 2026). Most of the gap comes from wheat flour, the costliest staple.\nSeasonal naive not shown (MAE Rs {sn:.0f}). {SRC}")

# 3. Predictability
p = pd.read_csv(OUT / "item_predictability.csv").head(12).iloc[::-1]
fig, ax = plt.subplots(figsize=(9, 6))
ax.barh(p.item, p.weekly_change_sd_pct, color="#2a78d6", height=0.6)
for y, v in enumerate(p.weekly_change_sd_pct):
    ax.text(v + 0.3, y, f"{v:.1f}%", va="center", color=INK, fontsize=9)
ax.set_xlabel("Typical weekly price change (standard deviation, %)")
ax.grid(axis="x", color=GRID, lw=0.8)
ax.set_title("Tomato prices move about 22% in a typical week, more than twice any other item",
             fontsize=13, color=INK, loc="left")
finish(fig, "results_3_predictability.png", f"12 most volatile of 51 SPI items, Oct 2024–Nov 2026. {SRC}")

# 4. Range coverage
c = pd.read_csv(OUT / "interval_coverage.csv")
c = c[c.model != "seasonal_naive"]
fig, ax = plt.subplots(figsize=(9, 5))
w = 0.26
for i, m in enumerate(["naive", "linear_lags", "xgboost_lags"]):
    d = c[c.model == m].sort_values("h")
    ax.bar(d.h + (i - 1) * w, d["coverage_%"], width=w - 0.02, color=COL[m], label=NAME[m])
ax.axhline(80, color=INK, lw=1, ls="--")
ax.text(4.45, 80.5, "target 80%", color=INK, fontsize=9)
ax.set_xticks([1, 2, 3, 4], ["1 week", "2 weeks", "3 weeks", "4 weeks"])
ax.set_ylim(0, 100)
ax.set_ylabel("Real price inside the 80% range (%)")
ax.legend(frameon=False, loc="lower left")
ax.grid(axis="y", color=GRID, lw=0.8)
ax.set_title("The naive model’s price range is honest; the other models are over-confident",
             fontsize=13, color=INK, loc="left")
finish(fig, "results_4_range_coverage.png", f"All 51 items, backtest Jan–Nov 2026. {SRC}")
print("saved results charts to", FIG)
