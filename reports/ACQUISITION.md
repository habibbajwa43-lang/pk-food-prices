# 2. Acquisition Record

**Source.** Pakistan Bureau of Statistics (PBS), Price Statistics section, Weekly SPI.
Page: https://www.pbs.gov.pk/price-statistics/ (tab "Weekly Sensitive Price Index (SPI)").
PBS describes the SPI as computed weekly "to assess the price movements of essential
commodities at shorter interval of time", from 51 items collected in 50 markets across
17 cities.

**Files.** Weekly "Annexure (Excel)" files (city-wise min/avg/max prices, Appendix-A)
and weekly "Report (Excel)" files (national average prices for the current week,
previous week and the same week a year earlier). Pulled by hand from the archive
table on 2026-10-18. Untouched copies are in `data/raw/` and `data/raw/reports/`.

**Acquisition method.** I used direct file downloads from the PBS website's archive table. I downloaded the available Report and Annexure Excel files rather than using an API, scraping the website, or manually entering prices, because the source already provided downloadable files in a structured format. I then used scripts to inspect, combine and validate the downloaded data.

**Terms of use / privacy.** PBS's *Official Statistics and Data Dissemination Policy* (August 2026, https://www.pbs.gov.pk/wp-content/uploads/2020/07/policy.pdf) states that aggregate statistics and non-confidential datasets are normally released free of charge under an open licence that permits copying, adaptation and redistribution, provided the source is acknowledged, changes are identified, and altered data are not presented as official PBS statistics. The restrictions in the policy apply to microdata, customised data and sampling frames, not to the public SPI price tables used here. This repository cites PBS as the source, keeps the raw files unchanged in `data/raw/`, and records every change in `CLEANING.md`. The data are market prices of goods, not information about people, so there are no personal-data concerns.

**Could a stranger re-pull this next month?** Another person could probably repeat the process because the PBS archive is publicly accessible and a new row is added each Thursday. However, the process is not fully automated or guaranteed to work unchanged: filenames follow inconsistent patterns, the latest reports may use different naming conventions, and the person repeating the acquisition would need to identify the correct files and check that their structure has not changed.
