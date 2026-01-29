import logging

import discord
from discord.ext import commands

from command_utils.CContext import CoolBot
from command_utils.embed_util import create_log_embed
from cogs.member_events_utils import time_ago, get_changes, MISSING, nick_update_embed, roles_changed_embed, timeout_embed, MissingType, avatar_update_embed

logger = logging.getLogger('discord')


class MemberEvents(commands.Cog, name="Member Events"):
    def __init__(self, bot: CoolBot):
        self.bot: CoolBot = bot
        self.jl_logs_channel: discord.TextChannel | None = None
        self.member_logs_channel: discord.TextChannel | None = None
    
    def ensure_jl_logs_channel(self) -> bool:
        if not isinstance(self.jl_logs_channel, discord.TextChannel):
            logs_channel = self.bot.get_channel(self.bot.config.join_leave_log_channel_id)
            
            if not isinstance(logs_channel, discord.TextChannel):
                logger.error(f'Join Leave log channel not found or not of correct type. Type: {type(logs_channel)}.\n' +
                             f'Given ID: {self.bot.config.join_leave_log_channel_id}.')
                return False
            
            self.jl_logs_channel = logs_channel
            return True
        return True
    
    def ensure_member_logs_channel(self):
        if not isinstance(self.member_logs_channel, discord.TextChannel):
            logs_channel = self.bot.get_channel(self.bot.config.member_logs_channel_id)
            
            if not isinstance(logs_channel, discord.TextChannel):
                logger.error(f'Member log channel not found or not of correct type. Type: {type(logs_channel)}.\n' +
                             f'Given ID: {self.bot.config.member_logs_channel_id}.')
                return False
            
            self.member_logs_channel = logs_channel
            return True
        return True
        
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        logger.debug(f'{member.name} with ID {member.id} joined the server.')
        if not self.ensure_jl_logs_channel():
            return
        
        assert self.jl_logs_channel is not None
        
        member_count: str = str(member.guild.member_count if member.guild.member_count else len(member.guild.members))
        suffix: str
        if member_count[-1] == '1': suffix = 'st'
        elif member_count[-1] == '2': suffix = 'nd'
        elif member_count[-1] == '3': suffix = 'rd'
        else: suffix = 'th'
        description: str = f'{member.mention}, {member_count}{suffix} to join.\n'
        description += f'Current display name: {member.display_name}\n'
        description += f'Account created {time_ago(member.created_at)}\n'
        if member.bot:
            description += 'This user is a bot.\n'
        
        if member.system:
            description += 'This user is a Discord system user (represents Discord officially).\n'
        
        
        embed = create_log_embed(member.name,
                member.display_avatar.url,
                description,
                discord.Color.from_rgb(102, 219, 174),
                'Member joined',
                f'ID: {member.id}',
        )
        
        
        await self.jl_logs_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        logger.debug(f'{member.name} with ID {member.id} left the server.')
        if not self.ensure_jl_logs_channel():
            return
        
        assert self.jl_logs_channel is not None
        
        left_ago: str = time_ago(member.joined_at) if member.joined_at is not None else 'Unknown join date'
        roles: str = ", ".join([m.mention for m in member.roles[1:]])
        if roles == "":
            roles = "None"
        
        description: str = f'Joined {left_ago}.\nRoles: {roles}'
        embed: discord.Embed = create_log_embed(
                member.name,
                member.display_avatar.url,
                description,
                discord.Color.yellow(),
                'Member left',
                f'ID: {member.id}'
        )
        
        await self.jl_logs_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        logger.debug(f'{before.name} with ID {before.id} updated.')
        changes = get_changes(before, after)
        logger.debug("Changes: " + str(changes))
        
        if not self.ensure_member_logs_channel():
            return
        
        assert self.jl_logs_channel is not None
        
        if changes['nick'] is not MISSING:
            logger.debug(f'{before.name} changed nickname: {changes["nick"]}')
            embed = nick_update_embed(before.nick, after)
            await self.jl_logs_channel.send(embed=embed)
        
        if changes['roles_added'] is not MISSING:
            assert not isinstance(changes['roles_added'], MissingType)
            logger.debug(f'{before.name} added roles: {", ".join([c.name for c in changes["roles_added"]])}')
            embed = roles_changed_embed(changes["roles_added"], after, 'Roles added', 'added to')
            await self.jl_logs_channel.send(embed=embed)
        
        if changes['roles_removed'] is not MISSING:
            assert not isinstance(changes['roles_removed'], MissingType)
            logger.debug(f'{before.name} removed roles: {", ".join([c.name for c in changes["roles_removed"]])}')
            embed = roles_changed_embed(changes["roles_removed"], after, 'Roles removed', 'removed from')
            await self.jl_logs_channel.send(embed=embed)
        
        if changes['timed_out_until'] is not MISSING:
            assert not isinstance(changes['timed_out_until'], MissingType)
            logger.debug(f'{before.name} timeout changed')
            embed = timeout_embed(after, changes["timed_out_until"])
            await self.jl_logs_channel.send(embed=embed)
        
        if changes['avatar'] is not MISSING:
            logger.debug(f'{before.name} changed avatar')
            embed = avatar_update_embed(after)
            await self.jl_logs_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User | discord.Member):
        logger.debug(f'{user.name} with ID {user.id} was banned from {guild.name}.')
        if not self.ensure_member_logs_channel():
            return
        
        assert self.member_logs_channel is not None
        
        embed = create_log_embed(user.name, user.display_avatar.url, f'{user.mention} was banned.', discord.Color.red(), 'Member banned', f'ID: {user.id}')
        await self.member_logs_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        logger.debug(f'{user.name} with ID {user.id} was unbanned from {guild.name}.')
        if not self.ensure_member_logs_channel():
            return
        
        assert self.member_logs_channel is not None
        
        embed = create_log_embed(user.name, user.display_avatar.url, f'{user.mention} was unbanned.', discord.Color.green(), 'Member unbanned', f'ID: {user.id}')
        await self.member_logs_channel.send(embed=embed)

async def setup(bot: CoolBot):
    await bot.add_cog(MemberEvents(bot))
