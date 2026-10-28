# Data Governance & PII Classification Policy

## Regulated Data Classifications
1. **Public**: Product names, MSRP, store locations, regional tax rates.
2. **Internal**: Unit sales volumes, marketing spend by channel, internal repair costs.
3. **Restricted PII**: Customer full names, residential addresses, phone numbers, email addresses.

## Role-Based Access Control (RBAC)
- **Role `analyst`**: Restricted PII fields (`first_name`, `last_name`, `email`, `phone`, `street_address`) MUST be masked using SHA-256 hash or `***MASKED***`. Query row limit capped at 1,000 rows.
- **Role `finance`**: PII masked; full access to revenue, margins, and financial reconciliation ledgers.
- **Role `admin`**: Unmasked access with comprehensive query auditing in `audit_log`.
