import discord
from discord.ext import commands
from discord.ui import View
import logging
from utils.image_generator import ImageGenerator
from views.verify_button import PersistentView
from utils.models import VerificationData

logger = logging.getLogger('captcha_bot')

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.image_generator = ImageGenerator()
        self.bot.loop.create_task(self.setup_verification_message())

    async def setup_verification_message(self):
        """Sets up the verification message in the designated channel."""
        await self.bot.wait_until_ready()

        self.bot.add_view(PersistentView(self))

        channel = self.bot.get_channel(self.bot.config.channel_id)
        if not channel:
            logger.error(f"Could not find channel with ID {self.bot.config.channel_id}")
            return

        try:
            async for message in channel.history(limit=100):
                await message.delete()
        except Exception as e:
            logger.error(f"Error clearing channel: {e}")

        embed = discord.Embed(
            title="<:locked:1330487709243801600> ` Verification Required! `",
            description="<:new:1119328501846265928> Welcome to ` Crspy's Server `! To access the full server, you need to pass our verification first.\n"
                        "<:space:1330490770188140681> <:add:1330488764593606696> Click on the **Verify** button below to start.",
            color=self.bot.config.success_color
        )

        try:
            await channel.send(embed=embed, view=PersistentView(self))
            logger.info("Verification message sent to channel")
        except Exception as e:
            logger.error(f"Error sending verification message: {e}")

    async def generate_verification(self):
        """Generates a new verification problem."""
        try:
            pattern_file, problem_text, answer = self.image_generator.generate_math_problem()
            image_buffer = await self.image_generator.create_problem_image(pattern_file, problem_text)

            verification_data = VerificationData(
                answer=answer,
                pattern_file=pattern_file,
                polynomial=problem_text,
                attempts=0
            )

            return {
                'verification': verification_data,
                'image': image_buffer
            }
        except Exception as e:
            logger.error(f"Error generating verification: {e}")
            raise

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def resetverification(self, ctx):
        """Admin command to reset the verification message."""
        await self.setup_verification_message()

        embed = discord.Embed(
            title="Error",
            description="Verification message has been reset.",
            color=self.bot.config.error_color
        )
        await ctx.send(embed=embed, delete_after=5)
        await ctx.message.delete()


async def setup(bot):
    await bot.add_cog(Verification(bot))