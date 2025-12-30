import os
import random
import cachetools.func
import discord.ext.commands

from discord.ext.commands import Context
import requests


@cachetools.func.ttl_cache(maxsize=5, ttl=3600)  # Cache for 1 hour
def get_nasa_apod() -> dict[str, str]:
    api_key = os.getenv('NASA_API_KEY')
    
    url = f'https://api.nasa.gov/planetary/apod?api_key={api_key}'
    response = requests.get(url, timeout=5)
    
    if response.status_code != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch data from NASA API: {response.status_code}')
    
    return response.json()


async def get_dog_pic(ctx: Context) -> None:
    url = 'https://dog.ceo/api/breeds/image/random'
    response = requests.get(url, timeout=5)
    
    if response.status_code != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch dog picture: {response.status_code}')
    
    data = response.json()
    if 'message' not in data:
        raise discord.ext.commands.CommandError('Unexpected response format from dog API')
    
    await ctx.send(data['message'])


async def get_fox_pic(ctx: Context) -> None:
    urls = ['https://randomfox.ca/floof/', 'https://api.sefinek.net/api/v2/random/animal/fox']
    url = random.choice(urls)
    response = requests.get(url, timeout=5)
    
    if response.status_code != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch fox picture: {response.status_code}')
    
    data = response.json()
    if 'image' in data:
        await ctx.send(data['image'])
        return
        
    if 'message' in data:
        await ctx.send(data['message'])
        return
    
    raise discord.ext.commands.CommandError('Unexpected response format from fox API')


async def get_cat_pic(ctx: Context) -> None:
    url = 'https://api.thecatapi.com/v1/images/search'
    
    header = {'x-api-key': os.getenv('CAT_API_KEY'), 'Content-Type': 'application/json'}
    response = requests.get(url, headers=header, timeout=5)
    
    if response.status_code != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch cat picture: {response.status_code}')
    
    data = response.json()
    if not data or 'url' not in data[0]:
        raise discord.ext.commands.CommandError('Unexpected response format from cat API')
    
    await ctx.send(data[0]['url'])


async def get_insult(ctx: Context) -> None:
    url = 'https://evilinsult.com/generate_insult.php?lang=en&type=json'
    response = requests.get(url, timeout=5)
    
    if response.status_code != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch insult: {response.status_code}')
    
    data = response.json()
    if 'insult' not in data:
        raise discord.ext.commands.CommandError('Unexpected response format from insult API')
    
    await ctx.send(data['insult'])


async def get_advice(ctx: Context) -> None:
    url = 'https://api.adviceslip.com/advice'
    response = requests.get(url, timeout=5)
    
    if response.status_code != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch advice: {response.status_code}')
    
    data = response.json()
    if 'slip' not in data or 'advice' not in data['slip']:
        raise discord.ext.commands.CommandError('Unexpected response format from advice API')
    
    await ctx.send(data['slip']['advice'])


async def get_joke(ctx: Context) -> None:
    url = 'https://v2.jokeapi.dev/joke/Any?blacklistFlags=racist,sexist'
    response = requests.get(url, timeout=5)
    
    if response.status_code != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch joke: {response.status_code}')
    
    data = response.json()
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
    response = requests.get(url, timeout=5)
    
    if response.status_code != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch Would You Rather question: {response.status_code}')
    
    data = response.json()
    if 'question' not in data:
        raise discord.ext.commands.CommandError('Unexpected response format from Would You Rather API')
    
    await ctx.send(data['question'])


def get_karma_pic() -> tuple[str, str] | None:
    karma_pics = [f for f in os.listdir('data/karma_pics') if os.path.isfile(os.path.join('data/karma_pics', f))]
    if not karma_pics:
        return None
    
    # Choose a random file
    chosen_pic = random.choice(karma_pics)
    file_path = f'data/karma_pics/{chosen_pic}'
    
    return file_path, chosen_pic


async def get_no(ctx: Context) -> None:
    url = "https://naas.isalman.dev/no"
    response = requests.get(url, timeout=5)
    
    if response.status_code != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch no: {response.status_code}')
    
    data = response.json()
    
    if "reason" not in data:
        raise discord.ext.commands.CommandError(f'Unexpected reason format from no API: {data}')
    
    await ctx.send(data["reason"])
