import discord
from discord.ext import commands

import utils.utils
from currency import curr_utils
from command_utils.checks import is_admin, not_blacklisted

class CurrencyCmds(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@commands.command(name = "balance", aliases = ["bal"],
					  brief = "Check your balance",
					  help = "Check your current money and bank balance")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.check(not_blacklisted)
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
	@commands.check(not_blacklisted)
	async def baltop_cmd(self, ctx: commands.Context):
		top_users = curr_utils.get_top_balances()
		if not top_users:
			await ctx.send("No users found in the database.")
			return

		top_list = "\n"
		for user, balance in top_users:
			top_list += f"{discord.utils.get(ctx.bot.get_all_members(), id=user).display_name}: {balance} FoxCoins\n"
		await ctx.send(f"**Top Wallet Balances:**\n{top_list}")

	@commands.command(name = "deposit", aliases = ["dep"],
					  brief = "Deposit money into your bank",
					  help = "Deposit some of your money from your wallet into your bank",
					  usage = "deposit <amount>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.check(not_blacklisted)
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
		await ctx.send(f"Deposited {amount} FoxCoins into your bank!")

	@commands.command(name = "withdraw", aliases = ["with"],
					  brief = "Withdraw money from your bank",
					  help = "Withdraw some of your money from your bank into your wallet",
					  usage = "withdraw <amount>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.check(not_blacklisted)
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
		await ctx.send(f"Withdrew {amount} FoxCoins from your bank!")

	@commands.command(name = "pay", aliases = ["give"],
					  brief = "Pay another user",
					  help = "Pay another user some of your money",
					  usage = "pay <user> <amount>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.check(not_blacklisted)
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
		await ctx.send(f"Paid {recipient.mention} {amount} FoxCoins!")

	@commands.command(name = "set_balance", aliases = ["set_bal"],
					  brief = "Set a user's balance",
					  help = "Set a user's wallet balance",
					  usage = "set_balance <user> <amount>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.check(is_admin)
	async def set_balance_cmd(self, ctx: commands.Context, user: str, amount: int):
		target_user = discord.utils.get(ctx.guild.members, name=utils.utils.get_id_from_str(user))
		if target_user is None or target_user is False:
			await ctx.send("Invalid user ID or mention!")
			return

		if amount < 0:
			await ctx.send("You cannot set a negative balance!")
			return

		curr_utils.set_wallet(target_user, amount)
		await ctx.send(f"Set {target_user.display_name}'s wallet balance to {amount} FoxCoins!")

	@commands.command(name = "set_bank",
					  brief = "Set a user's bank balance",
					  help = "Set a user's bank balance",
					  usage = "set_bank <user> <amount>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.check(is_admin)
	async def set_bank_cmd(self, ctx: commands.Context, user: str, amount: int):
		target_user = discord.utils.get(ctx.guild.members, name=utils.utils.get_id_from_str(user))
		if target_user is None or target_user is False:
			await ctx.send("Invalid user ID or mention!")
			return

		if amount < 0:
			await ctx.send("You cannot set a negative bank balance!")
			return

		curr_utils.set_bank(target_user, amount)
		await ctx.send(f"Set {target_user.display_name}'s bank balance to {amount} FoxCoins!")


async def setup(bot: commands.Bot) -> None:
	await bot.add_cog(CurrencyCmds(bot))
