"""High-performance synthetic star-schema data generator for OrchardIQ."""

import os
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from src.data_gen.schema import (
    ORCHARD_PRODUCTS,
    REGIONS,
    RETURN_REASONS,
    CLAIM_TYPES,
    CLAIM_STATUSES,
    MARKETING_CHANNELS,
    CUSTOMER_SEGMENTS,
    SCHEMA_DIM_PRODUCT,
    SCHEMA_DIM_REGION,
    SCHEMA_DIM_STORE,
    SCHEMA_DIM_CUSTOMER,
    SCHEMA_DIM_DATE,
    SCHEMA_FACT_SALES,
    SCHEMA_FACT_RETURNS,
    SCHEMA_FACT_SUPPORT_CLAIMS,
    SCHEMA_FACT_FINANCE_REVENUE,
    SCHEMA_FACT_MARKETING_SPEND,
)


class OrchardWarehouseGenerator:
    """Generates a complete Kimball-style star schema warehouse for Orchard Inc."""

    def __init__(
        self,
        output_dir: Path,
        seed: int = 42,
        scale: float = 1.0,
    ):
        self.output_dir = output_dir
        self.marts_dir = output_dir / "marts"
        self.seed = seed
        self.scale = max(0.005, float(scale))
        self.rng = np.random.RandomState(seed)

    def generate_all(self) -> Dict[str, int]:
        """Generate all dimensions and facts, returning row counts."""
        self.marts_dir.mkdir(parents=True, exist_ok=True)

        counts = {}
        # 1. Dimensions
        counts["dim_product"] = self._generate_dim_product()
        counts["dim_region"] = self._generate_dim_region()
        stores, counts["dim_store"] = self._generate_dim_store()
        customers, counts["dim_customer"] = self._generate_dim_customer()
        dates, counts["dim_date"] = self._generate_dim_date()

        # 2. Facts
        sales_samples, counts["fact_sales"] = self._generate_fact_sales(dates, stores, customers)
        counts["fact_returns"] = self._generate_fact_returns(sales_samples)
        counts["fact_support_claims"] = self._generate_fact_support_claims(dates, customers, stores)
        counts["fact_marketing_spend"] = self._generate_fact_marketing_spend(dates)
        counts["fact_finance_revenue"] = self._generate_fact_finance_revenue(dates)

        return counts

    def _generate_dim_product(self) -> int:
        records = []
        for p in ORCHARD_PRODUCTS:
            records.append({
                "product_id": p.product_id,
                "product_name": p.product_name,
                "category": p.category,
                "product_line": p.product_line,
                "price_usd": float(p.price_usd),
                "cost_usd": float(p.cost_usd),
                "launch_date": datetime.strptime(p.launch_date, "%Y-%m-%d").date(),
                "warranty_months": p.warranty_months,
                "status": p.status,
            })
        table = pa.Table.from_pylist(records, schema=SCHEMA_DIM_PRODUCT)
        out_path = self.marts_dir / "dim_product"
        out_path.mkdir(parents=True, exist_ok=True)
        pq.write_table(table, out_path / "dim_product.parquet")
        return len(records)

    def _generate_dim_region(self) -> int:
        records = []
        for r in REGIONS:
            records.append({
                "region_id": r["region_id"],
                "region_name": r["region_name"],
                "headquarters_city": r["headquarters_city"],
                "currency": r["currency"],
                "tax_rate_standard": float(r["tax_rate_standard"]),
            })
        table = pa.Table.from_pylist(records, schema=SCHEMA_DIM_REGION)
        out_path = self.marts_dir / "dim_region"
        out_path.mkdir(parents=True, exist_ok=True)
        pq.write_table(table, out_path / "dim_region.parquet")
        return len(records)

    def _generate_dim_store(self) -> Tuple[List[Dict[str, Any]], int]:
        stores = []
        # Flagship Online Stores (1 per region)
        for r in REGIONS:
            stores.append({
                "store_id": f"STR-ONL-{r['region_id']}",
                "store_name": f"Orchard Online Store ({r['region_id']})",
                "channel": "Online Store",
                "city": r["headquarters_city"].split(",")[0],
                "state_province": "Digital",
                "country": "International",
                "region_id": r["region_id"],
                "square_feet": 0,
                "opened_date": date(2010, 1, 1),
            })

        # Physical Flagship & Retail Stores
        physical_cities = [
            ("New York", "NY", "United States", "AMER", 18500),
            ("San Francisco", "CA", "United States", "AMER", 16200),
            ("Chicago", "IL", "United States", "AMER", 14500),
            ("Los Angeles", "CA", "United States", "AMER", 15800),
            ("Miami", "FL", "United States", "AMER", 12400),
            ("Toronto", "ON", "Canada", "AMER", 13000),
            ("London", "England", "United Kingdom", "EMEA", 19200),
            ("Paris", "Île-de-France", "France", "EMEA", 14800),
            ("Berlin", "Berlin", "Germany", "EMEA", 13900),
            ("Milan", "Lombardy", "Italy", "EMEA", 12100),
            ("Dubai", "Dubai", "United Arab Emirates", "EMEA", 17500),
            ("Tokyo", "Tokyo", "Japan", "APAC", 18900),
            ("Singapore", "Singapore", "Singapore", "APAC", 15600),
            ("Sydney", "NSW", "Australia", "APAC", 14200),
            ("Seoul", "Seoul", "South Korea", "APAC", 16000),
            ("Hong Kong", "Hong Kong", "Hong Kong", "APAC", 15100),
            ("São Paulo", "SP", "Brazil", "LATAM", 11500),
            ("Mexico City", "CDMX", "Mexico", "LATAM", 12800),
            ("Santiago", "Santiago", "Chile", "LATAM", 9800),
            ("Bogotá", "Cundinamarca", "Colombia", "LATAM", 9200),
        ]

        store_idx = 1
        for city, state, country, region, sqft in physical_cities:
            # 1-3 stores per city
            num_in_city = 2 if city in ["New York", "London", "Tokyo"] else 1
            for k in range(num_in_city):
                s_name = f"Orchard {city} {'Central' if k == 0 else 'West'}"
                stores.append({
                    "store_id": f"STR-RET-{store_idx:03d}",
                    "store_name": s_name,
                    "channel": "Retail Store",
                    "city": city,
                    "state_province": state,
                    "country": country,
                    "region_id": region,
                    "square_feet": sqft + (k * 1200),
                    "opened_date": date(2015 + (store_idx % 8), (store_idx % 12) + 1, 15),
                })
                store_idx += 1

        table = pa.Table.from_pylist(stores, schema=SCHEMA_DIM_STORE)
        out_path = self.marts_dir / "dim_store"
        out_path.mkdir(parents=True, exist_ok=True)
        pq.write_table(table, out_path / "dim_store.parquet")
        return stores, len(stores)

    def _generate_dim_customer(self) -> Tuple[List[Dict[str, Any]], int]:
        # Scale customers from 2,000 in fast test mode up to 100,000
        num_customers = int(max(1000, 100000 * self.scale))
        first_names = ["James", "Emma", "Liam", "Olivia", "Noah", "Sophia", "Lucas", "Mia", "Alexander", "Isabella", "Chen", "Wei", "Yuki", "Kenji", "Mateo", "Camila", "Elena", "Lucas", "Hans", "Chloe"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Tanaka", "Sato", "Wong", "Zhang", "Silva", "Santos", "Mueller", "Dubois", "Rossi", "Martin", "Clark", "Lewis"]
        cities_by_region = {
            "AMER": [("San Jose", "United States"), ("Seattle", "United States"), ("Austin", "United States"), ("Boston", "United States")],
            "EMEA": [("Munich", "Germany"), ("Manchester", "United Kingdom"), ("Lyon", "France"), ("Zurich", "Switzerland")],
            "APAC": [("Osaka", "Japan"), ("Brisbane", "Australia"), ("Incheon", "South Korea"), ("Auckland", "New Zealand")],
            "LATAM": [("Rio de Janeiro", "Brazil"), ("Guadalajara", "Mexico"), ("Medellín", "Colombia"), ("Lima", "Peru")],
        }

        customers = []
        regions = ["AMER", "EMEA", "APAC", "LATAM"]
        reg_weights = [0.45, 0.25, 0.22, 0.08]

        for i in range(num_customers):
            c_id = f"CUST-{100000 + i}"
            fn = first_names[self.rng.randint(len(first_names))]
            ln = last_names[self.rng.randint(len(last_names))]
            reg = self.rng.choice(regions, p=reg_weights)
            city_pair = cities_by_region[reg][self.rng.randint(len(cities_by_region[reg]))]
            email = f"{fn.lower()}.{ln.lower()}{i % 997}@example.com"
            phone = f"+1-{self.rng.randint(200, 999)}-555-{self.rng.randint(1000, 9999)}"
            addr = f"{self.rng.randint(10, 9999)} Orchard Way"
            seg = self.rng.choice(CUSTOMER_SEGMENTS, p=[0.70, 0.15, 0.10, 0.05])
            signup = date(2021 + (i % 4), (i % 12) + 1, (i % 28) + 1)

            customers.append({
                "customer_id": c_id,
                "first_name": fn,
                "last_name": ln,
                "email": email,
                "phone": phone,
                "street_address": addr,
                "city": city_pair[0],
                "country": city_pair[1],
                "region_id": reg,
                "customer_segment": seg,
                "signup_date": signup,
            })

        table = pa.Table.from_pylist(customers, schema=SCHEMA_DIM_CUSTOMER)
        out_path = self.marts_dir / "dim_customer"
        out_path.mkdir(parents=True, exist_ok=True)
        pq.write_table(table, out_path / "dim_customer.parquet")
        return customers, len(customers)

    def _generate_dim_date(self) -> Tuple[List[Dict[str, Any]], int]:
        # 3 complete years: 2023-01-01 to 2025-12-31
        start_date = date(2023, 1, 1)
        end_date = date(2025, 12, 31)
        cur = start_date
        dates = []

        holidays = {
            (1, 1): "New Year's Day",
            (7, 4): "Independence Day",
            (11, 28): "Thanksgiving Day",
            (11, 29): "Black Friday",
            (12, 1): "Cyber Monday",
            (12, 24): "Christmas Eve",
            (12, 25): "Christmas Day",
            (12, 31): "New Year's Eve",
        }

        while cur <= end_date:
            d_id = cur.year * 10000 + cur.month * 100 + cur.day
            dow = cur.isoweekday()
            day_name = cur.strftime("%A")
            month_name = cur.strftime("%B")
            cal_quarter = f"{cur.year}-Q{(cur.month - 1) // 3 + 1}"

            # Orchard Fiscal Calendar: Oct 1 starts next FY
            if cur.month >= 10:
                f_year = cur.year + 1
                f_q = "FY" + str(f_year) + "-Q1"
            elif cur.month <= 3:
                f_year = cur.year
                f_q = "FY" + str(f_year) + "-Q2"
            elif cur.month <= 6:
                f_year = cur.year
                f_q = "FY" + str(f_year) + "-Q3"
            else:
                f_year = cur.year
                f_q = "FY" + str(f_year) + "-Q4"

            is_weekend = dow in (6, 7)
            h_name = holidays.get((cur.month, cur.day), None)
            is_holiday = h_name is not None

            dates.append({
                "date_id": d_id,
                "full_date": cur,
                "day_of_week": dow,
                "day_name": day_name,
                "day_of_month": cur.day,
                "month_number": cur.month,
                "month_name": month_name,
                "calendar_quarter": cal_quarter,
                "calendar_year": cur.year,
                "fiscal_quarter": f_q,
                "fiscal_year": f_year,
                "is_weekend": is_weekend,
                "is_holiday": is_holiday,
                "holiday_name": h_name or "",
            })
            cur += timedelta(days=1)

        table = pa.Table.from_pylist(dates, schema=SCHEMA_DIM_DATE)
        out_path = self.marts_dir / "dim_date"
        out_path.mkdir(parents=True, exist_ok=True)
        pq.write_table(table, out_path / "dim_date.parquet")
        return dates, len(dates)

    def _generate_fact_sales(
        self,
        dates: List[Dict[str, Any]],
        stores: List[Dict[str, Any]],
        customers: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Generate partitioned fact_sales, incorporating seasonal trends and Story 2 & 3 injections."""
        product_map = {p.product_id: p for p in ORCHARD_PRODUCTS}
        p_ids = [p.product_id for p in ORCHARD_PRODUCTS]
        p_weights = [
            0.20, 0.18, 0.12,  # 16PM, 16P, 16
            0.05, 0.04,        # 15P, 15
            0.06, 0.05, 0.07,  # NBK 16P, 14P, AIR
            0.05, 0.04,        # PAD 13P, AIR
            0.04, 0.05,        # WCH ULT2, S10
            0.03, 0.02,        # AUD PRO2, ACC MAGS
        ]
        # Normalize weights
        p_weights = np.array(p_weights) / sum(p_weights)

        # Pre-group stores by region
        stores_by_region = {}
        for s in stores:
            stores_by_region.setdefault(s["region_id"], []).append(s)

        # Scale target: ~1,600,000 sales rows at scale=1.0
        total_sales_target = int(max(2000, 1600000 * self.scale))
        rows_per_date = max(2, total_sales_target // len(dates))

        total_rows = 0
        sales_samples_for_returns = []
        sale_counter = 1

        # We will write partitioned Parquet by year and month
        out_base = self.marts_dir / "fact_sales"
        out_base.mkdir(parents=True, exist_ok=True)

        # Group dates by (year, month)
        date_groups: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}
        for d in dates:
            key = (d["calendar_year"], d["month_number"])
            date_groups.setdefault(key, []).append(d)

        num_customers = len(customers)

        for (year, month), m_dates in date_groups.items():
            month_records = []

            # Seasonal Multipliers
            # Q4 holiday lift (Nov/Dec)
            season_mult = 1.6 if month in (11, 12) else (1.4 if month == 9 else 1.0)

            # Story 2: EMEA sales slump in Q2 2025 (months 4, 5, 6)
            is_emea_slump = (year == 2025 and month in (4, 5, 6))

            for d_info in m_dates:
                d_id = d_info["date_id"]
                day_sales_count = int(rows_per_date * season_mult)
                if d_info["is_weekend"]:
                    day_sales_count = int(day_sales_count * 1.25)
                if d_info["is_holiday"]:
                    day_sales_count = int(day_sales_count * 1.5)

                for _ in range(day_sales_count):
                    # Customer selection
                    cust = customers[self.rng.randint(num_customers)]
                    region = cust["region_id"]

                    # Story 2 drop for EMEA
                    if is_emea_slump and region == "EMEA" and self.rng.rand() < 0.28:
                        continue  # 28% drop in sales volume due to lack of marketing

                    # Product selection
                    p_id = self.rng.choice(p_ids, p=p_weights)
                    prod = product_map[p_id]

                    # Store selection
                    avail_stores = stores_by_region.get(region, stores)
                    store = avail_stores[self.rng.randint(len(avail_stores))]
                    channel = "Online" if store["channel"] == "Online Store" else "Retail"

                    units = 1 if self.rng.rand() > 0.08 else 2
                    price = prod.price_usd
                    cost = prod.cost_usd
                    tax_rate = 0.0825 if region == "AMER" else (0.20 if region == "EMEA" else 0.09)

                    # Discount (education / promo)
                    discount = (price * 0.10 * units) if (cust["customer_segment"] == "Education" and self.rng.rand() < 0.7) else 0.0
                    gross_rev = round(price * units, 2)
                    net_rev = round(gross_rev - discount, 2)
                    cogs = round(cost * units, 2)
                    gross_margin = round(net_rev - cogs, 2)
                    tax = round(net_rev * tax_rate, 2)

                    sale_id = f"SAL-{year}-{sale_counter:07d}"
                    sale_counter += 1

                    row = {
                        "sale_id": sale_id,
                        "date_id": d_id,
                        "customer_id": cust["customer_id"],
                        "product_id": p_id,
                        "store_id": store["store_id"],
                        "region_id": region,
                        "channel": channel,
                        "units": units,
                        "unit_price": price,
                        "discount_amount": discount,
                        "gross_revenue": gross_rev,
                        "net_revenue": net_rev,
                        "cogs": cogs,
                        "gross_margin": gross_margin,
                        "tax_amount": tax,
                        "year": year,
                        "month": month,
                    }
                    month_records.append(row)

                    # Keep a sample for returns generation (adaptive sample rate)
                    sample_rate = min(1.0, 0.20 / max(0.01, self.scale))
                    if self.rng.rand() < sample_rate:
                        sales_samples_for_returns.append(row)

                    # Story 3 Injection: AMER Q4 2025 PearWatch Ultra 2 Holiday Attach Surge
                    # When PearPhone 16 Pro is bought in AMER Q4 2025, inject paired PearWatch Ultra 2 sale ~41% of time
                    if (
                        year == 2025 and month in (10, 11, 12)
                        and region == "AMER"
                        and p_id == "PRD-PHN-16P"
                        and self.rng.rand() < 0.41
                    ):
                        watch_prod = product_map["PRD-WCH-ULT2"]
                        watch_discount = 150.0  # $150 bundle credit
                        w_gross = watch_prod.price_usd
                        w_net = round(w_gross - watch_discount, 2)
                        w_cogs = watch_prod.cost_usd
                        w_margin = round(w_net - w_cogs, 2)
                        w_tax = round(w_net * tax_rate, 2)
                        w_sale_id = f"SAL-{year}-{sale_counter:07d}"
                        sale_counter += 1

                        month_records.append({
                            "sale_id": w_sale_id,
                            "date_id": d_id,
                            "customer_id": cust["customer_id"],
                            "product_id": "PRD-WCH-ULT2",
                            "store_id": store["store_id"],
                            "region_id": region,
                            "channel": channel,
                            "units": 1,
                            "unit_price": watch_prod.price_usd,
                            "discount_amount": watch_discount,
                            "gross_revenue": w_gross,
                            "net_revenue": w_net,
                            "cogs": w_cogs,
                            "gross_margin": w_margin,
                            "tax_amount": w_tax,
                            "year": year,
                            "month": month,
                        })

            if month_records:
                partition_dir = out_base / f"year={year}" / f"month={month:02d}"
                partition_dir.mkdir(parents=True, exist_ok=True)
                table = pa.Table.from_pylist(month_records, schema=SCHEMA_FACT_SALES)
                pq.write_table(table, partition_dir / "data.parquet", compression="snappy")
                total_rows += len(month_records)

        return sales_samples_for_returns, total_rows

    def _generate_fact_returns(
        self,
        sales_samples: List[Dict[str, Any]],
    ) -> int:
        """Generate partitioned fact_returns with Story 4 (PearBook Pro flicker return surge) injected."""
        out_base = self.marts_dir / "fact_returns"
        out_base.mkdir(parents=True, exist_ok=True)

        return_counter = 1
        total_returns = 0
        records_by_partition: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}

        for sale in sales_samples:
            p_id = sale["product_id"]
            y = sale["year"]
            m = sale["month"]

            # Story 4: PearBook Pro 16" in Q1 2025 has high return rate
            is_story_4_period = (y == 2025 and m in (1, 2) and p_id == "PRD-NBK-16P")

            return_prob = 0.22 if is_story_4_period else 0.024
            if self.rng.rand() < return_prob:
                if is_story_4_period:
                    reason = "Defective / Hardware Issue"
                else:
                    reason = self.rng.choice(RETURN_REASONS, p=[0.40, 0.25, 0.15, 0.10, 0.10])

                r_id = f"RET-{y}-{return_counter:06d}"
                return_counter += 1

                rec = {
                    "return_id": r_id,
                    "sale_id": sale["sale_id"],
                    "date_id": sale["date_id"],
                    "customer_id": sale["customer_id"],
                    "product_id": sale["product_id"],
                    "store_id": sale["store_id"],
                    "region_id": sale["region_id"],
                    "return_reason": reason,
                    "units": sale["units"],
                    "refund_amount": sale["net_revenue"],
                    "restock_status": self.rng.choice(["Refurbished", "Recycled", "Resold"], p=[0.6, 0.3, 0.1]),
                    "year": y,
                    "month": m,
                }
                key = (y, m)
                records_by_partition.setdefault(key, []).append(rec)

        for (y, m), recs in records_by_partition.items():
            part_dir = out_base / f"year={y}" / f"month={m:02d}"
            part_dir.mkdir(parents=True, exist_ok=True)
            table = pa.Table.from_pylist(recs, schema=SCHEMA_FACT_RETURNS)
            pq.write_table(table, part_dir / "data.parquet", compression="snappy")
            total_returns += len(recs)

        return total_returns

    def _generate_fact_support_claims(
        self,
        dates: List[Dict[str, Any]],
        customers: List[Dict[str, Any]],
        stores: List[Dict[str, Any]],
    ) -> int:
        """Generate fact_support_claims with Story 1 (APAC Q3 2025 BP-2025-08 battery claims) injected."""
        out_base = self.marts_dir / "fact_support_claims"
        out_base.mkdir(parents=True, exist_ok=True)

        target_claims = int(max(1000, 100000 * self.scale))
        claims_per_date = max(1, target_claims // len(dates))

        product_ids = [p.product_id for p in ORCHARD_PRODUCTS]
        num_cust = len(customers)
        num_stores = len(stores)
        claim_counter = 1
        total_claims = 0

        # Group dates by (year, month)
        date_groups: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}
        for d in dates:
            key = (d["calendar_year"], d["month_number"])
            date_groups.setdefault(key, []).append(d)

        for (y, m), m_dates in date_groups.items():
            month_claims = []
            is_story_1 = (y == 2025 and m in (7, 8, 9))

            for d_info in m_dates:
                d_id = d_info["date_id"]
                for _ in range(claims_per_date):
                    cust = customers[self.rng.randint(num_cust)]
                    store = stores[self.rng.randint(num_stores)]
                    region = cust["region_id"]
                    prod_id = self.rng.choice(product_ids)

                    c_type = self.rng.choice(CLAIM_TYPES)
                    status = self.rng.choice(CLAIM_STATUSES, p=[0.60, 0.25, 0.10, 0.05])
                    repair_cost = float(round(self.rng.uniform(79.0, 450.0), 2))
                    deductible = 29.0 if c_type == "Display/Glass Crack" else (99.0 if self.rng.rand() > 0.4 else 0.0)
                    turnaround = self.rng.randint(1, 6)
                    batch_id = "STD-LOT"

                    claim_id = f"CLM-{y}-{claim_counter:06d}"
                    claim_counter += 1

                    month_claims.append({
                        "claim_id": claim_id,
                        "date_id": d_id,
                        "customer_id": cust["customer_id"],
                        "product_id": prod_id,
                        "store_id": store["store_id"],
                        "region_id": region,
                        "claim_type": c_type,
                        "claim_status": status,
                        "repair_cost": repair_cost,
                        "customer_deductible": deductible,
                        "turnaround_days": turnaround,
                        "component_batch_id": batch_id,
                        "year": y,
                        "month": m,
                    })

                # Inject Story 1: APAC Q3 2025 PearPhone 16 Pro Battery Spike with BP-2025-08
                if is_story_1:
                    # Inject extra claims for PRD-PHN-16P in APAC
                    spike_count = max(1, int(claims_per_date * 1.5))
                    for _ in range(spike_count):
                        cust = customers[self.rng.randint(num_cust)]
                        store = stores[self.rng.randint(num_stores)]
                        claim_id = f"CLM-{y}-{claim_counter:06d}"
                        claim_counter += 1

                        month_claims.append({
                            "claim_id": claim_id,
                            "date_id": d_id,
                            "customer_id": cust["customer_id"],
                            "product_id": "PRD-PHN-16P",
                            "store_id": store["store_id"],
                            "region_id": "APAC",
                            "claim_type": "Battery Degradation/Thermal",
                            "claim_status": "Approved & Replaced",
                            "repair_cost": 129.00,
                            "customer_deductible": 0.0,
                            "turnaround_days": 1,
                            "component_batch_id": "BP-2025-08",
                            "year": y,
                            "month": m,
                        })

            if month_claims:
                part_dir = out_base / f"year={y}" / f"month={m:02d}"
                part_dir.mkdir(parents=True, exist_ok=True)
                table = pa.Table.from_pylist(month_claims, schema=SCHEMA_FACT_SUPPORT_CLAIMS)
                pq.write_table(table, part_dir / "data.parquet", compression="snappy")
                total_claims += len(month_claims)

        return total_claims

    def _generate_fact_marketing_spend(
        self,
        dates: List[Dict[str, Any]],
    ) -> int:
        """Generate partitioned fact_marketing_spend with Story 2 (EMEA Q2 spend cut) injected."""
        out_base = self.marts_dir / "fact_marketing_spend"
        out_base.mkdir(parents=True, exist_ok=True)

        spend_counter = 1
        total_records = 0

        # Group dates by (year, month)
        date_groups: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}
        for d in dates:
            key = (d["calendar_year"], d["month_number"])
            date_groups.setdefault(key, []).append(d)

        products = [p.product_id for p in ORCHARD_PRODUCTS]
        channels = MARKETING_CHANNELS

        for (y, m), m_dates in date_groups.items():
            month_records = []
            is_emea_dip = (y == 2025 and m in (4, 5, 6))

            for d_info in m_dates:
                d_id = d_info["date_id"]

                for reg in REGIONS:
                    r_id = reg["region_id"]
                    base_daily = 3500.0 if r_id == "AMER" else (2200.0 if r_id == "EMEA" else 1800.0)

                    # Story 2: Cut EMEA spend by 70% in Q2 2025
                    if is_emea_dip and r_id == "EMEA":
                        base_daily *= 0.30

                    for ch in channels:
                        if ch == "Keynote Event / PR" and d_info["month_number"] not in (6, 9):
                            continue  # Keynotes only in June & September

                        spend = round(base_daily * self.rng.uniform(0.7, 1.4), 2)
                        impr = int(spend * self.rng.uniform(35.0, 65.0))
                        clicks = int(impr * self.rng.uniform(0.015, 0.045))
                        conv = int(clicks * self.rng.uniform(0.02, 0.06))

                        s_id = f"MKT-{y}-{spend_counter:06d}"
                        spend_counter += 1

                        month_records.append({
                            "spend_id": s_id,
                            "date_id": d_id,
                            "region_id": r_id,
                            "product_id": self.rng.choice(products),
                            "channel": ch,
                            "spend_usd": spend,
                            "impressions": impr,
                            "clicks": clicks,
                            "conversions": conv,
                            "year": y,
                            "month": m,
                        })

            if month_records:
                part_dir = out_base / f"year={y}" / f"month={m:02d}"
                part_dir.mkdir(parents=True, exist_ok=True)
                table = pa.Table.from_pylist(month_records, schema=SCHEMA_FACT_MARKETING_SPEND)
                pq.write_table(table, part_dir / "data.parquet", compression="snappy")
                total_records += len(month_records)

        return total_records

    def _generate_fact_finance_revenue(
        self,
        dates: List[Dict[str, Any]],
    ) -> int:
        """Generate fact_finance_revenue reconciliation table."""
        out_base = self.marts_dir / "fact_finance_revenue"
        out_base.mkdir(parents=True, exist_ok=True)

        lines = ["Pro", "Standard", "Ultra", "Air"]
        regions = [r["region_id"] for r in REGIONS]
        finance_records = []
        f_counter = 1

        # Generate 1 reconciliation row per (year, month, region, product_line)
        seen_months = set()
        for d in dates:
            m_key = (d["calendar_year"], d["month_number"], d["fiscal_quarter"], d["fiscal_year"])
            if m_key not in seen_months:
                seen_months.add(m_key)
                y, m, fq, fy = m_key
                d_id = d["date_id"]

                for reg in regions:
                    for line in lines:
                        base_rev = 12500000.0 if reg == "AMER" else (8200000.0 if reg == "EMEA" else 6500000.0)
                        if line == "Pro":
                            base_rev *= 1.8
                        if y == 2025 and m in (4, 5, 6) and reg == "EMEA":
                            base_rev *= 0.76  # Reflects Story 2 retail dip

                        rec_net = round(base_rev * self.rng.uniform(0.9, 1.15), 2)
                        deferred = round(rec_net * self.rng.uniform(0.12, 0.18), 2)
                        total_gaap = round(rec_net + deferred, 2)
                        op_margin = round(self.rng.uniform(0.28, 0.36), 4)

                        finance_records.append({
                            "finance_entry_id": f"FIN-{y}-{f_counter:05d}",
                            "date_id": d_id,
                            "fiscal_quarter": fq,
                            "fiscal_year": fy,
                            "region_id": reg,
                            "product_line": line,
                            "recognized_net_revenue": rec_net,
                            "deferred_services_revenue": deferred,
                            "total_gaap_revenue": total_gaap,
                            "operating_margin": op_margin,
                        })
                        f_counter += 1

        table = pa.Table.from_pylist(finance_records, schema=SCHEMA_FACT_FINANCE_REVENUE)
        pq.write_table(table, out_base / "fact_finance_revenue.parquet")
        return len(finance_records)
