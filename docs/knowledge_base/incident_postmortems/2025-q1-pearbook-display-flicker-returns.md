# Incident Postmortem: PearBook Pro 16" Q1 2025 Display Flicker Return Surge

## Incident Summary
- **Incident ID**: INC-2025-0118-PEARBOOK
- **Date Range**: January 15, 2025 – February 28, 2025
- **Impacted Product**: `PRD-NBK-16P` (PearBook Pro 16")
- **Defect Category**: Hardware/Firmware Compatibility (`Defective / Hardware Issue`)

## Root Cause
On January 12, 2025, Orchard released PearOS firmware update v14.2. A regression in the DisplayPort 2.1 DSC (Display Stream Compression) clock synchronization PLL caused periodic horizontal screen flickering and momentary blackouts when connected to high-resolution external monitors (including PearStudio Display).

## Customer & Return Impact
Believing the issue to be a discrete GPU solder failure, customers returned units at elevated rates. In `fact_returns`, return rates for `PRD-NBK-16P` rose from 2.1% to 8.4% during late January and February.

## Remediation
PearOS firmware hotfix v14.2.1 was released over-the-air on February 24, 2025, resolving the clock timing issue. Return rates normalized to 2.2% by mid-March.
