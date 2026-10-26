"""Discord Utility Bot - main entry point.

Run with:  python bot.py
"""

import logging
import os
import sys

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from utils.config import load_config, to_id

# Feature modules ("cogs") to load from the cogs/ folder.
COGS = [
    "cogs.welcome",
    "cogs.roles",
    "cogs.faq",
    "cogs.utility",
    "cogs.moderation",
]

log = logging.getLogger("bot")


class UtilityBot(commands.Bot):
    def __init__(self, config: dict):
        # Intents decide which events Discord sends us.
        intents = discord.Intents.default()
        intents.members = True          # needed for welcome messages (privileged intent)
        intents.message_content = True  # needed for FAQ keyword replies (privileged intent)

        # We only use slash commands, so the text prefix is just a placeholder.
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)
        self.config = config

    async def setup_hook(self):
        """Runs once before the bot connects: load cogs and sync slash commands."""
        for cog in COGS:
            await self.load_extension(cog)
            log.info("Loaded %s", cog)

        # Send all errors from slash commands to our friendly error handler.
        self.tree.on_error = on_app_command_error

        guild_id = to_id(self.config.get("guild_id"))
        if guild_id:
            # Guild sync = commands appear instantly in that one server (best for testing).
            guild = discord.Object(id=guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info("Synced %d slash commands to server %s", len(synced), guild_id)
        else:
            # Global sync = commands work in every server (can take a while to appear).
            synced = await self.tree.sync()
            log.info("Synced %d slash commands globally", len(synced))

    async def on_ready(self):
        log.info("Logged in as %s (ID: %s)", self.user, self.user.id)
        log.info("Connected to %d server(s)", len(self.guilds))


async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Turn any slash-command error into a clear, private message for the user."""
    if isinstance(error, app_commands.MissingPermissions):
        perms = ", ".join(p.replace("_", " ").title() for p in error.missing_permissions)
        message = f"🚫 You need the **{perms}** permission to use this command."
    elif isinstance(error, app_commands.BotMissingPermissions):
        perms = ", ".join(p.replace("_", " ").title() for p in error.missing_permissions)
        message = (
            f"⚠️ I'm missing the **{perms}** permission here.\n"
            "Ask an admin to give it to my role (Server Settings → Roles) or in this channel's settings."
        )
    elif isinstance(error, app_commands.NoPrivateMessage):
        message = "This command only works inside a server."
    elif isinstance(error, app_commands.CommandInvokeError) and isinstance(error.original, discord.Forbidden):
        # Discord refused the action - almost always a permission or role-order problem.
        message = (
            "⚠️ Discord didn't let me do that. I'm probably missing a permission, "
            "or my role is too low in the role list."
        )
    else:
        log.exception("Unexpected error in /%s", interaction.command.name if interaction.command else "?",
                      exc_info=error)
        message = "❌ Something went wrong while running this command. The error was logged in the console."

    # Reply privately (ephemeral). If we already replied, send a follow-up instead.
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    load_dotenv()  # reads the .env file into environment variables
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        sys.exit("[setup] No bot token found. Copy .env.example to .env and paste your token after DISCORD_TOKEN=")

    bot = UtilityBot(load_config())
    try:
        bot.run(token, log_handler=None)  # log_handler=None: we set up logging ourselves above
    except discord.LoginFailure:
        sys.exit("[setup] Discord rejected the token. Reset it in the Developer Portal and paste the new one into .env")
    except discord.PrivilegedIntentsRequired:
        sys.exit(
            "[setup] Privileged intents are not enabled.\n"
            "        Developer Portal → your app → Bot → turn ON 'Server Members Intent' and 'Message Content Intent'."
        )


if __name__ == "__main__":
    main()
