"""Shared permission checks used by several features."""

import discord


def role_problem(guild: discord.Guild, role: discord.Role) -> str | None:
    """Check whether the bot is able to give/remove `role`.

    Returns a human-readable explanation of the problem, or None if everything is fine.
    """
    me = guild.me

    if not me.guild_permissions.manage_roles:
        return "I'm missing the **Manage Roles** permission. Please give it to my role in Server Settings → Roles."

    # Discord only lets a bot manage roles that are BELOW its own highest role.
    if role >= me.top_role:
        return (
            f"My role ({me.top_role.mention}) is not high enough to manage {role.mention}.\n"
            "Fix: Server Settings → Roles, then drag my role **above** that role."
        )

    if role.managed:
        return f"{role.mention} is managed by an integration (e.g. another bot or boosts) and can't be assigned manually."

    return None
