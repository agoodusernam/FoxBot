import os
import sys
from typing import Any

import discord
from discord.ext import commands

from command_utils.checks import is_dev
from custom_logging import voice_log
from utils import db_stuff, utils


async def restart(client: 'discord.Client') -> None:
	await client.close()
	db_stuff.disconnect()

	# run git pull to update the codebase, then restart the script
	os.system('git pull https://github.com/agoodusernam/FoxBot.git')

	os.execv(sys.executable, ['python'] + sys.argv)


async def upload_all_history(channel: discord.TextChannel, author: discord.Member) -> None:
	print(f'Deleting old messages from channel: {channel.name}, ID: {channel.id}')
	db_stuff.del_channel_from_db(channel)
	print(f'Starting to download all messages from channel: {channel.name}, ID: {channel.id}')
	messages = [message async for message in channel.history(limit=None)]
	print(f'Downloaded {len(messages)} messages from channel: {channel.name}, ID: {channel.id}')
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
	await dm.send('--------------------------')
	for channel in guild.text_channels:
		if channel.id in nolog_channels:
			await dm.send(f'Skipping channel {channel.name} as it is in the nolog list')
			await dm.send('--------------------------')
			continue
		if channel.permissions_for(guild.me).read_message_history:
			await dm.send(f'Uploading messages from channel: {channel.name}')
			await upload_all_history(channel, author)
			await dm.send('--------------------------')
		else:
			await dm.send(f'Skipping channel {channel.name} due to insufficient permissions')
			await dm.send('--------------------------')

	print('Finished uploading all messages from server:', guild.name)
	await dm.send(f'Finished uploading all messages from server: {guild.name}')


class DevCommands(commands.Cog, name='Dev', command_attrs=dict(hidden=True, add_check=is_dev)):
	"""Developer commands for bot maintenance and management."""

	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@commands.command(name="restart",
					  brief="Restart the bot",
					  help="Dev only: Git pull and restart the bot instance")
	async def restart_cmd(self, ctx: discord.ext.commands.Context):
		if not isinstance(ctx.message.channel, discord.DMChannel):
			await ctx.message.delete()
		voice_log.leave_all(ctx.bot)
		await restart(ctx.bot)

	@commands.command(name="shutdown",
					  brief="Shutdown the bot",
					  help="Dev only: Shutdown the bot instance")
	async def shutdown(self, ctx: discord.ext.commands.Context):
		if not isinstance(ctx.message.channel, discord.DMChannel):
			await ctx.message.delete()
		await ctx.message.channel.send('Shutting down the bot...', delete_after=ctx.bot.del_after)
		print('Bot is shutting down...')
		voice_log.leave_all(ctx.bot)
		db_stuff.disconnect()
		await ctx.bot.close()

	@commands.command(name="add_admin",
					  brief="Add a user to the admin list",
					  help="Dev only: Add a user to the admin list",
					  usage="add_admin <user_id/mention>")
	async def add_admin(self, ctx: discord.ext.commands.Context, u_id: str):
		if not isinstance(ctx.message.channel, discord.DMChannel):
			await ctx.message.delete()

		try:
			if u_id is None:
				raise ValueError
			u_id = utils.get_id_from_str(u_id)
		except ValueError:
			await ctx.message.channel.send('Invalid user ID format. Please provide a valid integer ID.',
										   delete_after=ctx.bot.del_after)
			return
		if u_id in ctx.bot.admin_ids:
			await ctx.message.channel.send(f'User with ID {u_id} is already an admin.',
										   delete_after=ctx.bot.del_after)
			return
		if u_id in ctx.bot.blacklist_ids['ids']:
			await ctx.message.channel.send(f'User with ID {u_id} is blacklisted. Please unblacklist them first.',
										   delete_after=ctx.bot.del_after)
			return

		ctx.bot.admin_ids.append(u_id)
		utils.add_to_config(config=ctx.bot.config, key='admin_ids', value=u_id)

		await ctx.message.channel.send(f'User with ID {u_id} has been added to the admin list.',
									   delete_after=ctx.bot.del_after)

	@commands.command(name="remove_admin",
					  brief="Remove a user from the admin list",
					  help="Dev only: Remove a user from the admin list",
					  usage="remove_admin <user_id/mention>")
	async def remove_admin(self, ctx: discord.ext.commands.Context, u_id: str):
		if not isinstance(ctx.message.channel, discord.DMChannel):
			await ctx.message.delete()

		try:
			if u_id is None:
				raise ValueError
			u_id = utils.get_id_from_str(u_id)
		except ValueError:
			await ctx.message.channel.send('Invalid user ID format. Please provide a valid integer ID.',
										   delete_after=ctx.bot.del_after)
			return
		if u_id not in ctx.bot.admin_ids:
			await ctx.message.channel.send(f'User with ID {u_id} is not an admin.', delete_after=ctx.bot.del_after)
			return
		ctx.bot.admin_ids.remove(u_id)
		utils.remove_from_config(config=ctx.bot.config, key='admin_ids')

		await ctx.message.channel.send(f'User with ID {u_id} has been removed from the admin list.',
									   delete_after=ctx.bot.del_after)

	@commands.command(name="upload_all_history",
					  brief="Upload all messages from a server",
					  help="Dev only: Upload all messages from a specific guild to the database",
					  usage="upload_all_history")
	async def upload_all_history(self, ctx: discord.ext.commands.Context):
		if not isinstance(ctx.message.channel, discord.DMChannel):
			await ctx.message.delete()

		nolog_channels = [1299640499493273651, 1329366175796432898, 1329366741909770261, 1329366878623236126,
						  1329367139018215444, 1329367314671472682, 1329367677940006952]

		await upload_whole_server(ctx.guild, ctx.author, nolog_channels)

	@commands.command(name="maintenance_mode",
					  brief="Toggle maintenance mode",
					  help="Dev only: Toggle maintenance mode for the bot",
					  usage="maintenance_mode <on/off>")
	async def maintenance_mode(self, ctx: discord.ext.commands.Context, mode: str):
		if not isinstance(ctx.message.channel, discord.DMChannel):
			await ctx.message.delete()

		if mode.lower() not in ['on', 'off']:
			await ctx.message.channel.send('Please specify "on" or "off" for maintenance mode.',
										   delete_after=ctx.bot.del_after)
			return

		ctx.bot.maintenance_mode = mode.lower() == 'on'

		status = 'enabled' if ctx.bot.maintenance_mode else 'disabled'
		await ctx.message.channel.send(f'Maintenance mode has been {status}.', delete_after=ctx.bot.del_after)


async def setup(bot):
	await bot.add_cog(DevCommands(bot))
