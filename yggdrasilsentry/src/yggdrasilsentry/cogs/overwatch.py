from discord.ext import commands
from typing import TYPE_CHECKING
import discord
from yggdrasilsentry.database.tables import get_session, Messages, Users, Guilds
from sqlmodel import select

from yggdrasilsentry.database.helpers import (
    upsert_guild,
    upsert_message,
    upsert_message_delete,
    upsert_message_edit,
    upsert_user,
)

from yggdrasilsentry.bot import Sentry


class Overwatch(commands.Cog):
    def __init__(self, bot: Sentry):
        self.bot: Sentry = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await upsert_guild(message.author.guild)
        await upsert_user(message.author)
        await upsert_message(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        await upsert_guild(after.author.guild)
        await upsert_user(after.author)
        await upsert_message_edit(after)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        await upsert_guild(message.author.guild)
        await upsert_user(message.author)
        await upsert_message_delete(message)


async def setup(bot: Sentry):
    await bot.add_cog(Overwatch(bot))
