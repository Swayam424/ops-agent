import json
import os
from datetime import datetime

MEMORY_FILE = "conversation_history.json"
MAX_HISTORY = 20  # keep last 20 exchanges

def load_history():
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_history(history):
    with open(MEMORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def add_exchange(user_input, system_response):
    history = load_history()
    history.append({
        "timestamp": datetime.now().isoformat(),
        "user": user_input,
        "response": system_response
    })
    history = history[-MAX_HISTORY:]  # trim to last N
    save_history(history)

def get_recent_context(n=5):
    history = load_history()
    recent = history[-n:]
    if not recent:
        return "No prior conversation."
    lines = []
    for h in recent:
        lines.append(f"User: {h['user']}\nAssistant: {h['response']}")
    return "\n".join(lines)
