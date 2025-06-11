import datetime
import json
import os
from typing import Union

import discord

import utils.utils as utils


async def rek(admin_ids: list[int], del_after: int, message: discord.Message, guild: discord.Guild) -> None:
	if message.author.id not in admin_ids:
		await message.channel.send('You are not allowed to use this command.', delete_after=del_after)
		await message.delete()
		return

	if not isinstance(message.channel, discord.DMChannel):
		await message.delete()

	u_id = utils.get_id_from_msg(message)

	try:
		u_id = int(u_id)
	except ValueError:
		await message.channel.send('Invalid user ID format. Please provide a valid integer ID.',
		                           delete_after=del_after)
		return

	member = guild.get_member(u_id)

	if member is None:
		await message.channel.send(f'User with ID {u_id} not found.', delete_after=del_after)
		return

	await member.timeout(datetime.timedelta(days=28), reason='get rekt nerd')
	await message.channel.send(f'<@{u_id}> has been rekt.', delete_after=del_after)
	return

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


async def hardlockdown(message: discord.Message) -> None:
	previous_perms: dict[int, dict[str, dict[str, Union[bool, None]]]] = {}

	for channel in message.guild.channels:
		previous_perms[channel.id] = format_permissions(channel.overwrites)

	if os.path.exists('hardlockdown.txt'):
		os.rename('hardlockdown.txt', 'hardlockdown_old.txt')

	with open('hardlockdown.txt', 'w') as file:
		json.dump(previous_perms, file, indent=4)
