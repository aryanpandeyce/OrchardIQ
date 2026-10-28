"""IsolationForest anomaly detection for claims, returns, and time-series variance analysis."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest

from src.warehouse.query_engine import WarehouseQueryEngine
from src.ml.registry import ModelRegistry


@dataclass
class AnomalyPoint:
    """Individual data point scored by anomaly detector."""
    label: str
    value: float
    anomaly_score: float  # Lower score indicates higher abnormality (standard IsolationForest score)
    is_anomaly: bool
    severity: str  # HIGH, MEDIUM, LOW, NORMAL
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "value": round(self.value, 2),
            "anomaly_score": round(self.anomaly_score, 4),
            "is_anomaly": self.is_anomaly,
            "severity": self.severity,
            "explanation": self.explanation,
        }


@dataclass
class AnomalyReport:
    """Comprehensive anomaly detection result."""
    metric_name: str
    contamination: float
    points: List[AnomalyPoint]
    anomaly_count: int
    top_anomalies: List[AnomalyPoint]
    model_version: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "contamination": self.contamination,
            "points": [p.to_dict() for p in self.points],
            "anomaly_count": self.anomaly_count,
            "top_anomalies": [p.to_dict() for p in self.top_anomalies],
            "model_version": self.model_version,
        }


class IsolationForestAnomalyDetector:
    """Scikit-learn IsolationForest anomaly detector with ModelRegistry integration."""

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        query_engine: Optional[WarehouseQueryEngine] = None,
        contamination: float = 0.08,
        random_state: int = 42,
    ):
        self.registry = registry or ModelRegistry()
        self.query_engine = query_engine or WarehouseQueryEngine()
        self.contamination = contamination
        self.random_state = random_state

    def fit_predict_series(
        self,
        series: List[Dict[str, Any]],
        label_key: str,
        value_key: str,
        metric_name: str = "metric_series",
    ) -> AnomalyReport:
        """
        Fit IsolationForest on a 1D time series augmented with rolling statistics
        and identify anomalous periods.
        """
        if not series or len(series) < 4:
            # Not enough data for meaningful clustering
            points = [
                AnomalyPoint(
                    label=str(r.get(label_key, "")),
                    value=float(r.get(value_key, 0.0)),
                    anomaly_score=0.0,
                    is_anomaly=False,
                    severity="NORMAL",
                    explanation="Insufficient sample size (< 4 points)",
                )
                for r in series
            ]
            return AnomalyReport(
                metric_name=metric_name,
                contamination=self.contamination,
                points=points,
                anomaly_count=0,
                top_anomalies=[],
                model_version=0,
            )

        labels = [str(r[label_key]) for r in series]
        values = np.array([float(r[value_key]) for r in series], dtype=np.float64)

        # Build feature matrix: [value, diff_from_median, z_score]
        mean_val = float(np.mean(values))
        std_val = float(np.std(values)) + 1e-6
        median_val = float(np.median(values))

        diff_from_med = np.abs(values - median_val)
        z_scores = (values - mean_val) / std_val

        # 2D feature matrix
        X = np.column_stack([values, diff_from_med, z_scores])

        # Adjust contamination if dataset is small
        eff_contamination = min(self.contamination, max(0.01, 2.0 / len(series)))
        iso = IsolationForest(
            contamination=eff_contamination,
            random_state=self.random_state,
            n_estimators=100,
        )
        preds = iso.fit_predict(X)  # -1 for anomaly, 1 for normal
        scores = iso.decision_function(X)  # lower = more abnormal

        points: List[AnomalyPoint] = []
        for i in range(len(series)):
            is_anom = bool(preds[i] == -1)
            score = float(scores[i])
            val = float(values[i])
            z = float(z_scores[i])

            if is_anom and z > 2.0:
                severity = "HIGH"
                exp = f"Significant upward spike ({val:,.1f} vs mean {mean_val:,.1f}, z={z:.2f})"
            elif is_anom and z < -2.0:
                severity = "HIGH"
                exp = f"Significant downward drop ({val:,.1f} vs mean {mean_val:,.1f}, z={z:.2f})"
            elif is_anom:
                severity = "MEDIUM"
                exp = f"Moderate statistical anomaly (score={score:.3f})"
            else:
                severity = "NORMAL"
                exp = "Within expected operational baseline"

            points.append(
                AnomalyPoint(
                    label=labels[i],
                    value=val,
                    anomaly_score=score,
                    is_anomaly=is_anom,
                    severity=severity,
                    explanation=exp,
                )
            )

        anomalies = [p for p in points if p.is_anomaly]
        # Sort top anomalies by lowest decision function score
        anomalies_sorted = sorted(anomalies, key=lambda x: x.anomaly_score)

        # Register model artifact
        safe_metric_name = metric_name.replace(" ", "_").replace("/", "_").lower()
        meta = self.registry.register_model(
            model_name=f"isolation_forest_{safe_metric_name}",
            framework="scikit-learn",
            architecture="IsolationForest(n_estimators=100)",
            hyperparameters={"contamination": eff_contamination, "random_state": self.random_state},
            eval_metrics={"anomaly_rate": len(anomalies) / max(1, len(points))},
            save_fn=lambda path: joblib.dump(iso, path),
        )

        return AnomalyReport(
            metric_name=metric_name,
            contamination=eff_contamination,
            points=points,
            anomaly_count=len(anomalies),
            top_anomalies=anomalies_sorted,
            model_version=meta.version,
        )

    def detect_claims_spike(
        self,
        region_id: str = "APAC",
        claim_type: str = "Battery Degradation/Thermal",
        product_id: Optional[str] = None,
    ) -> AnomalyReport:
        """Detect anomalies in warranty/support claims time series."""
        prod_filter = f"AND product_id = '{product_id}'" if product_id else ""
        sql = f"""
            SELECT 
                CAST(year AS VARCHAR) || '-' || LPAD(CAST(month AS VARCHAR), 2, '0') as period,
                COUNT(*) as claim_count
            FROM fact_support_claims
            WHERE region_id = '{region_id}'
              AND claim_type = '{claim_type}'
              {prod_filter}
            GROUP BY year, month
            ORDER BY year, month;
        """
        res = self.query_engine.execute_query(sql)
        series = res.rows if res.success else []
        return self.fit_predict_series(
            series=series,
            label_key="period",
            value_key="claim_count",
            metric_name=f"Claims_{region_id}_{claim_type}",
        )

    def detect_returns_spike(
        self,
        product_id: str = "PRD-NBK-16P",
        return_reason: str = "Defective / Hardware Issue",
    ) -> AnomalyReport:
        """Detect anomalies in hardware return rates."""
        sql = f"""
            SELECT 
                CAST(s.year AS VARCHAR) || '-' || LPAD(CAST(s.month AS VARCHAR), 2, '0') as period,
                ROUND(COUNT(DISTINCT r.return_id) * 100.0 / NULLIF(COUNT(DISTINCT s.sale_id), 0), 2) as defect_rate
            FROM fact_sales s
            LEFT JOIN fact_returns r 
              ON s.sale_id = r.sale_id 
             AND r.return_reason = '{return_reason}'
            WHERE s.product_id = '{product_id}'
            GROUP BY s.year, s.month
            ORDER BY s.year, s.month;
        """
        res = self.query_engine.execute_query(sql)
        series = res.rows if res.success else []
        return self.fit_predict_series(
            series=series,
            label_key="period",
            value_key="defect_rate",
            metric_name=f"ReturnsDefectRate_{product_id}",
        )
