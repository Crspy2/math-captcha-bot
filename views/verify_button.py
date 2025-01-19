import asyncio
import time

import discord
from discord.ui import Button, View
import logging
from views.answer_modal import AnswerModal

logger = logging.getLogger('captcha_bot')

class PersistentView(View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.add_item(VerifyButton(cog))
        self.add_item(VerifyHelpButton(cog))

class VerifyButton(Button):
    def __init__(self, cog):
        super().__init__(
            label="Verify",
            style=discord.ButtonStyle.green,
            custom_id="verify_button"
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.get_role(self.cog.bot.config.role_id):
            embed = discord.Embed(
                title="Error",
                description="You are already verified.",
                color=self.cog.bot.config.error_color
            )
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
            return

        result = await self.cog.generate_verification()
        verification_data = result['verification']

        logger.info(
            f'VERIFICATION_STARTED: User {interaction.user} (ID: {interaction.user.id})\n'
            f'  Pattern: {verification_data.pattern_file}\n'
            f'  Answer: {verification_data.answer}'
        )

        self.cog.bot.pending_verifications[interaction.user.id] = verification_data

        embed = discord.Embed(
            title="Verification Challenge",
            description=f"Please solve the mathematical problem below. The captcha challenge expires <t:{int(time.time() + 10 * 60)}:R>",
            color=self.cog.bot.config.success_color
        )
        embed.add_field(
            name="Instructions",
            value="1. Look at the pattern image\n2. Solve the mathematical equation\n3. Click 'Submit Answer' and enter your solution"
        )

        verify_view = View(timeout=600)
        submit_button = Button(
            label="Submit Answer",
            style=discord.ButtonStyle.green,
            custom_id=f"submit_answer_{interaction.user.id}"
        )

        async def submit_callback(submit_interaction: discord.Interaction):
            if submit_interaction.user.id != interaction.user.id:
                embed = discord.Embed(
                    title="Error",
                    description="This is not your verification challenge!",
                    color=self.cog.bot.config.error_color
                )
                await submit_interaction.response.send_message(
                    embed=embed,
                    ephemeral=True
                )
                return

            verification = self.cog.bot.pending_verifications.get(submit_interaction.user.id)
            if verification:
                modal = AnswerModal(self.cog, verification)
                await submit_interaction.response.send_modal(modal)
            else:
                embed = discord.Embed(
                    title="Error",
                    description="Verification expired. Please start over.",
                    color=self.cog.bot.config.error_color
                )
                await submit_interaction.response.send_message(
                    embed=embed,
                    ephemeral=True
                )

        submit_button.callback = submit_callback
        verify_view.add_item(submit_button)

        file = discord.File(result['image'], filename="captcha.png")
        embed.set_image(url="attachment://captcha.png")

        await interaction.response.send_message(
            embed=embed,
            file=file,
            view=verify_view,
            ephemeral=True
        )

        await asyncio.sleep(60 * 10)
        submit_button.disabled = True
        await interaction.edit_original_response(
            embed=embed,
            view=verify_view,
        )


class VerifyHelpButton(Button):
    def __init__(self, cog):
        super().__init__(
            label="Help",
            style=discord.ButtonStyle.gray,
            custom_id="help_button"
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Help",
            description="See the instructions for the captcha and a helpful resource to assist you in completing it.",
            color=self.cog.bot.config.success_color
        )
        embed.add_field(
            name="Instructions",
            value="• You will be shown a pattern and a mathematical equation\n"
                  "• Solve the equation using the pattern\n"
                  "• Enter your answer in the prompt\n"
                  "• You have 3 attempts to get it right"
        )
        embed.add_field(
            name="Helpful Resources",
            value="https://www.youtube.com/watch?v=WsQQvHm4lSw"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )