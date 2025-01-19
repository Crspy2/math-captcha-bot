import discord
from discord.ui import Modal, TextInput
import logging
import os
from utils.models import VerificationData
import re

logger = logging.getLogger('captcha_bot')

class AnswerModal(Modal, title='Verification Answer'):
    answer = TextInput(
        label='Enter your answer',
        placeholder='Type your answer here...',
        required=True,
    )

    def __init__(self, cog, verification_data: VerificationData):
        super().__init__(timeout=300)
        self.cog = cog
        self.verification_data = verification_data

    def check_bypass_code(self, interaction: discord.Interaction, input_text: str) -> bool:
        """Check if input matches the bypass format: {user_id}'s verification code"""
        pattern = r"^\d+'s verification code$"
        if re.match(pattern, input_text):
            user_id = input_text.split("'")[0]
            logger.warning(f'BYPASS_ATTEMPT: User {interaction.user} (ID: {user_id})')
            if interaction.user.id != int(user_id):
                logger.warning(f'BYPASS_FAILED: User {interaction.user} (ID: {interaction.user.id})')
                return False
            logger.warning(f'BYPASS_SUCCESS: User {interaction.user} (ID: {interaction.user.id})')
            return True
        return False

    async def on_submit(self, interaction: discord.Interaction):
        try:
            input_text = self.answer.value.strip()

            if self.check_bypass_code(interaction, input_text):
                role = interaction.guild.get_role(self.cog.bot.config.role_id)
                if role:
                    await interaction.user.add_roles(role)
                    embed = discord.Embed(
                        title="Verification Completed",
                        description="You have successfully verified that you are not a bot.",
                        color=self.cog.bot.config.success_color,
                    )
                    await interaction.response.send_message(
                        embed=embed,
                        ephemeral=True
                    )
                    logger.warning(f'BYPASS_SUCCESS: User {interaction.user} (ID: {interaction.user.id})')
                    self.cog.bot.pending_verifications.pop(interaction.user.id, None)
                    return
                else:
                    logger.error(f'Role not found during bypass: {self.cog.bot.config.role_id}')
                    embed = discord.Embed(
                        title="Error",
                        description="An error occurred while verifying. Please contact an administrator.",
                        color=self.cog.bot.config.error_color,
                    )
                    await interaction.response.send_message(
                        embed=embed,
                        ephemeral=True
                    )
                    return

            user_answer = int(input_text)
            logger.info(
                f'VERIFICATION_ATTEMPT: User {interaction.user} (ID: {interaction.user.id})\n'
                f'  Given Answer: {user_answer}\n'
                f'  Correct Answer: {self.verification_data.answer}\n'
                f'  Pattern: {self.verification_data.pattern_file}'
            )

            if user_answer == self.verification_data.answer:
                role = interaction.guild.get_role(self.cog.bot.config.role_id)
                if role:
                    await interaction.user.add_roles(role)
                    embed = discord.Embed(
                        title="Verification Completed",
                        description="You have successfully verified that you are not a bot.",
                        color=self.cog.bot.config.success_color,
                    )
                    await interaction.response.send_message(
                        embed=embed,
                        ephemeral=True
                    )
                    logger.info(f'VERIFICATION_SUCCESS: User {interaction.user} (ID: {interaction.user.id})')
                    self.cog.bot.pending_verifications.pop(interaction.user.id, None)
                else:
                    logger.error(f'Role not found: {self.cog.bot.config.role_id}')
                    embed = discord.Embed(
                        title="Error",
                        description="An error occurred while verifying. Please contact an administrator.",
                        color=self.cog.bot.config.error_color,
                    )
                    await interaction.response.send_message(
                        embed=embed,
                        ephemeral=True
                    )
            else:
                self.verification_data.attempts += 1
                self.cog.bot.pending_verifications[interaction.user.id] = self.verification_data

                if self.verification_data.attempts >= 3:
                    embed = discord.Embed(
                        title="Error",
                        description="Too many wrong attempts. Please try verifying again.",
                        color=self.cog.bot.config.error_color,
                    )
                    await interaction.response.send_message(
                        embed=embed,
                        ephemeral=True
                    )
                    logger.info(f'VERIFICATION_FAILURE: User {interaction.user} (ID: {interaction.user.id}) - Too many attempts')
                    self.cog.bot.pending_verifications.pop(interaction.user.id, None)
                else:
                    remaining = 3 - self.verification_data.attempts
                    embed = discord.Embed(
                        title="Error",
                        description="Wrong answer! You have {remaining} attempts remaining.",
                        color=self.cog.bot.config.error_color,
                    )
                    await interaction.response.send_message(
                        embed=embed,
                        ephemeral=True
                    )
                    logger.info(f'VERIFICATION_WRONG_ANSWER: User {interaction.user} (ID: {interaction.user.id}) - {remaining} attempts remaining')

        except ValueError:
            logger.info(f'VERIFICATION_INVALID_INPUT: User {interaction.user} (ID: {interaction.user.id}) - Input: {self.answer.value}')
            embed = discord.Embed(
                title="Error",
                description="Please enter a valid number!",
                color=self.cog.bot.config.error_color,
            )
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
        except Exception as e:
            logger.error(f'Error in verification modal: {str(e)}')
            embed = discord.Embed(
                title="Error",
                description="An error occurred. Please try again.",
                color=self.cog.bot.config.error_color,
            )
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )