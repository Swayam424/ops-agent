import json
from config import client
from task_manager import handle_task, load_tasks
from email_agent import handle_email, load_emails
from calendar_agent import handle_calendar, load_events

def is_list_request(user_input):
    text = user_input.lower()
    return any(word in text for word in ["list", "show my", "what are my", "view my"])

def format_list(items, kind):
    if not items:
        return f"No {kind} found."
    lines = [f"{i+1}. {item.get('text', item)}" for i, item in enumerate(items)]
    return f"Your {kind}:\n" + "\n".join(lines)

def decompose_request(user_input):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": (
                "Break the user's message into one or more sub-tasks. "
                "Respond ONLY with a JSON array, no explanation, no markdown fences. "
                "Each item must be: {\"worker\": \"task\"|\"email\"|\"calendar\", \"text\": \"...\"}. "
                "worker='task' for to-dos/reminders with no specific person involved. "
                "worker='email' for messages meant to be sent to a specific person. "
                "worker='calendar' for scheduling meetings/appointments/events. "
                "Example input: 'remind me to submit assignment tonight and email professor about extension' "
                "Example output: [{\"worker\":\"task\",\"text\":\"submit assignment tonight\"},{\"worker\":\"email\",\"text\":\"email professor about extension\"}]"
            )},
            {"role": "user", "content": user_input}
        ]
    )
    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None

def route_request(user_input):
    if is_list_request(user_input):
        text = user_input.lower()
        if "email" in text:
            return format_list(load_emails(), "emails")
        elif "calendar" in text or "event" in text:
            return format_list(load_events(), "events")
        else:
            return format_list(load_tasks(), "tasks")

    subtasks = decompose_request(user_input)
    if not subtasks:
        return handle_task(user_input)  # fallback if parsing fails

    results = []
    for st in subtasks:
        worker = st.get("worker")
        text = st.get("text", user_input)
        if worker == "email":
            results.append(handle_email(text))
        elif worker == "calendar":
            results.append(handle_calendar(text))
        else:
            results.append(handle_task(text))
    return "\n".join(results)

if __name__ == "__main__":
    while True:
        q = input("You: ")
        if q.lower() == "exit":
            break
        print("Router:", route_request(q))
