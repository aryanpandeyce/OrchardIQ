"""Session management routes: GET /sessions, POST /sessions, GET /sessions/{id}."""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.api.routes.ask import session_manager
from src.api.auth import get_current_role

router = APIRouter(prefix="/sessions", tags=["Sessions & Memory"])


class CreateSessionRequest(BaseModel):
    title: Optional[str] = "Executive Analytics Session"


@router.get("")
def list_sessions(role: str = Depends(get_current_role)):
    """List all active and recent chat sessions."""
    return {"sessions": session_manager.list_sessions()}


@router.post("")
def create_session(req: CreateSessionRequest, role: str = Depends(get_current_role)):
    """Initialize a new chat session."""
    sess = session_manager.create_session(title=req.title)
    return sess.to_dict()


@router.get("/{session_id}")
def get_session_details(session_id: str, role: str = Depends(get_current_role)):
    """Retrieve full conversation history for a session."""
    sess = session_manager.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return sess.to_dict()
