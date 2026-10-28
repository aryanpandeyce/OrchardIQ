# Data Dictionary: fact_support_claims

## Overview
Fact table recording OrchardCare hardware warranty claims, in-store Genius Bar diagnostics, component replacements, and repair turnarounds.

## Schema Specification
| Column Name | Data Type | Partition Key | Description |
|-------------|-----------|---------------|-------------|
| `claim_id` | STRING | No | Primary Key. Unique support case number. |
| `date_id` | INTEGER | No | Foreign Key to `dim_date`. |
| `customer_id` | STRING | No | Foreign Key to `dim_customer`. |
| `product_id` | STRING | No | Foreign Key to `dim_product`. |
| `store_id` | STRING | No | Foreign Key to `dim_store` where service was rendered. |
| `region_id` | STRING | No | Foreign Key to `dim_region`. |
| `claim_type` | STRING | No | Fault classification (`Battery Degradation/Thermal`, `Display/Glass Crack`, etc.). |
| `claim_status` | STRING | No | Status (`Approved & Replaced`, `Repaired In-Store`, etc.). |
| `repair_cost` | DOUBLE | No | Internal Orchard service cost incurred. |
| `customer_deductible` | DOUBLE | No | Out-of-pocket fee paid by customer under warranty. |
| `turnaround_days` | INTEGER | No | Days elapsed from check-in to customer handoff. |
| `component_batch_id` | STRING | No | Traceable component lot identifier (e.g. `BP-2025-08`). |
| `year` | INTEGER | Yes | Partition key. |
| `month` | INTEGER | Yes | Partition key. |
