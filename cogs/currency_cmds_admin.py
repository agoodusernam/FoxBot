import discord
from decimal import Decimal
from discord.ext import commands

from command_utils.CContext import CContext
from command_utils.checks import is_dev
from currency import collector, curr_utils
from currency.curr_config import CURRENCY_NAME
from currency.currency_types import Profile


async def get_profile(user: discord.Member) -> Profile:
    return await Profile.fetch_from_user_id(user.id)


class CurrencyCmdsAdmin(commands.Cog, name="Currency Admin",
                        command_attrs=dict(add_check=is_dev, hidden=True)):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="set_wallet", aliases=["set_bal"],
                      brief="Set a user's wallet",
                      help="Set a user's wallet balance",
                      usage="f!set_wallet<user> <amount>")
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def set_wallet_cmd(self, ctx: CContext, user: discord.Member, amount: int):
        if user is None:
            await ctx.send("Invalid user ID or mention!")
            return
        
        if amount < 0:
            await ctx.send("You cannot set a negative balance!")
            return
        
        profile = await get_profile(user)
        profile.wallet = Decimal(amount)
        await ctx.send(f"Set {user.display_name}'s wallet balance to {amount} {CURRENCY_NAME}!")
    
    @commands.command(name="set_bank",
                      brief="Set a user's bank balance",
                      help="Set a user's bank balance",
                      usage="f!set_bank <user> <amount>")
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def set_bank_cmd(self, ctx: CContext, user: discord.Member, amount: int):
        if user is None:
            await ctx.send("Invalid user ID or mention!")
            return
        
        if amount < 0:
            await ctx.send("You cannot set a negative bank balance!")
            return
        
        profile = await get_profile(user)
        profile.bank = Decimal(amount)
        await ctx.send(f"Set {user.display_name}'s bank balance to {amount} {CURRENCY_NAME}!")
    
    @commands.command(name="set_debt",
                      brief="Set a user's debt",
                      help="Set a user's debt for loans",
                      usage="f!set_debt <user> <amount>")
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def set_debt_cmd(self, ctx: CContext, user: discord.Member, amount: int):
        if user is None:
            await ctx.send("Invalid user ID or mention!")
            return
        
        if amount < 0:
            await ctx.send("You cannot set a negative debt!")
            return
        
        profile = await get_profile(user)
        profile.debt = Decimal(amount)
        await ctx.send(f"Set {user.display_name}'s debt to {amount} {CURRENCY_NAME}!")
    
    @commands.command(name="set_income",
                      brief="Set a user's income",
                      help="Set a user's income for working",
                      usage="f!set_income <user> <amount>")
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def set_income_cmd(self, ctx: CContext, user: discord.Member, amount: int):
        if user is None:
            await ctx.send("Invalid user ID or mention!")
            return
        
        if amount < 0:
            await ctx.send("You cannot set a negative income!")
            return
        
        profile = await get_profile(user)
        profile.work_income = Decimal(amount)
        await ctx.send(f"Set {user.display_name}'s income to {amount} {CURRENCY_NAME} per year!")
    
    @commands.command(name="set_stock",
                      brief="Set the stock of a shop item",
                      help="Set the stock of a specific shop item",
                      usage="f!set_stock <item_name> <amount>")
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def set_stock_cmd(self, ctx: CContext, item_name: str, amount: int):
        item = collector.item_from_str(item_name)
        if item is None:
            await ctx.send(f"Item '{item_name}' not found in the shop!")
            return
        
        if amount < 0:
            await ctx.send("You cannot set a negative stock!")
            return
        
        await curr_utils.set_stock(item, amount)
        await ctx.send(f"Set stock for {item.name} to {amount} units!")
    
    @commands.command(name="reset_profile",
                      brief="Reset a user's currency profile",
                      help="Reset a user's currency profile to default values",
                      usage="f!reset_profile <user>")
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def reset_profile_cmd(self, ctx: CContext, user: discord.Member):
        if user is None:
            await ctx.send("Invalid user ID or mention!")
            return
        
        profile = await get_profile(user)
        await profile.reset_db_entry()
        await ctx.send(f"Reset {user.display_name}'s currency profile to default values!")
        
    @commands.command(name="reset_job",
                        brief="Reset a user's job profile",
                        help="Reset a user's job profile to default values",
                        usage="f!reset_job <user>")
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def reset_job_cmd(self, ctx: CContext, user: discord.Member):
        if user is None:
            await ctx.send("Invalid user ID or mention!")
            return
        
        profile = await get_profile(user)
        profile.reset_job()
        await ctx.send(f"Reset {user.display_name}'s job profile to default values!")


async def setup(bot: commands.Bot):
    pass
    # await bot.add_cog(CurrencyCmdsAdmin(bot))
