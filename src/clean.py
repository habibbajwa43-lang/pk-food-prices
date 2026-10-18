"""
clean.py — turn PBS weekly SPI annexure files (Appendix-A) into one tidy table.

Input : every file matching data/raw/spi_weekly_annex_*.xlsx
Output: data/clean/spi_weekly_long.csv
        one row = one item, in one city, in one week
        columns: week_ending, city_code, city, item_no, item, unit,
                 price_min, price_avg, price_max, reported

Why the reshaping is needed: PBS prints the sheet like a paper table.
Cities run across the page in groups (Islamabad..Sargodha, Multan..., Bannu...),
each city has MIN/AVG/MAX columns, and the 51 items run down the page.
Analysis needs one row per item-city-week instead.

Decision on zeros: PBS writes 0 when an item was not priced in a city
(e.g. Rice IRRI-6/9 in Gujranwala). A price of Rs 0 is impossible, so 0 is
turned into missing (NaN) and flagged with reported = False. Rows are kept,
not dropped, so we can count exactly what is missing.
"""

import re
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd

RAW = Path("data/raw")
OUT = Path("data/clean/spi_weekly_long.csv")
CITY_RE = re.compile(r"^(.+?)\s*\((\d+)\)$")      # "Islamabad (01)"
DATE_RE = re.compile(r"PRICES ON (\d{2}-\d{2}-\d{4})")


def parse_file(path: Path) -> pd.DataFrame:
    ws = openpyxl.load_workbook(path, data_only=True)["Appendix-A"]
    rows = list(ws.iter_rows(values_only=True))
    records, cities, week = [], [], None

    for row in rows:
        cells = list(row)
        # A city header row: remember which column each city starts in.
        if cells[0] == "SL." and any(isinstance(c, str) and CITY_RE.match(c) for c in cells):
            cities = [(i, *CITY_RE.match(c).groups()) for i, c in enumerate(cells)
                      if isinstance(c, str) and CITY_RE.match(c)]
            continue
        # The date row: "PRICES ON 15-10-2026".
        for c in cells:
            if isinstance(c, str) and (m := DATE_RE.search(c)):
                week = pd.to_datetime(m.group(1), format="%d-%m-%Y")
        # An item row: serial number 1-51 plus an item name.
        if isinstance(cells[0], (int, float)) and isinstance(cells[1], str) and cities:
            for col, city, code in cities:
                mn, avg, mx = cells[col:col + 3]
                records.append({
                    "week_ending": week, "city_code": int(code), "city": city.strip(),
                    "item_no": int(cells[0]), "item": cells[1].strip(),
                    "unit": str(cells[2]).strip(),
                    "price_min": mn, "price_avg": avg, "price_max": mx,
                })
    df = pd.DataFrame(records)
    df["source_file"] = path.name
    return df


def main():
    files = sorted(RAW.glob("spi_weekly_annex_*.xlsx"))
    df = pd.concat([parse_file(f) for f in files], ignore_index=True)

    price_cols = ["price_min", "price_avg", "price_max"]
    df[price_cols] = df[price_cols].apply(pd.to_numeric, errors="coerce")
    n_zero = int((df["price_avg"] == 0).sum())
    df[price_cols] = df[price_cols].replace(0, np.nan)
    df["reported"] = df["price_avg"].notna()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    print(f"files read: {len(files)}")
    print(f"rows: {len(df)}  | weeks: {df.week_ending.nunique()}  | "
          f"cities: {df.city.nunique()}  | items: {df.item_no.nunique()}")
    print(f"avg price recorded as 0 -> set to missing: {n_zero}")
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
