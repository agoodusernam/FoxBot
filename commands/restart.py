import os
import sys

import discord

from utils import db_stuff


async def restart(client: 'discord.Client') -> None:
	await client.close()
	db_stuff.disconnect()

	# run git pull to update the codebase, then restart the script
	os.system('git pull https://github.com/agoodusernam/DiscordStatBot.git')

	os.execv(sys.executable, ['python'] + sys.argv)
