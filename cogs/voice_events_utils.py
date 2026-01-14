import datetime
import logging
from typing import TypedDict

import discord

from command_utils.CContext import CoolBot
from utils import db_stuff

logger = logging.getLogger('discord')

class VoiceSession(TypedDict):
    channel_id: str
    channel_name: str
    joined_at: datetime.datetime

active_voice_sessions: dict[int, VoiceSession] = {}


def handle_join(member: discord.Member, after: discord.VoiceState | discord.VoiceChannel) -> None:
    """Track when a user joins a voice channel"""
    if isinstance(after, discord.VoiceState):
        if after.channel is None:
            logger.error(f'{member.name} joined a voice state with no channel')
            return
        logger.info(f'{member.name} joined {after.channel.name}')
        
        active_voice_sessions[member.id] = {
            'channel_id':   str(after.channel.id),
            'channel_name': after.channel.name,
            'joined_at':    discord.utils.utcnow()
        }
    else:
        logger.info(f'{member.name} joined {after.name}')
        
        # Record join time
        active_voice_sessions[member.id] = {
            'channel_id':   str(after.id),
            'channel_name': after.name,
            'joined_at':    discord.utils.utcnow()
        }


async def handle_leave(member: discord.Member) -> None:
    """Track when a user leaves a voice channel and upload session data"""
    logger.info(f'{member.name} left {active_voice_sessions[member.id]["channel_name"]}')
    
    # Get join data
    if member.id not in active_voice_sessions:
        logger.error(f"No join record found for {member.name}")
        return
    
    join_data = active_voice_sessions[member.id]
    leave_time = discord.utils.utcnow()
    join_time = join_data['joined_at']
    
    # Calculate duration
    duration_seconds = int((leave_time - join_time).total_seconds())
    
    # Create voice session document
    voice_session = {
        'user_id':          str(member.id),
        'user_name':        member.name,
        'user_global_name': member.global_name,
        'channel_id':       join_data['channel_id'],
        'channel_name':     join_data['channel_name'],
        'join_time':        join_time.isoformat(),
        'leave_time':       leave_time.isoformat(),
        'duration_seconds': duration_seconds
    }
    
    await db_stuff.send_voice_session(voice_session)
    
    # Clear session data
    del active_voice_sessions[member.id]


async def handle_move(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
    """Handle a user moving from one channel to another"""
    if before.channel is None or after.channel is None:
        logger.error(f'{member.name} moved but one of the channels is None')
        return
    logger.info(f'{member.name} moved from {before.channel.name} to {after.channel.name}')
    
    # First record the "leave" from the previous channel
    await handle_leave(member)
    
    # Then record the "join" to the new channel
    handle_join(member, after)


async def leave_all(bot: CoolBot) -> None:
    """Force leave all active voice sessions"""
    for member_id in list(active_voice_sessions.keys()):
        member = discord.utils.get(bot.get_all_members(), id=member_id)
        if member:
            await handle_leave(member)
        else:
            logger.warning(f"Member with ID {member_id} not found, clearing session data")
            del active_voice_sessions[member_id]
