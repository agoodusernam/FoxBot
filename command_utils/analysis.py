# pylint: disable=trailing-whitespace, line-too-long
import collections
import copy
import datetime
import logging
import os
import string
from typing import Any, TYPE_CHECKING

import discord
from discord.ext.commands import Context
import matplotlib.pyplot as plt

import config.bot_config
from command_utils.CContext import CContext, CoolBot
from utils import db_stuff, utils

# omg this code is so ass
# i really hope it doesnt break because if it does im fucked

# Configure logging
logger = logging.getLogger('discord')

# Constants
EXCLUDED_USER_IDS = ['1107579143140413580']
GUILD_ID = config.bot_config.get_config_option('guild_id', 0)
TIME_FILTERS = {
    'w': ('week', datetime.timedelta(days=7)),
    'd': ('day', datetime.timedelta(days=1)),
    'h': ('hour', datetime.timedelta(hours=1))
}


def check_required_keys(message: dict[str, Any]) -> bool:
    """
    Validate that a message contains all required keys.

    Args:
        message: The message dictionary to validate

    Returns:
        bool: True if the message contains all required keys, False otherwise
    """
    required_keys = {
        'author', 'author_id', 'author_global_name',
        'content', 'reply_to', 'HasAttachments',
        'timestamp', 'channel', 'channel_id',
    }
    return all(key in message for key in required_keys)


def remove_invalid_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    valid_messages = []
    for message in messages:
        if check_required_keys(message):
            valid_messages.append(message)
        else:
            db_stuff.delete_message(message['_id'])
    
    return valid_messages

def get_valid_messages(flag: str | None = None, ctx: CContext | None = None) -> tuple[list[dict[str, str | float]], int]:
    """
    Download and validate messages from the database.

    Args:
        flag: Optional time filter - 'w' for last week, 'd' for last day,
                    'h' for last hour, or None for all messages
        ctx: Discord command context, used to get the guild for user validation

    Returns:
        Tuple containing a list of valid messages and the total message count
    """
    try:
        # Download all messages from database
        messages = db_stuff.cached_download_all()
        if messages is None:
            return [], 0
        total_messages = len(messages)
        guild = None
        if ctx is not None:
            guild = ctx.bot.get_guild(1081760248433492140)
        
        if not messages:
            logger.warning('No messages found or failed to connect to the database.')
            return [], 0
        
        # Filter out excluded users
        all_messages = [msg for msg in messages if msg['author_id'] not in EXCLUDED_USER_IDS]
        
        # Validate messages and remove invalid ones
        valid_messages = remove_invalid_messages(all_messages)

        
        # Apply time filter if specified
        if flag in TIME_FILTERS:
            filter_name, time_delta = TIME_FILTERS[flag]
            time_ago = discord.utils.utcnow() - time_delta
            
            # I can't decide if I hate that you can do this purely with list comprehensions or not
            valid_messages = [
                msg for msg in valid_messages
                if datetime.datetime.fromtimestamp(msg['timestamp'], datetime.UTC) >= time_ago
            ]
            logger.info(f'Applied {filter_name} filter: {len(valid_messages)} messages')
        
        if flag != "il" and guild is not None:
            # don't include messages from users no longer in the guild
            valid_messages = [msg for msg in valid_messages if guild.get_member(int(msg['author_id']))]
        
        logger.info('Total valid messages: %s', len(valid_messages))
        logger.info('Total messages in database: %s', total_messages)
        return valid_messages, total_messages
    
    except Exception as e:
        logger.error("Error retrieving messages: %s", e)
        return [], 0


def analyse_word_stats(content_list: list[str]) -> dict[str, str | int | float]:
    """
    Analyse word statistics from a list of message content.

    Args:
        content_list: List of message content strings

    Returns:
        Dictionary containing word statistics
    """
    if not content_list:
        return {}
    
    # Extract and normalize all words
    all_words = [word.lower() for msg in content_list for word in msg.split() if word]
    if not all_words:
        return {}
    
    # Calculate statistics
    word_count = collections.Counter(all_words)
    most_common_word, most_common_count = word_count.most_common(1)[0]
    unique_words = set(all_words)
    
    # Calculate average word length
    avg_length = sum(len(word) for word in unique_words) / len(unique_words) if unique_words else 0
    
    return {
        'most_common_word':       most_common_word,
        'most_common_word_count': most_common_count,
        'total_unique_words':     len(unique_words),
        'average_length':         avg_length
    }


def get_channel_stats(messages: list[dict[str, str | float]]) -> list[dict[str, str | int]]:
    """
    Get statistics about channel activity.

    Args:
        messages: List of message dictionaries

    Returns:
        List of dictionaries containing channel statistics
    """
    if not messages:
        return []
    
    channel_counts = collections.Counter(msg['channel'] for msg in messages)
    return [
        {'channel': channel, 'num_messages': count}
        for channel, count in channel_counts.items()
        if count > 0
    ]


def analyse_messages(ctx: CContext, time_filter: str | None = None) -> dict[str, int | str | float | list[dict[str,
                                                                     str | int]]] | str:
    """
    analyse all messages in the database.

    Args:
        time_filter: Optional time filter - 'w' for last week, 'd' for last day, 
                    'h' for last hour, or None for all messages
        ctx: Discord command context, used to get the guild for user validation

    Returns:
        Dictionary containing analysis results or error message
    """
    try:
        valid_messages, total_messages = get_valid_messages(time_filter, ctx=ctx)
        if not valid_messages:
            return 'No valid messages found to analyse.'
        
        # Extract message content
        content_list = [message['content'] for message in valid_messages]
        
        # analyse word statistics
        word_stats = analyse_word_stats(content_list)
        if not word_stats:
            return 'No valid content to analyse.'
        
        # Get user message counts
        user_message_count = collections.Counter(msg['author_id'] for msg in valid_messages)
        active_users: list[dict[str, int | str]] = [
            {'user': user, 'num_messages': count}
            for user, count in user_message_count.items()
        ]
        
        # Get channel stats
        active_channels = get_channel_stats(valid_messages)
        
        return {
            'total_messages':         total_messages,
            'most_common_word':       word_stats['most_common_word'],
            'most_common_word_count': word_stats['most_common_word_count'],
            'total_unique_words':     word_stats['total_unique_words'],
            'average_length':         word_stats['average_length'],
            'active_users_lb':        active_users,
            'active_channels_lb':     active_channels,
            'total_users':            len(user_message_count),
        }
    
    except Exception as e:
        logger.error('Error during message analysis: %s', e)
        return f'Error during analysis: {str(e)}'


def analyse_user_messages(member: discord.User, time_filter: str | None = None) -> dict[str, int | str | float | list[
                                                                            dict[str, str | int]]] | str | None:
    """
    analyse messages from a specific user.

    Args:
        member: Discord user to analyse
        time_filter: Optional time filter - 'w' for last week, 'd' for last day, 
                    'h' for last hour, or None for all messages

    Returns:
        Dictionary containing analysis results, error message, or None
    """
    try:
        valid_messages, _ = get_valid_messages(time_filter)
        if not valid_messages:
            return None
        
        # Filter messages by this user
        user_id_str = str(member.id)
        messages_by_user = [msg for msg in valid_messages if msg['author_id'] == user_id_str]
        
        if not messages_by_user:
            return f'No messages found for user {member.display_name}.'
        
        # Extract content and analyse
        content_list = [msg['content'] for msg in messages_by_user]
        word_stats = analyse_word_stats(content_list)
        
        if not word_stats:
            return f'No analysable content found for user {member.display_name}.'
        
        # Get channel stats for this user
        active_channels = get_channel_stats(messages_by_user)
        
        # Find most recent message timestamp
        most_recent = max(
                (datetime.datetime.fromtimestamp(msg['timestamp'], tz=datetime.UTC) for msg in messages_by_user),
                default=None
        )
        
        # Calculate leaderboard position
        user_message_count = collections.Counter(msg['author_id'] for msg in valid_messages)
        active_users = [
            {'user': user, 'num_messages': count}
            for user, count in user_message_count.items()
        ]
        
        # Sort users by message count
        active_user_lb = sorted(
                active_users,
                key=lambda x: x['num_messages'],
                reverse=True
        )
        
        # Find user's position in leaderboard
        lb_position = next(
                (i for i, user in enumerate(active_user_lb, 1)
                 if user['user'] == user_id_str), 0
        )
        
        # Format most recent message timestamp
        formatted_time = (
            int(most_recent.timestamp())
            if most_recent else 'N/A'
        )
        
        return {
            'total_messages':           len(messages_by_user),
            'most_common_word':         word_stats['most_common_word'],
            'most_common_word_count':   word_stats['most_common_word_count'],
            'total_unique_words':       word_stats['total_unique_words'],
            'average_length':           word_stats['average_length'],
            'active_channels_lb':       active_channels,
            'active_users_lb_position': lb_position,
            'most_recent_message':      formatted_time,
        }
    except Exception as e:
        logger.error('Error during user message analysis: %s', e)
        return f'Error during analysis: {str(e)}'


async def format_analysis(ctx: CContext, graph: bool = False) -> None:
    """
    Format and send analysis results.

    Args:
        ctx: Discord command context
        graph: Whether to generate and send a graph
    """
    
    # Try to delete the command message
    await ctx.delete()
    # Parse time filter from message
    flag: str | None = ctx.message.content.split()[-1].replace('-', '')
    if flag not in ['w', 'd', 'h', 'il']:
        flag = None
    else:
        ctx.message.content = ctx.message.content.replace(f'-{flag}', '')
    
    # Send initial "Analysing..." message
    new_msg = await ctx.send('Analysing...')
    
    # Check if a user was specified
    if len(ctx.message.content.split()) > 1:
        try:
            member_id = utils.get_id_from_str(ctx.message.content.split()[1])
            member = await ctx.bot.fetch_user(member_id)
            
            if member is None:
                await new_msg.edit(content=f'User with ID {member_id} not found.')
                return
            
            await analyse_single_user_cmd(ctx, member, flag)
            await new_msg.delete()
            return
        
        except ValueError:
            await new_msg.edit(content='Invalid user ID format. Please provide a valid integer ID.')
            return
    
    # analyse all messages
    try:
        result = analyse_messages(ctx, flag)
        
        if isinstance(result, dict):
            guild = ctx.bot.get_guild(GUILD_ID)
            
            # Get top users and channels
            active_users_lb = copy.deepcopy(result['active_users_lb'])
            top_5_users = sorted(
                    active_users_lb,
                    key=lambda x: x['num_messages'],
                    reverse=True
            )[:5]
            
            top_5_channels = sorted(
                    result['active_channels_lb'],
                    key=lambda x: x['num_messages'],
                    reverse=True
            )[:5]
            
            # Replace user IDs with display names
            for user in top_5_users:
                user: dict = user  # type hinting
                user_id = int(user['user'].strip())
                
                # Try to get member from guild first
                guild_member: discord.Member | None = guild.get_member(user_id)
                if isinstance(guild_member, discord.Member):
                    user['user'] = guild_member.display_name
                elif guild_member is None:
                    # Fetch user if not in guild
                    try:
                        fetched_user = await ctx.bot.fetch_user(user_id)
                        user['user'] = fetched_user.display_name
                    except:
                        # Keep ID if fetch fails
                        pass
            
            # Format message
            msg = (
                f"{result['total_messages']} total messages analysed\n"
                f"Most common word: \"{result['most_common_word']}\" said {result['most_common_word_count']} times\n"
                f"({result['total_unique_words']} unique words, average length: {result['average_length']:.2f} "
                f"characters)\nTotal users: {result['total_users']}\n"
                f"Top 5 most active users:\n"
            )
            
            # Add top users
            for i, user in enumerate(top_5_users, start=1):
                msg += f"**{i}. {user['user']}** {user['num_messages']} messages\n"
            
            # Add top channels
            msg += '\nTop 5 most active channels:\n'
            for i, channel in enumerate(top_5_channels, start=1):
                channel: dict = channel  # type hinting
                msg += f"**{i}. {channel['channel']}** {channel['num_messages']} messages\n"
            
            # Send the message
            await new_msg.edit(content=msg)
            
            # Generate graph if requested
            if graph:
                await generate_user_activity_graph(ctx, result, guild)
        
        elif isinstance(result, str):
            await new_msg.edit(content=result)
    
    except Exception as e:
        logger.error('Error formatting analysis: %s', e)
        await ctx.send(f'Error during analysis: {e}')


async def generate_user_activity_graph(ctx: Context, result: dict[str, int | str | float | list[dict[str, str | int]]],
                                       guild: discord.Guild) -> None:
    """
    Generate and send a graph of user activity.

    Args:
        ctx: Discord command context
        result: Analysis results
        guild: Discord guild
    """
    try:
        # Get top 15 users
        top_15_users = sorted(
                result['active_users_lb'],
                key=lambda x: x['num_messages'],
                reverse=True
        )[:15]
        
        usernames = []
        message_counts = []
        
        # Process each user
        for user in top_15_users:
            user: dict = user  # type hinting
            user_id = int(user['user'].strip())
            
            # Try to get member from guild first
            discord_member: discord.Member | discord.User | None = guild.get_member(user_id)
            if discord_member is None:
                # Fetch user if not in guild
                try:
                    discord_member = await ctx.bot.fetch_user(user_id)
                except:
                    discord_member = None
            
            # Get display name
            display = user['user']
            if discord_member is not None:
                display = discord_member.display_name
            
            if not all(c in string.printable for c in display) and discord_member is not None:
                display = discord_member.name
            
            usernames.append(display)
            message_counts.append(user['num_messages'])
        
        # Reverse lists so users with most messages are at the top
        usernames = usernames[::-1]
        message_counts = message_counts[::-1]
        
        # Create the plot
        plt.figure(figsize=(10, 6), facecolor='#1f1f1f')
        ax = plt.gca()
        ax.set_facecolor('#2d2d2d')
        plt.barh(usernames, message_counts, color='#8a2be2')
        plt.xlabel('Number of Messages', color='white')
        plt.title('Top 15 Active Users', color='white')
        plt.tick_params(axis='both', colors='white')
        
        # Style the plot
        for spine in ax.spines.values():
            spine.set_color('#555555')
        plt.tight_layout()
        
        # Save and send the graph
        graph_file = 'top_active_users.png'
        plt.savefig(graph_file)
        plt.close()
        
        await ctx.send(file=discord.File(graph_file))
        
        # Clean up the file
        try:
            os.remove(graph_file)
        except:
            pass # Ignore if file deletion fails, we'd rather keep the bot running and clean up manually later
    
    except Exception as e:
        logger.error('Error generating graph: %s', e)
        await ctx.send(f'Error generating graph: {e}')


async def analyse_single_user_cmd(ctx: CContext, member: discord.User,
                                  time_filter: str | None = None) -> None:
    """
    Format and send analysis results for a single user.

    Args:
        ctx: Discord command context
        member: Discord user to analyse
        time_filter: Optional time filter
    """
    result = analyse_user_messages(member, time_filter)
    
    if isinstance(result, dict):
        # Sort channels by message count
        active_channels = sorted(
                result['active_channels_lb'],
                key=lambda x: x['num_messages'],
                reverse=True
        )
        
        # Determine how many channels to show
        num_channels = 5
        
        active_channels = active_channels[:num_channels]
        
        # Format message
        msg = (
            f"{result['total_messages']} messages found for **{member.name}**\n"
            f"Most common word: \"{result['most_common_word']}\" said {result['most_common_word_count']} times\n"
            f"({result['total_unique_words']} unique words, average length: {result['average_length']:.2f} "
            f"characters)\n"
            f"Leaderboard position: {result['active_users_lb_position']}\n"
            f"Most recent message sent at: <t:{result['most_recent_message']}>\n"
            f"Top {num_channels} most active channels:\n"
        )
        
        # Add channel information
        for i, channel in enumerate(active_channels, 1):
            channel: dict = channel  # type hinting
            msg += f"**{i}. {channel['channel']}** {channel['num_messages']} messages\n"
        
        await ctx.send(msg)
    
    elif isinstance(result, str):
        await ctx.send(result)
    
    else:
        await ctx.send('An error occurred during analysis.')


# ===== Voice Analysis Functions =====

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
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    if minutes > 0:
        return f"{int(minutes)}m {int(seconds)}s"
    return f"{int(seconds)}s"


def get_voice_statistics(include_left: bool = False, guild: discord.Guild = None) -> dict[str, list[dict[str, str | int]]] | None:
    """
    Retrieve voice statistics from MongoDB and calculate user and channel totals.
    
    Args:
        include_left: Whether to include users who have left the server
        guild: Discord guild, used to check if users are still in the server

    Returns:
        Dictionary containing voice statistics or None if no data
    """
    try:
        sessions = db_stuff.download_voice_sessions()
        
        if not sessions:
            return None
        
        # Calculate user statistics
        user_stats: dict[str, str | int | dict[str, int]] | None = {}
        for session in sessions:
            user_id = session.get('user_id')
            if not include_left and guild is not None:
                if guild.get_member(int(user_id)) is None:
                    continue
            user_name = session.get('user_global_name') or session.get('user_name')
            duration = session.get('duration_seconds', 0)
            
            if user_id not in user_stats:
                user_stats[user_id] = {
                    'name':          user_name,
                    'total_seconds': 0
                }
            
            user_stats[user_id]['total_seconds'] += duration
        
        # Calculate channel statistics
        channel_stats: dict[str, str | int | dict[str, int]] | None = {}
        for session in sessions:
            channel_id = session.get('channel_id')
            exists = discord.utils.get(guild.channels, id=int(channel_id)) if guild else None
            if not isinstance(exists, discord.VoiceChannel):
                continue
            channel_name = session.get('channel_name')
            duration = session.get('duration_seconds', 0)
            
            if channel_id not in channel_stats:
                channel_stats[channel_id] = {
                    'name':          channel_name,
                    'total_seconds': 0
                }
            
            channel_stats[channel_id]['total_seconds'] += duration
        
        # Sort statistics
        top_users = sorted(
                [{'id': user_id, 'name': data['name'], 'total_seconds': data['total_seconds']}
                 for user_id, data in user_stats.items()],
                key=lambda x: x['total_seconds'],
                reverse=True
        )
        
        top_channels = sorted(
                [{'id': channel_id, 'name': data['name'], 'total_seconds': data['total_seconds']}
                 for channel_id, data in channel_stats.items()],
                key=lambda x: x['total_seconds'],
                reverse=True
        )
        
        return {
            'users':    top_users[:15],  # Top 5 users
            'channels': top_channels[:15]  # Top 5 channels
        }
    
    except Exception as e:
        logger.error('Error retrieving voice statistics: %s', e)
        return None


def get_user_voice_statistics(user_id: str) -> dict[str, str | None | int | list[dict[str, Any]]] | None:
    """
    Retrieve voice statistics for a specific user.

    Args:
        user_id: Discord user ID

    Returns:
        Dictionary containing user voice statistics or None if no data
    """
    try:
        sessions = db_stuff.download_voice_sessions()
        
        if not sessions:
            return None
        
        # Filter sessions for this user
        user_sessions = [s for s in sessions if s.get('user_id') == user_id]
        
        if not user_sessions:
            return None
        
        # Get username
        user_name = user_sessions[0].get('user_global_name') or user_sessions[0].get('user_name')
        
        # Calculate total time
        total_seconds = sum(s.get('duration_seconds', 0) for s in user_sessions)
        
        # Calculate per-channel stats
        channel_stats = {}
        for session in user_sessions:
            channel_id = session.get('channel_id')
            channel_name = session.get('channel_name')
            duration = session.get('duration_seconds', 0)
            
            if channel_id not in channel_stats:
                channel_stats[channel_id] = {
                    'name':          channel_name,
                    'total_seconds': 0
                }
            
            channel_stats[channel_id]['total_seconds'] += duration
        
        # Sort channels by time
        top_channels = sorted(
                [{'id': channel_id, 'name': data['name'], 'total_seconds': data['total_seconds']}
                 for channel_id, data in channel_stats.items()],
                key=lambda x: x['total_seconds'],
                reverse=True
        )
        
        return {
            'user_id':       user_id,
            'user_name':     user_name,
            'total_seconds': total_seconds,
            'channels':      top_channels[:5]  # Top 5 channels
        }
    
    except Exception as e:
        logger.error('Error retrieving user voice statistics: %s', e)
        return None


async def voice_analysis(ctx: CContext, graph: bool = False, include_left: bool = False) -> None:
    """
    Generate voice activity statistics and send as a message.

    Args:
        ctx: Discord context
        graph: Whether to generate and send a graph
        include_left: Whether to include users who have left the server
    """
    guild: discord.Guild | None = None
    if not include_left:
        guild = ctx.bot.get_guild(GUILD_ID)
        
    stats = get_voice_statistics(include_left, guild)
    
    if not stats:
        await ctx.send("No voice activity data available.")
        return
    
    result = "**Voice Activity Statistics**\n\n"
    
    # Top users
    result += "**Top 5 Users by Voice Activity**\n"
    for i, user in enumerate(stats['users'][:5], 1):
        formatted_time = format_duration(user['total_seconds'])
        result += f"{i}. {user['name']}: {formatted_time}\n"
    
    result += "\n"
    
    # Top channels
    result += "**Top 5 Voice Channels by [Man Hours](https://en.wikipedia.org/wiki/Man-hour)**\n"
    for i, channel in enumerate(stats['channels'][:5], 1):
        formatted_time = format_duration(channel['total_seconds'])
        result += f"{i}. {channel['name']}: {formatted_time}\n"
    
    await ctx.send(result)
    if graph:
        try:
            await generate_voice_activity_graph(ctx, stats)
        except Exception as e:
            logger.error('Error generating voice activity graph: %s', e)
            await ctx.send(f'Error generating graph: {e}')


async def add_voice_analysis_for_user(ctx: CContext, member: discord.User) -> None:
    """
    Generate voice activity statistics for a specific user.

    Args:
        ctx: The Discord command context
        member: Discord user to analyse
    """
    stats = get_user_voice_statistics(str(member.id))
    
    if not stats:
        await ctx.send(f"No voice activity data available for {member.display_name}.")
        return
    
    formatted_total_time = format_duration(stats['total_seconds'])
    
    result = f"**Voice Activity for {stats['user_name']}**\n\n"
    result += f"**Total time in voice channels:** {formatted_total_time}\n\n"
    
    result += f"**Top {len(stats['channels'])} Most Used Voice Channels**\n"
    for i, channel in enumerate(stats['channels'], 1):
        if TYPE_CHECKING:
            channel: dict
        formatted_time = format_duration(channel['total_seconds'])
        try:
            channelobj = await ctx.bot.fetch_channel(channel['id'])
        except discord.NotFound:
            result += f"{i}. {channel['name']}: {formatted_time}\n"
            continue

        result += f"{i}. {channelobj.name}: {formatted_time}\n"
        
    
    await ctx.send(result)


async def format_voice_analysis(ctx: CContext, graph: bool = False) -> None:
    """
    Format and send voice analysis results.

    Args:
        ctx: Discord command context
        graph: Whether to generate and send a graph
    """
    include_left: bool = ctx.message.content.endswith('-il')
    # Try to delete the command message
    await ctx.delete()
    
    # Send initial "Analysing..." message
    new_msg: discord.Message = await ctx.send('Analysing voice statistics...')
    
    # Check if a user was specified
    if len(ctx.message.content.split()) > 1:
        try:
            member_id = utils.get_id_from_str(ctx.message.content.split()[1])
            member = await ctx.bot.fetch_user(member_id)
            
            if member is None:
                await new_msg.edit(content=f'User with ID {member_id} not found.')
                return
            
            await add_voice_analysis_for_user(ctx, member)
            await new_msg.delete()
            return
        
        except ValueError:
            await new_msg.edit(
                    content=f'Invalid user ID format. Please provide a valid integer ID. Provided: {ctx.message.content.split()[1]}'
            )
            return
    
    # No user specified, show general voice stats
    try:
        await voice_analysis(ctx, graph, include_left)
        await new_msg.delete()
    except Exception as e:
        logger.error('Error during voice analysis: %s', e)
        await ctx.send(f'Error during voice analysis: {e}')


async def generate_voice_activity_graph(ctx: CContext, stats: dict[str, list[dict[str, str | int]]]):
    """ Generate and
    send a graph of voice activity.
    Args:
        ctx: Discord command context
        stats: Voice analysis statistics
    """
    try:
        guild = ctx.guild
        if not guild:
            await ctx.send("Could not retrieve guild information.")
            return
    
        top_users = stats.get('users', [])
        if not top_users:
            await ctx.send("No user voice activity data to graph.")
            return
    
        usernames = []
        voice_time_hours = []
    
        for user_data in top_users:
            user_id_str = user_data.get('id')
            if not user_id_str:
                continue
    
            user_id = int(user_id_str)
            total_seconds = user_data.get('total_seconds', 0)
    
            display_name = user_data.get('name', str(user_id))
            try:
                member = guild.get_member(user_id) or await ctx.bot.fetch_user(user_id)
                if member:
                    display_name = member.display_name
                    if not all(c in string.printable for c in display_name):
                        display_name = member.name
            except discord.NotFound:
                pass  # Keep the stored name if user not found
            except Exception as e:
                logger.warning(f"Could not fetch user {user_id}: {e}")
            
                
            usernames.append(str(display_name))
            voice_time_hours.append(int(total_seconds) / 3600)
    
        if not usernames:
            await ctx.send("No valid user data to generate a graph.")
            return
    
        # Reverse for horizontal bar chart
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
    
        await ctx.send(file=discord.File(graph_file))
    
        try:
            os.remove(graph_file)
        except OSError as e:
            logger.warning('Could not remove graph file %s: %s', graph_file, e)
    
    except Exception as e:
        logger.error('Error generating voice activity graph: %s', e)
        await ctx.send(f'Error generating graph: {e}')
