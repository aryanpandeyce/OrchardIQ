# Data Dictionary: dim_region

## Overview
Geographic operational theaters governing Orchard Inc. worldwide distribution, legal entities, and statutory tax obligations.

## Schema Specification
| Column Name | Data Type | Nullable | Description | Sample Values |
|-------------|-----------|----------|-------------|---------------|
| `region_id` | STRING | No | Primary Key. Global geographic abbreviation. | `AMER`, `EMEA`, `APAC`, `LATAM` |
| `region_name` | STRING | No | Full territorial designation. | `Americas`, `Europe, Middle East & Africa` |
| `headquarters_city` | STRING | No | Regional operating headquarters. | `Cupertino, CA`, `London, UK` |
| `currency` | STRING | No | Primary reporting currency. | `USD`, `EUR` |
| `tax_rate_standard` | DOUBLE | No | Baseline standard VAT/sales tax rate. | `0.0825`, `0.2000` |
