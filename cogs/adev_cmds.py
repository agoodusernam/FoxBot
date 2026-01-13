import asyncio
import gc
import os
import sys
import threading
from typing import Any
import logging

import discord
import psutil
from discord.ext import commands

import utils.utils
from command_utils.checks import is_dev
from custom_logging import voice_log
from utils import db_stuff
from command_utils.CContext import CContext, CoolBot
# added the 'a' to the start of the file so it loads first

logger = logging.getLogger('discord')

async def aexec(func_name: str, context: CContext) -> Any:
    locs: dict[str, Any] = {}
    ctx = context
    logger.debug(f'Running function: {func_name}')
    
    exec(f'async def __ex(): await discord.utils.maybe_coroutine({func_name})', globals(), locs)
    return await locs['__ex']()

def run_func(loop: asyncio.AbstractEventLoop, func_name: str, ctx: CContext) -> Any:
    asyncio.set_event_loop(loop)
    loop.run_until_complete(aexec(func_name, ctx))

async def shutdown(bot: CoolBot, update=False, restart=False) -> None:
    voice_log.leave_all(bot)
    db_stuff.disconnect()
    await bot.close()
    
    if update:
        os.system('git pull https://github.com/agoodusernam/FoxBot.git')
    
    if restart:
        os.execv(sys.executable, ['python'] + sys.argv)

async def upload_all_history(channel: discord.TextChannel) -> None:
    logger.info(f'Deleting old messages from channel: {channel.name}, ID: {channel.id}')
    db_stuff.del_channel_from_db(channel)
    logger.info(f'Starting to download all messages from channel: {channel.name}, ID: {channel.id}')
    messages = [message async for message in channel.history(limit=None)]
    logger.info(f'Downloaded {len(messages)} messages from channel: {channel.name}, ID: {channel.id}')
    bulk_data: list[dict[str, Any]] = []
    for i, message in enumerate(messages):
        if not isinstance(message.channel, discord.TextChannel):
            logger.info("Message channel is not a TextChannel, skipping...")
            continue
        
        has_attachment = False
        if message.attachments:
            has_attachment = True
        
        if message.reference is None:
            reply = None
        
        else:
            reply = str(message.reference.message_id)
        
        json_data = {
            'author':             message.author.name,
            'author_id':          str(message.author.id),
            'author_global_name': message.author.global_name,
            'content':            message.content,
            'reply_to':           reply,
            'HasAttachments':     has_attachment,
            'timestamp':          message.created_at.timestamp(),
            'id':                 str(message.id),
            'channel':            message.channel.name,
            'channel_id':         str(message.channel.id)
        }
        bulk_data.append(json_data)
    
    db_stuff.bulk_send_messages(bulk_data)
    del bulk_data
    gc.collect()


async def upload_whole_server(guild: discord.Guild, author: discord.User | discord.Member, nolog_channels: list[int]) -> None:
    dm = await author.create_dm()
    await dm.send(f'Starting to download all messages from server: {guild.name}')
    await dm.send('--------------------------')
    for channel in guild.text_channels:
        if channel.id in nolog_channels:
            await dm.send(f'Skipping channel {channel.name} as it is in the nolog list')
            await dm.send('--------------------------')
            continue
        if channel.permissions_for(guild.me).read_message_history:
            await dm.send(f'Uploading messages from channel: {channel.name}')
            await upload_all_history(channel)
            await dm.send(f'Finished uploading all messages from channel: {channel.name}')
            await dm.send('--------------------------')
        else:
            await dm.send(f'Skipping channel {channel.name} due to insufficient permissions')
            await dm.send('--------------------------')
    
    logger.info('Finished uploading all messages from server:', guild.name)
    await dm.send(f'Finished uploading all messages from server: {guild.name}')


class DevCommands(commands.Cog, name='Dev', command_attrs=dict(hidden=True, add_check=is_dev)):
    """Developer commands for bot maintenance and management."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='restart',
                      brief='Restart the bot',
                      help='Dev only: restart the bot instance')
    async def restart_cmd(self, ctx: CContext):
        await ctx.delete()
        await shutdown(ctx.bot, update=False, restart=True)
    
    @commands.command(name='shutdown',
                      brief='Shutdown the bot',
                      help='Dev only: Shutdown the bot instance')
    async def shutdown(self, ctx: CContext):
        await ctx.delete()
        await shutdown(ctx.bot, update=False, restart=False)
    
    @commands.command(name='update',
                      brief='Update the bot code',
                      help='Dev only: Update the bot code from the repository',
                      usage='f!update')
    async def update(self, ctx: CContext):
        await ctx.delete()
        await shutdown(ctx.bot, update=True, restart=True)
        
    """
    @commands.command(name='upload_all_history',
                      brief='Upload all messages from a server',
                      help='Dev only: Upload all messages from a specific guild to the database',
                      usage='f!upload_all_history')
    async def upload_all_history(self, ctx: CContext):
        await ctx.delete()
        if ctx.guild is None:
            raise discord.ext.commands.CommandError("This command can only be used in a server.")
        
        nolog_channels = [1299640499493273651, 1329366175796432898, 1329366741909770261, 1329366878623236126,
                          1329367139018215444, 1329367314671472682, 1329367677940006952]
        
        await upload_whole_server(ctx.guild, ctx.author, nolog_channels)
    """
    
    
    @commands.command(name='maintenance_mode',
                      brief='Toggle maintenance mode',
                      help='Dev only: Toggle maintenance mode for the bot',
                      usage='f!maintenance_mode <on/off>')
    async def maintenance_mode(self, ctx: CContext, mode: bool):
        await ctx.delete()
        
        ctx.bot.config.maintenance_mode = mode
        
        status: str = 'enabled' if ctx.bot.config.maintenance_mode else 'disabled'
        await ctx.send(f'Maintenance mode has been {status}.', delete_after=ctx.bot.del_after)
    
    @commands.command(name='reset_cooldowns',
                        brief='Reset command cooldowns',
                        help='Dev only: Reset all command cooldowns for the bot',
                        usage='f!reset_cooldowns')
    async def reset_cooldowns(self, ctx: CContext):
        await ctx.delete()
        
        for command in self.bot.commands:
            command.reset_cooldown(ctx)
        
        await ctx.send('All command cooldowns have been reset.', delete_after=ctx.bot.del_after)
    
    @commands.command(name='run_func',
                      brief='Run a function',
                      help='Dev only: Run a function from the bot',
                      usage='f!run_func <function_name>')
    async def run_func(self, ctx: CContext, func_name: str):
        await ctx.delete()
        if ctx.author.id != 542798185857286144: return
        loop = asyncio.new_event_loop()
        ctx.bot.dev_func_thread = threading.Thread(target=run_func, args=(loop, func_name))
        ctx.bot.dev_func_thread.start()
    
    @commands.command(name='debug_status',
                        brief='Get debug status',
                        help='Dev only: Get debug info about the bot',
                        usage='f!debug_status')
    async def debug_status(self, ctx: CContext):
        internet: str = 'Available' if utils.utils.internet() else 'Not Available'
        ping: str = str(round(ctx.bot.latency * 1000, 1))
        
        process = psutil.Process(os.getpid())
        py_cpu_usage: str = str(round(process.cpu_percent(interval=0.5), 2))
        py_mem_usage: str = str(round(process.memory_info().rss / (1024 * 1024), 2)) + "MiB"
        
        tts_lock: str = 'Locked' if ctx.bot.tts_lock.locked() else 'Unlocked'
        vc_client: str
        assert isinstance(ctx.bot.vc_client, discord.VoiceClient) or ctx.bot.vc_client is None
        if ctx.bot.vc_client is None:
            vc_client = 'No VC client'
        elif ctx.bot.vc_client.is_connected():
            vc_client = f'Connected to {ctx.bot.vc_client.channel.name}'
        else:
            vc_client = 'Exists, not connected'
        
        discord_version = discord.__version__
        
        embed = discord.Embed(title='Debug Status', color=discord.Color.blue())
        embed.add_field(name='Internet', value=internet, inline=True)
        embed.add_field(name='Ping', value=ping, inline=True)
        embed.add_field(name='Python CPU Usage', value=py_cpu_usage, inline=True)
        embed.add_field(name='Python Memory Usage', value=py_mem_usage, inline=True)
        embed.add_field(name='TTS Lock', value=tts_lock, inline=True)
        embed.add_field(name='Voice Client', value=vc_client, inline=True)
        embed.add_field(name='Discord.py Version', value=discord_version, inline=True)
        
        err_log_file = ctx.bot.log_path / 'err.log'
        err_log = err_log_file.read_text()
        if err_log.strip() != '':
            last_5_errs = err_log.split('\n')[-5:]
            embed.add_field(name='Last 5 Errors', value='\n'.join(last_5_errs), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='debug_log',
                      brief='Get the debug log',
                      help='Dev only: Send the debug log to the channel',
                      usage='f!debug_log')
    async def debug_log(self, ctx: CContext):
        await ctx.send(file=discord.File(ctx.bot.log_path / 'debug.log'))
    
    @commands.command(name='err_log',
                      brief='Get the error log',
                      help='Dev only: Send the error log to the channel',
                      usage='f!err_log')
    async def err_log(self, ctx: CContext):
        await ctx.send(file=discord.File(ctx.bot.log_path / 'err.log'))
        

async def setup(bot):
    await bot.add_cog(DevCommands(bot))
