# Pakistan Food Price Forecasting (PBS Weekly SPI)

Problem Solving with Data Science · ITU · Fall 2026

## Question
How accurately can simple models using past weekly prices forecast selected
essential food prices in Pakistan 1–4 weeks ahead, compared with a naive baseline?

## Data
Pakistan Bureau of Statistics (PBS), Sensitive Price Indicator (SPI):
https://www.pbs.gov.pk/price-statistics/
Files were downloaded by hand from the archive table on 2026-10-18 (see `reports/ACQUISITION.md`). Running `src/fetch_data.py` also writes `data/raw/acquisition_log.csv` with URLs, dates and file hashes.

## Reproduce
```
pip install -r requirements.txt
python src/fetch_data.py      # downloads raw files into data/raw/
python src/clean.py           # weekly Annexure files -> data/clean/spi_weekly_long.csv
python src/parse_reports.py   # weekly Report files  -> data/clean/spi_national_weekly.csv
python src/checks.py > reports/checks_output.txt   # six-things check
python src/eda_charts.py      # charts -> reports/figures/
python src/confounder_check.py  # big-city vs other-city check by item type
```

## Repository layout
- `data/raw/` untouched downloads (never edited by hand)
- `data/clean/` output of the cleaning script
- `src/` fetch and cleaning scripts
- `notebooks/` EDA
- `reports/` 1_proposal_v2, ACQUISITION (item 2), 3_five_questions, 5_eda_notes, 6_journal, 7_limitations, predictions, checks_output, figures/
- `CLEANING.md`, `DATA_DICTIONARY.md`, `CONTRIBUTIONS.md`, `AI_USE_LOG.md`
