"""
Session and Conversation Manager for Local Service AI.
Tracks the multi-turn lifecycle of customer inquiries:
[INITIAL_INPUT] -> [AWAITING_FOLLOWUP] -> [RECOMMENDED] -> [BOOKING_COMPLETED]
"""
import uuid
import time
from typing import Dict, Any, Optional
from .analyzer import ProblemAnalysis


class SessionState:
    INITIAL_INPUT = "INITIAL_INPUT"
    AWAITING_FOLLOWUP = "AWAITING_FOLLOWUP"
    RECOMMENDED = "RECOMMENDED"
    BOOKED = "BOOKED"


class ServiceSession:
    def __init__(self, session_id: Optional[str] = None):
        self.session_id: str = session_id or str(uuid.uuid4())
        self.created_at: float = time.time()
        self.state: str = SessionState.INITIAL_INPUT
        self.initial_query: str = ""
        self.has_image: bool = False
        self.analysis: Optional[ProblemAnalysis] = None
        self.follow_up_answer: Optional[str] = None
        self.location: Dict[str, float] = {"lat": 12.9716, "lon": 77.5946}
        self.city_name: str = "Bangalore (Central)"
        self.recommendations: Optional[Dict[str, Any]] = None
        self.selected_provider_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "state": self.state,
            "initial_query": self.initial_query,
            "has_image": self.has_image,
            "analysis": self.analysis.model_dump() if self.analysis else None,
            "follow_up_answer": self.follow_up_answer,
            "location": self.location,
            "city_name": self.city_name,
            "selected_provider_id": self.selected_provider_id,
        }


# In-memory session store
_SESSIONS: Dict[str, ServiceSession] = {}


def get_or_create_session(session_id: Optional[str] = None) -> ServiceSession:
    if session_id and session_id in _SESSIONS:
        return _SESSIONS[session_id]
    new_sess = ServiceSession(session_id)
    _SESSIONS[new_sess.session_id] = new_sess
    return new_sess


def get_session(session_id: str) -> Optional[ServiceSession]:
    return _SESSIONS.get(session_id)
