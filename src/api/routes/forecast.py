"""Demand forecasting endpoint: POST /forecast."""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.ml.forecast import WeeklyDemandForecaster
from src.api.auth import get_current_role

router = APIRouter(prefix="/forecast", tags=["Machine Learning & Forecasting"])

forecaster = WeeklyDemandForecaster()


class ForecastRequest(BaseModel):
    product_id: str = Field("PRD-PHN-16P", description="Hardware product identifier")
    horizon_weeks: int = Field(6, ge=1, le=12, description="Forecast horizon in weeks")


@router.post("")
def generate_demand_forecast(
    req: ForecastRequest,
    role: str = Depends(get_current_role),
):
    """Generate multi-step hardware shipment demand forecast with 95% confidence bounds."""
    result = forecaster.forecast(product_id=req.product_id, horizon_weeks=req.horizon_weeks)
    return result.to_dict()
