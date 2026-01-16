import logging
from typing import Any

import discord
from discord.ext import commands

import cogs.counting_utils as counting_utils
import cogs.message_events_utils as message_events_utils
import command_utils.analysis
from command_utils.CContext import CContext, CoolBot
from utils import utils, db_stuff

logger = logging.getLogger('discord')


async def try_uid_to_discord_obj(uid: int, bot: CoolBot) -> discord.User | discord.Member | None:
    """
    Attempt to resolve a user ID to a display name.
    If the user's display name can't be found, return their ID as a string.
    """
    guild: discord.Guild | None = bot.get_guild(bot.config.guild_id)
    
    guild_member: discord.Member | None
    
    if guild is not None:
        guild_member = guild.get_member(uid)
    else:
        guild_member = None
    
    if isinstance(guild_member, discord.Member):
        return guild_member
    
    try:
        fetched = await bot.fetch_user(uid)
        if isinstance(fetched, discord.User):
            return fetched
    
    except (discord.NotFound, discord.HTTPException):
        pass
    
    return None

class TTS(commands.Cog, name='TTS'):
    def __init__(self, bot: CoolBot):
        self.bot: CoolBot = bot
    
    async def tts_msg(self, message: discord.Message):
        ctx: CContext
        
        ctx = await self.bot.get_context(message)
        command = self.bot.get_command('tts')
        
        if not command:
            logger.error('TTS command not found in bot commands.')
            return
        
        if not self.bot.config.tts_requires_role:
            logger.debug("Processing TTS command without role requirement.")
            
            await ctx.invoke(command, message=message.content.replace("!f", "").strip())  # type: ignore
            return
        
        if self.bot.config.required_tts_role == 0:
            logger.warning('TTS role requirement is enabled, but no role ID is set in the config.')
            await message.reply('TTS commands are currently unavailable.')
            return
        
        if isinstance(message.author, discord.User):
            await message.reply('TTS commands are only available in guild channels.')
            return
        
        has_role: bool = utils.user_has_role(message.author, self.bot.config.required_tts_role)
        
        if not has_role:
            await message.reply('You do not have the required role to use TTS commands.')
            return
        
        logger.debug("Processing TTS command with role requirement.")
        if not command:
            logger.error('TTS command not found in bot commands.')
            return
        
        await ctx.invoke(cmd, message=message.content.replace("!f", "").strip())  # type: ignore


class MessageLogging(commands.Cog, name='Message Logging'):
    def __init__(self, bot: CoolBot):
        self.bot: CoolBot = bot
        self.logs_channel: discord.TextChannel | None = None
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        logger.debug('Received message from %s: %s', message.author.display_name, message.content)
        if message.author.bot:
            return
        
        commands_enabled: bool = True
        if self.bot.config.staging:
            commands_enabled = False
        if self.bot.config.maintenance_mode:
            commands_enabled = False
        if message.author.id in self.bot.config.admin_ids or message.author.id in self.bot.config.dev_ids:
            commands_enabled = True
        
        assert isinstance(self.bot.command_prefix, str)
        if self.bot.config.staging:
            if commands_enabled and message.content.startswith(self.bot.command_prefix):
                self.bot.config.today = utils.formatted_today()
                logging.debug('Processing command in staging bot.')
                await self.bot.process_commands(message)
                
            elif not commands_enabled and message.content.startswith(self.bot.command_prefix):
                await message.channel.send('This is the staging bot. Commands are currently disabled.')
            
            return
        
        if message.content.startswith('\u200B'):  # Zero-width space
            logger.info(f'[NOT LOGGED] Message from {message.author.global_name} [#{message.channel}]: {message.content}')
            return
        
        await message_events_utils.check_landmine(message, bot=self.bot)
        
        if (message.channel.id == self.bot.config.counting_channel
                and message_events_utils.url_in_string(message.content)
                and not message.author.bot
                and not (message.author.id in self.bot.config.admin_ids
                         or message.author.id in self.bot.config.dev_ids)):
            # If the message contains a URL, delete it and send a warning
            await message.delete()
            await message.channel.send('Please do not send links in this channel.', delete_after=self.bot.config.del_after)
        
        if commands_enabled and message.content.startswith(self.bot.command_prefix):
            self.bot.config.today = utils.formatted_today()
            logging.debug('Processing command.')
            await self.bot.process_commands(message)
        
        
        elif not commands_enabled and message.content.startswith(self.bot.command_prefix):
            await message.channel.send('The bot is currently in maintenance mode. Please try again later.')
            return
        
        if ((message.channel.id == 1346720879651848202) and (message.author.id == 542798185857286144) and
                (message.content.startswith('FUN FACT'))):
            await message.channel.send('<@&1352341336459841688>', delete_after=2)
        
        if ((message.author != self.bot.user)
                and hasattr(message.channel, 'category_id')
                and (message.author.id not in self.bot.config.no_log.user_ids)
                and (message.channel.id not in self.bot.config.no_log.channel_ids)
                and (message.channel.category_id not in self.bot.config.no_log.category_ids)):
            
            await message_events_utils.log_msg(message)
        
        if message.channel.id == self.bot.config.counting_channel and not self.bot.config.staging:
            await counting_utils.counting_msg(message, self.bot)
            self.bot.config.save()
        
        if message.content.startswith('!f'):
            tts_cog = self.bot.get_cog('TTS')
            if tts_cog:
                await tts_cog.tts_msg(message) # type: ignore
            else:
                logger.error('TTS cog not loaded.')
    
    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent) -> None:
        if self.bot.config.staging:
            return
        
        db_msg = await db_stuff.get_from_db('messages', {'id': str(payload.message_id)})
        if db_msg is None:
            logger.error(f'Message {payload.message_id} not found in database.')
        else:
            await self.post_deleted_to_log(db_msg, payload.channel_id, payload.message_id)
        
        if payload.channel_id != self.bot.config.counting_channel:
            return
        
        if payload.message_id != self.bot.config.last_counted_message_id:
            return
        
        unknown_author: bool = False
        author_id: int = 0
        
        if payload.cached_message is not None:
            author_id = payload.cached_message.author.id
        else:
            if db_msg is not None:
                author_id = int(db_msg['author_id'])
            else:
                unknown_author = True
        
        channel = self.bot.get_channel(payload.channel_id)
        assert isinstance(channel, discord.TextChannel)
        
        if unknown_author or author_id == 0:
            await channel.send(f'Unknown user deleted their message. The next number is {self.bot.config.last_count + 1}')
            return
        
        await channel.send(f'<@{author_id}> deleted their message. The next number is `{self.bot.config.last_count + 1}`')
    
    async def post_deleted_to_log(self, message: discord.Message | dict[str, Any], channel_id: int, message_id: int):
        """
        Post the deleted message to the log channel.
        """
        assert self.bot.user is not None
        
        author_obj: discord.Member | discord.User | None
        display_name: str
        name: str
        content: str
        
        if isinstance(message, discord.Message):
            content = message.content
            if content.strip() == 'f!update': return
            author_obj = message.author
            
        else:
            content = message['content']
            if content.strip() == 'f!update': return
            author_obj = await try_uid_to_discord_obj(int(message['author_id']), self.bot)
        
        if content.strip() == '':
            content = 'Message had no content, it may have been an embed or was just an attachment.'
        
        
        if author_obj is None:
            display_name = 'Unknown user'
            name = 'Unknown user'
        else:
            if author_obj.id == self.bot.user.id:
                return
            
            display_name = author_obj.display_name
            name = author_obj.name
        
        
        embed = discord.Embed(title=f'{display_name} deleted a message in <#{channel_id}>', color=discord.Color.red())
        url = author_obj.display_avatar.url if author_obj is not None else self.bot.user.display_avatar.url
        embed.set_author(name=name, icon_url=url)
        embed.timestamp = discord.utils.utcnow()
        embed.footer.text = f'ID: {message_id}'
        embed.description = content
        
        if not isinstance(self.logs_channel, discord.TextChannel):
            logs_channel = self.bot.get_channel(self.bot.config.msg_log_channel_id)
            
            if not isinstance(logs_channel, discord.TextChannel):
                logger.error(f'Message log channel not found or not of correct type. Type: {type(logs_channel)}.')
                return
            
            self.logs_channel = logs_channel
        
        await self.logs_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:
        if self.bot.config.staging:
            return
        
        before_content: str
        after_content: str
        
        db_msg = await db_stuff.get_from_db('messages', {'id': str(payload.message_id)})
        if db_msg is None:
            logger.error(f'Message {payload.message_id} not found in database.')
            return
        
        author_obj: discord.Member | discord.User = payload.message.author
        after_content = payload.message.content
        
        if payload.cached_message is not None:
            before_content = payload.cached_message.content
        else:
            before_content = db_msg['content']
        
        await self.post_edit_to_log(before_content, after_content, author_obj, payload.channel_id, payload.message_id)
    
    
    async def post_edit_to_log(self, before_content: str, after_content: str,
                              author: discord.Member | discord.User,
                              channel_id: int, message_id: int) -> None:
        """
        Post the edited message to the log channel.
        """
        assert self.bot.user is not None
        display_name: str
        name: str
        description: str
        
        
        if author.id == self.bot.user.id:
            return
        
        
        if before_content.strip() == '':
            before_content = '[No message content. Perhaps an embed or attachment?]'
        if after_content.strip() == '':
            after_content = '[No message content. Perhaps an embed or attachment?]'
        
        description = '**Before:** ' + before_content + '\n**After:** ' + after_content
        
        embed = discord.Embed(title=f'{author.display_name} edited a message in <#{channel_id}>', color=discord.Color.blurple())
        embed.set_author(name=author.name, icon_url=author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        embed.footer.text = f'ID: {message_id}'
        embed.description = description
        
        if not isinstance(self.logs_channel, discord.TextChannel):
            logs_channel = self.bot.get_channel(self.bot.config.msg_log_channel_id)
            
            if not isinstance(logs_channel, discord.TextChannel):
                logger.error(f'Message log channel not found or not of correct type. Type: {type(logs_channel)}.')
                return
            
            self.logs_channel = logs_channel
        
        await self.logs_channel.send(embed=embed)
        


class ReactionEvents(commands.Cog, name='Reaction Logging'):
    def __init__(self, bot: CoolBot):
        self.bot: CoolBot = bot
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.guild_id is None:
            return
        if payload.member is None:
            return
        if self.bot.config.staging:
            return
        
        if payload.message_id != self.bot.config.reaction_roles.message_id:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        
        emoji_to_role = self.bot.config.get_emoji_to_role_discord_objects()
        try:
            role_id = emoji_to_role[payload.emoji]
        except KeyError:
            logger.info(f"Emoji {payload.emoji} not found in emoji_to_role mapping.")
            return
        
        role = guild.get_role(role_id)
        if role is None:
            logger.info(f"Role with ID {role_id} not found for emoji {payload.emoji}.")
            return
        
        try:
            await payload.member.add_roles(role)
        except discord.HTTPException:
            pass
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.message_id != self.bot.config.reaction_roles.message_id:
            return
        if self.bot.config.staging:
            return
        
        if payload.guild_id is None:
            return
        if payload.member is None:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        
        emoji_to_role = self.bot.config.get_emoji_to_role_discord_objects()
        try:
            role_id = emoji_to_role[payload.emoji]
        except KeyError:
            return
        
        role = guild.get_role(role_id)
        if role is None:
            return
        
        member = guild.get_member(payload.user_id)
        if member is None:
            return
        
        try:
            await member.remove_roles(role)
        except discord.HTTPException:
            pass


async def setup(bot: CoolBot):
    await bot.add_cog(MessageLogging(bot))
    await bot.add_cog(TTS(bot))
    await bot.add_cog(ReactionEvents(bot))
