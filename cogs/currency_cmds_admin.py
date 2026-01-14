import discord
from discord.ext import commands

from command_utils.CContext import CContext
from command_utils.checks import is_dev
from currency import curr_utils
from currency.curr_config import currency_name


class CurrencyCmdsAdmin(commands.Cog, name="Currency Admin",
                        command_attrs=dict(add_check=is_dev, hidden=True)):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="set_wallet", aliases=["set_bal"],
                      brief="Set a user's wallet",
                      help="Set a user's wallet balance",
                      usage="f!set_wallet<user> <amount>")
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def set_wallet_cmd(self, ctx: CContext, user: discord.Member, amount: int):
        if user is None:
            await ctx.send("Invalid user ID or mention!")
            return
        
        if amount < 0:
            await ctx.send("You cannot set a negative balance!")
            return
        
        await curr_utils.set_wallet(user, amount)
        await ctx.send(f"Set {user.display_name}'s wallet balance to {amount} {currency_name}!")
    
    @commands.command(name="set_bank",
                      brief="Set a user's bank balance",
                      help="Set a user's bank balance",
                      usage="f!set_bank <user> <amount>")
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def set_bank_cmd(self, ctx: CContext, user: discord.Member, amount: int):
        if user is None:
            await ctx.send("Invalid user ID or mention!")
            return
        
        if amount < 0:
            await ctx.send("You cannot set a negative bank balance!")
            return
        
        await curr_utils.set_bank(user, amount)
        await ctx.send(f"Set {user.display_name}'s bank balance to {amount} {currency_name}!")
    
    @commands.command(name="set_debt",
                      brief="Set a user's debt",
                      help="Set a user's debt for loans",
                      usage="f!set_debt <user> <amount>")
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def set_debt_cmd(self, ctx: CContext, user: discord.Member, amount: int):
        if user is None:
            await ctx.send("Invalid user ID or mention!")
            return
        
        if amount < 0:
            await ctx.send("You cannot set a negative debt!")
            return
        
        await curr_utils.set_debt(user, amount)
        await ctx.send(f"Set {user.display_name}'s debt to {amount} {currency_name}!")
    
    @commands.command(name="set_income",
                      brief="Set a user's income",
                      help="Set a user's income for working",
                      usage="f!set_income <user> <amount>")
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def set_income_cmd(self, ctx: CContext, user: discord.Member, amount: int):
        if user is None:
            await ctx.send("Invalid user ID or mention!")
            return
        
        if amount < 0:
            await ctx.send("You cannot set a negative income!")
            return
        
        await curr_utils.set_income(user, amount)
        await ctx.send(f"Set {user.display_name}'s income to {amount} {currency_name} per work session!")
    
    @commands.command(name="set_stock",
                      brief="Set the stock of a shop item",
                      help="Set the stock of a specific shop item",
                      usage="f!set_stock <item_name> <amount>")
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def set_stock_cmd(self, ctx: CContext, item_name: str, amount: int):
        item = await curr_utils.get_shop_item(item_name)
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
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def reset_profile_cmd(self, ctx: CContext, user: discord.Member):
        if user is None:
            await ctx.send("Invalid user ID or mention!")
            return
        
        await curr_utils.delete_profile(user)
        await curr_utils.create_new_profile(user)
        await ctx.send(f"Reset {user.display_name}'s currency profile to default values!")
        
    @commands.command(name="reset_job",
                        brief="Reset a user's job profile",
                        help="Reset a user's job profile to default values",
                        usage="f!reset_job <user>")
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def reset_job_cmd(self, ctx: CContext, user: discord.Member):
        if user is None:
            await ctx.send("Invalid user ID or mention!")
            return
        
        await curr_utils.reset_job(user)
        await ctx.send(f"Reset {user.display_name}'s job profile to default values!")


async def setup(bot: commands.Bot):
    pass
    # await bot.add_cog(CurrencyCmdsAdmin(bot))
