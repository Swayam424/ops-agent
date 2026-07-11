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

def get_route_decision(user_input):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a router. Given a user request, respond with ONLY ONE WORD: 'task', 'email', or 'calendar' — whichever worker should handle it. No explanation, no punctuation."},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content.strip().lower()

def route_request(user_input):
    if is_list_request(user_input):
        decision = get_route_decision(user_input)
        if "email" in decision:
            return format_list(load_emails(), "emails")
        elif "calendar" in decision:
            return format_list(load_events(), "events")
        else:
            return format_list(load_tasks(), "tasks")

    decision = get_route_decision(user_input)
    if "email" in decision:
        return handle_email(user_input)
    elif "calendar" in decision:
        return handle_calendar(user_input)
    else:
        return handle_task(user_input)

if __name__ == "__main__":
    while True:
        q = input("You: ")
        if q.lower() == "exit":
            break
        print("Router:", route_request(q))
