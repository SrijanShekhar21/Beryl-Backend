import uuid
from typing import Dict, Optional
from app.analysis.orchestrator import AnalysisOrchestrator


class SessionStore:
    """
    Stores one AnalysisOrchestrator per user session.
    Each orchestrator holds the FinalOutput and ChromaDB index
    for that user's search — so follow-ups work correctly
    without mixing up data between users.
    """

    def __init__(self):
        self._sessions: Dict[str, AnalysisOrchestrator] = {}

    def create_session(self) -> tuple[str, AnalysisOrchestrator]:
        """
        Creates a new session with a fresh AnalysisOrchestrator.
        Returns (session_id, orchestrator).
        """
        session_id = str(uuid.uuid4())
        orchestrator = AnalysisOrchestrator()
        self._sessions[session_id] = orchestrator
        print(f"[Session] Created session: {session_id}")
        return session_id, orchestrator

    def get_session(self, session_id: str) -> Optional[AnalysisOrchestrator]:
        """
        Returns the orchestrator for this session, or None if not found.
        """
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> None:
        """
        Cleans up a session when user is done.
        Important for memory management — each orchestrator
        holds a ChromaDB index and embedding model in memory.
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            print(f"[Session] Deleted session: {session_id}")

    def active_sessions(self) -> int:
        return len(self._sessions)


# Single global instance shared across all requests
# FastAPI is async but our pipeline is sync, so this is safe
session_store = SessionStore()