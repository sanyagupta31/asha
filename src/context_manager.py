# src/context_manager.py

from typing import List, Dict, Any

# In-memory session store: {session_id: [{"role": "user"/"bot", "content": ...}, ...]}
_sessions: Dict[str, List[Dict[str, Any]]] = {}

def get_history(session_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve the conversation history for a given session.
    Returns a list of message dicts: [{"role": "user", "content": ...}, ...]
    """
    return _sessions.get(session_id, [])

def add_message(session_id: str, role: str, content: str) -> None:
    """
    Add a message to the session history.
    role: "user" or "bot"
    content: message text
    """
    if session_id not in _sessions:
        _sessions[session_id] = []
    _sessions[session_id].append({"role": role, "content": content})

def clear_history(session_id: str) -> None:
    """
    Clear the conversation history for a session (if needed).
    """
    if session_id in _sessions:
        del _sessions[session_id]

def get_recent_history(session_id: str, n: int = 5) -> List[Dict[str, Any]]:
    """
    Get the last n messages from the session history (for context window).
    """
    return get_history(session_id)[-n:]
