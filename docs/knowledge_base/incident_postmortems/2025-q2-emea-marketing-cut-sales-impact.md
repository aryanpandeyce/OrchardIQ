# Incident Postmortem: EMEA Q2 2025 Marketing Spend Slump & Retail Contraction

## Incident Summary
- **Incident ID**: INC-2025-0428-EMEA
- **Date Range**: April 1, 2025 – June 30, 2025 (FY2025-Q3 / Calendar Q2)
- **Impacted Entity**: EMEA Retail Channel
- **Impacted Region**: `EMEA` (UK, Germany, France, Italy)
- **Severity**: P2 - Commercial Performance Anomaly

## Background & Decision
During executive budgeting in March 2025, global marketing leadership approved an extraordinary reallocation of $1.8M in regional marketing funds from EMEA Paid Social and Digital Search to fund title sponsorship of the North American Worldwide Pear Developers Conference (WWPC 2025).

## Observed Impact
As a consequence of the 65% reduction in digital acquisition spend across EMEA, physical retail store foot traffic fell by 31%, resulting in a quarterly retail net revenue drop of ~24% compared to Q1 2025 and 22% YoY. Online store direct sales also dropped 16%.

## Key Finding for Analytics
When querying `fact_sales` and `fact_marketing_spend` for EMEA in 2025, the sharp sales downturn in months 4, 5, and 6 directly correlates with the collapse in `spend_usd` in `fact_marketing_spend`.
