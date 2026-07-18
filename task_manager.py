import json
import os
from config import client

TASKS_FILE = "tasks.json"

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, "r") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def extract_due_date(request):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Extract only the due date/deadline mentioned in this request. Respond with ONLY the date/time phrase (e.g. 'tonight', 'friday', 'next week'). If none mentioned, respond 'unspecified'."},
            {"role": "user", "content": request}
        ]
    )
    return response.choices[0].message.content.strip()

def handle_task(request, update_index=None):
    tasks = load_tasks()
    due = extract_due_date(request)

    if update_index is not None and 0 <= update_index < len(tasks):
        tasks[update_index] = {"text": request, "due": due}
        save_tasks(tasks)
        return f"[task_manager] Updated task: '{request}' (due: {due})"

    tasks.append({"text": request, "due": due})
    save_tasks(tasks)
    return f"[task_manager] Saved task: '{request}' (due: {due})"
