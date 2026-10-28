# Metrics Catalog: Sales & Revenue

## Available Metrics
1. **Total Net Revenue**: `SUM(net_revenue)` from `fact_sales`
2. **Gross Margin Dollar**: `SUM(gross_margin)` from `fact_sales`
3. **Gross Margin Percentage**: `SUM(gross_margin) * 100.0 / NULLIF(SUM(net_revenue), 0)`
4. **Units Sold**: `SUM(units)` from `fact_sales`
5. **Average Selling Price (ASP)**: `SUM(net_revenue) * 1.0 / NULLIF(SUM(units), 0)`
