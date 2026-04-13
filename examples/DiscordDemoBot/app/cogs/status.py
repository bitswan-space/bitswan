from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from app.cogs.helpers import get_active_meeting, refresh_status_embed
from app.database import async_session


class StatusCog(commands.Cog):
    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot

    @app_commands.command(name="status", description="Refresh and repost the demo status embed")
    async def status(self, interaction: discord.Interaction) -> None:
        async with async_session() as db:
            meeting = await get_active_meeting(db)
        if not meeting:
            await interaction.response.send_message("No active meeting. Use /meeting_new to start one.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        await refresh_status_embed(self.bot)
        await interaction.followup.send("Status embed refreshed.", ephemeral=True)


async def setup(bot: discord.Client) -> None:
    await bot.add_cog(StatusCog(bot))
