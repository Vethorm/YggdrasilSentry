from yggdrasilsentry.bot import Sentry

from discord.ext import commands
import discord
from discord import app_commands

from yggdrasilsentry.database.helpers import upsert_guild, upsert_user
from yggdrasilsentry.database.tables import get_session, GuildUsers
from sqlmodel import select


@app_commands.guild_only()
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
class ChatManagement(commands.GroupCog, group_name="chat_management"):
    def __init__(self, bot: Sentry):
        self.bot: Sentry = bot

    @app_commands.command()
    @app_commands.default_permissions(administrator=True)
    async def cleanup(self, interaction: discord.Interaction, count: int):
        await interaction.response.defer(thinking=True)
        async for message in interaction.channel.history(
            limit=count, oldest_first=False
        ):
            await message.delete()
        await interaction.followup.send(f"Cleaned up chat!")


async def setup(bot: Sentry):
    await bot.add_cog(ChatManagement(bot))
