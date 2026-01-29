import asyncio
import logging
import os
import threading

import discord
import psutil
from discord.ext import commands

from cogs import adev_cmds_utils
import utils.utils
from command_utils.CContext import CContext
from command_utils.checks import is_dev

# added the 'a' to the start of the file so it loads first

logger = logging.getLogger('discord')


class DevCommands(commands.Cog, name='Dev', command_attrs=dict(hidden=True, add_check=is_dev)):
    """Developer commands for bot maintenance and management."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='restart',
                      brief='Restart the bot',
                      help='Dev only: restart the bot instance')
    async def restart_cmd(self, ctx: CContext):
        await ctx.delete()
        await adev_cmds_utils.shutdown(ctx.bot, update=False, restart=True)
    
    @commands.command(name='shutdown',
                      brief='Shutdown the bot',
                      help='Dev only: Shutdown the bot instance')
    async def shutdown(self, ctx: CContext):
        await ctx.delete()
        await adev_cmds_utils.shutdown(ctx.bot, update=False, restart=False)
    
    @commands.command(name='update',
                      brief='Update the bot code',
                      help='Dev only: Update the bot code from the repository',
                      usage='f!update')
    async def update(self, ctx: CContext):
        await ctx.delete()
        await adev_cmds_utils.shutdown(ctx.bot, update=True, restart=True)
        
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
        ctx.bot.dev_func_thread = threading.Thread(target=adev_cmds_utils.run_func, args=(loop, func_name, ctx))
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
