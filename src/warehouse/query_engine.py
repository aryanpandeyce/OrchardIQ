"""Safe query engine for executing analytical queries against the DuckDB lakehouse."""

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import duckdb

from src.config import Settings, settings
from src.warehouse.connection import DuckDBConnectionFactory
from src.warehouse.catalog import WarehouseCatalog


@dataclass
class QueryResult:
    """Encapsulates the execution result, columns metadata, latency, and rows."""
    sql: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    latency_ms: float
    execution_plan: Optional[str] = None
    error: Optional[str] = None
    success: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sql": self.sql,
            "columns": self.columns,
            "rows": self.rows,
            "row_count": self.row_count,
            "latency_ms": self.latency_ms,
            "success": self.success,
            "error": self.error,
        }


class WarehouseQueryEngine:
    """Executes analytical SQL queries against the DuckDB star-schema warehouse."""

    def __init__(
        self,
        conn: Optional[duckdb.DuckDBPyConnection] = None,
        config: Optional[Settings] = None,
        auto_register_views: bool = True,
    ):
        self.config = config or settings
        self.factory = DuckDBConnectionFactory(config=self.config)
        self.conn = conn or self.factory.create_connection()
        self.catalog = WarehouseCatalog(config=self.config)

        if auto_register_views:
            self.catalog.register_all_views(self.conn)

    def execute_query(
        self,
        sql: str,
        max_rows: Optional[int] = None,
        include_plan: bool = False,
    ) -> QueryResult:
        """Execute a SQL query with timeout and row limit constraints."""
        clean_sql = sql.strip().rstrip(";")
        limit = max_rows or self.config.ANALYST_ROW_LIMIT

        t0 = time.perf_counter()
        plan = None

        try:
            if include_plan:
                plan_rows = self.conn.execute(f"EXPLAIN {clean_sql}").fetchall()
                plan = "\n".join([r[1] for r in plan_rows]) if plan_rows else None

            # Execute main query
            rel = self.conn.sql(clean_sql)
            columns = rel.columns
            # Fetch limited rows to prevent memory exhaustion
            raw_rows = rel.limit(limit).fetchall()
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

            # Convert to list of dicts
            formatted_rows = [
                {columns[i]: val for i, val in enumerate(row)}
                for row in raw_rows
            ]

            return QueryResult(
                sql=clean_sql,
                columns=columns,
                rows=formatted_rows,
                row_count=len(formatted_rows),
                latency_ms=elapsed_ms,
                execution_plan=plan,
                success=True,
            )

        except Exception as e:
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            return QueryResult(
                sql=clean_sql,
                columns=[],
                rows=[],
                row_count=0,
                latency_ms=elapsed_ms,
                error=str(e),
                success=False,
            )

    def explain_query(self, sql: str) -> str:
        """Retrieve the query optimizer execution plan from DuckDB."""
        clean_sql = sql.strip().rstrip(";")
        rows = self.conn.execute(f"EXPLAIN {clean_sql}").fetchall()
        return "\n".join([r[1] for r in rows])

    def close(self) -> None:
        """Close connection if open."""
        try:
            self.conn.close()
        except Exception:
            pass
