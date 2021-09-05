import time
import asyncio
import discord
from discord.ext import commands, tasks
import auxiliary
from db import db
from auxiliary import time_handle


class EmbedHandle(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        db.clear_all_embeds()
        self.garbage_collect.start()
        self.notifyPlayer.start()


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
        await ctx.message.delete()
        for i in db.get_all_guilds():
            ch = self.bot.get_channel(i['channel'])
            await ch.send(f'<@&{i["ping_role"]}>')
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
        current_reacts = db.get_current_participation(db.get_tracked_embed(reaction.message.id)['_id'], {'name': user.name, 'uid': user.id})
        print(db.try_pull_all_reactions(db.get_tracked_embed(reaction.message.id), {'name': user.name, 'uid': user.id}).acknowledged)
        if str(reaction.emoji) == '✅' and not {'name': user.name, 'uid': user.id} in current_reacts[0]:
            db.add_participation(t_em['_id'], 'participating', [user.name, user.id])
        elif str(reaction.emoji) == '❓' and not {'name': user.name, 'uid': user.id} in current_reacts[1]:
            db.add_participation(t_em['_id'], 'mb_participating', [user.name, user.id])
        elif str(reaction.emoji) == '❌' and not {'name': user.name, 'uid': user.id} in current_reacts[2]:
            db.add_participation(t_em['_id'], 'not_participating', [user.name, user.id])
        elif str(reaction.emoji) == '🏳️':
            db.try_pull_all_reactions(t_em['_id'], {'name': user.name, 'uid': user.id})
        embed = await self.generate_embed(msgid=t_em['_id'])
        for i in t_em['messages']:
            ch = self.bot.get_channel(i['channel'])
            msg = await ch.fetch_message(i['embed_messages_id'])
            await msg.edit(embed=embed)
        await reaction.remove(user)

    async def generate_embed(self, ctx=None, msgid=None):
        if ctx is not None:
            db_emb = db.get_embed(ctx.message.id)
        else:
            db_emb = db.get_embed(msgid)
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
            str(i['name']) for i in db_emb['participating']))
        embed.add_field(name="❓Maybe Participating",
                        value='Noone' if len(db_emb['mb_participating']) < 1 else '\n'.join(
                            str(i['name']) for i in db_emb['mb_participating']))
        embed.add_field(name="❌Not Participating", value='Noone' if len(db_emb['not_participating']) < 1 else '\n'.join(
            str(i['name']) for i in db_emb['not_participating']))
        return embed
    
    @tasks.loop(minutes=10)
    async def garbage_collect(self):
        for event in db.get_all_embeds():
            if int(time.time()) - event['starting_time'] > 172800:
                db.remove_embed(event['_id'])
                db.remove_tracked_embed(event['_id'])

    @tasks.loop(seconds=10)
    async def notifyPlayer(self):
        for event in db.get_all_embeds():
            if event['starting_time'] - int(time.time()) < 300 and event['when_notified'] == 600:
                for player in event['participating'] + event['mb_participating']:
                    await self.bot.get_user(player['uid']).send(f"hey, game is starting in around 5 minutes! Hurry up! {str(db.get_guild(event['guild'])['invite_url'])}")
                db.set_notify(event['_id'], 300)
            elif event['starting_time'] - int(time.time()) < 600 and event['when_notified'] == 3600:
                for player in event['participating'] + event['mb_participating']:
                    await self.bot.get_user(player['uid']).send(f"hey, game is starting in around 10 minutes! Hurry up! {str(db.get_guild(event['guild'])['invite_url'])}")
                db.set_notify(event['_id'], 600)
            elif event['starting_time'] - int(time.time()) < 3600 and event['when_notified'] == 0:
                for player in event['participating'] + event['mb_participating']:
                    await self.bot.get_user(player['uid']).send(f"hey, game is starting in around one hour. {str(db.get_guild(event['guild'])['invite_url'])}")
                db.set_notify(event['_id'], 3600)

    @commands.command(name="update_id",
                        usage=' <target embed> <game id> [password=None]',
                        description="update the game ID of an embed you are an author of, and the password if one is provided.")
    async def update_id(self, ctx, target_embed, game_id, password=None):
        tg_embed = db.get_tracked_embed(target_embed)['_id']
        if tg_embed['author'] == ctx.message.author.id:
            db.update_embed(tg_embed, 'game_id', game_id )
            if password is not None:
                db.update_embed(tg_embed, 'game_password', password )
        else:
            ctx.message.send(f'you are not the author of this embed. <@{ctx.message.author.id}>')
        ctx.message.delete()

    @commands.command(name="update_time",
                        usage=' <target embed> <new time>',
                        description="update the new time of an embed you are an author of.")
    async def update_time(self, ctx, target_embed, gtime):
        tg_embed = db.get_tracked_embed(target_embed)['_id']
        if tg_embed['author'] == ctx.message.author.id:
            db.update_embed(tg_embed, 'game_time', time_handle.interpret_time(gtime))
            db.update_when_notified(0)
        else:
            ctx.message.send(f'you are not the author of this embed. <@{ctx.message.author.id}>')
        ctx.message.delete()



def setup(bot: commands.Bot):
    bot.add_cog(EmbedHandle(bot))
