"""Build the live status embed — pure render, no DB access."""
from __future__ import annotations

import discord


def build_status_embed(
    meeting_date: str,
    present: list[str],
    absent: list[str],
    projects_with_topics: list[tuple[str, str, list[tuple[str, str]]]],
    # projects_with_topics: [(project_name, guarantor_name, [(title, presenter_name), ...]), ...]
) -> discord.Embed:
    embed = discord.Embed(
        title=f"Demo Meeting — {meeting_date}",
        color=0x5865F2,
    )

    # Attendance — two inline fields
    embed.add_field(
        name=f"Present ({len(present)})",
        value="\n".join(present) or "—",
        inline=True,
    )
    embed.add_field(
        name=f"Absent ({len(absent)})",
        value="\n".join(absent) or "—",
        inline=True,
    )

    # Spacer so projects start on a new line
    embed.add_field(name="\u200b", value="\u200b", inline=False)

    for project_name, guarantor_name, topics in projects_with_topics:
        if not topics:
            continue
        lines = [f"*guarantor: {guarantor_name}*"]
        for title, presenter in topics:
            lines.append(f"• {title} — {presenter}")
        value = "\n".join(lines)
        # Guard Discord's 1024-char field limit
        if len(value) > 1000:
            value = value[:997] + "…"
        embed.add_field(name=f"[{project_name}]", value=value, inline=False)

    embed.set_footer(text=f"Last updated: {discord.utils.utcnow().strftime('%H:%M UTC')}")
    return embed
