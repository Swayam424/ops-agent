import json
import os

TASKS_FILE = "tasks.json"


def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, "r") as f:
        return json.load(f)


def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


def handle_task(request):
    tasks = load_tasks()
    tasks.append(request)
    save_tasks(tasks)
    return f"[task_manager] Saved task: '{request}' (total tasks: {len(tasks)})"
