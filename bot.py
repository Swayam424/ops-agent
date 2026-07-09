import os
import discord
from dotenv import load_dotenv
from groq import Groq
from task_manager import handle_task
from email_agent import handle_email
from calendar_agent import handle_calendar

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def get_route_decision(user_input):
    response = client_groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a router. Given a user request, respond with ONLY ONE WORD: 'task', 'email', or 'calendar' — whichever worker should handle it. No explanation, no punctuation."},
            {"role": "user", "content": user_input}
        ]
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

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    result = route_request(message.content)
    await message.channel.send(result)

client.run(DISCORD_TOKEN)
