"""Tests for synthetic star-schema data generation, partitioning, and determinism."""

import os
from pathlib import Path
import pyarrow.parquet as pq
import pytest

from src.data_gen.generator import OrchardWarehouseGenerator
from src.data_gen.unstructured import generate_knowledge_base_docs, generate_support_tickets
from src.config import Settings


def test_determinism(tmp_path: Path):
    """Assert generating twice with the exact same seed produces identical row counts."""
    dir1 = tmp_path / "run1"
    dir2 = tmp_path / "run2"

    gen1 = OrchardWarehouseGenerator(dir1, seed=42, scale=0.01)
    counts1 = gen1.generate_all()

    gen2 = OrchardWarehouseGenerator(dir2, seed=42, scale=0.01)
    counts2 = gen2.generate_all()

    assert counts1 == counts2
    assert counts1["dim_product"] == 14
    assert counts1["dim_region"] == 4
    assert counts1["dim_date"] == 1096  # 3 full years


def test_unstructured_docs_generation(tmp_path: Path):
    """Assert ~30 structured Markdown documentation files are created in knowledge base."""
    docs_dir = tmp_path / "docs"
    count = generate_knowledge_base_docs(docs_dir)

    assert count >= 30
    assert (docs_dir / "business_glossary" / "net_revenue.md").exists()
    assert (docs_dir / "business_glossary" / "attach_rate.md").exists()
    assert (docs_dir / "incident_postmortems" / "2025-q3-apac-battery-claims-spike.md").exists()
    assert (docs_dir / "data_dictionary" / "fact_sales.md").exists()
    assert (docs_dir / "data_quality" / "pii_governance_standards.md").exists()


def test_support_tickets_generation(tmp_path: Path):
    """Assert synthetic support tickets are written to JSONL and Parquet with required fields."""
    unstr_dir = tmp_path / "unstructured"
    jsonl_path = generate_support_tickets(unstr_dir, num_tickets=100, seed=42)

    assert jsonl_path.exists()
    parquet_path = unstr_dir / "support_tickets.parquet"
    assert parquet_path.exists()

    table = pq.read_table(parquet_path)
    assert table.num_rows == 100
    expected_cols = {"ticket_id", "created_at", "customer_id", "product_id", "subject", "component_batch_id"}
    assert expected_cols.issubset(set(table.column_names))


def test_partitioned_parquet_layout(populated_warehouse: Settings):
    """Assert transactional facts are partitioned by year=YYYY/month=MM."""
    warehouse_dir = populated_warehouse.get_warehouse_path() / "marts"

    sales_dir = warehouse_dir / "fact_sales"
    assert sales_dir.exists()

    year_dirs = [d for d in sales_dir.iterdir() if d.is_dir() and d.name.startswith("year=")]
    assert len(year_dirs) >= 3  # 2023, 2024, 2025

    sample_year = year_dirs[0]
    month_dirs = [d for d in sample_year.iterdir() if d.is_dir() and d.name.startswith("month=")]
    assert len(month_dirs) == 12

    sample_parquet = month_dirs[0] / "data.parquet"
    assert sample_parquet.exists()
    assert sample_parquet.stat().st_size > 0


def test_referential_integrity(duckdb_conn):
    """Assert all fact foreign keys resolve to valid dimension primary keys."""
    # 1. fact_sales -> dim_product
    orphan_products = duckdb_conn.execute("""
        SELECT COUNT(*) 
        FROM fact_sales s 
        LEFT JOIN dim_product p ON s.product_id = p.product_id 
        WHERE p.product_id IS NULL;
    """).fetchone()[0]
    assert orphan_products == 0

    # 2. fact_sales -> dim_customer
    orphan_customers = duckdb_conn.execute("""
        SELECT COUNT(*) 
        FROM fact_sales s 
        LEFT JOIN dim_customer c ON s.customer_id = c.customer_id 
        WHERE c.customer_id IS NULL;
    """).fetchone()[0]
    assert orphan_customers == 0

    # 3. fact_sales -> dim_store
    orphan_stores = duckdb_conn.execute("""
        SELECT COUNT(*) 
        FROM fact_sales s 
        LEFT JOIN dim_store st ON s.store_id = st.store_id 
        WHERE st.store_id IS NULL;
    """).fetchone()[0]
    assert orphan_stores == 0

    # 4. fact_sales -> dim_region
    orphan_regions = duckdb_conn.execute("""
        SELECT COUNT(*) 
        FROM fact_sales s 
        LEFT JOIN dim_region r ON s.region_id = r.region_id 
        WHERE r.region_id IS NULL;
    """).fetchone()[0]
    assert orphan_regions == 0
