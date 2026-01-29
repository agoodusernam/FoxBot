import discord
from discord.ext import commands

from command_utils.CContext import CoolBot, CContext
from command_utils.checks import is_admin


class Backup(commands.Cog):
    def __init__(self, bot: CoolBot):
        self.bot: CoolBot = bot
    
    @commands.command(name='backup', help='Backup the server data', usage='f!backup')
    @commands.cooldown(1, 60, commands.BucketType.user)  # type: ignore
    @commands.check(is_admin)
    async def backup(self, ctx: CContext):
        await ctx.send('Backup started.')
    
    
    
async def setup(bot: CoolBot):
    pass
    # await bot.add_cog(Backup(bot))
