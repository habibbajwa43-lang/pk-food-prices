# 3. The five questions

**What is a row?**
A row represents one item (such as onions) for one week, along with its average price per unit across Pakistan. The dataset contains 971 rows, covering 19 weeks and 52 item names, as shown in `reports/checks_output.txt`. Confidence: High, because the row structure and dataset summary support this interpretation.

**What is the unit of the outcome?**
The outcome variable `price_avg` is measured in Pakistani rupees (Rs) per unit of an item. The dataset contains 14 distinct units, with 1 Kg being the most common unit (17 items). No item changes its unit across weeks or cities, as confirmed by `items whose unit changes across weeks/cities: 0`.
Prices of different units, such as a 20 Kg flour bag costing Rs 2,681 and 1 Kg of potatoes costing Rs 57, cannot be compared directly because their quantities differ. Therefore, Chart 1 converts prices to an index where the first week equals 100, allowing price changes over time to be compared.
Confidence: High, because the unit counts and consistency checks support this interpretation.

**What is the timeframe?**
The national table covers 10 July–4 September 2025 (9 weeks from the `year_ago` column) and 2 July–3 September 2026 (10 weeks), with a 301-day gap between 4 September 2025 and 2 July 2026. This gap is a problem for forecasting because the data does not provide continuous weekly observations across that period. The city table covers six weeks, from 10 September to 15 October 2026. One unusual week ends on Wednesday, 13 August 2025, instead of Thursday.
Confidence: Medium, because the date ranges are confirmed by the checks, but the 301-day gap remains unfilled.

**Who is missing?**
1. Missing areas: The dataset covers 17 urban centres: 8 in Punjab (Bahawalpur, Faisalabad, Gujranwala, Lahore, Multan, Rawalpindi, Sargodha and Sialkot), 3 in Sindh (Hyderabad, Karachi and Sukkur), 2 in Khyber Pakhtunkhwa (Bannu and Peshawar), and 2 in Balochistan (Khuzdar and Quetta), plus Islamabad and Larkana?
2. Missing people: The data represents urban markets, not everyone in Pakistan. Rural communities, people in unlisted cities, and households whose shopping prices differ from official market prices are not directly represented; the 17-centre list contains no city from Gilgit-Baltistan or Azad Jammu and Kashmir.
3. Missing data: Rice IRRI-6/9 is missing from three cities for some weeks, but the exact city names and week counts need to be verified from the `MISSING` section of `checks_output.txt`.
Confidence: Medium — the listed cities support the coverage limitations, but the exact rice-missing details and regional counts should be checked against the report.

**What was the sampling frame?**
PBS collects prices for 51 essential items from 50 markets across 17 urban centres, using tablets and Computer-Assisted Personal Interviews (CAPI) for digital data collection. This is a market price survey, not an administrative record or a model-generated dataset.
The available PBS documents confirm that prices are collected from 50 markets, but they do not explain how those markets were selected; therefore, the sampling method cannot be confirmed from the available evidence.
Confidence: High for the collection method and the limitation in the available documentation.
