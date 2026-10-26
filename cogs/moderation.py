"""Moderation commands: /clear and /timeout (staff only)."""

from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

MAX_TIMEOUT_MINUTES = 28 * 24 * 60  # Discord's limit is 28 days


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.max_clear = bot.config.get("moderation", {}).get("max_clear", 100)

    @app_commands.command(name="clear", description="Delete the last N messages in this channel.")
    @app_commands.describe(amount="How many messages to delete")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)  # hides the command from regular members
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True, read_message_history=True)
    async def clear(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 1000]):
        if amount > self.max_clear:
            await interaction.response.send_message(
                f"You can delete at most **{self.max_clear}** messages at once.", ephemeral=True
            )
            return

        # Deleting can take a few seconds, so tell Discord we're working on it.
        await interaction.response.defer(ephemeral=True, thinking=True)
        deleted = await interaction.channel.purge(limit=amount, reason=f"/clear by {interaction.user}")
        await interaction.followup.send(f"🧹 Deleted **{len(deleted)}** message(s).", ephemeral=True)

    @app_commands.command(name="timeout", description="Temporarily mute a member. Use 0 minutes to remove a timeout.")
    @app_commands.describe(member="Who to time out", minutes="Length in minutes (0 = remove timeout)",
                           reason="Why (shown in the audit log)")
    @app_commands.guild_only()
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member,
                      minutes: app_commands.Range[int, 0, MAX_TIMEOUT_MINUTES], reason: str | None = None):
        guild = interaction.guild
        moderator = interaction.user

        # Safety checks with clear explanations (Discord would otherwise give a vague error).
        problem = None
        if member == moderator:
            problem = "You can't time out yourself."
        elif member == guild.me:
            problem = "I can't time out myself."
        elif member == guild.owner:
            problem = "The server owner can't be timed out."
        elif member.guild_permissions.administrator:
            problem = f"{member.mention} is an Administrator. Discord doesn't allow timing out admins."
        elif moderator != guild.owner and member.top_role >= moderator.top_role:
            problem = f"{member.mention}'s highest role is equal to or above yours, so you can't time them out."
        elif member.top_role >= guild.me.top_role:
            problem = (
                f"My role ({guild.me.top_role.mention}) is not above {member.mention}'s highest role.\n"
                "Fix: Server Settings → Roles, then drag my role higher."
            )

        if problem:
            await interaction.response.send_message(f"⚠️ {problem}", ephemeral=True)
            return

        audit_reason = f"{moderator}: {reason or 'No reason given'}"
        if minutes == 0:
            await member.timeout(None, reason=audit_reason)
            await interaction.response.send_message(f"🔊 Removed the timeout for {member.mention}.")
        else:
            await member.timeout(timedelta(minutes=minutes), reason=audit_reason)
            await interaction.response.send_message(
                f"🔇 {member.mention} has been timed out for **{minutes} minute(s)**."
                + (f"\nReason: {reason}" if reason else "")
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
