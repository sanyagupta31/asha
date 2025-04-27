# src/analytics.py
import json
import os
from datetime import datetime

ANALYTICS_FILE = "data/analytics_log.json"

def log_analytics(event_type, session_id, details):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "session_id": session_id,
        "details": details
    }
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(ANALYTICS_FILE):
        with open(ANALYTICS_FILE, "w") as f:
            json.dump([], f)
    with open(ANALYTICS_FILE, "r") as f:
        data = json.load(f)
    data.append(entry)
    with open(ANALYTICS_FILE, "w") as f:
        json.dump(data, f, indent=2)
