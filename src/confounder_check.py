"""
confounder_check.py — "Are bigger cities more expensive?" sliced by item type.

Relationship: big city (Karachi, Lahore) vs the other 15 cities -> price level.
Third variable: item type (fresh vegetables vs packaged goods).
Uses the city table (6 weeks), averaging each city's price over the 6 weeks.
Ratio > 1 means Karachi/Lahore are dearer than the average of the other cities.
"""
import pandas as pd

city = pd.read_csv("data/clean/spi_weekly_long.csv")
BIG = ["Karachi", "Lahore"]
GROUPS = {
    "fresh vegetables": ["Tomatoes", "Potatoes"],
    "packaged goods": ["Sugar Refined", "Tea Lipton Yellow Label 190 gm Packet"],
}

rows = []
for group, items in GROUPS.items():
    for item in items:
        d = city[city.item == item].groupby("city").price_avg.mean()
        big = d[BIG].mean()
        other = d.drop(BIG).mean()
        rows.append({"group": group, "item": item,
                     "karachi": round(d["Karachi"], 2), "lahore": round(d["Lahore"], 2),
                     "big_city_avg": round(big, 2), "other_15_avg": round(other, 2),
                     "ratio_big_to_other": round(big / other, 3)})
out = pd.DataFrame(rows)
print(out.to_string(index=False))

# Overall (all four items pooled, before slicing): average of the item ratios
print("\nPooled ratio (all 4 items):", round(out.ratio_big_to_other.mean(), 3))
print(out.groupby("group").ratio_big_to_other.mean().round(3).to_string())
