"""LangGraph Multi-Agent Orchestration State Machine for OrchardIQ."""

import time
import uuid
from typing import Dict, List, Any, Optional, Generator, AsyncGenerator
from langgraph.graph import StateGraph, START, END

from src.agents.state import OrchardAgentState, AgentStepLog
from src.agents.router_planner import RouterPlannerAgent
from src.agents.sql_agent import SQLAgent
from src.agents.analyst_agent import AnalystAgent
from src.agents.narrator_agent import NarratorAgent
from src.rag.retriever import HybridRetriever
from src.rag.vector_store import ChromaVectorStore
from src.rag.citations import format_citations
from src.warehouse.query_engine import WarehouseQueryEngine
from src.governance.guardrails import GovernanceGuardrails
from src.governance.masking import mask_result_rows
from src.governance.audit import AuditManager, get_audit_manager
from src.agents.llm_provider import LLMProvider, get_llm_provider


class OrchardAgentOrchestrator:
    """Coordinates the multi-agent graph with LangGraph state transitions and SSE streaming."""

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        query_engine: Optional[WarehouseQueryEngine] = None,
        retriever: Optional[HybridRetriever] = None,
        audit_manager: Optional[AuditManager] = None,
    ):
        self.llm_provider = llm_provider or get_llm_provider()
        self.query_engine = query_engine or WarehouseQueryEngine()
        self.retriever = retriever or HybridRetriever()
        self.audit_manager = audit_manager or get_audit_manager()
        self.guardrails = GovernanceGuardrails()

        # Instantiate sub-agents
        self.planner_agent = RouterPlannerAgent(llm_provider=self.llm_provider)
        self.sql_agent = SQLAgent(
            llm_provider=self.llm_provider,
            query_engine=self.query_engine,
            guardrails=self.guardrails,
            audit_manager=self.audit_manager,
        )
        self.analyst_agent = AnalystAgent(query_engine=self.query_engine)
        self.narrator_agent = NarratorAgent(llm_provider=self.llm_provider)

        # Build and compile LangGraph state graph
        self.graph = self._build_graph()

    def _build_graph(self):
        """Construct the LangGraph StateGraph with conditional edges."""
        workflow = StateGraph(OrchardAgentState)

        # Register nodes
        workflow.add_node("router_planner", self._node_planner)
        workflow.add_node("catalog_rag", self._node_rag)
        workflow.add_node("sql_agent", self._node_sql)
        workflow.add_node("governance_agent", self._node_governance)
        workflow.add_node("analyst_agent", self._node_analyst)
        workflow.add_node("narrator_agent", self._node_narrator)

        # Entry edge
        workflow.add_edge(START, "router_planner")

        # Conditional edge after router_planner
        def route_after_planner(state: OrchardAgentState) -> str:
            if state.get("requires_rag"):
                return "catalog_rag"
            elif state.get("requires_sql"):
                return "sql_agent"
            elif state.get("requires_analyst"):
                return "analyst_agent"
            return "narrator_agent"

        workflow.add_conditional_edges(
            "router_planner",
            route_after_planner,
            {
                "catalog_rag": "catalog_rag",
                "sql_agent": "sql_agent",
                "analyst_agent": "analyst_agent",
                "narrator_agent": "narrator_agent",
            },
        )

        # Conditional edge after catalog_rag
        def route_after_rag(state: OrchardAgentState) -> str:
            if state.get("requires_sql"):
                return "sql_agent"
            elif state.get("requires_analyst"):
                return "analyst_agent"
            return "narrator_agent"

        workflow.add_conditional_edges(
            "catalog_rag",
            route_after_rag,
            {
                "sql_agent": "sql_agent",
                "analyst_agent": "analyst_agent",
                "narrator_agent": "narrator_agent",
            },
        )

        # Edge from sql_agent to governance
        workflow.add_edge("sql_agent", "governance_agent")

        # Conditional edge after governance_agent
        def route_after_gov(state: OrchardAgentState) -> str:
            if state.get("governance_status") == "REJECTED":
                return "narrator_agent"
            if state.get("requires_analyst"):
                return "analyst_agent"
            return "narrator_agent"

        workflow.add_conditional_edges(
            "governance_agent",
            route_after_gov,
            {
                "analyst_agent": "analyst_agent",
                "narrator_agent": "narrator_agent",
            },
        )

        # Edge from analyst to narrator
        workflow.add_edge("analyst_agent", "narrator_agent")
        workflow.add_edge("narrator_agent", END)

        return workflow.compile()

    # Node Implementations
    def _node_planner(self, state: OrchardAgentState) -> Dict[str, Any]:
        return self.planner_agent.plan(state)

    def _node_rag(self, state: OrchardAgentState) -> Dict[str, Any]:
        query = state.get("user_query", "")
        start_t = time.time()
        try:
            results = self.retriever.retrieve(query, top_k=4)
            docs = [r.to_dict() for r in results]
            citations = [
                {
                    "citation_id": f"CIT-{i+1}",
                    "doc_id": r.doc_id,
                    "title": r.title,
                    "doc_type": r.category,
                    "snippet": r.excerpt,
                    "source_file": r.source_file,
                    "score": round(r.score, 4),
                }
                for i, r in enumerate(results)
            ]
            msg = f"Retrieved {len(docs)} relevant knowledge artifacts (top: '{docs[0]['title'] if docs else 'None'}')."
        except Exception as e:
            docs = []
            citations = []
            msg = f"RAG lookup bypassed: {str(e)}"

        step_log: AgentStepLog = {
            "step_name": "Catalog RAG",
            "status": "COMPLETED",
            "agent": "CatalogRAG",
            "message": msg,
            "timestamp": time.time(),
            "metadata": {"doc_count": len(docs)},
        }
        steps = list(state.get("steps", []))
        steps.append(step_log)

        return {
            "retrieved_docs": docs,
            "citations": citations,
            "current_step": "CatalogRAG",
            "steps": steps,
        }

    def _node_sql(self, state: OrchardAgentState) -> Dict[str, Any]:
        query = state.get("user_query", "")
        role = state.get("role", "analyst")
        sql_res = self.sql_agent.run(query=query, role=role)

        step_log: AgentStepLog = {
            "step_name": "SQL Engine",
            "status": "COMPLETED" if sql_res.success else "FAILED",
            "agent": "SQLAgent",
            "message": f"Generated and executed SQL query in {len(sql_res.attempts)} attempt(s). Result: {'Success' if sql_res.success else 'Error'}.",
            "timestamp": time.time(),
            "metadata": {
                "sql": sql_res.final_sql,
                "row_count": len(sql_res.query_result.rows) if sql_res.query_result else 0,
                "error": sql_res.error,
            },
        }
        steps = list(state.get("steps", []))
        steps.append(step_log)

        raw_rows = sql_res.query_result.rows if sql_res.query_result else []
        columns = sql_res.query_result.columns if sql_res.query_result else []

        return {
            "sql_query": sql_res.final_sql,
            "sql_attempts": sql_res.attempts,
            "sql_success": sql_res.success,
            "raw_data": raw_rows,
            "columns": columns,
            "governance_violations": [sql_res.error] if sql_res.error else [],
            "audit_id": sql_res.audit_id or "",
            "current_step": "SQLAgent",
            "steps": steps,
        }

    def _node_governance(self, state: OrchardAgentState) -> Dict[str, Any]:
        raw_rows = state.get("raw_data", [])
        role = state.get("role", "analyst")
        violations = state.get("governance_violations", [])
        sql = state.get("sql_query", "")

        if violations or not state.get("sql_success", True):
            status = "REJECTED"
            masked_rows = []
            msg = f"Governance blocked query execution: {'; '.join(violations)}"
        else:
            # Apply RBAC post-execution column masking
            masked_rows = mask_result_rows(raw_rows, role=role)
            status = "MASKED" if role != "admin" else "APPROVED"
            msg = f"Applied RBAC security policy for role '{role}'. Restricted PII masked: {role != 'admin'}."

        step_log: AgentStepLog = {
            "step_name": "Governance Guardrails",
            "status": "COMPLETED" if status != "REJECTED" else "FAILED",
            "agent": "GovernanceAgent",
            "message": msg,
            "timestamp": time.time(),
            "metadata": {
                "status": status,
                "role": role,
                "masked": role != "admin",
                "row_count": len(masked_rows),
            },
        }
        steps = list(state.get("steps", []))
        steps.append(step_log)

        return {
            "governance_status": status,
            "masked_data": masked_rows,
            "row_count": len(masked_rows),
            "current_step": "GovernanceAgent",
            "steps": steps,
        }

    def _node_analyst(self, state: OrchardAgentState) -> Dict[str, Any]:
        query = state.get("user_query", "")
        masked_rows = state.get("masked_data", [])
        analyst_res = self.analyst_agent.auto_analyze(query=query, sql_rows=masked_rows)
        res_dict = analyst_res.to_dict() if analyst_res else None

        step_log: AgentStepLog = {
            "step_name": "Quantitative Analyst",
            "status": "COMPLETED",
            "agent": "AnalystAgent",
            "message": f"Completed {analyst_res.analysis_type if analyst_res else 'baseline'} diagnostic analysis.",
            "timestamp": time.time(),
            "metadata": {
                "analysis_type": analyst_res.analysis_type if analyst_res else "none",
                "findings_count": len(analyst_res.key_findings) if analyst_res else 0,
            },
        }
        steps = list(state.get("steps", []))
        steps.append(step_log)

        return {
            "analyst_result": res_dict,
            "current_step": "AnalystAgent",
            "steps": steps,
        }

    def _node_narrator(self, state: OrchardAgentState) -> Dict[str, Any]:
        return self.narrator_agent.synthesize(state)

    def invoke(self, query: str, role: str = "analyst", session_id: Optional[str] = None) -> OrchardAgentState:
        """Synchronously execute the full multi-agent state graph."""
        initial_state: OrchardAgentState = {
            "session_id": session_id or f"sess_{uuid.uuid4().hex[:8]}",
            "run_id": f"run_{uuid.uuid4().hex[:8]}",
            "user_query": query,
            "role": role,
            "steps": [],
            "plan": [],
            "retrieved_docs": [],
            "citations": [],
            "sql_query": "",
            "sql_attempts": [],
            "sql_success": False,
            "raw_data": [],
            "masked_data": [],
            "columns": [],
            "governance_status": "APPROVED",
            "governance_violations": [],
            "audit_id": "",
            "row_count": 0,
            "analyst_result": None,
            "narrative": "",
            "visual_spec": None,
        }
        return self.graph.invoke(initial_state)

    def stream_execution(
        self,
        query: str,
        role: str = "analyst",
        session_id: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, OrchardAgentState]:
        """
        Generator yielding real-time step events as each agent executes,
        ending with the full synthesized answer payload.
        """
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        state: OrchardAgentState = {
            "session_id": session_id or f"sess_{uuid.uuid4().hex[:8]}",
            "run_id": run_id,
            "user_query": query,
            "role": role,
            "steps": [],
            "plan": [],
            "retrieved_docs": [],
            "citations": [],
            "sql_query": "",
            "sql_attempts": [],
            "sql_success": False,
            "raw_data": [],
            "masked_data": [],
            "columns": [],
            "governance_status": "APPROVED",
            "governance_violations": [],
            "audit_id": "",
            "row_count": 0,
            "analyst_result": None,
            "narrative": "",
            "visual_spec": None,
        }

        # Step 1: Router & Planner
        yield {"event": "step", "agent": "RouterPlanner", "status": "RUNNING", "message": "Analyzing query intent and building plan..."}
        state.update(self._node_planner(state))
        yield {"event": "step", "agent": "RouterPlanner", "status": "COMPLETED", "message": f"Intent: {state.get('intent')}. Plan created ({len(state.get('plan', []))} steps).", "data": state.get("plan")}

        # Step 2: Catalog RAG if needed
        if state.get("requires_rag"):
            yield {"event": "step", "agent": "CatalogRAG", "status": "RUNNING", "message": "Searching data catalog and engineering postmortems..."}
            state.update(self._node_rag(state))
            yield {"event": "step", "agent": "CatalogRAG", "status": "COMPLETED", "message": f"Found {len(state.get('retrieved_docs', []))} reference docs.", "citations": state.get("citations")}

        # Step 3: SQL Agent if needed
        if state.get("requires_sql"):
            yield {"event": "step", "agent": "SQLAgent", "status": "RUNNING", "message": "Synthesizing schema-grounded DuckDB SQL..."}
            state.update(self._node_sql(state))
            yield {"event": "step", "agent": "SQLAgent", "status": "COMPLETED" if state.get("sql_success") else "FAILED", "message": f"SQL executed with {len(state.get('raw_data', []))} records.", "sql": state.get("sql_query")}

            # Step 4: Governance Agent
            yield {"event": "step", "agent": "GovernanceAgent", "status": "RUNNING", "message": f"Verifying AST safety and applying RBAC policies for role '{role}'..."}
            state.update(self._node_governance(state))
            yield {"event": "step", "agent": "GovernanceAgent", "status": "COMPLETED", "message": f"Status: {state.get('governance_status')}. PII masked for role '{role}'.", "audit_id": state.get("audit_id")}

        # Step 5: Analyst Agent if needed
        if state.get("requires_analyst") and state.get("governance_status") != "REJECTED":
            yield {"event": "step", "agent": "AnalystAgent", "status": "RUNNING", "message": "Executing statistical decomposition / ML models..."}
            state.update(self._node_analyst(state))
            yield {"event": "step", "agent": "AnalystAgent", "status": "COMPLETED", "message": "Quantitative findings ready."}

        # Step 6: Narrator Agent
        yield {"event": "step", "agent": "NarratorAgent", "status": "RUNNING", "message": "Synthesizing executive narrative and Recharts visual spec..."}
        state.update(self._node_narrator(state))
        yield {"event": "step", "agent": "NarratorAgent", "status": "COMPLETED", "message": "Executive briefing synthesized."}

        # Final Event
        yield {
            "event": "answer",
            "session_id": state["session_id"],
            "run_id": state["run_id"],
            "narrative": state["narrative"],
            "visual_spec": state["visual_spec"],
            "sql_query": state["sql_query"],
            "data": state["masked_data"],
            "citations": state["citations"],
            "governance": {
                "status": state["governance_status"],
                "role": state["role"],
                "audit_id": state["audit_id"],
                "violations": state["governance_violations"],
            },
            "steps": state["steps"],
        }

        return state
