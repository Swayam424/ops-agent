import json
from config import client
from task_manager import handle_task, load_tasks
from email_agent import handle_email, load_emails
from calendar_agent import handle_calendar, load_events
from memory import add_exchange, get_recent_context

def is_list_request(user_input):
    text = user_input.lower()
    return any(word in text for word in ["list", "show my", "what are my", "view my"])

def format_list(items, kind):
    if not items:
        return f"No {kind} found."
    lines = [f"{i+1}. {item.get('text', item)}" for i, item in enumerate(items)]
    return f"Your {kind}:\n" + "\n".join(lines)

def decompose_request(user_input):
    context = get_recent_context(n=5)
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": (
                    "Break the user's message into one or more sub-tasks. "
                    "You have access to recent conversation history for context.\n\n"
                    f"Recent conversation:\n{context}\n\n"
                    "Respond ONLY with a JSON array, no explanation, no markdown fences. "
                    "Each item must be: {\"worker\": \"task\"|\"email\"|\"calendar\", \"text\": \"...\", \"is_update\": true|false}. "
                    "Set is_update=true ONLY if this message is clearly correcting/modifying something just discussed "
                    "(e.g. 'actually make that 5pm instead', 'change it to friday'). Otherwise is_update=false.\n"
                    "Rules to decide worker:\n"
                    "- 'calendar': ONLY for scheduling a meeting/appointment/event at a specific time with another person, or something explicitly called a 'meeting', 'appointment', or 'event'.\n"
                    "- 'email': ONLY when the message is about sending/telling something to a specific named person (mom, professor, boss, etc).\n"
                    "- 'task': everything else — personal to-dos, reminders, errands, deadlines — even if they mention a date/time like 'tomorrow' or 'tonight'. A reminder to do something yourself is ALWAYS 'task', never 'calendar', unless it explicitly says 'meeting' or 'appointment'.\n"
                    "Example: 'buy groceries tomorrow' -> [{\"worker\":\"task\",\"text\":\"buy groceries tomorrow\",\"is_update\":false}]\n"
                    "Example: 'schedule a meeting with professor friday' -> [{\"worker\":\"calendar\",\"text\":\"schedule a meeting with professor friday\",\"is_update\":false}]\n"
                    "Example: (after scheduling a professor meeting) 'actually make that 5pm instead' -> [{\"worker\":\"calendar\",\"text\":\"meeting with professor at 5pm\",\"is_update\":true}]"
                )},
                {"role": "user", "content": user_input}
            ]
        )
        raw = response.choices[0].message.content.strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        print("[warning] LLM returned malformed JSON, falling back to task")
        return None
    except Exception as e:
        print(f"[error] Groq API call failed: {e}")
        return None

def get_last_calendar_event_id():
    events = load_events()
    for e in reversed(events):
        if e.get("google_event_id"):
            return e["google_event_id"]
    return None

def route_request(user_input):
    if is_list_request(user_input):
        text = user_input.lower()
        if "email" in text:
            result = format_list(load_emails(), "emails")
        elif "calendar" in text or "event" in text:
            result = format_list(load_events(), "events")
        else:
            result = format_list(load_tasks(), "tasks")
        add_exchange(user_input, result)
        return result

    subtasks = decompose_request(user_input)
    if not subtasks:
        result = "Sorry, I couldn't process that request right now. Please try again."
        add_exchange(user_input, result)
        return result

    results = []
    for st in subtasks:
        worker = st.get("worker")
        text = st.get("text", user_input)
        is_update = st.get("is_update", False)
        try:
            if worker == "email":
                results.append(handle_email(text))
            elif worker == "calendar":
                if is_update:
                    event_id = get_last_calendar_event_id()
                    results.append(handle_calendar(text, update_event_id=event_id))
                else:
                    results.append(handle_calendar(text))
            else:
                results.append(handle_task(text))
        except Exception as e:
            results.append(f"[error] Failed to process '{text}': {e}")
    result = "\n".join(results)
    add_exchange(user_input, result)
    return result

if __name__ == "__main__":
    while True:
        q = input("You: ")
        if q.lower() == "exit":
            break
        print("Router:", route_request(q))
