"""
eda_charts.py — draft EDA charts from the cleaned tables, saved to reports/figures/.

Headline titles and captions were written by the team after checking the numbers.

Charts:
  1. Weekly national prices of 8 food staples, indexed to the first week = 100
     (standardization: puts Rs 50 potatoes and Rs 2,600 flour bags on one scale).
  2. Before/after transformation: raw prices vs log prices across all 51 items.
  3. Change from the same week last year, per food item (latest report week).
  4. City spread: lowest vs highest city average price in the latest week.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIG = Path("reports/figures")
FIG.mkdir(parents=True, exist_ok=True)
nat = pd.read_csv("data/clean/spi_national_weekly.csv", parse_dates=["week_ending"])
city = pd.read_csv("data/clean/spi_weekly_long.csv", parse_dates=["week_ending"])

STAPLES = ["Tomatoes", "Onions", "Potatoes", "Eggs Hen (Farm)",
           "Chicken Farm Broiler (Live)", "Sugar Refined", "Wheat Flour Bag",
           "Pulse Masoor (Washed)"]

# ---- 1. Indexed weekly prices, 2026 run of consecutive weeks only
recent = nat[nat.week_ending >= "2026-01-01"]
wide = recent[recent.item.isin(STAPLES)].pivot(index="week_ending", columns="item",
                                                values="price_avg")
indexed = wide / wide.iloc[0] * 100
fig, ax = plt.subplots(figsize=(9, 5))
for col in indexed:
    ax.plot(indexed.index, indexed[col], marker="o", ms=3, label=col)
ax.axhline(100, color="grey", lw=0.8, ls="--")
ax.set_title("Onion Prices More Than Doubled While Tomato Prices Fell by 26%\nBetween July and September 2026", fontsize=11)
ax.set_ylabel(f"Index (week of {indexed.index[0].date()} = 100)")
ax.legend(fontsize=8, ncol=2)
fig.autofmt_xdate()
fig.text(0.01, 0.01, "Source: PBS Sensitive Price Indicator (SPI), national average across 17 urban centres, "
         "2 July–3 September 2026; prices indexed to the first week = 100.", fontsize=7.5)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(FIG / "1_staples_indexed.png", dpi=150)

# ---- 2. Transformation: raw vs log prices (latest week, all items)
latest = nat[nat.week_ending == nat.week_ending.max()]
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
axes[0].hist(latest.price_avg, bins=20)
axes[0].set_title("Before: raw prices (Rs)")
axes[1].hist(np.log10(latest.price_avg), bins=20)
axes[1].set_title("After: log10(price)")
fig.suptitle("Log Transformation Spreads Out Skewed Price Data, Making Differences\n"
             "Between Cheap and Expensive Items Easier to See", fontsize=11)
fig.text(0.01, 0.01, "Source: PBS SPI price data; raw and log-transformed item prices compared "
         "to show how transformation changes the distribution.", fontsize=7.5)
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(FIG / "2_log_transform.png", dpi=150)

# ---- 3. Year-on-year change for food staples (latest report week vs year-ago week)
last_week = nat.week_ending.max()
year_ago = nat[(nat.week_ending < last_week - pd.Timedelta(days=300))].week_ending.max()
a = nat[nat.week_ending == last_week].set_index("item").price_avg
b = nat[nat.week_ending == year_ago].set_index("item").price_avg
yoy = ((a / b - 1) * 100).reindex(STAPLES).sort_values()
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.barh(yoy.index, yoy.values, color=["#c0504d" if v > 0 else "#4f81bd" for v in yoy])
ax.axvline(0, color="black", lw=0.8)
ax.set_xlabel(f"% change, {last_week.date()} vs {year_ago.date()}")
ax.set_title("Onion Prices Rose 162.8% Year-on-Year While Potato Prices Fell 31.6%", fontsize=11)
fig.text(0.01, 0.01, "Source: PBS SPI, comparison with year-ago prices for selected essential items, "
         "September 2026 versus September 2025.", fontsize=7.5)
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(FIG / "3_yoy_change.png", dpi=150)

# ---- 4. City spread in the latest annex week
lw = city[city.week_ending == city.week_ending.max()]
s = lw[lw.item.isin(STAPLES)].groupby("item").price_avg.agg(["min", "max"])
s["spread_pct"] = (s["max"] / s["min"] - 1) * 100
s = s.sort_values("spread_pct")
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.barh(s.index, s.spread_pct)
ax.set_xlabel("Highest city average vs lowest city average (%)")
ax.set_title("Tomato and Potato Prices Vary Sharply Across Cities,\n"
             "While Sugar Prices Remain More Consistent", fontsize=11)
fig.text(0.01, 0.01, "Source: PBS SPI city-level prices across 17 urban centres; spread = (highest - lowest "
         "city price) / lowest city price.", fontsize=7.5)
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(FIG / "4_city_spread.png", dpi=150)

print("saved charts to", FIG)
print("\nYoY % change:\n", yoy.round(1).to_string())
print("\nCity spread %:\n", s.round(1).to_string())
