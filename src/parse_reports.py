"""
parse_reports.py — read national average item prices from PBS weekly SPI Report files.

Input : data/raw/reports/*.xlsx   ("SPI Report" Excel, one file per week)
Output: data/clean/spi_national_weekly.csv
        one row = one item, in one week (national average across 17 cities)
        columns: week_ending, item, unit, price_avg, source_file, role

Each report's "Page 2" table gives, for every item, three prices:
  col 3 = this week, col 4 = previous week, col 5 = same week last year.
So one file gives three dated observations. 'role' records which one a
row came from ("current", "previous", "year_ago"), because the same week
can appear in two files (as "current" in one and "previous" in the next).
We keep the "current" value when both exist, and check that they agree.
"""

import re
from pathlib import Path

import openpyxl
import pandas as pd

RAW = Path("data/raw/reports")
OUT = Path("data/clean/spi_national_weekly.csv")
DATE = r"(\d{2}-\d{2}-\d{4})"


def parse_report(path: Path) -> pd.DataFrame:
    ws = openpyxl.load_workbook(path, data_only=True)["Page 2"]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    # Line 1: "...for the week ended on 03-09-2026 over"
    # Line 2: "previous and corresponding weeks ended on 27-08-2026 and 04-09-2025 ..."
    current = re.search(DATE, str(rows[0][1])).group(1)
    previous, year_ago = re.findall(DATE, str(rows[1][0]))[:2]
    dates = {"current": current, "previous": previous, "year_ago": year_ago}

    recs = []
    for r in rows:
        # item rows: col B = serial number, col C = item name, cols E-G = prices
        if isinstance(r[1], int) and isinstance(r[2], str) and isinstance(r[4], (int, float)):
            for role, col in [("current", 4), ("previous", 5), ("year_ago", 6)]:
                recs.append({
                    "week_ending": pd.to_datetime(dates[role], format="%d-%m-%Y"),
                    "item": r[2].strip(), "unit": str(r[3]).strip(),
                    "price_avg": r[col], "source_file": path.name, "role": role,
                })
    return pd.DataFrame(recs)


def main():
    files = sorted(RAW.glob("*.xlsx"))
    raw = pd.concat([parse_report(f) for f in files], ignore_index=True)

    # Same item-week reported twice (current in one file, previous in next): do they agree?
    both = raw[raw.role.isin(["current", "previous"])].pivot_table(
        index=["week_ending", "item"], columns="role", values="price_avg")
    both = both.dropna()
    diff = (both["current"] - both["previous"]).abs()
    print(f"item-weeks reported in two files: {len(both)}; "
          f"disagreeing by > Rs 0.01: {(diff > 0.01).sum()}")

    # Keep one value per item-week: prefer 'current', then 'previous', then 'year_ago'.
    order = {"current": 0, "previous": 1, "year_ago": 2}
    df = (raw.assign(rank=raw.role.map(order))
             .sort_values(["week_ending", "item", "rank"])
             .drop_duplicates(["week_ending", "item"])
             .drop(columns="rank"))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"files read: {len(files)} | rows kept: {len(df)} | items: {df.item.nunique()}")
    print("weeks covered:", ", ".join(sorted(df.week_ending.dt.strftime('%Y-%m-%d').unique())))
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
