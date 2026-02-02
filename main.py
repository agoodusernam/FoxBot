# pylint: disable=trailing-whitespace, line-too-long
import atexit
import logging
import os
from typing import Any

import discord
import discord.utils
from discord.ext import commands
from dotenv import load_dotenv

import help_cmd
from cogs import voice_events_utils
from command_utils.CContext import CoolBot, CContext
from utils import db_stuff, utils

load_dotenv()


@atexit.register
def on_exit():
    db_stuff.disable_connection()
    db_stuff.synchronous_disconnect()


bot = CoolBot(intents=discord.Intents.all(), case_insensitive=True)
logger = logging.getLogger('discord')

@bot.event
async def on_ready() -> None:
    await load_extensions()
    utils.check_env_variables()
    utils.clean_up_APOD()
    
    logger.info(f"Loaded {len(bot.cogs)} cogs:")
    for cog in bot.cogs:
        logger.info(f" - {cog}")
    
    logger.info(f"Total commands: {len(bot.commands)}")
    if bot.config.maintenance_mode:
        logger.info("Bot is in maintenance mode. Only admins can use commands.")
    
    if bot.config.staging:
        logger.info("Staging mode is enabled. Most features are disabled.")
    
    # Reconnect voice states
    if not bot.config.staging:
        for channel in bot.get_all_channels():
            if not isinstance(channel, discord.VoiceChannel):
                continue
            
            for member in channel.members:
                if member.bot:
                    continue
                
                await voice_events_utils.handle_join(member, channel)
                logger.info(f'Reconnected voice state for {member.name} in {channel.name}')
    
    assert bot.user is not None
    logging_channel: Any = bot.get_channel(bot.config.bot_logs_channel_id)
    if not isinstance(logging_channel, discord.TextChannel):
        logger.warning(f'No logging channel! ID: {bot.config.bot_logs_channel_id}')
    else:
        bot.logs_channel = logging_channel
        
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    logger.info('------')
    
    await bot.change_presence(activity=discord.CustomActivity(name='f!help'))


@bot.event
async def on_command_error(ctx: CContext, error: discord.ext.commands.CommandError):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send('This command is on cooldown. Please try again in ' +
                       f'{utils.seconds_to_human_readable(error.retry_after)}.')
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send('This command cannot be used in private messages.')
        await ctx.delete()
    
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'Missing required argument: {error.param.name}')
        await ctx.delete()
    
    elif isinstance(error, commands.BotMissingPermissions):
        missing = ', '.join(error.missing_permissions)
        await ctx.send(f'I am missing the following permissions to run this command: {missing}')
        await ctx.delete()
    
    elif isinstance(error, commands.CheckFailure):
        await ctx.send('You do not have permission to use this command.')
        await ctx.delete()
    
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f'Bad argument: {error}')
    
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(f'Command not found: {error}')
        await ctx.delete()
    
    else:
        logger.error(f'Error in command {ctx.command}: {error}', exc_info=error)


async def load_extensions() -> None:
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename[:-3].endswith("utils"):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                logger.info(f'Loaded {filename[:-3]}')
            
            except discord.ext.commands.ExtensionNotFound:
                logger.error(f'Extension not found: {filename[:-3]}')
            
            except discord.ext.commands.ExtensionAlreadyLoaded:
                logger.warning(f'Extension already loaded: {filename[:-3]}')
            
            except discord.ext.commands.NoEntryPointError:
                logger.error(f'No entry point found for extension {filename[:-3]}')
            
            except discord.ext.commands.ExtensionFailed as e:
                logger.error(f'Extension {filename[:-3]} encountered an error:\n{e}')
        else:
            logger.debug(f'Skipping {filename}')


@bot.check
async def not_blacklisted(ctx: CContext):
    """
    Check if the user is blacklisted from using commands.
    """
    if bot.blacklist.is_blacklisted(ctx.author.id):
        logger.debug(f'{ctx.author} is blacklisted.')
        return False
    return True

@bot.event
async def on_message(message: discord.Message):
    # Suppressed because we are listening for messages in cogs/message_events.py
    _ = message

# Run the bot
token = os.getenv('TOKEN')
if not isinstance(token, str):
    raise TypeError('TOKEN environment variable not set.')

bot.help_command = help_cmd.CustomHelpCommand()
bot.run(token=token, reconnect=True, log_handler=None)
