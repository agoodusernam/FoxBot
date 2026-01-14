import logging

import discord
from discord.ext import commands

import counting_utils
import message_events_utils
from command_utils.CContext import CContext, CoolBot
from utils import utils, db_stuff

logger = logging.getLogger('discord')

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
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        logger.debug('Received message from %s: %s', message.author.global_name, message.content)
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
        
        if payload.channel_id != self.bot.config.counting_channel:
            return
        
        if payload.message_id != self.bot.config.last_counted_message_id:
            return
        
        unknown_author: bool = False
        author_id: int = 0
        
        if payload.cached_message is not None:
            author_id = payload.cached_message.author.id
        else:
            msg = db_stuff.get_from_db('messages', {'id': payload.message_id})
            if msg is not None:
                author_id = int(msg['author_id'])
            else:
                unknown_author = True
        
        channel = self.bot.get_channel(payload.channel_id)
        assert isinstance(channel, discord.TextChannel)
        
        if unknown_author or author_id == 0:
            await channel.send(f'Unknown user deleted their message. The next number is {self.bot.config.last_count + 1}')
            return
        
        await channel.send(f'<@{author_id}> deleted their message. The next number is `{self.bot.config.last_count + 1}`')


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
