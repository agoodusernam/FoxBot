import discord
from discord.ext import commands

from command_utils.CContext import CoolBot, CContext
from command_utils.checks import is_admin
from cogs.server_backup_utils import save_guild


class Backup(commands.Cog):
    def __init__(self, bot: CoolBot):
        self.bot: CoolBot = bot
    
    @commands.command(name='backup', help='Backup the server data', usage='f!backup')
    @commands.cooldown(1, 60, commands.BucketType.user)  # type: ignore
    @commands.check(is_admin)
    @commands.guild_only()
    async def backup(self, ctx: CContext):
        assert ctx.guild is not None
        await ctx.send('Backup started.')
        result: str | None = await save_guild(ctx.guild)
        if isinstance(result, str):
            await ctx.send(result)
            return
        
        await ctx.send('Backup complete.')

    
async def setup(bot: CoolBot):
    await bot.add_cog(Backup(bot))
