# Business Glossary: Net Revenue

## Definition
Net Revenue represents the total monetary proceeds recognized by Orchard Inc. from the sale of hardware products and accessories, after subtracting commercial discounts, employee concessions, and education promotional allowances from Gross Revenue.

## Business Formula
$$\text{Net Revenue} = \text{Gross Revenue} - \text{Discount Amount}$$
Where:
$$\text{Gross Revenue} = \text{Units Sold} \times \text{Unit Price (MSRP)}$$

## Data Warehouse Source
- **Table**: `fact_sales`
- **Columns**: `net_revenue`, `gross_revenue`, `discount_amount`
- **Aggregation**: `SUM(net_revenue)`

## Governance & Reconciliation
Net Revenue on `fact_sales` is reconciled monthly against `fact_finance_revenue.recognized_net_revenue`. Variances exceeding 0.05% trigger an automated audit event.
