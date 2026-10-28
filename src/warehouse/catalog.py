"""Warehouse catalog manager: view registration, schema introspection, and catalog health."""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import duckdb
from rich.console import Console
from rich.table import Table

from src.config import Settings, settings
from src.warehouse.connection import get_duckdb_connection


class WarehouseCatalog:
    """Manages DuckDB view creation over Parquet datasets and exposes schema metadata."""

    STAR_SCHEMA_TABLES = [
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
    ]

    PARTITIONED_FACTS = [
        "fact_sales",
        "fact_returns",
        "fact_support_claims",
        "fact_marketing_spend",
    ]

    def __init__(self, config: Optional[Settings] = None, base_uri: Optional[str] = None):
        self.config = config or settings
        if base_uri:
            self.base_uri = base_uri
        elif self.config.is_s3_configured:
            self.base_uri = f"s3://{self.config.S3_BUCKET}/marts"
        else:
            # Local Parquet directory formatted with forward slashes for DuckDB
            local_marts = self.config.get_warehouse_path() / "marts"
            self.base_uri = str(local_marts).replace("\\", "/")

    def get_parquet_path_for_table(self, table_name: str) -> str:
        """Resolve the Parquet file or wildcard pattern for a given table."""
        if table_name in self.PARTITIONED_FACTS:
            return f"{self.base_uri}/{table_name}/*/*/*.parquet"
        return f"{self.base_uri}/{table_name}/*.parquet"

    def register_all_views(self, conn: duckdb.DuckDBPyConnection) -> Dict[str, str]:
        """Create or replace DuckDB views pointing to Parquet datasets."""
        registered = {}
        for table in self.STAR_SCHEMA_TABLES:
            pattern = self.get_parquet_path_for_table(table)
            view_sql = f"CREATE OR REPLACE VIEW {table} AS SELECT * FROM read_parquet('{pattern}', hive_partitioning=true);"
            try:
                conn.execute(view_sql)
                registered[table] = pattern
            except Exception as e:
                # If wildcard doesn't match yet (e.g. before generation), record warning
                registered[table] = f"FAILED: {e}"
        return registered

    def get_tables(self, conn: duckdb.DuckDBPyConnection) -> List[str]:
        """Return list of accessible tables/views in the warehouse."""
        result = conn.execute("SHOW TABLES;").fetchall()
        return [row[0] for row in result]

    def get_table_schema(self, conn: duckdb.DuckDBPyConnection, table_name: str) -> List[Dict[str, Any]]:
        """Return schema column information for a specific table."""
        query = f"PRAGMA table_info('{table_name}');"
        rows = conn.execute(query).fetchall()
        # cid, name, type, notnull, dflt_value, pk
        columns = []
        for r in rows:
            columns.append({
                "column_name": r[1],
                "data_type": r[2],
                "nullable": not bool(r[3]),
                "is_primary_key": bool(r[5]),
            })
        return columns

    def get_full_catalog_metadata(self, conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
        """Inspect all registered warehouse tables, columns, and approximate counts."""
        catalog = {}
        tables = self.get_tables(conn)
        for t in tables:
            schema = self.get_table_schema(conn, t)
            try:
                count_res = conn.execute(f"SELECT COUNT(*) FROM {t};").fetchone()
                row_count = count_res[0] if count_res else 0
            except Exception:
                row_count = 0

            catalog[t] = {
                "table_name": t,
                "layer": "Fact / Mart" if t.startswith("fact_") else "Dimension",
                "row_count": row_count,
                "columns": schema,
            }
        return catalog

    def verify_catalog_health(self, conn: duckdb.DuckDBPyConnection) -> Dict[str, int]:
        """Verify each star-schema view can be queried successfully and return row counts."""
        health = {}
        for t in self.STAR_SCHEMA_TABLES:
            try:
                res = conn.execute(f"SELECT COUNT(*) FROM {t};").fetchone()
                health[t] = res[0] if res else 0
            except Exception as e:
                health[t] = -1
        return health


def main() -> None:
    """CLI utility to inspect warehouse catalog and verify view registration."""
    console = Console()
    catalog = WarehouseCatalog()
    conn = get_duckdb_connection()

    console.print(f"[bold cyan]Registering warehouse views from:[/bold cyan] {catalog.base_uri}")
    registered = catalog.register_all_views(conn)

    table = Table(title="OrchardIQ Lakehouse Catalog Status", show_header=True, header_style="bold green")
    table.add_column("View Name", style="cyan")
    table.add_column("Status / Row Count", justify="right", style="yellow")
    table.add_column("Parquet Source Pattern", style="white")

    health = catalog.verify_catalog_health(conn)
    for name, pattern in registered.items():
        count = health.get(name, -1)
        count_str = f"{count:,}" if count >= 0 else "[red]Error reading Parquet[/red]"
        table.add_row(name, count_str, pattern)

    console.print(table)


if __name__ == "__main__":
    main()
