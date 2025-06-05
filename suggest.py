import discord


HELP_MSG = """Please post your suggestions for the <@1377636535968600135> in here using `f!suggest [suggestion]`.
If you have any additional comments, please use the thread.
✅: Implemented
💻: Working on it
❌: Will not add

👍: Vote for suggestion
"""

async def send_suggestion(client: "discord.Client", message: discord.Message) -> None:
	await message.delete()
	suggestion = message.content.replace('suggest', '').strip()

	channel: discord.TextChannel = client.get_channel(1379193761791213618)
	last_msges = [message async for message in channel.history(limit=10)]
	for message in last_msges:
		if HELP_MSG in message.content:
			await message.delete()

	try:
		embed = discord.Embed(title="Suggestion", description=suggestion, color=discord.Color.blue())
		embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
		embed.timestamp = message.created_at
		msg = await channel.send(embed=embed)
		await msg.add_reaction("👍")

		await msg.create_thread(
				name = f"suggestion-{message.author.display_name}",
		)

		await channel.send(HELP_MSG)
		print(f"Suggestion sent: {suggestion}")
	except discord.HTTPException as e:
		print(f"Failed to send suggestion: {e}")
	except Exception as e:
		print(f"An error occurred while sending suggestion: {e}")
