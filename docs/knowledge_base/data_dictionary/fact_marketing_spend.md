# Data Dictionary: fact_marketing_spend

## Overview
Daily marketing campaign expenditure by region, channel, and target product line, including digital acquisition and keynote broadcast investments.

## Schema Specification
| Column Name | Data Type | Partition Key | Description |
|-------------|-----------|---------------|-------------|
| `spend_id` | STRING | No | Primary Key. |
| `date_id` | INTEGER | No | Foreign Key to `dim_date`. |
| `region_id` | STRING | No | Foreign Key to `dim_region`. |
| `product_id` | STRING | No | Target product SKU or `PRD-BRAND`. |
| `channel` | STRING | No | Medium (`Digital Search`, `Paid Social`, `Broadcast TV & Cinema`, `Out of Home (OOH)`, `Keynote Event / PR`). |
| `spend_usd` | DOUBLE | No | Total campaign expenditure in USD. |
| `impressions` | BIGINT | No | Ad views or verified impressions. |
| `clicks` | BIGINT | No | Verified direct-response click-throughs. |
| `conversions` | BIGINT | No | Attributed purchases within 14-day window. |
| `year` | INTEGER | Yes | Partition key. |
| `month` | INTEGER | Yes | Partition key. |
