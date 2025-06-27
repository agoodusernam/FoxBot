import discord
from discord.ext import commands

from command_utils.checks import is_admin
from currency import curr_utils
from currency.curr_config import currency_name
from utils import utils


class CurrencyCmdsAdmin(commands.Cog, name="Currency Admin",
						command_attrs=dict(add_check=is_admin, hidden=True)):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@commands.command(name="set_wallet", aliases=["set_bal"],
					  brief="Set a user's wallet",
					  help="Set a user's wallet balance",
					  usage="set_wallet<user> <amount>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def set_wallet_cmd(self, ctx: commands.Context, user: discord.Member, amount: int):
		if user is None:
			await ctx.send("Invalid user ID or mention!")
			return

		if amount < 0:
			await ctx.send("You cannot set a negative balance!")
			return

		curr_utils.set_wallet(user, amount)
		await ctx.send(f"Set {user.display_name}'s wallet balance to {amount} {currency_name}!")

	@commands.command(name="set_bank",
					  brief="Set a user's bank balance",
					  help="Set a user's bank balance",
					  usage="set_bank <user> <amount>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def set_bank_cmd(self, ctx: commands.Context, user: discord.Member, amount: int):
		if user is None:
			await ctx.send("Invalid user ID or mention!")
			return

		if amount < 0:
			await ctx.send("You cannot set a negative bank balance!")
			return

		curr_utils.set_bank(user, amount)
		await ctx.send(f"Set {user.display_name}'s bank balance to {amount} {currency_name}!")

	@commands.command(name="set_debt",
					  brief="Set a user's debt",
					  help="Set a user's debt for loans",
					  usage="set_debt <user> <amount>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def set_debt_cmd(self, ctx: commands.Context, user: discord.Member, amount: int):
		if user is None:
			await ctx.send("Invalid user ID or mention!")
			return

		if amount < 0:
			await ctx.send("You cannot set a negative debt!")
			return

		curr_utils.set_debt(user, amount)
		await ctx.send(f"Set {user.display_name}'s debt to {amount} {currency_name}!")

	@commands.command(name="set_income",
					  brief="Set a user's income",
					  help="Set a user's income for working",
					  usage="set_income <user> <amount>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def set_income_cmd(self, ctx: commands.Context, user: discord.Member, amount: int):
		if user is None:
			await ctx.send("Invalid user ID or mention!")
			return

		if amount < 0:
			await ctx.send("You cannot set a negative income!")
			return

		curr_utils.set_income(user, amount)
		await ctx.send(f"Set {user.display_name}'s income to {amount} {currency_name} per work session!")


async def setup(bot: commands.Bot):
	pass
	#await bot.add_cog(CurrencyCmdsAdmin(bot))
