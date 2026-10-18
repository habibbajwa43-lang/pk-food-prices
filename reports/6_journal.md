# 6. Engagement journal

## Before I looked
Before examining the data, I had not committed to any predictions, so I cannot honestly claim that I made these predictions in advance. For the next unseen weeks, my three predictions are: onion prices may remain volatile after their sharp increase; tomato prices may rise or fall depending on seasonal supply; and sugar prices may remain relatively stable compared with fresh vegetables. I will record these predictions separately before checking the new data so I can evaluate them fairly.

## What I did, in order
I started by developing the project idea and checking the PBS data, then examined the first two files and discovered that each contained only one week's information. I searched the PBS archive and downloaded 15 files, but nine were mistakenly the "Report" files rather than the intended "Annexure" files; this apparent dead end turned out to be useful because the Report files contained national prices for three weeks. I then ran data checks, which revealed 18 zero-price rows for rice, inconsistent gas labels, one Wednesday-ending week and a 301-day gap in the national series. I also reviewed the methodology documentation and could not find how PBS selected the SPI markets. Finally, I converted the Excel data into long format, documented the cleaning decisions and revised my initial interpretation of the gas labels after comparing the dates, prices and units across files.

## What surprised me
I was surprised that each of the first two PBS files contained only one week of data, while the Report files provided national prices for three weeks; I checked the file contents and compared the dates to confirm this. I was also surprised that onion prices increased by 162.8% year-on-year, while potato prices fell by 31.6%; I verified these figures against the national price data used for the year-on-year chart. Finally, I found that tomatoes were cheaper in Karachi (Rs 147) than in Lahore (Rs 186) and the other 15 cities' average (Rs 159); I checked the six-week city averages to confirm that the pattern was not simply a difference between the two largest cities.

## What I revised
Initially, I thought the two gas labels might refer to different reporting periods, but comparing the source files showed that they referred to the same item-week, with the same unit and price. I revised my explanation and documented the duplicate-row issue while keeping the labels separate because gas is outside my main food-price forecasting scope.

I also initially treated the Report files as the wrong files for my project, assuming the Annexures were the main source I needed. After inspecting the Report files, I discovered that they contained national prices for multiple weeks, making them useful for the national analysis. This changed how I understood the available data and helped explain the structure of the national dataset.

## What I still don't trust
I do not fully trust the representativeness of the SPI data because the available PBS documentation confirms that prices are collected from 50 markets in 17 urban centres but does not explain how those markets were selected. The results may therefore not represent rural areas or all households across Pakistan.

I also do not fully trust forecasts based on the national time series because there is a 301-day gap between September 2025 and July 2026. This makes it difficult to establish continuous weekly patterns and could weaken forecasting performance. In addition, the dataset covers a limited number of weeks and items, so I would treat predictions as uncertain until they are tested against genuinely unseen data.
