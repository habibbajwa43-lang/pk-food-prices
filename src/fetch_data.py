"""
fetch_data.py — download raw PBS price files into data/raw/ without changing them.

What it does:
  1. Downloads each file listed in SOURCES from the PBS website.
  2. Saves it to data/raw/ with the download date in the filename,
     so older pulls are never overwritten.
  3. Records the URL, date pulled, file size and SHA-256 hash in
     data/raw/acquisition_log.csv. The hash lets anyone confirm later
     that the raw file was never edited.

Run from the project root:
    python src/fetch_data.py

Note: PBS replaces the "latest week" file links every week. If a URL
stops working, open https://www.pbs.gov.pk/price-statistics/ and copy
the current link into SOURCES.
"""

import csv
import hashlib
from datetime import date
from pathlib import Path

import requests

RAW_DIR = Path("data/raw")
LOG_FILE = RAW_DIR / "acquisition_log.csv"

# name -> URL (links copied from the PBS Price Statistics page on 2026-10-18)
SOURCES = {
    "spi_weekly_annex_2026-10-15": "https://www.pbs.gov.pk/wp-content/uploads/2020/07/Annex_15.10.2026.xlsx",
    "spi_weekly_report_2026-10-15": "https://www.pbs.gov.pk/wp-content/uploads/2020/07/3.-SPI-Report-15.10.2026.xlsx",
    "spi_monthly_avg_prices": "https://www.pbs.gov.pk/wp-content/uploads/2020/07/SPI-Monthly-Prices-Annex-9.xlsx",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def download(name: str, url: str) -> Path:
    today = date.today().isoformat()
    out = RAW_DIR / f"{name}__pulled_{today}.xlsx"
    if out.exists():
        print(f"Already have {out.name}, skipping.")
        return out
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()  # stop loudly if the link is dead
    out.write_bytes(resp.content)
    print(f"Saved {out.name} ({len(resp.content):,} bytes)")
    return out


def log(name: str, url: str, path: Path) -> None:
    new_file = not LOG_FILE.exists()
    with open(LOG_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["name", "url", "date_pulled", "file", "bytes", "sha256"])
        w.writerow([name, url, date.today().isoformat(), path.name,
                    path.stat().st_size, sha256(path)])


if __name__ == "__main__":
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for name, url in SOURCES.items():
        try:
            path = download(name, url)
            log(name, url, path)
        except requests.RequestException as e:
            print(f"FAILED {name}: {e}")
