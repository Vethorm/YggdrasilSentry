from yggdrasilsentry.bot import Sentry

from discord.ext import commands
import discord
from discord import app_commands

from yggdrasilsentry.database.helpers import upsert_guild, upsert_user
from yggdrasilsentry.database.tables import (
    get_session,
    GuildUsers,
    Guilds,
    QuarantineStatus,
    QuarantineLog,
)
from sqlmodel import select

from typing import Union

import traceback


@app_commands.guild_only()
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
class QuarantineAdmin(commands.GroupCog, group_name="quarantine_admin"):
    def __init__(self, bot: Sentry):
        self.bot: Sentry = bot
        print("Loading quarantine cog!")

    @app_commands.command()
    async def mode(self, interaction: discord.Interaction, mode: bool):
        await interaction.response.defer(thinking=True)
        guild = interaction.guild
        try:
            await upsert_guild(guild)
            quaratine_channel = await get_current_quarantine_channel(guild)
            if quaratine_channel is None:
                # create a SentryBot category if one does not exist
                category: discord.CategoryChannel = await guild.create_category(
                    "SentryBot"
                )
                await update_quarantine_category(category)
                # create a channel for quarantine logs if one does not exist
                channel: discord.TextChannel = await category.create_text_channel(
                    "quarantine_log"
                )
                await update_quarantine_channel(channel)
                # create a quarantine role
                quarantine_role: discord.Role = await guild.create_role(
                    name="SentryQuarantine"
                )
                await update_quaratine_role(guild, quarantine_role)
                # enable quarantine mode

            quarantine_role = await get_current_quarantine_role(guild)
            await deny_quarantine_role(guild, quarantine_role)
            await update_quaratine_mode(guild, mode)

            await interaction.followup.send(f"Set quarantine mode to {mode}")
        except Exception as e:
            print(e)
            await interaction.followup.send("command failed!")

    @app_commands.command()
    async def sync_quarantine(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            guild = interaction.guild
            quarantine_role = await get_current_quarantine_role(guild)
            await deny_quarantine_role(guild, quarantine_role)
            await interaction.followup.send(f"Synced {quarantine_role.mention}")
        except Exception as e:
            print(e)
            await interaction.followup.send("command failed!")

    @app_commands.command()
    async def arm(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(thinking=True)
        try:
            await arming_user(interaction.user, user, arm=True)
            print("Following up")
            await interaction.followup.send(
                f"{interaction.user.mention} armed {user.mention}\n"
                "with great power comes with great responsibility..."
            )
        except Exception as e:
            print(e)
            print("Errored but following up")
            await interaction.followup.send(f"Failed to arm {user}")

    @app_commands.command()
    async def disarm(self, interaction: discord.Interaction, user: discord.Member):
        await arming_user(interaction.user, user, arm=False)
        await interaction.response.send_message(
            f"{interaction.user.mention} disarmed {user.mention}"
        )

    @app_commands.command()
    async def list_active(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            users = []
            for user in await get_active_quarantine_list(interaction.guild):
                if user is None:
                    continue
                user: discord.Member
                users.append(user.name)
            if users:
                message = "\n".join(users)
            else:
                message = "No users in quarantine!"
            await interaction.followup.send(message)
        except Exception as e:
            print(e)
            await interaction.followup.send("command failed")

    @app_commands.command()
    async def remove_quarantine(
        self, interaction: discord.Interaction, user: discord.Member
    ):
        await interaction.response.defer(thinking=True)
        try:
            await remove_user_from_quarantine(interaction.user, user, "manual")
            await interaction.followup.send(
                f"{interaction.user.mention} removed {user.mention} from quarantine!"
            )
        except Exception as e:
            print(e)
            await interaction.followup.send("command failed")


class QuarantineListeners(commands.Cog):
    def __init__(self, bot: Sentry):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        print("member listener")
        is_quarantined = await user_is_quarantined(member)
        quarantine_active = await is_quarantine_active(member.guild)
        print(is_quarantined, quarantine_active)
        if is_quarantined and quarantine_active:
            quarantine_role = await get_current_quarantine_role(member.guild)
            await member.add_roles(quarantine_role)


@app_commands.guild_only()
class QuarantineUser(commands.GroupCog, group_name="quarantine"):
    def __init__(self, bot: Sentry):
        self.bot: Sentry = bot

    @app_commands.command()
    async def shoot(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(thinking=True)
        try:
            quarantine_active = await is_quarantine_active(interaction.guild)
            user_armed = await armed(interaction.user)
            misused_shoot = await user_misused_shoot(user)
            if quarantine_active and user_armed and not misused_shoot:
                await place_user_in_quarantine(interaction.user, user, "manual")
                await interaction.followup.send(
                    f"{interaction.user.mention} placed {user.mention} in quarantine"
                )
            else:
                responses = []
                if misused_shoot and user_armed:
                    responses.append(
                        f"You misused your power, peasentry welcomes you back..."
                    )
                    await arming_user(interaction.user, user, arm=False)
                if not user_armed:
                    responses.append(f"{interaction.user.mention} is not armed")
                if not quarantine_active:
                    responses.append(
                        f"Quarantine not active, your bullets have no power here"
                    )
                message = "\n".join(responses)
                await interaction.followup.send(message)
        except Exception as e:
            print(traceback.format_exc())
            await interaction.followup.send(f"command failed")


async def remove_user_from_quarantine(
    initiator: discord.Member, user: discord.Member, action_type: str
):
    guild = initiator.guild
    await upsert_user(user)
    quarantine_channel = await get_current_quarantine_channel(guild)
    quarantine_role = await get_current_quarantine_role(guild)

    await append_to_quarantine_log(initiator, user, False, action_type)
    await user.remove_roles(quarantine_role)

    await update_user_quarantine_status(user, False)

    await quarantine_channel.send(
        content=f"{user.mention} was remvoed into quarantine by {initiator.mention}"
    )


async def arming_user(
    giver: discord.Member, receiver: discord.Member, arm: bool = False
):
    guild = giver.guild
    await upsert_guild(guild)
    await upsert_user(giver)
    await upsert_user(receiver)

    async with get_session() as session:
        print("ARMING USER")
        statement = select(GuildUsers).where(
            GuildUsers.id == receiver.id, GuildUsers.guild_id == giver.guild.id
        )
        result = await session.exec(statement)
        row = result.first()

        if row is None:
            print("adding new user")
            _row = GuildUsers(
                id=receiver.id,
                guild_id=receiver.guild.id,
                armed=arm,
                armed_by=giver.id,
            )
            session.add(_row)
        else:
            print("updating user")
            row.armed = arm
            row.armed_by = giver.id
            session.add(row)
        await session.commit()

    print("Upserted arms !")


async def get_active_quarantine_list(guild: discord.Guild) -> list[discord.Member]:
    async with get_session() as session:
        result = await session.exec(
            select(QuarantineStatus).where(QuarantineStatus.active == True)
        )
        return [guild.get_member(row.user_id) for row in result]


async def user_is_quarantined(user: discord.Member) -> bool:
    async with get_session() as session:
        result = await session.exec(
            select(QuarantineStatus).where(QuarantineStatus.user_id == user.id)
        )
        row = result.first()
        if row is not None:
            return row.active
        else:
            return False


async def user_misused_shoot(target: discord.Member):
    if target.guild_permissions.administrator:
        return True
    if target.bot:
        return True
    return False


async def armed(user: discord.Member) -> bool:
    async with get_session() as session:
        statement = select(GuildUsers).where(
            GuildUsers.guild_id == user.guild.id, GuildUsers.id == user.id
        )
        result = await session.exec(statement)
        row = result.first()
        if row is None:
            return False
        else:
            return row.armed


async def is_quarantine_active(guild: discord.Guild) -> bool:
    async with get_session() as session:
        statement = select(Guilds).where(Guilds.id == guild.id)
        result = await session.exec(statement)
        guild: Guilds = result.first()
        return guild.sentry_mode


async def deny_quarantine_role(guild: discord.Guild, role: discord.Role):
    """updates deny permissions in all channels for quarantine role"""
    for channel in await guild.fetch_channels():
        channel: discord.abc.GuildChannel
        if isinstance(channel, discord.TextChannel):
            await channel.set_permissions(
                target=role, read_messages=False, send_messages=False
            )


async def get_current_quarantine_role(guild: discord.Guild) -> discord.Role:
    """returns a quarantine role"""
    async with get_session() as session:
        statement = select(Guilds).where(Guilds.id == guild.id)
        result = await session.exec(statement)
        _guild: Guilds = result.first()
        role = guild.get_role(_guild.sentry_quarantine_role_id)
        return role


async def get_current_quarantine_channel(
    guild: discord.Guild,
) -> Union[discord.TextChannel, None]:
    async with get_session() as session:
        statement = select(Guilds).where(Guilds.id == guild.id)
        result = await session.exec(statement)
        _guild: Guilds = result.first()
        if _guild.sentry_quaratine_channel_id is None:
            return None
        else:
            return await guild.fetch_channel(_guild.sentry_quaratine_channel_id)


async def update_quaratine_role(guild: discord.Guild, role: discord.Role):
    async with get_session() as session:
        statement = select(Guilds).where(Guilds.id == guild.id)
        result = await session.exec(statement)
        guild: Guilds = result.first()
        guild.sentry_quarantine_role_id = role.id
        session.add(guild)
        await session.commit()


async def update_quaratine_mode(guild: discord.Guild, mode: bool):
    async with get_session() as session:
        statement = select(Guilds).where(Guilds.id == guild.id)
        result = await session.exec(statement)
        guild: Guilds = result.first()
        guild.sentry_mode = mode
        session.add(guild)
        await session.commit()


async def update_quarantine_category(category: discord.CategoryChannel):
    async with get_session() as session:
        statement = select(Guilds).where(Guilds.id == category.guild.id)
        result = await session.exec(statement)
        guild: Guilds = result.first()
        guild.sentry_category_id = category.category_id
        session.add(guild)
        await session.commit()


async def update_quarantine_channel(channel: discord.TextChannel):
    async with get_session() as session:
        statement = select(Guilds).where(Guilds.id == channel.guild.id)
        result = await session.exec(statement)
        guild: Guilds = result.first()
        guild.sentry_quaratine_channel_id = channel.id
        session.add(guild)
        await session.commit()


async def append_to_quarantine_log(
    initiator: discord.Member,
    user: discord.Member,
    quarantined: bool,
    action_type: str,
):
    guild = initiator.guild
    async with get_session() as session:
        new_log = QuarantineLog(
            guild_id=guild.id,
            user_id=user.id,
            quarantine_status=quarantined,
            action_type=action_type,
            initiator=initiator.id,
        )
        session.add(new_log)
        await session.commit()


async def update_user_quarantine_status(user: discord.Member, quarantined: bool):
    guild = user.guild
    await upsert_user(user)
    async with get_session() as session:
        result = await session.exec(
            select(QuarantineStatus).where(
                QuarantineStatus.guild_id == guild.id,
                QuarantineStatus.user_id == user.id,
            )
        )
        row: QuarantineStatus = result.first()
        if row is None:
            new_row = QuarantineStatus(
                guild_id=guild.id, user_id=user.id, active=quarantined
            )
            session.add(new_row)
        else:
            row.active = quarantined
            session.add(row)
        await session.commit()


async def place_user_in_quarantine(
    initiator: discord.Member, user: discord.Member, action_type: str
):
    guild = initiator.guild
    await upsert_user(user)
    quarantine_channel = await get_current_quarantine_channel(guild)
    quarantine_role = await get_current_quarantine_role(guild)

    await append_to_quarantine_log(initiator, user, True, action_type)
    await update_user_quarantine_status(user, True)

    await user.add_roles(quarantine_role)
    direct_message = await user.create_dm()
    await direct_message.send(
        content="You have been placed in quarantine and can no longer send messages. The moderator team has been made aware of this. If you have been incorrectly quarantined the moderator team will remove it shortly!"
    )
    await quarantine_channel.send(
        content=f"{user.mention} was placed into quarantine by {initiator.mention}"
    )


async def setup(bot: Sentry):
    await bot.add_cog(QuarantineAdmin(bot))
    await bot.add_cog(QuarantineUser(bot))
    await bot.add_cog(QuarantineListeners(bot))
