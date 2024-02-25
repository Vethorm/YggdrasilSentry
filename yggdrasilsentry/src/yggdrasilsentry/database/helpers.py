import discord
from yggdrasilsentry.database.tables import get_session, Messages, Users, Guilds
from sqlmodel import select


async def upsert_guild(guild: discord.Guild):
    async with get_session() as session:
        # upsert guild
        statement = select(Guilds).where(Guilds.id == guild.id)
        result = await session.exec(statement)
        _guild = result.first()

        if _guild is None:
            _guild = Guilds(id=guild.id)
            session.add(_guild)
        await session.commit()


async def upsert_user(user: discord.User):
    async with get_session() as session:
        # upsert user
        statement = select(Users).where(Users.id == user.id)
        result = await session.exec(statement)
        _user = result.first()

        if _user is None:
            _user = Users(id=user.id)
            session.add(_user)
        await session.commit()


async def upsert_message(message: discord.Message):
    try:
        author = message.author
        async with get_session() as session:
            new_message = Messages(
                id=message.id,
                channel_id=message.channel.id,
                user_id=author.id,
                guild_id=author.guild.id,
                message_content=message.content,
                message_attachments=set(
                    attachment.proxy_url for attachment in message.attachments
                ),
                message_date=str(message.created_at),
                message_type="original",
            )
            session.add(new_message)

            await session.commit()
    except Exception as e:
        print(e)


async def upsert_message_edit(message: discord.Message):
    try:
        author = message.author
        async with get_session() as session:
            new_message = Messages(
                id=message.id,
                channel_id=message.channel.id,
                user_id=author.id,
                guild_id=author.guild.id,
                message_content=message.content,
                message_date=str(message.edited_at),
                message_type="edit",
            )
            session.add(new_message)

            await session.commit()
    except Exception as e:
        print(e)


async def upsert_message_delete(message: discord.Message):
    author = message.author
    async with get_session() as session:
        new_message = Messages(
            id=message.id,
            channel_id=message.channel.id,
            user_id=author.id,
            guild_id=author.guild.id,
            message_content=message.content,
            message_date=str(message.edited_at or message.created_at),
            message_type="delete",
        )
        session.add(new_message)

        await session.commit()
