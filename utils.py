import datetime
import os
import urllib.request
from pathlib import Path

import discord


async def send_image(message: discord.Message, file_path: str | Path, file_name: str) -> None:
	if not os.path.exists(file_path):
		print(f'File {file_path} does not exist.')
		return

	try:
		file = discord.File(file_path, filename=file_name)
		embed = discord.Embed()
		embed.set_image(url=f'attachment://{file_name}')
		await message.channel.send(file=file, embed=embed)

		print(f'Sent file: {file_path}')
	except discord.HTTPException as e:
		print(f'Failed to send file {file_path}: {e}')
	except Exception as e:
		print(f'An error occurred while sending file {file_path}: {e}')


def get_id_from_msg(message: discord.Message) -> str:
	u_id: str | int = message.content.split()[-1]
	u_id = u_id.replace('@', '').strip()
	u_id = u_id.replace('<', '')
	u_id = u_id.replace('>', '')
	return u_id


def formatted_time() -> str:
	return datetime.datetime.now(datetime.timezone.utc).strftime('%d-%m-%Y_%H-%M-%S')


def make_file(name: str = 'messages'):
	if not os.path.exists('data'):
		os.makedirs('data')
	if not os.path.exists('data/attachments'):
		os.makedirs('data/attachments')
	return open(f'data/{name}.json', 'a+', encoding='utf-8')


def make_empty_file(path: str | Path):
	if not os.path.exists(path):
		with open(path, 'x'):
			pass


async def save_attachments(message: discord.Message):
	for attachment in message.attachments:
		file_path = Path(os.path.abspath(f'data/attachments/{formatted_time()}_{attachment.filename}'))
		make_empty_file(file_path)

		await attachment.save(file_path)
		print(f'Saved attachment: {file_path}')


def download_from_url(path: str | Path, url: str):
	with urllib.request.urlopen(url) as f:
		pic = f.read()

	with open(path, 'wb') as file:
		file.write(pic)

	print(f'Downloaded file from {url} to {path}')
	return None


def clean_up_APOD():
	"""Cleans up old APOD images from the data directory."""
	apod_dir = Path('nasa/')
	if not apod_dir.exists():
		print('APOD directory does not exist.')
		return

	for file in apod_dir.iterdir():
		if file.is_file() and file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
			try:
				file.unlink()
				print(f'Deleted old APOD image: {file.name}')
			except Exception as e:
				print(f'Failed to delete {file.name}: {e}')


def check_env_variables():
	if not os.getenv('MONGO_URI'):
		print('No MONGO_URI found in environment variables. Please set it to connect to a database.')
		os.environ['LOCAL_SAVE'] = 'True'

	if not os.getenv('NASA_API_KEY'):
		print('No NASA_API_KEY found in environment variables. Please set it to fetch NASA pictures.')

	if not os.getenv('CAT_API_KEY'):
		print('No CAT_API_KEY found in environment variables. Please set it to fetch cat pictures.')

	if not os.getenv('LOCAL_SAVE'):
		print('No LOCAL_SAVE found in environment variables. Defaulting to False.')
		os.environ['LOCAL_SAVE'] = 'False'

	if os.getenv('LOCAL_SAVE') not in ['True', 'False']:
		print('Invalid LOCAL_SAVE value. Please set it to True or False. Defaulting to False.')
		os.environ['LOCAL_SAVE'] = 'False'
