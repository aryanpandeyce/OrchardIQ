"""Generator for unstructured enterprise assets: ~30 Markdown documentation files and ~5,000 support tickets."""

import json
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from src.data_gen.schema import ORCHARD_PRODUCTS, REGIONS, CLAIM_TYPES
from src.data_gen.stories import INJECTED_STORIES


def generate_knowledge_base_docs(docs_dir: Path) -> int:
    """Generate ~30 enterprise markdown docs covering glossary, dictionary, quality, and incident postmortems."""
    docs_created = 0

    subdirs = [
        "data_dictionary",
        "business_glossary",
        "incident_postmortems",
        "data_quality",
        "metrics_catalog",
    ]
    for subdir in subdirs:
        (docs_dir / subdir).mkdir(parents=True, exist_ok=True)

    # 1. Data Dictionary Docs (10 tables)
    table_docs = {
        "dim_product": """# Data Dictionary: dim_product

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
""",
        "dim_store": """# Data Dictionary: dim_store

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
""",
        "dim_customer": """# Data Dictionary: dim_customer

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
""",
        "dim_date": """# Data Dictionary: dim_date

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
""",
        "dim_region": """# Data Dictionary: dim_region

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
""",
        "fact_sales": """# Data Dictionary: fact_sales

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
""",
        "fact_returns": """# Data Dictionary: fact_returns

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
""",
        "fact_support_claims": """# Data Dictionary: fact_support_claims

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
""",
        "fact_finance_revenue": """# Data Dictionary: fact_finance_revenue

## Overview
Finance ledger reconciliation fact table recording recognized net hardware revenue, deferred services revenue (OrchardCare, Cloud), total GAAP revenue, and operating margin.

## Schema Specification
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `finance_entry_id` | STRING | Primary Key for ledger entry. |
| `date_id` | INTEGER | Foreign Key to `dim_date`. |
| `fiscal_quarter` | STRING | Orchard Fiscal Quarter (e.g. `FY2025-Q3`). |
| `fiscal_year` | INTEGER | Fiscal Year integer. |
| `region_id` | STRING | Foreign Key to `dim_region`. |
| `product_line` | STRING | Product line category (`Pro`, `Standard`, `Ultra`, `Air`). |
| `recognized_net_revenue` | DOUBLE | Hardware recognized GAAP revenue in USD. |
| `deferred_services_revenue` | DOUBLE | Amortized services / subscription revenue. |
| `total_gaap_revenue` | DOUBLE | Total recognized top-line revenue. |
| `operating_margin` | DOUBLE | Operating profit margin ratio (0.0 to 1.0). |
""",
        "fact_marketing_spend": """# Data Dictionary: fact_marketing_spend

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
""",
    }

    for name, content in table_docs.items():
        (docs_dir / "data_dictionary" / f"{name}.md").write_text(content, encoding="utf-8")
        docs_created += 1

    # 2. Business Glossary Docs (10 docs)
    glossary_docs = {
        "net_revenue": """# Business Glossary: Net Revenue

## Definition
Net Revenue represents the total monetary proceeds recognized by Orchard Inc. from the sale of hardware products and accessories, after subtracting commercial discounts, employee concessions, and education promotional allowances from Gross Revenue.

## Business Formula
$$\\text{Net Revenue} = \\text{Gross Revenue} - \\text{Discount Amount}$$
Where:
$$\\text{Gross Revenue} = \\text{Units Sold} \\times \\text{Unit Price (MSRP)}$$

## Data Warehouse Source
- **Table**: `fact_sales`
- **Columns**: `net_revenue`, `gross_revenue`, `discount_amount`
- **Aggregation**: `SUM(net_revenue)`

## Governance & Reconciliation
Net Revenue on `fact_sales` is reconciled monthly against `fact_finance_revenue.recognized_net_revenue`. Variances exceeding 0.05% trigger an automated audit event.
""",
        "attach_rate": """# Business Glossary: Attach Rate

## Definition
Attach Rate measures the proportion of secondary devices or accessories purchased alongside a primary flagship hardware product (such as a PearPhone or PearBook).

## Standard Orchard Formulas
1. **Wearable Attach Rate**:
$$\\text{Attach Rate}_{\\text{Watch}} = \\frac{\\sum \\text{Units of PearWatch}}{\\sum \\text{Units of PearPhone}} \\times 100\\%$$

2. **Audio Attach Rate**:
$$\\text{Attach Rate}_{\\text{Pods}} = \\frac{\\sum \\text{Units of PearPods}}{\\sum \\text{Units of PearPhone}} \\times 100\\%$$

## Benchmark Targets
- Baseline Wearable Attach Rate: **12% – 16%**
- Promotional Campaign Target: **> 30%** (Achieved during AMER Q4 2025 holiday bundle promotion).
""",
        "gross_margin": """# Business Glossary: Gross Margin

## Definition
Gross Margin reflects the profitability of hardware manufacturing and sales before deduction of operating expenses (OPEX), research & development (R&D), and general administrative costs.

## Business Formula
$$\\text{Gross Margin (\\$)} = \\text{Net Revenue} - \\text{Cost of Goods Sold (COGS)}$$
$$\\text{Gross Margin (\\%)} = \\frac{\\text{Gross Margin (\\$)}}{\\text{Net Revenue}} \\times 100\\%$$

## Data Warehouse Source
- **Table**: `fact_sales`
- **Columns**: `gross_margin`, `net_revenue`, `cogs`
""",
        "return_rate": """# Business Glossary: Return Rate

## Definition
The percentage of sold hardware units that are returned by customers within the standard 14-day consumer return window.

## Formula
$$\\text{Return Rate (\\%)} = \\frac{\\text{Count of Units in } fact\\_returns}{\\text{Count of Units in } fact\\_sales} \\times 100\\%$$

## SLA Thresholds
- **Normal Operating Range**: 1.5% – 2.8%
- **Amber Warning**: 3.0% – 5.0%
- **Red Incident Alert**: > 5.0% (Triggers hardware engineering triage, as seen in Q1 2025 PearBook Pro display flicker incident).
""",
        "claims_frequency": """# Business Glossary: Claims Frequency

## Definition
The annualized rate of warranty and OrchardCare repair requests submitted per 1,000 active device units in field operation.

## Formula
$$\\text{Claims Frequency} = \\frac{\\text{Total Support Claims}}{\\text{Active Installed Base (Thousands)}} \\times 1000$$

## Critical Anomaly Indicator
A spike in specific claim categories (e.g. `Battery Degradation/Thermal`) isolated to a single component batch identifier indicates manufacturing defects rather than random field failures.
""",
        "customer_lifetime_value": """# Business Glossary: Customer Lifetime Value (CLV)

## Definition
The cumulative net contribution margin generated by a customer across all hardware purchases, repeat upgrade cycles, and accessories over a rolling 36-month window.

## Usage
Used by Marketing to calibrate maximum allowable Customer Acquisition Cost (CAC) by customer segment (`Consumer`, `Enterprise`, `Education`).
""",
        "blended_cac": """# Business Glossary: Blended CAC

## Definition
Blended Customer Acquisition Cost calculated by dividing total regional marketing expenditures by the number of new customer accounts activated within the same fiscal quarter.

## Formula
$$\\text{Blended CAC} = \\frac{\\sum \\text{Marketing Spend (USD)}}{\\sum \\text{New Customer Signups}}$$
""",
        "roas": """# Business Glossary: Return on Ad Spend (ROAS)

## Definition
The revenue multiple generated directly from paid marketing campaigns across Digital Search, Paid Social, and Broadcast media.

## Formula
$$\\text{ROAS} = \\frac{\\text{Attributed Net Revenue}}{\\text{Marketing Spend (USD)}}$$
""",
        "services_arpu": """# Business Glossary: Services ARPU

## Definition
Average Revenue Per User generated from recurring digital services, warranty subscriptions (OrchardCare), and cloud storage allocations.
""",
        "same_store_sales": """# Business Glossary: Same-Store Sales (SSS)

## Definition
Comparative sales growth percentage generated by physical retail stores open continuously for at least 12 months, excluding newly opened or remodeled locations.
""",
    }

    for name, content in glossary_docs.items():
        (docs_dir / "business_glossary" / f"{name}.md").write_text(content, encoding="utf-8")
        docs_created += 1

    # 3. Incident Postmortems (4 docs matching stories)
    postmortems = {
        "2025-q3-apac-battery-claims-spike": """# Incident Postmortem: APAC Q3 2025 PearPhone 16 Pro Battery Claims Spike

## Incident Summary
- **Incident ID**: INC-2025-0814-APAC
- **Date Range**: July 1, 2025 – September 30, 2025 (FY2025-Q4 / Calendar Q3)
- **Impacted SKU**: `PRD-PHN-16P` (PearPhone 16 Pro)
- **Impacted Region**: `APAC` (Hong Kong, Japan, Singapore, Australia)
- **Severity**: P1 - Quality & Safety Escrow

## Symptoms & Detection
In early August 2025, Orchard Genius Bars in Singapore, Tokyo, and Sydney reported an unprecedented 4.5x surge in PearPhone 16 Pro warranty repair submissions. Over 62% of all claims for the device in APAC were classified under `Battery Degradation/Thermal`, compared to a historical baseline of 14%.

## Root Cause Analysis
Metallurgical analysis conducted at Orchard Materials Lab in Cupertino identified chemical cathode contamination in battery cells manufactured at Supplier Plant B in Shenzhen under production lot `BP-2025-08`. Under high ambient temperatures in APAC and fast-charging conditions, the contaminated electrolyte experienced microscopic dendritic formation leading to thermal resistance increases and battery pouch expansion.

## Resolution & Remediation
1. **Supplier Quarantine**: Lot `BP-2025-08` was isolated and purged from worldwide inventory on August 22, 2025.
2. **Genius Bar Service Program**: Free same-day battery module replacement authorized for all affected serial ranges.
3. **Data Quality Note**: In the data warehouse, `fact_support_claims` records associated with this incident are tagged with `component_batch_id = 'BP-2025-08'`.
""",
        "2025-q2-emea-marketing-cut-sales-impact": """# Incident Postmortem: EMEA Q2 2025 Marketing Spend Slump & Retail Contraction

## Incident Summary
- **Incident ID**: INC-2025-0428-EMEA
- **Date Range**: April 1, 2025 – June 30, 2025 (FY2025-Q3 / Calendar Q2)
- **Impacted Entity**: EMEA Retail Channel
- **Impacted Region**: `EMEA` (UK, Germany, France, Italy)
- **Severity**: P2 - Commercial Performance Anomaly

## Background & Decision
During executive budgeting in March 2025, global marketing leadership approved an extraordinary reallocation of $1.8M in regional marketing funds from EMEA Paid Social and Digital Search to fund title sponsorship of the North American Worldwide Pear Developers Conference (WWPC 2025).

## Observed Impact
As a consequence of the 65% reduction in digital acquisition spend across EMEA, physical retail store foot traffic fell by 31%, resulting in a quarterly retail net revenue drop of ~24% compared to Q1 2025 and 22% YoY. Online store direct sales also dropped 16%.

## Key Finding for Analytics
When querying `fact_sales` and `fact_marketing_spend` for EMEA in 2025, the sharp sales downturn in months 4, 5, and 6 directly correlates with the collapse in `spend_usd` in `fact_marketing_spend`.
""",
        "2025-q4-amer-pearwatch-ultra-attach-surge": """# Commercial Review: AMER Q4 2025 PearWatch Ultra 2 Holiday Attach Surge

## Initiative Summary
- **Program Name**: "Orchard Adventure Pro" Holiday Bundle Promotion
- **Date Range**: October 1, 2025 – December 31, 2025 (FY2026-Q1 / Calendar Q4)
- **Target Products**: `PRD-PHN-16P` (PearPhone 16 Pro) and `PRD-WCH-ULT2` (PearWatch Ultra 2)
- **Target Region**: `AMER`

## Campaign Mechanics
Customers purchasing a PearPhone 16 Pro in Orchard Retail Stores or Orchard Online Store received an instant $150 credit towards the purchase of a PearWatch Ultra 2.

## Results & Attach Rate Metrics
- **Historical Baseline Attach Rate**: 12.8%
- **Q4 2025 Observed Attach Rate**: **41.2%**
- **Net Incremental Units**: Over 18,000 incremental PearWatch Ultra 2 units sold in AMER during Q4.
- **Gross Margin Impact**: Despite the $150 credit, the bundle delivered a 14% lift in total gross margin dollar contribution per transaction.
""",
        "2025-q1-pearbook-display-flicker-returns": """# Incident Postmortem: PearBook Pro 16\" Q1 2025 Display Flicker Return Surge

## Incident Summary
- **Incident ID**: INC-2025-0118-PEARBOOK
- **Date Range**: January 15, 2025 – February 28, 2025
- **Impacted Product**: `PRD-NBK-16P` (PearBook Pro 16\")
- **Defect Category**: Hardware/Firmware Compatibility (`Defective / Hardware Issue`)

## Root Cause
On January 12, 2025, Orchard released PearOS firmware update v14.2. A regression in the DisplayPort 2.1 DSC (Display Stream Compression) clock synchronization PLL caused periodic horizontal screen flickering and momentary blackouts when connected to high-resolution external monitors (including PearStudio Display).

## Customer & Return Impact
Believing the issue to be a discrete GPU solder failure, customers returned units at elevated rates. In `fact_returns`, return rates for `PRD-NBK-16P` rose from 2.1% to 8.4% during late January and February.

## Remediation
PearOS firmware hotfix v14.2.1 was released over-the-air on February 24, 2025, resolving the clock timing issue. Return rates normalized to 2.2% by mid-March.
""",
    }

    for name, content in postmortems.items():
        (docs_dir / "incident_postmortems" / f"{name}.md").write_text(content, encoding="utf-8")
        docs_created += 1

    # 4. Data Quality & Governance (4 docs)
    quality_docs = {
        "dq_rules_and_freshness": """# Data Quality Standards & Warehouse Freshness

## Ingestion SLAs
- `fact_sales`: Partitioned Parquet batches updated hourly; daily close reconciled at 02:00 UTC.
- `fact_support_claims`: Genius Bar warranty claims synchronized every 4 hours.
- Freshness threshold: Alerts fire if `MAX(date_id)` is older than 24 hours in production.

## Completeness & Null Rules
- Zero tolerance (0.0% nulls) on primary keys (`sale_id`, `product_id`, `date_id`, `customer_id`).
- Referential integrity: 100% of foreign keys in fact tables must resolve to corresponding dimension tables.
""",
        "pii_governance_standards": """# Data Governance & PII Classification Policy

## Regulated Data Classifications
1. **Public**: Product names, MSRP, store locations, regional tax rates.
2. **Internal**: Unit sales volumes, marketing spend by channel, internal repair costs.
3. **Restricted PII**: Customer full names, residential addresses, phone numbers, email addresses.

## Role-Based Access Control (RBAC)
- **Role `analyst`**: Restricted PII fields (`first_name`, `last_name`, `email`, `phone`, `street_address`) MUST be masked using SHA-256 hash or `***MASKED***`. Query row limit capped at 1,000 rows.
- **Role `finance`**: PII masked; full access to revenue, margins, and financial reconciliation ledgers.
- **Role `admin`**: Unmasked access with comprehensive query auditing in `audit_log`.
""",
        "anomaly_thresholds": """# Statistical Anomaly Detection Thresholds

## Monitored Metrics
- **Claims Frequency**: Anomaly flagged if weekly claims per product exceed $\\mu + 3\\sigma$.
- **Return Rate**: Anomaly flagged if weekly return percentage exceeds $4.0\\%$.
- **Revenue Volatility**: Anomaly flagged if period-over-period variance exceeds $\\pm 25\\%$ without a registered holiday or launch event.
""",
        "sla_definitions": """# Enterprise Analytics SLA Definitions

## Response Time Targets
- Natural Language Query Plan: < 1.5 seconds
- DuckDB Parquet Scan (< 10M rows): < 450 milliseconds
- End-to-end Agent Response (Narrative + Chart Spec + SQL): < 3.5 seconds
""",
    }

    for name, content in quality_docs.items():
        (docs_dir / "data_quality" / f"{name}.md").write_text(content, encoding="utf-8")
        docs_created += 1

    # 5. Metrics Catalog (3 docs)
    catalog_docs = {
        "sales_and_revenue_metrics": """# Metrics Catalog: Sales & Revenue

## Available Metrics
1. **Total Net Revenue**: `SUM(net_revenue)` from `fact_sales`
2. **Gross Margin Dollar**: `SUM(gross_margin)` from `fact_sales`
3. **Gross Margin Percentage**: `SUM(gross_margin) * 100.0 / NULLIF(SUM(net_revenue), 0)`
4. **Units Sold**: `SUM(units)` from `fact_sales`
5. **Average Selling Price (ASP)**: `SUM(net_revenue) * 1.0 / NULLIF(SUM(units), 0)`
""",
        "support_and_warranty_metrics": """# Metrics Catalog: Support & Warranty

## Available Metrics
1. **Total Support Claims**: `COUNT(*)` from `fact_support_claims`
2. **Battery Claims Ratio**: `COUNT(CASE WHEN claim_type = 'Battery Degradation/Thermal' THEN 1 END) * 100.0 / COUNT(*)`
3. **Average Turnaround Time**: `AVG(turnaround_days)` from `fact_support_claims`
4. **Total Internal Repair Cost**: `SUM(repair_cost)` from `fact_support_claims`
""",
        "marketing_efficiency_metrics": """# Metrics Catalog: Marketing Efficiency

## Available Metrics
1. **Total Marketing Spend**: `SUM(spend_usd)` from `fact_marketing_spend`
2. **Cost Per Click (CPC)**: `SUM(spend_usd) * 1.0 / NULLIF(SUM(clicks), 0)`
3. **Conversion Rate (CVR)**: `SUM(conversions) * 100.0 / NULLIF(SUM(clicks), 0)`
4. **Blended Customer Acquisition Cost**: `SUM(spend_usd) * 1.0 / NULLIF(SUM(conversions), 0)`
""",
    }

    for name, content in catalog_docs.items():
        (docs_dir / "metrics_catalog" / f"{name}.md").write_text(content, encoding="utf-8")
        docs_created += 1

    return docs_created


def generate_support_tickets(
    output_dir: Path,
    num_tickets: int = 5000,
    seed: int = 42,
) -> Path:
    """Generate ~5,000 synthetic customer support tickets with injected story correlations."""
    rng = np.random.RandomState(seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    general_subjects = [
        ("Screen cracked after drop", "I accidentally dropped my phone on concrete and the glass shattered.", "Display/Glass Crack"),
        ("Battery draining faster than normal", "My device battery drops from 100% to 20% in just 3 hours without heavy use.", "Battery Degradation/Thermal"),
        ("Device will not turn on", "My laptop died yesterday and won't boot up even when connected to the MagSafe charger.", "Logic Board Failure"),
        ("Audio distortion during calls", "The speaker crackles whenever someone speaks at medium or high volume.", "Audio"),
        ("Trade-in inquiry", "Checking status of my trade-in credit for my previous device.", "Billing"),
        ("Accidental liquid spill", "Spilled some coffee near the keyboard; now spacebar is sticky.", "Water Ingress"),
        ("Bluetooth pairing drops", "My headphones keep disconnecting intermittently during outdoor runs.", "Connectivity"),
    ]

    tickets = []

    # Scale injected tickets proportionally to total tickets
    story_1_count = max(5, int(num_tickets * 0.09))
    story_4_count = max(3, int(num_tickets * 0.05))

    # Inject tickets for Story 1: APAC Q3 2025 Battery Degradation (BP-2025-08)
    for i in range(story_1_count):
        t_id = f"TCK-APAC-2025-{10000 + i}"
        m = rng.choice([7, 8, 9])
        d = rng.randint(1, 28)
        created_at = f"2025-{m:02d}-{d:02d}T{rng.randint(8, 20):02d}:{rng.randint(10, 59):02d}:00Z"
        tickets.append({
            "ticket_id": t_id,
            "created_at": created_at,
            "customer_id": f"CUST-{rng.randint(100000, 199999)}",
            "product_id": "PRD-PHN-16P",
            "region_id": "APAC",
            "channel": rng.choice(["Genius Bar In-Store", "OrchardCare Phone Support", "Online Chat"]),
            "category": "Hardware / Battery Thermal",
            "subject": "PearPhone 16 Pro overheating and rapid battery swelling",
            "customer_comment": (
                "My PearPhone 16 Pro gets burning hot to the touch while charging and the back casing is bulging slightly. "
                "I bought this in Singapore last month. Battery health dropped to 71% within 4 weeks."
            ),
            "agent_notes": (
                "Customer presented unit with severe battery swelling. Diagnostic confirmed thermal safety throttle. "
                "Component batch tag identified as BP-2025-08. Swapped under safety recall guidance."
            ),
            "component_batch_id": "BP-2025-08",
            "sentiment": "Negative",
            "status": "Resolved - Replaced",
        })

    # Inject tickets for Story 4: PearBook Pro 16" display flicker after v14.2 in Jan/Feb 2025
    for i in range(story_4_count):
        t_id = f"TCK-NBK-2025-{20000 + i}"
        m = rng.choice([1, 2])
        d = rng.randint(15, 28) if m == 1 else rng.randint(1, 25)
        created_at = f"2025-{m:02d}-{d:02d}T{rng.randint(8, 20):02d}:{rng.randint(10, 59):02d}:00Z"
        tickets.append({
            "ticket_id": t_id,
            "created_at": created_at,
            "customer_id": f"CUST-{rng.randint(100000, 199999)}",
            "product_id": "PRD-NBK-16P",
            "region_id": rng.choice(["AMER", "EMEA", "APAC"]),
            "channel": rng.choice(["Online Chat", "Genius Bar In-Store"]),
            "category": "Display / Firmware Bug",
            "subject": "External monitor flickering and blackout on PearBook Pro 16\"",
            "customer_comment": (
                "Ever since updating to PearOS v14.2 last week, my external 6K display flickers continuously and goes black every 4 minutes. "
                "Unusable for video editing."
            ),
            "agent_notes": (
                "Known issue with DisplayPort handshake timing under v14.2. Advised customer on forthcoming v14.2.1 patch. Customer requested hardware return."
            ),
            "component_batch_id": "N/A",
            "sentiment": "Frustrated",
            "status": "Return Initiated",
        })

    # Fill remaining tickets up to num_tickets with general realistic tickets
    remaining = max(0, num_tickets - len(tickets))
    products = [p.product_id for p in ORCHARD_PRODUCTS]
    regions = [r["region_id"] for r in REGIONS]

    for i in range(remaining):
        t_id = f"TCK-GEN-2025-{30000 + i}"
        subj, comment, cat = general_subjects[rng.randint(len(general_subjects))]
        p_id = rng.choice(products)
        reg_id = rng.choice(regions)
        y = rng.choice([2024, 2025])
        m = rng.randint(1, 13)
        d = rng.randint(1, 29)
        created_at = f"{y}-{m:02d}-{d:02d}T{rng.randint(8, 20):02d}:{rng.randint(10, 59):02d}:00Z"

        tickets.append({
            "ticket_id": t_id,
            "created_at": created_at,
            "customer_id": f"CUST-{rng.randint(100000, 199999)}",
            "product_id": p_id,
            "region_id": reg_id,
            "channel": rng.choice(["Online Chat", "Phone Support", "Genius Bar"]),
            "category": cat,
            "subject": subj,
            "customer_comment": comment,
            "agent_notes": f"Standard triage completed. Diagnostics run. Status updated for {p_id}.",
            "component_batch_id": "N/A",
            "sentiment": rng.choice(["Neutral", "Negative", "Satisfied"], p=[0.5, 0.35, 0.15]),
            "status": rng.choice(["Resolved", "In Progress", "Closed"]),
        })

    # Save to JSONL
    jsonl_path = output_dir / "support_tickets.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for t in tickets:
            f.write(json.dumps(t) + "\n")

    # Save to Parquet
    parquet_path = output_dir / "support_tickets.parquet"
    table = pa.Table.from_pylist(tickets)
    pq.write_table(table, parquet_path, compression="snappy")

    return jsonl_path
