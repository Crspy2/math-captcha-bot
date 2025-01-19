import discord
from discord.ext import commands
import asyncio
from utils.logger import setup_logger
from utils.config import Config, ConfigError
import sys
import os

logger = setup_logger()


class CrspyBot(commands.Bot):
    def __init__(self):
        # Load configuration
        try:
            self.config = Config.load()
        except ConfigError as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(1)

        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(
            command_prefix=self.config.prefix,
            intents=intents
        )

        self.pending_verifications = {}

    async def load_cogs(self):
        """Loads all cogs from the cogs directory."""
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('_'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    logger.info(f'Loaded cog: {filename[:-3]}')
                except Exception as e:
                    logger.error(f'Failed to load cog {filename[:-3]}: {str(e)}')

    async def setup_hook(self):
        """Called when the bot is setting up."""
        await self.load_cogs()
        logger.info(f'Bot logged in as {self.user}')


async def main():
    bot = CrspyBot()

    try:
        async with bot:
            await bot.start(bot.config.discord_token)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        await bot.close()
    except Exception as e:
        logger.error(f"Error running bot: {e}")
    finally:
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down from main thread...")