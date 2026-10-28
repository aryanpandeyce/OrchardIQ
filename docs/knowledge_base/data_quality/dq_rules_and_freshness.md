# Data Quality Standards & Warehouse Freshness

## Ingestion SLAs
- `fact_sales`: Partitioned Parquet batches updated hourly; daily close reconciled at 02:00 UTC.
- `fact_support_claims`: Genius Bar warranty claims synchronized every 4 hours.
- Freshness threshold: Alerts fire if `MAX(date_id)` is older than 24 hours in production.

## Completeness & Null Rules
- Zero tolerance (0.0% nulls) on primary keys (`sale_id`, `product_id`, `date_id`, `customer_id`).
- Referential integrity: 100% of foreign keys in fact tables must resolve to corresponding dimension tables.
