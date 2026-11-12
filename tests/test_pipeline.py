"""
tests/test_pipeline.py — checks that the cleaned data and the forecasting outputs
are sane. Run from the project root after the pipeline:   python -m pytest -q
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NAT = ROOT / "data/clean/spi_national_weekly.csv"
CITY = ROOT / "data/clean/spi_weekly_long.csv"
OUT = ROOT / "reports/model_outputs"


def test_national_one_row_per_item_week():
    d = pd.read_csv(NAT)
    assert not d.duplicated(["week_ending", "item"]).any()


def test_national_covers_two_years_and_51_items():
    d = pd.read_csv(NAT, parse_dates=["week_ending"])
    assert d.item.nunique() == 51
    assert d.week_ending.nunique() >= 100
    gaps = d.week_ending.drop_duplicates().sort_values().diff().dt.days.dropna()
    assert gaps.max() <= 14          # at most one unpublished week in a row


def test_city_min_avg_max_order():
    d = pd.read_csv(CITY).dropna(subset=["price_min", "price_avg", "price_max"])
    assert (d.price_min <= d.price_avg).all() and (d.price_avg <= d.price_max).all()


def test_no_zero_or_negative_prices_left():
    for path in (NAT, CITY):
        assert (pd.read_csv(path).price_avg.dropna() > 0).all()


def test_backtest_never_trains_on_the_future():
    p = pd.read_csv(OUT / "backtest_predictions.csv", parse_dates=["origin_week", "target_week"])
    assert (p.target_week > p.origin_week).all()
    for h, g in p.groupby("h"):
        folds = g.groupby("target_week").train_rows.first().sort_index()
        assert folds.is_monotonic_increasing      # expanding window, time order kept


def test_naive_prediction_equals_origin_price():
    p = pd.read_csv(OUT / "backtest_predictions.csv")
    n = p[p.model == "naive"]
    assert np.allclose(n.predicted, n.origin_price)


def test_forecasts_are_after_last_observed_week():
    f = pd.read_csv(OUT / "forecast_next_weeks.csv", parse_dates=["forecast_week"])
    last = pd.read_csv(NAT, parse_dates=["week_ending"]).week_ending.max()
    assert (f.forecast_week > last).all()
