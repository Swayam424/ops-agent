import os

from dotenv import load_dotenv
from groq import Groq

from calendar_agent import handle_calendar
from email_agent import handle_email
from task_manager import handle_task

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def get_route_decision(user_input):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a router. Given a user request, respond with ONLY ONE WORD: 'task', 'email', or 'calendar' — whichever worker should handle it. No explanation, no punctuation.",
            },
            {"role": "user", "content": user_input},
        ],
    )
    return response.choices[0].message.content.strip().lower()


def route_request(user_input):
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
