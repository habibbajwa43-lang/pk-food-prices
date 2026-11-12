# Pakistan Food Price Forecasting (PBS Weekly SPI)

Problem Solving with Data Science · ITU · Fall 2026
Laiba Amir (BSEDS-23057) · Habib Javaid Bajwa (BSEDS-23066)

## Question
Can historical weekly prices predict the price of essential items in urban Pakistan
1–4 weeks ahead, and does any model beat the simple guess that next week's price will be
the same as this week's?

**Stakeholder:** a household planning its food budget (also policymakers and
consumer-protection groups watching prices).

## Data
Pakistan Bureau of Statistics (PBS), Weekly Sensitive Price Indicator (SPI):
https://www.pbs.gov.pk/price-statistics/ (51 items, 50 markets, 17 cities).
- **National prices:** all 52 SPI Report Excel files in PBS's archive (weeks ending
  23-10-2025 to 05-11-2026) plus their "same week last year" column → **102 weeks,
  24-10-2024 to 05-11-2026**. See `data/raw/pbs_report_extract/README.md` and `reports/ACQUISITION.md`.
- **City prices:** 6 weekly Annexure files (10-09-2026 to 15-10-2026).
Raw files are kept unchanged in `data/raw/`.

## Results in one paragraph
On a rolling-origin backtest over 43 weeks of 2026, the naive forecast ("same as last week")
had the lowest error across all 51 items at every horizon. For the 8 staple foods, linear
regression on recent price changes had 2.6% (1 week ahead) to 6.3% (4 weeks ahead) lower
rupee error, mostly thanks to wheat flour; XGBoost and "same week last year" did worse.
Only the naive model's 80% price ranges were close to honest, and sudden >5% rises were
mostly not predictable. Details: `reports/8_model_results.md`.

## Dashboard
`app.py` (Streamlit): overview and price-rise watch, two-year price history, 4-week forecasts
with 80% ranges, backtest evaluation by horizon, insights (volatility, month pattern, SHAP),
city comparison, and an About page. Forecasts are always labelled as forecasts.

## Reproduce
```
pip install -r requirements.txt
python src/clean.py              # Annexure files -> data/clean/spi_weekly_long.csv
python src/parse_reports.py      # Report files + extract -> data/clean/spi_national_weekly.csv
python src/checks.py > reports/checks_output_v2.txt   # six-things check on the full data
python src/eda_charts.py         # Assignment 1 EDA charts (pinned to the original 19 weeks)
python src/confounder_check.py
python src/forecast.py           # models, backtest, ranges, alerts -> reports/model_outputs/
python src/results_charts.py     # results charts -> reports/figures/results_*.png
python -m pytest -q              # 7 sanity tests
streamlit run app.py             # dashboard at http://localhost:8501
```
(`reports/checks_output.txt` is the Assignment 1 version; it is not overwritten.)

## Deploy the dashboard (Streamlit Community Cloud, free)
1. Push this repository to GitHub (cleaned CSVs and `reports/model_outputs/` included).
2. Go to https://share.streamlit.io, sign in with GitHub, click **Create app**.
3. Choose this repository, branch `main`, main file `app.py`, and click **Deploy**.

## Repository layout
- `data/raw/` untouched PBS downloads and the Report extract (never edited by hand)
- `data/clean/` output of the cleaning scripts
- `src/` cleaning, checks, EDA, forecasting and chart scripts
- `app.py` Streamlit dashboard · `tests/` sanity tests
- `reports/` proposal v2, acquisition record, five questions, EDA notes, journal,
  limitations, model results, checks outputs, figures, model outputs
- `CLEANING.md`, `DATA_DICTIONARY.md`, `CONTRIBUTIONS.md`, `AI_USE_LOG.md`
