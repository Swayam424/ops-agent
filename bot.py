import discord
from config import DISCORD_TOKEN, client
from task_manager import handle_task
from email_agent import handle_email
from calendar_agent import handle_calendar

intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

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
    decision = get_route_decision(user_input)
    if "email" in decision:
        return handle_email(user_input)
    elif "calendar" in decision:
        return handle_calendar(user_input)
    else:
        return handle_task(user_input)

@discord_client.event
async def on_ready():
    print(f"Logged in as {discord_client.user}")

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return
    result = route_request(message.content)
    await message.channel.send(result)

discord_client.run(DISCORD_TOKEN)
