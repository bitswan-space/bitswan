from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.cogs.helpers import get_active_meeting, resolve_person
from app.database import async_session
from app.models.attendance import Attendance
from app.models.person import Person
from app.models.project import Project


class RegistryCog(commands.Cog):
    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot

    person_group = app_commands.Group(name="person", description="Manage the attendee list")

    @person_group.command(name="add", description="Add someone to the standing attendee list")
    @app_commands.describe(name="Full name", email="Email address")
    async def person_add(self, interaction: discord.Interaction, name: str, email: str) -> None:
        async with async_session() as db:
            person = Person(name=name, email=email)
            db.add(person)
            try:
                await db.flush()
            except IntegrityError:
                await db.rollback()
                await interaction.response.send_message(f"A person named '{name}' already exists.", ephemeral=True)
                return

            meeting = await get_active_meeting(db)
            if meeting:
                db.add(Attendance(meeting_id=meeting.id, person_id=person.id, present=False))

            await db.commit()

        await interaction.response.send_message(f"Added **{name}** ({email}) to the attendee list.", ephemeral=True)

    project_group = app_commands.Group(name="project", description="Manage the project registry")

    @project_group.command(name="add", description="Add a project to the registry")
    @app_commands.describe(name="Project name", guarantor="Name of the guarantor")
    async def project_add(self, interaction: discord.Interaction, name: str, guarantor: str) -> None:
        async with async_session() as db:
            person = await resolve_person(db, guarantor)
            if not person:
                await interaction.response.send_message(f"No person found matching '{guarantor}'.", ephemeral=True)
                return
            proj = Project(name=name, guarantor_id=person.id)
            db.add(proj)
            try:
                await db.commit()
            except IntegrityError:
                await db.rollback()
                await interaction.response.send_message(f"Project '{name}' already exists.", ephemeral=True)
                return

        await interaction.response.send_message(f"Added project **{name}** (guarantor: {person.name}).", ephemeral=True)

    @project_add.autocomplete("guarantor")
    async def guarantor_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        async with async_session() as db:
            rows = (await db.execute(
                select(Person).where(Person.name.ilike(f"%{current}%")).limit(25)
            )).scalars().all()
        return [app_commands.Choice(name=p.name, value=p.name) for p in rows]


async def setup(bot: discord.Client) -> None:
    await bot.add_cog(RegistryCog(bot))
