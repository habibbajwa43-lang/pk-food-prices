"""
app.py — Streamlit dashboard: Pakistan food price forecasts (PBS weekly SPI).

Run from the project root:
    pip install -r requirements.txt
    streamlit run app.py
(The CSVs it reads are committed. To rebuild them from the raw PBS files, run the
pipeline in README.md.)

Observed PBS prices are always solid dark lines; forecasts are dashed, coloured and
labelled "Forecast", so a forecast is never mistaken for an official price.
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).parent
OUT = ROOT / "reports" / "model_outputs"
RETRIEVED = "12 November 2026"
STAPLES = ["Onions", "Tomatoes", "Potatoes", "Sugar Refined", "Wheat Flour Bag",
           "Eggs Hen (Farm)", "Chicken Farm Broiler (Live)", "Pulse Masoor (Washed)"]
NAME = {"naive": "Naive (same as last week)", "linear_lags": "Linear regression",
        "xgboost_lags": "XGBoost", "seasonal_naive": "Seasonal naive (same week last year)"}
COL = {"naive": "#2a78d6", "linear_lags": "#eb6834", "xgboost_lags": "#1baf7a",
       "seasonal_naive": "#eda100"}
INK = "#14213D"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

st.set_page_config(page_title="Pakistan Food Price Forecasts", page_icon="🧅", layout="wide")


@st.cache_data
def load():
    r = lambda f, **k: pd.read_csv(OUT / f, **k)
    return {
        "nat": pd.read_csv(ROOT / "data/clean/spi_national_weekly.csv", parse_dates=["week_ending"]),
        "city": pd.read_csv(ROOT / "data/clean/spi_weekly_long.csv", parse_dates=["week_ending"]),
        "bt": r("backtest_predictions.csv", parse_dates=["origin_week", "target_week"]),
        "summary": r("metrics_summary.csv"), "by_item": r("metrics_by_item.csv"),
        "cov": r("interval_coverage.csv"), "alert_perf": r("alert_performance.csv"),
        "fc": r("forecast_next_weeks.csv", parse_dates=["forecast_week", "last_week"]),
        "alerts": r("alerts_next_week.csv"), "shap": r("feature_importance.csv"),
        "pred": r("item_predictability.csv"), "season": r("seasonality.csv"),
    }


try:
    D = load()
except FileNotFoundError as e:
    st.error(f"Missing file: {e.filename}. Run the pipeline first (see README.md).")
    st.stop()

nat = D["nat"]
last_wk = nat.week_ending.max()

# ---------------- Sidebar ----------------
st.sidebar.header("Settings")
items = sorted(nat.item.unique())
item = st.sidebar.selectbox("Item", items, index=items.index("Tomatoes"))
unit = nat.loc[nat.item == item, "unit"].iloc[0]
model = st.sidebar.radio("Forecast model", list(NAME)[:3], format_func=NAME.get, index=1,
                         help="Linear regression had the lowest error for the 8 staples; "
                              "the naive model was best across all 51 items.")
st.sidebar.caption(f"Prices are Rs per **{unit}**.")
st.sidebar.divider()
st.sidebar.caption("Source: Pakistan Bureau of Statistics, Weekly Sensitive Price Indicator "
                   f"(SPI), national average of 17 cities. Data to week ending {last_wk.date()}. "
                   f"Retrieved {RETRIEVED}.")

st.title("🧅 Pakistan Food Price Forecasts")
st.write("Can last week’s prices predict next week’s? Two years of official weekly prices "
         "for 51 essential items, four forecasting models, and an honest check of how well they work.")

t_over, t_hist, t_fc, t_eval, t_ins, t_city, t_about = st.tabs(
    ["🏠 Overview", "📈 Price history", "🔮 Forecast", "✅ How good are the models?",
     "💡 Insights", "🏙️ Cities", "ℹ️ About"])

# ---------------- Overview ----------------
with t_over:
    s = D["summary"]
    st1 = s[(s.scope == "8 staples") & (s.h == 1)].set_index("model")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Weeks of data", nat.week_ending.nunique(),
              help=f"{nat.week_ending.min().date()} to {last_wk.date()}")
    c2.metric("Items tracked", nat.item.nunique())
    c3.metric("Lowest rupee error, 8 staples", "Linear reg.",
              f"{st1.loc['linear_lags', 'MAE_vs_naive_%']:+.1f}% error vs naive", delta_color="inverse")
    tom = D["pred"].set_index("item").loc["Tomatoes", "weekly_change_sd_pct"]
    c4.metric("Most unpredictable item", "Tomatoes", f"±{tom:.0f}% in a typical week", delta_color="off")

    st.subheader(f"⚠️ Price-rise watch: week ending {(last_wk + pd.Timedelta(days=7)).date()}")
    apm = D["alert_perf"].set_index("model").loc[model]
    st.caption(f"Chance that the price rises more than 5% next week ({NAME[model]}). "
               f"This is a model estimate, not a PBS figure. In testing, when this model gave a 50%+ chance, "
               f"prices really rose >5% only {apm['precision_%']:.0f}% of the time, and it caught "
               f"{apm['recall_%']:.0f}% of real rises — treat it as a heads-up, not a promise.")
    a = D["alerts"][D["alerts"].model == model].sort_values("p_rise5_%", ascending=False).head(8)
    last = nat[nat.week_ending == last_wk].set_index("item")
    a = a.assign(**{"Latest price (Rs)": a.item.map(last.price_avg).round(2),
                    "Unit": a.item.map(last.unit),
                    "Chance of >5% rise": a["p_rise5_%"].round(0).astype(int).astype(str) + "%"})
    st.dataframe(a[["item", "Unit", "Latest price (Rs)", "Chance of >5% rise"]].rename(columns={"item": "Item"}),
                 hide_index=True, width="stretch")

    st.subheader("Key findings")
    st.markdown(f"""
1. **“Same as last week” is very hard to beat.** Across all 51 items the naive forecast had the lowest error.
2. **For the 8 staples, linear regression wins narrowly in rupees**: {abs(st1.loc['linear_lags', 'MAE_vs_naive_%']):.1f}% lower error one week ahead and
   {abs(s[(s.scope == '8 staples') & (s.model == 'linear_lags') & (s.h == 4)]['MAE_vs_naive_%'].iloc[0]):.1f}% four weeks ahead. Most of that gain comes from wheat flour,
   the most expensive staple; in percent terms (MAPE) the two are level, and naive is still best for onions, tomatoes and chicken.
3. **XGBoost did worse than the simple models**, and “same week last year” was far worse, because prices changed so much between years.
4. **Tomatoes are the hardest item**: a typical weekly move of ±{tom:.0f}%, more than twice any other item.
5. **The naive model’s 80% price ranges are honest** (they held the real price
   {D['cov'].set_index(['model','h']).loc[('naive',1),'coverage_%']:.0f}% of the time); the other models’ ranges were too narrow.
""")

# ---------------- History ----------------
with t_hist:
    h = nat[nat.item == item].sort_values("week_ending")
    fig = go.Figure(go.Scatter(x=h.week_ending, y=h.price_avg, mode="lines", name="Observed PBS price",
                               line=dict(color=INK, width=2.5),
                               hovertemplate="%{x|%d %b %Y}<br>Rs %{y:,.2f}<extra></extra>"))
    fig.update_layout(title=f"{item}: national average price, Rs per {unit}", height=430,
                      yaxis_title=f"Rs per {unit}", hovermode="x unified", margin=dict(t=60))
    st.plotly_chart(fig, width="stretch")
    first, lastp = h.iloc[0], h.iloc[-1]
    hi_row, lo_row = h.loc[h.price_avg.idxmax()], h.loc[h.price_avg.idxmin()]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"First week ({first.week_ending.date()})", f"Rs {first.price_avg:,.2f}")
    c2.metric(f"Latest ({lastp.week_ending.date()})", f"Rs {lastp.price_avg:,.2f}",
              f"{(lastp.price_avg / first.price_avg - 1) * 100:+.1f}% over the period", delta_color="off")
    c3.metric("Highest", f"Rs {hi_row.price_avg:,.2f}", str(hi_row.week_ending.date()), delta_color="off")
    c4.metric("Lowest", f"Rs {lo_row.price_avg:,.2f}", str(lo_row.week_ending.date()), delta_color="off")
    st.caption("PBS did not publish a report for a few weeks (for example around Eid), "
               "so a handful of points are two weeks apart.")

# ---------------- Forecast ----------------
with t_fc:
    f = D["fc"][(D["fc"].item == item) & (D["fc"].model == model)].sort_values("h")
    st.subheader(f"{item}: forecast for the next 4 weeks ({NAME[model]})")
    cv = D["cov"].set_index(["model", "h"])["coverage_%"]
    st.warning(f"These are **model forecasts**, not prices published by PBS. The shaded band is meant to be an "
               f"80% range. In testing, this model’s range held the real price **{cv[(model, 1)]:.0f}%** of the time "
               f"one week ahead and **{cv[(model, 4)]:.0f}%** four weeks ahead"
               + (" — so treat it as narrower than it should be." if cv[(model, 1)] < 75 else "."))
    recent = nat[(nat.item == item) & (nat.week_ending >= last_wk - pd.Timedelta(days=26 * 7))].sort_values("week_ending")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=recent.week_ending, y=recent.price_avg, name="Observed PBS price",
                             mode="lines+markers", line=dict(color=INK, width=2.5), marker=dict(size=5)))
    xs = [last_wk] + list(f.forecast_week)
    p0 = recent.price_avg.iloc[-1]
    fig.add_trace(go.Scatter(x=xs + xs[::-1], y=[p0] + list(f.hi80) + list(f.lo80)[::-1] + [p0],
                             fill="toself", fillcolor="rgba(235,104,52,0.15)", line=dict(width=0),
                             mode="lines", name="80% range", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=xs, y=[p0] + list(f.forecast), name=f"Forecast: {NAME[model]}",
                             mode="lines+markers", line=dict(color=COL[model], width=2.5, dash="dash"),
                             marker=dict(size=8)))
    fig.update_layout(height=440, yaxis_title=f"Rs per {unit}", hovermode="x unified", margin=dict(t=30))
    st.plotly_chart(fig, width="stretch")
    tbl = f.assign(**{"Week ending": f.forecast_week.dt.date, "Weeks ahead": f.h,
                      "Forecast (Rs)": f.forecast.round(2),
                      "80% range (Rs)": f.lo80.round(1).astype(str) + " – " + f.hi80.round(1).astype(str),
                      "Change vs latest": ((f.forecast / f.last_price - 1) * 100).round(1).astype(str) + "%"})
    st.dataframe(tbl[["Week ending", "Weeks ahead", "Forecast (Rs)", "80% range (Rs)", "Change vs latest"]],
                 hide_index=True, width="stretch")

# ---------------- Evaluation ----------------
with t_eval:
    st.subheader("How each model did on weeks it had never seen")
    st.write("**Rolling-origin backtest.** For each of 43 test weeks (January–November 2026), the models "
             "were trained only on earlier weeks and then asked to forecast ahead. Nothing was shuffled.")
    hz = st.select_slider("Forecast horizon", options=[1, 2, 3, 4], value=1,
                          format_func=lambda x: f"{x} week{'s' if x > 1 else ''} ahead")
    b = D["bt"][(D["bt"].item == item) & (D["bt"].h == hz)]
    fig = go.Figure()
    act = b[b.model == "naive"].sort_values("target_week")
    fig.add_trace(go.Scatter(x=act.target_week, y=act.actual, name="Actual PBS price", mode="lines+markers",
                             line=dict(color=INK, width=3)))
    for m in ["naive", "linear_lags", "xgboost_lags", "seasonal_naive"]:
        pm = b[b.model == m].sort_values("target_week")
        fig.add_trace(go.Scatter(x=pm.target_week, y=pm.predicted, name=f"Forecast: {NAME[m]}",
                                 mode="lines", line=dict(color=COL[m], dash="dash", width=2),
                                 visible=True if m in ("naive", model) else "legendonly"))
    fig.update_layout(title=f"{item}: actual price vs forecasts, {hz} week(s) ahead", height=430,
                      yaxis_title=f"Rs per {unit}", hovermode="x unified")
    st.plotly_chart(fig, width="stretch")
    st.caption("Click a model in the legend to show or hide it.")

    m_item = D["bt"][(D["bt"].item == item) & (D["bt"].h == hz)].dropna(subset=["error"])
    tab = m_item.groupby("model").apply(lambda d: pd.Series({
        "MAE (Rs)": d.error.abs().mean(), "RMSE (Rs)": (d.error ** 2).mean() ** 0.5,
        "MAPE (%)": (d.error.abs() / d.actual).mean() * 100}), include_groups=False).round(2)
    tab.index = tab.index.map(NAME)
    st.markdown(f"**{item}**, {hz} week(s) ahead. Lowest MAE: **{tab['MAE (Rs)'].idxmin()}**.")
    st.dataframe(tab.sort_values("MAE (Rs)"), width="stretch")

    st.divider()
    st.markdown("**All items: how much higher (+) or lower (−) each model’s error is than the naive forecast**")
    s = D["summary"][D["summary"].model != "naive"].copy()
    s["model"] = s.model.map(NAME)
    piv = s.pivot_table(index=["scope", "model"], columns="h", values="MAE_vs_naive_%").round(1)
    piv.columns = [f"{c} wk ahead" for c in piv.columns]
    st.dataframe(piv.astype(str) + "%", width="stretch")
    c1, c2 = st.columns(2)
    with c1:
        cov = D["cov"][D["cov"].model != "seasonal_naive"]
        fig = go.Figure([go.Bar(x=[f"{h} wk" for h in g.h], y=g["coverage_%"], name=NAME[m], marker_color=COL[m])
                         for m, g in cov.groupby("model")])
        fig.add_hline(y=80, line_dash="dash", annotation_text="target 80%")
        fig.update_layout(title="Did the 80% range hold the real price?", yaxis_title="% of weeks",
                          barmode="group", height=360, yaxis_range=[0, 100])
        st.plotly_chart(fig, width="stretch")
    with c2:
        ap = D["alert_perf"].copy()
        ap["model"] = ap.model.map(NAME)
        st.markdown("**>5% rise alerts (1 week ahead)**")
        st.dataframe(ap.rename(columns={"alerts": "Alerts raised", "actual_rises": "Real >5% rises",
                                        "correct_alerts": "Correct alerts", "precision_%": "Right when raised (%)",
                                        "recall_%": "Rises caught (%)"}).round(1),
                     hide_index=True, width="stretch")
        st.caption("Sudden jumps are the hardest thing to predict from past prices alone.")
    st.markdown("""
**Metrics.** **MAE** (Mean Absolute Error) is the average miss in rupees, our main score.
**RMSE** (Root Mean Squared Error) punishes big misses more. **MAPE** (Mean Absolute Percentage Error)
is the average miss in percent, so cheap and expensive items can be compared.
""")

# ---------------- Insights ----------------
with t_ins:
    c1, c2 = st.columns(2)
    with c1:
        p = D["pred"].head(15).iloc[::-1]
        fig = go.Figure(go.Bar(x=p.weekly_change_sd_pct, y=p.item, orientation="h", marker_color="#2a78d6",
                               text=p.weekly_change_sd_pct.round(1).astype(str) + "%", textposition="outside"))
        fig.update_xaxes(range=[0, p.weekly_change_sd_pct.max() * 1.18])
        fig.update_layout(title="Which prices jump the most? (typical weekly move)", height=520,
                          xaxis_title="Standard deviation of weekly change (%)", margin=dict(l=10))
        st.plotly_chart(fig, width="stretch")
    with c2:
        se = D["season"][D["season"].item == item].set_index("month").reindex(range(1, 13))
        fig = go.Figure(go.Bar(x=MONTHS, y=se.avg_weekly_change_pct,
                               marker_color=["#eb6834" if v > 0 else "#2a78d6" for v in se.avg_weekly_change_pct.fillna(0)],
                               text=se.avg_weekly_change_pct.round(1).astype(str) + "%", textposition="outside"))
        fig.update_layout(title=f"{item}: average weekly price change by month", height=520,
                          yaxis_title="Average weekly change (%)")
        st.plotly_chart(fig, width="stretch")
        st.caption("Orange = prices usually rise that month, blue = usually fall. Based on only two years, "
                   "so treat it as a hint, not a rule.")
    sh = D["shap"].sort_values("mean_abs_shap")
    labels = {"chg_lag1": "Last week’s change", "chg_lag2": "Change 2 weeks ago", "chg_lag3": "Change 3 weeks ago",
              "chg_lag4": "Change 4 weeks ago", "vol8": "Recent volatility (8 weeks)", "yoy": "Change vs a year ago",
              "month_sin": "Month (seasonal cycle, sin)", "month_cos": "Month (seasonal cycle, cos)",
              "perishable": "Perishable item"}
    fig = go.Figure(go.Bar(x=sh.mean_abs_shap, y=sh.feature.map(labels), orientation="h", marker_color="#1baf7a"))
    fig.update_layout(title="What the XGBoost model relies on most (mean |SHAP value|)", height=380,
                      xaxis_title="Average influence on the forecast (log change)")
    st.plotly_chart(fig, width="stretch")
    st.caption("SHAP values show how much each input pushed each forecast up or down. "
               "Last week’s price change matters most: prices tend to keep moving in the same direction for a while.")

# ---------------- Cities ----------------
with t_city:
    c = D["city"][(D["city"].item == item) & D["city"].reported]
    if c.empty:
        st.warning("No city prices for this item.")
    else:
        weeks = sorted(c.week_ending.dt.date.unique())
        wk = st.select_slider("Week", options=weeks, value=weeks[-1])
        cw = c[c.week_ending.dt.date == wk].sort_values("price_avg")
        fig = go.Figure(go.Bar(x=cw.price_avg, y=cw.city, orientation="h", marker_color=INK,
                               text=cw.price_avg.round(1), textposition="outside"))
        fig.update_layout(title=f"{item}: average price by city, week ending {wk}",
                          xaxis_title=f"Rs per {unit}", height=560)
        st.plotly_chart(fig, width="stretch")
        lo, hi = cw.iloc[0], cw.iloc[-1]
        st.write(f"Cheapest: **{lo.city}** (Rs {lo.price_avg:,.2f}). Dearest: **{hi.city}** "
                 f"(Rs {hi.price_avg:,.2f}), {hi.price_avg / lo.price_avg * 100 - 100:.0f}% higher.")
        st.caption("City prices are available for 6 weeks (10 September to 15 October 2026).")

# ---------------- About ----------------
with t_about:
    st.markdown(f"""
### About this project
**Question.** Can historical weekly prices predict the price of essential items in urban Pakistan
1–4 weeks ahead, and does any model beat the simple guess that next week will be the same as this week?

**Who it is for.** Households planning their food budget; policymakers and consumer-protection
groups watching prices.

**Data.** Pakistan Bureau of Statistics, Weekly Sensitive Price Indicator (SPI): 51 essential items,
50 markets, 17 cities. National averages for {nat.week_ending.nunique()} weeks
({nat.week_ending.min().date()} to {last_wk.date()}) from all 52 SPI Report Excel files in PBS’s archive,
including each report’s “same week last year” column. City prices from the weekly Annexure files.

**Models.** (1) Naive: next week = this week. (2) Seasonal naive: next week = same week last year.
(3) Linear regression and (4) XGBoost on the last four weekly price changes, recent volatility,
the calendar month and a perishable-item flag (XGBoost also sees the change versus a year ago).
Models 3–4 predict the percentage change, so all 51 items share one model.

**Validation.** Rolling-origin backtest, 43 test weeks (Jan–Nov 2026), horizons 1–4 weeks.
Rows are never shuffled; every input uses only earlier weeks.

**Limitations.**
- 17 urban cities only; rural households are not covered.
- PBS does not document how the 50 markets were chosen.
- Past prices can predict but cannot explain why prices move (floods, fuel, imports are not in the data).
- Two years is short for learning seasonal patterns.
- PBS prices are official averages, not what every household pays.

Code and data: github.com/habibbajwa43-lang/pk-food-prices
""")
