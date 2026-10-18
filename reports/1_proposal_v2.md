# 1. Proposal v2

Week 1 proposal: `reports/proposal_v1_week1.docx`

**Framing sentence:** For a household or consumer planning their budget, estimate next week's prices for selected essential items using weekly PBS urban price data, so they can anticipate possible changes in the cost of essential goods.

**Primary stakeholder:** A household or consumer budgeting for essential goods.

**Success metric:** Predict the next week's price for selected items using the most recent observed price as the baseline. Evaluate the model on unseen weeks using mean absolute error (MAE); the model succeeds if it achieves a lower MAE than the baseline that predicts next week's price will equal the most recently observed price.

**What changed:** The data source changed from the initially intended Annexure files to the PBS Report files because these provided the national weekly prices needed for the analysis. The project retains households and consumers as its primary stakeholder, while recognising that policymakers and consumer-protection organisations may also benefit from the findings. The absence of market-level observations and the 301-day gap in the national series limit the conclusions and forecasting reliability.
