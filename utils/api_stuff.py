import os
import random
import cachetools

import discord
import requests


@cachetools.cached(cache=cachetools.TTLCache(maxsize=8, ttl=3_600))  # Cache for 1 hour
def get_nasa_apod() -> dict[str, str]:
	api_key = os.getenv('NASA_API_KEY')

	url = f'https://api.nasa.gov/planetary/apod?api_key={api_key}'
	response = requests.get(url, timeout=5)

	if response.status_code != 200:
		raise Exception(f'Failed to fetch data from NASA API: {response.status_code}')

	return response.json()


async def get_dog_pic(message: discord.Message) -> None:
	url = 'https://dog.ceo/api/breeds/image/random'
	response = requests.get(url, timeout=5)

	if response.status_code != 200:
		raise Exception(f'Failed to fetch dog picture: {response.status_code}')

	data = response.json()
	if 'message' not in data:
		raise ValueError('Unexpected response format from dog API')

	await message.channel.send(data['message'])


async def get_fox_pic(message: discord.Message) -> None:
	url = 'https://randomfox.ca/floof/'
	response = requests.get(url, timeout=5)

	if response.status_code != 200:
		raise Exception(f'Failed to fetch fox picture: {response.status_code}')

	data = response.json()
	if 'image' not in data:
		raise ValueError('Unexpected response format from fox API')

	await message.channel.send(data['image'])


async def get_cat_pic(message: discord.Message) -> None:
	url = 'https://api.thecatapi.com/v1/images/search'

	header = {'x-api-key': os.getenv('CAT_API_KEY'), 'Content-Type': 'application/json'}
	response = requests.get(url, headers=header, timeout=5)

	if response.status_code != 200:
		raise Exception(f'Failed to fetch cat picture: {response.status_code}')

	data = response.json()
	if not data or 'url' not in data[0]:
		raise ValueError('Unexpected response format from cat API')

	await message.channel.send(data[0]['url'])


async def get_insult(message: discord.Message) -> None:
	url = 'https://evilinsult.com/generate_insult.php?lang=en&type=json'
	response = requests.get(url, timeout=5)

	if response.status_code != 200:
		raise Exception(f'Failed to fetch insult: {response.status_code}')

	data = response.json()
	if 'insult' not in data:
		raise ValueError('Unexpected response format from insult API')

	await message.channel.send(data['insult'])


async def get_advice(message: discord.Message) -> None:
	url = 'https://api.adviceslip.com/advice'
	response = requests.get(url, timeout=5)

	if response.status_code != 200:
		raise Exception(f'Failed to fetch advice: {response.status_code}')

	data = response.json()
	if 'slip' not in data or 'advice' not in data['slip']:
		raise ValueError('Unexpected response format from advice API')

	await message.channel.send(data['slip']['advice'])


async def get_joke(message: discord.Message) -> None:
	url = 'https://v2.jokeapi.dev/joke/Any?blacklistFlags=racist,sexist'
	response = requests.get(url, timeout=5)

	if response.status_code != 200:
		raise Exception(f'Failed to fetch joke: {response.status_code}')

	data = response.json()
	if 'joke' not in data and ('setup' not in data or 'delivery' not in data):
		raise ValueError('Unexpected response format from joke API')

	# Two-part joke format
	if 'setup' in data and 'delivery' in data:
		to_send = f'{data['setup']}\n{data['delivery']}'

	elif 'joke' in data:
		# Single joke format
		to_send = data['joke']
	else:
		raise ValueError('Unexpected joke format from joke API')

	await message.channel.send(to_send)


async def get_wyr(message: discord.Message) -> None:
	url = 'https://api.truthordarebot.xyz/api/wyr'
	response = requests.get(url, timeout=5)

	if response.status_code != 200:
		raise Exception(f'Failed to fetch Would You Rather question: {response.status_code}')

	data = response.json()
	if 'question' not in data:
		raise ValueError('Unexpected response format from Would You Rather API')

	await message.channel.send(data['question'])


def get_karma_pic() -> tuple[str, str] | None:
	karma_pics = [f for f in os.listdir('data/karma_pics') if os.path.isfile(os.path.join('data/karma_pics', f))]
	if not karma_pics:
		return None

	# Choose a random file
	chosen_pic = random.choice(karma_pics)
	file_path = f'data/karma_pics/{chosen_pic}'

	return file_path, chosen_pic
