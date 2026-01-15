import datetime
import logging
import math
import random
from typing import Any, Generator

import cachetools.func
import discord
import discord.ext.commands

from cogs import api_cmds_utils

logger = logging.getLogger('discord')


def monday_generator() -> Generator[datetime.datetime, None, None]:
    now: datetime.datetime = datetime.datetime.now(datetime.UTC)
    days_until_monday: int = (7 - now.weekday()) % 7
    if days_until_monday == 0 and now.time() > datetime.time(0, 0):
        days_until_monday = 7
    next_monday: datetime.datetime = datetime.datetime.combine(now.date() + datetime.timedelta(days=days_until_monday), datetime.time(0, 0))
    
    while True:
        yield next_monday
        next_monday += datetime.timedelta(days=7)


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


@cachetools.func.ttl_cache(maxsize=1, ttl=60 * 60)
async def get_last_commit() -> None | tuple[int, str, dict[str, int]]:
    """
    Get the latest commit info from the FoxBot GitHub repository.
    Returns None if an error occurs.
    Else, it returns a tuple containing the commit timestamp, commit message, and change stats.
    """
    logger.debug('Getting latest commit info from GitHub...')
    
    response = await api_cmds_utils.fetch('https://api.github.com/repos/agoodusernam/FoxBot/commits/master')
    logger.debug(f'GitHub status code: {response.status}')
    logger.debug(f'GitHub response: {await response.text()}')
    if not response.ok:
        return None
    
    body: dict[str, Any] = await response.json()
    commit = body['commit']
    message = commit['message']
    date = commit['author']['date']
    stats = body['stats']
    change_stats: dict[str, int] = {'additions': stats['additions'], 'deletions': stats['deletions'], 'total': stats['total']}
    return round(datetime.datetime.fromisoformat(date).timestamp()), message, change_stats
