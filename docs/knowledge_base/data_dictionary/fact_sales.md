# Data Dictionary: fact_sales

## Overview
Core transactional fact table recording every unit sale across physical Orchard stores and digital direct-to-consumer storefronts. Partitioned by `year` and `month`.

## Schema Specification
| Column Name | Data Type | Partition Key | Description |
|-------------|-----------|---------------|-------------|
| `sale_id` | STRING | No | Primary Key. Unique invoice identifier. |
| `date_id` | INTEGER | No | Foreign Key to `dim_date`. |
| `customer_id` | STRING | No | Foreign Key to `dim_customer`. |
| `product_id` | STRING | No | Foreign Key to `dim_product`. |
| `store_id` | STRING | No | Foreign Key to `dim_store`. |
| `region_id` | STRING | No | Foreign Key to `dim_region`. |
| `channel` | STRING | No | Sales channel: `Retail` or `Online`. |
| `units` | INTEGER | No | Number of units purchased. |
| `unit_price` | DOUBLE | No | Transactional unit price in USD. |
| `discount_amount` | DOUBLE | No | Total promotional / educational discount. |
| `gross_revenue` | DOUBLE | No | `units * unit_price`. |
| `net_revenue` | DOUBLE | No | `gross_revenue - discount_amount`. |
| `cogs` | DOUBLE | No | Cost of goods sold (`units * cost_usd`). |
| `gross_margin` | DOUBLE | No | `net_revenue - cogs`. |
| `tax_amount` | DOUBLE | No | Applicable sales / value-added tax. |
| `year` | INTEGER | Yes | Year partition key. |
| `month` | INTEGER | Yes | Month partition key (1-12). |
