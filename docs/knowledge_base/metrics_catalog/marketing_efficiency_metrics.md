# Metrics Catalog: Marketing Efficiency

## Available Metrics
1. **Total Marketing Spend**: `SUM(spend_usd)` from `fact_marketing_spend`
2. **Cost Per Click (CPC)**: `SUM(spend_usd) * 1.0 / NULLIF(SUM(clicks), 0)`
3. **Conversion Rate (CVR)**: `SUM(conversions) * 100.0 / NULLIF(SUM(clicks), 0)`
4. **Blended Customer Acquisition Cost**: `SUM(spend_usd) * 1.0 / NULLIF(SUM(conversions), 0)`
