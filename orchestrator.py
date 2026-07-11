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
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": (
                    "Break the user's message into one or more sub-tasks. "
                    "Respond ONLY with a JSON array, no explanation, no markdown fences. "
                    "Each item must be: {\"worker\": \"task\"|\"email\"|\"calendar\", \"text\": \"...\"}. "
                    "Rules to decide worker:\n"
                    "- 'calendar': ONLY for scheduling a meeting/appointment/event at a specific time with another person, or something explicitly called a 'meeting', 'appointment', or 'event'.\n"
                    "- 'email': ONLY when the message is about sending/telling something to a specific named person (mom, professor, boss, etc).\n"
                    "- 'task': everything else — personal to-dos, reminders, errands, deadlines — even if they mention a date/time like 'tomorrow' or 'tonight'. A reminder to do something yourself is ALWAYS 'task', never 'calendar', unless it explicitly says 'meeting' or 'appointment'.\n"
                    "Example: 'buy groceries tomorrow' -> task (not calendar, no meeting mentioned)\n"
                    "Example: 'schedule a meeting with professor friday' -> calendar\n"
                    "Example: 'remind me to call insurance' -> task\n"
                    "Example: 'tell mom dinner will be late' -> email"
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
        return "Sorry, I couldn't process that request right now. Please try again."

    results = []
    for st in subtasks:
        worker = st.get("worker")
        text = st.get("text", user_input)
        try:
            if worker == "email":
                results.append(handle_email(text))
            elif worker == "calendar":
                results.append(handle_calendar(text))
            else:
                results.append(handle_task(text))
        except Exception as e:
            results.append(f"[error] Failed to process '{text}': {e}")
    return "\n".join(results)

if __name__ == "__main__":
    while True:
        q = input("You: ")
        if q.lower() == "exit":
            break
        print("Router:", route_request(q))
