# Metrics Catalog: Support & Warranty

## Available Metrics
1. **Total Support Claims**: `COUNT(*)` from `fact_support_claims`
2. **Battery Claims Ratio**: `COUNT(CASE WHEN claim_type = 'Battery Degradation/Thermal' THEN 1 END) * 100.0 / COUNT(*)`
3. **Average Turnaround Time**: `AVG(turnaround_days)` from `fact_support_claims`
4. **Total Internal Repair Cost**: `SUM(repair_cost)` from `fact_support_claims`
