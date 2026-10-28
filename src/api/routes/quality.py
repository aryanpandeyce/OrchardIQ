"""Data Quality scorecard endpoint: GET /quality/report."""

import time
from typing import Dict, List, Any
from fastapi import APIRouter, Depends

from src.warehouse.query_engine import WarehouseQueryEngine
from src.api.auth import get_current_role
from src.pipelines.quality import DataQualityEngine

router = APIRouter(prefix="/quality", tags=["Data Quality & Integrity"])

dq_engine = DataQualityEngine()


@router.get("/report")
def get_data_quality_report(role: str = Depends(get_current_role)):
    """Generate enterprise Data Quality validation report across star-schema tables."""
    return dq_engine.run_all_checks()

