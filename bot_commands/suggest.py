import os

import discord

HELP_MSG = '''Please post your suggestions for the <@1377636535968600135> in here using `f!suggest <suggestion>.
If you have any additional comments, please use the thread.
✅: Implemented
💻: Working on it
❌: Will not add

👍: Vote for suggestion
'''


async def send_suggestion(client: 'discord.Client', message: discord.Message) -> None:
	await message.delete()
	suggestion = message.content.replace('suggest', '').strip()

	channel: discord.TextChannel = client.get_channel(1379193761791213618)
	last_msges = [message async for message in channel.history(limit=10)]
	for message in last_msges:
		if HELP_MSG in message.content:
			await message.delete()

	try:
		embed = discord.Embed(title='Suggestion', description=suggestion, color=discord.Color.blue())
		embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
		embed.timestamp = message.created_at
		msg = await channel.send(embed=embed)
		await msg.add_reaction('👍')

		await msg.create_thread(
				name=f'suggestion-{message.author.display_name}',
		)

		msg = await channel.send(HELP_MSG)
		print(f'Suggestion sent: {suggestion}')
		await save_h_msg_id(client, msg)
	except discord.HTTPException as e:
		print(f'Failed to send suggestion: {e}')
	except Exception as e:
		print(f'An error occurred while sending suggestion: {e}')

async def save_h_msg_id(client: 'discord.Client', message: discord.Message) -> None:
	"""
	Saves the ID of the help message to a file.
	"""
	if os.path.exists('h_msg_id.txt'):
		with open('data/help_msg_id.txt', 'r') as f:
			old_id = f.read().strip()
			if old_id:
				try:
					old_message = client.get_channel(1379193761791213618).get_partial_message(int(old_id))
					if old_message:
						print(f'Deleting old help message ID: {old_id}')
						await old_message.delete()
				except discord.NotFound:
					print(f'Old help message ID {old_id} not found, skipping deletion.')
				except Exception as e:
					print(f'Error deleting old help message: {e}')
	with open('data/help_msg_id.txt', 'w') as f:
		f.write(str(message.id))
	print(f'Help message ID saved: {message.id}')
