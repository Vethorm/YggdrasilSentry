from yggdrasilsentry.bot import Sentry

from discord.ext import commands
import discord
from discord import app_commands

from yggdrasilsentry.database.helpers import upsert_guild, upsert_user
from yggdrasilsentry.database.tables import get_session, GuildUsers, Messages
from sqlmodel import select

from typing import List


@app_commands.guild_only()
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
class Moderation(commands.GroupCog, group_name="moderation"):
    def __init__(self, bot: Sentry):
        self.bot: Sentry = bot

    @app_commands.command()
    async def user_logs(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(thinking=True)
        try:
            messages = await self.get_user_logs(user)
            messages: List[Messages]
            log_path = f"/tmp/{user.guild.id}_{user.id}_logs.txt"
            with open(log_path, "w") as f:
                for message in messages:
                    output = (
                        f"\n{message.message_type} - {message.id} - {message.message_date}\n"
                        f"{message.message_content}\n"
                        f"Attachments: {message.message_attachments}\n"
                    )
                    f.write(output)
            with open(log_path, "rb") as f:
                await interaction.followup.send(file=discord.File(f))
        except Exception as e:
            print(e)
            await interaction.followup.send("command failed")

    async def get_user_logs(self, user: discord.Member) -> List[Messages]:
        async with get_session() as session:
            print(f"Looking up {user.id} in guild {user.guild.id}")
            result = await session.exec(
                select(Messages).where(
                    Messages.user_id == user.id, Messages.guild_id == user.guild.id
                )
            )
            messages = [row for row in result]
            print(f"Found {len(messages)} user logs!")
            return messages


async def setup(bot: Sentry):
    await bot.add_cog(Moderation(bot))
