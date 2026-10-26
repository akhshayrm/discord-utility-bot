"""FAQ feature: auto-reply when a message contains a keyword from config.json."""

import re
import time

import discord
from discord.ext import commands


class FAQ(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings = bot.config.get("faq", {})
        self.cooldown = self.settings.get("cooldown_seconds", 30)

        # Pre-build one search pattern per FAQ entry. \b = word boundary, so "rules"
        # matches "the rules?" but not "rulesets". re.IGNORECASE ignores capital letters.
        self.entries = []
        for entry in self.settings.get("entries", []):
            keywords = "|".join(re.escape(k) for k in entry.get("keywords", []))
            if keywords:
                pattern = re.compile(rf"\b(?:{keywords})\b", re.IGNORECASE)
                self.entries.append((pattern, entry["answer"]))

        # Remembers when we last answered each FAQ in each channel: {(channel_id, faq_index): timestamp}
        self.last_reply: dict[tuple[int, int], float] = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore bots (including ourselves), DMs, and the feature being turned off.
        if message.author.bot or message.guild is None or not self.settings.get("enabled", True):
            return

        for index, (pattern, answer) in enumerate(self.entries):
            if not pattern.search(message.content):
                continue

            key = (message.channel.id, index)
            now = time.monotonic()
            if now - self.last_reply.get(key, 0) < self.cooldown:
                return  # answered this recently in this channel - stay quiet

            self.last_reply[key] = now
            try:
                await message.reply(answer, mention_author=False)
            except discord.Forbidden:
                pass  # no permission to talk in this channel - silently skip
            return  # only answer the first matching FAQ


async def setup(bot: commands.Bot):
    await bot.add_cog(FAQ(bot))
