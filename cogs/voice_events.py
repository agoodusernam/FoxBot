import logging

import discord
from discord.ext import commands

from command_utils.CContext import CoolBot
from cogs.voice_events_utils import handle_join, handle_move, handle_leave

logger = logging.getLogger('discord')

class VoiceLogging(commands.Cog, name='Voice Logging'):
    def __init__(self, bot: CoolBot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return
        if self.bot.config.staging:
            return
        
        logging_channel = self.bot.get_channel(self.bot.config.logging_channels.voice) if self.bot.config.logging_channels.voice else None
        
        if not isinstance(logging_channel, discord.TextChannel):
            return
        
        url = member.avatar.url if member.avatar is not None else member.default_avatar.url
        
        # Member joined channel
        if before.channel is None and after.channel is not None:
            handle_join(member, after)
            embed = discord.Embed(title=f'{member.display_name} joined #{after.channel.name}',
                    color=discord.Color.green())
            embed.set_author(name=member.name, icon_url=url)
            embed.timestamp = discord.utils.utcnow()
            if logging_channel:
                await logging_channel.send(embed=embed)
        
        
        # Member left channel
        elif before.channel is not None and after.channel is None:
            await handle_leave(member)
            if logging_channel:
                embed = discord.Embed(title=f'{member.display_name} left #{before.channel.name}',
                        color=discord.Color.red())
                embed.set_author(name=member.name, icon_url=url)
                embed.timestamp = discord.utils.utcnow()
                await logging_channel.send(embed=embed)
            
            if before.channel.name.startswith('private_'):
                if before.channel and len(before.channel.members) == 0:
                    await before.channel.delete(reason='Private VC empty after member left')
            
            if before.channel.name.startswith('temp_'):
                if before.channel and len(before.channel.members) == 0:
                    await before.channel.delete(reason='Temp VC empty after member left')
            
            if self.bot.vc_client is None:
                return
            
            if len(before.channel.members) == 1 and self.bot.vc_client.channel.id == before.channel.id:
                await self.bot.vc_client.disconnect()
                self.bot.vc_client = None
        
        # Member moved to another channel
        elif before.channel != after.channel:
            if before.channel is None or after.channel is None:
                return
            await handle_move(member, before, after)
            embed = discord.Embed(title=f'{member.display_name} moved from #{before.channel.name} to'
                                        f' #{after.channel.name}', color=discord.Color.blue())
            embed.set_author(name=member.name, icon_url=url)
            embed.timestamp = discord.utils.utcnow()
            if logging_channel:
                await logging_channel.send(embed=embed)
            
            if before.channel.name.startswith('private_'):
                if before.channel and len(before.channel.members) == 0:
                    await before.channel.delete(reason='Private VC empty after member left')
            
            if self.bot.vc_client is None:
                return
            
            if len(before.channel.members) == 1 and self.bot.vc_client.channel.id == before.channel.id:
                await self.bot.vc_client.disconnect()
                self.bot.vc_client = None


async def setup(bot):
    pass
    # await bot.add_cog(VoiceLogging(bot))
