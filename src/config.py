"""Configuration settings for OrchardIQ."""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for OrchardIQ data platform and services."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Base Paths
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = Field(default=Path("data"))
    WAREHOUSE_DIR: Path = Field(default=Path("data/warehouse"))
    DOCS_DIR: Path = Field(default=Path("docs/knowledge_base"))
    UNSTRUCTURED_DIR: Path = Field(default=Path("data/unstructured"))

    # DuckDB Engine Settings
    DUCKDB_DATABASE_PATH: Path = Field(default=Path("data/warehouse/orchard_dw.duckdb"))
    DUCKDB_MEMORY_LIMIT: str = "4GB"
    DUCKDB_THREADS: int = 4

    # AWS S3-compatible Lakehouse Configuration
    S3_ENDPOINT: Optional[str] = None
    S3_BUCKET: Optional[str] = None
    S3_REGION: str = "us-west-2"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    S3_USE_SSL: bool = True
    S3_URL_STYLE: str = "path"

    # LLM & Agent Config
    ANTHROPIC_API_KEY: Optional[str] = None
    MOCK_LLM_MODE: bool = True
    DEMO_MODE: bool = True
    PER_IP_RATE_LIMIT_PER_MINUTE: int = 60
    DAILY_COST_CAP_USD: float = 10.0
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"

    # Security & Governance
    JWT_SECRET_KEY: str = "orchardiq_dev_secret_change_in_production_key_32chars"
    ANALYST_ROW_LIMIT: int = 1000
    QUERY_TIMEOUT_SECONDS: int = 30

    @property
    def is_s3_configured(self) -> bool:
        """Check if S3 storage is enabled."""
        return bool(self.S3_BUCKET and self.AWS_ACCESS_KEY_ID and self.AWS_SECRET_ACCESS_KEY)

    def resolve_path(self, path: Path) -> Path:
        """Resolve a path relative to the project root if it is not absolute."""
        if path.is_absolute():
            return path
        return (self.PROJECT_ROOT / path).resolve()

    def get_warehouse_path(self) -> Path:
        return self.resolve_path(self.WAREHOUSE_DIR)

    def get_docs_path(self) -> Path:
        return self.resolve_path(self.DOCS_DIR)

    def get_unstructured_path(self) -> Path:
        return self.resolve_path(self.UNSTRUCTURED_DIR)

    def get_duckdb_path(self) -> Path:
        return self.resolve_path(self.DUCKDB_DATABASE_PATH)


settings = Settings()
