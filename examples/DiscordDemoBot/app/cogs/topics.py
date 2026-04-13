from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select

from app.cogs.helpers import get_active_meeting, refresh_status_embed, resolve_person, resolve_project
from app.database import async_session
from app.models.person import Person
from app.models.project import Project
from app.models.topic import Topic


class TopicsCog(commands.Cog):
    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot

    topic_group = app_commands.Group(name="topic", description="Manage presentation topics")

    @topic_group.command(name="add", description="Register a presentation topic under a project")
    @app_commands.describe(project="Project name", title="Topic title", presenter="Presenter name")
    async def topic_add(self, interaction: discord.Interaction, project: str, title: str, presenter: str) -> None:
        async with async_session() as db:
            proj = await resolve_project(db, project)
            if not proj:
                await interaction.response.send_message(f"Project '{project}' not found.", ephemeral=True)
                return
            person = await resolve_person(db, presenter)
            if not person:
                await interaction.response.send_message(f"Person '{presenter}' not found.", ephemeral=True)
                return
            meeting = await get_active_meeting(db)
            if not meeting:
                await interaction.response.send_message("No active meeting. Use /meeting new first.", ephemeral=True)
                return
            db.add(Topic(meeting_id=meeting.id, project_id=proj.id, title=title, presenter_id=person.id))
            await db.commit()

        await refresh_status_embed(self.bot)
        await interaction.response.send_message(
            f"Added topic **{title}** under **{proj.name}**, presented by **{person.name}**.", ephemeral=True
        )

    @topic_add.autocomplete("project")
    async def project_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        async with async_session() as db:
            rows = (await db.execute(
                select(Project).where(Project.name.ilike(f"%{current}%")).limit(25)
            )).scalars().all()
        return [app_commands.Choice(name=p.name, value=p.name) for p in rows]

    @topic_add.autocomplete("presenter")
    async def presenter_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        async with async_session() as db:
            rows = (await db.execute(
                select(Person).where(Person.name.ilike(f"%{current}%")).limit(25)
            )).scalars().all()
        return [app_commands.Choice(name=p.name, value=p.name) for p in rows]

    @topic_group.command(name="remove", description="Remove a presentation topic from this meeting")
    @app_commands.describe(project="Project name", title="Topic title to remove")
    async def topic_remove(self, interaction: discord.Interaction, project: str, title: str) -> None:
        async with async_session() as db:
            proj = await resolve_project(db, project)
            meeting = await get_active_meeting(db)
            if not proj or not meeting:
                await interaction.response.send_message("Project or active meeting not found.", ephemeral=True)
                return
            row = (await db.execute(
                select(Topic).where(
                    Topic.meeting_id == meeting.id,
                    Topic.project_id == proj.id,
                    Topic.title.ilike(title),
                ).limit(1)
            )).scalars().first()
            if not row:
                await interaction.response.send_message(f"Topic '{title}' not found under {proj.name}.", ephemeral=True)
                return
            await db.delete(row)
            await db.commit()

        await refresh_status_embed(self.bot)
        await interaction.response.send_message(f"Removed topic **{title}** from **{proj.name}**.", ephemeral=True)

    @topic_remove.autocomplete("project")
    async def remove_project_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return await self.project_autocomplete(interaction, current)

    @topic_remove.autocomplete("title")
    async def remove_title_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        async with async_session() as db:
            meeting = await get_active_meeting(db)
            if not meeting:
                return []
            rows = (await db.execute(
                select(Topic).where(
                    Topic.meeting_id == meeting.id,
                    Topic.title.ilike(f"%{current}%"),
                ).limit(25)
            )).scalars().all()
        return [app_commands.Choice(name=t.title, value=t.title) for t in rows]


async def setup(bot: discord.Client) -> None:
    await bot.add_cog(TopicsCog(bot))
