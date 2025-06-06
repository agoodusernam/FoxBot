import asyncio  # type: ignore
import datetime
import os
from copy import deepcopy
from typing import Callable
import time
from dotenv import load_dotenv


import discord
import json

from discord.utils import get

import admin_cmds
import db_stuff
import api_stuff
import fun_cmds
import one_use_cmds
import restart
import suggest
import utils
import analysis
import help_cmd
import hardlockdown

load_dotenv()


class MyClient(discord.Client):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# Date tracking
		self.today = utils.formatted_time()

		# Access control
		self.prefix = 'f!'
		self.no_log = {
			'user_ids':     [1329366814517628969, 1329366963805491251, 1329367238146396211,
			                 1329367408330145805, 235148962103951360, 1299640624848306177],
			'channel_ids':  [],
			'category_ids': [1329366612821938207]
		}

		self.admin_ids = [235644709714788352, 542798185857286144, 937278965557641227]
		self.dev_ids = [542798185857286144]
		self.blacklist_ids = {'ids': []}

		self.send_blacklist = {
			'channel_ids':  [],
			'category_ids': []
		}

		# Cooldown settings
		self.cooldowns = {
			'analyse': {
				'duration':  300,
				'last_time': int(time.time()) - 300

			},
			'global':  {
				'duration':  5,
				'last_time': int(time.time()) - 5
			}
		}

		# Command names/aliases
		self.command_aliases: dict[str, list[str]] = {
			'nasa':    ['nasa', 'nasa_pic', 'nasa_apod'],
			'dogpic':  ['dogpic', 'dog', 'dog_pic'],
			'catpic':  ['catpic', 'cat', 'cat_pic'],
			'foxpic':  ['foxpic', 'fox', 'fox_pic'],
			'dice':    ['dice', 'roll', 'dice_roll'],
			'insult':  ['insult', 'insults', 'insult_me'],
			'advice':  ['advice', 'advise', 'give_advice'],
			'help':    ['help', 'commands', 'cmds', 'command_list'],
			'ping':    ['ping', 'latency'],
			'karma':   ['karmapic', 'karma', 'karma_pic'],
			'joke':    ['joke', 'jokes'],
			'suggest': ['suggest', 'suggestion'],
			'analyse': ['analyse', 'analysis', 'analyze', 'stats', 'statistics'],
			'flip':   ['flip', 'coin_flip', 'coinflip'],
		}

		self.nasa_data: dict[str, str] = {}

		# UI settings
		self.del_after = 3

	async def on_ready(self):
		utils.check_env_variables()
		utils.clean_up_APOD()
		await self.change_presence(activity=discord.CustomActivity(name='f!help'))
		print(f'Logged in as {self.user} (ID: {self.user.id})')
		print('------')

		if not os.path.isfile('blacklist_users.json'):
			with open('blacklist_users.json', 'w') as f:
				json.dump(self.blacklist_ids, f, indent=4)
		else:
			with open('blacklist_users.json', 'r') as f:
				self.blacklist_ids = json.load(f)

		channel = self.get_channel(1379193761791213618)
		for u_id in self.blacklist_ids['ids']:
			await channel.set_permissions(get(self.get_all_members(), id=u_id), send_messages=False)

	def check_global_cooldown(self) -> bool:
		current_time = int(time.time())
		complete = (current_time - self.cooldowns['global']['last_time']) >= self.cooldowns['global']['duration']
		if complete:
			self.cooldowns['global']['last_time'] = current_time
			return True
		return False

	def check_analyse_cooldown(self) -> bool | int:
		# int = time until cooldown complete, True = ready
		current_time = int(time.time())
		complete = (current_time - self.cooldowns['analyse']['last_time']) >= self.cooldowns['analyse']['duration']
		if complete:
			self.cooldowns['analyse']['last_time'] = current_time
			return True
		return self.cooldowns['analyse']['duration'] - (current_time - self.cooldowns['analyse']['last_time'])

	async def hard_lockdown(self, message: discord.Message):
		await message.delete()
		if message.author.id not in self.admin_ids:
			await message.channel.send('You are not allowed to use this command.', delete_after=self.del_after)
			return

		await hardlockdown.hardlockdown(self, message)

		for member in message.guild.members:
			if member.id in self.admin_ids:
				continue

			if member.id not in self.blacklist_ids['ids']:
				self.blacklist_ids['ids'].append(member.id)

		for member in message.guild.members:
			if member.id not in self.admin_ids:
				try:
					await member.timeout(datetime.timedelta(days = 28), reason = 'Hard lockdown initiated by admin')
				except Exception as e:
					print(f'Error during hard lockdown for user {member.id}: {e}')
					continue


	async def blacklist_id(self, message: discord.Message):
		await message.delete()
		if message.author.id not in self.admin_ids:
			await message.channel.send('You are not allowed to use this command.', delete_after=self.del_after)
			return

		u_id = utils.get_id_from_msg(message)

		try:
			u_id = int(u_id)
		except ValueError:
			await message.channel.send('Invalid user ID format. Please provide a valid integer ID.',
			                           delete_after=self.del_after)
			return

		if u_id in self.blacklist_ids:
			await message.channel.send(f'User with ID {u_id} is already blacklisted.', delete_after=self.del_after)
			return

		if u_id in self.admin_ids:
			await message.channel.send('You cannot blacklist an admin.', delete_after=self.del_after)
			return

		self.blacklist_ids['ids'].append(u_id)
		if os.path.isfile(f'blacklist_users.json'):
			os.remove(f'blacklist_users.json')

		with open('blacklist_users.json', 'w') as f:
			json.dump(self.blacklist_ids, f, indent=4)

		channel = self.get_channel(1379193761791213618)
		await channel.set_permissions(get(self.get_all_members(), id=u_id), send_messages=False)

		await message.channel.send(f'User <@{u_id}> has been blacklisted.', delete_after=self.del_after)

	async def unblacklist_id(self, message: discord.Message):
		await message.delete()
		if message.author.id not in self.admin_ids:
			await message.channel.send('You are not allowed to use this command.', delete_after=self.del_after)
			return

		u_id = utils.get_id_from_msg(message)

		try:
			u_id = int(u_id)
		except ValueError:
			await message.channel.send('Invalid user ID format. Please provide a valid integer ID.',
			                           delete_after=self.del_after)
			return

		if u_id not in self.blacklist_ids['ids']:
			await message.channel.send(f'User with ID {u_id} is not blacklisted.', delete_after=self.del_after)
			return

		self.blacklist_ids['ids'].remove(u_id)
		if os.path.isfile(f'blacklist_users.json'):
			os.remove(f'blacklist_users.json')

		with open('blacklist_users.json', 'w') as f:
			json.dump(self.blacklist_ids, f, indent=4)

		await message.channel.send(f'User with ID {u_id} has been unblacklisted.', delete_after=self.del_after)

	async def get_from_api(self, message: discord.Message, api_func: Callable):

		if not self.check_global_cooldown():
			await message.channel.send(f'Please wait {self.cooldowns['global']['duration']} seconds before using this '
			                           f'command again.', delete_after=self.del_after)
			await message.delete()
			return

		try:
			data = api_func()
			await message.channel.send(data)
		except Exception as e:
			await message.channel.send(f'Error fetching data: {e}')

	async def nasa_pic(self, message: discord.Message):

		if not self.check_global_cooldown():
			await message.channel.send(
					f'Please wait {self.cooldowns['global']['duration']} seconds before using this command again.',
					delete_after=self.del_after)
			await message.delete()
			return

		if os.path.exists(f'nasa/nasa_pic_{self.today}.jpg'):
			await message.channel.send(f'**{self.nasa_data['title']}**\n')
			await utils.send_image(message, f'nasa/nasa_pic_{self.today}.jpg', f'nasa_pic_{self.today}.jpg')
			await message.channel.send(f'**Explanation:** {self.nasa_data['explanation']}')
			return

		try:
			await message.channel.send('Fetching NASA picture of the day...')
			nasa_data = api_stuff.get_nasa_apod()
			self.nasa_data = deepcopy(nasa_data)
			if 'hdurl' in nasa_data:
				url = nasa_data['hdurl']
			else:
				url = nasa_data['url']

			utils.download_from_url(f'nasa/nasa_pic_{self.today}.jpg', url)

			await message.channel.send(f'**{nasa_data['title']}**\n')
			await utils.send_image(message, f'nasa/nasa_pic_{self.today}.jpg', f'nasa_pic_{self.today}.jpg')
			await message.channel.send(f'**Explanation:** {nasa_data['explanation']}')

		except Exception as e:
			await message.channel.send(f'Error fetching NASA picture: {e}')

	async def on_message(self, message: discord.Message):
		if isinstance(message.channel, discord.DMChannel):
			return

		if message.content.startswith('​'):  # Don't log messages that start with a zero-width space
			print(f'[NOT LOGGED] Message from {message.author.global_name} [#{message.channel}]: {message.content}')
			return

		if message.content.startswith(self.prefix):
			message.content = message.content.replace(self.prefix, '')

			if message.author.id in self.blacklist_ids['ids']:
				await message.delete()
				await message.channel.send('You are not allowed to use this command.', delete_after=self.del_after)
				return

			if message.content.lower().startswith('hardlockdown'):
				await self.hard_lockdown(message)
				return

			if message.content.lower().split()[0] in self.command_aliases['ping']:
				if not self.check_global_cooldown():
					await message.channel.send(
							f'Please wait {self.cooldowns['global']['duration']} seconds before using this command again.',
							delete_after=self.del_after)
					await message.delete()
					return
				await message.channel.send(f'{self.latency * 1000:.2f}ms', delete_after=self.del_after)
				await message.delete()
				return

			if message.content.lower().startswith('rek'):
				await admin_cmds.rek(self.admin_ids, self.del_after, message, self.get_guild(message.guild.id))
				return

			if message.content.lower().split()[0] in self.command_aliases['analyse']:
				await analysis.format_analysis(self.admin_ids, self.check_analyse_cooldown(), self.del_after, message)
				return

			if message.content.lower().startswith('blacklist'):
				await self.blacklist_id(message)
				return

			if message.content.lower().startswith('unblacklist'):
				await self.unblacklist_id(message)
				return

			if message.content.lower().startswith('uploadallhistory'):
				if message.author.id != 542798185857286144:
					await message.delete()
					await message.channel.send('You are not allowed to use this command.', delete_after=self.del_after)
					return
				await message.delete()

				try:
					channel = message.guild.get_channel(int(message.content.split()[1]))
				except (IndexError, ValueError):
					await message.channel.send('Please provide a valid channel ID.', delete_after=self.del_after)
					return

				db_stuff.del_channel_from_db(channel)
				await one_use_cmds.upload_all_history(channel, message.author)
				return

			if message.content.lower().startswith('restart'):
				await message.delete()
				if message.author.id not in self.dev_ids:
					await message.channel.send('You are not allowed to use this command.', delete_after=self.del_after)
					return

				await restart.restart(self)
				return

			if message.content.lower().split()[0] in self.command_aliases['nasa']:
				await self.nasa_pic(message)
				return

			if message.content.lower().split()[0] in self.command_aliases['help']:
				await help_cmd.help_cmds(self, message)
				return

			if message.content.lower().split()[0] in self.command_aliases['dogpic']:
				await self.get_from_api(message, api_stuff.get_dog_pic)
				return

			if message.content.lower().split()[0] in self.command_aliases['catpic']:
				await self.get_from_api(message, api_stuff.get_cat_pic)
				return

			if message.content.lower().split()[0] in self.command_aliases['foxpic']:
				await self.get_from_api(message, api_stuff.get_fox_pic)
				return

			if message.content.lower().startswith('insult'):
				await self.get_from_api(message, api_stuff.get_insult)
				return

			if message.content.lower().startswith('advice'):
				await self.get_from_api(message, api_stuff.get_advice)
				return

			if message.content.lower().split()[0] in self.command_aliases['joke']:
				await self.get_from_api(message, api_stuff.get_joke)
				return

			if message.content.lower().split()[0] in self.command_aliases['dice']:
				await fun_cmds.dice_roll(self.del_after, message)
				return

			if message.content.lower().split()[0] in self.command_aliases['flip']:
				coin_flip = fun_cmds.flip_coin()
				await message.channel.send(f'You flipped a coin and got: **{coin_flip}**', delete_after=self.del_after)
				return

			if message.content.lower().startswith('suggest'):
				await suggest.send_suggestion(self, message)
				return

			if message.content.lower().split()[0] in self.command_aliases['karma']:
				karma_pic = fun_cmds.get_karma_pic()
				if karma_pic is None:
					await message.channel.send('No karma pictures found.')
					return
				file_path, file_name = karma_pic
				await utils.send_image(message, file_path, file_name)
				return

		if (message.author != self.user) and (
				message.author.id not in self.no_log['user_ids']) and (
				message.channel.id not in self.no_log['channel_ids']) and (
				message.channel.category_id not in self.no_log['category_ids']):

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
				'channel':            message.channel.name
			}

			if os.getenv('LOCAL_SAVE') == 'True':
				with utils.make_file(self.today) as file:
					file.write(json.dumps(json_data, ensure_ascii=False) + '\n')

			print(f'Message from {message.author.global_name} [#{message.channel}]: {message.content}')
			if has_attachment:
				if os.environ.get('LOCAL_IMG_SAVE') == 'True':
					await utils.save_attachments(message)

				else:
					for attachment in message.attachments:
						await db_stuff.send_attachment(message, attachment)

			db_stuff.send_message(json_data)
			self.today = utils.formatted_time()


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = MyClient(intents=intents)
client.run(os.getenv('TOKEN'))
