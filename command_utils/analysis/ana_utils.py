import discord

from command_utils.CContext import CoolBot
from utils import db_stuff


async def _resolve_deleted_uid(uid: int) -> str:
    """
    Resolve a deleted user's name from their most recent stored message.

    Returns the latest recorded global name (which already falls back to the
    username at write time), or the ID as a string if no message exists.
    """
    messages = await db_stuff.get_many_from_db(
        'messages',
        {'author_id': str(uid)},
        sort_by='timestamp',
        direction='desc',
        limit=1,
    )
    if not messages:
        return str(uid)
    
    latest = messages[0]
    return latest.get('author_global_name') or latest.get('author') or str(uid)


async def try_resolve_uid(uid: int, bot: CoolBot) -> str:
    """
    Attempt to resolve a user ID to a display name.
    
    Deleted users (whose name surfaces as ``deleted_user_*``) are resolved to
    their latest stored name instead. If the display name can't be found,
    return their ID as a string.
    """
    guild: discord.Guild | None = bot.get_guild(bot.config.guild_id)
    
    guild_member: discord.Member | None
    
    if guild is not None:
        guild_member = guild.get_member(uid)
        if guild_member is not None:
            return guild_member.display_name
    
    try:
        fetched = await bot.fetch_user(uid)
        if isinstance(fetched, discord.User):
            if fetched.name.startswith('deleted_user_'):
                return await _resolve_deleted_uid(uid)
            return fetched.display_name
    
    except (discord.NotFound, discord.HTTPException):
        pass
    
    return str(uid)


async def try_resolve_channel_id(channel_id: str, guild: discord.Guild | None = None) -> str:
    if guild is None:
        return channel_id
    
    channel = guild.get_channel(int(channel_id))
    return channel.name if channel else channel_id
