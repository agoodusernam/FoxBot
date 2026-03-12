import datetime
import logging
import os
import traceback
from collections import Counter
from typing import Any, NotRequired, TypeVar, TypedDict

import discord
from matplotlib import pyplot as plt

from command_utils.CContext import CContext, CoolBot
from command_utils.analysis.ana_utils import try_resolve_channel_id, try_resolve_uid
from utils import db_stuff

logger = logging.getLogger('discord')

class DBVoiceSession(TypedDict):
    user_id: str
    channel_id: str
    duration_seconds: int
    _id: Any  # The database internal ID, type depends on the database
    timestamp: NotRequired[int]


class UserVoiceStats(TypedDict):
    user_id: str
    total_seconds: int


class ChannelVoiceStats(TypedDict):
    channel_id: str
    total_seconds: int


class CompanionStats(TypedDict):
    user_id: str
    total_seconds: int


class UserVoiceAnalysisResult(TypedDict):
    user_id: str
    total_seconds: int
    active_channel_lb: list[ChannelVoiceStats]
    top_companions: list[CompanionStats]
    avg_session_duration: int
    peak_activity_hour: NotRequired[int]
    favorite_day: NotRequired[str]


class VoiceAnalysisResult(TypedDict):
    total_seconds: int
    total_users: int
    active_users_lb: list[UserVoiceStats]
    active_channels_lb: list[ChannelVoiceStats]

T = TypeVar('T', UserVoiceStats, ChannelVoiceStats, ChannelVoiceStats)

def add_time_stats(stats: T, seconds: int) -> T:
    total = stats.get('total_seconds', 0)
    stats['total_seconds'] = total + seconds
    return stats


def format_duration(seconds: int) -> str:
    """
    Format seconds into a readable duration string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


async def remove_invalid_voice_sessions(sessions: list[dict[str, Any]]) -> tuple[list[DBVoiceSession], int] | None:
    required_keys = {'user_id', 'channel_id', 'duration_seconds'}
    valid_sessions: list[DBVoiceSession] = []
    total_seconds: int = 0
    
    for session in sessions:
        
        valid = all(key in session for key in required_keys)
        
        if not valid:
            logger.warning(f'deleting invalid voice session: {session}')
            await db_stuff.del_db_entry('voice_sessions', session['_id'])
            continue
            
        total_seconds += session['duration_seconds']
        valid_session = DBVoiceSession(user_id=session['user_id'], channel_id=session['channel_id'], duration_seconds=session['duration_seconds'], _id=session['_id'])
        
        if 'timestamp' in session:
            valid_session['timestamp'] = session['timestamp']
            
        valid_sessions.append(valid_session)
        
    if not valid_sessions:
        return None
    return valid_sessions, total_seconds


async def get_valid_voice_sessions(skip_cache: bool = False) -> tuple[list[DBVoiceSession], int] | None:
    sessions = await db_stuff.cached_download_voice_sessions(skip_cache)
    
    if not sessions:
        return None
    
    return await remove_invalid_voice_sessions(sessions)


async def get_voice_statistics(include_left: bool = False, guild: discord.Guild | None = None) -> VoiceAnalysisResult | None:
    """
    Retrieve voice statistics from MongoDB and calculate user and channel totals.
    
    Args:
        include_left: Whether to include users who have left the server
        guild: Discord guild, used to check if users are still in the server

    Returns:
        Dictionary containing voice statistics or None if no data
    """
    DB_sessions: tuple[list[DBVoiceSession], int] | None = await get_valid_voice_sessions()
    
    if not DB_sessions:
        return None
    
    sessions, total_seconds_including_left = DB_sessions
    total_seconds: int = 0
    # Calculate user statistics
    user_stats: dict[str, UserVoiceStats] = {}
    channel_stats: dict[str, ChannelVoiceStats] = {}
    for session in sessions:
        user_id = session['user_id']
        if not include_left and guild is not None:
            if guild.get_member(int(user_id)) is None:
                continue
        
        user_stat: UserVoiceStats = user_stats.get(user_id, {'user_id': user_id, 'total_seconds': 0})
        user_stats[user_id] = add_time_stats(user_stat, session['duration_seconds'])
        total_seconds += session['duration_seconds']
        
        channel_id = session['channel_id']
        if guild is not None:
            exists = not (discord.utils.get(guild.channels, id=int(channel_id)) is None)
            if not exists:
                continue
        
        channel_stat: ChannelVoiceStats = channel_stats.get(channel_id, {'channel_id': channel_id, 'total_seconds': 0})
        channel_stats[channel_id] = add_time_stats(channel_stat, session['duration_seconds'])
    
    # Sort statistics
    top_users: list[UserVoiceStats] = sorted(
            [UserVoiceStats(user_id=user_id, total_seconds=data['total_seconds'])
             for user_id, data in user_stats.items()],
            key=lambda x: x['total_seconds'],
            reverse=True,
    )
    
    top_channels: list[ChannelVoiceStats] = sorted(
            [ChannelVoiceStats(channel_id=channel_id, total_seconds=data['total_seconds'])
             for channel_id, data in channel_stats.items()],
            key=lambda x: x['total_seconds'],
            reverse=True,
    )
    
    return VoiceAnalysisResult(
            total_seconds=total_seconds_including_left if include_left else total_seconds,
            total_users=len(user_stats),
            active_users_lb=top_users,
            active_channels_lb=top_channels,
    )


async def get_user_voice_statistics(user_id: str) -> UserVoiceAnalysisResult | None:
    """
    Retrieve voice statistics for a specific user.

    Args:
        user_id: Discord user ID

    Returns:
        Dictionary containing user voice statistics or None if no data
    """
    DB_sessions: tuple[list[DBVoiceSession], int] | None = await get_valid_voice_sessions()
    
    if not DB_sessions:
        return None
    
    sessions, total_seconds = DB_sessions
    
    # Filter sessions for this user
    user_sessions = [s for s in sessions if s["user_id"] == user_id]
    
    if not user_sessions:
        return None
    
    # Calculate total time
    total_seconds = sum(s["duration_seconds"] for s in user_sessions)
    
    # Calculate per-channel stats
    channel_stats: dict[str, ChannelVoiceStats] = {}
    for session in user_sessions:
        channel_id = session['channel_id']
        channel_stat: ChannelVoiceStats = channel_stats.get(channel_id, {'channel_id': channel_id, 'total_seconds': 0})
        channel_stats[channel_id] = add_time_stats(channel_stat, session['duration_seconds'])
    
    # Sort channels by time
    top_channels = sorted(
            [ChannelVoiceStats(channel_id=channel_id, total_seconds=data['total_seconds'])
             for channel_id, data in channel_stats.items()],
            key=lambda x: x['total_seconds'],
            reverse=True,
    )
    
    # Calculate top companions (who they spent the most time with)
    # Only consider sessions that have a timestamp
    timed_user_sessions = [s for s in user_sessions if 'timestamp' in s]
    other_sessions = [s for s in sessions if s['user_id'] != user_id and 'timestamp' in s]
    
    companion_seconds: dict[str, int] = {}
    for us in timed_user_sessions:
        us_end = us['timestamp']
        us_start = us_end - us['duration_seconds']
        us_channel = us['channel_id']
        
        for other in other_sessions:
            if other['channel_id'] != us_channel:
                continue
            o_end = other['timestamp']
            o_start = o_end - other['duration_seconds']
            
            overlap_start = max(us_start, o_start)
            overlap_end = min(us_end, o_end)
            overlap = overlap_end - overlap_start
            
            if overlap > 0:
                companion_seconds[other['user_id']] = companion_seconds.get(other['user_id'], 0) + overlap
    
    top_companions = sorted(
            [CompanionStats(user_id=uid, total_seconds=secs) for uid, secs in companion_seconds.items()],
            key=lambda x: x['total_seconds'],
            reverse=True,
    )
    
    # Session duration stats
    avg_session_duration = total_seconds // len(user_sessions) if user_sessions else 0
    
    # Peak activity hour and favorite day (only from timed sessions)
    result_dict = UserVoiceAnalysisResult(
            user_id=user_id,
            total_seconds=total_seconds,
            active_channel_lb=top_channels,
            top_companions=top_companions,
            avg_session_duration=avg_session_duration,
    )
    
    if timed_user_sessions:
        hour_counter: Counter[int] = Counter()
        day_counter: Counter[int] = Counter()
        for s in timed_user_sessions:
            start_ts = s['timestamp'] - s['duration_seconds']
            start_dt = datetime.datetime.fromtimestamp(start_ts, tz=datetime.timezone.utc)
            hour_counter[start_dt.hour] += s['duration_seconds']
            day_counter[start_dt.weekday()] += s['duration_seconds']
        
        result_dict['peak_activity_hour'] = hour_counter.most_common(1)[0][0]
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        result_dict['favorite_day'] = day_names[day_counter.most_common(1)[0][0]]
    
    return result_dict


async def voice_analysis(ctx: CContext, graph: bool = False, include_left: bool = False) -> None:
    """
    Generate voice activity statistics and send as a message.

    Args:
        ctx: Discord context
        graph: Whether to generate and send a graph
        include_left: Whether to include users who have left the server
    """
    guild: discord.Guild | None = ctx.bot.get_guild(ctx.bot.config.guild_id)
    
    stats: VoiceAnalysisResult | None = await get_voice_statistics(include_left, guild)
    
    if not stats:
        await ctx.send("No voice activity data available.")
        return
    
    result = "**Voice Activity Statistics**\n\n"
    
    # Top users
    result += "**Top 5 Users by Voice Activity**\n"
    for i, user in enumerate(stats['active_users_lb'][:5], 1):
        formatted_time = format_duration(user['total_seconds'])
        result += f"{i}. {await try_resolve_uid(int(user['user_id']), ctx.bot)}: {formatted_time}\n"
    
    result += "\n"
    
    # Top channels
    result += "**Top 5 Voice Channels by [Man Hours](https://en.wikipedia.org/wiki/Man-hour)**\n"
    for i, channel in enumerate(stats['active_channels_lb'][:5], 1):
        formatted_time = format_duration(channel['total_seconds'])
        result += f"{i}. {await try_resolve_channel_id(channel["channel_id"], guild)}: {formatted_time}\n"
    
    total_time_formatted = format_duration(stats['total_seconds'])
    if include_left:
        result += f"\n**Total time in voice channels, all time:** {total_time_formatted}"
    else:
        result += f"\n**Total time in voice channels:** {total_time_formatted}"
    
    await ctx.send(result)
    if graph:
        try:
            await generate_voice_activity_graph(ctx.channel, ctx.bot, stats, 15)
        except Exception as e:
            logger.error(f'Error generating voice activity graph: {traceback.format_exc()}')
            await ctx.send(f'Error generating graph: {e}')


async def add_voice_analysis_for_user(ctx: CContext, member: discord.Object) -> None:
    """
    Generate voice activity statistics for a specific user.

    Args:
        ctx: The Discord command context
        member: Discord user to analyse
    """
    stats: UserVoiceAnalysisResult | None = await get_user_voice_statistics(str(member.id))
    guild: discord.Guild | None = ctx.bot.get_guild(ctx.bot.config.guild_id)
    
    if not stats:
        if member.type == discord.abc.User:
            user = await ctx.bot.fetch_user(member.id)
            assert user is not None
            await ctx.send(f"No voice activity data available for {user.display_name}.")
            return
        
        await ctx.send("The input is not be a valid user.")
        return
    
    formatted_total_time: str = format_duration(stats['total_seconds'])
    
    result = f"**Voice Activity for {await try_resolve_uid(int(stats["user_id"]), ctx.bot)}**\n\n"
    result += f"**Total time in voice channels:** {formatted_total_time}\n\n"
    
    result += f"**Top {len(stats["active_channel_lb"][:5])} Most Used Voice Channels**\n"
    for i, channel in enumerate(stats["active_channel_lb"][:5], 1):
        formatted_time = format_duration(channel['total_seconds'])
        result += f"{i}. {await try_resolve_channel_id(channel["channel_id"], guild)}: {formatted_time}\n"
    
    if stats['top_companions']:
        result += f"\n**Top {len(stats['top_companions'][:5])} Most Time Spent With**\n"
        for i, companion in enumerate(stats['top_companions'][:5], 1):
            formatted_time = format_duration(companion['total_seconds'])
            result += f"{i}. {await try_resolve_uid(int(companion['user_id']), ctx.bot)}: {formatted_time}\n"
    
    result += f"\n**Average session duration:** {format_duration(stats['avg_session_duration'])}\n"
    
    if 'peak_activity_hour' in stats:
        result += f"**Peak activity hour (UTC):** {stats['peak_activity_hour']}:00 - {stats['peak_activity_hour']}:59\n"
    if 'favorite_day' in stats:
        result += f"**Most active day of the week:** {stats['favorite_day']}\n"
    
    await ctx.send(result)


async def format_voice_analysis(ctx: CContext, graph: bool = False, user: discord.Object | None = None,
                                include_left: bool = False) -> None:
    """
    Format and send voice analysis results.

    Args:
        ctx: Discord command context
        graph: Whether to generate and send a graph
        user: The optional user to analyse
        include_left: If True, include users who have left the server
    """
    
    new_msg: discord.Message = await ctx.send('Analysing voice statistics...')
    
    if user is not None:
        await add_voice_analysis_for_user(ctx, user)
        await new_msg.delete()
        return
    
    # No user specified, show general voice stats
    try:
        await voice_analysis(ctx, graph, include_left)
        await new_msg.delete()
    except Exception as e:
        logger.error(f'Error during voice analysis: {traceback.format_exc()}')
        await ctx.send(f'Error during voice analysis: {e}')


async def generate_voice_activity_graph(channel: discord.TextChannel, bot: CoolBot,
        stats: VoiceAnalysisResult | list[UserVoiceStats], count: int, send_errors: bool = True) -> None:
    """ Generate and send a graph of voice activity.
    Args:
        channel: The channel where to send the graph
        bot: The bot instance
        stats: Voice analysis statistics
        count: The amount of users to show on the graph
        send_errors: Whether to send an error message if no data is available
    """
    if isinstance(stats, list):
        top_users = stats[:count]
    else:
        top_users = stats["active_users_lb"][:count]
        
    if not top_users:
        logger.error("No user voice activity data to graph.")
        if send_errors:
            await channel.send("No user voice activity data to graph.")
        return
    
    usernames: list[str] = []
    voice_time_hours = []
    
    for user_data in top_users:
        total_seconds = user_data['total_seconds']
        
        name = await try_resolve_uid(int(user_data['user_id']), bot)
        
        usernames.append(name if name is not None else f"ID:{user_data['user_id']}")
        voice_time_hours.append(int(total_seconds) / 3600)
    
    if not usernames:
        logger.error("No user voice activity data to graph.")
        if send_errors:
            await channel.send("No valid user data to generate a graph.")
        return
    
    # Reverse so the highest is at the top
    usernames.reverse()
    voice_time_hours.reverse()
    
    # Create the plot
    plt.figure(figsize=(10, 8), facecolor='#1f1f1f')
    ax = plt.gca()
    ax.set_facecolor('#2d2d2d')
    plt.barh(usernames, voice_time_hours, color='#8a2be2')
    plt.xlabel('Total Voice Time (hours)', color='white')
    plt.title('Top Users by Voice Activity', color='white')
    plt.tick_params(axis='both', colors='white')
    
    for spine in ax.spines.values():
        spine.set_color('#555555')
    plt.tight_layout()
    
    graph_file = 'top_voice_users.png'
    plt.savefig(graph_file)
    plt.close()
    
    await channel.send(file=discord.File(graph_file))
    
    try:
        os.remove(graph_file)
    except OSError:
        logger.warning(f'Could not remove graph file {graph_file}: {traceback.format_exc()}')


async def user_time_in_channel(ctx: CContext, user: discord.User, channel: discord.VoiceChannel) -> None:
    sessions = await get_valid_voice_sessions()
    
    if not sessions:
        await ctx.send("No voice activity data available.")
        return
    
    sessions_list, _ = sessions
    
    total_seconds: int = 0
    for session in sessions_list:
        if session['user_id'] == str(user.id) and session['channel_id'] == str(channel.id):
            total_seconds += session['duration_seconds']
    
    await ctx.send(f"{user.display_name} has been in {channel.mention} for {format_duration(total_seconds)}")


async def all_sessions_this_week(skip_cache: bool = False) -> list[DBVoiceSession]:
    """
    Retrieve all voice sessions from the past week.

    Returns:
        List of voice session dictionaries
    """
    sessions = await get_valid_voice_sessions(skip_cache)
    
    if not sessions:
        return []
    
    sessions_list, _ = sessions
    
    valid_sessions: list[DBVoiceSession] = []
    for session in sessions_list:
        if 'timestamp' not in session:
            continue
            
        logger.debug('session timestamp: %s', session['timestamp'])
        session_time = datetime.datetime.fromtimestamp(session['timestamp'], datetime.UTC)
        difference = discord.utils.utcnow() - session_time
        if difference <= datetime.timedelta(days=7):
            valid_sessions.append(DBVoiceSession(
                    user_id=session['user_id'],
                    channel_id=session['channel_id'],
                    duration_seconds=session['duration_seconds'],
                    _id=session['_id']
            ))
    
    return valid_sessions


async def voice_activity_this_week(skip_cache: bool = False) -> list[UserVoiceStats]:
    sessions = await all_sessions_this_week(skip_cache)
    stats: dict[str, UserVoiceStats] = {}
    for session in sessions:
        user_id = session['user_id']
        user_stat: UserVoiceStats = stats.get(user_id, {'user_id': user_id, 'total_seconds': 0})
        stats[user_id] = add_time_stats(user_stat, session['duration_seconds'])
    
    return sorted(stats.values(), key=lambda x: x['total_seconds'], reverse=True)[:5]
