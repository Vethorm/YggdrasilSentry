import asyncio
import os

from yggdrasilsentry.bot import Sentry

try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

bot_token = os.environ["DISCORD_TOKEN"]


async def run_bot():
    async with Sentry() as bot:
        await bot.start()


def main():
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
