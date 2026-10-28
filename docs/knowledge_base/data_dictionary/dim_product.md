# Data Dictionary: dim_product

## Overview
Dimension table containing the master record for all hardware devices and accessories manufactured and sold by Orchard Inc.

## Schema Specification
| Column Name | Data Type | Nullable | Description | Sample Values |
|-------------|-----------|----------|-------------|---------------|
| `product_id` | STRING | No | Primary Key. Standard Orchard SKU identifier. | `PRD-PHN-16P`, `PRD-NBK-16P` |
| `product_name` | STRING | No | Commercial marketing product name. | `PearPhone 16 Pro`, `PearBook Pro 16"` |
| `category` | STRING | No | High-level device taxonomy. | `Smartphone`, `Laptop`, `Tablet`, `Wearables` |
| `product_line` | STRING | No | Product tier / specification segment. | `Pro`, `Standard`, `Ultra`, `Air` |
| `price_usd` | DOUBLE | No | Manufacturer's Suggested Retail Price (MSRP) in USD. | `999.00`, `2499.00` |
| `cost_usd` | DOUBLE | No | Bill of Materials (BOM) & landed manufacturing cost in USD. | `415.00`, `1050.00` |
| `launch_date` | DATE | No | Date of global retail availability. | `2024-09-20` |
| `warranty_months` | INTEGER | No | Standard limited warranty duration in months. | `12`, `24` |
| `status` | STRING | No | Lifecycle status. | `Active`, `Discontinued` |

## Primary Grain
One row per distinct Orchard hardware SKU.
