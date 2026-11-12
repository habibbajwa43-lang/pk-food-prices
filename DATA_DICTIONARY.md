# Data Dictionary

Source for both tables: Pakistan Bureau of Statistics (PBS), Weekly Sensitive Price
Indicator (SPI), https://www.pbs.gov.pk/price-statistics/ . Prices are retail prices
collected by PBS from 50 markets in 17 cities.

## data/clean/spi_national_weekly.csv  (built by src/parse_reports.py)
One row = one item in one week, national average across the 17 SPI cities.
5,202 rows: 51 items × 102 weeks, 24-10-2024 to 05-11-2026.

| Column | Type | Unit | Definition | Caveats |
|---|---|---|---|---|
| week_ending | date | — | Date the SPI week ends (normally a Thursday) | 6 of 102 weeks end on a Wednesday; 5 two-week gaps (CLEANING.md entry 9) |
| item | text | — | PBS item description | Gas labels merged into "Gas Charges for Q1" (CLEANING.md entry 7) |
| unit | text | — | Quantity the price refers to (1 Kg, Each, 20 Kg, 1 Dozen…) | 14 different units, so prices of different items are not comparable in Rs |
| price_avg | float | Rs per unit | PBS national average price | Averaging method across cities is PBS's; not recomputed by us |
| source_file | text | — | Report file the value was read from | — |
| role | text | — | Where in the report the value came from: current, previous or year_ago week | Weeks before 23-10-2025 come only from the year_ago column |

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

## reports/model_outputs/  (built by src/forecast.py)

| File | One row = | Key columns |
|---|---|---|
| backtest_predictions.csv | item × forecast origin week × horizon × model | origin_week, target_week, h (weeks ahead), origin_price, actual, predicted, error (Rs), lo/hi (80% range), inside, p_rise5, rose5 |
| metrics_summary.csv | scope × horizon × model | MAE, RMSE (Rs per unit), MAPE_% , MAE_vs_naive_% |
| metrics_by_item.csv | item × model (1 week ahead) | MAE, RMSE, MAPE_% |
| interval_coverage.csv | model × horizon | coverage_% (share of real prices inside the 80% range) |
| alert_performance.csv | model | alerts, actual_rises, correct_alerts, precision_%, recall_% |
| forecast_next_weeks.csv | item × horizon × model | forecast_week, forecast, lo80, hi80 (Rs per unit). Forecasts, not PBS prices |
| alerts_next_week.csv | item × model | p_rise5_% (estimated chance of a >5% rise next week) |
| feature_importance.csv | feature | mean_abs_shap (XGBoost, 1 week ahead) |
| item_predictability.csv | item | weekly_change_sd_pct, naive_MAPE_% |
| seasonality.csv | item × calendar month | avg_weekly_change_pct |
