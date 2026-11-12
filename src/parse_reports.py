"""
parse_reports.py — national average item prices from PBS weekly SPI Report files.

Inputs (both are used when present):
  1. data/raw/reports/*.xlsx
     "SPI Report (Excel)" files downloaded by hand (9 weeks, Jul–Sep 2026).
  2. data/raw/pbs_report_extract/  (payload.txt + meta.txt)
     The "Page 2" price table of all 52 SPI Report Excel files PBS lists in its
     archive (weeks ending 23-10-2025 to 05-11-2026). See
     data/raw/pbs_report_extract/README.md for how it was made and checked.

Output: data/clean/spi_national_weekly.csv
        one row = one item, in one week (national average across 17 cities)
        columns: week_ending, item, unit, price_avg, source_file, role

Each report gives, for every item, three prices: this week ("current"), the
previous week ("previous") and the same week a year earlier ("year_ago").
The same item-week therefore often appears more than once. We check that the
copies agree, then keep one value: current > previous > year_ago.

Label drift fixed here (see CLEANING.md): the gas item appears as
"Gas Charges for Q1", "Gas Charges upto 3.3719 MMBTU" and, in some files,
the typo "Gad Charges for Q1". All three are mapped to "Gas Charges for Q1".
"""

import base64
import re
import zlib
from pathlib import Path

import openpyxl
import pandas as pd

RAW = Path("data/raw/reports")
EXTRACT = Path("data/raw/pbs_report_extract")
OUT = Path("data/clean/spi_national_weekly.csv")
DATE = r"(\d{2}-\d{2}-\d{4})"
ROLES = ["current", "previous", "year_ago"]
ITEM_FIX = {"Gas Charges upto 3.3719 MMBTU": "Gas Charges for Q1",
            "Gad Charges for Q1": "Gas Charges for Q1"}


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
            for role, col in zip(ROLES, (4, 5, 6)):
                recs.append({"week_ending": pd.to_datetime(dates[role], format="%d-%m-%Y"),
                             "item": r[2].strip(), "unit": str(r[3]).strip(),
                             "price_avg": r[col], "source_file": path.name, "role": role})
    return pd.DataFrame(recs)


def parse_extract(folder: Path) -> pd.DataFrame:
    """Decode the compact extract (see its README): prices in paisa, delta + zigzag
    varint encoded per item and role across files, raw-deflate, base64."""
    meta = (folder / "meta.txt").read_text()
    names = meta.split("NAMES\n")[1].split("\nDATES")[0].split("~")
    files = [blk.split() for blk in meta.split("DATES\n")[1].split("\nCHECKSUM")[0].split(" / ")]
    checksum = int(meta.split("CHECKSUM\n")[1].split()[0])
    raw = zlib.decompress(base64.b64decode("".join((folder / "payload.txt").read_text().split())), -15)

    vals, i = [], 0
    while i < len(raw):
        z = s = 0
        while True:
            b = raw[i]; i += 1
            z |= (b & 127) << s; s += 7
            if b < 128:
                break
        vals.append((z >> 1) ^ -(z & 1))
    n_files, k, total, recs = len(files), 0, 0, []
    for name in names:
        item, unit = name.split("|")
        for slot, role in enumerate(ROLES):
            prev = 0
            for f in range(n_files):
                v = prev + vals[k]; k += 1; prev = v; total += v
                if v >= 0:   # -1 = item not in that file
                    recs.append({"week_ending": pd.to_datetime(files[f][slot], format="%d-%m-%Y"),
                                 "item": item.strip(), "unit": unit.strip(), "price_avg": v / 100,
                                 "source_file": f"SPI Report {files[f][0]} (extract)", "role": role})
    assert total == checksum, "extract checksum mismatch: the payload is damaged"
    return pd.DataFrame(recs)


def main():
    parts = []
    files = sorted(RAW.glob("*.xlsx"))
    if files:
        parts.append(pd.concat([parse_report(f) for f in files], ignore_index=True))
    if (EXTRACT / "payload.txt").exists():
        parts.append(parse_extract(EXTRACT))
    raw = pd.concat(parts, ignore_index=True)
    raw["item"] = raw["item"].replace(ITEM_FIX)

    # Every copy of the same item-week should carry the same price.
    spread = raw.groupby(["week_ending", "item"]).price_avg.agg(["min", "max", "count"])
    multi = spread[spread["count"] > 1]
    bad = multi[(multi["max"] - multi["min"]) > 0.01]
    print(f"item-weeks reported more than once: {len(multi)}; disagreeing by > Rs 0.01: {len(bad)}")
    if len(bad):
        print(bad.head(10).to_string())

    order = {r: i for i, r in enumerate(ROLES)}
    df = (raw.assign(rank=raw.role.map(order))
             .sort_values(["week_ending", "item", "rank"])
             .drop_duplicates(["week_ending", "item"])
             .drop(columns="rank"))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    wk = sorted(df.week_ending.unique())
    gaps = [(a, b) for a, b in zip(wk, wk[1:]) if (b - a).days > 8]
    print(f"rows kept: {len(df)} | items: {df.item.nunique()} | weeks: {len(wk)} "
          f"({pd.Timestamp(wk[0]).date()} to {pd.Timestamp(wk[-1]).date()})")
    print("gaps longer than 8 days:",
          [f"{pd.Timestamp(a).date()}->{pd.Timestamp(b).date()}" for a, b in gaps] or "none")
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
