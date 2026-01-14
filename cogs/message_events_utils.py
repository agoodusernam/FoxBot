import datetime
import json
import logging
import os
import random
import re

import discord

from command_utils.CContext import CoolBot
from utils import utils, db_stuff

logger = logging.getLogger('discord')

regex = r'\b((?:https?|ftp|file):\/\/[-a-zA-Z0-9+&@#\/%?=~_|!:,.;]*[-a-zA-Z0-9+&@#\/%=~_|])'
url_pattern = re.compile(regex, re.IGNORECASE)


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
    try:
        msgs: list[str] = ["Landmine exploded!", "You stepped in a claymore!", "A grenade exploded next to you!",
                           "A rogue cluster bomblet went off!", "You tripped down some stairs. (How did you manage that one?)",
                           "You went too close to a proximity mine.", "A tree fell on you. (What an idiot.)",
                           "You were hit by a car.", "You got struck by lightning.", "You fell off a cliff.",
                           "You tripped on a rock and drowned in a puddle.",
                           "A subspace tripmine appeared under you and detonated.",
                           "You fell beyond the event horizon of a black hole and disappeared forever.",
                           "nuke"]
        msg: str = random.choice(msgs)
        if msg == "nuke":
            await message.author.timeout(datetime.timedelta(seconds=60), reason='Nuke exploded')
            await message.reply(f'A nuclear bomb went off below your feet! You cannot talk for 60 seconds.')
        else:
            await message.author.timeout(datetime.timedelta(seconds=10), reason='Landmine exploded')
            await message.reply(f'{msg} You cannot talk for 10 seconds.')
        
        if not forced:
            await message.channel.send(
                    f'There are now {bot.landmine_channels[message.channel.id] - 1} traps left in this channel.')
            bot.landmine_channels[message.channel.id] -= 1
            if bot.landmine_channels[message.channel.id] == 0:
                del bot.landmine_channels[message.channel.id]
        else:
            left = bot.landmine_channels.get(message.channel.id, 0)
            await message.channel.send(f'There are now {left} traps left in this channel.')
            bot.forced_landmines.remove(message.author.id)
    
    except Exception:
        pass


async def check_landmine(message: discord.Message, bot: CoolBot) -> None:
    if isinstance(message.author, discord.User):
        return
    if message.author.id in bot.forced_landmines:
        await landmine_explode(message, bot, forced=True)
        return
    
    if message.channel.id not in bot.landmine_channels.keys():
        return
    
    if (message.author.id in bot.config.admin_ids or message.author.id in bot.config.dev_ids or
            message.author.guild_permissions.administrator):
        return
    
    if random.random() < 0.05:  # 5% chance for a landmine to explode
        await landmine_explode(message, bot)


async def log_msg(message: discord.Message) -> bool:
    has_attachment: bool = bool(message.attachments)
    
    reply: str | None = None if message.reference is None else str(message.reference.message_id)
    
    json_data = {
        'author':             message.author.name,
        'author_id':          str(message.author.id),
        'author_global_name': message.author.global_name,
        'content':            message.content,
        'reply_to':           reply,
        'HasAttachments':     has_attachment,
        'timestamp':          message.created_at.timestamp(),
        'id':                 str(message.id),
        'channel':            message.channel.name if hasattr(message.channel, 'name') else 'Unknown',
        'channel_id':         str(message.channel.id)
    }
    
    if os.getenv('LOCAL_SAVE') == 'True':
        with utils.make_file() as file:
            file.write(json.dumps(json_data, ensure_ascii=False) + '\n')
    
    logger.info(f'Message from {message.author.display_name} [#{message.channel}]: {message.content}')
    if has_attachment:
        if os.environ.get('LOCAL_IMG_SAVE') == 'True':
            saved = await utils.save_attachments(message)
            logger.debug(f'Saved {saved} attachments for message {message.id}')
        else:
            for attachment in message.attachments:
                await db_stuff.send_attachment(message, attachment)
    
    return await db_stuff.send_message(json_data)
