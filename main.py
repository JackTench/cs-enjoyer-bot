import os

import discord
from discord.ext import commands

# Set up bot.
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents = intents)

# Connect bot to discord network.
token = os.getenv("DISCORD_TOKEN")
bot.run(token)
