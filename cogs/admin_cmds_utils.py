import datetime
import re
import secrets

import discord
from discord.ext import commands

from command_utils.analysis.text_analysis import DatetimeDBMessage, DBMessage
from command_utils.CContext import CContext


async def get_member_by_id(ctx: CContext, member_id: int) -> discord.Member | None:
    if ctx.guild is None:
        return None
    member = ctx.guild.get_member(member_id)
    if member is not None:
        return member
    try:
        return await ctx.guild.fetch_member(member_id)
    except discord.HTTPException:
        return None
    
async def rek_random_in_channel(ctx: CContext, channel: discord.VoiceChannel | discord.StageChannel):
    users: list[int] = list(channel.voice_states)
    valid_users: list[int] = []
    for user in users:
        if user not in ctx.bot.admin_ids:
            valid_users.append(user)

    if not valid_users:
        await ctx.send("No users in the specified channel.")
        return

    to_rek: int = secrets.choice(valid_users)
    member: discord.Member | None = await get_member_by_id(ctx, to_rek)
    if member is None:
        await ctx.send("User not found.")
        return
    
    try:
        await member.timeout(datetime.timedelta(days=28), reason="get rekt nerd")
        await ctx.send(f"{member.display_name} has been rekt.")
    except discord.HTTPException:
        await ctx.send("Failed to rekt user.")
    return

def dt_from_timestamp(timestamp: float) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.UTC)


def sort_by_timestamp(messages: list[DBMessage]) -> list[DatetimeDBMessage]:
    new_msgs: list[DatetimeDBMessage]
    
    new_msgs = [DatetimeDBMessage(**message, timestamp=dt_from_timestamp(message['timestamp'])) for message in messages]
    
    return sorted(new_msgs, key=lambda x: x['timestamp'], reverse=True)


async def last_log(ctx: commands.Context, anonymous: bool = False) -> None:
    mod_log_channel = ctx.bot.get_channel(1329367677940006952)  # Channel where the carlbot logs are sent
    pub_logs_channel = ctx.bot.get_channel(1345300442376310885)  # Public logs channel (#guillotine)
    
    if mod_log_channel is None or pub_logs_channel is None:
        await ctx.send('Mod log channel or public logs channel not found.', delete_after=ctx.bot.del_after)
        return
    
    last_mod_log_message: discord.Message = next(msg async for msg in mod_log_channel.history(limit=1))
    if last_mod_log_message.content == 'Posted':
        await ctx.send('This log has already been sent to the public logs channel.', delete_after=ctx.bot.del_after)
        return
    
    embed = last_mod_log_message.embeds[0]
    if embed is None or embed.title is None or embed.description is None:
        await ctx.send('No embed found in the last mod log message.', delete_after=ctx.bot.del_after)
        return
    
    offence = embed.title.split(sep='|')[0].title()
    if offence.strip() == 'Warn':
        offence = 'Warning'
    description: list[str] = embed.description.split(sep='\n')
    offender = re.sub(r'^.*?<', '<', description[0])  # Extract offender mention
    description.pop(0)
    duration: str | None = None
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
            timestamp=discord.utils.utcnow(),
    )
    if duration:
        to_send_embed.add_field(name='Duration', value=duration, inline=False)
    
    await pub_logs_channel.send(embed=to_send_embed)
    await mod_log_channel.send('Posted')
