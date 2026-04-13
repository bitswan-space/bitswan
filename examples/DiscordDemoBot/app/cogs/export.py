from __future__ import annotations

import io

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select

from app.cogs.helpers import get_active_meeting
from app.database import async_session
from app.docx_export import generate_docx
from app.models.attendance import Attendance
from app.models.person import Person
from app.models.project import Project
from app.models.topic import Topic


class ExportCog(commands.Cog):
    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot

    @app_commands.command(name="export", description="Export the current meeting as a .docx file")
    async def export(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        async with async_session() as db:
            meeting = await get_active_meeting(db)
            if not meeting:
                await interaction.followup.send("No active meeting.", ephemeral=True)
                return

            att_rows = (await db.execute(
                select(Attendance, Person)
                .join(Person, Person.id == Attendance.person_id)
                .where(Attendance.meeting_id == meeting.id)
                .order_by(Person.name)
            )).all()
            present = [p.name for a, p in att_rows if a.present]
            absent  = [p.name for a, p in att_rows if not a.present]
            all_persons = [p.name for _, p in att_rows]

            projects = (await db.execute(select(Project).order_by(Project.name))).scalars().all()
            projects_data = []
            for proj in projects:
                guarantor = (await db.execute(select(Person).where(Person.id == proj.guarantor_id))).scalars().first()
                topics_rows = (await db.execute(
                    select(Topic, Person)
                    .join(Person, Person.id == Topic.presenter_id)
                    .where(Topic.meeting_id == meeting.id, Topic.project_id == proj.id)
                )).all()
                projects_data.append((proj.name, guarantor.name if guarantor else "—", [(t.title, p.name) for t, p in topics_rows]))

        data = await generate_docx(str(meeting.meeting_date), present, absent, all_persons, projects_data)
        filename = f"demo-registration-{meeting.meeting_date}.docx"
        await interaction.followup.send(file=discord.File(io.BytesIO(data), filename=filename))


async def setup(bot: discord.Client) -> None:
    await bot.add_cog(ExportCog(bot))
