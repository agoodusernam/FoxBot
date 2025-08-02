import datetime
import json
import os
import re
from typing import Union

import discord
from discord.ext import commands
from discord.utils import get

import utils.utils as utils
from command_utils.CContext import CContext
from utils import db_stuff
from command_utils import analysis
from command_utils.checks import is_admin

STAFF_ROLE_ID = 1396395163835699310 # Role ID for staff, used in checks


def save_perms(ctx: CContext) -> None:
    previous_perms: dict[int, dict[str, dict[str, Union[bool, None]]]] = {}
    
    for channel in ctx.message.guild.channels:
        previous_perms[channel.id] = utils.format_permissions(channel.overwrites)
    
    if os.path.exists('hardlockdown.txt'):
        os.rename('hardlockdown.txt', 'hardlockdown_old.txt')
    
    with open('hardlockdown.txt', 'w') as file:
        json.dump(previous_perms, file, indent=4)


async def last_log(ctx: discord.ext.commands.Context, anonymous=False) -> None:
    mod_log_channel = ctx.bot.get_channel(1329367677940006952)  # Channel where the carlbot logs are sent
    pub_logs_channel = ctx.bot.get_channel(1345300442376310885)  # Public logs channel (#guillotine)
    
    if mod_log_channel is None or pub_logs_channel is None:
        await ctx.send('Mod log channel or public logs channel not found.', delete_after=ctx.bot.del_after)
        return
    
    last_mod_log_message = [msg async for msg in mod_log_channel.history(limit=1)][0]
    if last_mod_log_message.content == 'Posted':
        await ctx.send('This log has already been sent to the public logs channel.', delete_after=ctx.bot.del_after)
        return
    embed = last_mod_log_message.embeds[0]
    
    offence = embed.title.split(sep='|')[0].title()
    if offence.strip() == 'Warn':
        offence = 'Warning'
    description = embed.description.split(sep='\n')
    offender = re.sub(r'^.*?<', '<', description[0])  # Extract offender mention
    description.pop(0)
    duration = None
    if description[0].startswith('**Duration'):
        duration = description[0].replace('**Duration:**', '')
        description.pop(0)
    
    reason = description[0].replace('**Reason:** ', '')
    description.pop(0)
    new_description = f'**Offender**: {offender}\n**Reason**: {reason}'
    if not anonymous:
        moderator = description[0].replace('**Responsible moderator:** ', '')
        moderator_user = await commands.UserConverter().convert(ctx, moderator)
        new_description += f'\n**Responsible moderator**: {moderator_user.mention}'
    
    to_send_embed = discord.Embed(
            title=f'{offence}',
            description=new_description,
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
    )
    if duration:
        to_send_embed.add_field(name='Duration', value=duration, inline=False)
    
    await pub_logs_channel.send(embed=to_send_embed)
    await mod_log_channel.send('Posted')


class AdminCmds(commands.Cog, name='Admin', command_attrs=dict(hidden=True)):
    """Admin commands for managing the server and users."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='rek',
                      brief='Absolutely rek a user',
                      help='Admin only: Timeout a user for 28 days',
                      usage='rek <user_id/mention>')
    @commands.check(is_admin)
    async def rek(self, ctx: CContext, member: discord.Member) -> None:
        await ctx.delete()
        
        if member is None:
            await ctx.send(f'User not found.', delete_after=ctx.bot.del_after)
            return
        
        await member.timeout(datetime.timedelta(days=28), reason='get rekt nerd')
        await ctx.send(f'{member.display_name} has been rekt.', delete_after=ctx.bot.del_after)
        return
    
    @commands.command(name='hardlockdown',
                      brief='Lock down the entire server',
                      help='Admin only: Timeout all non-admin users for 28 days')
    @commands.check(is_admin)
    async def hard_lockdown(self, ctx: CContext):
        await ctx.delete()
        # await admin_cmds.hardlockdown(ctx.message)
        
        for member in ctx.guild.members:
            if member.id in ctx.bot.admin_ids:
                continue
            
            await member.timeout(datetime.timedelta(days=28), reason='Hard lockdown initiated by admin')
        
        await ctx.message.channel.send(
                'Hard lockdown initiated. All non-admin users have been timed out for 28 days.',
                delete_after=ctx.bot.del_after)
    
    @commands.command(name='unhardlockdown',
                      brief='Unlock the server from hard lockdown',
                      help='Admin only: Remove timeouts and blacklist from all users')
    @commands.check(is_admin)
    async def unhard_lockdown(self, ctx: CContext):
        await ctx.delete()
        guild: discord.Guild = ctx.guild
        for member in guild.members:
            if member.id in ctx.bot.admin_ids:
                continue
            
            if member.id in ctx.bot.blacklist_ids['ids']:
                ctx.bot.blacklist_ids['ids'].remove(member.id)
            
            try:
                await member.timeout(None, reason='Hard lockdown lifted by admin')
            except Exception as e:
                print(f'Error during unhardlockdown for user {member.id}: {e}')
                continue
        
        if os.path.isfile('blacklist_users.json'):
            with open('blacklist_users.json', 'r') as f:
                ctx.bot.blacklist_ids = json.load(f)
        
        await ctx.message.channel.send('Hard lockdown lifted. All users have been removed from timeout.',
                                       delete_after=ctx.bot.del_after)
    
    @commands.command(name='analyse', aliases=['analysis', 'analyze', 'stats', 'statistics', 'ana'],
                      brief='Analyze server message data',
                      help='Provides statistics about messages sent in the server',
                      usage='analyse [user_id/mention]')
    @commands.check(is_admin)
    @commands.cooldown(1, 2, commands.BucketType.guild)  # type: ignore
    async def analyse(self, ctx: CContext):
        await analysis.format_analysis(ctx)
    
    @commands.command(name='analyse_graph', aliases=['graph_analysis', 'graph_stats', 'graph_analyse', 'anag'],
                      brief='Analyze server message data with graphs',
                      help='Provides statistics about messages sent in the server with graphical representation',
                      usage='analyse_graph')
    @commands.check(is_admin)
    @commands.cooldown(1, 2, commands.BucketType.guild)  # type: ignore
    async def analyse_graph(self, ctx: CContext):
        await analysis.format_analysis(ctx, graph=True)
    
    @commands.command(name='analyse_voice', aliases=['voice_analysis', 'voice_stats', 'voice_analyse', 'anavc'],
                      brief='Analyze voice channel usage',
                      help='Provides statistics about voice channel usage in the server',
                      usage='analyse_voice [user_id/mention]')
    @commands.check(is_admin)
    @commands.cooldown(1, 30, commands.BucketType.user)  # type: ignore
    async def analyse_voice(self, ctx: CContext):
        await analysis.format_voice_analysis(ctx)
    
    @commands.command(name='analyse_graph', aliases=['graph_voice_analysis', 'voice_graph_stats',
                                                     'graph_analyse_voice', 'anavcg'],
                      brief='Analyze server message data with graphs',
                      help='Provides statistics about messages sent in the server with graphical representation',
                      usage='analyse_graph')
    @commands.check(is_admin)
    @commands.cooldown(1, 2, commands.BucketType.guild)  # type: ignore
    async def analyse_graph(self, ctx: CContext):
        await analysis.format_voice_analysis(ctx, graph=True)
    
    @commands.command(name='blacklist',
                      brief='Blacklist a user',
                      help='Admin only: Prevent a user from using bot commands',
                      usage='blacklist <user_id/mention>')
    @commands.check(is_admin)
    async def blacklist_id(self, ctx: CContext, user: discord.User):
        await ctx.delete()
        
        if user is None:
            await ctx.send('User not found.', delete_after=ctx.bot.del_after)
            return
        
        u_id = user.id
        
        if (u_id in ctx.bot.admin_ids) or (u_id in ctx.bot.dev_ids):
            await ctx.message.channel.send('You cannot blacklist an admin.', delete_after=ctx.bot.del_after)
            return
        
        if ctx.bot.blacklist.add_user(u_id):
            await ctx.send(f'User **{user.display_name}** has been blacklisted.', delete_after=ctx.bot.del_after)
            
            channel = ctx.bot.get_channel(1379193761791213618)
            await channel.set_permissions(get(ctx.bot.get_all_members(), id=u_id), send_messages=False)
        else:
            await ctx.message.channel.send(f'User **{user.display_name}** is already blacklisted.', delete_after=ctx.bot.del_after)
            return
        
    
    @commands.command(name='unblacklist',
                      brief='Remove user from blacklist',
                      help='Admin only: Allow a blacklisted user to use bot commands again',
                      usage='unblacklist <user_id/mention>')
    @commands.check(is_admin)
    async def unblacklist_id(self, ctx: CContext, user: discord.User):
        await ctx.delete()
        
        if user is None:
            await ctx.send('User not found.', delete_after=ctx.bot.del_after)
            return
        
        u_id = user.id
        
        if ctx.bot.blacklist.remove_user(u_id):
            await ctx.send(f'User **{user.display_name}** has been removed from the blacklist.',
                           delete_after=ctx.bot.del_after)
            
            channel = ctx.bot.get_channel(1379193761791213618)
            await channel.set_permissions(get(ctx.bot.get_all_members(), id=u_id), send_messages=True)
        else:
            await ctx.send(f'User **{user.display_name}** was not blacklisted.', delete_after=ctx.bot.del_after)
            return
    
    @commands.command(name='echo',
                      brief='Make the bot say something',
                      help='Admin only: Makes the bot say the specified message',
                      usage='echo [channel id] <message>')
    @commands.check(is_admin)
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def echo_cmd(self, ctx: CContext, *, message: str):
        if message is None:
            await ctx.channel.send('Nothing to echo.', delete_after=ctx.bot.del_after)
            return
        
        msg: str = message
        
        # Send the message content back to the channel
        split_message: list[str] = msg.split()
        channel: discord.abc.MessageableChannel = ctx.channel
        try:
            channel_id: int = int(split_message[0].replace('#', '', 1).replace('<', '', 1).replace('>', '', 1))
            channel: discord.abc.MessageableChannel = ctx.bot.get_channel(channel_id)
            msg = msg.replace(str(channel_id), '', 1)
        except ValueError:
            pass
        
        await channel.send(msg)
        
        # Delete the original message
        await ctx.message.delete()
    
    @commands.command(name='edit_message',
                      brief='Edit a message the bot has sent',
                      help='Admin only: Edit a specific message sent by the bot',
                      usage='edit_message <channel_id> <message_id> <new_content>')
    @commands.check(is_admin)
    async def edit_message_cmd(self, ctx: CContext, *, args: str):
        await ctx.delete()
        
        split_args = args.split(' ', 2)
        try:
            channel_id = int(split_args[0])
        except ValueError:
            await ctx.send('Invalid channel ID format. Please provide a valid integer ID.',
                           delete_after=ctx.bot.del_after)
            return
        
        try:
            message_id = int(split_args[1])
        
        except ValueError:
            await ctx.send('Invalid message ID format. Please provide a valid integer ID.',
                           delete_after=ctx.bot.del_after)
            return
        
        if len(split_args) < 3:
            await ctx.send('Please provide the new content for the message.',
                           delete_after=ctx.bot.del_after)
            return
        new_content = split_args[2]
        
        message: discord.Message = await ctx.bot.get_channel(channel_id).fetch_message(message_id)
        if message.author.id != ctx.bot.user.id:
            await ctx.send('You can only edit messages sent by the bot.',
                           delete_after=ctx.bot.del_after)
            return
        try:
            await message.edit(content=new_content)
            await ctx.send(f'Message with ID {message_id} has been edited.',
                           delete_after=ctx.bot.del_after)
        except discord.NotFound:
            await ctx.send(f'Message with ID {message_id} not found.',
                           delete_after=ctx.bot.del_after)
        except discord.Forbidden:
            await ctx.send(f'Cannot edit message with ID {message_id}. Permission denied.',
                           delete_after=ctx.bot.del_after)
        except discord.HTTPException as e:
            await ctx.send(f'Failed to edit message with ID {message_id}. Error: {e}',
                           delete_after=ctx.bot.del_after)
    
    @commands.command(name='last_log', aliases=['lastlog', 'lastmodlog', 'last_modlog', 'modlog', 'log'],
                      brief='Send the last modlog message',
                      help='Admin only: Send the last modlog message',
                      usage='last_log')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    @commands.has_role(STAFF_ROLE_ID)
    async def send_last_log(self, ctx: CContext):
        await ctx.delete()
        
        await last_log(ctx)
    
    @commands.command(name='last_log_anonymous', aliases=['last_log_a', 'lastlog_anonymous', 'lastlog_a',
                                                          'last_modlog_anonymous', 'last_modlog_a',
                                                          'modlog_anonymous', 'modlog_a', 'log_anonymous', 'log_a',
                                                          'loga'],
                      brief='Send the last modlog message anonymously',
                      help='Admin only: Send the last modlog message without mentioning the moderator',
                      usage='last_log_anonymous')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    @commands.has_role(STAFF_ROLE_ID)
    async def send_last_log_anonymous(self, ctx: CContext):
        await ctx.delete()
        
        await last_log(ctx, anonymous=True)
    
    @commands.command(name='warn',
                      brief='Warn a user',
                      help='Admin only: Warn a user without showing in the public logs',
                      usage='warn <user_id/mention> <reason>')
    @commands.check(is_admin)
    async def warn(self, ctx: CContext, member: discord.Member, *,
                   reason: str = 'No reason provided'):
        await ctx.delete()
        
        if member is None:
            await ctx.send('User not found.', delete_after=ctx.bot.del_after)
            return
        data = {
            'user_id':   member.id,
            'reason':    reason,
            'timestamp': int(discord.utils.utcnow().timestamp()),
            'issuer_id': ctx.author.id,
        }
        
        db_stuff.send_to_db("warns", data)
        await ctx.send(f'{member.display_name} has been warned for: {reason}', delete_after=ctx.bot.del_after)
    
    @commands.command(name='warns',
                      brief='View warns for a user',
                      help='Admin only: View all warns for a user',
                      usage='warns <user_id/mention>')
    @commands.check(is_admin)
    async def view_warns(self, ctx: CContext, member: discord.Member):
        await ctx.delete()
        
        if member is None:
            await ctx.send('User not found.', delete_after=ctx.bot.del_after)
            return
        
        warns = db_stuff.get_many_from_db("warns", {"user_id": member.id})
        if not warns:
            await ctx.send(f'{member.display_name} has no warns.', delete_after=ctx.bot.del_after)
            return
        
        warn_list = '\n'.join([f'**{i + 1}.** {warn["reason"]} (Issued by '
                               f'{(await ctx.bot.fetch_user(warn["issuer_id"])).display_name} at '
                               f'<t:{warn["timestamp"]}>)'
                               for i, warn in enumerate(warns)])
        
        embed = discord.Embed(title=f'Warns for {member.display_name}', description=warn_list,
                              color=discord.Color.red())
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AdminCmds(bot))
