"""Governance Audit Log endpoint: GET /audit."""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Query, Depends

from src.governance.audit import get_audit_manager
from src.api.auth import get_current_role, require_role

router = APIRouter(prefix="/audit", tags=["Governance & Security"])


@router.get("")
def get_audit_logs(
    limit: int = Query(50, ge=1, le=500, description="Max entries to return"),
    role_filter: Optional[str] = Query(None, description="Filter by user role"),
    status_filter: Optional[str] = Query(None, description="Filter by decision (APPROVED, REJECTED, MASKED)"),
    current_role: str = Depends(get_current_role),
):
    """Retrieve immutable audit log of all query attempts, AST safety decisions, and PII masking."""
    audit_mgr = get_audit_manager()
    records = audit_mgr.get_recent_logs(limit=limit)

    if role_filter:
        records = [r for r in records if r.get("user_role") == role_filter]
    if status_filter:
        records = [r for r in records if r.get("status") == status_filter]

    return {
        "count": len(records),
        "audit_logs": records,
    }
