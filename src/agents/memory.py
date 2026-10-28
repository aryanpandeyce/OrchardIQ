"""Session conversation memory and persistent long-term insight bookmarking."""

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.agents.state import OrchardAgentState


@dataclass
class ConversationTurn:
    """Single question-answer exchange within a chat session."""
    turn_id: str
    timestamp: float
    user_query: str
    role: str
    narrative: str
    sql_query: Optional[str] = None
    visual_spec: Optional[Dict[str, Any]] = None
    citations: List[Dict[str, Any]] = field(default_factory=list)
    governance_status: str = "APPROVED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "timestamp": self.timestamp,
            "user_query": self.user_query,
            "role": self.role,
            "narrative": self.narrative,
            "sql_query": self.sql_query,
            "visual_spec": self.visual_spec,
            "citations": self.citations,
            "governance_status": self.governance_status,
        }


@dataclass
class ChatSession:
    """Stateful chat session containing chronological turns."""
    session_id: str
    created_at: float
    title: str
    turns: List[ConversationTurn] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "title": self.title,
            "turn_count": len(self.turns),
            "turns": [t.to_dict() for t in self.turns],
        }


class SessionManager:
    """Manages active chat sessions with optional filesystem persistence."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path("data/sessions")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._sessions: Dict[str, ChatSession] = {}
        self._load_all()

    def _load_all(self) -> None:
        if not self.storage_dir.exists():
            return
        for file in self.storage_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    turns = [ConversationTurn(**t) for t in data.get("turns", [])]
                    sess = ChatSession(
                        session_id=data["session_id"],
                        created_at=data["created_at"],
                        title=data.get("title", "New Session"),
                        turns=turns,
                    )
                    self._sessions[sess.session_id] = sess
            except Exception:
                pass

    def create_session(self, title: Optional[str] = None) -> ChatSession:
        """Create and register a new chat session."""
        sess_id = f"sess_{uuid.uuid4().hex[:8]}"
        sess = ChatSession(
            session_id=sess_id,
            created_at=time.time(),
            title=title or "Executive Analytics Session",
            turns=[],
        )
        self._sessions[sess_id] = sess
        self._save(sess)
        return sess

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[Dict[str, Any]]:
        return [
            {
                "session_id": s.session_id,
                "title": s.title,
                "created_at": s.created_at,
                "turn_count": len(s.turns),
            }
            for s in sorted(self._sessions.values(), key=lambda x: x.created_at, reverse=True)
        ]

    def add_turn(self, session_id: str, state: OrchardAgentState) -> ConversationTurn:
        """Record an executed agent state into the session memory."""
        sess = self._sessions.get(session_id)
        if not sess:
            sess = self.create_session(title=state.get("user_query", "Analytics Query")[:40])
            self._sessions[session_id] = sess

        turn = ConversationTurn(
            turn_id=f"turn_{uuid.uuid4().hex[:6]}",
            timestamp=time.time(),
            user_query=state.get("user_query", ""),
            role=state.get("role", "analyst"),
            narrative=state.get("narrative", ""),
            sql_query=state.get("sql_query"),
            visual_spec=state.get("visual_spec"),
            citations=state.get("citations", []),
            governance_status=state.get("governance_status", "APPROVED"),
        )
        sess.turns.append(turn)
        if len(sess.turns) == 1:
            # Set title from first query
            sess.title = turn.user_query[:50]
        self._save(sess)
        return turn

    def _save(self, session: ChatSession) -> None:
        try:
            path = self.storage_dir / f"{session.session_id}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(session.to_dict(), f, indent=2)
        except Exception:
            pass


@dataclass
class SavedInsight:
    """Persistent saved finding or chart pinned by an enterprise user."""
    insight_id: str
    title: str
    user_query: str
    narrative: str
    visual_spec: Optional[Dict[str, Any]]
    created_at: float
    role: str
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "insight_id": self.insight_id,
            "title": self.title,
            "user_query": self.user_query,
            "narrative": self.narrative,
            "visual_spec": self.visual_spec,
            "created_at": self.created_at,
            "role": self.role,
            "tags": self.tags,
        }


class InsightManager:
    """Manages bookmarkable enterprise insights."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path("data/insights")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._insights: Dict[str, SavedInsight] = {}
        self._load_all()

    def _load_all(self) -> None:
        if not self.storage_dir.exists():
            return
        for file in self.storage_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    ins = SavedInsight(**data)
                    self._insights[ins.insight_id] = ins
            except Exception:
                pass

    def save_insight(
        self,
        title: str,
        user_query: str,
        narrative: str,
        visual_spec: Optional[Dict[str, Any]] = None,
        role: str = "analyst",
        tags: Optional[List[str]] = None,
    ) -> SavedInsight:
        ins_id = f"ins_{uuid.uuid4().hex[:8]}"
        ins = SavedInsight(
            insight_id=ins_id,
            title=title,
            user_query=user_query,
            narrative=narrative,
            visual_spec=visual_spec,
            created_at=time.time(),
            role=role,
            tags=tags or ["executive"],
        )
        self._insights[ins_id] = ins
        path = self.storage_dir / f"{ins_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ins.to_dict(), f, indent=2)
        return ins

    def list_insights(self) -> List[Dict[str, Any]]:
        return [
            i.to_dict()
            for i in sorted(self._insights.values(), key=lambda x: x.created_at, reverse=True)
        ]

    def get_insight(self, insight_id: str) -> Optional[SavedInsight]:
        return self._insights.get(insight_id)

    def delete_insight(self, insight_id: str) -> bool:
        if insight_id in self._insights:
            del self._insights[insight_id]
            file = self.storage_dir / f"{insight_id}.json"
            if file.exists():
                file.unlink()
            return True
        return False
