import asyncio
import gc
import json
import logging
import os
import sys
from typing import Any

import discord

from cogs import voice_events_utils
from command_utils.CContext import CContext, CoolBot
from utils import db_stuff

logger = logging.getLogger('discord')


async def aexec(func_name: str, context: CContext) -> Any:
    locs: dict[str, Any] = {}
    # noinspection PyUnusedLocal
    ctx = context
    # The "ctx" var exists, so 'ctx'. functions can be run from here.
    logger.debug(f'Running function: {func_name}')
    
    exec(f'async def __ex(): await discord.utils.maybe_coroutine({func_name})', globals(), locs)
    return await locs['__ex']()


def run_func(loop: asyncio.AbstractEventLoop, func_name: str, ctx: CContext) -> Any:
    asyncio.set_event_loop(loop)
    loop.run_until_complete(aexec(func_name, ctx))


async def shutdown(bot: CoolBot, update=False, restart=False) -> None:
    logger.info('Shutting down')
    await voice_events_utils.leave_all(bot)
    await db_stuff.disconnect()
    await bot.close()
    
    if update:
        logger.debug('Updating')
        os.system('git pull https://github.com/agoodusernam/FoxBot.git')
    
    if restart:
        logger.debug('Restarting')
        os.execv(sys.executable, ['python'] + sys.argv)


async def upload_all_history(channel: discord.TextChannel) -> None:
    logger.info(f'Deleting old messages from channel: {channel.name}, ID: {channel.id}')
    await db_stuff.del_channel_from_db(channel)
    logger.info(f'Starting to download all messages from channel: {channel.name}, ID: {channel.id}')
    messages = [message async for message in channel.history(limit=None)]
    logger.info(f'Downloaded {len(messages)} messages from channel: {channel.name}, ID: {channel.id}')
    bulk_data: list[dict[str, Any]] = []
    for i, message in enumerate(messages):
        if not isinstance(message.channel, discord.TextChannel):
            logger.info("Message channel is not a TextChannel, skipping...")
            continue
        
        has_attachment = False
        if message.attachments:
            has_attachment = True
        
        if message.reference is None:
            reply = None
        
        else:
            reply = str(message.reference.message_id)
        
        json_data = {
            'author':             message.author.name,
            'author_id':          str(message.author.id),
            'author_global_name': message.author.global_name,
            'content':            message.content,
            'reply_to':           reply,
            'HasAttachments':     has_attachment,
            'timestamp':          message.created_at.timestamp(),
            'id':                 str(message.id),
            'channel':            message.channel.name,
            'channel_id':         str(message.channel.id)
        }
        bulk_data.append(json_data)
    
    await db_stuff.bulk_send_messages(bulk_data)
    del bulk_data
    gc.collect()


async def upload_whole_server(guild: discord.Guild, author: discord.User | discord.Member, nolog_channels: list[int]) -> None:
    dm = await author.create_dm()
    await dm.send(f'Starting to download all messages from server: {guild.name}')
    await dm.send('--------------------------')
    for channel in guild.text_channels:
        if channel.id in nolog_channels:
            await dm.send(f'Skipping channel {channel.name} as it is in the nolog list')
            await dm.send('--------------------------')
            continue
        if channel.permissions_for(guild.me).read_message_history:
            await dm.send(f'Uploading messages from channel: {channel.name}')
            await upload_all_history(channel)
            await dm.send(f'Finished uploading all messages from channel: {channel.name}')
            await dm.send('--------------------------')
        else:
            await dm.send(f'Skipping channel {channel.name} due to insufficient permissions')
            await dm.send('--------------------------')
    
    logger.info('Finished uploading all messages from server:', guild.name)
    await dm.send(f'Finished uploading all messages from server: {guild.name}')
