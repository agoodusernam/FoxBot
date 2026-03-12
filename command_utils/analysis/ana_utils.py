import discord

from command_utils.CContext import CoolBot


async def try_resolve_uid(uid: int, bot: CoolBot) -> str:
    """
    Attempt to resolve a user ID to a display name.
    If the user's display name can't be found, return their ID as a string.
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
            return fetched.display_name
    
    except (discord.NotFound, discord.HTTPException):
        pass
    
    return str(uid)


async def try_resolve_channel_id(channel_id: str, guild: discord.Guild | None = None) -> str:
    if guild is None:
        return channel_id
    
    channel = guild.get_channel(int(channel_id))
    return channel.name if channel else channel_id
