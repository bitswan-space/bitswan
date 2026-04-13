from __future__ import annotations

import datetime
import os

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.cogs.helpers import refresh_status_embed
from app.database import async_session
from app.models.attendance import Attendance
from app.models.meeting import Meeting
from app.models.person import Person


class MeetingsCog(commands.Cog):
    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot

    @app_commands.command(name="meeting_new", description="Start a new demo meeting")
    @app_commands.describe(date="Meeting date in YYYY-MM-DD format")
    async def meeting_new(self, interaction: discord.Interaction, date: str) -> None:
        try:
            meeting_date = datetime.date.fromisoformat(date)
        except ValueError:
            await interaction.response.send_message("Invalid date format. Use YYYY-MM-DD.", ephemeral=True)
            return

        channel_id = os.environ.get("DISCORD_STATUS_CHANNEL_ID", str(interaction.channel_id))

        async with async_session() as db:
            meeting = Meeting(
                meeting_date=meeting_date,
                status_channel_id=channel_id,
                status_message_id=None,
            )
            db.add(meeting)
            try:
                await db.flush()
            except IntegrityError:
                await db.rollback()
                await interaction.response.send_message(f"A meeting for {date} already exists.", ephemeral=True)
                return

            persons = (await db.execute(select(Person))).scalars().all()
            for person in persons:
                db.add(Attendance(meeting_id=meeting.id, person_id=person.id, present=False))

            await db.commit()

        await refresh_status_embed(self.bot)
        await interaction.response.send_message(
            f"New meeting started for **{date}**. Status embed posted in <#{channel_id}>.", ephemeral=True
        )


async def setup(bot: discord.Client) -> None:
    await bot.add_cog(MeetingsCog(bot))
