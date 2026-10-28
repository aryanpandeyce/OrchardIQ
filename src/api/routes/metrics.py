"""Prometheus metrics exposition endpoint: GET /metrics."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from src.warehouse.query_engine import WarehouseQueryEngine
from src.governance.audit import get_audit_manager
from src.api.routes.ask import session_manager
from src.observability.metrics import metrics_collector

router = APIRouter(tags=["Observability & Telemetry"])

query_engine = WarehouseQueryEngine()


@router.get("/metrics", response_class=PlainTextResponse)
def get_prometheus_metrics():
    """Expose application and platform metrics in Prometheus text format."""
    audit_mgr = get_audit_manager()
    recent_logs = audit_mgr.get_recent_logs(limit=500)

    for r in recent_logs:
        st = r.get("status", "APPROVED")
        if st in metrics_collector.governance_counts:
            metrics_collector.governance_counts[st] = sum(1 for x in recent_logs if x.get("status") == st)

    active_sessions = len(session_manager.list_sessions())
    metrics_text = metrics_collector.export_prometheus_text(active_sessions=max(1, active_sessions))
    return PlainTextResponse(metrics_text, media_type="text/plain; version=0.0.4; charset=utf-8")
