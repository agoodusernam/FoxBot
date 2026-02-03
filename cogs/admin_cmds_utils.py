import datetime
import re

import discord
from discord.ext import commands

from command_utils.analysis import DBMessage, DatetimeDBMessage


def dt_from_timestamp(timestamp: float) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)

def sort_by_timestamp(messages: list[DBMessage]) -> list[DatetimeDBMessage]:
    new_msgs: list[DatetimeDBMessage]
    
    new_msgs = [DatetimeDBMessage(**message, timestamp = dt_from_timestamp(message['timestamp'])) for message in messages]
    
    return sorted(new_msgs, key=lambda x: x['timestamp'], reverse=True)


async def last_log(ctx: discord.ext.commands.Context, anonymous: bool = False) -> None:
    mod_log_channel = ctx.bot.get_channel(1329367677940006952)  # Channel where the carlbot logs are sent
    pub_logs_channel = ctx.bot.get_channel(1345300442376310885)  # Public logs channel (#guillotine)
    
    if mod_log_channel is None or pub_logs_channel is None:
        await ctx.send('Mod log channel or public logs channel not found.', delete_after=ctx.bot.del_after)
        return
    
    last_mod_log_message = [msg async for msg in mod_log_channel.history(limit=1)][0]
    if last_mod_log_message.content == 'Posted':
        await ctx.send('This log has already been sent to the public logs channel.', delete_after=ctx.bot.del_after)
        return
    
    embed = last_mod_log_message.embeds[0]
    
    offence = embed.title.split(sep='|')[0].title()
    if offence.strip() == 'Warn':
        offence = 'Warning'
    description = embed.description.split(sep='\n')
    offender = re.sub(r'^.*?<', '<', description[0])  # Extract offender mention
    description.pop(0)
    duration = None
    if description[0].startswith('**Duration'):
        duration = description[0].replace('**Duration:**', '')
        description.pop(0)
    
    reason = description[0].replace('**Reason:** ', '')
    description.pop(0)
    new_description = f'**Offender**: {offender}\n**Reason**: {reason}'
    if not anonymous:
        moderator = description[0].replace('**Responsible moderator:** ', '')
        moderator_user = await commands.UserConverter().convert(ctx, moderator)
        new_description += f'\n**Responsible moderator**: {moderator_user.mention}'
    
    to_send_embed = discord.Embed(
            title=f'{offence}',
            description=new_description,
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
    )
    if duration:
        to_send_embed.add_field(name='Duration', value=duration, inline=False)
    
    await pub_logs_channel.send(embed=to_send_embed)
    await mod_log_channel.send('Posted')
