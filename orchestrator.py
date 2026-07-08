import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def ask_orchestrator(user_input):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a planning orchestrator for a personal ops assistant. You don't execute tasks yourself — you decide which worker (task_manager, email_agent, calendar_agent) should handle the request. Just respond with your reasoning for now.",
            },
            {"role": "user", "content": user_input},
        ],
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    while True:
        q = input("You: ")
        if q.lower() == "exit":
            break
        print("Orchestrator:", ask_orchestrator(q))
