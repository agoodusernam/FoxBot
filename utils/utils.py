import datetime
import json
import os
import urllib.request
from io import TextIOWrapper
from pathlib import Path
from typing import Union

import discord


def get_id_from_str(u_id: str) -> int:
	u_id = u_id.replace("<", "")
	u_id = u_id.replace(">", "")
	u_id = u_id.replace("@", "")
	u_id = u_id.replace("#", "")
	return int(u_id)


def formatted_time() -> str:
	return datetime.datetime.now(datetime.timezone.utc).strftime('%d-%m-%Y_%H-%M-%S')

def formatted_today() -> str:
	return datetime.datetime.now(datetime.timezone.utc).strftime('%d-%m-%Y')


def make_file() -> 'TextIOWrapper':
	if not os.path.exists('../data'):
		os.makedirs('../data')
	if not os.path.exists('../data/attachments'):
		os.makedirs('../data/attachments')
	return open(f'data/{formatted_today()}.json', 'a+', encoding='utf-8')


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
		print('APOD directory does not exist, creating it.')
		apod_dir.mkdir(parents=True, exist_ok=True)

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

	if os.getenv('LOCAL_IMG_SAVE') is None:
		print('No LOCAL_IMG_SAVE found in environment variables. Defaulting to False.')
		os.environ['LOCAL_IMG_SAVE'] = 'False'

	if os.getenv('LOCAL_IMG_SAVE') not in ['True', 'False']:
		print('Invalid LOCAL_IMG_SAVE value. Please set it to True or False. Defaulting to False.')
		os.environ['LOCAL_IMG_SAVE'] = 'False'


def parse_utciso8601(date_str: str) -> datetime.datetime | None:
	"""
	Parses a UTC ISO 8601 date string into a datetime object.
	"""
	try:
		return datetime.datetime.fromisoformat(date_str)
	except ValueError as e:
		print(f'Error parsing date string "{date_str}": {e}')
		return None


def add_to_config(*, config: dict, key: str, key2: str = None, value: str | int) -> None:
	"""
	Adds a value to the config file under the specified key.
	"""
	if not key2:
		if isinstance(config.get(key), list):
			if value not in config[key]:
				config[key].append(value)
	else:
		if isinstance(config.get(key), dict):
			if key2 not in config[key]:
				config[key][key2] = value
			else:
				print(f'Key "{key2}" already exists in "{key}". Not adding again.')
				return
		elif isinstance(config.get(key), list):
			if value not in config[key]:
				config[key].append(value)
			else:
				print(f'Value "{value}" already exists in "{key}". Not adding again.')
				return

	if isinstance(config.get(key), (int, str, dict)):
		raise TypeError('Cannot add a value to a key that is not a list.')

	with open('config.json', 'w') as f:
		json.dump(config, f, indent=4)
		print(f'Config updated with key "{key}".')


def update_config(*, config: dict, key: str, key2=None, value: str | int) -> None:
	"""
	Updates the config file with a new value for the specified key.
	"""
	if key2:
		if isinstance(config[key], dict):
			config[key][key2] = value
		else:
			print(f'Key "{key}" is not a dictionary. Cannot update "{key2}".')
			return

	else:
		config[key] = value

	with open('config.json', 'w') as f:
		json.dump(config, f, indent=4)
		print(f'Config updated with key "{key}".')


def remove_from_config(*, config: dict, key: str, key2: str = None) -> None:
	"""
	Removes a key or a subkey from the config file.
	"""
	if key2:
		if isinstance(config.get(key), dict) and key2 in config[key]:
			del config[key][key2]
			print(f'Removed key "{key2}" from "{key}".')
		else:
			print(f'Key "{key}" is not a dictionary or does not contain "{key2}".')
	else:
		if key in config:
			del config[key]
			print(f'Removed key "{key}".')
		else:
			print(f'Key "{key}" does not exist in the config.')

	with open('config.json', 'w') as f:
		json.dump(config, f, indent=4)


def format_perms_overwrite(overwrite: discord.PermissionOverwrite) -> dict[str, Union[bool, None]]:
	perms: dict[str, Union[bool, None]] = {}
	for permission in overwrite:
		name = permission[0]
		value = permission[1]
		perms[name] = value

	return perms


def format_permissions(permissions: dict[discord.Role | discord.Member | discord.Object,
discord.PermissionOverwrite]) -> dict[str, dict[str, Union[bool, None]]]:
	formatted = {}

	for key in permissions:
		if isinstance(key, discord.Role):
			formatted[f'R{key.id}'] = format_perms_overwrite(permissions[key])
		elif isinstance(key, discord.Member):
			formatted[f'M{key.id}'] = format_perms_overwrite(permissions[key])
		else:
			formatted[f'O{key.id}'] = format_perms_overwrite(permissions[key])

	return formatted
