from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select

from app.cogs.helpers import get_active_meeting, refresh_status_embed, resolve_person
from app.database import async_session
from app.models.attendance import Attendance
from app.models.person import Person


class CheckinCog(commands.Cog):
    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot

    @app_commands.command(name="checkin", description="Mark a person as present for today's meeting")
    @app_commands.describe(name="Name of the person (partial match works)")
    async def checkin(self, interaction: discord.Interaction, name: str) -> None:
        async with async_session() as db:
            person = await resolve_person(db, name)
            if not person:
                await interaction.response.send_message(f"No person found matching '{name}'. Use /person add first.", ephemeral=True)
                return
            meeting = await get_active_meeting(db)
            if not meeting:
                await interaction.response.send_message("No active meeting. Use /meeting new first.", ephemeral=True)
                return
            row = (await db.execute(
                select(Attendance).where(Attendance.meeting_id == meeting.id, Attendance.person_id == person.id)
            )).scalars().first()
            if row:
                row.present = True
            else:
                db.add(Attendance(meeting_id=meeting.id, person_id=person.id, present=True))
            await db.commit()

        await refresh_status_embed(self.bot)
        await interaction.response.send_message(f"Marked **{person.name}** as present.", ephemeral=True)

    @checkin.autocomplete("name")
    async def checkin_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        async with async_session() as db:
            rows = (await db.execute(
                select(Person).where(Person.name.ilike(f"%{current}%")).limit(25)
            )).scalars().all()
        return [app_commands.Choice(name=p.name, value=p.name) for p in rows]

    @app_commands.command(name="checkout", description="Mark a person as absent for today's meeting")
    @app_commands.describe(name="Name of the person")
    async def checkout(self, interaction: discord.Interaction, name: str) -> None:
        async with async_session() as db:
            person = await resolve_person(db, name)
            if not person:
                await interaction.response.send_message(f"No person found matching '{name}'.", ephemeral=True)
                return
            meeting = await get_active_meeting(db)
            if not meeting:
                await interaction.response.send_message("No active meeting.", ephemeral=True)
                return
            row = (await db.execute(
                select(Attendance).where(Attendance.meeting_id == meeting.id, Attendance.person_id == person.id)
            )).scalars().first()
            if row:
                row.present = False
                await db.commit()

        await refresh_status_embed(self.bot)
        await interaction.response.send_message(f"Marked **{person.name}** as absent.", ephemeral=True)

    @checkout.autocomplete("name")
    async def checkout_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return await self.checkin_autocomplete(interaction, current)


async def setup(bot: discord.Client) -> None:
    await bot.add_cog(CheckinCog(bot))
