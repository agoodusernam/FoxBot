import asyncio
import math
import os
import random

import discord
from discord.ext import commands

from command_utils import suggest


async def dice_roll(del_after: int, message: discord.Message) -> None:
    nums: list[int | str] = message.content.replace('f!dice', '').replace('f!roll', '').split()
    if len(nums) < 2:
        await message.delete()
        await message.channel.send('Please choose 2 numbers to roll the dice, e.g. `dice 1 6`',
                                   delete_after=del_after)
        return
    try:
        nums = list(map(int, nums))
    except ValueError:
        await message.delete()
        await message.channel.send('Please provide valid numbers for the dice roll, e.g. `dice 1 6`',
                                   delete_after=del_after)
        return
    if nums[0] > nums[1]:
        num: int | str = random.randint(nums[1], nums[0])
    else:
        num = random.randint(nums[0], nums[1])
    oversize = False
    if math.log10(num) > 1984:
        oversize = True
        num = hex(num)
        if len(num) > 1984:
            await message.channel.send('The output number would be too large to send in discord')
            return
    
    await message.channel.send(f'You rolled a {num}')
    if oversize:
        await message.channel.send(
                'The number is too large to display in decimal format, so it has been converted to hex.')
    return


class FunCommands(commands.Cog, name='Fun'):
    @commands.command(name='dice', aliases=['roll', 'dice_roll'],
                      brief='Roll a dice',
                      help='Roll a dice between two values',
                      usage='dice <min> <max>')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def dice(self, ctx: discord.ext.commands.Context):
        await dice_roll(ctx.bot.del_after, ctx.message)
    
    @commands.command(name='flip', aliases=['coin_flip', 'coinflip'],
                      brief='Flip a coin',
                      help='Flip a coin and get either Heads or Tails')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def flip(self, ctx: discord.ext.commands.Context):
        await ctx.message.channel.send(f'You flipped a coin and got: **{random.choice(['Heads', 'Tails'])}**')
    
    @commands.command(name='ping', aliases=['latency'],
                      brief='Check the bot\'s latency',
                      help='Shows the bot\'s current latency in milliseconds')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def ping(self, ctx: discord.ext.commands.Context):
        await ctx.message.channel.send(f'{ctx.bot.latency * 1000:.1f}ms')  # type: ignore
    
    @commands.command(name='suggest', aliases=['suggestion'],
                      brief='Submit a suggestion',
                      help='Submit a suggestion for the bot',
                      usage='suggest <suggestion>')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def suggest_cmd(self, ctx: discord.ext.commands.Context, *, args: str):
        await suggest.send_suggestion(ctx, args)
        
    @commands.command(name='8ball', aliases=['eight_ball', 'magic_8_ball'],
                        brief='Ask the magic 8-ball a question',
                        help='Ask the magic 8-ball a question and get a random answer')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def eight_ball(self, ctx: discord.ext.commands.Context):
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
        await ctx.reply(f'{answer}')
        
    @commands.command(name='owoify', aliases=['owo', 'uwu'],
                        brief='Convert text to OwO language',
                        help='Converts the given text to OwO language (UwU style)',
                        usage='owoify <text>')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def owoify(self, ctx: discord.ext.commands.Context, *, text: str):
        # Simple conversion to OwO language
        owo_text = text.replace('r', 'w').replace('l', 'w').replace('v', 'w')
        owo_text = owo_text.replace('th', 'd').replace('Th', 'D').replace('TH', 'D')
        if owo_text.endswith('!'):
            owo_text = owo_text + ' OwO'
        await ctx.send(owo_text)
    
    @commands.command(name='code', aliases=['source', 'github'],
                      brief="Get the bot's source code",
                      help="Get the link to the bot's source code on GitHub")
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def code(self, ctx: discord.ext.commands.Context):
        await ctx.message.channel.send(
                'You can find the source code for this bot on GitHub: https://github.com/agoodusernam/FoxBot'
        )
    
    @commands.command(name='lines_of_code', aliases=['lines', 'loc'],
                      brief='Get the number of lines of code in the bot',
                      help="Get the number of lines of code in the bot's source code")
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def lines_of_code(self, ctx: discord.ext.commands.Context):
        # function that returns the number of lines of code in a given directory recursively, excluding .venv
        total_lines = 0
        
        for root, dirs, files in os.walk('/root/pyVenv/'):
            # Skip .venv directory
            if 'discBot' in dirs:
                dirs.remove('discBot')
            
            # Count lines in .py files
            for file in files:
                if not file.endswith('.py'):
                    continue
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        line_count = sum(1 for _ in f)
                    total_lines += line_count
                    print(f'{file_path}: {line_count} lines')
                except Exception as e:
                    print(f'Error reading {file_path}: {e}')
        
        await ctx.send(f'There are {total_lines} lines of code in the bot')


async def setup(bot) -> None:
    await bot.add_cog(FunCommands(bot))
