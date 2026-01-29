import datetime
import logging
import math
import random
from typing import Any, Generator

import cachetools  # type: ignore[import-untyped]
import discord
import discord.ext.commands
from dateutil.relativedelta import relativedelta, MO  # type: ignore[import-untyped]

from cogs import api_cmds_utils

logger = logging.getLogger('discord')

last_commit_cache: cachetools.TTLCache[None, tuple[int, str, dict[str, int]] | None] = cachetools.TTLCache(maxsize=1, ttl=300)

def monday_generator() -> Generator[datetime.datetime, None, None]:
    next_monday = datetime.datetime.now(tz=datetime.UTC) + relativedelta(days=+1, weekday=MO(+1))
    while True:
        yield next_monday
        next_monday = datetime.datetime.now(tz=datetime.UTC) + relativedelta(days=+1, weekday=MO(+1))


async def dice_roll(message: discord.Message) -> None:
    str_nums: list[str] = message.content.replace('f!dice', '').replace('f!roll', '').split()
    if len(str_nums) < 2:
        await message.delete()
        await message.channel.send('Please choose 2 numbers to roll the dice, e.g. `dice 1 6`')
        return
    try:
        nums: list[int] = list(map(int, str_nums))
    except ValueError:
        await message.delete()
        await message.channel.send('Please provide valid numbers for the dice roll, e.g. `dice 1 6`')
        return
    if nums[0] > nums[1]:
        num: int = random.randint(nums[1], nums[0])
    else:
        num = random.randint(nums[0], nums[1])
    if math.log10(num) > 1984:
        await message.channel.send('The output number would be too large to send in discord')
        return
    
    await message.channel.send(f'You rolled a {num}')
    return


async def cached_get_last_commit() -> None | tuple[int, str, dict[str, int]]:
    global last_commit_cache
    if last_commit_cache.get(None) is not None:
        return last_commit_cache[None]
    stuff = await _get_last_commit()
    last_commit_cache[None] = stuff
    return stuff
    
async def _get_last_commit() -> None | tuple[int, str, dict[str, int]]:
    """
    Get the latest commit info from the FoxBot GitHub repository.
    Returns None if an error occurs.
    Else, it returns a tuple containing the commit timestamp, commit message, and change stats.
    """
    logger.debug('Getting latest commit info from GitHub...')
    
    status, response = await api_cmds_utils.fetch_json('https://api.github.com/repos/agoodusernam/FoxBot/commits/master')
    logger.debug(f'GitHub status code: {status}')
    logger.debug(f'GitHub response: {response}')
    if status != 200:
        return None
    
    body: dict[str, Any] = response
    commit = body['commit']
    message = commit['message']
    date = commit['author']['date']
    stats = body['stats']
    change_stats: dict[str, int] = {'additions': stats['additions'], 'deletions': stats['deletions'], 'total': stats['total']}
    return round(datetime.datetime.fromisoformat(date).timestamp()), message, change_stats
