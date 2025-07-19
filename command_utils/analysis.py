import collections
import copy
import datetime
import logging
import os
from typing import Any

import discord
import matplotlib.pyplot as plt
from discord.ext.commands import Context

from utils import db_stuff, utils

# Configure logging
logger = logging.getLogger(__name__)

# Constants
EXCLUDED_USER_IDS = ['1107579143140413580']
GUILD_ID = 1081760248433492140
TIME_FILTERS = {
    'w': ('week', datetime.timedelta(days=7)),
    'd': ('day', datetime.timedelta(days=1)),
    'h': ('hour', datetime.timedelta(hours=1))
}


def check_valid_syntax(message: dict[str, Any]) -> bool:
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


def get_valid_messages(time_filter: str = None) -> tuple[list[dict[str, str]], int]:
    """
    Download and validate messages from the database.

    Args:
        time_filter: Optional time filter - 'w' for last week, 'd' for last day, 
                    'h' for last hour, or None for all messages

    Returns:
        Tuple containing a list of valid messages and the total message count
    """
    try:
        # Download all messages from database
        messages = db_stuff.download_all()
        total_messages = len(messages)
        
        if not messages:
            logger.warning('No messages found or failed to connect to the database.')
            return [], 0
        
        # Filter out excluded users
        all_messages = [msg for msg in messages if msg['author_id'] not in EXCLUDED_USER_IDS]
        
        # Validate messages and remove invalid ones
        valid_messages = []
        for message in all_messages:
            if check_valid_syntax(message):
                valid_messages.append(message)
            else:
                db_stuff.delete_message(message['_id'])
        
        # Apply time filter if specified
        if time_filter in TIME_FILTERS:
            filter_name, time_delta = TIME_FILTERS[time_filter]
            time_ago = discord.utils.utcnow() - time_delta
            
            valid_messages = [
                msg for msg in valid_messages
                if utils.parse_utciso8601(msg['timestamp']) >= time_ago
            ]
            logger.info(f'Applied {filter_name} filter: {len(valid_messages)} messages')
        
        logger.info(f'Total valid messages: {len(valid_messages)}')
        logger.info(f'Total messages in database: {total_messages}')
        return valid_messages, total_messages
    
    except Exception as e:
        logger.error(f"Error retrieving messages: {e}")
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


def get_channel_stats(messages: list[dict[str, str]]) -> list[dict[str, str | int]]:
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


def analyse_messages(time_filter: str = None) -> dict[str, int | str | float | list[dict[str, str | int]]] | str:
    """
    analyse all messages in the database.

    Args:
        time_filter: Optional time filter - 'w' for last week, 'd' for last day, 
                    'h' for last hour, or None for all messages

    Returns:
        Dictionary containing analysis results or error message
    """
    try:
        valid_messages, total_messages = get_valid_messages(time_filter)
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
        active_users = [
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
        logger.error(f'Error during message analysis: {e}')
        return f'Error during analysis: {str(e)}'


def analyse_user_messages(member: discord.User, time_filter: str = None) -> dict[str, int | str | float | list[
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
                (utils.parse_utciso8601(msg['timestamp']) for msg in messages_by_user),
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
                 if user['user'] == user_id_str),
                0
        )
        
        # Format most recent message timestamp
        formatted_time = (
            f"{most_recent:%H:%M:%S} on the {most_recent:%d.%m.%Y}"
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
        logger.error(f'Error during user message analysis: {e}')
        return f'Error during analysis: {str(e)}'


async def format_analysis(ctx: Context, graph: bool = False) -> None:
    """
    Format and send analysis results.

    Args:
        ctx: Discord command context
        graph: Whether to generate and send a graph
    """
    message = ctx.message
    
    # Try to delete the command message
    try:
        await message.delete()
    except discord.Forbidden:
        pass
    
    # Parse time filter from message
    flag = message.content.split()[-1].replace('-', '')
    if flag not in ['w', 'd', 'h', 'all']:
        flag = None
    else:
        message.content = message.content.replace(f'-{flag}', '')
    
    # Send initial "Analysing..." message
    new_msg = await message.channel.send('Analysing...')
    
    # Check if a user was specified
    if len(message.content.split()) > 1:
        try:
            member_id = utils.get_id_from_str(message.content.split()[1])
            member = await ctx.bot.fetch_user(member_id)
            
            if member is None:
                await new_msg.edit(content=f'User with ID {member_id} not found.')
                return
            
            await analyse_single_user_cmd(message, member, flag)
            await new_msg.delete()
            return
        
        except ValueError:
            await new_msg.edit(content='Invalid user ID format. Please provide a valid integer ID.')
            return
    
    # analyse all messages
    try:
        result = analyse_messages(flag)
        
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
                member = guild.get_member(user_id)
                if isinstance(member, discord.Member):
                    user['user'] = member.display_name
                elif member is None:
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
                await generate_user_activity_graph(ctx, result, guild, message)
        
        elif isinstance(result, str):
            await new_msg.edit(content=result)
    
    except Exception as e:
        logger.error(f"Error formatting analysis: {e}")
        await ctx.send(f'Error during analysis: {e}')


async def generate_user_activity_graph(ctx: Context, result: dict[str, int | str | float | list[dict[str, str | int]]],
                                       guild: discord.Guild, message: discord.Message) -> None:
    """
    Generate and send a graph of user activity.

    Args:
        ctx: Discord command context
        result: Analysis results
        guild: Discord guild
        message: Original command message
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
            discord_member = guild.get_member(user_id)
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
            
            # Clean name for display
            clean_name = ''.join(e for e in display if e.isalnum())
            usernames.append(clean_name)
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
        
        await message.channel.send(file=discord.File(graph_file))
        
        # Clean up the file
        try:
            os.remove(graph_file)
        except:
            pass
    
    except Exception as e:
        logger.error(f"Error generating graph: {e}")
        await ctx.send(f'Error generating graph: {e}')


async def analyse_single_user_cmd(message: discord.Message, member: discord.User,
                                  time_filter: str = None) -> None:
    """
    Format and send analysis results for a single user.

    Args:
        message: Discord message
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
        if time_filter == 'all':
            num_channels = len(result['active_channels_lb'])
            active_channels = active_channels[:num_channels]
        else:
            active_channels = active_channels[:5]
        
        # Format message
        msg = (
            f"{result['total_messages']} messages found for **{member.name}**\n"
            f"Most common word: \"{result['most_common_word']}\" said {result['most_common_word_count']} times\n"
            f"({result['total_unique_words']} unique words, average length: {result['average_length']:.2f} "
            f"characters)\n"
            f"Leaderboard position: {result['active_users_lb_position']}\n"
            f"Most recent message sent at: {result['most_recent_message']}\n"
            f"Top {num_channels} most active channels:\n"
        )
        
        # Add channel information
        for i, channel in enumerate(active_channels, 1):
            channel: dict = channel  # type hinting
            msg += f"**{i}. {channel['channel']}** {channel['num_messages']} messages\n"
        
        await message.channel.send(msg)
    
    elif isinstance(result, str):
        await message.channel.send(result)
    
    else:
        await message.channel.send('An error occurred during analysis.')


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
    elif minutes > 0:
        return f"{int(minutes)}m {int(seconds)}s"
    else:
        return f"{int(seconds)}s"


def get_voice_statistics() -> dict[str, list[dict[str, str | int]]] | None:
    """
    Retrieve voice statistics from MongoDB and calculate user and channel totals.

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
            'users':    top_users[:5],  # Top 5 users
            'channels': top_channels[:5]  # Top 5 channels
        }
    
    except Exception as e:
        logger.error(f"Error retrieving voice statistics: {e}")
        return None


def get_user_voice_statistics(user_id: str) -> dict[str, str | int | list[dict[str, str | int]]] | None:
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
        logger.error(f"Error retrieving user voice statistics: {e}")
        return None


async def voice_analysis(message: discord.Message) -> None:
    """
    Generate voice activity statistics and send as a message.

    Args:
        message: Discord message
    """
    stats = get_voice_statistics()
    
    if not stats:
        await message.channel.send("No voice activity data available.")
        return
    
    result = "**Voice Activity Statistics**\n\n"
    
    # Top users
    result += "**Top 5 Users by Voice Activity**\n"
    for i, user in enumerate(stats['users'], 1):
        formatted_time = format_duration(user['total_seconds'])
        result += f"{i}. {user['name']}: {formatted_time}\n"
    
    result += "\n"
    
    # Top channels
    result += "**Top 5 Voice Channels by [Man Hours](https://en.wikipedia.org/wiki/Man-hour)**\n"
    for i, channel in enumerate(stats['channels'], 1):
        formatted_time = format_duration(channel['total_seconds'])
        result += f"{i}. {channel['name']}: {formatted_time}\n"
    
    await message.channel.send(result)


async def add_voice_analysis_for_user(message: discord.Message, member: discord.User) -> None:
    """
    Generate voice activity statistics for a specific user.

    Args:
        message: Discord message
        member: Discord user to analyse
    """
    stats = get_user_voice_statistics(str(member.id))
    
    if not stats:
        await message.channel.send(f"No voice activity data available for {member.display_name}.")
        return
    
    formatted_total_time = format_duration(stats['total_seconds'])
    
    result = f"**Voice Activity for {stats['user_name']}**\n\n"
    result += f"**Total time in voice channels:** {formatted_total_time}\n\n"
    
    result += f"**Top {len(stats['channels'])} Most Used Voice Channels**\n"
    for i, channel in enumerate(stats['channels'], 1):
        channel: dict = channel  # type hinting
        formatted_time = format_duration(channel['total_seconds'])
        result += f"{i}. {channel['name']}: {formatted_time}\n"
    
    await message.channel.send(result)


async def format_voice_analysis(ctx: Context) -> None:
    """
    Format and send voice analysis results.

    Args:
        ctx: Discord command context
    """
    message = ctx.message
    
    # Try to delete the command message
    try:
        await message.delete()
    except discord.Forbidden:
        pass
    
    # Send initial "Analysing..." message
    new_msg = await message.channel.send('Analysing voice statistics...')
    
    # Check if a user was specified
    if len(message.content.split()) > 1:
        try:
            member_id = utils.get_id_from_str(message.content.split()[1])
            member = await ctx.bot.fetch_user(member_id)
            
            if member is None:
                await new_msg.edit(content=f'User with ID {member_id} not found.')
                return
            
            await add_voice_analysis_for_user(message, member)
            await new_msg.delete()
            return
        
        except ValueError:
            await new_msg.edit(
                    content=f'Invalid user ID format. Please provide a valid integer ID. Provided: {message.content.split()[1]}'
            )
            return
    
    # No user specified, show general voice stats
    try:
        await voice_analysis(message)
        await new_msg.delete()
    except Exception as e:
        logger.error(f"Error during voice analysis: {e}")
        await message.channel.send(f'Error during voice analysis: {e}')
