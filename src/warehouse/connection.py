"""DuckDB connection factory with local Parquet and AWS S3 Lakehouse configuration."""

import duckdb
from typing import Optional
from src.config import Settings, settings


class DuckDBConnectionFactory:
    """Manages DuckDB connections, memory limits, extensions, and S3 credentials."""

    def __init__(self, config: Optional[Settings] = None):
        self.config = config or settings

    def create_connection(
        self,
        database_path: Optional[str] = None,
        read_only: bool = False,
    ) -> duckdb.DuckDBPyConnection:
        """Create and configure a DuckDB connection with S3 or local lakehouse settings."""
        db_path = database_path or (
            ":memory:" if not self.config.DUCKDB_DATABASE_PATH else str(self.config.get_duckdb_path())
        )

        conn = duckdb.connect(database=db_path, read_only=read_only)

        # Set performance pragmas
        conn.execute(f"SET memory_limit = '{self.config.DUCKDB_MEMORY_LIMIT}';")
        conn.execute(f"SET threads = {self.config.DUCKDB_THREADS};")
        conn.execute("SET preserve_insertion_order = false;")

        # Configure AWS S3 / MinIO / Ceph credentials if provided
        if self.config.is_s3_configured or self.config.S3_ENDPOINT:
            self._configure_s3(conn)

        return conn

    def _configure_s3(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Install and configure the DuckDB httpfs extension for AWS S3 compatibility."""
        try:
            conn.execute("INSTALL httpfs; LOAD httpfs;")
            if self.config.S3_ENDPOINT:
                conn.execute(f"SET s3_endpoint = '{self.config.S3_ENDPOINT}';")
            if self.config.S3_REGION:
                conn.execute(f"SET s3_region = '{self.config.S3_REGION}';")
            if self.config.AWS_ACCESS_KEY_ID:
                conn.execute(f"SET s3_access_key_id = '{self.config.AWS_ACCESS_KEY_ID}';")
            if self.config.AWS_SECRET_ACCESS_KEY:
                conn.execute(f"SET s3_secret_access_key = '{self.config.AWS_SECRET_ACCESS_KEY}';")
            if self.config.S3_URL_STYLE:
                conn.execute(f"SET s3_url_style = '{self.config.S3_URL_STYLE}';")
            if not self.config.S3_USE_SSL:
                conn.execute("SET s3_use_ssl = false;")
        except Exception as e:
            # S3 extension configuration failure logged without crashing local fallback
            print(f"[Warning] Failed to configure S3 httpfs: {e}")


def get_duckdb_connection(
    database_path: Optional[str] = None,
    read_only: bool = False,
    config: Optional[Settings] = None,
) -> duckdb.DuckDBPyConnection:
    """Convenience helper to acquire a configured DuckDB connection."""
    factory = DuckDBConnectionFactory(config=config)
    return factory.create_connection(database_path=database_path, read_only=read_only)
