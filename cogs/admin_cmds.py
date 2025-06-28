import datetime
import json
import os
from typing import Union

import discord
from discord.ext import commands
from discord.utils import get

import utils.utils as utils
from command_utils import analysis
from command_utils.checks import is_admin


def save_perms(ctx: discord.ext.commands.Context) -> None:
	previous_perms: dict[int, dict[str, dict[str, Union[bool, None]]]] = {}

	for channel in ctx.message.guild.channels:
		previous_perms[channel.id] = utils.format_permissions(channel.overwrites)

	if os.path.exists('hardlockdown.txt'):
		os.rename('hardlockdown.txt', 'hardlockdown_old.txt')

	with open('hardlockdown.txt', 'w') as file:
		json.dump(previous_perms, file, indent = 4)


class AdminCmds(commands.Cog, name = 'Admin', command_attrs = dict(hidden = True, add_check = is_admin)):
	"""Admin commands for managing the server and users."""

	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@commands.command(name = "rek",
					  brief = "Absolutely rek a user",
					  help = "Admin only: Timeout a user for 28 days and add them to blacklist",
					  usage = "rek <user_id/mention>")
	async def rek(self, ctx: discord.ext.commands.Context, u_id: str) -> None:
		del_after = ctx.bot.del_after

		if not isinstance(ctx.message.channel, discord.DMChannel):
			await ctx.message.delete()

		try:
			if u_id is None:
				raise ValueError
			u_id = utils.get_id_from_str(u_id)
		except ValueError:
			await ctx.send('Invalid user ID format. Please provide a valid integer ID.',
						   delete_after = del_after)
			return

		member = ctx.guild.get_member(u_id)

		if member is None:
			await ctx.send(f'User with ID {u_id} not found.', delete_after = del_after)
			return

		await member.timeout(datetime.timedelta(days = 28), reason = 'get rekt nerd')
		await ctx.send(f'<@{u_id}> has been rekt.', delete_after = del_after)
		return

	@commands.command(name = "hardlockdown",
					  brief = "Lock down the entire server",
					  help = "Admin only: Timeout all non-admin users for 28 days and add them to blacklist")
	async def hard_lockdown(self, ctx: discord.ext.commands.Context):
		if not isinstance(ctx.message.channel, discord.DMChannel):
			await ctx.message.delete()
		# await admin_cmds.hardlockdown(ctx.message)

		for member in ctx.guild.members:
			if member.id in ctx.bot.admin_ids:
				continue

			if member.id not in ctx.bot.blacklist_ids['ids']:
				ctx.bot.blacklist_ids['ids'].append(member.id)

		for member in ctx.guild.members:
			if member.id not in ctx.bot.admin_ids:
				try:
					await member.timeout(datetime.timedelta(days = 28), reason = 'Hard lockdown initiated by admin')
				except Exception as e:
					print(f'Error during hard lockdown for user {member.id}: {e}')
					continue

		await ctx.message.channel.send(
				'Hard lockdown initiated. All non-admin users have been timed out for 28 days and added to the blacklist.',
				delete_after = ctx.bot.del_after)

	@commands.command(name = "unhardlockdown",
					  brief = "Unlock the server from hard lockdown",
					  help = "Admin only: Remove timeouts and blacklist from all users")
	async def unhard_lockdown(self, ctx: discord.ext.commands.Context):
		if not isinstance(ctx.message.channel, discord.DMChannel):
			await ctx.message.delete()
		guild: discord.Guild = ctx.guild
		for member in guild.members:
			if member.id in ctx.bot.admin_ids:
				continue

			if member.id in ctx.bot.blacklist_ids['ids']:
				ctx.bot.blacklist_ids['ids'].remove(member.id)

			try:
				await member.timeout(None, reason = 'Hard lockdown lifted by admin')
			except Exception as e:
				print(f'Error during unhardlockdown for user {member.id}: {e}')
				continue

		if os.path.isfile('blacklist_users.json'):
			with open('blacklist_users.json', 'r') as f:
				ctx.bot.blacklist_ids = json.load(f)

		await ctx.message.channel.send('Hard lockdown lifted. All users have been removed from timeout and blacklist.',
									   delete_after = ctx.bot.del_after)

	@commands.command(name = "analyse", aliases = ["analysis", "analyze", "stats", "statistics", "ana"],
					  brief = "Analyze server message data",
					  help = "Provides statistics about messages sent in the server",
					  usage = "analyse [user_id/mention]")
	@commands.cooldown(1, 30, commands.BucketType.user)
	async def analyse(self, ctx: discord.ext.commands.Context):
		await analysis.format_analysis(ctx.message)

	@commands.command(name = "analyse_voice", aliases = ["voice_analysis", "voice_stats", "voice_analyse", "anavc"],
					  brief = "Analyze voice channel usage",
					  help = "Provides statistics about voice channel usage in the server",
					  usage = "analyse_voice [user_id/mention]")
	@commands.cooldown(1, 30, commands.BucketType.user)
	async def analyse_voice(self, ctx: discord.ext.commands.Context):
		await analysis.format_voice_analysis(ctx.message)

	@commands.command(name = "blacklist",
					  brief = "Blacklist a user",
					  help = "Admin only: Prevent a user from using bot commands",
					  usage = "blacklist <user_id/mention>")
	async def blacklist_id(self, ctx: discord.ext.commands.Context, u_id: str):
		if not isinstance(ctx.message.channel, discord.DMChannel):
			await ctx.message.delete()

		try:
			if u_id is None:
				raise ValueError
			u_id = utils.get_id_from_str(u_id)
		except ValueError:
			await ctx.message.channel.send('Invalid user ID format. Please provide a valid integer ID.',
										   delete_after = ctx.bot.del_after)
			return

		if u_id in ctx.bot.blacklist_ids:
			await ctx.message.channel.send(f'User with ID {u_id} is already blacklisted.',
										   delete_after = ctx.bot.del_after)
			return

		if u_id in ctx.bot.admin_ids:
			await ctx.message.channel.send('You cannot blacklist an admin.', delete_after = ctx.bot.del_after)
			return

		ctx.bot.blacklist_ids['ids'].append(u_id)
		if os.path.isfile(f'blacklist_users.json'):
			os.remove(f'blacklist_users.json')

		with open('blacklist_users.json', 'w') as f:
			json.dump(ctx.bot.blacklist_ids, f, indent = 4)

		channel = ctx.bot.get_channel(1379193761791213618)
		await channel.set_permissions(get(ctx.bot.get_all_members(), id = u_id), send_messages = False)

		await ctx.message.channel.send(f'User <@{u_id}> has been blacklisted.', delete_after = ctx.bot.del_after)

	@commands.command(name = "unblacklist",
					  brief = "Remove user from blacklist",
					  help = "Admin only: Allow a blacklisted user to use bot commands again",
					  usage = "unblacklist <user_id/mention>")
	async def unblacklist_id(self, ctx: discord.ext.commands.Context, u_id: str):
		if not isinstance(ctx.message.channel, discord.DMChannel):
			await ctx.message.delete()

		try:
			if u_id is None:
				raise ValueError
			u_id = utils.get_id_from_str(u_id)
		except ValueError:
			await ctx.message.channel.send('Invalid user ID format. Please provide a valid integer ID.',
										   delete_after = ctx.bot.del_after)
			return

		if u_id not in ctx.bot.blacklist_ids['ids']:
			await ctx.message.channel.send(f'User with ID {u_id} is not blacklisted.', delete_after = ctx.bot.del_after)
			return

		ctx.bot.blacklist_ids['ids'].remove(u_id)
		if os.path.isfile(f'blacklist_users.json'):
			os.remove(f'blacklist_users.json')

		with open('blacklist_users.json', 'w') as f:
			json.dump(ctx.bot.blacklist_ids, f, indent = 4)

		await ctx.message.channel.send(f'User with ID {u_id} has been unblacklisted.', delete_after = ctx.bot.del_after)

	@commands.command(name = "nologc", aliases = ["nologchannel", "nolog_channel"],
					  brief = "Add a channel to no-log list",
					  help = "Admin only: Prevent logging messages in a specific channel",
					  usage = "nolog <channel_id/mention>")
	async def nolog_channel(self, ctx: discord.ext.commands.Context, channel_id: str = None):
		if not isinstance(ctx.message.channel, discord.DMChannel):
			await ctx.message.delete()

		try:
			if channel_id is None:
				raise ValueError
			channel_id = utils.get_id_from_str(channel_id)

		except ValueError:
			await ctx.message.channel.send('Invalid channel ID format. Please provide a valid integer ID.',
										   delete_after = ctx.bot.del_after)
			return

		if channel_id in ctx.bot.no_log['channel_ids']:
			await ctx.message.channel.send(f'Channel with ID {channel_id} is already in the no-log list.',
										   delete_after = ctx.bot.del_after)
			return

		ctx.bot.no_log['channel_ids'].append(channel_id)

		await ctx.message.channel.send(f'Channel with ID {channel_id} has been added to the no-log list.',
									   delete_after = ctx.bot.del_after)

	@commands.command(name = "nologc_remove", aliases = ["nolog_channel_remove", "nolog_channel_rm"],
					  brief = "Remove a channel from no-log list",
					  help = "Admin only: Allow logging messages in a specific channel again",
					  usage = "nolog_remove <channel_id/mention>")
	async def nolog_channel_remove(self, ctx: discord.ext.commands.Context, channel_id: str):
		if not isinstance(ctx.message.channel, discord.DMChannel):
			await ctx.message.delete()

		try:
			if channel_id is None:
				raise ValueError
			channel_id = utils.get_id_from_str(channel_id)

		except ValueError:
			await ctx.message.channel.send('Invalid channel ID format. Please provide a valid integer ID.',
										   delete_after = ctx.bot.del_after)
			return

		if channel_id not in ctx.bot.no_log['channel_ids']:
			await ctx.message.channel.send(f'Channel with ID {channel_id} is not in the no-log list.',
										   delete_after = ctx.bot.del_after)
			return

		ctx.bot.no_log['channel_ids'].remove(channel_id)
		await ctx.message.channel.send(f'Channel with ID {channel_id} has been removed from the no-log list.',
									   delete_after = ctx.bot.del_after)

	@commands.command(name = "nologu", aliases = ["nologuser", "nolog_user"],
					  brief = "Add a user to no-log list",
					  help = "Admin only: Prevent logging messages from a specific user",
					  usage = "nologu <user_id/mention>")
	async def nolog_user(self, ctx: discord.ext.commands.Context, u_id: str):
		if not isinstance(ctx.message.channel, discord.DMChannel):
			await ctx.message.delete()

		try:
			if u_id is None:
				raise ValueError
			u_id = utils.get_id_from_str(u_id)
		except ValueError:
			await ctx.message.channel.send('Invalid user ID format. Please provide a valid integer ID.',
										   delete_after = ctx.bot.del_after)
			return
		if u_id in ctx.bot.no_log['user_ids']:
			await ctx.message.channel.send(f'User with ID {u_id} is already in the no-log list.',
										   delete_after = ctx.bot.del_after)
			return
		ctx.bot.no_log['user_ids'].append(u_id)
		utils.add_to_config(config = ctx.bot.config, key = 'nolog', key2 = 'user_ids', value = u_id)

	@commands.command(name = "echo",
					  brief = "Make the bot say something",
					  help = "Admin only: Makes the bot say the specified message",
					  usage = "echo [channel id] <message>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def echo_cmd(self, ctx: discord.ext.commands.Context):
		message = ctx.message
		del_after = ctx.bot.del_after
		client = ctx.bot
		if message.content is None:
			await message.channel.send('Nothing to echo.', delete_after = del_after)
			return

		msg = message.content.replace('f!echo', '', 1)

		# Send the message content back to the channel
		split_message = msg.split()
		channel = message.channel
		try:
			channel_id = int(split_message[0].replace('#', '', 1).replace('<', '', 1).replace('>', '', 1))
			channel = client.get_channel(channel_id)
			msg = msg.replace(str(channel_id), '', 1)
		except ValueError:
			pass

		await channel.send(msg)

		# Delete the original message
		await message.delete()

	@commands.command(name = "edit_message",
					  brief = "Edit a message the bot has sent",
					  help = "Admin only: Edit a specific message sent by the bot",
					  usage = "edit_message <channel_id> <message_id> <new_content>")
	async def edit_message_cmd(self, ctx: discord.ext.commands.Context, *, args: str):
		if not isinstance(ctx.message.channel, discord.DMChannel):
			await ctx.message.delete()

		split_args = args.split(' ', 2)
		try:
			channel_id = int(split_args[0])
		except ValueError:
			await ctx.send('Invalid channel ID format. Please provide a valid integer ID.',
						   delete_after = ctx.bot.del_after)
			return

		try:
			message_id = int(split_args[1])

		except ValueError:
			await ctx.send('Invalid message ID format. Please provide a valid integer ID.',
						   delete_after = ctx.bot.del_after)
			return

		if len(split_args) < 3:
			await ctx.send('Please provide the new content for the message.',
						   delete_after = ctx.bot.del_after)
			return
		new_content = split_args[2]

		message: discord.Message = await ctx.bot.get_channel(channel_id).fetch_message(message_id)
		if message.author.id != ctx.bot.user.id:
			await ctx.send('You can only edit messages sent by the bot.',
						   delete_after = ctx.bot.del_after)
			return
		try:
			await message.edit(content = new_content)
			await ctx.send(f'Message with ID {message_id} has been edited.',
						   delete_after = ctx.bot.del_after)
		except discord.NotFound:
			await ctx.send(f'Message with ID {message_id} not found.',
						   delete_after = ctx.bot.del_after)
		except discord.Forbidden:
			await ctx.send(f'Cannot edit message with ID {message_id}. Permission denied.',
						   delete_after = ctx.bot.del_after)
		except discord.HTTPException as e:
			await ctx.send(f'Failed to edit message with ID {message_id}. Error: {e}',
						   delete_after = ctx.bot.del_after)


async def setup(bot):
	await bot.add_cog(AdminCmds(bot))
