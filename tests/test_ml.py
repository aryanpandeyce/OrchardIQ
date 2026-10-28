"""Comprehensive automated test suite for Machine Learning tools, statistical utilities, and Analyst Agent."""

import shutil
from pathlib import Path
import pytest
import numpy as np
import torch

from src.warehouse.query_engine import WarehouseQueryEngine
from src.ml.stats import (
    compute_period_over_period,
    compute_driver_contributions,
    detect_iqr_outliers,
)
from src.ml.registry import ModelRegistry
from src.ml.forecast import WeeklyDemandForecaster, DemandForecasterNet
from src.ml.anomaly import IsolationForestAnomalyDetector
from src.agents.analyst_agent import AnalystAgent


@pytest.fixture
def temp_registry_dir(tmp_path: Path):
    reg_dir = tmp_path / "models_registry"
    reg_dir.mkdir(parents=True, exist_ok=True)
    yield reg_dir
    if reg_dir.exists():
        shutil.rmtree(reg_dir, ignore_errors=True)


def test_compute_period_over_period():
    """Verify PoP math for growth, contraction, and edge cases."""
    # Growth
    res_growth = compute_period_over_period(current_val=150.0, prior_val=100.0)
    assert res_growth.percentage_change == 50.0
    assert res_growth.absolute_change == 50.0
    assert res_growth.direction == "GROWTH"

    # Contraction
    res_drop = compute_period_over_period(current_val=80.0, prior_val=100.0)
    assert res_drop.percentage_change == -20.0
    assert res_drop.direction == "CONTRACTION"

    # Zero prior value safe handling
    res_zero = compute_period_over_period(current_val=50.0, prior_val=0.0)
    assert res_zero.percentage_change == 100.0

    # Annualization
    res_ann = compute_period_over_period(current_val=110.0, prior_val=100.0, annualize_periods=4)
    assert res_ann.annualized_rate is not None
    assert res_ann.annualized_rate > 40.0  # Compound growth


def test_compute_driver_contributions():
    """Verify waterfall driver decomposition shares sum up to total delta."""
    current = {"PearPhone": 600.0, "PearBook": 300.0, "Services": 200.0}
    prior = {"PearPhone": 500.0, "PearBook": 350.0, "Services": 150.0}

    # Total delta = 1100 - 1000 = 100
    drivers = compute_driver_contributions(current, prior)
    assert len(drivers) == 3

    driver_map = {d.entity: d for d in drivers}
    # PearPhone delta = +100 -> 100% of net 100 delta
    assert driver_map["PearPhone"].delta == 100.0
    assert driver_map["PearPhone"].contribution_percentage == 100.0

    # PearBook delta = -50 -> -50% of net 100 delta
    assert driver_map["PearBook"].delta == -50.0
    assert driver_map["PearBook"].contribution_percentage == -50.0

    # Services delta = +50 -> 50% of net 100 delta
    assert driver_map["Services"].delta == 50.0
    assert driver_map["Services"].contribution_percentage == 50.0


def test_detect_iqr_outliers():
    """Verify Tukey IQR outlier detection identifies extreme values."""
    data = [10.0, 11.0, 12.0, 10.5, 11.5, 9.8, 10.2, 11.1, 10.8, 12.0, 95.0]  # 95 is extreme
    outliers = detect_iqr_outliers(data)
    assert len(outliers) == 1
    assert outliers[0]["value"] == 95.0
    assert outliers[0]["direction"] == "UPPER"


def test_model_registry_lifecycle(temp_registry_dir: Path):
    """Verify versioned model registration, filesystem layout, and metadata persistence."""
    registry = ModelRegistry(registry_dir=temp_registry_dir)

    # Register version 1
    m1 = registry.register_model(
        model_name="test_mlp",
        framework="pytorch",
        architecture="DemandForecasterNet(8, 64, 6)",
        hyperparameters={"lr": 0.005, "epochs": 10},
        eval_metrics={"mape": 9.4},
        save_fn=lambda p: torch.save(torch.tensor([1, 2, 3]), p),
    )
    assert m1.version == 1
    assert Path(m1.artifact_path).exists()

    # Register version 2
    m2 = registry.register_model(
        model_name="test_mlp",
        framework="pytorch",
        architecture="DemandForecasterNet(8, 64, 6)",
        hyperparameters={"lr": 0.001, "epochs": 20},
        eval_metrics={"mape": 7.1},
        save_fn=lambda p: torch.save(torch.tensor([4, 5, 6]), p),
    )
    assert m2.version == 2

    # Query latest metadata
    latest = registry.get_latest_metadata("test_mlp")
    assert latest is not None
    assert latest.version == 2
    assert latest.eval_metrics["mape"] == 7.1

    all_versions = registry.list_models()
    assert len(all_versions) == 1
    assert all_versions[0]["latest_version"] == 2


def test_weekly_demand_forecaster(query_engine: WarehouseQueryEngine, temp_registry_dir: Path):
    """Verify PyTorch demand forecaster training loop, MAPE evaluation, and confidence intervals."""
    registry = ModelRegistry(registry_dir=temp_registry_dir)
    forecaster = WeeklyDemandForecaster(registry=registry, query_engine=query_engine)

    # Train model
    res = forecaster.train_and_register(
        product_id="PRD-PHN-16P",
        epochs=15,
        lr=0.005,
    )
    assert res.horizon_weeks == 6
    assert len(res.forecast_values) == 6
    assert len(res.lower_bounds) == 6
    assert len(res.upper_bounds) == 6
    # Upper bound must be strictly greater than lower bound
    for lb, ub in zip(res.lower_bounds, res.upper_bounds):
        assert ub > lb

    # MAPE should be reasonably low (< 25%)
    assert res.mape < 25.0
    assert res.model_version >= 1

    # Test standalone forecast inference
    inf_res = forecaster.forecast(product_id="PRD-PHN-16P", horizon_weeks=4)
    assert inf_res.horizon_weeks == 4
    assert len(inf_res.forecast_values) == 4


def test_isolation_forest_anomaly_detector_on_story_data(
    query_engine: WarehouseQueryEngine,
    temp_registry_dir: Path,
):
    """
    Verify IsolationForest correctly identifies the injected Story 1 spike
    (APAC battery claims surge in Q3 2025).
    """
    registry = ModelRegistry(registry_dir=temp_registry_dir)
    detector = IsolationForestAnomalyDetector(
        registry=registry,
        query_engine=query_engine,
        contamination=0.10,
    )

    report = detector.detect_claims_spike(
        region_id="APAC",
        claim_type="Battery Degradation/Thermal",
        product_id="PRD-PHN-16P",
    )
    assert report.anomaly_count > 0

    # Ensure the top detected anomalies contain the incident months (2025-07, 2025-08, or 2025-09)
    top_labels = [a.label for a in report.top_anomalies]
    incident_months = {"2025-07", "2025-08", "2025-09"}
    detected_incident = any(lbl in incident_months for lbl in top_labels)
    assert detected_incident is True

    # Check that model was registered
    latest_meta = registry.get_latest_metadata("isolation_forest_claims_apac_battery_degradation_thermal")
    assert latest_meta is not None
    assert latest_meta.framework == "scikit-learn"


def test_analyst_agent_end_to_end(query_engine: WarehouseQueryEngine, temp_registry_dir: Path):
    """Verify AnalystAgent provides structured outputs and declarative visual specs."""
    registry = ModelRegistry(registry_dir=temp_registry_dir)
    agent = AnalystAgent(query_engine=query_engine, registry=registry)

    # 1. Forecast tool
    fc_res = agent.forecast_demand(product_id="PRD-PHN-16P", horizon_weeks=6)
    assert fc_res.success is True
    assert fc_res.analysis_type == "forecast"
    assert fc_res.visual_spec is not None
    assert fc_res.visual_spec["chart_type"] == "line"

    # 2. PoP Variance tool
    pop_res = agent.analyze_pop(current_val=500000.0, prior_val=420000.0, metric_name="APAC Q3 Net Revenue")
    assert pop_res.success is True
    assert pop_res.analysis_type == "pop_variance"
    assert "19.05%" in pop_res.key_findings[0]

    # 3. Driver decomposition tool
    curr_breakdown = {"Online": 250000.0, "Retail": 180000.0, "Enterprise": 70000.0}
    prior_breakdown = {"Online": 200000.0, "Retail": 190000.0, "Enterprise": 50000.0}
    driver_res = agent.analyze_drivers(curr_breakdown, prior_breakdown, metric_name="Channel Revenue")
    assert driver_res.success is True
    assert driver_res.analysis_type == "driver_decomposition"
    assert len(driver_res.key_findings) > 0

    # 4. Auto-analyze routing
    auto_fc = agent.auto_analyze("What is the projected future demand forecast for PearPhone next month?")
    assert auto_fc is not None
    assert auto_fc.analysis_type == "forecast"

    auto_anom = agent.auto_analyze("Were there any warranty defect spikes or anomalies in APAC battery claims?")
    assert auto_anom is not None
    assert auto_anom.analysis_type == "anomaly_detection"
