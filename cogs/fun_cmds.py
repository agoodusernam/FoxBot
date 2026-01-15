import asyncio
import ctypes.util
import datetime
import logging
import os
import random
import time
from typing import Any

import discord
from discord.ext import commands
from discord.ext.commands import guild_only
from discord.ext.tasks import loop
from gtts import gTTS  # type: ignore[import-untyped]

import cogs.fun_cmds_utils as fun_cmds_utils
import command_utils.analysis
from command_utils.analysis import try_resolve_uid
import utils.utils
from command_utils.CContext import CContext, CoolBot

logger = logging.getLogger('discord')

monday_gen = fun_cmds_utils.monday_generator()
current_monday = next(monday_gen)


class FunCommands(commands.Cog, name='Fun'):
    def __init__(self, bot: CoolBot):
        self.bot: CoolBot = bot
        self.check_tts_leave.start()
        self.send_vc_lb.start()
        self.add_ping.start()
        
    @commands.command(name='dice', aliases=['roll', 'dice_roll'],
                      brief='Roll a dice',
                      help='Roll a dice between two values',
                      usage='f!dice <min> <max>')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def dice(self, ctx: CContext):
        await fun_cmds_utils.dice_roll(ctx.message)
    
    @commands.command(name='flip', aliases=['coin_flip', 'coinflip'],
                      brief='Flip a coin',
                      help='Flip a coin and get either Heads or Tails')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def flip(self, ctx: CContext):
        await ctx.send(f'You flipped a coin and got: **{random.choice(['Heads', 'Tails'])}**')
    
    @commands.command(name='ping', aliases=['latency'],
                      brief="Check the bot's latency",
                      help="Shows the bot's current latency in milliseconds")
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def ping(self, ctx: CContext):
        await ctx.send(f'{ctx.bot.latency * 1000:.1f}ms')  # type: ignore
    
    @commands.command(name='suggest', aliases=['suggestion'],
                      brief='Submit a suggestion',
                      help='Submit a suggestion for the bot',
                      usage='f!suggest <suggestion>')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def suggest_cmd(self, ctx: CContext, *, suggestion: str):
        """
        Sends a suggestion to the designated channel and creates a thread for discussion.
        """
        HELP_MSG = '''Please post your suggestions for the server or <@1377636535968600135> in here using `f!suggest <suggestion>`.
        If you have any additional comments, please use the thread.
        ✅: Implemented
        💻: Working on it
        ❌: Will not add

        👍: Vote for suggestion
        '''
        
        await ctx.delete()
        
        channel: Any = ctx.bot.get_channel(1379193761791213618)
        if not isinstance(channel, discord.TextChannel):
            logger.error('Channel not found for sending suggestion.')
            return
        
        last_msgs = [message async for message in channel.history(limit=3)]
        for message in last_msgs:
            if message.content.startswith(HELP_MSG[:20]):
                await message.delete()
        
        try:
            embed = discord.Embed(title='Suggestion', description=suggestion, color=discord.Color.blue())
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            msg = await channel.send(embed=embed)
            await msg.add_reaction('👍')
            
            await msg.create_thread(name=f'suggestion-{ctx.author.display_name}')
            
            await channel.send(HELP_MSG)
            logger.info(f'Suggestion sent: {suggestion}')
        
        except discord.Forbidden as exc:
            raise discord.ext.commands.BotMissingPermissions(["manage_channels", "manage_threads", "create_public_threads"]) from exc
        
        except discord.NotFound:
            logger.error('Channel not found for sending suggestion.')
        
        except discord.HTTPException as e:
            logger.error(f'Failed to send suggestion: {e}')
        
    @commands.command(name='8ball', aliases=['eight_ball', 'magic_8_ball'],
                        brief='Ask the magic 8-ball a question',
                        help='Ask the magic 8-ball a question and get a random answer')
    @commands.cooldown(1, 3, commands.BucketType.user)  # type: ignore
    async def eight_ball(self, ctx: CContext):
        pos_responses = [ # 10 positive responses
            'It is certain', 'It is decidedly so', 'Without a doubt', 'Yes definitely',
            'You may rely on it', 'As I see it, yes', 'Most likely', 'Outlook good',
            'Yes', 'Signs point to yes'
        ]
        neut_responses = [ # 4 neutral responses
            'Reply hazy try again', 'Better not tell you now', 'I see no clear answer',
            "I shouldn't answer that"
        ]
        neg_responses = [ # 10 negative responses
            "Don't count on it", 'Certainly not', 'My sources say unlikely',
            'Outlook not so good', 'Very doubtful', 'No', 'Definitely not',
            'You should not count on it', 'I would not rely on it', 'In my opinion, no'
        ]
        responses = pos_responses + neut_responses + neg_responses
        answer = random.choice(responses)
        logger.debug(f'Magic 8-ball answer: {answer}')
        await ctx.typing()
        await asyncio.sleep(2)  # Simulate thinking time
        await ctx.safe_reply(f'{answer}')
        
    @commands.command(name='owoify', aliases=['owo', 'uwu'],
                        brief='Convert text to OwO language',
                        help='Converts the given text to OwO language (UwU style)',
                        usage='f!owo <text>')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def owoify(self, ctx: CContext, *, text: str):
        # Simple conversion to OwO language
        # Why did I add this. I hate myself
        owo_text = text.replace('r', 'w').replace('l', 'w').replace('v', 'w')
        owo_text = owo_text.replace('th', 'd').replace('Th', 'D').replace('TH', 'D')
        if owo_text.endswith('!'):
            owo_text = owo_text + ' OwO'
        await ctx.send(owo_text)
    
    @commands.command(name='code', aliases=['source', 'github'],
                      brief="Get the bot's source code",
                      help="Get the link to the bot's source code on GitHub")
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def code(self, ctx: CContext):
        await ctx.send('You can find the source code for this bot on GitHub: https://github.com/agoodusernam/FoxBot')
    
    @commands.command(name='lines_of_code', aliases=['lines', 'loc'],
                      brief='Get the number of lines of code in the bot',
                      help="Get the number of lines of code in the bot's source code",
                      usage='f!loc')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def lines_of_code(self, ctx: CContext):
        # function that returns the number of lines of code in a given directory recursively, excluding .venv
        total_lines, total_files = utils.utils.loc_total()
        
        await ctx.send(f'There are {total_lines} lines of code across {total_files} Python files in this bot\'s source code.')
        
    
    @commands.command(name='tts',
                      brief='Send a text-to-speech message',
                      help='Send a text-to-speech message in the current channel',
                      usage='f!tts <message>')
    @commands.cooldown(1, 1, commands.BucketType.guild) # type: ignore
    @guild_only()
    @commands.has_role(1405824995946532995) # TODO: Make configurable
    async def tts(self, ctx: CContext, *, message: str):
        if isinstance(ctx.author, discord.User):
            return
        
        if message.strip() == '':
            await ctx.send('Please provide a message to convert to speech.')
            return
        
        opus = ctypes.util.find_library('opus')
        if opus is None:
            await ctx.send('TTS command is unavailable.')
            logger.error('Could not find opus library.')
            return
        
        state = ctx.author.voice
        if state is None or state.channel is None:
            await ctx.send('You must be in a voice channel to use this command.')
            return
        
        lock: asyncio.Lock = ctx.bot.tts_lock
        
        vc_client: discord.VoiceClient
        ctx.bot.last_tts_sent_time = time.time()
        await lock.acquire()
        gTTS(text=message).save('msg.mp3')
        def done(error: Exception | None) -> None:
            lock.release()
            if os.path.exists('msg.mp3'):
                os.remove('msg.mp3')
                
            if error:
                logger.error(f'TTS playback error: {error}')
            
        
        discord.opus.load_opus(opus)
        if ctx.bot.vc_client is not None:
            if not ctx.bot.vc_client.channel.id == state.channel.id:
                await ctx.bot.vc_client.move_to(state.channel)
            vc_client = ctx.bot.vc_client
        else:
            vc_client = await state.channel.connect(timeout=15.0, reconnect=False)
            ctx.bot.vc_client = vc_client
        
        audio = discord.FFmpegPCMAudio(source='msg.mp3')
        vc_client.play(audio, after=done)
    
    @commands.command(name='tts_leave', aliases=['tts_disconnect', "ttsl"],
                        brief='Disconnect the bot from voice channel',
                        help='Disconnect the bot from the voice channel it is currently in',
                        usage='f!tts_leave')
    @commands.cooldown(1, 1, commands.BucketType.guild)  # type: ignore
    @guild_only()
    async def tts_leave(self, ctx: CContext):
        if ctx.bot.vc_client is None:
            await ctx.send('The bot is not connected to a voice channel.')
            if hasattr(ctx.bot, 'last_tts_sent_time'):
                del ctx.bot.last_tts_sent_time
            return
        
        if ctx.bot.vc_client.is_connected():
            await ctx.bot.vc_client.disconnect()
        
        ctx.bot.vc_client = None
        
        if hasattr(ctx.bot, "last_sent_tts_time"):
            del ctx.bot.last_sent_tts_time
    
    
    @commands.command(name='stats',
                      brief="Get bot statistics",
                      help="Get statistics about the bot")
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def stats(self, ctx: CContext):
        loc = utils.utils.loc_total()[0]
        files = utils.utils.loc_total()[1]
        uptime = utils.utils.seconds_to_human_readable(time.time() - ctx.bot.start_time)
        ping = f"{self.bot.latency * 1000:.1f}"
        
        embed = discord.Embed(title='Bot Statistics', colour=discord.Colour.purple())
        embed.add_field(name='Lines of Code', value=loc, inline=True)
        embed.add_field(name='Files', value=files, inline=True)
        embed.add_field(name='Uptime', value=uptime, inline=True)
        embed.add_field(name='Ping', value=ping + 'ms', inline=True)
        embed.add_field(name='Avg Ping', value=f"{self.bot.avg_latency:.1f} ms", inline=True)
        commit = await fun_cmds_utils.cached_get_last_commit()
        
        if commit is None:
            await ctx.send(embed=embed)
            return
        
        commit_time, commit_message, changes = commit
        
        embed.add_field(name='Last Commit at', value=f'<t:{commit_time}>', inline=False)
        embed.add_field(name='Commit Message', value=commit_message, inline=False)
        embed.add_field(name='Total lines changed', value=changes['total'], inline=False)
        await ctx.send(embed=embed)
    
    @discord.ext.tasks.loop(seconds=59)
    async def check_tts_leave(self) -> None:
        logger.debug('Checking for TTS disconnect')
        if self.bot.vc_client is None and not hasattr(self.bot, 'last_tts_sent_time'):
            return
        
        if self.bot.vc_client is None and hasattr(self.bot, 'last_tts_sent_time'):
            del self.bot.last_tts_sent_time
            return
        
        if self.bot.vc_client is not None and not hasattr(self.bot, 'last_tts_sent_time'):
            if self.bot.vc_client.is_connected():
                await self.bot.vc_client.disconnect()
            self.bot.vc_client = None
            return
        
        assert self.bot.vc_client is not None
        assert hasattr(self.bot, 'last_tts_sent_time')
        assert isinstance(self.bot.last_tts_sent_time, float)
        
        if not self.bot.vc_client.is_connected():
            self.bot.vc_client = None
            del self.bot.last_tts_sent_time
            return
        
        if time.time() - self.bot.last_tts_sent_time > 180.0:
            await self.bot.vc_client.disconnect()
            self.bot.vc_client = None
            del self.bot.last_tts_sent_time
        
        return
    
    @discord.ext.tasks.loop(seconds=59)
    async def send_vc_lb(self) -> None:
        global current_monday
        now: datetime.datetime = datetime.datetime.now(datetime.UTC)
        if now < current_monday:
            return
        
        current_monday = next(monday_gen)
        channel = self.bot.get_channel(self.bot.config.vc_lb_channel_id)
        if not hasattr(channel, 'send') or channel is None:
            logger.error('VC leaderboard channel not found.')
            return
        
        lb = await command_utils.analysis.voice_activity_this_week()
        msg: str = 'Time spent in VCs leaderboard for last week:\n'
        for i, stat in enumerate(lb):
            formatted_time = utils.utils.seconds_to_human_readable(stat["total_seconds"])
            msg += f'{i + 1}. <@{stat["user_id"]}>: {formatted_time}\n'
        
        await channel.send(msg)
        await command_utils.analysis.generate_voice_activity_graph(channel, self.bot, lb, 5, send_errors=False) # type: ignore
    
    @discord.ext.tasks.loop(minutes=1)
    async def add_ping(self):
        self.bot.add_ping()
    
    @add_ping.before_loop
    async def before_add_ping(self):
        await self.bot.wait_until_ready()

async def setup(bot: CoolBot) -> None:
    await bot.add_cog(FunCommands(bot))
