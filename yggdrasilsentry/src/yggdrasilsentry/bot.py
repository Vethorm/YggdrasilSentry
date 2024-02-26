from discord.ext import commands
import discord
import os

from yggdrasilsentry.database.tables import create_db_and_tables, get_session


class Sentry(commands.Bot):
    def __init__(self):
        intents = discord.Intents(
            messages=True,
            message_content=True,
            guilds=True,
            members=True,
        )
        command_prefix = "sentry:"
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.initial_extensions = [
            "yggdrasilsentry.cogs.overwatch",
            "yggdrasilsentry.cogs.quarantine",
            "yggdrasilsentry.cogs.chat_management",
            "yggdrasilsentry.cogs.moderation",
        ]

    async def setup_hook(self) -> None:
        await create_db_and_tables()
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
            except Exception as e:
                print(f"Failed to load extension - {extension}")
                raise e

        self.tree.copy_global_to(guild=discord.Object(id=1211082461824417802))
        await self.tree.sync(guild=discord.Object(id=1211082461824417802))
        print("Finished setup !")

    async def on_ready(self):
        async with get_session() as session:
            pass
        print(f"{self.user} online (ID: {self.user.id})")

    async def on_command_error(self, ctx, error: commands.CommandError) -> None:
        # TODO: pulled from Danny bot, should write my own
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send("This command cannot be used in private messages.")
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send("Sorry. This command is disabled and cannot be used.")
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if not isinstance(original, discord.HTTPException):
                print("In %s:", ctx.command.qualified_name, exc_info=original)
        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.send(str(error))

    async def start(self) -> None:
        await super().start(os.environ["DISCORD_TOKEN"], reconnect=True)
