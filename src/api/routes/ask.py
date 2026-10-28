"""POST /ask endpoint with SSE streaming and JSON response options."""

import json
import asyncio
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from src.api.auth import get_current_role
from src.agents.graph import OrchardAgentOrchestrator
from src.agents.memory import SessionManager

router = APIRouter(tags=["Ask & Multi-Agent"])

# Global orchestrator and session manager instances
orchestrator = OrchardAgentOrchestrator()
session_manager = SessionManager()


class AskRequest(BaseModel):
    query: str = Field(..., description="Natural language enterprise question")
    session_id: Optional[str] = Field(None, description="Active session ID for conversational memory")
    role: Optional[str] = Field(None, description="Override role for demo switching (analyst, finance, admin)")
    stream: bool = Field(True, description="Whether to stream real-time agent steps via SSE")


@router.post("/ask")
async def ask_question(
    req: AskRequest,
    current_role: str = Depends(get_current_role),
):
    """
    Execute multi-agent orchestration for a natural language inquiry.
    Streams agent steps via Server-Sent Events (SSE) or returns JSON.
    """
    effective_role = req.role if req.role in {"analyst", "finance", "admin"} else current_role
    sess_id = req.session_id or session_manager.create_session(title=req.query[:40]).session_id

    if not req.stream:
        # Synchronous execution
        final_state = orchestrator.invoke(query=req.query, role=effective_role, session_id=sess_id)
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
        generator = orchestrator.stream_execution(
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
