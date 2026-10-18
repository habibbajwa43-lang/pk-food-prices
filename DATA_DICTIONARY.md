# Data Dictionary

Source for both tables: Pakistan Bureau of Statistics (PBS), Weekly Sensitive Price
Indicator (SPI), https://www.pbs.gov.pk/price-statistics/ . Prices are retail prices
collected by PBS from 50 markets in 17 cities.

## data/clean/spi_national_weekly.csv  (built by src/parse_reports.py)
One row = one item in one week, national average across the 17 SPI cities.

| Column | Type | Unit | Definition | Caveats |
|---|---|---|---|---|
| week_ending | date | — | Date the SPI week ends (normally a Thursday) | 2025-08-13 is a Wednesday |
| item | text | — | PBS item description | Gas item appears under two names (see CLEANING.md) |
| unit | text | — | Quantity the price refers to (1 Kg, Each, 20 Kg, 1 Dozen…) | 14 different units, so prices of different items are not comparable in Rs |
| price_avg | float | Rs per unit | PBS national average price | Averaging method across cities is PBS's; not recomputed by us |
| source_file | text | — | Report file the value was read from | — |
| role | text | — | Where in the report the value came from: current, previous or year_ago week | year_ago values only exist for weeks a year before a downloaded report |

## data/clean/spi_weekly_long.csv  (built by src/clean.py)
One row = one item in one city in one week.

| Column | Type | Unit | Definition | Caveats |
|---|---|---|---|---|
| week_ending | date | — | Date in the "PRICES ON dd-mm-yyyy" line of Appendix-A | — |
| city_code | int | — | PBS city number, 1–17 | — |
| city | text | — | City name | Urban centres only |
| item_no | int | — | PBS item serial number, 1–51 | Stable across the 6 weeks checked |
| item | text | — | PBS item description | — |
| unit | text | — | Quantity the price refers to | — |
| price_min | float | Rs per unit | Lowest price recorded in that city's markets | 0 in raw file → missing |
| price_avg | float | Rs per unit | Average price across that city's markets | 0 in raw file → missing |
| price_max | float | Rs per unit | Highest price recorded in that city's markets | 0 in raw file → missing |
| source_file | text | — | Annexure file the row came from | — |
| reported | bool | — | False where PBS wrote 0 (item not priced in that city) | 18 rows, all Rice IRRI-6/9 |
