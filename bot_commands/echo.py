import discord

async def echo(message: discord.Message, del_after: int, client: "discord.client") -> None:
	if not message.content:
		await message.channel.send('Nothing to echo.', delete_after=del_after)
		return

	msg = message.content.replace('echo', '', 1)

	# Send the message content back to the channel
	split_message = msg.split()
	channel = message.channel
	try:
		channel_id = int(split_message[0])
		channel = client.get_channel(channel_id)
		msg = msg.replace(str(channel_id), '', 1)
	except:
		pass

	await channel.send(msg)

	# Delete the original message
	await message.delete()