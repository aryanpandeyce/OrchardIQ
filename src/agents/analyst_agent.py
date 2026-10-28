"""Analyst Agent: Performs deeper statistical analysis, driver decomposition, and invokes ML tools."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from src.ml.stats import (
    PoPResult,
    DriverContribution,
    compute_period_over_period,
    compute_driver_contributions,
    detect_iqr_outliers,
)
from src.ml.registry import ModelRegistry
from src.ml.forecast import WeeklyDemandForecaster, ForecastResult
from src.ml.anomaly import IsolationForestAnomalyDetector, AnomalyReport
from src.warehouse.query_engine import WarehouseQueryEngine


@dataclass
class AnalystResult:
    """Consolidated quantitative and diagnostic findings from the Analyst Agent."""
    success: bool
    analysis_type: str  # forecast, anomaly_detection, pop_variance, driver_decomposition, incident_diagnostic
    headline: str
    key_findings: List[str]
    quantitative_summary: Dict[str, Any]
    visual_spec: Optional[Dict[str, Any]] = None  # Declarative chart hints for Narrator / Recharts
    raw_artifact: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "analysis_type": self.analysis_type,
            "headline": self.headline,
            "key_findings": self.key_findings,
            "quantitative_summary": self.quantitative_summary,
            "visual_spec": self.visual_spec,
            "raw_artifact": self.raw_artifact,
            "error": self.error,
        }


class AnalystAgent:
    """Coordinates statistical decomposition, PyTorch demand forecasting, and IsolationForest anomaly detection."""

    def __init__(
        self,
        query_engine: Optional[WarehouseQueryEngine] = None,
        registry: Optional[ModelRegistry] = None,
        forecaster: Optional[WeeklyDemandForecaster] = None,
        anomaly_detector: Optional[IsolationForestAnomalyDetector] = None,
    ):
        self.query_engine = query_engine or WarehouseQueryEngine()
        self.registry = registry or ModelRegistry()
        self.forecaster = forecaster or WeeklyDemandForecaster(
            registry=self.registry,
            query_engine=self.query_engine,
        )
        self.anomaly_detector = anomaly_detector or IsolationForestAnomalyDetector(
            registry=self.registry,
            query_engine=self.query_engine,
        )

    def forecast_demand(
        self,
        product_id: str = "PRD-PHN-16P",
        horizon_weeks: int = 6,
    ) -> AnalystResult:
        """Execute trained PyTorch demand forecasting with 95% confidence bounds."""
        try:
            res: ForecastResult = self.forecaster.forecast(
                product_id=product_id,
                horizon_weeks=horizon_weeks,
            )
            total_proj = sum(res.forecast_values)
            avg_proj = total_proj / max(1, len(res.forecast_values))

            findings = [
                f"Projected next {res.horizon_weeks} weeks demand for {product_id}: {total_proj:,.0f} total units (avg {avg_proj:,.0f}/wk).",
                f"Demand model confidence interval: ±{(res.upper_bounds[0] - res.lower_bounds[0])/2.0:,.0f} units at 95% certainty.",
                f"PyTorch Multi-Layer Perceptron historical test MAPE: {res.mape:.1f}%.",
            ]

            chart_data = []
            # Historical context
            for i, h in enumerate(res.historical_weeks[-8:]):
                chart_data.append({"week": f"Hist W-{8-i}", "historical": round(h, 1)})
            # Forecasted points
            for i, (f_val, lb, ub) in enumerate(zip(res.forecast_values, res.lower_bounds, res.upper_bounds)):
                chart_data.append({
                    "week": f"W+{i+1}",
                    "forecast": round(f_val, 1),
                    "lower_ci": round(lb, 1),
                    "upper_ci": round(ub, 1),
                })

            visual_spec = {
                "chart_type": "line",
                "x_axis": "week",
                "series": ["historical", "forecast", "lower_ci", "upper_ci"],
                "data": chart_data,
            }

            return AnalystResult(
                success=True,
                analysis_type="forecast",
                headline=f"Weekly Hardware Demand Forecast ({product_id})",
                key_findings=findings,
                quantitative_summary=res.to_dict(),
                visual_spec=visual_spec,
                raw_artifact=res.to_dict(),
            )
        except Exception as e:
            return AnalystResult(
                success=False,
                analysis_type="forecast",
                headline="Demand Forecast Failed",
                key_findings=[f"Forecasting encountered an error: {str(e)}"],
                quantitative_summary={},
                error=str(e),
            )

    def detect_claims_anomalies(
        self,
        region_id: str = "APAC",
        claim_type: str = "Battery Degradation/Thermal",
        product_id: Optional[str] = "PRD-PHN-16P",
    ) -> AnalystResult:
        """Run IsolationForest on support claims to flag quality incidents and defect surges."""
        try:
            report: AnomalyReport = self.anomaly_detector.detect_claims_spike(
                region_id=region_id,
                claim_type=claim_type,
                product_id=product_id,
            )

            anom_points = report.top_anomalies
            findings = [
                f"IsolationForest scanned {len(report.points)} periods and identified {report.anomaly_count} anomalous periods.",
            ]
            for p in anom_points[:3]:
                findings.append(f"Period {p.label}: {p.value:,.0f} claims ({p.severity} severity) - {p.explanation}")

            chart_data = [
                {
                    "period": p.label,
                    "claim_count": p.value,
                    "is_anomaly": p.is_anomaly,
                    "anomaly_score": p.anomaly_score,
                }
                for p in report.points
            ]

            visual_spec = {
                "chart_type": "bar",
                "x_axis": "period",
                "series": ["claim_count"],
                "highlight_condition": "is_anomaly",
                "data": chart_data,
            }

            return AnalystResult(
                success=True,
                analysis_type="anomaly_detection",
                headline=f"Warranty Claims Anomaly Detection ({region_id} - {claim_type})",
                key_findings=findings,
                quantitative_summary=report.to_dict(),
                visual_spec=visual_spec,
                raw_artifact=report.to_dict(),
            )
        except Exception as e:
            return AnalystResult(
                success=False,
                analysis_type="anomaly_detection",
                headline="Anomaly Detection Failed",
                key_findings=[str(e)],
                quantitative_summary={},
                error=str(e),
            )

    def detect_returns_anomalies(
        self,
        product_id: str = "PRD-NBK-16P",
        return_reason: str = "Defective / Hardware Issue",
    ) -> AnalystResult:
        """Run IsolationForest on return defect rates."""
        try:
            report: AnomalyReport = self.anomaly_detector.detect_returns_spike(
                product_id=product_id,
                return_reason=return_reason,
            )
            findings = [
                f"IsolationForest evaluated return rates for {product_id} across {len(report.points)} periods.",
                f"Detected {report.anomaly_count} anomalous spike windows exceeding baseline return thresholds.",
            ]
            for p in report.top_anomalies[:2]:
                findings.append(f"Period {p.label}: {p.value:.2f}% return rate ({p.severity} severity).")

            chart_data = [
                {"period": p.label, "defect_rate": p.value, "is_anomaly": p.is_anomaly}
                for p in report.points
            ]

            return AnalystResult(
                success=True,
                analysis_type="anomaly_detection",
                headline=f"Return Defect Rate Anomaly Detection ({product_id})",
                key_findings=findings,
                quantitative_summary=report.to_dict(),
                visual_spec={"chart_type": "line", "x_axis": "period", "series": ["defect_rate"], "data": chart_data},
                raw_artifact=report.to_dict(),
            )
        except Exception as e:
            return AnalystResult(
                success=False,
                analysis_type="anomaly_detection",
                headline="Return Anomaly Detection Failed",
                key_findings=[str(e)],
                quantitative_summary={},
                error=str(e),
            )

    def analyze_pop(
        self,
        current_val: float,
        prior_val: float,
        metric_name: str = "Revenue",
        annualize_periods: Optional[int] = None,
    ) -> AnalystResult:
        """Run Period-over-Period variance calculation."""
        res: PoPResult = compute_period_over_period(current_val, prior_val, annualize_periods)
        pct_sign = "+" if res.percentage_change > 0 else ""
        findings = [
            f"{metric_name} changed by {pct_sign}{res.percentage_change:.2f}% ({res.direction}).",
            f"Absolute delta: ${res.absolute_change:,.2f} (Current: ${res.current_value:,.2f} vs Prior: ${res.prior_value:,.2f}).",
        ]
        if res.annualized_rate is not None:
            findings.append(f"Annualized growth rate: {res.annualized_rate:.2f}%.")

        return AnalystResult(
            success=True,
            analysis_type="pop_variance",
            headline=f"Period-over-Period Variance Analysis ({metric_name})",
            key_findings=findings,
            quantitative_summary=res.to_dict(),
            raw_artifact=res.to_dict(),
        )

    def analyze_drivers(
        self,
        current_breakdown: Dict[str, float],
        prior_breakdown: Dict[str, float],
        metric_name: str = "Variance",
    ) -> AnalystResult:
        """Calculate driver waterfall decomposition."""
        drivers = compute_driver_contributions(current_breakdown, prior_breakdown)
        total_delta = sum(current_breakdown.values()) - sum(prior_breakdown.values())

        findings = [
            f"Total net variance: ${total_delta:,.2f} across {len(drivers)} segment drivers.",
        ]
        for d in drivers[:3]:
            findings.append(
                f"Driver '{d.entity}': delta of ${d.delta:,.2f} accounting for {d.contribution_percentage:.1f}% of total variance."
            )

        chart_data = [d.to_dict() for d in drivers]

        return AnalystResult(
            success=True,
            analysis_type="driver_decomposition",
            headline=f"Driver Contribution Analysis ({metric_name})",
            key_findings=findings,
            quantitative_summary={"total_delta": total_delta, "drivers": [d.to_dict() for d in drivers]},
            visual_spec={"chart_type": "bar", "x_axis": "entity", "series": ["delta"], "data": chart_data},
            raw_artifact={"drivers": [d.to_dict() for d in drivers]},
        )

    def auto_analyze(
        self,
        query: str,
        sql_rows: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[AnalystResult]:
        """
        Heuristic auto-routing to determine if quantitative/ML tool invocation is needed
        based on the user intent or query characteristics.
        """
        q_lower = query.lower()

        # 1. Forecasting intent
        if any(w in q_lower for w in ["forecast", "predict", "projection", "future demand", "next weeks", "next month"]):
            # Extract product if mentioned
            product_id = "PRD-PHN-16P"
            if "watch" in q_lower:
                product_id = "PRD-WCH-ULT2"
            elif "pearbook" in q_lower or "mac" in q_lower or "laptop" in q_lower:
                product_id = "PRD-NBK-16P"
            elif "pad" in q_lower or "tablet" in q_lower:
                product_id = "PRD-TAB-AIR"
            return self.forecast_demand(product_id=product_id)

        # 2. Anomaly / Spikes / Incident detection
        if any(w in q_lower for w in ["anomaly", "spike", "outlier", "incident", "failure", "surge", "unusual", "defect"]):
            if "return" in q_lower:
                return self.detect_returns_anomalies()
            return self.detect_claims_anomalies()

        # 3. Variance / Growth / Comparison
        if sql_rows and len(sql_rows) >= 2 and any(w in q_lower for w in ["grow", "decline", "vs", "compare", "yoy", "qoq", "pop", "variance"]):
            # If 2 rows, try PoP
            numeric_cols = [k for k, v in sql_rows[0].items() if isinstance(v, (int, float))]
            if numeric_cols:
                n_col = numeric_cols[0]
                val_curr = float(sql_rows[0][n_col])
                val_prior = float(sql_rows[1][n_col])
                return self.analyze_pop(current_val=val_curr, prior_val=val_prior, metric_name=n_col)

        return None
