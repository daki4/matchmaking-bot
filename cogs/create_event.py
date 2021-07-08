import discord
from discord.ext import commands
from db import db
from auxiliary import time_handle


class EmbedHandle(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="new_game",
                      usage=' <game id> "<game rules in quotation marks>" <game password> <starting time in UTC in format hh:mm:ss> <next day?:0>',
                      description="create a new posting, game rules need to be encapsulated in quotation marks, time in UTC in hh:mm:ss format")
    @commands.guild_only()
    @commands.has_permissions()
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def new_game(self, ctx: commands.Context, game_id: str = None, game_password: str = None,
                       game_rules: str = None, starting_time: str = "0:0:0"):
        gtime = time_handle.interpret_time(starting_time)
        db.create_embed(ctx.message.id, ctx.message.author.id, ctx.message.guild.id, game_id, game_password, game_rules,
                        gtime, str(ctx.message.guild.get_member(ctx.message.author.id).avatar_url))
        embed = await self.generate_embed(msgid=ctx.message.id)
        print(ctx.message.id)
        await ctx.message.delete()
        for i in db.get_all_guilds():
            ch = self.bot.get_channel(i['channel'])
            message = await ch.send(embed=embed)
            db.track_embed(embed_id=ctx.message.id, em_id=message.id, channel=i['channel'])
            await message.add_reaction('✅')
            await message.add_reaction('❓')
            await message.add_reaction('❌')
            await message.add_reaction('🏳️')

    @commands.Cog.listener('on_reaction_add')
    async def on_reaction_add(self, reaction: discord.Reaction, user):
        if user.id == self.bot.user.id:
            return
        t_em = db.get_tracked_embed(reaction.message.id)
        db.try_pull_all_reactions(t_em['_id'], user.name)
        if str(reaction.emoji) == '✅':
            db.add_participation(t_em['_id'], 'participating', user.name)
        if str(reaction.emoji) == '❓':
            db.add_participation(t_em['_id'], 'mb_participating', user.name)
        if str(reaction.emoji) == '❌':
            db.add_participation(t_em['_id'], 'not_participating', user.name)
        if str(reaction.emoji) == '🏳️':
            db.try_pull_all_reactions(t_em['_id'], user.name)
        embed = await self.generate_embed(msgid=t_em['_id'])
        for i in t_em['messages']:
            print(i)
            ch = self.bot.get_channel(i['channel'])
            msg = await ch.fetch_message(i['embed_messages_id'])
            await msg.edit(embed=embed)
        await reaction.remove(user)

    # @commands.Cog.listener('on_reaction_remove')
    # async def on_reaction_remove(self, reaction: discord.Reaction, user):
    #     if user == self.bot:
    #         return
    #     em_id = db.get_tracked_embed(reaction.message.id)['_id']
    #     db.try_pull_all_reactions(em_id, user.name)
    #     if str(reaction.emoji) == '✅':
    #         db.remove_participation(em_id, 'participating', user.name)
    #     if str(reaction.emoji) == '❓':
    #         db.remove_participation(em_id, 'mb_participating', user.name)
    #     if str(reaction.emoji) == '❌':
    #         db.remove_participation(em_id, 'not_participating', user.name)
    #     embed = await self.generate_embed(msgid=em_id)
    #     # for message in db.get_tracked_embed():
    #     #     pass

    async def generate_embed(self, ctx=None, msgid=None):
        if ctx is not None:
            db_emb = db.get_embed(ctx.message.id)
        else:
            db_emb = db.get_embed(msgid)
            print(db_emb)
            print(db_emb["guild"])
        embed = discord.Embed(title=str(self.bot.get_guild(db_emb["guild"])))
        embed.add_field(name="Server invite", value=db.get_guild(db_emb['guild'])['invite_url'])
        embed.set_author(name=str(await self.bot.fetch_user(db_emb['author'])),
                         icon_url=db_emb['author_avatar'])
        embed.add_field(name="Game ID", value=db_emb['game_id'], inline=False)
        embed.add_field(name="Password", value=db_emb['game_password'], inline=True)
        embed.add_field(name="Game Rules", value=db_emb['game_rules'], inline=False)
        embed.add_field(name="Starting time", value=f'<t:{db_emb["starting_time"]}:T>, <t:{db_emb["starting_time"]}:R>',
                        inline=False)
        embed.add_field(name="✅Participating", value='Noone' if len(db_emb['participating']) < 1 else '\n'.join(
            str(i) for i in db_emb['participating']))
        embed.add_field(name="❓Maybe Participating",
                        value='Noone' if len(db_emb['mb_participating']) < 1 else '\n'.join(
                            str(i) for i in db_emb['mb_participating']))
        embed.add_field(name="❌Not Participating", value='Noone' if len(db_emb['not_participating']) < 1 else '\n'.join(
            str(i) for i in db_emb['not_participating']))
        return embed

    # async def generate_embed(self, ctx):

    #     embed = discord.Embed(title=server_name, url=server_invite, description=starting_times)
    #     embed.set_author(name=author, url=server_id, icon_url=author_pfp)
    #     embed.add_field(name="Game ID", value=game_id, inline=True)
    #     embed.add_field(name="Password", value=game_password, inline=True)
    #     embed.add_field(name="Game Rules", value=game_rules, inline=False)
    #     embed.add_field(name="Participating", value=list_participating, inline=True)
    #     embed.add_field(name="Maybe Participating", value=list_mb_participating, inline=True)
    #     embed.add_field(name="Not Participating", value=list_not_participating, inline=True)
    #     return embed


def setup(bot: commands.Bot):
    bot.add_cog(EmbedHandle(bot))
