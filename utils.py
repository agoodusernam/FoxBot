import datetime
import os
from pathlib import Path

import discord


def get_id_from_msg(message: discord.Message) -> str:
	u_id: str | int = message.content.split()[-1]
	u_id = u_id.replace('@', '').strip()
	u_id = u_id.replace('<', '')
	u_id = u_id.replace('>', '')
	return u_id


def formatted_time() -> str:
	return datetime.datetime.now(datetime.timezone.utc).strftime("%d-%m-%Y_%H-%M-%S")


def make_file(name :str ="messages"):
	if not os.path.exists('data'):
		os.makedirs('data')
	if not os.path.exists('data/attachments'):
		os.makedirs('data/attachments')
	return open(f'data/{name}.json', 'a+', encoding = 'utf-8')


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
