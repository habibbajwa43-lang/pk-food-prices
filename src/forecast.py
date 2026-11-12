"""
forecast.py — forecasting models, rolling-origin backtest, prediction intervals,
price-rise alerts and model explanations for the dashboard.

Input : data/clean/spi_national_weekly.csv  (from src/parse_reports.py)
Output: reports/model_outputs/
    backtest_predictions.csv  one row per item x test week x horizon x model
    metrics_summary.csv       MAE / RMSE / MAPE by scope, horizon and model
    metrics_by_item.csv       the same per item (horizon 1)
    interval_coverage.csv     how often the 80% range contained the real price
    alert_performance.csv     how good the ">5% rise next week" alert was
    forecast_next_weeks.csv   forecasts (with 80% ranges) for the 4 weeks after the last week
    alerts_next_week.csv      chance of a >5% rise next week, per item
    feature_importance.csv    mean |SHAP value| per feature (XGBoost, horizon 1)
    item_predictability.csv   weekly volatility and naive error per item
    seasonality.csv           average weekly price change by calendar month, per item

Run from the project root:   python src/forecast.py

------------------------------------------------------------------------------
Design (read before trusting any number)

* Target: the national average price (Rs per unit) h published weeks ahead,
  h = 1, 2, 3, 4. PBS skipped a few weeks (e.g. around Eid), so "one week ahead"
  means "the next published week"; at most one week is ever skipped.
* Models
    naive           price(t+h) = price(t)
    seasonal_naive  price(t+h) = price in the same week last year
    linear_lags     linear regression, features below, pooled across all items
    xgboost_lags    gradient-boosted trees, same features plus the year-on-year change
  Models 3-4 predict the log change log(price(t+h)/price(t)), so cheap and
  expensive items can share one model; the forecast is price(t) * exp(prediction).
* Features, all known at week t:
    chg_lag1..chg_lag4  the last four weekly log changes
    vol8                standard deviation of the last eight weekly changes
    month_sin, month_cos  calendar month of the target week (seasonality)
    perishable          1 for vegetables, fruit, eggs, chicken, milk, curd
    yoy                 log(price(t) / price a year earlier)   [XGBoost only, may be missing]
* Validation: rolling-origin backtest. For every test week from 1 Jan 2026 on,
  models are trained only on rows whose TARGET week is before the test origin's
  target, i.e. nothing from the future is ever used. Nothing is shuffled.
* 80% prediction ranges: for each item and model, the 10th and 90th percentiles
  of that item's earlier backtest errors (log scale). Coverage is checked only on
  weeks after at least 8 earlier errors exist.
* Rise alert: the chance that next week's price is more than 5% above this
  week's, estimated as the share of (prediction + past error) above +5%.
------------------------------------------------------------------------------
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

IN = Path("data/clean/spi_national_weekly.csv")
OUT = Path("reports/model_outputs")

STAPLES = ["Onions", "Tomatoes", "Potatoes", "Sugar Refined", "Wheat Flour Bag",
           "Eggs Hen (Farm)", "Chicken Farm Broiler (Live)", "Pulse Masoor (Washed)"]
PERISHABLE = ["Onions", "Tomatoes", "Potatoes", "Garlic (Lehsun)", "Bananas (Kela) Local",
              "Eggs Hen (Farm)", "Chicken Farm Broiler (Live)", "Milk fresh (Un-boiled)",
              "Curd (Dahi) Loose"]
HORIZONS = [1, 2, 3, 4]
LIN_FEATS = ["chg_lag1", "chg_lag2", "chg_lag3", "chg_lag4", "vol8",
             "month_sin", "month_cos", "perishable"]
XGB_FEATS = LIN_FEATS + ["yoy"]
MODELS = ["naive", "seasonal_naive", "linear_lags", "xgboost_lags"]
TEST_START = pd.Timestamp("2026-01-01")
RISE = np.log(1.05)


def xgb():
    return XGBRegressor(n_estimators=300, max_depth=3, learning_rate=0.04, subsample=0.8,
                        colsample_bytree=0.9, min_child_weight=5, random_state=42, n_jobs=4)


def lin():
    return make_pipeline(StandardScaler(), LinearRegression())


def last_year_price(df: pd.DataFrame) -> pd.Series:
    """Price of the same item 364 days earlier (within 4 days), else NaN."""
    a = df[["item", "week_ending", "price_avg"]].rename(
        columns={"week_ending": "wk_ly", "price_avg": "p_ly"}).sort_values("wk_ly")
    b = df[["item", "week_ending"]].copy()
    b["key"] = b.week_ending - pd.Timedelta(days=364)
    b["_i"] = np.arange(len(b))
    m = pd.merge_asof(b.sort_values("key"), a, left_on="key", right_on="wk_ly", by="item",
                      direction="nearest", tolerance=pd.Timedelta(days=4))
    return m.sort_values("_i").p_ly.values


def build(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["item", "week_ending"]).reset_index(drop=True)
    g = df.groupby("item")
    df["log_p"] = np.log(df.price_avg)
    df["chg"] = g.log_p.diff()
    for k in range(1, 5):
        df[f"chg_lag{k}"] = df.groupby("item").chg.shift(k - 1)       # lag1 = change ending at t
    df["vol8"] = df.groupby("item").chg.transform(lambda s: s.rolling(8, min_periods=4).std())
    df["p_ly"] = last_year_price(df)
    df["yoy"] = np.log(df.price_avg / df.p_ly)
    df["perishable"] = df.item.isin(PERISHABLE).astype(int)
    rows = []
    for h in HORIZONS:
        d = df.copy()
        d["h"] = h
        d["target_week"] = df.groupby("item").week_ending.shift(-h)
        d["target_price"] = df.groupby("item").price_avg.shift(-h)
        d["target_p_ly"] = df.groupby("item").p_ly.shift(-h)
        d["y"] = np.log(d.target_price / d.price_avg)
        m = d.target_week.dt.month.fillna(d.week_ending.dt.month)
        d["month_sin"], d["month_cos"] = np.sin(2 * np.pi * m / 12), np.cos(2 * np.pi * m / 12)
        rows.append(d)
    return pd.concat(rows, ignore_index=True)


def backtest(data: pd.DataFrame) -> pd.DataFrame:
    usable = data.dropna(subset=LIN_FEATS + ["y"])
    out = []
    for h in HORIZONS:
        u = usable[usable.h == h]
        origins = sorted(u[u.target_week >= TEST_START].week_ending.unique())
        for t in origins:
            test = u[u.week_ending == t]
            target_wk = test.target_week.min()
            train = u[u.target_week < target_wk]           # only targets already observed
            lm = lin().fit(train[LIN_FEATS], train.y)
            xm = xgb().fit(train[XGB_FEATS], train.y)
            preds = {"naive": test.price_avg.values,
                     "seasonal_naive": test.target_p_ly.values,
                     "linear_lags": test.price_avg.values * np.exp(lm.predict(test[LIN_FEATS])),
                     "xgboost_lags": test.price_avg.values * np.exp(xm.predict(test[XGB_FEATS]))}
            for mname, p in preds.items():
                o = test[["item", "unit", "week_ending", "target_week", "price_avg", "target_price"]].copy()
                o["h"], o["model"], o["predicted"], o["train_rows"] = h, mname, p, len(train)
                out.append(o)
    res = pd.concat(out, ignore_index=True).rename(
        columns={"week_ending": "origin_week", "price_avg": "origin_price", "target_price": "actual"})
    res["error"] = res.predicted - res.actual
    res["log_err"] = np.log(res.actual / res.predicted)
    return res


def score(res: pd.DataFrame, by) -> pd.DataFrame:
    def f(d):
        d = d.dropna(subset=["error"])
        return pd.Series({"MAE": d.error.abs().mean(), "RMSE": np.sqrt((d.error ** 2).mean()),
                          "MAPE_%": (d.error.abs() / d.actual).mean() * 100, "n": len(d)})
    return res.groupby(by).apply(f, include_groups=False).reset_index()


def add_intervals(res: pd.DataFrame) -> pd.DataFrame:
    """80% range from each item's EARLIER errors only (expanding window)."""
    # An earlier error may only be used if its target week had already been
    # observed at the forecast origin (target_week <= origin_week).
    res = res.sort_values(["model", "h", "item", "target_week"]).copy()
    lo, hi, p_rise = [], [], []
    for _, g in res.groupby(["model", "h", "item"], sort=False):
        e, tw = g.log_err.values, g.target_week.values
        pred_chg = np.log(g.predicted / g.origin_price).values
        for o, pc in zip(g.origin_week.values, pred_chg):
            past = e[(tw <= o) & ~np.isnan(e)]
            if len(past) >= 8:
                lo.append(np.quantile(past, 0.10)); hi.append(np.quantile(past, 0.90))
                p_rise.append(np.mean(pc + past > RISE))
            else:
                lo.append(np.nan); hi.append(np.nan); p_rise.append(np.nan)
    res["lo"] = res.predicted * np.exp(np.array(lo))
    res["hi"] = res.predicted * np.exp(np.array(hi))
    res["inside"] = np.where(res.lo.notna(), (res.actual >= res.lo) & (res.actual <= res.hi), np.nan)
    res["p_rise5"] = p_rise
    res["rose5"] = np.log(res.actual / res.origin_price) > RISE
    return res


def fit_final(data: pd.DataFrame, h: int):
    u = data[(data.h == h)].dropna(subset=LIN_FEATS + ["y"])
    return lin().fit(u[LIN_FEATS], u.y), xgb().fit(u[XGB_FEATS], u.y), u


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    nat = pd.read_csv(IN, parse_dates=["week_ending"])
    data = build(nat)

    res = add_intervals(backtest(data))
    res.to_csv(OUT / "backtest_predictions.csv", index=False)

    scopes = [res[res.item.isin(STAPLES)].assign(scope="8 staples"),
              res.assign(scope=f"all {res.item.nunique()} items")]
    summary = pd.concat([score(s, ["scope", "h", "model"]) for s in scopes], ignore_index=True)
    base = summary[summary.model == "naive"].set_index(["scope", "h"]).MAE
    summary["MAE_vs_naive_%"] = (summary.MAE / [base[(s, h)] for s, h in
                                 zip(summary.scope, summary.h)] - 1) * 100
    summary.to_csv(OUT / "metrics_summary.csv", index=False)
    score(res[res.h == 1], ["item", "model"]).to_csv(OUT / "metrics_by_item.csv", index=False)

    cov = (res.dropna(subset=["inside"]).groupby(["model", "h"]).inside.mean() * 100).rename(
        "coverage_%").reset_index()
    cov.to_csv(OUT / "interval_coverage.csv", index=False)

    al = res[(res.h == 1) & res.p_rise5.notna()].copy()
    rows = []
    for m, g in al.groupby("model"):
        flag = g.p_rise5 >= 0.5
        tp = (flag & g.rose5).sum()
        rows.append({"model": m, "alerts": int(flag.sum()), "actual_rises": int(g.rose5.sum()),
                     "correct_alerts": int(tp),
                     "precision_%": 100 * tp / flag.sum() if flag.sum() else np.nan,
                     "recall_%": 100 * tp / g.rose5.sum() if g.rose5.sum() else np.nan})
    pd.DataFrame(rows).to_csv(OUT / "alert_performance.csv", index=False)

    # ---- Forecasts for the weeks after the last observed week
    last_wk = nat.week_ending.max()
    fc_rows, alerts = [], []
    for h in HORIZONS:
        lm, xm, train = fit_final(data, h)
        x = data[(data.h == h) & (data.week_ending == last_wk)].dropna(subset=LIN_FEATS).copy()
        tw = last_wk + pd.Timedelta(days=7 * h)
        ly = nat[(nat.week_ending - (tw - pd.Timedelta(days=364))).abs() <= pd.Timedelta(days=4)]
        ly = ly.set_index("item").price_avg
        preds = {"naive": x.price_avg.values,
                 "seasonal_naive": x.item.map(ly).values,
                 "linear_lags": x.price_avg.values * np.exp(lm.predict(x[LIN_FEATS])),
                 "xgboost_lags": x.price_avg.values * np.exp(xm.predict(x[XGB_FEATS]))}
        for m, p in preds.items():
            errs = res[(res.model == m) & (res.h == h)].groupby("item").log_err
            q10, q90 = errs.quantile(0.10), errs.quantile(0.90)
            o = x[["item", "unit", "price_avg"]].rename(columns={"price_avg": "last_price"}).copy()
            o["last_week"], o["h"], o["forecast_week"], o["model"] = last_wk.date(), h, tw.date(), m
            o["forecast"] = p
            o["lo80"] = p * np.exp(o.item.map(q10).values)
            o["hi80"] = p * np.exp(o.item.map(q90).values)
            fc_rows.append(o)
            if h == 1:
                e_by_item = res[(res.model == m) & (res.h == 1)].dropna(subset=["log_err"]).groupby("item").log_err.apply(np.array)
                pc = np.log(p / x.price_avg.values)
                pr = [np.mean(c + e_by_item.get(it, np.array([0.0])) > RISE) for it, c in zip(x.item, pc)]
                alerts.append(pd.DataFrame({"item": x.item.values, "model": m, "p_rise5_%": np.array(pr) * 100}))
        if h == 1:   # SHAP-style contributions from XGBoost's built-in TreeSHAP
            import xgboost as xg
            contrib = xm.get_booster().predict(xg.DMatrix(train[XGB_FEATS]), pred_contribs=True)
            imp = pd.DataFrame({"feature": XGB_FEATS,
                                "mean_abs_shap": np.abs(contrib[:, :-1]).mean(axis=0)})
            imp.sort_values("mean_abs_shap", ascending=False).to_csv(OUT / "feature_importance.csv", index=False)
            lin_coef = pd.Series(lm[-1].coef_, index=LIN_FEATS)
    fc = pd.concat(fc_rows, ignore_index=True)
    fc.to_csv(OUT / "forecast_next_weeks.csv", index=False)
    pd.concat(alerts).to_csv(OUT / "alerts_next_week.csv", index=False)

    # ---- Predictability and seasonality
    d1 = data[data.h == 1]
    pred = d1.groupby("item").agg(unit=("unit", "first"), weekly_change_sd_pct=("chg", lambda s: s.std() * 100))
    pred = pred.join(score(res[(res.h == 1) & (res.model == "naive")], ["item"]).set_index("item")[["MAPE_%"]]
                     .rename(columns={"MAPE_%": "naive_MAPE_%"}))
    pred.sort_values("weekly_change_sd_pct", ascending=False).reset_index().to_csv(OUT / "item_predictability.csv", index=False)
    season = (d1.dropna(subset=["chg"]).assign(month=d1.week_ending.dt.month)
                .groupby(["item", "month"]).chg.mean().mul(100).rename("avg_weekly_change_pct").reset_index())
    season.to_csv(OUT / "seasonality.csv", index=False)

    # ---- Console summary
    t1 = res[res.h == 1]
    print(f"weeks: {nat.week_ending.nunique()} ({nat.week_ending.min().date()} to {last_wk.date()}) | items: {nat.item.nunique()}")
    print(f"test origins (h=1): {t1.origin_week.nunique()} | forecasts per model (h=1): {len(t1[t1.model=='naive'])}")
    print(f"training rows: first fold {res.train_rows.min()}, last fold {res.train_rows.max()}")
    print("\nSummary (lower is better):")
    print(summary.round(2).to_string(index=False))
    print("\nStaples, MAE (h=1):")
    print(score(t1[t1.item.isin(STAPLES)], ["item", "model"]).pivot(index="item", columns="model", values="MAE")[MODELS].round(2).to_string())
    print("\n80% range coverage (target 80%):")
    print(cov.round(1).to_string(index=False))
    print("\nRise alert performance (h=1, alert when chance >= 50%):")
    print(pd.DataFrame(rows).round(1).to_string(index=False))
    print("\nXGBoost mean |SHAP|:")
    print(imp.sort_values("mean_abs_shap", ascending=False).round(4).to_string(index=False))
    print("\nLinear coefficients (standardised):")
    print(lin_coef.round(4).to_string())
    print(f"\nsaved outputs to {OUT}")


if __name__ == "__main__":
    main()
