import asyncio

import discord
from discord.ext import commands

from services.cs_lobby import (
    Lobby,
    ServiceCounterStrikeLobby,
    AlreadyJoined,
    LobbyAlreadyExists,
    LobbyClosed,
    LobbyFull,
    LobbyNotFound,
    NotInLobby,
)

class JoinLobbyButton(discord.ui.Button):
    def __init__(self, cog: "CogCounterStrikeLobby", lobby_id: str, label: str, disabled: bool):
        super().__init__(
            style = discord.ButtonStyle.primary,
            label = label,
            custom_id = f"join:{lobby_id}",
            disabled = disabled,
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        if interaction.message is None:
            await interaction.response.send_message("Could not find the signup message.", ephemeral = True)
            return

        # Attempt to join lobby.
        try:
            lobby = self.cog.service.join_lobby(interaction.message.id, interaction.user.id)
        # Handle errors when joining lobby.
        except LobbyNotFound as e:
            await interaction.response.send_message(str(e), ephemeral = True)
            return
        except LobbyClosed as e:
            await interaction.response.send_message(str(e), ephemeral = True)
            return
        except AlreadyJoined as e:
            await interaction.response.send_message(str(e), ephemeral = True)
            return
        except LobbyFull as e:
            await interaction.response.send_message(str(e), ephemeral = True)
            return

        await interaction.response.edit_message(
            embed = self.cog.build_embed(lobby),
            view = self.cog.build_view(lobby),
        )

        if len(lobby.players) == 5:
            try:
                message = await interaction.channel.fetch_message(interaction.message.id)
                closed_lobby = self.cog.service.close_lobby(message.id, "full")

                await message.edit(
                    embed = self.cog.build_embed(closed_lobby),
                    view = self.cog.build_view(closed_lobby),
                )

                mentions = " ".join(f"<@{user_id}>" for user_id in closed_lobby.players)
                await message.channel.send(f"Game ready: {mentions}")
            except Exception as err:
                print(f"Failed to close full lobby: {err}")

class LeaveLobbyButton(discord.ui.Button):
    def __init__(self, cog: "CogCounterStrikeLobby", lobby_id: str, disabled: bool):
        super().__init__(
            style = discord.ButtonStyle.secondary,
            label = "Leave",
            custom_id = f"leave:{lobby_id}",
            disabled = disabled,
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        if interaction.message is None:
            return

        try:
            lobby = self.cog.service.leave_lobby(
                interaction.message.id,
                interaction.user.id,
            )
        except NotInLobby as e:
            return
        except LobbyClosed as e:
            return

        await interaction.response.edit_message(
            embed = self.cog.build_embed(lobby),
            view = self.cog.build_view(lobby),
        )

class CogCounterStrikeLobby(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.service = ServiceCounterStrikeLobby()

    def build_embed(self, lobby: Lobby) -> discord.Embed:
        title = "CS Lobby"
        if lobby.status == "full":
            title = "CS Lobby - Full"
        elif lobby.status == "expired":
            title = "CS Lobby - Closed"

        roster = "\n".join(
            f"{index + 1}. <@{user_id}>"
            for index, user_id in enumerate(lobby.players)
        ) or "No players"

        time_remaining = (
            f"{self.service.minutes_left(lobby)} min"
            if lobby.status == "open"
            else "Ended"
        )

        return discord.Embed(
            title = title,
            description = "\n".join(
                [
                    f"**Host:** <@{lobby.host_id}>",
                    f"**Players:** {len(lobby.players)}/5",
                    f"**Time remaining:** {time_remaining}",
                    "",
                    "**Roster**",
                    roster,
                ]
            )
        )

    def build_view(self, lobby: Lobby) -> discord.ui.View:
        view = discord.ui.View(timeout = None)
        view.add_item(
            JoinLobbyButton(
                cog = self,
                lobby_id = lobby.id,
                label = f"Join({len(lobby.players)}/5)",
                disabled = (lobby.status != "open" or len(lobby.players) >= 5),
            )
        )
        view.add_item(
            LeaveLobbyButton(
                cog = self,
                lobby_id = lobby.id,
                disabled = (lobby.status != "open")
            )
        )
        return view

    async def expire_lobby_after_delay(self, channel_id: int, message_id: int, delay_seconds: int):
        await asyncio.sleep(delay_seconds)

        lobby = self.service.expire_lobby_if_needed(message_id)
        if lobby is None:
            return

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as err:
                print(f"Failed to fetch channel for expiring lobby: {err}")
                return

        try:
            message = await channel.fetch_message(message_id)
            await message.edit(
                embed = self.build_embed(lobby),
                view = self.build_view(lobby),
            )

            mentions = " ".join(f"<@{user_id}>" for user_id in lobby.players)
            await message.channel.send(f"Signup closed. Final roster: {mentions}")
        except Exception as err:
            print(f"Failed to expire lobby: {err}")

    @discord.slash_command(name = "wanttoplay", description = "Start a Counter-Strike lobby")
    async def wanttoplay(self, ctx: discord.ApplicationContext):
        # Check command is being run in a server channel.
        if ctx.channel is None:
            await ctx.respond("This command can only be used in a server channel.", ephemeral = True)
            return

        try:
            # Register lobby via service class.
            lobby = self.service.create_lobby(
                channel_id = ctx.channel.id,
                host_id = ctx.user.id,
                duration_mins = 30,
            )
        # Fail if lobby already exists in context.
        except LobbyAlreadyExists as e:
            await ctx.respond(str(e), ephemeral = True)
            return

        await ctx.respond(
            embed = self.build_embed(lobby),
            view = self.build_view(lobby),
        )

        message = await ctx.interaction.original_response()
        self.service.attach_message(lobby, message.id)

        asyncio.create_task(
            self.expire_lobby_after_delay(
                channel_id = ctx.channel.id,
                message_id = message.id,
                delay_seconds = 30 * 60,
            )
        )

def setup(bot: commands.Bot):
    bot.add_cog(CogCounterStrikeLobby(bot))
