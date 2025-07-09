import os

from discord.ext import commands

from command_utils.checks import not_blacklisted


class CTF(commands.Cog, name='CTF', command_attrs=dict(add_check=not_blacklisted)):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command(name='submit')
	@commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
	async def submit(self, ctx: commands.Context, *, args: str):
		"""The command to submit a solution to a CTF challenge."""
		if not args:
			await ctx.send(f"Your first clue is: {os.getenv('CTF_FIRST_CLUE')}")
			return
		
		if args.lower() == os.getenv('CTF_FIRST_ANSWER').lower():
			await ctx.send("Congratulations! You've solved the first challenge!")
			return


async def setup(bot):
	pass
# await bot.add_cog(CTF(bot))
