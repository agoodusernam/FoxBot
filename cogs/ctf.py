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
        if not args or args in ['help', 'h', '?', '', ' ']:
            await ctx.send(f'Your first clue is: {os.getenv('CTF_FIRST_CLUE')}')
            return
        
        if args.lower() == os.getenv('CTF_FIRST_ANSWER').lower():
            await ctx.send("Congratulations! You've solved the first challenge!")
            await ctx.send(f'Your second clue is: {os.getenv('CTF_SECOND_CLUE')}')
            return
        
        if args.lower() == os.getenv('CTF_SECOND_ANSWER').lower():
            await ctx.send("Well done! You've solved the second challenge!")
            await ctx.send(f'Your final clue is: {os.getenv('CTF_FINAL_CLUE')}')
            return
        
        if args.lower() == os.getenv('CTF_FINAL_ANSWER').lower():
            await ctx.send("Amazing! You've completed the CTF challenge!")
            # TODO: Add reward logic here
            return


async def setup(bot):
    pass
# await bot.add_cog(CTF(bot))
