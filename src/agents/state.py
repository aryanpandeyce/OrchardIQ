"""Typed state definitions for LangGraph multi-agent orchestration."""

from typing import Dict, List, Any, Optional, TypedDict


class AgentStepLog(TypedDict, total=False):
    """Real-time timeline event emitted by agent execution graph."""
    step_name: str
    status: str  # RUNNING, COMPLETED, FAILED, SKIPPED
    agent: str   # RouterPlanner, CatalogRAG, SQLAgent, GovernanceAgent, AnalystAgent, NarratorAgent
    message: str
    timestamp: float
    metadata: Dict[str, Any]


class OrchardAgentState(TypedDict, total=False):
    """Consolidated state schema propagated through the LangGraph StateGraph."""
    # Session and Request context
    session_id: str
    run_id: str
    user_query: str
    role: str  # analyst, finance, admin
    current_step: str

    # Execution Plan
    plan: List[str]
    intent: str  # sql_analytics, knowledge_lookup, hybrid_investigation, demand_forecast, anomaly_audit
    requires_rag: bool
    requires_sql: bool
    requires_analyst: bool

    # Catalog & RAG context
    retrieved_docs: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]

    # SQL Agent context
    sql_query: str
    sql_attempts: List[Dict[str, Any]]
    sql_success: bool
    raw_data: List[Dict[str, Any]]
    masked_data: List[Dict[str, Any]]
    columns: List[str]

    # Governance Agent context
    governance_status: str  # APPROVED, REJECTED, MASKED
    governance_violations: List[str]
    audit_id: str
    row_count: int

    # Analyst / ML Agent context
    analyst_result: Optional[Dict[str, Any]]

    # Narrator output
    narrative: str
    visual_spec: Optional[Dict[str, Any]]

    # Real-time execution logs for SSE streaming
    steps: List[AgentStepLog]
    error: Optional[str]
