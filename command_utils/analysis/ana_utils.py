import discord

from command_utils.CContext import CoolBot
from utils import db_stuff, discord_utils


async def _resolve_deleted_uid(uid: int) -> str:
    """
    Resolve a deleted user"s name from their most recent stored message.

    Returns the latest recorded global name (which already falls back to the
    username at write time), or the ID as a string if no message exists.
    """
    messages = await db_stuff.get_many_from_db(
        "messages",
        {"author_id": str(uid)},
        sort_by="timestamp",
        direction="desc",
        limit=1,
    )
    if not messages:
        return str(uid)
    
    latest = messages[0]
    return latest.get("author_global_name") or latest.get("author") or str(uid)


async def user_id_to_display_name(uid: int, bot: CoolBot) -> str:
    """
    Attempt to resolve a user ID to a display name.
    
    Deleted users (whose name surfaces as ``deleted_user_*``) are resolved to
    their latest stored name instead. If the display name can't be found,
    return their ID as a string.
    """
    user = await discord_utils.get_user_by_id(uid, bot)
    return user.display_name if user else await _resolve_deleted_uid(uid)


async def try_resolve_channel_id(channel_id: str, guild: discord.Guild | None = None) -> str:
    if guild is None:
        return channel_id
    
    channel = guild.get_channel(int(channel_id))
    return channel.name if channel else channel_id
