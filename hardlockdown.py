import os.path
import json

import discord


async def hardlockdown(client, message: discord.Message) -> None:
	previous_perms: dict[int, dict[discord.Role | discord.Member | discord.Object, discord.PermissionOverwrite]] | None = None

	for channel in message.guild.channels:
		previous_perms[channel.id] = channel.overwrites

	if os.path.exists("hardlockdown.txt"):
		os.rename("hardlockdown.txt", "hardlockdown_old.txt")

	with open('hardlockdown.txt', 'w') as file:
		json.dump(previous_perms, file, indent=4)
