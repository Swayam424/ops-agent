import json
import os
import asyncio
import discord
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1427743642159681579

def load_json(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "r") as f:
        return json.load(f)

def is_due_today(date_phrase):
    today = datetime.now().strftime("%A, %B %d, %Y")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": f"Today is {today}. Given a date/time phrase, respond with ONLY 'yes' or 'no' — is this due today or already overdue? No explanation."},
            {"role": "user", "content": date_phrase}
        ]
    )
    return response.choices[0].message.content.strip().lower() == "yes"

def check_due_items():
    tasks = load_json("tasks.json")
    events = load_json("calendar.json")
    due_today = []

    for t in tasks:
        due = t.get("due", "unspecified")
        if due != "unspecified" and is_due_today(due):
            due_today.append(f"Task: {t['text']} (due: {due})")

    for e in events:
        date = e.get("date", "TBD")
        if date not in ["TBD", "unspecified"] and is_due_today(date):
            due_today.append(f"Event: {e['text']} (date: {date})")

    return due_today

async def send_reminder():
    items = check_due_items()
    if not items:
        print("Nothing due today.")
        return

    intents = discord.Intents.default()
    client_discord = discord.Client(intents=intents)

    @client_discord.event
    async def on_ready():
        channel = client_discord.get_channel(CHANNEL_ID)
        message = "**Reminders for today:**\n" + "\n".join(f"- {i}" for i in items)
        await channel.send(message)
        await client_discord.close()

    await client_discord.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(send_reminder())
