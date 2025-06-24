import discord
from discord.ext import commands

import utils.utils
from currency import curr_utils
from currency.curr_config import currency_name, loan_interest_rate
from command_utils.checks import not_blacklisted

class CurrencyCmds(commands.Cog, name = "Currency", command_attrs=dict(add_check=not_blacklisted)):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@commands.command(name = "balance", aliases = ["bal"],
					  brief = "Check your balance",
					  help = "Check your current money and bank balance")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def balance_cmd(self, ctx: commands.Context):
		profile = curr_utils.get_profile(ctx.author)
		wallet = profile['wallet']
		bank = profile['bank']
		await ctx.send(f"**Balance:**\nWallet: {wallet}\nBank: {bank}\nTotal: {wallet + bank}")

	@commands.command(name = "baltop", aliases = ["balance_top", "bal_top"],
					  brief = "Check the top balances",
					  help = "Check the top users with the highest balances",
					  usage = "baltop")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def baltop_cmd(self, ctx: commands.Context):
		top_users = curr_utils.get_top_balances()
		if not top_users:
			await ctx.send("No users found in the database.")
			return

		top_list = "\n"
		for user, balance in top_users:
			top_list += f"{discord.utils.get(ctx.bot.get_all_members(), id=user).display_name}: {balance} {currency_name}\n"
		await ctx.send(f"**Top Wallet Balances:**\n{top_list}")

	@commands.command(name = "deposit", aliases = ["dep"],
					  brief = "Deposit money into your bank",
					  help = "Deposit some of your money from your wallet into your bank",
					  usage = "deposit <amount>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def deposit_cmd(self, ctx: commands.Context, amount: int):
		if amount <= 0:
			await ctx.send("You must deposit a positive amount!")
			return
		profile = curr_utils.get_profile(ctx.author)
		if profile['wallet'] < amount:
			await ctx.send("You do not have enough money in your wallet!")
			return
		curr_utils.set_wallet(ctx.author, profile['wallet'] - amount)
		curr_utils.set_bank(ctx.author, profile['bank'] + amount)
		await ctx.send(f"Deposited {amount} {currency_name} into your bank!")

	@commands.command(name = "withdraw", aliases = ["with"],
					  brief = "Withdraw money from your bank",
					  help = "Withdraw some of your money from your bank into your wallet",
					  usage = "withdraw <amount>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def withdraw_cmd(self, ctx: commands.Context, amount: int):
		if amount <= 0:
			await ctx.send("You must withdraw a positive amount!")
			return
		profile = curr_utils.get_profile(ctx.author)
		if profile['bank'] < amount:
			await ctx.send("You do not have enough money in your bank!")
			return
		curr_utils.set_wallet(ctx.author, profile['wallet'] + amount)
		curr_utils.set_bank(ctx.author, profile['bank'] - amount)
		await ctx.send(f"Withdrew {amount} {currency_name} from your bank!")

	@commands.command(name = "pay", aliases = ["give"],
					  brief = "Pay another user",
					  help = "Pay another user some of your money",
					  usage = "pay <user> <amount>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def pay_cmd(self, ctx: commands.Context, user: str, amount: int):
		recipient = discord.utils.get(ctx.guild.members, name=utils.utils.get_id_from_str(user))
		if recipient is None or recipient is False:
			await ctx.send("Invalid user ID or mention!")
			return

		if recipient.id == ctx.author:
			await ctx.send("You cannot pay yourself!")
			return
		if amount <= 0:
			await ctx.send("You must pay a positive amount!")
			return
		payer_profile = curr_utils.get_profile(ctx.author)
		if payer_profile['wallet'] < amount:
			await ctx.send("You do not have enough money in your wallet!")
			return

		recipient_profile = curr_utils.get_profile(recipient)
		curr_utils.set_wallet(ctx.author, payer_profile['wallet'] - amount)
		curr_utils.set_wallet(recipient, recipient_profile['wallet'] + amount)
		await ctx.send(f"Paid {recipient.mention} {amount} {currency_name}!")

	@commands.command(name= "work",
					  brief = "Work to earn money",
					  help = "Work to earn some money. You can do this every day.")
	@commands.cooldown(1, 24*60*60, commands.BucketType.user) # 24-hour cooldown
	async def work_cmd(self, ctx: commands.Context):
		profile = curr_utils.get_profile(ctx.author)

		earnings = profile['income']
		debt = profile['debt'] * (1 + loan_interest_rate)
		if earnings <= 0:
			await ctx.send(f"You have no job! Choose a job first using `{ctx.bot.command_prefix}job`.")
			return
		wallet = earnings + profile['wallet']
		curr_utils.set_wallet(ctx.author, wallet)
		curr_utils.set_debt(ctx.author, debt)
		await ctx.send(f"You worked hard and earned {earnings} {currency_name}!")

	@commands.command(name = "debt",
					  brief = "Check your debt",
					  help = "Check how much debt you have")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def debt_cmd(self, ctx: commands.Context):
		profile = curr_utils.get_profile(ctx.author)
		debt = profile['debt']
		if debt <= 0:
			await ctx.send("You have no debt!")
		else:
			await ctx.send(f"You currently owe {debt} {currency_name} in loans.")

	@commands.command(name = "pay_debt", aliases = ["payloan", "pay_load", "repay", "paydebt"],
					  brief = "Pay off your debt",
					  help = "Pay off some of your debt from loans",
					  usage = "pay_debt <amount>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def pay_debt_cmd(self, ctx: commands.Context, amount: int):
		if amount <= 0:
			await ctx.send("You must pay a positive amount!")
			return
		profile = curr_utils.get_profile(ctx.author)
		if profile['debt'] < amount:
			amount = profile['debt']  # If they try to pay more than they owe, pay off the entire debt

		if profile['wallet'] < amount:
			await ctx.send("You do not have enough money in your wallet to pay off that much debt!")
			return
		curr_utils.set_wallet(ctx.author, profile['wallet'] - amount)
		curr_utils.set_debt(ctx.author, profile['debt'] - amount)
		await ctx.send(f"Paid off {amount} {currency_name} of your debt!")

	@commands.command(name = "get_loan", aliases = ["loan"],
					  brief = "Get a loan",
					  help = "Get a loan to increase your wallet balance",
					  usage = "get_loan <amount>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def get_loan_cmd(self, ctx: commands.Context, amount: int):
		if amount <= 0:
			await ctx.send("You must request a positive loan amount!")
			return
		profile = curr_utils.get_profile(ctx.author)
		if profile['debt'] > 0:
			await ctx.send("You already have an outstanding loan! Pay it off first.")
			return

		if profile['bank'] * 5 + 20_000 < amount:
			await ctx.send(f"You can only take a loan up to 5 times your bank balance + 20000.")
			return

		curr_utils.set_wallet(ctx.author, profile['wallet'] + amount)
		curr_utils.set_debt(ctx.author, amount)
		await ctx.send(f"You have taken a loan of {amount} {currency_name}. Remember to pay it back with interest!")

async def setup(bot: commands.Bot) -> None:
	pass
#	await bot.add_cog(CurrencyCmds(bot))
