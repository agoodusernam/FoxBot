import os

import discord
import json
import datetime
from Crypto.Cipher import AES


def make_file(name="messages"):
	if not os.path.exists('data'):
		os.makedirs('data')
	if not os.path.exists('data/attachments'):
		os.makedirs('data/attachments')
	return open(f'data/{name}.json', 'a+', encoding = 'utf-8')

def make_empty_file(path):
	if not os.path.exists(path):
		with open(path, 'w'):
			pass


class MyClient(discord.Client):
	now = datetime.datetime.now(datetime.timezone.utc).strftime("%d-%m-%Y")
	disallwed_user_ids: list[int] = [1329366814517628969, 1329366963805491251, 1329367238146396211, 1329367408330145805,
									 235148962103951360]
	rek_user_ids: list[int] = [542798185857286144, 235644709714788352]
	disallwed_channel_ids: list[int] = []
	disallwed_category_ids: list[int] = [1329366612821938207]

	async def on_ready(self):
		print(f'Logged in as {self.user} (ID: {self.user.id})')
		print('------')

	async def on_message(self, message):
		replied = False
		if message.content.startswith('​'): # Don't log messages that start with a zero-width space
			replied = True

		if message.content.startswith('._'):
			if message.content.startswith('._ttotal'):
				replied = True
				with open(f'data/{self.now}.json') as f:
					count = sum(1 for _ in f)

				await message.channel.send(f'Total messages logged today: {count}')

			if message.content.startswith('._rek'):
				if message.author.id not in self.rek_user_ids:
					return
				u_id = message.content.split()[-1]
				until = datetime.timedelta(days = 28)
				reason = 'get rekt nerd'
				try:
					u_id = int(u_id)
				except ValueError:
					await message.channel.send('Invalid user ID format. Please provide a valid integer ID.')
					return

				guild = self.get_guild(1081760248433492140)
				member = guild.get_member(u_id)
				if member is None:
					await message.channel.send(f'User with ID {u_id} not found.')
					return
				await member.timeout(until, reason=reason)
				replied = True


		if (message.author != self.user) and (
                message.author.id not in self.disallwed_user_ids) and (
				message.channel.id not in self.disallwed_channel_ids) and (
				message.channel.category_id not in self.disallwed_category_ids) and not replied:
			#TODO: Add uploading to a mongodb(?) server (hosted on hostinger?)
			has_attachment = False
			if message.attachments:
				for attachment in message.attachments:
					time_now = datetime.datetime.now(datetime.timezone.utc).strftime("%d-%m-%Y_%H-%M-%S")
					file_path = f'data/attachments/{time_now}_{attachment.filename}'
					if not os.path.exists(file_path):
						with open(file_path, 'x'):
							pass
					await attachment.save(file_path)
					print(f'Saved attachment: {file_path}')
					has_attachment = True


			json_data = {
					"author": message.author.name,
					"author_id": str(message.author.id),
					"content":   message.content,
					"HasAttachments": has_attachment,
					"timestamp": message.created_at.isoformat(),
					"channel":   str(message.channel)
				}

			with make_file(self.now) as file:
				file.write(json.dumps(json_data, ensure_ascii = False) + '\n')

			print(f'Message from {message.author.name}: {message.content} in {message.channel}')


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
cipher = AES.new(key.encode('utf-8'), AES.MODE_GCM, nonce=nonce)
decrypted_token = cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')
client.run(decrypted_token)
