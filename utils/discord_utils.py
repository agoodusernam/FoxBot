import asyncio
import datetime
import logging
import traceback
from typing import TypeVar

import discord
from cachetools import TTLCache

from command_utils.CContext import CoolBot

logger = logging.getLogger("discord")

K = TypeVar("K")
V = TypeVar("V")
T = TypeVar("T")

class TTLLRUCache[K, V](TTLCache[K, V]):
    def __getitem__(self, key: K) -> V:
        value = super().__getitem__(key)
        
        super().__delitem__(key)
        super().__setitem__(key, value)
        
        return value
    
    def get(self, key: K, default: T | None = None) -> V | T | None:
        try:
            return self[key]
        except KeyError:
            return default

_member_cache: TTLLRUCache[int, discord.Member | None] = TTLLRUCache(25, 300)
_user_cache: TTLLRUCache[int, discord.User | None] = TTLLRUCache(25, 300)
_channel_cache: TTLLRUCache[int, discord.abc.GuildChannel | discord.Thread | None] = TTLLRUCache(25, 300)
_api_lock: asyncio.Lock = asyncio.Lock()

async def _get_member_by_id(guild: discord.Guild, member_id: int) -> discord.Member | None:
    global _member_cache
    logger.debug(f"Getting member {member_id} by ID.")
    
    if member_id in _member_cache:
        logger.debug(f"Member {member_id} found in cache.")
        return _member_cache[member_id]
    
    member = guild.get_member(member_id)
    if member is not None:
        logger.debug(f"Member {member_id} found in discord cache.")
        _member_cache[member_id] = member
        return member
    
    try:
        logger.debug(f"Member {member_id} not found in discord cache. Fetching from API.")
        member = await guild.fetch_member(member_id)
        logger.debug(f"Member {member_id} found in API.")
        _member_cache[member_id] = member
        return member
    
    except discord.HTTPException:
        logger.debug(f"Member {member_id} not found in API.")
        _member_cache[member_id] = None
        return None

async def get_member_by_id(member_id: int, bot: CoolBot) -> discord.Member | None:
    guild: discord.Guild | None = bot.get_guild(bot.config.guild_id)
    if guild is None:
        logger.error("Guild not found when trying to get member by ID.")
        return None
    async with _api_lock:
        return await _get_member_by_id(guild, member_id)

async def _unsafe_get_member_by_id(member_id: int, bot: CoolBot) -> discord.Member | None:
    guild: discord.Guild | None = bot.get_guild(bot.config.guild_id)
    if guild is None:
        logger.error("Guild not found when trying to get member by ID.")
        return None

    return await _get_member_by_id(guild, member_id)

async def _get_user_by_id(
        user_id: int,
        bot: CoolBot,
    ) -> discord.User | None:
    global _user_cache
    logger.debug(f"Getting user {user_id} by ID.")
    
    if user_id in _user_cache:
        logger.debug(f"User {user_id} found in cache.")
        return _user_cache[user_id]
    
    user = bot.get_user(user_id)
    if user is not None:
        logger.debug(f"User {user_id} found in discord cache.")
        _user_cache[user_id] = user
        return user
    
    try:
        logger.debug(f"User {user_id} not found in discord cache. Fetching from API.")
        user = await bot.fetch_user(user_id)
        logger.debug(f"User {user_id} found in API.")
        _user_cache[user_id] = user
        return user
    
    except discord.HTTPException:
        logger.debug(f"User {user_id} not found in API.")
        _user_cache[user_id] = None
        return None

async def get_user_by_id(user_id: int, bot: CoolBot) -> discord.User | discord.Member | None:
    async with _api_lock:
        member = await get_member_by_id(user_id, bot)
    if member is not None:
        return member
    async with _api_lock:
        return await _unsafe_get_member_by_id(user_id, bot)

async def get_channel_by_id(channel_id: int, bot: CoolBot) -> discord.abc.GuildChannel | discord.Thread | None:
    async with _api_lock:
        return await _get_channel_by_id(channel_id, bot)


async def _get_channel_by_id(channel_id: int, bot: CoolBot) -> discord.abc.GuildChannel | discord.Thread | None:
    logger.debug(f"Getting channel {channel_id} by ID.")
    global _channel_cache
    if channel_id in _channel_cache:
        logger.debug(f"Channel {channel_id} found in cache.")
        return _channel_cache[channel_id]
    
    channel: discord.abc.GuildChannel | discord.Thread | discord.abc.PrivateChannel | None
    channel = bot.get_channel(channel_id)
    if isinstance(channel, discord.abc.PrivateChannel):
        logger.debug(f"Channel {channel_id} is a private channel.")
        _channel_cache[channel_id] = None
        return None
    
    if channel is not None:
        logger.debug(f"Channel {channel_id} found in bot cache.")
        _channel_cache[channel_id] = channel
        return channel
    
    logger.debug(f"Channel {channel_id} not found in bot cache. Fetching from API.")
    channel = await bot.fetch_channel(channel_id)
    if isinstance(channel, discord.abc.PrivateChannel) or channel is None:
        logger.debug(f"Channel {channel_id} not found in API, or is a private channel.")
        _channel_cache[channel_id] = None
        return None
    logger.debug(f"Channel {channel_id} found in API.")
    _channel_cache[channel_id] = channel
    return channel

async def safe_timeout(member: discord.Member, until: datetime.timedelta | None, reason: str) -> bool:
    try:
        await member.timeout(until, reason=reason)
        return True
    except discord.HTTPException:
        logger.error(f"Failed to timeout {member.display_name} ({member.id})")
        logger.error(traceback.format_exc())
        return False
