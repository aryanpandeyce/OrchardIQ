"""Statistical analysis tools: Period-over-Period (PoP) variance, driver contribution, and IQR outliers."""

import math
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
import numpy as np


@dataclass
class PoPResult:
    """Period-over-Period variance analysis result."""
    current_value: float
    prior_value: float
    absolute_change: float
    percentage_change: float
    direction: str  # GROWTH, CONTRACTION, NEUTRAL
    annualized_rate: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_value": round(self.current_value, 2),
            "prior_value": round(self.prior_value, 2),
            "absolute_change": round(self.absolute_change, 2),
            "percentage_change": round(self.percentage_change, 2),
            "direction": self.direction,
            "annualized_rate": round(self.annualized_rate, 2) if self.annualized_rate is not None else None,
        }


@dataclass
class DriverContribution:
    """Individual entity contribution to overall variance."""
    entity: str
    current_value: float
    prior_value: float
    delta: float
    contribution_percentage: float  # Share of total variance

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity": self.entity,
            "current_value": round(self.current_value, 2),
            "prior_value": round(self.prior_value, 2),
            "delta": round(self.delta, 2),
            "contribution_percentage": round(self.contribution_percentage, 2),
        }


def compute_period_over_period(
    current_val: float,
    prior_val: float,
    annualize_periods: Optional[int] = None,
) -> PoPResult:
    """Calculate absolute and percentage delta between two periods."""
    delta = current_val - prior_val
    if abs(prior_val) < 1e-6:
        pct_change = 100.0 if current_val > 0 else 0.0
    else:
        pct_change = (delta / prior_val) * 100.0

    if pct_change > 1.0:
        direction = "GROWTH"
    elif pct_change < -1.0:
        direction = "CONTRACTION"
    else:
        direction = "NEUTRAL"

    annualized = None
    if annualize_periods and annualize_periods > 1 and prior_val > 0 and current_val > 0:
        try:
            annualized = (((current_val / prior_val) ** annualize_periods) - 1.0) * 100.0
        except Exception:
            annualized = None

    return PoPResult(
        current_value=float(current_val),
        prior_value=float(prior_val),
        absolute_change=float(delta),
        percentage_change=float(pct_change),
        direction=direction,
        annualized_rate=annualized,
    )


def compute_driver_contributions(
    current_breakdown: Dict[str, float],
    prior_breakdown: Dict[str, float],
) -> List[DriverContribution]:
    """Calculate waterfall driver contributions to overall variance across entities."""
    all_entities = set(current_breakdown.keys()) | set(prior_breakdown.keys())
    contributions = []

    total_current = sum(current_breakdown.values())
    total_prior = sum(prior_breakdown.values())
    total_delta = total_current - total_prior

    for ent in all_entities:
        c_val = current_breakdown.get(ent, 0.0)
        p_val = prior_breakdown.get(ent, 0.0)
        d = c_val - p_val
        share = (d / total_delta * 100.0) if abs(total_delta) > 1e-6 else 0.0

        contributions.append(
            DriverContribution(
                entity=ent,
                current_value=c_val,
                prior_value=p_val,
                delta=d,
                contribution_percentage=share,
            )
        )

    # Sort by absolute delta impact
    contributions.sort(key=lambda x: abs(x.delta), reverse=True)
    return contributions


def detect_iqr_outliers(
    series: List[float],
    labels: Optional[List[str]] = None,
    multiplier: float = 1.5,
) -> List[Dict[str, Any]]:
    """Detect statistical outliers using the Interquartile Range (IQR) method."""
    if len(series) < 4:
        return []

    arr = np.array(series, dtype=np.float64)
    q25 = float(np.percentile(arr, 25))
    q75 = float(np.percentile(arr, 75))
    iqr = q75 - q25

    lower_bound = q25 - (multiplier * iqr)
    upper_bound = q75 + (multiplier * iqr)

    outliers = []
    for idx, val in enumerate(series):
        if val < lower_bound or val > upper_bound:
            lbl = labels[idx] if (labels and idx < len(labels)) else str(idx)
            outliers.append({
                "index": idx,
                "label": lbl,
                "value": float(val),
                "lower_bound": round(lower_bound, 2),
                "upper_bound": round(upper_bound, 2),
                "deviation_type": "HIGH" if val > upper_bound else "LOW",
                "direction": "UPPER" if val > upper_bound else "LOWER",
            })

    return outliers
