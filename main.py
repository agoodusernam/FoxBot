import asyncio
import os
from typing import Callable

import discord
import json
import datetime
import db_stuff
import api_stuff
import utils
from dotenv import load_dotenv
import analysis
import time

load_dotenv()


class MyClient(discord.Client):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# Date tracking
		self.today = utils.formatted_time()

		# Access control
		self.no_log = {
			'user_ids':     [1329366814517628969, 1329366963805491251, 1329367238146396211,
							 1329367408330145805, 235148962103951360, 1299640624848306177],
			'channel_ids':  [],
			'category_ids': [1329366612821938207]
		}
		self.admin_ids = [235644709714788352, 542798185857286144]
		self.blacklist_ids = {"ids": []}

		self.send_blacklist = {
			'channel_ids': [],
			'category_ids': []
		}

		# Cooldown settings
		self.cooldowns = {
			'analyse': {
				'duration':  60,
				'last_time': int(time.time()) - 60
			},
			'global':  {
				'duration':  5,
				'last_time': int(time.time()) - 5
			}
		}

		# UI settings
		self.del_after = 3

	async def on_ready(self):
		print(f'Logged in as {self.user} (ID: {self.user.id})')
		print('------')
		# Check for environment variables
		# TOKEN is checked by discord.py and this won't run in the first place if it's not set.
		if not os.getenv("MONGO_URI"):
			print('No MONGO_URI found in environment variables. Please set it to connect to a database.')

		if not os.getenv("NASA_API_KEY"):
			print('No NASA_API_KEY found in environment variables. Please set it to fetch NASA pictures.')

		if not os.getenv("CAT_API_KEY"):
			print('No CAT_API_KEY found in environment variables. Please set it to fetch cat pictures.')

		if not os.getenv("LOCAL_SAVE"):
			print('No LOCAL_SAVE found in environment variables. Defaulting to False.')
			os.environ["LOCAL_SAVE"] = 'False'

		if os.getenv("LOCAL_SAVE") not in ['True', 'False']:
			print('Invalid LOCAL_SAVE value. Please set it to True or False. Defaulting to False.')
			os.environ["LOCAL_SAVE"] = 'False'

		if not os.path.isfile('blacklist_users.json'):
			with open('blacklist_users.json', 'w') as f:
				json.dump(self.blacklist_ids, f, indent = 4)
		else:
			with open('blacklist_users.json', 'r') as f:
				self.blacklist_ids = json.load(f)

	def check_global_cooldown(self) -> bool:
		current_time = int(time.time())
		complete = (current_time - self.cooldowns['global']['last_time']) >= self.cooldowns['global']['duration']
		if complete:
			self.cooldowns['global']['last_time'] = current_time
			return True
		return False


	def check_analyse_cooldown(self) -> bool:
		current_time = int(time.time())
		complete = (current_time - self.cooldowns['analyse']['last_time']) >= self.cooldowns['analyse']['duration']
		if complete:
			self.cooldowns['analyse']['last_time'] = current_time
			return True
		return False

	async def rek(self, message: discord.Message):
		if message.author.id not in self.admin_ids:
			await message.channel.send('You are not allowed to use this command.', delete_after = self.del_after)
			await message.delete()
			return
		await message.delete()

		u_id = utils.get_id_from_msg(message)

		try:
			u_id = int(u_id)
		except ValueError:
			await message.channel.send('Invalid user ID format. Please provide a valid integer ID.',
									   delete_after = self.del_after)
			return

		member = self.get_guild(message.guild.id).get_member(u_id)

		if member is None:
			await message.channel.send(f'User with ID {u_id} not found.', delete_after = self.del_after)
			return

		await member.timeout(datetime.timedelta(days = 28), reason = 'get rekt nerd')
		await message.channel.send(f'<@{u_id}> has been rekt.', delete_after = self.del_after)
		return

	async def analyse(self, message: discord.Message):
		await message.delete()
		if message.author.id not in self.admin_ids:
			await message.channel.send('You are not allowed to use this command.', delete_after = self.del_after)
			return

		if not self.check_analyse_cooldown():
			await message.channel.send(f'Please wait {self.cooldowns['analyse']['duration']} seconds before using this command again.',
									   delete_after = self.del_after)
			return

		await message.channel.send('Analysing...')
		try:
			result = analysis.analyse()
			if isinstance(result, dict):
				top_3_active_users = sorted(result["active_users_lb"], key = lambda x: x["num_messages"],
											reverse = True)[:3]
				msg = (f'{result["total_messages"]} total messages analysed\n'
					   f'Most common word: {result["most_common_word"]} said {result["most_common_word_count"]} times \n'
					   f'({result["total_unique_words"]} unique words, average length: {result["average_length"]:.2f} characters)\n'
					   f'Top 3 most active users:\n')
				for user in top_3_active_users:
					msg += f'**{user["user"]}** with {user["num_messages"]} messages\n'

				await message.channel.send(msg)
			elif isinstance(result, Exception):
				await message.channel.send(f'Error during analysis: {result}')
				await message.channel.send(f'Contact HardlineMouse16 about this.')
			elif isinstance(result, str):
				await message.channel.send(result)

			else:
				print("No valid messages found for analysis.")
		except Exception as e:
			print(f"Error during analysis: {e}")


	async def blacklist_id(self, message: discord.Message):
		await message.delete()
		if message.author.id not in self.admin_ids:
			await message.channel.send('You are not allowed to use this command.', delete_after = self.del_after)
			return

		u_id = utils.get_id_from_msg(message)

		try:
			u_id = int(u_id)
		except ValueError:
			await message.channel.send('Invalid user ID format. Please provide a valid integer ID.',
									   delete_after = self.del_after)
			return

		if u_id in self.blacklist_ids:
			await message.channel.send(f'User with ID {u_id} is already blacklisted.', delete_after = self.del_after)
			return

		self.blacklist_ids['ids'].append(u_id)
		if os.path.isfile(f'blacklist_users.json'):
			os.rmdir(f'blacklist_users.json')

		with open('blacklist_users.json', 'w') as f:
			json.dump(self.blacklist_ids, f, indent = 4)

		await message.channel.send(f'User with ID {u_id} has been blacklisted.', delete_after = self.del_after)

	async def get_from_api(self, message: discord.Message, api_func: Callable, success_msg: str | None):

		if not self.check_global_cooldown():
			await message.channel.send(f'Please wait {self.cooldowns['global']['duration']} seconds before using this '
									   f'command again.',
									   delete_after = self.del_after)
			await message.delete()
			return

		if success_msg is not None:
			await message.channel.send(success_msg)
		try:
			data = await api_func()
			await message.channel.send(data)
		except Exception as e:
			await message.channel.send(f'Error fetching data: {e}')


	async def nasa_pic(self, message: discord.Message):

		if not self.check_global_cooldown():
			await message.channel.send(f'Please wait {self.cooldowns['global']['duration']} seconds before using this command again.',
									   delete_after = self.del_after)
			await message.delete()
			return

		await message.channel.send('Fetching NASA picture of the day...')
		try:
			nasa_data = await api_stuff.get_nasa_apod()
			if 'hdurl' in nasa_data:
				url = nasa_data['hdurl']
			else:
				url = nasa_data['url']

			await message.channel.send(f"**{nasa_data['title']}**\n{url}\nBlame discord for not embedding it properly.")
			await message.channel.send(f"**Explanation:** {nasa_data['explanation']}")

		except Exception as e:
			await message.channel.send(f'Error fetching NASA picture: {e}')

	async def on_message(self, message: discord.Message):
		if isinstance(message.channel, discord.DMChannel):
			await message.channel.send(f'This bot does not support direct messages. Please use it in the Foxes Haven '
									   f'Discord server.')
			return

		if message.content.startswith('​'):  # Don't log messages that start with a zero-width space
			print(f'[NOT LOGGED] Message from {message.author.global_name} [#{message.channel}]: {message.content}')
			return

		if '<@1377636535968600135>' in message.content:
			await message.channel.send(
					'Hello, I am just a statistics bot. For questions or concerns, please hesitate to contact HardlineMouse16')
			return

		if message.content.startswith('._'):
			if message.author.id in self.blacklist_ids['ids']:
				await message.channel.send('You are not allowed to use this command.', delete_after = self.del_after)
				return
			message.content = message.content.replace('._', '')

			if message.content.startswith('ping'):
				await message.channel.send(f'{self.latency * 1000:.2f}ms', delete_after = self.del_after)
				await message.delete()
				return

			if message.content.startswith('rek'):
				await self.rek(message)
				return

			if message.content.startswith('analyse'):
				await self.analyse(message)
				return

			if message.content.startswith('blacklist'):
				await self.blacklist_id(message)
				return

			if message.content.startswith('nasa'):
				await self.nasa_pic(message)
				return

			if message.content.startswith('dogpic'):
				await self.get_from_api(message, api_stuff.get_dog_pic, 'Fetching random dog picture...')
				return

			if message.content.startswith('catpic'):
				await self.get_from_api(message, api_stuff.get_cat_pic, 'Fetching random cat picture...')
				return

			if message.content.startswith('foxpic'):
				await self.get_from_api(message, api_stuff.get_fox_pic, 'Fetching random fox picture...')
				return

			if message.content.startswith('insult'):
				await self.get_from_api(message, api_stuff.get_insult, None)
				return

			if message.content.startswith('advice'):
				await self.get_from_api(message, api_stuff.get_advice, 'Fetching random advice...')
				return

		if (message.author != self.user) and (
				message.author.id not in self.no_log["user_ids"]) and (
				message.channel.id not in self.no_log["channel_ids"]) and (
				message.channel.category_id not in self.no_log["category_ids"]):

			has_attachment = False
			if message.attachments:
				has_attachment = True
				await utils.save_attachments(message)

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
				"channel":            str(message.channel)
			}

			if os.getenv("LOCAL_SAVE") == 'True':
				with utils.make_file(self.today) as file:
					file.write(json.dumps(json_data, ensure_ascii = False) + '\n')

			print(f'Message from {message.author.global_name} [#{message.channel}]: {message.content}')

			asyncio.create_task(db_stuff.send_message(json_data))
			self.today = utils.formatted_time()


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = MyClient(intents = intents)
client.run(os.getenv("TOKEN"))
