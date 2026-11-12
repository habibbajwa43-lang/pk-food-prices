# AI Use Log

**2026-10-18.** Used Claude to check which PBS price datasets exist and their
frequency/coverage (confirmed on pbs.gov.pk/price-statistics), and to set up the
repository structure and the fetch script (src/fetch_data.py). We read and
tested the script ourselves.

**2026-10-18.** Used Claude to write the parsing scripts (src/clean.py, src/parse_reports.py),
the six-things check script (src/checks.py), draft chart code (src/eda_charts.py) and a
draft data dictionary. We ran every script ourselves, checked the outputs against the
original Excel files, and rewrote all chart titles.

**2026-11-11.** Used Claude to draft the 5-slide project presentation and speaker notes,
based on our proposal and Assignment 1 outputs.

**2026-11-12.** Used Claude to:
- read all 52 SPI Report Excel files listed in the PBS archive through our own web browser
  (the PBS site blocks downloads from Claude's environment) and bring their price tables into the
  project as `data/raw/pbs_report_extract/`; the transfer was checked with a checksum and against
  the 9 Report files we had downloaded by hand (see that folder's README);
- update `src/parse_reports.py` to combine both sources and merge the gas labels;
- write the forecasting script (`src/forecast.py`: features, naive, seasonal naive, linear
  regression and XGBoost, rolling-origin backtest at 1–4 weeks, 80% ranges, rise alerts, SHAP),
  the results charts (`src/results_charts.py`), the Streamlit dashboard (`app.py`), the tests,
  the results summary (`reports/8_model_results.md`) and CLEANING.md entries 6–10.
The tables in the results summary are copied from the script outputs.
[What we checked ourselves: write here, e.g. re-ran the pipeline, compared a few prices with the
PBS Excel files on the website, opened every dashboard tab, read the results summary.]
