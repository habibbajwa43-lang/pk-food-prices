# 5. EDA v1

Charts are in `reports/figures/` (made by `src/eda_charts.py`); confounder numbers from `src/confounder_check.py`.

## Charts
1. `1_staples_indexed.png` — **Onion Prices More Than Doubled While Tomato Prices Fell by 26% Between July and September 2026.** Source: PBS Sensitive Price Indicator (SPI), national average across 17 urban centres, 2 July–3 September 2026; prices indexed to the first week = 100.
2. `2_log_transform.png` (transformation, before and after) — **Log Transformation Spreads Out Skewed Price Data, Making Differences Between Cheap and Expensive Items Easier to See.** Source: PBS SPI price data; raw and log-transformed item prices compared to show how transformation changes the distribution.
3. `3_yoy_change.png` — **Onion Prices Rose 162.8% Year-on-Year While Potato Prices Fell 31.6%.** Source: PBS SPI, comparison with year-ago prices for selected essential items, September 2026 versus September 2025.
4. `4_city_spread.png` — **Tomato and Potato Prices Vary Sharply Across Cities, While Sugar Prices Remain More Consistent.** Source: PBS SPI city-level prices across 17 urban centres; city price spread measured as the difference between the highest and lowest city prices relative to the lowest price.

## Five properties
1. Structure: The original PBS data was provided in wide-format Excel tables, which I converted into long format so each row represents one item-week nationally or one item-city-week in the city table.
2. Granularity: The national dataset records one item per week, while the city dataset records one item per city per week; market-level observations are not available.
3. Scope: The dataset covers 51 essential items across 17 urban centres, including food items and some non-food essentials such as gas.
4. Temporality: The data is weekly and covers two separate national periods: July–September 2025 and July–September 2026, with a 301-day gap between them.
5. Faithfulness: PBS prices are based on the geometric mean of prices collected from three shops, with markets selected using sales-volume criteria, so these figures may differ from the actual prices paid by individual households.

## Confounder check
Relationship: "Are bigger cities more expensive?" — Karachi and Lahore compared with the other 15 cities, sliced by item type (fresh vegetables: tomatoes, potatoes; packaged goods: sugar, tea).

Across all four items, Karachi and Lahore were about 3.2% more expensive on average than the other 15 cities. After splitting by item type, the difference was larger for fresh vegetables (4.7%) than for packaged goods (1.6%), but the direction stayed the same: both groups were more expensive in the two large cities.
However, the pattern does not apply equally to both cities: tomatoes were cheaper in Karachi (Rs 147) than in Lahore (Rs 186). Confidence is limited because this comparison covers only four items and six weeks, so it cannot establish a general rule for all items, cities or time periods.

## Three findings in everyday language
1. Onion prices more than doubled: The onion price index rose to about 218 between July and September 2026, while tomato prices fell to around 74.
2. Year-on-year price changes varied by item: Onion prices increased by 162.8%, while potato prices decreased by 31.6% compared with the previous year.
3. City price differences depend on the item: The cheapest and most expensive cities differed by 183% for tomatoes and 127% for potatoes, compared with only 14% for sugar.
