import collections
import copy
import datetime
import logging
import os
import string
import traceback
from typing import Any, Literal, Mapping, NotRequired, TypedDict

import discord
from matplotlib import pyplot as plt

from command_utils.CContext import CContext
from command_utils.analysis.ana_utils import try_resolve_channel_id, try_resolve_uid
from utils import db_stuff

logger = logging.getLogger('discord')


class DBMessageBase(TypedDict):
    author: str
    author_id: str  # Will always be a number
    author_global_name: str
    content: str
    reply_to: str | None  # Will be the id of the message this is replying to, or None if not replying
    HasAttachments: bool
    id: str  # The message ID will ideally always be a number
    channel: str
    channel_id: str  # Will always be a number
    edits: NotRequired[list[str]]
    _id: NotRequired[Any]  # The database internal ID


class DBMessage(DBMessageBase):
    timestamp: float


class DatetimeDBMessage(DBMessageBase):
    timestamp: datetime.datetime


class WordStats(TypedDict):
    most_common_word: str
    most_common_word_count: int
    total_unique_words: int
    average_length: float


class ChannelMessageStats(TypedDict):
    channel_id: str
    num_messages: int


class UserMessageStats(TypedDict):
    user_id: str
    num_messages: int
    display_name: NotRequired[str]


class MessageAnalysisResult(TypedDict):
    total_messages: int
    total_valid_messages: int
    most_common_word: str
    most_common_word_count: int
    total_unique_words: int
    average_length: float
    active_users_lb: list[UserMessageStats]
    active_channels_lb: list[ChannelMessageStats]
    total_users: int


class UserMessageAnalysisResult(TypedDict):
    total_messages: int
    most_common_word: str
    most_common_word_count: int
    total_unique_words: int
    average_length: float
    active_channels_lb: list[ChannelMessageStats]
    active_users_lb_position: int
    most_recent_message: int | Literal['N/A']


EXCLUDED_USER_IDS = ['1107579143140413580']
TIME_FILTERS = {
    'w': ('week', datetime.timedelta(days=7)),
    'd': ('day', datetime.timedelta(days=1)),
    'h': ('hour', datetime.timedelta(hours=1))
}


def check_required_message_keys(message: Mapping[str, Any]) -> bool:
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
        'timestamp', 'channel', 'channel_id', 'id'
    }
    return all(key in message for key in required_keys)


def to_dbm(message: dict[Any, Any] | DBMessage) -> DBMessage:
    return DBMessage(
            author=message['author'],
            author_id=message['author_id'],
            author_global_name=message['author_global_name'],
            content=message['content'],
            reply_to=message['reply_to'],
            HasAttachments=message['HasAttachments'],
            timestamp=message['timestamp'],
            channel=message['channel'],
            channel_id=message['channel_id'],
            id=message['id'],
            edits=message.get('edits', []),
            _id=message.get('_id', None)
        )


async def remove_invalid_messages(messages: list[DBMessage | dict[str, Any]] | None) -> list[DBMessage]:
    valid_messages: list[DBMessage] = []
    if messages is None:
        return valid_messages
    
    for message in messages:
        if check_required_message_keys(message):
            valid_messages.append(to_dbm(message))
            
        else:
            logger.warning(f'Removing invalid message with ID {message.get("_id", "unknown")}')
            await db_stuff.delete_message(message['_id'])
    
    return valid_messages


async def get_valid_messages(flag: str | None = None, ctx: CContext | None = None) -> tuple[list[DBMessage], int]:
    """
    Download and validate messages from the database.

    Args:
        flag: Optional time filter - 'w' for last week, 'd' for last day,
                    'h' for last hour, or None for all messages
        ctx: Discord command context, used to get the guild for user validation

    Returns:
        Tuple containing a list of valid messages and the total message count
    """
    # Download all messages from database
    messages: list[DBMessage] | None = await db_stuff.cached_download_all()  # type: ignore
    if messages is None:
        return [], 0
    total_messages: int = len(messages)
    guild: discord.Guild | None = None
    if ctx is not None:
        guild = ctx.bot.get_guild(1081760248433492140)
    
    if not messages:
        logger.warning('No messages found or failed to connect to the database.')
        return [], 0
    
    all_messages: list[DBMessage] = [msg for msg in messages if msg['author_id'] not in EXCLUDED_USER_IDS]
    
    valid_messages: list[DBMessage] = await remove_invalid_messages(all_messages)
    
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
    
    logger.info(f'Total valid messages: {len(valid_messages)}')
    logger.info(f'Total messages in database: {total_messages}')
    return valid_messages, total_messages


def analyse_word_stats(content_list: list[str]) -> WordStats | None:
    """
    Analyse word statistics from a list of message content.

    Args:
        content_list: List of message content strings

    Returns:
        Dictionary containing word statistics
    """
    if not content_list:
        return None
    
    # Extract and normalise all words
    all_words = [word.lower() for msg in content_list for word in msg.split() if word]
    if not all_words:
        return None
    
    # Calculate statistics
    word_count = collections.Counter(all_words)
    most_common_word, most_common_count = word_count.most_common(1)[0]
    unique_words = set(all_words)
    
    # Calculate average word length
    avg_length = sum(len(word) for word in unique_words) / len(unique_words) if unique_words else 0
    
    return WordStats(
            most_common_word=most_common_word,
            most_common_word_count=most_common_count,
            total_unique_words=len(unique_words),
            average_length=avg_length,
    )


def get_channel_stats(messages: list[DBMessage]) -> list[ChannelMessageStats]:
    """
    Get statistics about channel activity.

    Args:
        messages: List of message dictionaries

    Returns:
        List of dictionaries containing channel statistics
    """
    if not messages:
        return []
    
    channel_counts = collections.Counter(msg['channel_id'] for msg in messages)
    return [
        {'channel_id': channel_id, 'num_messages': count}
        for channel_id, count in channel_counts.items()
        if count > 0
    ]


async def analyse_messages(ctx: CContext, time_filter: str | None = None) -> MessageAnalysisResult | str:
    """
    analyse all messages in the database.

    Args:
        time_filter: Optional time filter - 'w' for last week, 'd' for last day,
                    'h' for last hour, or None for all messages
        ctx: Discord command context, used to get the guild for user validation

    Returns:
        Dictionary containing analysis results or error message
    """
    valid_messages, total_messages = await get_valid_messages(time_filter, ctx=ctx)
    if not valid_messages:
        return 'No valid messages found to analyse.'
    
    # Extract message content
    content_list = [message['content'] for message in valid_messages]
    
    # analyse word statistics
    word_stats: WordStats | None = analyse_word_stats(content_list)
    if not word_stats:
        return 'No valid content to analyse.'
    
    # Get user message counts
    user_message_count = collections.Counter(msg['author_id'] for msg in valid_messages)
    active_users: list[UserMessageStats] = [
        UserMessageStats(user_id=user_id, num_messages=count)
        for user_id, count in user_message_count.items()
    ]
    
    # Get channel stats
    active_channels = get_channel_stats(valid_messages)
    
    return MessageAnalysisResult(
            total_messages=total_messages,
            total_valid_messages=len(valid_messages),
            most_common_word=word_stats['most_common_word'],
            most_common_word_count=word_stats['most_common_word_count'],
            total_unique_words=word_stats['total_unique_words'],
            average_length=word_stats['average_length'],
            active_users_lb=active_users,
            active_channels_lb=active_channels,
            total_users=len(user_message_count),
    )


async def analyse_user_messages(member: discord.User, time_filter: str | None = None) -> UserMessageAnalysisResult | str:
    """
    analyse messages from a specific user.

    Args:
        member: Discord user to analyse
        time_filter: Optional time filter - 'w' for last week, 'd' for last day,
                    'h' for last hour, or None for all messages

    Returns:
        Dictionary containing analysis results, error message, or None
    """
    valid_messages, _ = await get_valid_messages(time_filter)
    if not valid_messages:
        return 'No valid messages found to analyse.'
    
    user_id_str = str(member.id)
    messages_by_user = [msg for msg in valid_messages if msg['author_id'] == user_id_str]
    
    if not messages_by_user:
        return f'No messages found for user {member.display_name}.'
    
    content_list = [msg['content'] for msg in messages_by_user]
    word_stats = analyse_word_stats(content_list)
    
    if not word_stats:
        return f'No analysable content found for user {member.display_name}.'
    
    active_channels = get_channel_stats(messages_by_user)
    
    # Find most recent message timestamp
    most_recent: datetime.datetime | None = max(
            (datetime.datetime.fromtimestamp(msg['timestamp'], tz=datetime.UTC) for msg in messages_by_user),
            default=None,
    )
    
    # Calculate leaderboard position
    user_message_count = collections.Counter(msg['author_id'] for msg in valid_messages)
    active_users: list[UserMessageStats] = [
        {'user_id': user, 'num_messages': count}
        for user, count in user_message_count.items()
    ]
    
    # Sort users by message count
    active_user_lb = sorted(
            active_users,
            key=lambda x: x['num_messages'],
            reverse=True,
    )
    
    # Find user's position in leaderboard
    lb_position = next(
            (i for i, user in enumerate(active_user_lb, 1)
             if user['user_id'] == user_id_str), 0,
    )
    
    return UserMessageAnalysisResult(
            total_messages=len(messages_by_user),
            most_common_word=word_stats['most_common_word'],
            most_common_word_count=word_stats['most_common_word_count'],
            total_unique_words=word_stats['total_unique_words'],
            average_length=word_stats['average_length'],
            active_channels_lb=active_channels,
            active_users_lb_position=lb_position,
            most_recent_message=int(most_recent.timestamp()) if most_recent else 'N/A',
    )


async def format_analysis(ctx: CContext, graph: bool = False, to_analyse: discord.Object | None = None, flag: str | None = '') -> None:
    """
    Format and send analysis results.

    Args:
        ctx: Discord command context
        graph: Whether to generate and send a graph
        to_analyse: The user to analyse
        flag: Optional time filter - 'w' for last week, 'd' for last day, etc.
    """
    # TODO: Make the filtering less dumb
    
    # Parse time filter from message
    valid_flags = ['-w', '-d', '-h', '-il']
    if flag:
        if flag.lower() not in valid_flags:
            await ctx.send(f'Invalid flag. Flag should be one of {valid_flags}.')
        else:
            ctx.message.content = ctx.message.content.replace(flag, '')
            flag = flag.lower().replace("-", "")
    
    new_msg = await ctx.send('Analysing...')
    
    # Check if a user was specified
    if to_analyse:
        try:
            to_ana_user = await ctx.bot.fetch_user(to_analyse.id)
            
        except discord.NotFound:
            await ctx.send("The input is not be a valid user.")
            return
        
        await analyse_single_user_cmd(ctx, to_ana_user, flag)
        await new_msg.delete()
        return
    
    # Analyse all messages
    guild: discord.Guild | None = ctx.bot.get_guild(ctx.bot.config.guild_id)
    if guild is None:
        await new_msg.edit(content='Guild not found.')
        logger.error(f'Guild not found. ID: {ctx.bot.config.guild_id}')
        return
    
    result = await analyse_messages(ctx, flag)
    
    if isinstance(result, str):
        await new_msg.edit(content=result)
        return
    
    # Get top users and channels
    active_users_lb: list[UserMessageStats] = copy.deepcopy(result['active_users_lb'])
    top_5_users: list[UserMessageStats] = sorted(
            active_users_lb,
            key=lambda x: x['num_messages'],
            reverse=True,
    )[:5]
    
    top_5_channels: list[ChannelMessageStats] = sorted(
            result['active_channels_lb'],
            key=lambda x: x['num_messages'],
            reverse=True,
    )[:5]
    
    activity_ratio: str = ""
    if guild.member_count and flag != 'il':
        activity_ratio = f"({round((result['total_users'] / guild.member_count) * 100, 2)}% activity)"
    
    msg = (
        f"{result['total_messages']} total messages analysed\n" +
        f"Most common word: \"{result['most_common_word']}\" said {result['most_common_word_count']} times\n" +
        f"({result['total_unique_words']} unique words, average length: {result['average_length']:.2f} characters)\n"
        f"Total users: {result['total_users']} {activity_ratio}\n"
        f"On average every active user has sent {round(result['total_valid_messages'] / result['total_users'], 2)} messages\n"
        f"Top 5 most active users:\n"
    )
    
    # Add top users
    for i, user in enumerate(top_5_users, start=1):
        msg += f"**{i}. {await try_resolve_uid(int(user['user_id']), ctx.bot)}** {user['num_messages']} messages\n"
    
    # Add top channels
    msg += '\nTop 5 most active channels:\n'
    for i, channel in enumerate(top_5_channels, start=1):
        msg += f"**{i}. {await try_resolve_channel_id(channel['channel_id'], guild)}** {channel['num_messages']} messages\n"
    
    # Send the message
    await new_msg.edit(content=msg)
    
    # Generate graph if requested
    if graph:
        await generate_user_activity_graph(ctx, result, guild)


async def generate_user_activity_graph(ctx: CContext, result: MessageAnalysisResult, guild: discord.Guild) -> None:
    """
    Generate and send a graph of user activity.

    Args:
        ctx: Discord command context
        result: Analysis results
        guild: Discord guild
    """
    # Get top 15 users
    top_15_users = sorted(
            result['active_users_lb'],
            key=lambda x: x['num_messages'],
            reverse=True)[:15]
    
    usernames: list[str] = []
    message_counts: list[int] = []
    
    for user in top_15_users:
        user_id = int(user['user_id'].strip())
        
        # Try to get member from guild first
        discord_member: discord.Member | discord.User | None = guild.get_member(user_id)
        if discord_member is None:
            # Fetch user if not in guild
            try:
                discord_member = await ctx.bot.fetch_user(user_id)
            except (discord.NotFound, discord.HTTPException):
                discord_member = None
        
        # Get display name
        display = user['user_id']
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
    
    except FileNotFoundError:
        pass
    
    except OSError:
        logger.warning(f'Error deleting graph file {graph_file}: {traceback.format_exc()}')
        # Ignore if file deletion fails, we'd rather keep the bot running and clean up manually later


async def analyse_single_user_cmd(ctx: CContext, member: discord.User,
        time_filter: str | None = None) -> None:
    """
    Format and send analysis results for a single user.

    Args:
        ctx: Discord command context
        member: Discord user to analyse
        time_filter: Optional time filter
    """
    result = await analyse_user_messages(member, time_filter)
    if isinstance(result, str):
        await ctx.send(result)
        return
    
    # Sort channels by message count
    active_channels = sorted(
            result['active_channels_lb'],
            key=lambda x: x['num_messages'],
            reverse=True,
    )
    
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
        f"**Top {num_channels} most active channels**\n"
    )
    
    # Add channel information
    for i, channel in enumerate(active_channels, 1):
        msg += f"{i}. <#{channel['channel_id']}> {channel['num_messages']} messages\n"
    
    await ctx.send(msg)
