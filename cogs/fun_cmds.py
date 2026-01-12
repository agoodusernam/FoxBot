import asyncio
import ctypes.util
import logging
import math
import os
import random
import time

import discord
from discord.ext import commands
from discord.ext.commands import guild_only
from discord.ext.tasks import loop
from gtts import gTTS

from command_utils import suggest
from command_utils.CContext import CContext, CoolBot

logger = logging.getLogger('discord')


async def dice_roll(del_after: int, message: discord.Message) -> None:
    str_nums: list[str] = message.content.replace('f!dice', '').replace('f!roll', '').split()
    if len(str_nums) < 2:
        await message.delete()
        await message.channel.send('Please choose 2 numbers to roll the dice, e.g. `dice 1 6`',
                                   delete_after=del_after)
        return
    try:
        nums: list[int] = list(map(int, str_nums))
    except ValueError:
        await message.delete()
        await message.channel.send('Please provide valid numbers for the dice roll, e.g. `dice 1 6`',
                                   delete_after=del_after)
        return
    if nums[0] > nums[1]:
        num: int = random.randint(nums[1], nums[0])
    else:
        num = random.randint(nums[0], nums[1])
    oversize = False
    if math.log10(num) > 1984:
        oversize = True
        str_num = hex(num)
        if len(str_num) > 1984:
            await message.channel.send('The output number would be too large to send in discord')
            return
    
    await message.channel.send(f'You rolled a {num}')
    if oversize:
        await message.channel.send(
                'The number is too large to display in decimal format, so it has been converted to hex.')
    return


class FunCommands(commands.Cog, name='Fun'):
    def __init__(self, bot: CoolBot):
        self.bot: CoolBot = bot
        self.check_tts_leave.start()
        
    @commands.command(name='dice', aliases=['roll', 'dice_roll'],
                      brief='Roll a dice',
                      help='Roll a dice between two values',
                      usage='f!dice <min> <max>')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def dice(self, ctx: CContext):
        await dice_roll(ctx.bot.del_after, ctx.message)
    
    @commands.command(name='flip', aliases=['coin_flip', 'coinflip'],
                      brief='Flip a coin',
                      help='Flip a coin and get either Heads or Tails')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def flip(self, ctx: CContext):
        await ctx.message.channel.send(f'You flipped a coin and got: **{random.choice(['Heads', 'Tails'])}**')
    
    @commands.command(name='ping', aliases=['latency'],
                      brief="Check the bot's latency",
                      help="Shows the bot's current latency in milliseconds")
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def ping(self, ctx: CContext):
        await ctx.message.channel.send(f'{ctx.bot.latency * 1000:.1f}ms')  # type: ignore
    
    @commands.command(name='suggest', aliases=['suggestion'],
                      brief='Submit a suggestion',
                      help='Submit a suggestion for the bot',
                      usage='f!suggest <suggestion>')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def suggest_cmd(self, ctx: CContext, *, args: str):
        await suggest.send_suggestion(ctx, args)
        
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
        total_lines = 0
        total_files = 0
        
        for root, dirs, files in os.walk(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')):
            # Skip .venv directory
            if '.venv' in dirs:
                dirs.remove('.venv')
            
            # Count lines in .py files
            for file in files:
                if not file.endswith('.py'):
                    continue
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        line_count = sum(1 for _ in f)
                    total_lines += line_count
                    total_files += 1
                    print(f'{file_path}: {line_count} lines')
                except Exception as e:
                    print(f'Error reading {file_path}: {e}')
        
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
            await ctx.send('Could not find opus library. TTS command is unavailable.')
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
    
    
    @discord.ext.tasks.loop(minutes=1.0)
    async def check_tts_leave(self) -> None:
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
        

async def setup(bot: CoolBot) -> None:
    await bot.add_cog(FunCommands(bot))
