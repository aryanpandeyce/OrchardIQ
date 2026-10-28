# Data Dictionary: fact_returns

## Overview
Fact table recording returned hardware units, customer refund amounts, return reasons, and disposition.

## Schema Specification
| Column Name | Data Type | Partition Key | Description |
|-------------|-----------|---------------|-------------|
| `return_id` | STRING | No | Primary Key. |
| `sale_id` | STRING | No | Foreign Key to `fact_sales`. |
| `date_id` | INTEGER | No | Foreign Key to `dim_date`. |
| `customer_id` | STRING | No | Foreign Key to `dim_customer`. |
| `product_id` | STRING | No | Foreign Key to `dim_product`. |
| `store_id` | STRING | No | Foreign Key to `dim_store`. |
| `region_id` | STRING | No | Foreign Key to `dim_region`. |
| `return_reason` | STRING | No | Primary return driver (`Defective / Hardware Issue`, `Buyer Remorse`, etc.). |
| `units` | INTEGER | No | Units returned. |
| `refund_amount` | DOUBLE | No | Net dollar amount refunded to customer. |
| `restock_status` | STRING | No | Post-return processing: `Refurbished`, `Recycled`, `Resold`. |
| `year` | INTEGER | Yes | Partition key. |
| `month` | INTEGER | Yes | Partition key. |
