import os.path
import json
from typing import Union, Generator

import discord

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


async def hardlockdown(client, message: discord.Message) -> None:
	previous_perms: dict[int, dict[discord.Role | discord.Member | discord.Object, discord.PermissionOverwrite]] = {}

	for channel in message.guild.channels:
		pass
		# previous_perms[channel.id] = format_permissions(channel.overwrites)

	if os.path.exists("hardlockdown.txt"):
		os.rename("hardlockdown.txt", "hardlockdown_old.txt")

	with open('hardlockdown.txt', 'w') as file:
		json.dump(None, file, indent=4)
