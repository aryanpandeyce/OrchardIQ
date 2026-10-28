# ADR 0003: Synthetic Star-Schema Design & Ground-Truth Story Injection

## Status
Accepted

## Date
2026-10-28

## Context
OrchardIQ requires realistic, high-fidelity data modeling that reflects a global consumer hardware enterprise (Orchard Inc.). The data warehouse must demonstrate:
1. Production dimensional modeling standards (Kimball star schema with conformed dimensions).
2. Realistic business dynamics: seasonal holiday spikes (Q4), fall hardware launch cycles (September), channel differences (Retail vs. Online), and standard corporate fiscal calendars (fiscal year begins October 1st).
3. Ground-truth injected stories and anomalies that enable rigorous evaluation of GenAI agent accuracy and root-cause analysis.
4. Governed PII columns to prove role-based column masking (analyst vs. finance vs. admin).

## Decision
We implement a conformed **Star Schema** across 5 dimensions and 5 fact tables, accompanied by 31 structured knowledge base markdown files and ~5,000 synthetic support tickets.

### Star Schema Architecture
- **Dimensions**:
  - `dim_product`: 14 SKUs across Smartphones, Laptops, Tablets, Wearables, Audio, and Accessories with MSRP and landed manufacturing cost.
  - `dim_store`: 50 retail locations across 4 continents plus 4 regional online flagship stores.
  - `dim_customer`: Customer demographics including PII fields (`first_name`, `last_name`, `email`, `phone`, `street_address`) for role-based governance.
  - `dim_date`: 1,096 dates (2023-2025) with calendar and corporate fiscal calendar attributes (`FY2025-Q1` through `FY2025-Q4`).
  - `dim_region`: 4 global operating theaters (`AMER`, `EMEA`, `APAC`, `LATAM`).
- **Facts**:
  - `fact_sales`: Transactional unit sales, retail discounts, COGS, and gross margin partitioned by `year` and `month`.
  - `fact_returns`: Return events, customer refund values, and disposition reasons.
  - `fact_support_claims`: Extended-warranty claims, component repair costs, turnaround days, and batch tracking.
  - `fact_finance_revenue`: Reconciled monthly ledger entries for GAAP revenue and deferred services.
  - `fact_marketing_spend`: Daily acquisition and keynote campaign expenditures across 5 channels.

### Injected Ground-Truth Stories
1. **Story 1 (APAC Q3 2025 Battery Degradation Spike)**: Defective battery supplier cathode lot `BP-2025-08` in Shenzhen causes a 4.5x surge in PearPhone 16 Pro battery claims in APAC.
2. **Story 2 (EMEA Q2 2025 Marketing Spend Slump)**: Reallocation of regional marketing funds causes a 65% drop in EMEA digital marketing spend, inducing a 25% contraction in retail sales.
3. **Story 3 (AMER Q4 2025 PearWatch Ultra Holiday Attach Surge)**: "Orchard Adventure Pro" promotional credit boosts PearWatch Ultra 2 attach rate to PearPhone 16 Pro from 13% to 41%.
4. **Story 4 (PearBook Pro 16" Q1 2025 Display Flicker Returns)**: Firmware patch v14.2 introduces a DisplayPort clock sync bug, driving return rates from 2.1% to 8.5% in Jan/Feb 2025.

## Consequences & Trade-offs
### Positive
- Fully reproducible: Deterministic random seed (`42`) ensures the exact same numerical answers across all test suites, CI pipelines, and demo environments.
- Cross-modal evaluation: Ground truth can be confirmed simultaneously via SQL queries against Parquet and vector search across incident postmortems and support tickets.
- Scalable: The generator supports an arbitrary scaling factor (`--scale 0.02` for fast 2-second test runs, `--scale 1.0` for ~2M production rows).

### Negative / Mitigations
- Synthetic data generation requires local disk space (~250MB for full 2M Parquet dataset). Mitigated by snappy compression and fast scale option in CI.
