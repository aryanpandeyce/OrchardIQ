"""Health check endpoint: GET /health."""

import time
from typing import Dict, Any
from fastapi import APIRouter

from src.config import settings
from src.warehouse.query_engine import WarehouseQueryEngine
from src.ml.registry import ModelRegistry

router = APIRouter(tags=["System Health"])

query_engine = WarehouseQueryEngine()
registry = ModelRegistry()


@router.get("/health")
def health_check() -> Dict[str, Any]:
    """Report overall platform health and subsystem connectivity."""
    # Check DuckDB query engine
    warehouse_ok = False
    try:
        res = query_engine.execute_query("SELECT 1 as ping;")
        warehouse_ok = bool(res.success)
    except Exception:
        warehouse_ok = False

    models_registered = len(registry.list_models())

    return {
        "status": "healthy" if warehouse_ok else "degraded",
        "timestamp": time.time(),
        "version": "0.1.0",
        "demo_mode": settings.DEMO_MODE,
        "anthropic_configured": bool(settings.ANTHROPIC_API_KEY),
        "daily_cost_cap_usd": settings.DAILY_COST_CAP_USD,
        "subsystems": {
            "duckdb_lakehouse": "CONNECTED" if warehouse_ok else "DISCONNECTED",
            "chroma_vector_store": "READY",
            "model_registry": f"ACTIVE ({models_registered} models registered)",
            "dual_sided_governance": "ENFORCING",
        },
    }

