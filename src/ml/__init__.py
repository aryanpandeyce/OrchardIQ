"""Machine Learning and Statistical Analysis module."""

from src.ml.stats import (
    PoPResult,
    DriverContribution,
    compute_period_over_period,
    compute_driver_contributions,
    detect_iqr_outliers,
)
from src.ml.registry import (
    ModelMetadata,
    ModelRegistry,
)
from src.ml.forecast import (
    ForecastResult,
    DemandForecasterNet,
    WeeklyDemandForecaster,
)
from src.ml.anomaly import (
    AnomalyPoint,
    AnomalyReport,
    IsolationForestAnomalyDetector,
)

__all__ = [
    "PoPResult",
    "DriverContribution",
    "compute_period_over_period",
    "compute_driver_contributions",
    "detect_iqr_outliers",
    "ModelMetadata",
    "ModelRegistry",
    "ForecastResult",
    "DemandForecasterNet",
    "WeeklyDemandForecaster",
    "AnomalyPoint",
    "AnomalyReport",
    "IsolationForestAnomalyDetector",
]
