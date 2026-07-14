import threading
from flask import Flask
import discord
from config import DISCORD_TOKEN
from orchestrator import route_request

# --- Tiny web server so Render treats this as a Web Service ---
app = Flask(__name__)

@app.route("/")
def home():
    return "ops-agent bot is alive"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# --- Discord bot ---
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

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    discord_client.run(DISCORD_TOKEN)
