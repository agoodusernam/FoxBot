import secrets

import discord
from discord.ext import commands

import utils
from command_utils import checks
from currency import curr_utils
import command_utils.gambling_utils as gambling_utils
from currency import gambling_config

class GamblingCmds(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@commands.command(name="slot", aliases=["slots"],
					  brief="Play a slot machine game",
					  help="Try your luck with the slot machine! You can win or lose coins.",
					  usage="slot <bet_amount>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.check(checks.not_blacklisted)
	async def slot_cmd(self, ctx: commands.Context, bet_amount: int):
		if bet_amount <= 0:
			await ctx.send("You must bet a positive amount!")
			return
		if bet_amount < gambling_config.slots_min_bet:
			await ctx.send(f"The minimum bet is {gambling_config.slots_min_bet} coins!")
			return
		profile = curr_utils.get_profile(ctx.author)
		if profile['wallet'] < bet_amount:
			await ctx.send("You do not have enough money in your wallet!")
			return
		curr_utils.set_wallet(ctx.author, profile['wallet'] - bet_amount)

		payout = gambling_utils.slots_select_payout(gambling_config.slots_payouts, gambling_config.slots_probabilities)
		payout *= bet_amount
		if payout > 0:
			curr_utils.set_wallet(ctx.author, profile['wallet'] + payout)
			await ctx.send(f"You won {payout} coins! 🎉")

		else:
			await ctx.send(f"You lost {bet_amount} coins. Better luck next time! 😢")


#async def setup(bot) -> None:
#	await bot.add_cog(GamblingCmds(bot))