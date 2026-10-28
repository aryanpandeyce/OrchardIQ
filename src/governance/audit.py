"""Immutable governance audit logging for all natural language and SQL execution events."""

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import duckdb


@dataclass
class AuditRecord:
    """Immutable audit record representing a governance decision and execution event."""
    audit_id: str
    timestamp: str
    session_id: str
    run_id: str
    user_role: str
    question: str
    sql_query: str
    decision: str  # ALLOWED, MUTATED_LIMIT, BLOCKED_UNSAFE_AST, BLOCKED_UNAUTHORIZED_TABLE, BLOCKED_INJECTION
    reason: str
    tables_accessed: List[str]
    row_count: int
    latency_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "run_id": self.run_id,
            "user_role": self.user_role,
            "question": self.question,
            "sql_query": self.sql_query,
            "decision": self.decision,
            "reason": self.reason,
            "tables_accessed": self.tables_accessed,
            "row_count": self.row_count,
            "latency_ms": self.latency_ms,
        }


class AuditManager:
    """Manages audit logging in memory and optionally writes to DuckDB."""

    def __init__(self, conn: Optional[duckdb.DuckDBPyConnection] = None):
        self._logs: List[AuditRecord] = []
        self._conn = conn
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create audit_log table in DuckDB if connected."""
        if self._conn:
            try:
                self._conn.execute("""
                    CREATE TABLE IF NOT EXISTS audit_log (
                        audit_id VARCHAR PRIMARY KEY,
                        timestamp VARCHAR,
                        session_id VARCHAR,
                        run_id VARCHAR,
                        user_role VARCHAR,
                        question VARCHAR,
                        sql_query VARCHAR,
                        decision VARCHAR,
                        reason VARCHAR,
                        tables_accessed VARCHAR,
                        row_count INTEGER,
                        latency_ms DOUBLE
                    );
                """)
            except Exception:
                pass

    def record_event(
        self,
        session_id: str,
        run_id: str,
        user_role: str,
        question: str,
        sql_query: str,
        decision: str,
        reason: str = "Policy validated successfully",
        tables_accessed: Optional[List[str]] = None,
        row_count: int = 0,
        latency_ms: float = 0.0,
    ) -> AuditRecord:
        """Create and store an immutable audit record."""
        record = AuditRecord(
            audit_id=f"AUD-{uuid.uuid4().hex[:12].upper()}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=session_id,
            run_id=run_id,
            user_role=user_role,
            question=question,
            sql_query=sql_query,
            decision=decision,
            reason=reason,
            tables_accessed=tables_accessed or [],
            row_count=row_count,
            latency_ms=latency_ms,
        )
        self._logs.append(record)

        if self._conn:
            try:
                self._conn.execute("""
                    INSERT INTO audit_log VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, [
                    record.audit_id,
                    record.timestamp,
                    record.session_id,
                    record.run_id,
                    record.user_role,
                    record.question,
                    record.sql_query,
                    record.decision,
                    record.reason,
                    ",".join(record.tables_accessed),
                    record.row_count,
                    record.latency_ms,
                ])
            except Exception:
                pass

        return record

    def get_logs(
        self,
        limit: int = 100,
        role: Optional[str] = None,
        decision: Optional[str] = None,
    ) -> List[AuditRecord]:
        """Query logged events with filtering."""
        filtered = self._logs
        if role:
            filtered = [r for r in filtered if r.user_role == role]
        if decision:
            filtered = [r for r in filtered if r.decision == decision]
        return list(reversed(filtered))[:limit]

    def count(self) -> int:
        return len(self._logs)


_global_audit_manager: Optional[AuditManager] = None


def get_audit_manager(conn: Optional[duckdb.DuckDBPyConnection] = None) -> AuditManager:
    """Return singleton audit manager."""
    global _global_audit_manager
    if _global_audit_manager is None:
        _global_audit_manager = AuditManager(conn=conn)
    elif conn and not _global_audit_manager._conn:
        _global_audit_manager._conn = conn
        _global_audit_manager._ensure_table()
    return _global_audit_manager
