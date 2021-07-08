import time
import datetime
import discord
from discord.ext import commands
from db import db


class Notify(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="new_game",
                      usage=" <game id> <game rules> <game password> <password: None> <starting time in UTC>",
                      description="create a new game")
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def new_game(self):
        pass


def setup(bot: commands.Bot):
    bot.add_cog(Notify(bot))
