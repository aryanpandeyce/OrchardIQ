# Incident Postmortem: APAC Q3 2025 PearPhone 16 Pro Battery Claims Spike

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
