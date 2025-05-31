import asyncio
import os
import discord
import json
import datetime
import db_stuff
import nasa_stuff
import utils
from dotenv import load_dotenv
import analysis

load_dotenv()

class MyClient(discord.Client):
	today = datetime.datetime.now(datetime.timezone.utc).strftime("%d-%m-%Y")
	# So nasa picture will always be deleted after use
	no_log_user_ids: list[int] = [1329366814517628969, 1329366963805491251, 1329367238146396211, 1329367408330145805,
								  235148962103951360, 1299640624848306177]
	allow_cmds: list[int] = [235644709714788352, 542798185857286144]
	no_log_channel_ids: list[int] = []
	no_log_category_ids: list[int] = [1329366612821938207]
	del_after: int = 3

	async def on_ready(self):
		print(f'Logged in as {self.user} (ID: {self.user.id})')
		print('------')

	async def set_time(self):
		self.today = datetime.datetime.now(datetime.timezone.utc).strftime("%d-%m-%Y")

	async def rek(self, message: discord.Message):
		if message.author.id not in self.allow_cmds:
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
		if message.author.id not in self.allow_cmds:
			return
		await message.channel.send('Analysing...')
		try:
			result = analysis.analyse()
			if isinstance(result, dict):
				msg = (f'{result["total_messages"]} total messages analysed\n' 
					f'Most common word: {result["most_common_word"]} said {result["most_common_word_count"]} times \n' 
					f'({result["total_unique_words"]} unique words, average length: {result["average_length"]:.2f} characters)\n'
					f'Most active user: {result["most_active_user"]} with {result["most_active_user_count"]} messages.')
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

	async def nasa_pic(self, message: discord.Message):
		if message.author.id not in self.allow_cmds:
			return
		await message.channel.send('Fetching NASA picture of the day...')
		try:
			nasa_data = await nasa_stuff.get_nasa_apod()
			embed = discord.Embed().set_image(url = nasa_data['url']).set_thumbnail(url = nasa_data['thumbnail_url'])
			await message.channel.send(f"**{nasa_data['title']}**", embed = embed)
			await message.channel.send(f"**Explanation:** {nasa_data['explanation']}")

		except Exception as e:
			await message.channel.send(f'Error fetching NASA picture: {e}')



	async def on_message(self, message: discord.Message):
		if message.content.startswith('​'):  # Don't log messages that start with a zero-width space
			print(f'[NOT LOGGED] Message from {message.author.global_name} [#{message.channel}]: {message.content}')
			return

		if '<@1377636535968600135>' in message.content:
			await message.channel.send(
				'Hello, I am just a statistics bot. For questions or concerns, please hesitate to contact HardlineMouse16')
			return

		if message.content.startswith('._'):
			message.content = message.content.replace('._', '')

			if message.content.startswith('ttotal'):
				with open(f'data/{self.today}.json', 'r', errors = 'ignore') as fp:
					for count, line in enumerate(fp):
						pass
				await message.delete()
				await message.channel.send(f'Total messages logged today: {count + 1}', delete_after = self.del_after)
				return

			if message.content.startswith('ping'):
				await message.delete()
				await message.channel.send(f'{self.latency * 1000:.2f}ms', delete_after = self.del_after)
				return

			if message.content.startswith('rek'):
				await message.delete()
				await self.rek(message)
				return

			if message.content.startswith('analyse'):
				await message.delete()
				await self.analyse(message)
				return

			if message.content.startswith('nasa'):
				await self.nasa_pic(message)
				return

		if (message.author != self.user) and (
				message.author.id not in self.no_log_user_ids) and (
				message.channel.id not in self.no_log_channel_ids) and (
				message.channel.category_id not in self.no_log_category_ids):

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
			asyncio.create_task(self.set_time())


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = MyClient(intents = intents)
client.run(os.getenv("TOKEN"))
