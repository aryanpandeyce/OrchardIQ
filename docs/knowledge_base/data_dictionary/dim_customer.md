# Data Dictionary: dim_customer

## Overview
Customer master table containing identity, contact information, segmentation, and regional affinity. Contains Restricted PII governed by policy.

## Schema Specification
| Column Name | Data Type | Nullable | PII Classification | Description |
|-------------|-----------|----------|--------------------|-------------|
| `customer_id` | STRING | No | None | Unique customer synthetic identifier (`CUST-XXXXXX`). |
| `first_name` | STRING | No | Restricted PII | Customer first name. Masked for role `analyst`. |
| `last_name` | STRING | No | Restricted PII | Customer family name. Masked for role `analyst`. |
| `email` | STRING | No | Restricted PII | Primary Orchard ID email address. Masked for role `analyst`. |
| `phone` | STRING | No | Restricted PII | Primary mobile telephone number. Masked for role `analyst`. |
| `street_address` | STRING | No | Restricted PII | Billing street address. Masked for role `analyst`. |
| `city` | STRING | No | None | Customer residential city. |
| `country` | STRING | No | None | Residence country. |
| `region_id` | STRING | No | None | Foreign Key to `dim_region`. |
| `customer_segment` | STRING | No | None | Segmentation: `Consumer`, `Enterprise`, `Education`, `Small Business`. |
| `signup_date` | DATE | No | None | Date customer created their Orchard account. |
