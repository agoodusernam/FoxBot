import asyncio
from typing import Any

import discord
from discord.ext import commands

from command_utils.CContext import CoolBot, CContext
from command_utils.checks import is_admin
from cogs.server_backup_utils import save_guild, get_most_recent_backup, load_backup


class Backup(commands.Cog):
    def __init__(self, bot: CoolBot):
        self.bot: CoolBot = bot
    
    @commands.command(name='backup', help='Backup the server data', usage='f!backup')
    @commands.cooldown(1, 60, commands.BucketType.user)
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
    
    @commands.command(name='load_backup')
    @commands.cooldown(1, 60 * 60, commands.BucketType.guild)
    @commands.check(is_admin)
    @commands.guild_only()
    async def load_backup(self, ctx: CContext, g_id: str):
        assert ctx.guild is not None
        assert ctx.guild.self_role is not None
        if not ctx.guild.me.guild_permissions.administrator:
            await ctx.send('Bot requires administrator permissions to load')
            return
        
        backup: dict[Any, Any] | str = get_most_recent_backup(g_id)
        if isinstance(backup, str):
            # There was an error
            await ctx.send(backup)
            return
        
        for channel in ctx.guild.channels:
            await asyncio.sleep(0.2)
            try:
                await channel.delete()
            except discord.NotFound:
                pass
        for role in ctx.guild.roles:
            if role.name == '@everyone' or role.id == ctx.guild.self_role.id:
                continue
            await asyncio.sleep(0.2)
            await role.delete()
        
        success = await load_backup(backup, ctx.guild)
        
        if isinstance(success, str):
            await ctx.send(f'There was an Error: {success}')


async def setup(bot: CoolBot):
    await bot.add_cog(Backup(bot))
