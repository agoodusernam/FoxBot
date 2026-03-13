import datetime
import logging
import tempfile
import traceback
from collections import Counter
from pathlib import Path
from statistics import median
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
    total_sessions: int
    avg_users_per_session: float
    median_session_duration: int
    peak_activity_hour: NotRequired[int]
    favorite_day: NotRequired[str]


class DuoStats(TypedDict):
    user_id_1: str
    user_id_2: str
    total_seconds: int


class WeeklyActiveStats(TypedDict):
    this_week: int
    last_week: int
    activity_ratio: float  # this_week / total_users


class VoiceAnalysisResult(TypedDict):
    total_seconds: int
    total_users: int
    active_users_lb: list[UserVoiceStats]
    active_channels_lb: list[ChannelVoiceStats]
    best_duo: NotRequired[DuoStats]
    avg_users_per_session: NotRequired[float]
    total_sessions: NotRequired[int]
    avg_session_duration: NotRequired[int]
    median_session_duration: NotRequired[int]
    weekly_active: NotRequired[WeeklyActiveStats]

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


def _merge_adjacent_sessions(sessions: list[DBVoiceSession], max_gap_seconds: int = 60) -> list[DBVoiceSession]:
    """
    Merge sessions from the same user and channel that are close together in time.
    This handles the case where the bot restarts and creates two separate sessions
    for what is effectively a single continuous voice session.
    
    Sessions are merged when the gap between one session's end and the next session's
    start is within max_gap_seconds.
    """
    # Only timed sessions can be merged; keep untimed ones as-is
    timed = [s for s in sessions if 'timestamp' in s]
    untimed = [s for s in sessions if 'timestamp' not in s]
    
    if not timed:
        return sessions
    
    # Sort by user_id, channel_id, then timestamp
    timed.sort(key=lambda s: (s['user_id'], s['channel_id'], s['timestamp']))
    
    merged: list[DBVoiceSession] = []
    current = timed[0]
    
    for next_session in timed[1:]:
        same_user = current['user_id'] == next_session['user_id']
        same_channel = current['channel_id'] == next_session['channel_id']
        
        if same_user and same_channel:
            current_end = current['timestamp']
            next_start = next_session['timestamp'] - next_session['duration_seconds']
            gap = next_start - current_end
            
            if 0 <= gap <= max_gap_seconds:
                # Merge: combine durations + gap, keep the later timestamp
                current = DBVoiceSession(
                    user_id=current['user_id'],
                    channel_id=current['channel_id'],
                    duration_seconds=current['duration_seconds'] + next_session['duration_seconds'] + gap,
                    _id=current['_id'],
                    timestamp=next_session['timestamp'],
                )
                continue
        
        merged.append(current)
        current = next_session
    
    merged.append(current)
    return untimed + merged


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
    
    valid_sessions = _merge_adjacent_sessions(valid_sessions)
    merged_total = sum(s['duration_seconds'] for s in valid_sessions)
    return valid_sessions, merged_total


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
    
    # Best duo calculation
    timed_sessions = [s for s in sessions if 'timestamp' in s]
    duo_seconds: dict[tuple[str, str], int] = {}
    for i, s1 in enumerate(timed_sessions):
        s1_start = s1['timestamp'] - s1['duration_seconds']
        s1_end = s1['timestamp']
        for s2 in timed_sessions[i + 1:]:
            if s1['user_id'] == s2['user_id']:
                continue
            if s1['channel_id'] != s2['channel_id']:
                continue
            s2_start = s2['timestamp'] - s2['duration_seconds']
            s2_end = s2['timestamp']
            overlap = min(s1_end, s2_end) - max(s1_start, s2_start)
            if overlap > 0:
                uid1, uid2 = sorted([s1['user_id'], s2['user_id']])
                pair: tuple[str, str] = (uid1, uid2)
                duo_seconds[pair] = duo_seconds.get(pair, 0) + overlap

    best_duo: DuoStats | None = None
    if duo_seconds:
        best_pair = max(duo_seconds, key=lambda k: duo_seconds[k])
        best_duo = DuoStats(user_id_1=best_pair[0], user_id_2=best_pair[1], total_seconds=duo_seconds[best_pair])

    # Average users per session and total sessions
    # A "session" is approximated by grouping overlapping timed sessions per channel
    total_session_count = len(sessions)
    # Count unique users per channel-session overlap window is complex;
    # simpler: for each session, count how many other users were in the same channel at the same time
    # Average users per session = average number of concurrent users when a session starts
    if timed_sessions:
        concurrent_counts: list[int] = []
        for s in timed_sessions:
            s_start = s['timestamp'] - s['duration_seconds']
            count: int = 0
            for other in timed_sessions:
                if other is s:
                    continue
                if other['channel_id'] != s['channel_id']:
                    continue
                o_start = other['timestamp'] - other['duration_seconds']
                o_end = other['timestamp']
                if o_start <= s_start < o_end:
                    count += 1
            concurrent_counts.append(count + 1)  # +1 for the user themselves
        avg_users_per_session = sum(concurrent_counts) / len(concurrent_counts)
    else:
        avg_users_per_session = 1.0

    # Average and median session duration
    session_durations = [s['duration_seconds'] for s in sessions]
    avg_session_duration = sum(session_durations) // len(session_durations) if session_durations else 0
    median_session_duration = int(median(session_durations)) if session_durations else 0

    # Weekly unique active users
    now = datetime.datetime.now(datetime.timezone.utc)
    one_week_ago = now - datetime.timedelta(days=7)
    two_weeks_ago = now - datetime.timedelta(days=14)
    this_week_users: set[str] = set()
    last_week_users: set[str] = set()
    for s in timed_sessions:
        session_time = datetime.datetime.fromtimestamp(s['timestamp'], datetime.timezone.utc)
        if session_time >= one_week_ago:
            this_week_users.add(s['user_id'])
        elif session_time >= two_weeks_ago:
            last_week_users.add(s['user_id'])

    total_user_count = len(user_stats) if user_stats else 1
    weekly_active = WeeklyActiveStats(
        this_week=len(this_week_users),
        last_week=len(last_week_users),
        activity_ratio=len(this_week_users) / total_user_count,
    )

    result_dict = VoiceAnalysisResult(
            total_seconds=total_seconds_including_left if include_left else total_seconds,
            total_users=len(user_stats),
            active_users_lb=top_users,
            active_channels_lb=top_channels,
            total_sessions=total_session_count,
            avg_users_per_session=avg_users_per_session,
            avg_session_duration=avg_session_duration,
            median_session_duration=median_session_duration,
            weekly_active=weekly_active,
    )
    if best_duo:
        result_dict['best_duo'] = best_duo

    return result_dict


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
    median_session_duration = int(median([s['duration_seconds'] for s in user_sessions])) if user_sessions else 0
    total_sessions = len(user_sessions)

    # Average users per session for this user
    timed_user_sessions_for_avg = [s for s in user_sessions if 'timestamp' in s]
    all_timed = [s for s in sessions if 'timestamp' in s]
    if timed_user_sessions_for_avg:
        concurrent_counts_user: list[int] = []
        for s in timed_user_sessions_for_avg:
            s_start = s['timestamp'] - s['duration_seconds']
            count: int = 0
            for other in all_timed:
                if other is s:
                    continue
                if other['channel_id'] != s['channel_id']:
                    continue
                o_start = other['timestamp'] - other['duration_seconds']
                o_end = other['timestamp']
                if o_start <= s_start < o_end:
                    count += 1
            concurrent_counts_user.append(count + 1)
        avg_users_per_session = sum(concurrent_counts_user) / len(concurrent_counts_user)
    else:
        avg_users_per_session = 1.0

    # Peak activity hour and favorite day (only from timed sessions)
    result_dict = UserVoiceAnalysisResult(
            user_id=user_id,
            total_seconds=total_seconds,
            active_channel_lb=top_channels,
            top_companions=top_companions,
            avg_session_duration=avg_session_duration,
            total_sessions=total_sessions,
            avg_users_per_session=avg_users_per_session,
            median_session_duration=median_session_duration,
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
        result += f"\n**Total time in voice channels, all time:** {total_time_formatted}\n"
    else:
        result += f"\n**Total time in voice channels:** {total_time_formatted}\n"

    # Best duo
    if 'best_duo' in stats:
        duo = stats['best_duo']
        duo_time = format_duration(duo['total_seconds'])
        user1 = await try_resolve_uid(int(duo['user_id_1']), ctx.bot)
        user2 = await try_resolve_uid(int(duo['user_id_2']), ctx.bot)
        result += f"\n**Best Duo:** {user1} & {user2} — {duo_time} together\n"

    # Session stats
    if 'total_sessions' in stats:
        result += f"**Total sessions:** {stats['total_sessions']}\n"
    if 'avg_users_per_session' in stats:
        result += f"**Average users per session:** {stats['avg_users_per_session']:.1f}\n"
    if 'avg_session_duration' in stats:
        result += f"**Average session length:** {format_duration(stats['avg_session_duration'])}\n"
    if 'median_session_duration' in stats:
        result += f"**Median session length:** {format_duration(stats['median_session_duration'])}\n"

    # Weekly active users
    if 'weekly_active' in stats:
        wa = stats['weekly_active']
        diff = wa['this_week'] - wa['last_week']
        trend = f"(+{diff})" if diff >= 0 else f"({diff})"
        result += f"\n**Weekly unique active users:** {wa['this_week']} {trend} vs last week ({wa['last_week']})\n"
        result += f"**Activity ratio:** {wa['activity_ratio']:.1%} of all users\n"

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
    
    result += f"\n**Total sessions:** {stats['total_sessions']}\n"
    result += f"**Average users per session:** {stats['avg_users_per_session']:.1f}\n"
    result += f"**Average session duration:** {format_duration(stats['avg_session_duration'])}\n"
    result += f"**Median session duration:** {format_duration(stats['median_session_duration'])}\n"
    
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
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        graph_file = Path('top_voice_users.png')
        plt.savefig(temp_dir_path / graph_file)
        plt.close()
    
        await channel.send(file=discord.File(graph_file))
    

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
