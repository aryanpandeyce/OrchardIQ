"""Shared pytest fixtures for OrchardIQ test suite."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator
import pytest
import duckdb

from src.config import Settings
from src.data_gen.generator import OrchardWarehouseGenerator
from src.data_gen.unstructured import generate_knowledge_base_docs, generate_support_tickets
from src.warehouse.catalog import WarehouseCatalog
from src.warehouse.connection import DuckDBConnectionFactory
from src.warehouse.query_engine import WarehouseQueryEngine


@pytest.fixture(scope="session")
def test_env_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test warehouse data and documentation."""
    temp_dir = Path(tempfile.mkdtemp(prefix="orchardiq_test_"))
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def test_settings(test_env_dir: Path) -> Settings:
    """Return test settings pointing to the temporary test environment."""
    return Settings(
        PROJECT_ROOT=test_env_dir,
        DATA_DIR=test_env_dir / "data",
        WAREHOUSE_DIR=test_env_dir / "data" / "warehouse",
        DOCS_DIR=test_env_dir / "docs" / "knowledge_base",
        UNSTRUCTURED_DIR=test_env_dir / "data" / "unstructured",
        DUCKDB_DATABASE_PATH=test_env_dir / "data" / "warehouse" / "test_dw.duckdb",
        DUCKDB_MEMORY_LIMIT="1GB",
        DUCKDB_THREADS=2,
        ENVIRONMENT="testing",
        MOCK_LLM_MODE=True,
    )


@pytest.fixture(scope="session")
def populated_warehouse(test_settings: Settings) -> Settings:
    """Generate a test-scale deterministic warehouse (~40k rows) and knowledge base."""
    docs_dir = test_settings.get_docs_path()
    unstructured_dir = test_settings.get_unstructured_path()
    warehouse_dir = test_settings.get_warehouse_path()

    generate_knowledge_base_docs(docs_dir)
    generate_support_tickets(unstructured_dir, num_tickets=500, seed=42)

    generator = OrchardWarehouseGenerator(warehouse_dir, seed=42, scale=0.02)
    generator.generate_all()

    return test_settings


@pytest.fixture(scope="session")
def duckdb_conn(populated_warehouse: Settings) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Provide a configured DuckDB connection with all star-schema views registered."""
    factory = DuckDBConnectionFactory(config=populated_warehouse)
    conn = factory.create_connection(database_path=":memory:")
    catalog = WarehouseCatalog(config=populated_warehouse)
    catalog.register_all_views(conn)
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def query_engine(duckdb_conn: duckdb.DuckDBPyConnection, populated_warehouse: Settings) -> WarehouseQueryEngine:
    """Provide an initialized query engine."""
    return WarehouseQueryEngine(conn=duckdb_conn, config=populated_warehouse, auto_register_views=False)
