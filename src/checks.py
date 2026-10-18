"""
checks.py — the six-things check (missing, duplicates, wrong types, wrong units,
encoding, drift) run on both cleaned tables. Prints counts only; it changes nothing.

Run after clean.py and parse_reports.py:
    python src/checks.py > reports/checks_output.txt
"""

import pandas as pd

city = pd.read_csv("data/clean/spi_weekly_long.csv", parse_dates=["week_ending"])
nat = pd.read_csv("data/clean/spi_national_weekly.csv", parse_dates=["week_ending"])

print("=== SHAPE ===")
print(f"city table: {len(city)} rows, {city.week_ending.nunique()} weeks, "
      f"{city.city.nunique()} cities, {city.item_no.nunique()} items")
print(f"national table: {len(nat)} rows, {nat.week_ending.nunique()} weeks, "
      f"{nat.item.nunique()} item names")

print("\n=== 1. MISSING ===")
miss = city[~city.reported]
print(f"city table: {len(miss)} of {len(city)} item-city-weeks not priced (PBS wrote 0)")
print(miss.groupby(["item", "city"]).size().to_string())
print(f"national table: missing price_avg = {nat.price_avg.isna().sum()}")
weeks = sorted(nat.week_ending.unique())
gaps = [(a, b) for a, b in zip(weeks, weeks[1:]) if (b - a).days > 8]
print("national gaps longer than 8 days:")
for a, b in gaps:
    print(f"  {pd.Timestamp(a).date()} -> {pd.Timestamp(b).date()} ({(b - a).days} days)")

print("\n=== 2. DUPLICATES ===")
print("city table duplicate item-city-week:",
      city.duplicated(["week_ending", "city", "item_no"]).sum())
print("national table duplicate item-week:",
      nat.duplicated(["week_ending", "item"]).sum())

print("\n=== 3. WRONG TYPES ===")
print(city.dtypes.to_string())
print("min > avg or avg > max (city):",
      ((city.price_min > city.price_avg) | (city.price_avg > city.price_max)).sum())
print("negative prices:", (city[["price_min", "price_avg", "price_max"]] < 0).sum().sum())

print("\n=== 4. UNITS ===")
u = city.groupby("item_no").unit.nunique()
print("items whose unit changes across weeks/cities (city table):", (u > 1).sum())
print("unit counts (one item each):")
print(city.drop_duplicates("item_no").unit.value_counts().to_string())

print("\n=== 5. ENCODING ===")
odd = city.item[city.item.str.contains(r"[^\x20-\x7E]", regex=True)].unique()
print("item names with non-ASCII characters:", list(odd))
print("city names:", sorted(city.city.unique()))

print("\n=== 6. DRIFT ===")
cnt = nat.groupby("item").week_ending.nunique()
print("item names not present in every week (national):")
print(cnt[cnt < cnt.max()].to_string())
dow = pd.Series(pd.to_datetime(weeks)).dt.day_name().value_counts()
print("weekday of week_ending:", dow.to_dict())
print("non-Thursday weeks:",
      [str(pd.Timestamp(w).date()) for w in weeks if pd.Timestamp(w).day_name() != "Thursday"])
