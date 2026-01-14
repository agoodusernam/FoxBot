import string
from typing import TypeVar

import discord
from discord.ext import commands

from command_utils.CContext import CContext, CoolBot
from cogs.counting_utils import *

T = TypeVar('T')

def sort_dict_by_value_h2l(d: dict[T, int]) -> dict[T, int]:
    return {k: v for k, v in sorted(d.items(), key=lambda item: item[1], reverse=True)}

class Counting(commands.Cog, name='Counting'):
    def __init__(self, bot: CoolBot):
        self.bot: CoolBot = bot
    
    @commands.command(name='counting_fails_lb', aliases=['cflb'],
            help='View the leaderboard for failed counting attempts',
            usage='f!counting_fails_lb [number_of_entries]')
    @commands.cooldown(1, 2, commands.BucketType.user)  # type: ignore
    async def count_fails_lb(self, ctx: CContext, number_of_entries: int = 10):
        lb = ctx.bot.config.counting_fails
        if len(lb) == 0:
            await ctx.send('No users have failed counting yet.')
            return
        
        sorted_lb = sort_dict_by_value_h2l(lb)
        embed = discord.Embed(title='Counting Fails Leaderboard', color=discord.Color.blue())
        description = ''
        for i in range(number_of_entries):
            if i >= len(sorted_lb):
                break
            user_id, count = list(sorted_lb.items())[i]
            user = await ctx.bot.fetch_user(user_id)
            description += f'{i + 1}. {user.display_name} - {count}\n'
        
        embed.description = description
        await ctx.send(embed=embed)
    
    @commands.command(name='count_fails', aliases=['cf'],
            help='View the number of failed counting attempts for a user',
            usage='f!count_fails <user>')
    @commands.cooldown(1, 2, commands.BucketType.user)  # type: ignore
    async def count_fails(self, ctx: CContext, member: discord.Member | discord.User):
        fails: int | None = ctx.bot.config.counting_fails.get(member.id, None)
        if fails is None:
            await ctx.send(f'{member.display_name} has not failed counting yet.')
            return
        await ctx.send(f'{member.display_name} has failed counting {fails} times.')
    
    @commands.command(name='count_leaderboard', aliases=['clb'],
            help='View the top 5 leaderboard for the most successful counting attempts, and highest number counted',
            usage='f!count_leaderboard')
    @commands.cooldown(1, 2, commands.BucketType.user)  # type: ignore
    async def count_leaderboard(self, ctx: CContext):
        if len(ctx.bot.config.counting_successes) == 0:
            await ctx.send('No users have counted yet.')
            return
        
        if len(ctx.bot.config.highest_user_count) == 0:
            await ctx.send('No users have counted yet.')
            return
        
        lb_success: dict[int, int] = sort_dict_by_value_h2l(ctx.bot.config.counting_successes)
        lb_user_number: dict[int, int] = sort_dict_by_value_h2l(ctx.bot.config.highest_user_count)
        
        num_successes_embed = discord.Embed(title='Most Successful Counting Attempts Leaderboard', color=discord.Color.blue())
        for i in range(5):
            if i >= len(lb_success):
                break
            user_id, count = list(lb_success.items())[i]
            user = await ctx.bot.fetch_user(user_id)
            num_successes_embed.add_field(name=f'{i + 1}. {user.display_name}', value=count, inline=False)
        
        num_user_embed = discord.Embed(title='Highest Number Counted Leaderboard', color=discord.Color.blue())
        for i in range(5):
            if i >= len(lb_user_number):
                break
            user_id, count = list(lb_user_number.items())[i]
            user = await ctx.bot.fetch_user(user_id)
            num_user_embed.add_field(name=f'{i + 1}. {user.display_name}', value=count, inline=False)
        
        await ctx.send(embed=num_successes_embed)
        await ctx.send(embed=num_user_embed)
    
    @commands.command(name='calculate', aliases=['calc'],
                      help='Calculate a mathematical expression',
                      usage='f!calculate <expression>')
    @commands.cooldown(1, 1, commands.BucketType.user)  # type: ignore
    async def calculate(self, ctx: CContext, *, expression: str) -> None:
        s = expression.lower()
        for char in string.whitespace:
            s = s.replace(char, "")
        
        if s.startswith('<') and s.endswith('>'):
            await ctx.send('You do not need to surround the expression with <> when using this command.')
        
        if s.startswith('<'):
            s = s[1:]
        
        if s.endswith('>'):
            s = s[:-1]
            
        
        if not count_only_allowed_chars(s):
            await ctx.safe_reply('The expression contains invalid characters.')
            return
        
        result, status = eval_count_msg(s)
        
        if status == CountStatus.TIMEOUT:
            await ctx.safe_reply("Expression took too long to evaluate.")
            return
        
        if status == CountStatus.INVALID:
            await ctx.safe_reply("Expression is invalid.")
            return
        
        if status == CountStatus.OVERFLOW:
            await ctx.safe_reply("Expression resulted in an under or overflow.")
            return
        
        if status == CountStatus.ZERO_DIV:
            await ctx.safe_reply("Expression resulted in a division by zero.")
            return
        
        if status == CountStatus.DECIMAL_ERR:
            await ctx.safe_reply("Expression resulted in a decimal error, likely due to insufficient precision. Try using smaller numbers.")
            return
        
        await ctx.safe_reply(f"Result: {round(result)}")
        

async def setup(bot: CoolBot) -> None:
    await bot.add_cog(Counting(bot))