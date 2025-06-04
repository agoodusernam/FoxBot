import datetime

import discord

import utils


async def rek(admin_ids: list[int], del_after: int, message: discord.Message, guild: discord.Guild) -> None:
	if message.author.id not in admin_ids:
		await message.channel.send('You are not allowed to use this command.', delete_after = del_after)
		await message.delete()
		return

	await message.delete()

	u_id = utils.get_id_from_msg(message)

	try:
		u_id = int(u_id)
	except ValueError:
		await message.channel.send('Invalid user ID format. Please provide a valid integer ID.',
		                           delete_after = del_after)
		return

	member = guild.get_member(u_id)

	if member is None:
		await message.channel.send(f'User with ID {u_id} not found.', delete_after = del_after)
		return

	await member.timeout(datetime.timedelta(days = 28), reason = 'get rekt nerd')
	await message.channel.send(f'<@{u_id}> has been rekt.', delete_after = del_after)
	return