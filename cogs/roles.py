"""Role menu feature: a message with buttons that let members add/remove roles themselves."""

import discord
from discord import app_commands
from discord.ext import commands

from utils.checks import role_problem

# Map the colour names used in config.json to Discord button styles.
BUTTON_STYLES = {
    "blurple": discord.ButtonStyle.primary,
    "green": discord.ButtonStyle.success,
    "red": discord.ButtonStyle.danger,
    "grey": discord.ButtonStyle.secondary,
    "gray": discord.ButtonStyle.secondary,
}


class RoleButton(discord.ui.Button):
    """One button that toggles one role."""

    def __init__(self, role_name: str, emoji: str | None, style: str):
        super().__init__(
            label=role_name,
            emoji=emoji or None,
            style=BUTTON_STYLES.get(style, discord.ButtonStyle.secondary),
            # A fixed custom_id lets Discord route clicks to us even after a restart.
            custom_id=f"rolemenu:{role_name}",
        )
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name=self.role_name)
        if role is None:
            await interaction.response.send_message(
                f"⚠️ The role **{self.role_name}** doesn't exist anymore. Please tell an admin.", ephemeral=True
            )
            return

        problem = role_problem(interaction.guild, role)
        if problem:
            await interaction.response.send_message(f"⚠️ {problem}", ephemeral=True)
            return

        member = interaction.user
        if role in member.roles:
            await member.remove_roles(role, reason="Role menu")
            await interaction.response.send_message(f"➖ Removed {role.mention}.", ephemeral=True)
        else:
            await member.add_roles(role, reason="Role menu")
            await interaction.response.send_message(f"➕ You now have {role.mention}!", ephemeral=True)


class RoleMenuView(discord.ui.View):
    """The set of buttons, built from config.json."""

    def __init__(self, roles_config: list[dict]):
        super().__init__(timeout=None)  # timeout=None keeps the buttons working forever
        for entry in roles_config[:25]:  # Discord allows max 25 buttons per message
            self.add_item(RoleButton(entry["name"], entry.get("emoji"), entry.get("style", "grey")))


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings = bot.config.get("role_menu", {})
        # Register the view at startup so old role-menu messages keep working after a restart.
        bot.add_view(RoleMenuView(self.settings.get("roles", [])))

    @app_commands.command(name="rolemenu", description="Post a message with buttons for self-assignable roles.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_roles=True)  # hides the command from regular members
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.checks.bot_has_permissions(send_messages=True, embed_links=True)
    async def rolemenu(self, interaction: discord.Interaction):
        roles_config = self.settings.get("roles", [])
        if not roles_config:
            await interaction.response.send_message("No roles are set in config.json → role_menu.roles.",
                                                    ephemeral=True)
            return

        embed = discord.Embed(
            title=self.settings.get("title", "Pick your roles"),
            description=self.settings.get("description", ""),
            color=discord.Color.blurple(),
        )
        lines = [f"{r.get('emoji', '•')} **{r['name']}**" for r in roles_config]
        embed.add_field(name="Available roles", value="\n".join(lines))

        await interaction.channel.send(embed=embed, view=RoleMenuView(roles_config))

        # Warn the admin right away about roles that are missing or can't be managed.
        warnings = []
        for entry in roles_config:
            role = discord.utils.get(interaction.guild.roles, name=entry["name"])
            if role is None:
                warnings.append(f"• Role **{entry['name']}** doesn't exist yet. Create it in Server Settings → Roles.")
            elif problem := role_problem(interaction.guild, role):
                warnings.append(f"• {problem}")

        reply = "✅ Role menu posted!"
        if warnings:
            reply += "\n\n**Heads up, these buttons won't work yet:**\n" + "\n".join(warnings)
        await interaction.response.send_message(reply, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot))
