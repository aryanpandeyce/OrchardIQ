"""Router & Planner Agent: Analyzes user intent, constructs an execution plan, and routes the graph."""

import re
import time
from typing import Dict, List, Any, Optional

from src.agents.state import OrchardAgentState, AgentStepLog
from src.agents.llm_provider import LLMProvider, get_llm_provider


class RouterPlannerAgent:
    """Classifies user intent and formulates a multi-step execution plan."""

    ROUTER_SYSTEM_PROMPT = """You are OrchardIQ's Strategic Planner Agent.
Analyze the user's inquiry and classify the appropriate analytical pipeline.
Available capabilities:
1. Catalog RAG (knowledge base lookup, metric definitions, SLAs, firmware postmortems, ticket searches)
2. SQL Analytics (querying DuckDB lakehouse for transactional facts, revenue, returns, claims)
3. Quantitative Analyst / ML (Period-over-Period variance, driver decomposition, PyTorch demand forecasting, IsolationForest anomaly detection)
4. Executive Narrator (summarizing findings, rendering Recharts declarative visual specs)
"""

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider or get_llm_provider()

    def plan(self, state: OrchardAgentState) -> Dict[str, Any]:
        """Construct execution plan and routing flags based on user query and role."""
        query = state.get("user_query", "").strip()
        role = state.get("role", "analyst")
        q_lower = query.lower()

        # Heuristic intent classification for immediate deterministic routing
        is_forecast = any(w in q_lower for w in ["forecast", "predict", "projection", "future demand", "next weeks"])
        is_anomaly = any(w in q_lower for w in ["anomaly", "spike", "outlier", "incident", "failure", "surge", "defect"])
        is_pop_or_driver = any(w in q_lower for w in ["yoy", "qoq", "pop", "variance", "driver", "slump", "attach ratio", "attach rate"])
        is_kb_or_doc = any(w in q_lower for w in ["definition", "glossary", "metric", "policy", "postmortem", "batch", "sla", "ticket", "firmware", "regression"])
        is_sql = any(w in q_lower for w in [
            "revenue", "sales", "units", "spend", "margin", "claims", "returns",
            "top", "total", "average", "avg", "how many", "which product", "compare", "by region", "customer"
        ]) or is_forecast or is_anomaly or is_pop_or_driver

        # Detect the 4 injected stories
        is_story_1 = "battery" in q_lower and ("apac" in q_lower or "thermal" in q_lower or "bp-2025-08" in q_lower)
        is_story_2 = "emea" in q_lower and ("marketing" in q_lower or "slump" in q_lower or "retail" in q_lower)
        is_story_3 = ("attach" in q_lower or "watch" in q_lower or "wearable" in q_lower) and ("amer" in q_lower or "holiday" in q_lower or "q4" in q_lower)
        is_story_4 = ("flicker" in q_lower or "pearbook" in q_lower or "firmware" in q_lower or "display" in q_lower) and ("return" in q_lower or "defect" in q_lower)

        if is_story_1 or is_story_2 or is_story_3 or is_story_4:
            intent = "hybrid_investigation"
            requires_rag = True
            requires_sql = True
            requires_analyst = True
            plan = [
                "1. Retrieve relevant engineering postmortems, component batch histories, and ticket logs via Hybrid RAG.",
                "2. Synthesize and execute star-schema DuckDB SQL to isolate quantitative variance and incident timelines.",
                "3. Enforce AST safety guardrails and role-based PII column masking.",
                "4. Perform statistical driver decomposition / anomaly detection with ML tooling.",
                "5. Generate executive narrative and interactive Recharts visualization.",
            ]
        elif is_forecast:
            intent = "demand_forecast"
            requires_rag = False
            requires_sql = True
            requires_analyst = True
            plan = [
                "1. Query historical weekly hardware shipments from DuckDB fact_sales.",
                "2. Execute PyTorch Multi-Layer Perceptron forecaster with 95% confidence intervals.",
                "3. Format timeline forecast chart and executive summary.",
            ]
        elif is_anomaly:
            intent = "anomaly_audit"
            requires_rag = True
            requires_sql = True
            requires_analyst = True
            plan = [
                "1. Retrieve quality incident records and postmortem tickets via RAG.",
                "2. Query metric time-series from data lakehouse.",
                "3. Run scikit-learn IsolationForest anomaly detection.",
                "4. Synthesize diagnostic narrative with anomaly markers.",
            ]
        elif is_kb_or_doc and not is_sql:
            intent = "knowledge_lookup"
            requires_rag = True
            requires_sql = False
            requires_analyst = False
            plan = [
                "1. Search enterprise knowledge base, data catalog, and metric glossary using Hybrid BM25+Dense retrieval.",
                "2. Synthesize cited response with verified document links.",
            ]
        else:
            intent = "sql_analytics"
            requires_rag = is_kb_or_doc
            requires_sql = True
            requires_analyst = is_pop_or_driver
            plan = [
                "1. Retrieve relevant business glossary context and metric formulas.",
                "2. Generate schema-grounded DuckDB SQL query.",
                "3. Validate AST guardrails and apply RBAC masking.",
                "4. Synthesize executive answer with data tables and charts.",
            ]

        step_log: AgentStepLog = {
            "step_name": "Planner",
            "status": "COMPLETED",
            "agent": "RouterPlanner",
            "message": f"Classified intent as '{intent}'. Formulated {len(plan)}-step execution plan for role '{role}'.",
            "timestamp": time.time(),
            "metadata": {
                "intent": intent,
                "plan": plan,
                "requires_rag": requires_rag,
                "requires_sql": requires_sql,
                "requires_analyst": requires_analyst,
            },
        }

        steps = list(state.get("steps", []))
        steps.append(step_log)

        return {
            "intent": intent,
            "plan": plan,
            "requires_rag": requires_rag,
            "requires_sql": requires_sql,
            "requires_analyst": requires_analyst,
            "current_step": "RouterPlanner",
            "steps": steps,
        }
