import asyncio
import os

import discord
from discord.ext import commands

# Create and set an event loop.
# Explicitly for Python 3.14+
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Set up bot.
intents = discord.Intents.default()
intents.message_content = False
bot = discord.Bot(intents = intents)

# Load cogs to register commands.
bot.load_extension("cogs.network")
bot.load_extension("cogs.cs_lobby")

# Log to console when logging in to discord.
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# Connect bot to discord network.
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN is missing from environment variables!")
bot.run(token)
