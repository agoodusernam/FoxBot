import os
import random
from typing import Final, Any

import discord.ext.commands
import aiohttp
from aiohttp import ClientTimeout
from discord.ext.commands import Context

TIMEOUT: Final[float] = 5

session = aiohttp.ClientSession(timeout=ClientTimeout(total=TIMEOUT))

async def fetch_json(url: str, headers: dict[str, str] | None = None) -> tuple[int, dict[Any, Any]]:
    async with session.get(url, headers=headers) as response:
        return response.status, await response.json()


async def get_nasa_apod() -> dict[str, str]:
    api_key = os.getenv('NASA_API_KEY')
    
    url = f'https://api.nasa.gov/planetary/apod?api_key={api_key}'
    status, data = await fetch_json(url)
    
    if status != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch data from NASA API: {status}')
    
    return data


async def get_dog_pic(ctx: Context) -> None:
    url = 'https://dog.ceo/api/breeds/image/random'
    status, data = await fetch_json(url)
    
    if status != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch dog picture: {status}')
    
    if 'message' not in data:
        raise discord.ext.commands.CommandError('Unexpected response format from dog API')
    
    await ctx.send(data['message'])


async def get_fox_pic(ctx: Context) -> None:
    urls = ['https://randomfox.ca/floof/', 'https://api.sefinek.net/api/v2/random/animal/fox']
    url = random.choice(urls)
    status, data = await fetch_json(url)
    
    if status != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch fox picture: {status}')
    
    if 'image' in data:
        await ctx.send(data['image'])
        return
        
    if 'message' in data:
        await ctx.send(data['message'])
        return
    
    raise discord.ext.commands.CommandError('Unexpected response format from fox API')


async def get_cat_pic(ctx: Context) -> None:
    url = 'https://api.thecatapi.com/v1/images/search'
    
    api_key = os.getenv('CAT_API_KEY')
    if api_key is None:
        raise discord.ext.commands.CommandError('CAT_API_KEY environment variable not set')
    
    header: dict[str, str] = {'x-api-key': api_key, 'Content-Type': 'application/json'}
    status, data = await fetch_json(url, headers=header)
    
    if status != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch cat picture: {status}')
    
    if not data or 'url' not in data[0]:
        raise discord.ext.commands.CommandError('Unexpected response format from cat API')
    
    await ctx.send(data[0]['url'])


async def get_insult(ctx: Context) -> None:
    url = 'https://evilinsult.com/generate_insult.php?lang=en&type=json'
    status, data = await fetch_json(url)
    
    if status != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch insult: {status}')
    
    if 'insult' not in data:
        raise discord.ext.commands.CommandError('Unexpected response format from insult API')
    
    await ctx.send(data['insult'])


async def get_advice(ctx: Context) -> None:
    url = 'https://api.adviceslip.com/advice'
    status, data = await fetch_json(url)
    
    if status != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch advice: {status}')
    
    if 'slip' not in data or 'advice' not in data['slip']:
        raise discord.ext.commands.CommandError('Unexpected response format from advice API')
    
    await ctx.send(data['slip']['advice'])


async def get_joke(ctx: Context) -> None:
    url = 'https://v2.jokeapi.dev/joke/Any?blacklistFlags=racist,sexist'
    status, data = await fetch_json(url)
    
    if status != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch joke: {status}')
    
    if 'joke' not in data and ('setup' not in data or 'delivery' not in data):
        raise discord.ext.commands.CommandError('Unexpected response format from joke API')
    
    # Two-part joke format
    if 'setup' in data and 'delivery' in data:
        to_send = f'{data['setup']}\n{data['delivery']}'
    
    elif 'joke' in data:
        # Single joke format
        to_send = data['joke']
    else:
        raise discord.ext.commands.CommandError('Unexpected joke format from joke API')
    
    await ctx.send(to_send)


async def get_wyr(ctx: Context) -> None:
    url = 'https://api.truthordarebot.xyz/api/wyr'
    status, data = await fetch_json(url)
    
    if status != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch Would You Rather question: {status}')
    
    if 'question' not in data:
        raise discord.ext.commands.CommandError('Unexpected response format from Would You Rather API')
    
    await ctx.send(data['question'])


async def get_no(ctx: Context) -> None:
    url = "https://naas.isalman.dev/no"
    status, data = await fetch_json(url)
    
    if status != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch no: {status}')
    
    if "reason" not in data:
        raise discord.ext.commands.CommandError(f'Unexpected reason format from no API: {data}')
    
    await ctx.send(data["reason"])
