import datetime
import logging
import typing
from pathlib import Path
from typing import Any

import discord
import discord.utils
from discord.ext import commands
from discord.ext.commands import guild_only

import utils.utils
from cogs.admin_cmds_utils import sort_by_timestamp, last_log
from command_utils import analysis
from command_utils.CContext import CContext, CoolBot
from command_utils.checks import is_admin
from config import bot_config
from utils import db_stuff

logger = logging.getLogger('discord')

staff_role_id = bot_config.get_config_option('staff_role_id', 0)

class AdminCmds(commands.Cog, name='Admin', command_attrs=dict(hidden=True)):
    """Admin commands for managing the server and users."""
    
    def __init__(self, bot: CoolBot) -> None:
        self.bot: CoolBot = bot
    
    @commands.command(name='rek',
                      brief='Absolutely rek a user',
                      help='Admin only: Timeout a user for 28 days',
                      usage='f!rek <user_id/mention>')
    @commands.check(is_admin)
    async def rek(self, ctx: CContext, member: discord.Member) -> None:
        
        if member is None:
            await ctx.delete()
            await ctx.send(f'User not found.', delete_after=ctx.bot.del_after)
            return
        
        await member.timeout(datetime.timedelta(days=28), reason='get rekt nerd')
        await ctx.send(f'{member.display_name} has been rekt.')
        return
    
    @commands.command(name='rekp',
                      brief='Absolutely rek a user privately',
                      help='Admin only: Timeout a user for 28 days and delete the message',
                      usage='f!rek <user_id/mention>')
    @commands.check(is_admin)
    async def rekp(self, ctx: CContext, member: discord.Member) -> None:
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
    @commands.guild_only()
    @commands.check(is_admin)
    async def hard_lockdown(self, ctx: CContext):
        assert ctx.guild is not None
        await ctx.delete()
        for member in ctx.guild.members:
            if member.id in ctx.bot.admin_ids:
                continue
            try:
                await member.timeout(datetime.timedelta(hours=1), reason='Hard lockdown initiated by admin')
            except Exception as e:
                logger.error(f'Error during hardlockdown for user {member.id}: {e}')
                continue
        
        await ctx.message.channel.send('Hard lockdown initiated. All non-admin users have been timed out for 28 days.')
    
    @commands.command(name='unhardlockdown',
                      brief='Unlock the server from hard lockdown',
                      help='Admin only: Remove timeouts and blacklist from all users')
    @commands.check(is_admin)
    @guild_only()
    async def unhard_lockdown(self, ctx: CContext):
        assert ctx.guild is not None
        await ctx.delete()
        guild: discord.Guild = ctx.guild
        for member in guild.members:
            if member.id in ctx.bot.admin_ids:
                continue
            
            try:
                await member.timeout(None, reason='Hard lockdown lifted by admin')
            except Exception as e:
                logger.error(f'Error during unhardlockdown for user {member.id}: {e}')
                continue
        
        await ctx.message.channel.send('Hard lockdown lifted. All users have been removed from timeout.',
                                       delete_after=ctx.bot.del_after)
    
    @commands.command(name='analyse', aliases=['ana'],
                      brief='Analyze server message data',
                      help='Provides statistics about messages sent in the server',
                      usage='f!ana [user_id/mention]')
    @commands.check(is_admin)
    @commands.cooldown(1, 2, commands.BucketType.guild)  # type: ignore
    async def analyse(self, ctx: CContext, user: typing.Optional[discord.Object] = None, *, args: str = ''):
        await analysis.format_analysis(ctx, graph=False, to_analyse=user, flag=args)
    
    @commands.command(name='analyse_graph', aliases=['anag'],
                      brief='Analyze server message data with graphs',
                      help='Provides statistics about messages sent in the server with graphical representation',
                      usage='f!anag')
    @commands.check(is_admin)
    @commands.cooldown(1, 2, commands.BucketType.guild)  # type: ignore
    async def analyse_graph(self, ctx: CContext,user: typing.Optional[discord.Object] = None, *, args: str = ''):
        await analysis.format_analysis(ctx, graph=True, to_analyse=user, flag=args)
    
    @commands.command(name='analyse_voice', aliases=['anavc'],
                      brief='Analyze voice channel usage',
                      help='Provides statistics about voice channel usage in the server',
                      usage='f!anavc [user_id/mention]')
    @commands.check(is_admin)
    @commands.cooldown(1, 2, commands.BucketType.user)  # type: ignore
    async def analyse_voice(self, ctx: CContext, user: typing.Optional[discord.Object] = None, *, args: str = ''):
        include_left = False
        if args.strip() == '-il':
            include_left = True
            
        await analysis.format_voice_analysis(ctx, graph=False, user=user, include_left=include_left)
    
    @commands.command(name='analyse_vc_graph', aliases=['anavcg'],
                      brief='Analyze server message data with graphs',
                      help='Provides statistics about messages sent in the server with graphical representation',
                      usage='f!anavcg')
    @commands.check(is_admin)
    @commands.cooldown(1, 2, commands.BucketType.guild)  # type: ignore
    async def analyse_vc_graph(self, ctx: CContext, user: typing.Optional[discord.Object] = None, *, args: str = ''):
        include_left = False
        if args.strip() == '-il':
            include_left = True
        
        await analysis.format_voice_analysis(ctx, graph=True, user=user, include_left=include_left)
    
    @commands.command(name='time_in_vc', aliases=["tiv"],
            brief="Get the time spent in a voice channel",
            help="Get the time a specific user has spent in a specific channel",
            usage="f!tiv <user> <channel>")
    @commands.check(is_admin)
    @commands.cooldown(1, 2, commands.BucketType.user) # type: ignore
    async def time_in_vc(self, ctx: CContext, user: discord.User, channel: discord.VoiceChannel):
        await analysis.user_time_in_channel(ctx, user, channel)
        
    
    @commands.command(name='blacklist',
                      brief='Blacklist a user',
                      help='Admin only: Prevent a user from using bot commands',
                      usage='f!blacklist <user_id/mention>')
    @commands.check(is_admin)
    async def blacklist_id(self, ctx: CContext, user: discord.User):
        if user is None:
            await ctx.send('User not found.', delete_after=ctx.bot.del_after)
            return
        
        u_id = user.id
        
        if (u_id in ctx.bot.admin_ids) or (u_id in ctx.bot.dev_ids):
            await ctx.message.channel.send('You cannot blacklist an admin.', delete_after=ctx.bot.del_after)
            return
        
        if ctx.bot.blacklist.add_user(u_id):
            await ctx.send(f'User **{user.display_name}** has been blacklisted.')
            
        else:
            await ctx.message.channel.send(f'User **{user.display_name}** is already blacklisted.', delete_after=ctx.bot.del_after)
            return
        
    
    @commands.command(name='unblacklist',
                      brief='Remove user from blacklist',
                      help='Admin only: Allow a blacklisted user to use bot commands again',
                      usage='f!unblacklist <user_id/mention>')
    @commands.check(is_admin)
    async def unblacklist_id(self, ctx: CContext, user: discord.User):
        if user is None:
            await ctx.send('User not found.', delete_after=ctx.bot.del_after)
            return
        
        u_id = user.id
        
        if ctx.bot.blacklist.remove_user(u_id):
            await ctx.send(f'User **{user.display_name}** has been removed from the blacklist.')
            
        else:
            await ctx.send(f'User **{user.display_name}** was not blacklisted.', delete_after=ctx.bot.del_after)
            return
    
    @commands.command(name='echo',
                      brief='Make the bot say something',
                      help='Admin only: Makes the bot say the specified message',
                      usage='f!echo [channel id] <message>')
    @commands.check(is_admin)
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def echo_cmd(self, ctx: CContext, *, message: str):
        if message is None:
            await ctx.send('Nothing to echo.', delete_after=ctx.bot.del_after)
            return
        
        msg: str = message
        
        split_message: list[str] = msg.split()
        try:
            channel_id: int = int(split_message[0].replace('#', '', 1).replace('<', '', 1).replace('>', '', 1))
            channel: Any = ctx.bot.get_channel(channel_id) # I wanted to type this but i gave up
            if channel is None:
                raise ValueError
            msg = msg.replace(str(channel_id), '', 1)
        except ValueError:
            channel = ctx.channel
        
        await channel.send(msg)
        
        await ctx.delete()
    
    @commands.command(name='edit_message',
                      brief='Edit a message the bot has sent',
                      help='Admin only: Edit a specific message sent by the bot',
                      usage='f!edit_message <channel_id> <message_id> <new_content>')
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
                      usage='f!last_log')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    @commands.has_role(staff_role_id)
    async def send_last_log(self, ctx: CContext):
        await ctx.delete()
        await last_log(ctx)
    
    @commands.command(name='last_log_anonymous', aliases=['last_log_a', 'lastlog_anonymous', 'lastlog_a',
                                                          'last_modlog_anonymous', 'last_modlog_a',
                                                          'modlog_anonymous', 'modlog_a', 'log_anonymous', 'log_a',
                                                          'loga'],
                      brief='Send the last modlog message anonymously',
                      help='Admin only: Send the last modlog message without mentioning the moderator',
                      usage='f!last_log_anonymous')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    @commands.has_role(staff_role_id)
    async def send_last_log_anonymous(self, ctx: CContext):
        await ctx.delete()
        await last_log(ctx, anonymous=True)
    
    @commands.command(name='warn',
                      brief='Warn a user',
                      help='Admin only: Warn a user without showing in the public logs',
                      usage='f!warn <user_id/mention> <reason>')
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
        
        await db_stuff.send_to_db("warns", data)
        await ctx.send(f'{member.display_name} has been warned for: {reason}', delete_after=ctx.bot.del_after)
    
    @commands.command(name='warns',
                      brief='View warns for a user',
                      help='Admin only: View all warns for a user',
                      usage='f!warns <user_id/mention>')
    @commands.check(is_admin)
    async def view_warns(self, ctx: CContext, member: discord.Member):
        await ctx.delete()
        
        if member is None:
            await ctx.send('User not found.', delete_after=ctx.bot.del_after)
            return
        
        warns = await db_stuff.get_many_from_db("warns", {"user_id": member.id})
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
        
    @commands.command(name='verify', aliases=['ver', 'v'],
                        brief='Verify a user',
                        help='Admin only: Assign the verified role to a user',
                        usage='f!verify <user_id/mention>')
    @commands.guild_only()
    @commands.has_role(staff_role_id)
    async def verify(self, ctx: CContext, member: discord.Member):
        await ctx.delete()
        assert ctx.guild is not None
        
        if member is None:
            await ctx.send('User not found.', delete_after=ctx.bot.del_after)
            return
        
        
        try:
            roles: list[discord.Role] = []
            for role_id in ctx.bot.config.verified_roles:
                role = discord.utils.get(ctx.guild.roles, id=role_id)
                if role is None:
                    logger.error(f'Failed to find role with ID {role_id} for verification.')
                    continue
                roles.append(role)
            
            await member.add_roles(*roles, reason='Verified by admin')
                    
            await ctx.send(f'{member.display_name} has been verified.', delete_after=ctx.bot.del_after)
            
        except Exception as e:
            logger.error(f'Failed to assign verified role to {member.display_name}: {e}')
            return
    
    @commands.command(name='last_messages', aliases=['lastmsgs', 'last_msgs'],
                      brief='Fetch last messages from a user',
                      help='Admin only: Fetch the last messages sent by a user in the server',
                      usage='f!last_messages <user_id/mention> [number_of_messages]')
    @commands.has_role(staff_role_id)
    async def last_messages(self, ctx: CContext, member: discord.User, number_of_messages: int = 5):
        await ctx.delete()
        
        if member is None:
            await ctx.send('User not found.', delete_after=ctx.bot.del_after)
            return
        
        if number_of_messages < 1:
            await ctx.send('Please specify a number between above 0 for the number of messages.',
                           delete_after=ctx.bot.del_after)
            return
        
        messages = await analysis.remove_invalid_messages(await db_stuff.cached_download_all())
        messages = [msg for msg in messages if msg['author_id'] == str(member.id)]
        messages = sort_by_timestamp(messages)[:number_of_messages]
        if not messages:
            await ctx.send(f'No messages found for {member.display_name}.', delete_after=ctx.bot.del_after)
            return
        
        attachments: list[Path] = []
        
        formatted_messages: str = ""
        for msg in messages:
            formatted_messages += f'**Channel:** <#{msg["channel_id"]}>\n'
            formatted_messages += f'**Timestamp:** <t:{int(msg["timestamp"].timestamp())}>\n'
            formatted_messages += f'**Content:** {discord.utils.escape_mentions(msg["content"])}'
            if msg["HasAttachments"]:
                attachment = utils.utils.get_attachment(msg["author_id"], msg["id"])
                if attachment is None:
                    formatted_messages += '\nMessage had attachment(s), but failed to retrieve them.'
                elif isinstance(attachment, Path):
                    formatted_messages += f'\nAttachment: {len(attachments)}{"".join(attachment.suffixes)}'
                    attachments.append(attachment)
                else:
                    for path in attachment:
                        formatted_messages += f'\nAttachment: {len(attachments)}{"".join(path.suffixes)}'
                        attachments.append(path)
            formatted_messages += '\n'
            
        if len(formatted_messages) > 2000:
            formatted_messages = formatted_messages[:1995] + '...'
            
        await ctx.send(f"Last {number_of_messages} sent by {member.display_name}:")
        await ctx.send(formatted_messages, suppress_embeds=True)
        if attachments:
            utils.utils.copy_attach_to_temp(attachments)
    
    @commands.command(name='landmine', aliases=['lm'],
                      brief='Set landmines in a channel',
                      help='Admin only: Set a specified number of landmines in a channel',
                      usage='f!landmine [channel_id] [amount]'
                      )
    @commands.check(is_admin)
    @guild_only()
    async def landmine(self, ctx: CContext, channel_or_amount: typing.Union[discord.TextChannel, int], amount: int = 0) -> None:
        if isinstance(channel_or_amount, int):
            channel = ctx.channel
            amount: int = channel_or_amount
        else:
            channel = channel_or_amount
        
        if amount < 0:
            await ctx.send('Please specify the number of landmines.',
                           delete_after=ctx.bot.del_after)
            return
        
        ctx.bot.landmine_channels[channel.id] = amount
        assert hasattr(channel, 'mention')
        await ctx.send(f'You have set {amount} landmines in {channel.mention}!')
    
    @commands.command(name='force_lm', aliases=['flm'],
                      brief='Force a landmine',
                      help='Admin only: Force a landmine for a specified user',
                      usage='f!force_lm <user>')
    @commands.check(is_admin)
    async def force_landmine(self, ctx: CContext, user: discord.Member) -> None:
        ctx.bot.forced_landmines.add(user.id)
        
        await ctx.send(f'{user.display_name} has been forced into landmine the next time they send a message.')
    
    @commands.command(name='landmines', aliases=['lm_list', 'lms'],
                      brief='List landmines',
                      help='Admin only: List all landmines',
                      usage='f!landmines')
    @commands.check(is_admin)
    async def landmines(self, ctx: CContext) -> None:
        if not ctx.bot.landmine_channels:
            await ctx.send('No landmines have been set.', delete_after=ctx.bot.del_after)
            return
        
        landmine_list = '\n'.join(
                [f'Channel: <#{channel_id}> - Landmines: {amount}'
                 for channel_id, amount in ctx.bot.landmine_channels.items()])
        
        await ctx.send(f'Landmines set in the following channels:\n{landmine_list}')
        
        if ctx.bot.forced_landmines:
            forced_landmines_list = ', '.join(
                    [f'<@{user_id}>' for user_id in ctx.bot.forced_landmines])
            await ctx.send(f'Forced landmines for the following users: {forced_landmines_list}')
    
    @commands.command(name='clear_lm', aliases=['clm'],
                      brief='Clear landmines',
                      help='Admin only: Clear all landmines',
                      usage='f!clear_lm')
    @commands.check(is_admin)
    async def clear_landmines(self, ctx: CContext) -> None:
        ctx.bot.landmine_channels = {}
        
        await ctx.send('All landmines have been cleared.')
    
    @commands.command(name='reset_counting_fails',
                      brief='Reset the number of failed counting attempts',
                      help='Admin only: Reset the number of failed counting attempts by a user',
                      usage='f!reset_counting_fails <user>')
    @commands.check(is_admin)
    async def reset_count_fails(self, ctx: CContext, member: discord.Member):
        reset: bool = ctx.bot.config.reset_counting_fails(member.id)
        if reset:
            await ctx.send(f'Counting fails for {member.display_name} have been reset.')
            return
        await ctx.send(f'{member.display_name} does not have any failed counting attempts to reset.')
        return
    

async def setup(bot):
    await bot.add_cog(AdminCmds(bot))
