"""Discord Demo Bot — entry point."""
from __future__ import annotations

import asyncio
import logging
import os

import discord
from discord.ext import commands

from app.database import async_session, init_db
from app.seed import preseed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("demo-bot")

COGS = [
    "app.cogs.checkin",
    "app.cogs.topics",
    "app.cogs.meetings",
    "app.cogs.registry",
    "app.cogs.status",
    "app.cogs.export",
]


class DemoBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        for cog in COGS:
            await self.load_extension(cog)
            log.info("Loaded cog: %s", cog)

        guild_id = os.environ.get("DISCORD_GUILD_ID")
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            log.info("Slash commands synced to guild %s", guild_id)
        else:
            await self.tree.sync()
            log.info("Slash commands synced globally")

    async def on_ready(self) -> None:
        log.info("Logged in as %s (id=%s)", self.user, self.user.id)


async def main() -> None:
    token = os.environ["DISCORD_TOKEN"]

    await init_db()
    log.info("Database initialised")

    async with async_session() as db:
        await preseed(db)
    log.info("Seed complete")

    bot = DemoBot()
    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
