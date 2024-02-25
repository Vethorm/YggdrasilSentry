from sqlmodel import Field, SQLModel, create_engine, Session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.dialects import postgresql
from typing import Optional, Set
import os

engine = create_engine(os.environ["DATABASE_URI"])
async_engine = create_async_engine(os.environ["DATABASE_URI"])


class Guilds(SQLModel, table=True):
    id: int = Field(default=None, sa_column=Column(BigInteger(), primary_key=True))
    sentry_category_id: int = Field(default=None, sa_column=Column(BigInteger()))
    sentry_quaratine_channel_id: int = Field(
        default=None, sa_column=Column(BigInteger())
    )
    sentry_quarantine_role_id: int = Field(default=None, sa_column=Column(BigInteger()))
    sentry_mode: bool = Field(default=False)


class Users(SQLModel, table=True):
    id: int = Field(default=None, sa_column=Column(BigInteger(), primary_key=True))


class GuildUsers(SQLModel, table=True):
    id: int = Field(default=None, sa_column=Column(BigInteger(), primary_key=True))
    guild_id: int = Field(
        default=None,
        sa_column=Column(
            BigInteger(),
            ForeignKey("guilds.id", ondelete="CASCADE", onupdate="CASCADE"),
            primary_key=True,
        ),
    )
    armed: bool = Field(default=False)
    armed_by: int = Field(
        default=None,
        sa_column=Column(
            BigInteger(), ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE")
        ),
    )


class Messages(SQLModel, table=True):
    id: int = Field(default=None, sa_column=Column(BigInteger(), primary_key=True))
    channel_id: int = Field(default=None, sa_column=Column(BigInteger()))
    user_id: int = Field(
        default=None,
        sa_column=Column(
            BigInteger(),
            ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
            primary_key=True,
        ),
    )
    guild_id: int = Field(
        default=None,
        sa_column=Column(
            BigInteger(),
            ForeignKey("guilds.id", ondelete="CASCADE", onupdate="CASCADE"),
            primary_key=True,
        ),
    )
    message_content: str = Field(default=None)
    message_attachments: Optional[Set[str]] = Field(
        default=None, sa_column=Column(postgresql.ARRAY(String()))
    )
    message_date: str = Field(default=None, primary_key=True)
    message_type: str = Field(default=None, primary_key=True)


class QuarantineStatus(SQLModel, table=True):
    guild_id: int = Field(
        default=None,
        sa_column=Column(
            BigInteger(),
            ForeignKey("guilds.id", ondelete="CASCADE", onupdate="CASCADE"),
            primary_key=True,
        ),
    )
    user_id: int = Field(
        default=None,
        sa_column=Column(
            BigInteger(),
            ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
            primary_key=True,
        ),
    )
    active: bool = Field(default=None)


class QuarantineLog(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None, sa_column=Column(BigInteger(), primary_key=True)
    )
    guild_id: int = Field(
        default=None,
        sa_column=Column(
            BigInteger(),
            ForeignKey("guilds.id", ondelete="CASCADE", onupdate="CASCADE"),
        ),
    )
    user_id: int = Field(
        default=None,
        sa_column=Column(
            BigInteger(), ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE")
        ),
    )
    quarantine_status: bool = Field(default=None)
    action_type: str = Field(default=None)
    initiator: int = Field(
        default=None,
        sa_column=Column(
            BigInteger(),
            ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        ),
    )


async def create_db_and_tables():
    async with async_engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    # SQLModel.metadata.create_all(async_engine)


def get_session():
    return AsyncSession(async_engine)
