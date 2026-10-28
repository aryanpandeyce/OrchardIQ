# Data Dictionary: fact_finance_revenue

## Overview
Finance ledger reconciliation fact table recording recognized net hardware revenue, deferred services revenue (OrchardCare, Cloud), total GAAP revenue, and operating margin.

## Schema Specification
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `finance_entry_id` | STRING | Primary Key for ledger entry. |
| `date_id` | INTEGER | Foreign Key to `dim_date`. |
| `fiscal_quarter` | STRING | Orchard Fiscal Quarter (e.g. `FY2025-Q3`). |
| `fiscal_year` | INTEGER | Fiscal Year integer. |
| `region_id` | STRING | Foreign Key to `dim_region`. |
| `product_line` | STRING | Product line category (`Pro`, `Standard`, `Ultra`, `Air`). |
| `recognized_net_revenue` | DOUBLE | Hardware recognized GAAP revenue in USD. |
| `deferred_services_revenue` | DOUBLE | Amortized services / subscription revenue. |
| `total_gaap_revenue` | DOUBLE | Total recognized top-line revenue. |
| `operating_margin` | DOUBLE | Operating profit margin ratio (0.0 to 1.0). |
