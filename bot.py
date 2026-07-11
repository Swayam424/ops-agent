import discord
from config import DISCORD_TOKEN
from orchestrator import route_request

intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

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
