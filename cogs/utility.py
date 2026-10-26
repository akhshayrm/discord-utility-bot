"""Utility commands: /ping, /serverinfo, /userinfo, /poll."""

import discord
from discord import app_commands
from discord.ext import commands

NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]


class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check if the bot is alive and how fast it responds.")
    async def ping(self, interaction: discord.Interaction):
        latency_ms = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! Latency: **{latency_ms} ms**")

    @app_commands.command(name="serverinfo", description="Show information about this server.")
    @app_commands.guild_only()
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=guild.name, color=discord.Color.blurple())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown")
        embed.add_field(name="Members", value=str(guild.member_count))
        embed.add_field(name="Roles", value=str(len(guild.roles) - 1))  # minus @everyone
        embed.add_field(name="Text channels", value=str(len(guild.text_channels)))
        embed.add_field(name="Voice channels", value=str(len(guild.voice_channels)))
        embed.add_field(name="Boosts", value=f"{guild.premium_subscription_count} (Level {guild.premium_tier})")
        # <t:...:D> is a Discord timestamp - it shows in each viewer's own time zone.
        embed.add_field(name="Created", value=f"<t:{int(guild.created_at.timestamp())}:D>")
        embed.set_footer(text=f"Server ID: {guild.id}")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Show information about a member.")
    @app_commands.describe(member="The member to look up (leave empty for yourself)")
    @app_commands.guild_only()
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member | None = None):
        member = member or interaction.user
        embed = discord.Embed(title=str(member), color=member.color)
        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name="Display name", value=member.display_name)
        embed.add_field(name="Bot?", value="Yes" if member.bot else "No")
        embed.add_field(name="Top role", value=member.top_role.mention)
        embed.add_field(name="Account created", value=f"<t:{int(member.created_at.timestamp())}:R>")
        if member.joined_at:
            embed.add_field(name="Joined server", value=f"<t:{int(member.joined_at.timestamp())}:R>")

        # List roles from highest to lowest, skipping @everyone.
        roles = [r.mention for r in reversed(member.roles) if r != interaction.guild.default_role]
        roles_text = ", ".join(roles) if roles else "None"
        if len(roles_text) > 1024:  # embed field limit
            roles_text = f"{len(roles)} roles"
        embed.add_field(name=f"Roles ({len(roles)})", value=roles_text, inline=False)
        embed.set_footer(text=f"User ID: {member.id}")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="poll", description="Create a poll with up to 4 options.")
    @app_commands.describe(question="What do you want to ask?", option1="First choice", option2="Second choice",
                           option3="Third choice (optional)", option4="Fourth choice (optional)")
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(add_reactions=True, embed_links=True, read_message_history=True)
    async def poll(self, interaction: discord.Interaction, question: str, option1: str, option2: str,
                   option3: str | None = None, option4: str | None = None):
        options = [o for o in (option1, option2, option3, option4) if o]

        description = "\n\n".join(f"{NUMBER_EMOJIS[i]}  {text}" for i, text in enumerate(options))
        embed = discord.Embed(title=f"📊 {question}", description=description, color=discord.Color.gold())
        embed.set_footer(text=f"Poll by {interaction.user.display_name} • React below to vote")

        await interaction.response.send_message(embed=embed)
        poll_message = await interaction.original_response()  # the message we just sent
        for i in range(len(options)):
            await poll_message.add_reaction(NUMBER_EMOJIS[i])


async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
