# src/feedback.py
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

# Simple file-based feedback storage
FEEDBACK_FILE = "data/feedback_records.json"

def _ensure_feedback_file():
    """Make sure the feedback file exists."""
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, "w") as f:
            json.dump([], f)

def record_feedback(session_id: str, rating: str, comments: Optional[str] = None) -> Dict[str, Any]:
    """
    Record user feedback for continuous improvement.
    
    Args:
        session_id: The user's session identifier
        rating: User rating (e.g., "good", "bad")
        comments: Optional detailed feedback
    
    Returns:
        Dict containing the recorded feedback
    """
    _ensure_feedback_file()
    
    # Create feedback entry
    feedback_entry = {
        "session_id": session_id,
        "rating": rating,
        "comments": comments,
        "timestamp": datetime.now().isoformat()
    }
    
    # Read existing feedback
    try:
        with open(FEEDBACK_FILE, "r") as f:
            feedback_data = json.load(f)
    except:
        feedback_data = []
    
    # Add new feedback
    feedback_data.append(feedback_entry)
    
    # Write back to file
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(feedback_data, f, indent=2)
    
    return feedback_entry

def get_feedback_stats() -> Dict[str, Any]:
    """Get statistics about recorded feedback."""
    _ensure_feedback_file()
    
    try:
        with open(FEEDBACK_FILE, "r") as f:
            feedback_data = json.load(f)
    except:
        feedback_data = []
    
    total = len(feedback_data)
    good_ratings = sum(1 for item in feedback_data if item.get("rating") == "good")
    
    return {
        "total_feedback": total,
        "positive_ratings": good_ratings,
        "positive_percentage": (good_ratings / total * 100) if total > 0 else 0,
        "recent_feedback": feedback_data[-5:] if feedback_data else []
    }
