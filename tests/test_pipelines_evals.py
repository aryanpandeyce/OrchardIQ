"""Test suite for Phase 7: Evals, Observability, and Data Pipelines."""

import json
from pathlib import Path
import pytest

from src.warehouse.query_engine import WarehouseQueryEngine
from src.observability.tracer import OrchardTracer, Span, Trace
from src.observability.metrics import MetricsCollector
from src.pipelines.quality import DataQualityEngine
from src.pipelines.etl import BatchETLPipeline
from src.pipelines.stream import TransactionStreamSimulator


@pytest.fixture(scope="module")
def query_engine():
    return WarehouseQueryEngine()


def test_golden_benchmark_dataset():
    """Verify that the golden benchmark set has >= 40 enterprise questions."""
    golden_path = Path("evals/golden_set.json")
    assert golden_path.exists(), "evals/golden_set.json must exist"

    with open(golden_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) >= 40, f"Expected >= 40 golden questions, found {len(data)}"
    for item in data:
        assert "id" in item
        assert "question" in item
        assert "category" in item
        assert "expected_governance_status" in item


def test_eval_results_file():
    """Verify that eval_results.json exists and contains required metrics."""
    res_path = Path("evals/eval_results.json")
    assert res_path.exists(), "evals/eval_results.json must exist"

    with open(res_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    assert results["total_questions"] >= 40
    assert results["sql_execution_accuracy_pct"] >= 95.0
    assert results["guardrail_pass_rate_pct"] >= 90.0
    assert results["latency_p50_seconds"] < 1.0


def test_opentelemetry_tracer():
    """Verify structured tracer, spans, and attributes recording."""
    tracer = OrchardTracer()
    trace = tracer.start_trace(run_id="run_test_123", query="Test sales?", role="finance")

    assert trace.trace_id.startswith("trc_")
    assert trace.status == "RUNNING"

    with tracer.span(run_id="run_test_123", name="test_span", attributes={"model": "mock"}):
        pass

    assert len(trace.spans) == 1
    span = trace.spans[0]
    assert span.name == "test_span"
    assert span.status == "OK"
    assert span.duration_ms >= 0.0

    trace.finish("COMPLETED")
    assert trace.status == "COMPLETED"
    assert trace.total_duration_ms >= 0.0

    retrieved = tracer.get_trace("run_test_123")
    assert retrieved is not None
    assert retrieved.trace_id == trace.trace_id


def test_prometheus_metrics_exporter():
    """Verify Prometheus exposition text format."""
    collector = MetricsCollector()
    collector.record_request(0.045, gov_status="APPROVED")
    collector.record_request(0.089, gov_status="MASKED")
    collector.record_request(0.012, gov_status="REJECTED")

    text = collector.export_prometheus_text(active_sessions=3, lakehouse_rows=2200000)

    assert "# HELP orchardiq_requests_total" in text
    assert 'orchardiq_governance_decisions_total{status="APPROVED"}' in text
    assert 'orchardiq_governance_decisions_total{status="MASKED"}' in text
    assert 'orchardiq_governance_decisions_total{status="REJECTED"}' in text
    assert "orchardiq_query_latency_seconds_p50" in text
    assert "orchardiq_query_latency_seconds_p95" in text


def test_data_quality_engine(query_engine):
    """Verify DataQualityEngine runs freshness, null rate, and uniqueness checks."""
    dq = DataQualityEngine(query_engine=query_engine)
    report = dq.run_all_checks()

    assert report["overall_status"] == "HEALTHY"
    assert report["total_lakehouse_rows"] > 1000000
    assert report["rules_passed"] > 15
    assert report["integrity_checks"]["duplicate_primary_keys"] == 0

    # Verify scorecards for key star-schema tables
    tables = [sc["table_name"] for sc in report["table_scorecards"]]
    assert "fact_sales" in tables
    assert "fact_returns" in tables
    assert "fact_support_claims" in tables
    assert "dim_product" in tables


def test_batch_etl_pipeline(query_engine):
    """Verify BatchETLPipeline raw -> staging -> marts execution with automated DQ gate."""
    pipeline = BatchETLPipeline(query_engine=query_engine)
    result = pipeline.execute_batch(batch_date="2025-10-28")

    assert result.status == "SUCCESS"
    assert result.dq_gate_status == "PASSED"
    assert result.raw_records_processed > 0
    assert result.staging_records_cleansed > 0
    assert result.marts_records_published > 0
    assert result.duration_ms > 0.0


def test_transaction_stream_simulator():
    """Verify transaction stream simulator event creation and buffering."""
    sim = TransactionStreamSimulator(buffer_size=50)

    event = sim.generate_event()
    assert event.id.startswith("EVT-")
    assert event.eventType in ("SALE", "CLAIM", "RETURN", "ATTACH")
    assert event.amount_usd > 0.0
    assert event.region in ("AMER", "EMEA", "APAC", "LATAM")
    assert "privaterelay" in event.customer_masked

    recent = sim.get_recent_events(limit=5)
    assert len(recent) == 5
    assert all("id" in e and "eventType" in e for e in recent)
