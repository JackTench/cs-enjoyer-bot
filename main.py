import os

import discord
from discord.ext import commands

# Set up bot.
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents = intents)

# Log to console when logging in to discord.
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# Connect bot to discord network.
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN is missing from environment variables!")
bot.run(token)
