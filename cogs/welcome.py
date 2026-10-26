"""Welcome feature: greet new members with an embed and give them an auto-role."""

import logging

import discord
from discord.ext import commands

from utils.checks import role_problem
from utils.config import to_id

log = logging.getLogger("welcome")


def fill_placeholders(text: str, member: discord.Member) -> str:
    """Replace {mention}, {name}, {server} and {member_count} in config text."""
    return (
        text.replace("{mention}", member.mention)
        .replace("{name}", member.display_name)
        .replace("{server}", member.guild.name)
        .replace("{member_count}", str(member.guild.member_count))
    )


class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings = bot.config.get("welcome", {})

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not self.settings.get("enabled", True) or member.bot:
            return

        await self.send_welcome(member)
        await self.give_auto_role(member)

    async def send_welcome(self, member: discord.Member):
        channel_id = to_id(self.settings.get("channel_id"))
        channel = member.guild.get_channel(channel_id)
        if channel is None:
            log.warning("Welcome channel %s not found in '%s'. Check welcome.channel_id in config.json.",
                        channel_id, member.guild.name)
            return

        embed = discord.Embed(
            title=fill_placeholders(self.settings.get("title", "Welcome!"), member),
            description=fill_placeholders(self.settings.get("message", "Welcome {mention}!"), member),
            color=discord.Color.green(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        try:
            await channel.send(content=member.mention, embed=embed)
        except discord.Forbidden:
            log.warning("I can't post in #%s. Give me 'View Channel', 'Send Messages' and 'Embed Links' there.",
                        channel.name)

    async def give_auto_role(self, member: discord.Member):
        role_name = self.settings.get("auto_role")
        if not role_name:
            return  # auto-role is optional

        role = discord.utils.get(member.guild.roles, name=role_name)
        if role is None:
            log.warning("Auto-role '%s' doesn't exist in '%s'. Create it or fix welcome.auto_role.",
                        role_name, member.guild.name)
            return

        problem = role_problem(member.guild, role)
        if problem:
            # Strip Discord markdown so the console message reads cleanly.
            log.warning("Can't give auto-role '%s': %s", role_name, problem.replace("**", ""))
            return

        await member.add_roles(role, reason="Welcome auto-role")


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
