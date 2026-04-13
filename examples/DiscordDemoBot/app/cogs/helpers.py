"""Shared helpers used across cogs."""
from __future__ import annotations

import discord
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.embed import build_status_embed
from app.models.attendance import Attendance
from app.models.meeting import Meeting
from app.models.person import Person
from app.models.project import Project
from app.models.topic import Topic


async def get_active_meeting(db: AsyncSession) -> Meeting | None:
    result = await db.execute(select(Meeting).order_by(Meeting.meeting_date.desc()).limit(1))
    return result.scalars().first()


async def resolve_person(db: AsyncSession, name: str) -> Person | None:
    result = await db.execute(
        select(Person).where(Person.name.ilike(f"%{name}%"))
    )
    return result.scalars().first()


async def resolve_project(db: AsyncSession, name: str) -> Project | None:
    result = await db.execute(
        select(Project).where(Project.name.ilike(f"%{name}%"))
    )
    return result.scalars().first()


async def refresh_status_embed(bot: discord.Client) -> None:
    """Rebuild and edit (or post) the live status embed for the active meeting."""
    async with async_session() as db:
        meeting = await get_active_meeting(db)
        if not meeting:
            return

        # Attendance
        rows = (await db.execute(
            select(Attendance, Person)
            .join(Person, Person.id == Attendance.person_id)
            .where(Attendance.meeting_id == meeting.id)
            .order_by(Person.name)
        )).all()
        present = [p.name for _, p in rows if _.present]
        absent  = [p.name for _, p in rows if not _.present]

        # Projects with topics
        projects = (await db.execute(select(Project).order_by(Project.name))).scalars().all()
        projects_data = []
        for proj in projects:
            guarantor = (await db.execute(select(Person).where(Person.id == proj.guarantor_id))).scalars().first()
            topics_rows = (await db.execute(
                select(Topic, Person)
                .join(Person, Person.id == Topic.presenter_id)
                .where(Topic.meeting_id == meeting.id, Topic.project_id == proj.id)
            )).all()
            topics = [(t.title, p.name) for t, p in topics_rows]
            projects_data.append((proj.name, guarantor.name if guarantor else "—", topics))

        embed = build_status_embed(
            str(meeting.meeting_date),
            present,
            absent,
            projects_data,
        )

        channel = bot.get_channel(int(meeting.status_channel_id))
        if channel is None:
            return

        if meeting.status_message_id:
            try:
                msg = await channel.fetch_message(int(meeting.status_message_id))
                await msg.edit(embed=embed)
                return
            except discord.NotFound:
                pass

        msg = await channel.send(embed=embed)
        meeting.status_message_id = str(msg.id)
        await db.commit()
