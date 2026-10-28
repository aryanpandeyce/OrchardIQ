"""Tests for DuckDB lakehouse connection, catalog views, and query engine."""

import pytest
from src.config import Settings
from src.warehouse.catalog import WarehouseCatalog
from src.warehouse.connection import DuckDBConnectionFactory
from src.warehouse.query_engine import WarehouseQueryEngine, QueryResult


def test_duckdb_connection_factory(test_settings: Settings):
    """Assert connection factory configures memory and threads properly."""
    factory = DuckDBConnectionFactory(config=test_settings)
    conn = factory.create_connection(database_path=":memory:")
    assert conn is not None

    # Check that settings pragmas applied
    threads = conn.execute("SELECT current_setting('threads');").fetchone()[0]
    assert int(threads) == test_settings.DUCKDB_THREADS
    conn.close()


def test_catalog_view_registration(duckdb_conn, populated_warehouse: Settings):
    """Assert all 10 star-schema views are registered and queryable."""
    catalog = WarehouseCatalog(config=populated_warehouse)
    tables = catalog.get_tables(duckdb_conn)

    expected_tables = {
        "dim_product",
        "dim_region",
        "dim_store",
        "dim_customer",
        "dim_date",
        "fact_sales",
        "fact_returns",
        "fact_support_claims",
        "fact_finance_revenue",
        "fact_marketing_spend",
    }
    assert expected_tables.issubset(set(tables))

    # Verify health checks return positive counts for all tables
    health = catalog.verify_catalog_health(duckdb_conn)
    for table_name in expected_tables:
        assert health[table_name] > 0, f"Table {table_name} has invalid row count: {health[table_name]}"


def test_schema_introspection(duckdb_conn, populated_warehouse: Settings):
    """Assert table column metadata is extracted accurately."""
    catalog = WarehouseCatalog(config=populated_warehouse)
    schema = catalog.get_table_schema(duckdb_conn, "dim_product")

    col_names = [col["column_name"] for col in schema]
    assert "product_id" in col_names
    assert "product_name" in col_names
    assert "price_usd" in col_names
    assert "warranty_months" in col_names


def test_query_engine_execution(query_engine: WarehouseQueryEngine):
    """Assert query engine executes analytical queries and returns QueryResult."""
    sql = """
        SELECT 
            p.category, 
            COUNT(*) as total_sales,
            ROUND(SUM(s.net_revenue), 2) as net_rev
        FROM fact_sales s
        JOIN dim_product p ON s.product_id = p.product_id
        GROUP BY p.category
        ORDER BY net_rev DESC;
    """
    res: QueryResult = query_engine.execute_query(sql)

    assert res.success is True
    assert res.error is None
    assert res.row_count > 0
    assert "category" in res.columns
    assert "net_rev" in res.columns
    assert res.latency_ms > 0.0
    assert len(res.rows) == res.row_count


def test_query_engine_row_limit(query_engine: WarehouseQueryEngine):
    """Assert query engine enforces max_rows safety cap."""
    sql = "SELECT * FROM fact_sales;"
    res: QueryResult = query_engine.execute_query(sql, max_rows=5)

    assert res.success is True
    assert res.row_count == 5
    assert len(res.rows) == 5


def test_query_engine_error_handling(query_engine: WarehouseQueryEngine):
    """Assert invalid SQL returns safe QueryResult without raising unhandled exception."""
    sql = "SELECT non_existent_column FROM non_existent_table;"
    res: QueryResult = query_engine.execute_query(sql)

    assert res.success is False
    assert res.error is not None
    assert res.row_count == 0


def test_query_engine_explain(query_engine: WarehouseQueryEngine):
    """Assert execution plan explanation is generated."""
    sql = "SELECT COUNT(*) FROM fact_sales WHERE net_revenue > 1000;"
    plan = query_engine.explain_query(sql)

    assert plan is not None
    plan_upper = plan.upper()
    assert any(term in plan_upper for term in ["SCAN", "AGGREGATE", "PROJECTION", "FILTER", "COUNT"])


def test_s3_uri_path_configuration():
    """Assert S3 lakehouse URI generation formats paths correctly for S3 bucket targets."""
    s3_settings = Settings(
        S3_BUCKET="orchardiq-demo-lakehouse",
        S3_ENDPOINT="https://s3.us-west-2.amazonaws.com",
        AWS_ACCESS_KEY_ID="test_key",
        AWS_SECRET_ACCESS_KEY="test_secret",
    )
    catalog = WarehouseCatalog(config=s3_settings)
    assert catalog.base_uri == "s3://orchardiq-demo-lakehouse/marts"
    parquet_path = catalog.get_parquet_path_for_table("fact_sales")
    assert parquet_path == "s3://orchardiq-demo-lakehouse/marts/fact_sales/*/*/*.parquet"
