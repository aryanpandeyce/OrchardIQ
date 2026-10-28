# Data Dictionary: dim_date

## Overview
Comprehensive enterprise calendar and fiscal calendar dimension. Orchard Inc. operates on a fiscal year starting October 1st.

## Fiscal Calendar Definition
- **Fiscal Q1**: October 1 – December 31 (Holiday Quarter)
- **Fiscal Q2**: January 1 – March 31
- **Fiscal Q3**: April 1 – June 30
- **Fiscal Q4**: July 1 – September 30 (Fall Product Launch Quarter)

## Schema Specification
| Column Name | Data Type | Nullable | Description | Sample Values |
|-------------|-----------|----------|-------------|---------------|
| `date_id` | INTEGER | No | Primary Key formatted as YYYYMMDD. | `20250920` |
| `full_date` | DATE | No | Standard ISO-8601 calendar date. | `2025-09-20` |
| `day_of_week` | INTEGER | No | Day of week index (1 = Monday, 7 = Sunday). | `6` |
| `day_name` | STRING | No | Full English name of the day. | `Saturday` |
| `day_of_month` | INTEGER | No | Day of month (1-31). | `20` |
| `month_number` | INTEGER | No | Calendar month index (1-12). | `9` |
| `month_name` | STRING | No | Full calendar month name. | `September` |
| `calendar_quarter` | STRING | No | Calendar quarter string. | `2025-Q3` |
| `calendar_year` | INTEGER | No | Calendar year. | `2025` |
| `fiscal_quarter` | STRING | No | Orchard fiscal quarter string. | `FY2025-Q4` |
| `fiscal_year` | INTEGER | No | Orchard fiscal year. | `2025` |
| `is_weekend` | BOOLEAN | No | True if Saturday or Sunday. | `true` |
| `is_holiday` | BOOLEAN | No | True if recognized public holiday. | `false` |
| `holiday_name` | STRING | Yes | Recognized holiday name or null. | `Black Friday` |
