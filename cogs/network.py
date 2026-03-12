import discord
from discord.ext import commands

class Network(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Checks latency to bot server. Mainly here just to test with.
    @discord.slash_command(name="ping_server", description = "Test latency to bot server.")
    async def ping_server(self, ctx: discord.ApplicationContext):
        await ctx.respond(f"Pong! {round(self.bot.latency * 1000)}ms")

def setup(bot):
    bot.add_cog(Network(bot))
