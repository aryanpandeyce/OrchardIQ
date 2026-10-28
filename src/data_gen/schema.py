"""Schema definitions, product catalogs, and dimension structures for OrchardIQ."""

from dataclasses import dataclass
from typing import List, Dict, Any
import pyarrow as pa


@dataclass(frozen=True)
class ProductInfo:
    product_id: str
    product_name: str
    category: str
    product_line: str
    price_usd: float
    cost_usd: float
    launch_date: str
    warranty_months: int
    status: str = "Active"


# Orchard Inc. Portfolio Catalog
ORCHARD_PRODUCTS: List[ProductInfo] = [
    ProductInfo("PRD-PHN-16PM", "PearPhone 16 Pro Max", "Smartphone", "Pro", 1199.00, 485.00, "2024-09-20", 12),
    ProductInfo("PRD-PHN-16P", "PearPhone 16 Pro", "Smartphone", "Pro", 999.00, 415.00, "2024-09-20", 12),
    ProductInfo("PRD-PHN-16", "PearPhone 16", "Smartphone", "Standard", 799.00, 320.00, "2024-09-20", 12),
    ProductInfo("PRD-PHN-15P", "PearPhone 15 Pro", "Smartphone", "Pro", 899.00, 390.00, "2023-09-22", 12),
    ProductInfo("PRD-PHN-15", "PearPhone 15", "Smartphone", "Standard", 699.00, 290.00, "2023-09-22", 12),
    ProductInfo("PRD-NBK-16P", "PearBook Pro 16\"", "Laptop", "Pro", 2499.00, 1050.00, "2023-11-07", 12),
    ProductInfo("PRD-NBK-14P", "PearBook Pro 14\"", "Laptop", "Pro", 1999.00, 850.00, "2023-11-07", 12),
    ProductInfo("PRD-NBK-AIR", "PearBook Air 15\"", "Laptop", "Air", 1299.00, 520.00, "2024-03-08", 12),
    ProductInfo("PRD-PAD-13P", "PearPad Pro 13\"", "Tablet", "Pro", 1299.00, 490.00, "2024-05-15", 12),
    ProductInfo("PRD-PAD-AIR", "PearPad Air 11\"", "Tablet", "Air", 599.00, 240.00, "2024-05-15", 12),
    ProductInfo("PRD-WCH-ULT2", "PearWatch Ultra 2", "Wearables", "Ultra", 799.00, 295.00, "2023-09-22", 24),
    ProductInfo("PRD-WCH-S10", "PearWatch Series 10", "Wearables", "Standard", 399.00, 155.00, "2024-09-20", 12),
    ProductInfo("PRD-AUD-PRO2", "PearPods Pro 2", "Audio", "Pro", 249.00, 85.00, "2023-09-22", 12),
    ProductInfo("PRD-ACC-MAGS", "PearCharge MagSafe Trio", "Accessories", "Standard", 129.00, 35.00, "2023-10-01", 12),
]

REGIONS: List[Dict[str, Any]] = [
    {
        "region_id": "AMER",
        "region_name": "Americas",
        "headquarters_city": "Cupertino, CA",
        "currency": "USD",
        "tax_rate_standard": 0.0825,
    },
    {
        "region_id": "EMEA",
        "region_name": "Europe, Middle East & Africa",
        "headquarters_city": "London, UK",
        "currency": "EUR",
        "tax_rate_standard": 0.2000,
    },
    {
        "region_id": "APAC",
        "region_name": "Asia-Pacific",
        "headquarters_city": "Singapore",
        "currency": "USD",
        "tax_rate_standard": 0.0900,
    },
    {
        "region_id": "LATAM",
        "region_name": "Latin America",
        "headquarters_city": "São Paulo, Brazil",
        "currency": "USD",
        "tax_rate_standard": 0.1200,
    },
]

RETURN_REASONS = [
    "Defective / Hardware Issue",
    "Buyer Remorse",
    "Wrong Size / Spec",
    "Software Incompatibility",
    "Gift Exchange",
]

CLAIM_TYPES = [
    "Battery Degradation/Thermal",
    "Display/Glass Crack",
    "Logic Board Failure",
    "Water Ingress",
    "Camera Sensor Fault",
]

CLAIM_STATUSES = [
    "Approved & Replaced",
    "Repaired In-Store",
    "Declined Out-of-Warranty",
    "Under Diagnostic Review",
]

MARKETING_CHANNELS = [
    "Digital Search",
    "Paid Social",
    "Broadcast TV & Cinema",
    "Out of Home (OOH)",
    "Keynote Event / PR",
]

CUSTOMER_SEGMENTS = ["Consumer", "Enterprise", "Education", "Small Business"]

# PyArrow Schemas for Star Schema Tables
SCHEMA_DIM_PRODUCT = pa.schema([
    ("product_id", pa.string()),
    ("product_name", pa.string()),
    ("category", pa.string()),
    ("product_line", pa.string()),
    ("price_usd", pa.float64()),
    ("cost_usd", pa.float64()),
    ("launch_date", pa.date32()),
    ("warranty_months", pa.int32()),
    ("status", pa.string()),
])

SCHEMA_DIM_REGION = pa.schema([
    ("region_id", pa.string()),
    ("region_name", pa.string()),
    ("headquarters_city", pa.string()),
    ("currency", pa.string()),
    ("tax_rate_standard", pa.float64()),
])

SCHEMA_DIM_STORE = pa.schema([
    ("store_id", pa.string()),
    ("store_name", pa.string()),
    ("channel", pa.string()),
    ("city", pa.string()),
    ("state_province", pa.string()),
    ("country", pa.string()),
    ("region_id", pa.string()),
    ("square_feet", pa.int32()),
    ("opened_date", pa.date32()),
])

SCHEMA_DIM_CUSTOMER = pa.schema([
    ("customer_id", pa.string()),
    ("first_name", pa.string()),
    ("last_name", pa.string()),
    ("email", pa.string()),
    ("phone", pa.string()),
    ("street_address", pa.string()),
    ("city", pa.string()),
    ("country", pa.string()),
    ("region_id", pa.string()),
    ("customer_segment", pa.string()),
    ("signup_date", pa.date32()),
])

SCHEMA_DIM_DATE = pa.schema([
    ("date_id", pa.int32()),
    ("full_date", pa.date32()),
    ("day_of_week", pa.int32()),
    ("day_name", pa.string()),
    ("day_of_month", pa.int32()),
    ("month_number", pa.int32()),
    ("month_name", pa.string()),
    ("calendar_quarter", pa.string()),
    ("calendar_year", pa.int32()),
    ("fiscal_quarter", pa.string()),
    ("fiscal_year", pa.int32()),
    ("is_weekend", pa.bool_()),
    ("is_holiday", pa.bool_()),
    ("holiday_name", pa.string()),
])

SCHEMA_FACT_SALES = pa.schema([
    ("sale_id", pa.string()),
    ("date_id", pa.int32()),
    ("customer_id", pa.string()),
    ("product_id", pa.string()),
    ("store_id", pa.string()),
    ("region_id", pa.string()),
    ("channel", pa.string()),
    ("units", pa.int32()),
    ("unit_price", pa.float64()),
    ("discount_amount", pa.float64()),
    ("gross_revenue", pa.float64()),
    ("net_revenue", pa.float64()),
    ("cogs", pa.float64()),
    ("gross_margin", pa.float64()),
    ("tax_amount", pa.float64()),
    ("year", pa.int32()),
    ("month", pa.int32()),
])

SCHEMA_FACT_RETURNS = pa.schema([
    ("return_id", pa.string()),
    ("sale_id", pa.string()),
    ("date_id", pa.int32()),
    ("customer_id", pa.string()),
    ("product_id", pa.string()),
    ("store_id", pa.string()),
    ("region_id", pa.string()),
    ("return_reason", pa.string()),
    ("units", pa.int32()),
    ("refund_amount", pa.float64()),
    ("restock_status", pa.string()),
    ("year", pa.int32()),
    ("month", pa.int32()),
])

SCHEMA_FACT_SUPPORT_CLAIMS = pa.schema([
    ("claim_id", pa.string()),
    ("date_id", pa.int32()),
    ("customer_id", pa.string()),
    ("product_id", pa.string()),
    ("store_id", pa.string()),
    ("region_id", pa.string()),
    ("claim_type", pa.string()),
    ("claim_status", pa.string()),
    ("repair_cost", pa.float64()),
    ("customer_deductible", pa.float64()),
    ("turnaround_days", pa.int32()),
    ("component_batch_id", pa.string()),
    ("year", pa.int32()),
    ("month", pa.int32()),
])

SCHEMA_FACT_FINANCE_REVENUE = pa.schema([
    ("finance_entry_id", pa.string()),
    ("date_id", pa.int32()),
    ("fiscal_quarter", pa.string()),
    ("fiscal_year", pa.int32()),
    ("region_id", pa.string()),
    ("product_line", pa.string()),
    ("recognized_net_revenue", pa.float64()),
    ("deferred_services_revenue", pa.float64()),
    ("total_gaap_revenue", pa.float64()),
    ("operating_margin", pa.float64()),
])

SCHEMA_FACT_MARKETING_SPEND = pa.schema([
    ("spend_id", pa.string()),
    ("date_id", pa.int32()),
    ("region_id", pa.string()),
    ("product_id", pa.string()),
    ("channel", pa.string()),
    ("spend_usd", pa.float64()),
    ("impressions", pa.int64()),
    ("clicks", pa.int64()),
    ("conversions", pa.int64()),
    ("year", pa.int32()),
    ("month", pa.int32()),
])
