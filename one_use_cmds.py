from typing import Any

import discord

import db_stuff


async def upload_all_history(message: discord.Message) -> None:
	channel = message.channel

	messages = [message async for message in channel.history(oldest_first=True)]
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
			"author":             message.author.name,
			"author_id":          str(message.author.id),
			"author_global_name": message.author.global_name,
			"content":            message.content,
			"reply_to":           reply,
			"HasAttachments":     has_attachment,
			"timestamp":          message.created_at.isoformat(),
			"id":                 str(message.id),
			"channel_id":            str(message.channel.id)
		}
		bulk_data.append(json_data)
		if i % 100 == 0:
			db_stuff.bulk_send_messages(bulk_data)
			bulk_data = []
			print("Bulk uploaded 100 messages")
			print(f"{len(messages) - i} messages remaining")
