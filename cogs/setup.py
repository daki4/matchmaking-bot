import discord
from discord.ext import commands
from db import db


class Setup(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot


    @commands.command(name = "setup",
                    usage="[server invite]",
                    description = "use this command in the server channel that you want \
                        to show games, if no invite is provided, then a permanent invite\
                        will be created and used.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def setup(self, ctx:commands.Context, server_invite: str=None, role: discord.Role=None):
        if server_invite is not None:
            db.add_guild(ctx.message.guild.id, server_invite, ctx.channel.id, role.id)
        else:
            invite = await ctx.channel.create_invite(reason="This is the Stellaris Matchmaking bot discord invite. \
                This invite was made by the bot because you did not input an invite at setup. you can redo setup with [p]delsetup and [p]setup \
                and this time provide an invite.")
            print(f'{ctx.message.guild.id, str(invite)}    {str(ctx.channel.id)}')
            print(role.id)
            # db.add_guild(ctx.message.guild.id, str(invite), ctx.channel.id, role.id)


    @commands.command(name = "delsetup",
                    usage="",
                    description = "use this command to delete the configuration for this server")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def delsetup(self, ctx:commands.Context):
        db.remove_guild(ctx.message.guild.id)


def setup(bot:commands.Bot):
    bot.add_cog(Setup(bot))
