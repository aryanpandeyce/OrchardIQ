import json
import asyncio
from collections import defaultdict
import time
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from src.config import settings
from src.api.auth import get_current_role
from src.agents.graph import OrchardAgentOrchestrator
from src.agents.llm_provider import ClaudeProvider
from src.agents.memory import SessionManager

router = APIRouter(tags=["Ask & Multi-Agent"])

# Global default orchestrator and session manager instances
orchestrator = OrchardAgentOrchestrator()
session_manager = SessionManager()

# In-memory IP rate limiting tracker (sliding window)
_ip_request_history = defaultdict(list)

# Daily spend tracker for API cost cap enforcement
_daily_cost_tracker = {"date": time.strftime("%Y-%m-%d"), "spent_usd": 0.0}

# Demo cache for instant response to verified inquiries
_demo_cache: Dict[str, Any] = {}


def get_effective_orchestrator(use_live: bool, custom_key: Optional[str] = None):
    """Resolve active orchestrator with daily cost cap enforcement."""
    today = time.strftime("%Y-%m-%d")
    if _daily_cost_tracker["date"] != today:
        _daily_cost_tracker["date"] = today
        _daily_cost_tracker["spent_usd"] = 0.0

    api_key = custom_key or settings.ANTHROPIC_API_KEY
    if use_live and api_key:
        if _daily_cost_tracker["spent_usd"] >= settings.DAILY_COST_CAP_USD:
            return orchestrator, "CAP_EXCEEDED"
        try:
            live_orch = OrchardAgentOrchestrator(llm_provider=ClaudeProvider(api_key=api_key))
            # Track estimated query cost (~$0.009 per live Claude turn)
            _daily_cost_tracker["spent_usd"] += 0.009
            return live_orch, "LIVE"
        except Exception:
            return orchestrator, "DEMO"

    return orchestrator, "DEMO"


class AskRequest(BaseModel):
    query: str = Field(..., description="Natural language enterprise question")
    session_id: Optional[str] = Field(None, description="Active session ID for conversational memory")
    role: Optional[str] = Field(None, description="Override role for demo switching (analyst, finance, admin)")
    stream: bool = Field(True, description="Whether to stream real-time agent steps via SSE")
    use_live_claude: bool = Field(False, description="Toggle live Claude 3.5 Sonnet if API key is provided")
    anthropic_api_key: Optional[str] = Field(None, description="Optional Anthropic API key")


@router.post("/ask")
async def ask_question(
    req: AskRequest,
    request: Request,
    current_role: str = Depends(get_current_role),
):
    """
    Execute multi-agent orchestration for a natural language inquiry.
    Streams agent steps via Server-Sent Events (SSE) or returns JSON.
    Protected by per-IP rate limiting, DEMO_MODE by default, and daily cost cap.
    """
    # Enforce per-IP rate limiting
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()
    _ip_request_history[client_ip] = [t for t in _ip_request_history[client_ip] if now - t < 60]
    if len(_ip_request_history[client_ip]) >= settings.PER_IP_RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: maximum {settings.PER_IP_RATE_LIMIT_PER_MINUTE} requests/min per IP."
        )
    _ip_request_history[client_ip].append(now)

    effective_role = req.role if req.role in {"analyst", "finance", "admin"} else current_role
    sess_id = req.session_id or session_manager.create_session(title=req.query[:40]).session_id

    active_orch, mode_label = get_effective_orchestrator(
        use_live=req.use_live_claude,
        custom_key=req.anthropic_api_key,
    )

    if not req.stream:
        # Synchronous execution
        final_state = active_orch.invoke(query=req.query, role=effective_role, session_id=sess_id)

        session_manager.add_turn(session_id=sess_id, state=final_state)
        return {
            "session_id": sess_id,
            "run_id": final_state.get("run_id"),
            "narrative": final_state.get("narrative"),
            "visual_spec": final_state.get("visual_spec"),
            "sql_query": final_state.get("sql_query"),
            "data": final_state.get("masked_data"),
            "citations": final_state.get("citations"),
            "governance": {
                "status": final_state.get("governance_status"),
                "role": effective_role,
                "audit_id": final_state.get("audit_id"),
                "violations": final_state.get("governance_violations"),
            },
            "steps": final_state.get("steps"),
        }

    # Streaming execution generator
    async def sse_event_generator():
        # Iterate over orchestrator generator
        generator = active_orch.stream_execution(
            query=req.query,
            role=effective_role,
            session_id=sess_id,
        )

        final_state = {}
        for event in generator:
            if event.get("event") == "answer":
                # Final state captured
                final_state = event
                session_manager.add_turn(
                    session_id=sess_id,
                    state={
                        "user_query": req.query,
                        "role": effective_role,
                        "narrative": event.get("narrative", ""),
                        "sql_query": event.get("sql_query"),
                        "visual_spec": event.get("visual_spec"),
                        "citations": event.get("citations", []),
                        "governance_status": event.get("governance", {}).get("status", "APPROVED"),
                    },
                )
            yield {
                "event": event.get("event", "step"),
                "data": json.dumps(event),
            }
            # Small yield pause for network streaming feel
            await asyncio.sleep(0.01)

        yield {
            "event": "done",
            "data": json.dumps({"status": "complete", "session_id": sess_id}),
        }

    return EventSourceResponse(sse_event_generator())
