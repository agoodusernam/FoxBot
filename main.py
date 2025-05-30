import discord
import json
import datetime
from Crypto.Cipher import AES
import db_stuff
import utils


class MyClient(discord.Client):
	today = datetime.datetime.now(datetime.timezone.utc).strftime("%d-%m-%Y")
	no_log_user_ids: list[int] = [1329366814517628969, 1329366963805491251, 1329367238146396211, 1329367408330145805,
								  235148962103951360, 1299640624848306177]
	rek_user_ids: list[int] = [235644709714788352, 542798185857286144]
	no_log_channel_ids: list[int] = []
	no_log_category_ids: list[int] = [1329366612821938207]
	del_after: int = 5

	async def on_ready(self):
		print(f'Logged in as {self.user} (ID: {self.user.id})')
		print('------')

	async def rek(self, message: discord.Message):
		if message.author.id not in self.rek_user_ids:
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
				await self.rek(message)
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

			with utils.make_file(self.today) as file:
				file.write(json.dumps(json_data, ensure_ascii = False) + '\n')

			print(f'Message from {message.author.global_name} [#{message.channel}]: {message.content}')
			await db_stuff.send_message(json_data)


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = MyClient(intents = intents)
#TODO: Get token from environment variable (cloudflare secrets?)
key = input("Enter password to decrypt token: ")
with open('token.txt', 'rb') as token_file:
	token = token_file.read()
nonce = token[:32]
ciphertext = token[32:-16]
tag = token[-16:]
cipher = AES.new(key.encode('utf-8'), AES.MODE_GCM, nonce = nonce)
decrypted_token = cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')
client.run(decrypted_token)
