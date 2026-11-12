# 8. Model results (produced by `src/forecast.py`)

All numbers are copied from `reports/model_outputs/`; re-running the pipeline reproduces them.
Charts: `reports/figures/results_1` to `results_4`.

## Set-up
- **Data:** national average prices of all 51 SPI items, 102 weeks (24-10-2024 to 05-11-2026).
- **Target:** the price 1, 2, 3 and 4 published weeks ahead (Rs per unit).
- **Models:** naive (same as last week); seasonal naive (same week last year); linear regression and
  XGBoost on the last four weekly log-changes, recent volatility (8-week s.d.), calendar month
  (sin/cos) and a perishable flag; XGBoost also gets the change versus a year earlier. Models 3–4
  predict the log change and are pooled across all 51 items.
- **Validation:** rolling-origin backtest, 43 forecast origins with targets from January to
  November 2026; at each origin the models are retrained on rows whose target week is already in
  the past (2,601 training rows in the first fold, 4,896 in the last). Nothing is shuffled.
- **80% ranges:** 10th–90th percentile of each item's earlier backtest errors, using only errors
  whose target week had already been observed.

## 1. Accuracy (lower is better)

**8 staples** (onions, tomatoes, potatoes, sugar, wheat flour, eggs, chicken, masoor), MAE in Rs per unit:

| Weeks ahead | Naive | Linear regression | XGBoost | Seasonal naive | Linear vs naive |
|---|---:|---:|---:|---:|---:|
| 1 | 12.71 | **12.38** | 16.07 | 132.74 | −2.6% |
| 2 | 20.82 | **20.48** | 25.09 | 132.74 | −1.6% |
| 3 | 27.91 | **26.37** | 33.76 | 132.74 | −5.5% |
| 4 | 34.39 | **32.22** | 39.00 | 132.74 | −6.3% |

**All 51 items**, MAE in Rs per unit:

| Weeks ahead | Naive | Linear regression | XGBoost | Seasonal naive |
|---|---:|---:|---:|---:|
| 1 | **7.56** | 8.53 | 8.99 | 89.73 |
| 2 | **12.49** | 13.95 | 13.56 | 89.73 |
| 3 | **16.75** | 19.06 | 18.98 | 89.73 |
| 4 | **19.80** | 22.87 | 22.60 | 89.73 |

**Staples one week ahead, MAE per item (Rs):**

| Item | Naive | Seasonal naive | Linear | XGBoost |
|---|---:|---:|---:|---:|
| Chicken Farm Broiler (Live) | **20.95** | 68.03 | 22.92 | 25.83 |
| Eggs Hen (Farm) | 7.80 | 52.18 | **7.36** | 8.15 |
| Onions | **6.76** | 47.99 | 7.02 | 10.52 |
| Potatoes | 1.56 | 31.56 | **1.41** | 1.43 |
| Pulse Masoor (Washed) | **1.16** | 33.09 | 1.22 | 1.18 |
| Sugar Refined | **0.56** | 26.59 | 0.75 | 0.58 |
| Tomatoes | **22.89** | 70.57 | 24.76 | 23.38 |
| Wheat Flour Bag | 39.98 | 731.94 | **33.57** | 57.45 |

Across all 51 items, linear regression had a lower one-week MAE than naive for 6 items, XGBoost for 14.

## 2. How honest are the 80% price ranges? (target: 80%)

| Weeks ahead | Naive | Linear regression | XGBoost |
|---|---:|---:|---:|
| 1 | 83.1% | 63.6% | 69.4% |
| 2 | 78.9% | 58.0% | 67.5% |
| 3 | 75.5% | 52.7% | 62.1% |
| 4 | 70.8% | 48.9% | 58.8% |

## 3. ">5% rise next week" alerts (alert when estimated chance ≥ 50%)

| Model | Alerts | Real >5% rises | Correct alerts | Right when raised | Rises caught |
|---|---:|---:|---:|---:|---:|
| Naive | 13 | 66 | 5 | 38.5% | 7.6% |
| Linear regression | 21 | 66 | 7 | 33.3% | 10.6% |
| XGBoost | 46 | 66 | 12 | 26.1% | 18.2% |
| Seasonal naive | 168 | 66 | 15 | 8.9% | 22.7% |

## What the numbers show
1. **"Same as last week" is very hard to beat.** Across all 51 items, the naive forecast had the lowest
   error at every horizon. Most SPI items (cloth, soap, fuel, phone charges) barely change week to week.
2. **For the 8 staples, linear regression is slightly better in rupees**, by 2.6% one week ahead and 6.3%
   four weeks ahead. **But the gain comes mostly from wheat flour**, the most expensive staple
   (Rs 39.98 → 33.57). In percentage terms the two are level one week ahead (MAPE 4.52% naive vs 4.62%
   linear). Naive is still best for onions, tomatoes, chicken, sugar and masoor.
3. **XGBoost did worse than the simple models** for the staples at every horizon, even though it had
   more inputs. With about 5,000 training rows and noisy weekly changes, the extra flexibility did not pay off.
4. **Seasonal naive was the worst by far**, because prices moved a lot between years (e.g. the 20 kg
   wheat flour bag went from about Rs 1,500 in mid-2025 to about Rs 2,940 in November 2026).
5. **Only the naive model's 80% ranges were close to honest** (83% one week ahead). The regression and
   XGBoost ranges were too narrow: their past errors understate how wrong they can be.
6. **Sudden >5% rises are mostly not predictable from past prices.** The best alerts were right about
   one time in three and caught at most 18% of real rises.
7. **Tomatoes are the least predictable item**: a typical weekly move of ±22.4%, more than twice onions (±9.1%).
8. **What the models rely on:** last week's price change matters most (XGBoost mean |SHAP| 0.0040,
   twice the next input), i.e. prices that started rising tend to keep rising for a while.

## Caution
- Two years of data is short for learning seasonal patterns; the month features are weak.
- The backtest covers 2026 only; a different year (e.g. a flood year) could rank the models differently.
- Forecasts for weeks after 05-11-2026 (`forecast_next_weeks.csv`) are model outputs, not PBS prices,
  and had not been checked against PBS's published figures at the time of writing.
