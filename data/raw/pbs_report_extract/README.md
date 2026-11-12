# PBS SPI Report extract (52 weeks)

**What this is.** The price table ("Page 2") of all 52 *SPI Report (Excel)* files listed
in the PBS Weekly SPI archive on 12 November 2026, weeks ending **23-10-2025 to
05-11-2026**. Each file gives, for every one of the 51 SPI items, the national average
price for that week, the previous week and the same week a year earlier, so the
extract covers prices from **24-10-2024 to 05-11-2026**.

Archive page: https://www.pbs.gov.pk/price-statistics/ (tab "Weekly Sensitive Price Index (SPI)").
File links follow the pattern
`https://www.pbs.gov.pk/wp-content/uploads/2020/07/SPI-Report-<dd.mm.yyyy>.xlsx`
(some files are named `3.-SPI-Report-…` or `SPI-Executive-Summary-SPI-Report_-…`).
The link for the week ending 30-04-2026 returned a web page instead of an Excel file;
that week's prices are recovered from the "previous week" column of the 07-05-2026 report.

**Why an extract and not the .xlsx files.** The PBS website does not allow downloads
from the environment where this project's code ran. The files were opened in a normal
web browser, and the "Page 2" sheet of each was read there with the SheetJS library.
Only the item name, unit and the three prices of each item row, plus the three dates
in the sheet's first two lines, were kept. The original .xlsx files are not stored here;
anyone can re-download them from the links above.

**Format** (decoded by `src/parse_reports.py`, function `parse_extract`):
- `meta.txt` → `NAMES`: item|unit list; `DATES`: per file, "current previous year_ago"
  dates, files separated by " / "; `CHECKSUM`: sum of all stored values.
- `payload.txt` → base64 of raw-deflate of zigzag-varint integers: prices in paisa
  (Rs × 100, so no rounding beyond 2 decimals), delta-encoded per item and column across
  files; −1 means the item was not in that file.

**How it was checked.**
1. The checksum of the decoded values equals the checksum computed in the browser (531,065,760).
2. 3,060 item-weeks appear in more than one source (current vs previous column, current vs
   year-ago column, and the 9 Report .xlsx files downloaded by hand in `data/raw/reports/`).
   All agree to the paisa except one: Electricity Charges for Q1, week ending 20-11-2025
   (Rs 4.83 vs Rs 5.40) — see CLEANING.md entry 8.
