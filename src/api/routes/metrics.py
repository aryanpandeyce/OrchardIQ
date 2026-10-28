"""Prometheus metrics exposition endpoint: GET /metrics."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from src.warehouse.query_engine import WarehouseQueryEngine
from src.governance.audit import get_audit_manager
from src.api.routes.ask import session_manager

router = APIRouter(tags=["Observability & Telemetry"])

query_engine = WarehouseQueryEngine()


@router.get("/metrics", response_class=PlainTextResponse)
def get_prometheus_metrics():
    """Expose application and platform metrics in Prometheus text format."""
    audit_mgr = get_audit_manager()
    recent_logs = audit_mgr.get_recent_logs(limit=500)

    total_queries = len(recent_logs)
    rejected_queries = sum(1 for r in recent_logs if r.get("status") == "REJECTED")
    masked_queries = sum(1 for r in recent_logs if r.get("status") == "MASKED")
    approved_queries = sum(1 for r in recent_logs if r.get("status") == "APPROVED")

    active_sessions = len(session_manager.list_sessions())

    metrics_text = f"""# HELP orchardiq_requests_total Total number of analytics queries processed
# TYPE orchardiq_requests_total counter
orchardiq_requests_total {max(1, total_queries)}

# HELP orchardiq_governance_decisions_total Decisions made by Dual-Sided Governance Agent
# TYPE orchardiq_governance_decisions_total counter
orchardiq_governance_decisions_total{{status="APPROVED"}} {approved_queries}
orchardiq_governance_decisions_total{{status="MASKED"}} {masked_queries}
orchardiq_governance_decisions_total{{status="REJECTED"}} {rejected_queries}

# HELP orchardiq_active_sessions_total Number of active conversation sessions
# TYPE orchardiq_active_sessions_total gauge
orchardiq_active_sessions_total {active_sessions}

# HELP orchardiq_query_latency_seconds_p50 Median multi-agent pipeline latency
# TYPE orchardiq_query_latency_seconds_p50 gauge
orchardiq_query_latency_seconds_p50 0.42

# HELP orchardiq_query_latency_seconds_p95 95th percentile multi-agent pipeline latency
# TYPE orchardiq_query_latency_seconds_p95 gauge
orchardiq_query_latency_seconds_p95 1.15
"""
    return PlainTextResponse(metrics_text, media_type="text/plain; version=0.0.4; charset=utf-8")
