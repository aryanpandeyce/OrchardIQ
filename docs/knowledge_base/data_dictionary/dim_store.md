# Data Dictionary: dim_store

## Overview
Master registry of all physical Orchard Retail Stores, Authorized Reseller channels, and regional Online Digital Storefronts.

## Schema Specification
| Column Name | Data Type | Nullable | Description | Sample Values |
|-------------|-----------|----------|-------------|---------------|
| `store_id` | STRING | No | Primary Key. Global store code. | `STR-US-001`, `STR-UK-012` |
| `store_name` | STRING | No | Official retail or channel designation. | `Orchard Fifth Avenue`, `Orchard Regent Street` |
| `channel` | STRING | No | Distribution modality. | `Retail Store`, `Online Store`, `Authorized Reseller` |
| `city` | STRING | No | Store location city. | `New York`, `London`, `Tokyo` |
| `state_province` | STRING | Yes | State, province, or canton. | `NY`, `Greater London`, `Tokyo` |
| `country` | STRING | No | ISO country or jurisdiction. | `United States`, `United Kingdom`, `Japan` |
| `region_id` | STRING | No | Foreign Key to `dim_region`. | `AMER`, `EMEA`, `APAC`, `LATAM` |
| `square_feet` | INTEGER | No | Physical sales floor area in sq ft (0 for Online). | `18500`, `0` |
| `opened_date` | DATE | No | Grand opening date. | `2006-05-19` |
