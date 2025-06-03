import discord

async def send_suggestion(client: "discord.Client", message: discord.Message) -> None:
	"""
	Sends a suggestion message to the channel.

	Args:
		message (discord.Message): The original message.
		client (discord.Client): A Discord client instance.
	"""
	await message.delete()
	suggestion = message.content.replace('suggest', '').strip()
	try:
		embed = discord.Embed(title="Suggestion", description=suggestion, color=discord.Color.blue())
		embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
		embed.timestamp = message.created_at
		channel: discord.TextChannel = client.get_channel(1379193761791213618)
		msg = await channel.send(embed=embed)
		await msg.add_reaction("👍")

		await msg.create_thread(
				name = f"suggestion-{message.author.display_name}",
		)


		print(f"Suggestion sent: {suggestion}")
	except discord.HTTPException as e:
		print(f"Failed to send suggestion: {e}")
	except Exception as e:
		print(f"An error occurred while sending suggestion: {e}")
