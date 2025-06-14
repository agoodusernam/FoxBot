import os
import sys
from typing import Any

import discord

from utils import db_stuff


async def restart(client: 'discord.Client') -> None:
	await client.close()
	db_stuff.disconnect()

	# run git pull to update the codebase, then restart the script
	os.system('git pull https://github.com/agoodusernam/DiscordStatBot.git')

	os.execv(sys.executable, ['python'] + sys.argv)


async def upload_all_history(channel: discord.TextChannel, author: discord.Member) -> None:
	print('Deleting old messages from channel:', channel.name)
	db_stuff.del_channel_from_db(channel)
	print('Starting to download all messages from channel:', channel.name)
	messages = [message async for message in channel.history(limit=None)]
	print('Downloaded', len(messages), 'messages from channel:', channel.name)
	bulk_data: list[dict[str, Any]] = []
	for i, message in enumerate(messages):

		has_attachment = False
		if message.attachments:
			has_attachment = True

		if message.reference is None:
			reply = None

		else:
			reply = str(message.reference.message_id)

		json_data = {
			'author':             message.author.name,
			'author_id':          str(message.author.id),
			'author_global_name': message.author.global_name,
			'content':            message.content,
			'reply_to':           reply,
			'HasAttachments':     has_attachment,
			'timestamp':          message.created_at.isoformat(),
			'id':                 str(message.id),
			'channel':            message.channel.name,
			'channel_id':         str(message.channel.id)
		}
		bulk_data.append(json_data)

	db_stuff.bulk_send_messages(bulk_data)
	del bulk_data

	dm = await author.create_dm()
	await dm.send(f'Finished uploading all messages from channel: {channel.name}')

async def upload_whole_server(guild: discord.Guild, author: discord.Member, nolog_channels: list[int]) -> None:
	dm = await author.create_dm()
	await dm.send(f'Starting to download all messages from server: {guild.name}')
	await dm.send(' ')
	for channel in guild.text_channels:
		if channel.id in nolog_channels:
			await dm.send(f'Skipping channel {channel.name} as it is in the nolog list')
			await dm.send(' ')
			continue
		if channel.permissions_for(guild.me).read_message_history:
			await dm.send(f'Uploading messages from channel: {channel.name}')
			await upload_all_history(channel, author)
			await dm.send(f'Finished uploading messages from channel: {channel.name}')
			await dm.send(' ')
		else:
			await dm.send(f'Skipping channel {channel.name} due to insufficient permissions')
			await dm.send(' ')

	print('Finished uploading all messages from server:', guild.name)
	await dm.send(f'Finished uploading all messages from server: {guild.name}')
