# Cleaning Log

Numbers referenced below come from `reports/checks_output.txt` (produced by `src/checks.py`).

## Entries

**1. Zero prices for Rice IRRI-6/9.**
I noticed that 18 prices were recorded as 0, all for Rice IRRI-6/9 in Gujranwala, Lahore, and Sialkot across all six weeks.
I corrected 18 rows (54 cells: min, avg and max) by converting the zero prices to missing values, because Rs 0 is not a realistic recorded market price for rice. I did not fill these values with averages from other cities because PBS did not record the actual prices, and imputing estimates could introduce misleading data.
I did not delete the rows because keeping them preserves the dataset structure and makes it possible to track how much data is missing; instead, I marked each affected row with `reported = False`.

**2. Two labels for the gas item (no change).**
I would keep the gas labels separate because gas is outside my main food-price forecasting scope, and I want to preserve the original source labels rather than change the data unnecessarily. The evidence suggests both labels refer to the same item: they have the same unit (MMBTU), price (Rs 2,566.5), and week, but different names in separate report files. This creates 2 duplicate rows, contributing to the total of 971 rows instead of 969; I would document this issue without merging them.

**3. Week ending on a Wednesday (no change).**
I noticed that 18 of the 19 national weeks end on Thursday, but 2025-08-13 ends on Wednesday; this date comes from the "year_ago" column in the 13 August 2026 report, and the timing may be related to the likely Independence Day holiday on 14 August 2025.
I did not change the date to Thursday, 14 August 2025, because the six-day interval is unlikely to have a major impact on the overall forecasting analysis, and we cannot confirm exactly when the prices were collected.
I would revisit this date if the one-day difference affects weekly alignment or forecasting results, and verify it against the original PBS report if possible.

**4. The same item-week reported in two files.**
I found 406 item-weeks reported in two files, once as the "current" week and once as the "previous" week. Comparing the values showed 0 disagreements greater than Rs 0.01, so I kept one row per item-week and prioritised the "current" value, although both values were identical in this dataset.
I did not keep both rows because that would double-count the same item-week and could distort the charts and forecasting model. Keeping the "current" record also provides a consistent rule if PBS revises earlier values in future data.

**5. Wide report-style Excel layout.**
I found that the PBS Excel annexures use a wide, report-style layout, with cities arranged in three column groups, each city having MIN, AVG and MAX columns, and items listed in rows. I converted the six files into long format, producing 5,202 rows (6 × 17 × 51), where each row represents one item, one city and one week; this format makes it easier to filter, compare cities and weeks, and prepare data for charts and forecasting.
I did not manually copy and paste data or edit the original Excel files because code-based processing is more consistent, reproducible and less likely to introduce manual errors.

## Six-things check

**1. Missing values.**
The city table contains 18 rows with missing prices for Rice IRRI-6/9 in Gujranwala, Lahore and Sialkot across six weeks. The national table has no missing prices, but I checked the gaps between consecutive weeks and found a 301-day gap.

**2. Duplicates.**
The duplicate check found zero exact duplicate rows, but two hidden duplicate rows exist because the same gas item-week was recorded under different names. I checked for duplicates using the item, city and week combination with `duplicated()`.

**3. Wrong data types and values.**
All price columns contain numeric values, no rows have negative prices, and no rows violate the expected order `min ≤ avg ≤ max`. I checked the column data types (`dtypes`) and tested the minimum, average and maximum price relationships.

**4. Wrong units.**
The check found 14 distinct units across the items, with `1 Kg` being the most common unit (17 items). I checked the number of unique units for each item using `unit.nunique()` and found that zero items changed units across weeks or cities in the city table (6 weeks).

**5. Encoding.**
No unusual non-ASCII characters were found, and all 17 city names were cleanly encoded. I checked the text using a regular expression to detect non-ASCII characters and reviewed the city names in the `ENCODING` section.

**6. Drift.**
I found two data consistency issues: the gas item has different labels in different report files, and one national week ends on Wednesday (13 August 2025) instead of Thursday. I checked how many weeks each item appeared in and examined the weekday of each `week_ending` date.
