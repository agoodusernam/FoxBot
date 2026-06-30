import datetime
import json
import logging
import os
import random
import re

import discord

from command_utils.analysis.text_analysis import DBMessage
from command_utils.CContext import CoolBot
from utils import db_stuff, utils

logger = logging.getLogger("discord")

url_regex = r"\b((?:https?|ftp|file):\/\/[-a-zA-Z0-9+&@#\/%?=~_|!:,.;]*[-a-zA-Z0-9+&@#\/%=~_|])"
url_pattern = re.compile(url_regex, re.IGNORECASE)


def url_in_string(string: str) -> bool:
    """
    Find a URL in a string using a regular expression.
    :param string: The string to search for a URL.
    :return: If a URL is found, return True; otherwise, return False.
    """
    global url_pattern
    
    match = url_pattern.search(string)
    return match is not None


async def landmine_explode(message: discord.Message, bot: CoolBot, forced: bool = False) -> None:
    assert not isinstance(message.author, discord.User)
    msgs: list[str] = [
        "Landmine exploded!",
        "You stepped in a claymore!",
        "A grenade exploded next to you!",
        "A rogue cluster bomblet went off!",
        "You tripped down some stairs. (How did you manage that one?)",
        "You went too close to a proximity mine.",
        "A tree fell on you. (What an idiot)",
        "You were hit by a car.",
        "You got struck by lightning.",
        "You fell off a cliff.",
        "You tripped on a rock and drowned in a puddle.",
        "A subspace tripmine appeared under you and detonated.",
        "You fell beyond the event horizon of a black hole and disappeared forever.",
        "nuke",
    ]
    msg: str = random.choice(msgs)
    if msg == "nuke":
        await message.author.timeout(datetime.timedelta(seconds=60), reason="Nuke exploded")
        await message.reply("A nuclear bomb went off below your feet! You cannot talk for 60 seconds.")
    else:
        await message.author.timeout(datetime.timedelta(seconds=10), reason="Landmine exploded")
        await message.reply(f"{msg} You cannot talk for 10 seconds.")
    
    if not forced:
        await message.channel.send(f"There are now {bot.landmine_channels[message.channel.id] - 1} traps left in this channel.")
        bot.landmine_channels[message.channel.id] -= 1
        if bot.landmine_channels[message.channel.id] == 0:
            del bot.landmine_channels[message.channel.id]
    else:
        left = bot.landmine_channels.get(message.channel.id, 0)
        await message.channel.send("f'There are now {left} traps left in this channel.'")
        bot.forced_landmines.remove(message.author.id)


async def check_landmine(message: discord.Message, bot: CoolBot) -> None:
    if isinstance(message.author, discord.User):
        return
    if message.author.id in bot.forced_landmines:
        await landmine_explode(message, bot, forced=True)
        return
    
    if message.channel.id not in bot.landmine_channels:
        return
    
    if (
        message.author.id in bot.config.admin_ids
        or message.author.id in bot.config.dev_ids
        or message.author.guild_permissions.administrator
    ):
        return
    
    if random.random() < 0.05:
        await landmine_explode(message, bot)


async def log_msg(message: discord.Message) -> bool:
    has_attachment: bool = bool(message.attachments)
    
    reply: str | None = None if message.reference is None else str(message.reference.message_id)
    
    json_data: DBMessage = {
        "author": message.author.name,
        "author_id": str(message.author.id),
        "author_global_name": message.author.global_name if message.author.global_name is not None else message.author.name,
        "content": message.content,
        "reply_to": reply,
        "HasAttachments": has_attachment,
        "timestamp": message.created_at.timestamp(),
        "id": str(message.id),
        "channel": message.channel.name if hasattr(message.channel, "name") and isinstance(message.channel.name, str) else "Unknown",
        "channel_id": str(message.channel.id),
        "edits": [],
    }
    
    if os.getenv("LOCAL_SAVE") == "True":
        with utils.make_file() as file:
            file.write(json.dumps(json_data, ensure_ascii=False) + "\n")
    
    logger.info(f"Message from {message.author.display_name} [#{message.channel}]: {message.content}")
    if has_attachment:
        if os.environ.get("LOCAL_IMG_SAVE") == "True":
            saved = await utils.save_attachments(message)
            logger.debug(f"Saved {saved} attachments for message {message.id}")
        else:
            for attachment in message.attachments:
                await db_stuff.send_attachment(message, attachment)
    
    return await db_stuff.send_message(json_data)


async def try_uid_to_discord_obj(uid: int, bot: CoolBot) -> discord.User | discord.Member | None:
    """
    Attempt to resolve a user ID to a display name.
    If the user's display name can't be found, return their ID as a string.
    """
    guild: discord.Guild | None = bot.get_guild(bot.config.guild_id)
    
    guild_member: discord.Member | None
    
    guild_member = guild.get_member(uid) if guild is not None else None
    
    if isinstance(guild_member, discord.Member):
        return guild_member
    
    try:
        fetched = await bot.fetch_user(uid)
        if isinstance(fetched, discord.User):
            return fetched
    
    except discord.NotFound, discord.HTTPException:
        pass
    
    return None


_channel_cache: dict[int, discord.abc.GuildChannel | discord.Thread | None] = {}


async def get_channel_by_id(channel_id: int, bot: CoolBot) -> discord.abc.GuildChannel | discord.Thread | None:
    global _channel_cache
    if channel_id in _channel_cache:
        return _channel_cache[channel_id]
    
    channel: discord.abc.GuildChannel | discord.Thread | discord.abc.PrivateChannel | None
    channel = bot.get_channel(channel_id)
    if isinstance(channel, discord.abc.PrivateChannel):
        _channel_cache[channel_id] = None
        return None
    
    if channel is not None:
        _channel_cache[channel_id] = channel
        return channel
    
    channel = await bot.fetch_channel(channel_id)
    if isinstance(channel, discord.abc.PrivateChannel) or channel is None:
        _channel_cache[channel_id] = None
        return None
    _channel_cache[channel_id] = channel
    return channel


async def post_log(message: discord.Message, bot: CoolBot) -> None:
    channel = await get_channel_by_id(1345300442376310885, bot)
    logger.debug(f"Posting log for message {message.id} in channel {channel.name if channel is not None else 'Unknown'}")
    msg: str = (
        f"Point and laugh! {message.author.mention} sent "
        + f"a message in <#{bot.config.ban_channel_id}> and has been timed out for a week! What an idiot."
    )
    if channel is None:
        logger.error("Public logs channel not found.")
        return
    await channel.send(msg)


def clear_channel_cache() -> None:
    global _channel_cache
    _channel_cache.clear()
