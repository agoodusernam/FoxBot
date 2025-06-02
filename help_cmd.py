import discord

NO_ARGS_STR = "Usage: Just type the command without any arguments."

async def help_cmds(client, message: discord.Message):
	if not message.content.replace("help", "").strip() == "":
		cmd = message.content.replace("help", "", 1).strip()

		match cmd:
			case "nasa":
				await message.channel.send(nasa_help(client))
				return
			case "dogpic":
				await message.channel.send(dogpic_help(client))
				return
			case "catpic":
				await message.channel.send(catpic_help(client))
				return
			case "foxpic":
				await message.channel.send(foxpic_help(client))
				return
			case "insult":
				await message.channel.send(insult_help(client))
				return
			case "advice":
				await message.channel.send(advice_help(client))
				return
			case "ping":
				await message.channel.send(ping_help(client))
				return
			case "help":
				await message.channel.send(help_help(client))
				return
			case _:
				await message.channel.send("Unknown command. Use `help` to see available commands.", delete_after=client.del_after)
				await message.delete()
				return

	await message.delete()
	if not client.check_global_cooldown():
		await message.channel.send(
			f'Please wait {client.cooldowns["global"]["duration"]} seconds before using this command again.',
			delete_after = client.del_after)
		return

	if message.author.id in client.blacklist_ids['ids']:
		await message.channel.send('You are not allowed to use this command.', delete_after = client.del_after)
		return

	if message.author.id in client.admin_ids:
		await admin_help(client, message)

	help_text = (
		"**Available Commands:**\n"
		f"`{client.prefix}ping` - Check the bot's latency\n"
		f"`{client.prefix}nasa` - Get NASA's picture of the day\n"
		f"`{client.prefix}dogpic` - Get a random dog picture\n"
		f"`{client.prefix}catpic` - Get a random cat picture\n"
		f"`{client.prefix}foxpic` - Get a random fox picture\n"
		f"`{client.prefix}insult` - Get a random insult\n"
		f"`{client.prefix}advice` - Get a random piece of advice\n"
		f"`{client.prefix}help` - Show this help message"
	)

	await message.channel.send(help_text)


async def admin_help(self, message: discord.Message):
	admin_help_text = (
		"**Admin Commands:**\n"
		f"`{self.prefix}rek <user_id>` - Absolutely rek a user\n"
		f"`{self.prefix}analyse` - Analyse the server's messages ({self.cooldowns['analyse']['duration']}s "
		f"cooldown)\n"
		f"`{self.prefix}blacklist <user_id>` - Blacklist a user from using commands\n"
		f"`{self.prefix}unblacklist <user_id>` - Remove a user from the blacklist\n"
		f"NOTE: There is a global cooldown of {self.cooldowns['global']['duration']} seconds for all commands.\n"
	)

	dm = await message.author.create_dm()
	await dm.send(admin_help_text)



def nasa_help(self):
	help_text = f"`{self.prefix}nasa` - Get NASA's picture of the day.\n" + NO_ARGS_STR
	return help_text

def dogpic_help(self):
	help_text = f"`{self.prefix}dogpic` - Get a random dog picture.\n" + NO_ARGS_STR

	return help_text

def catpic_help(self):
	help_text = f"`{self.prefix}catpic` - Get a random cat picture.\n" + NO_ARGS_STR

	return help_text

def foxpic_help(self):
	help_text = f"`{self.prefix}foxpic` - Get a random fox picture.\n" + NO_ARGS_STR

	return help_text

def insult_help(self):
	help_text = f"`{self.prefix}insult` - Get a random insult.\n" + NO_ARGS_STR

	return help_text

def advice_help(self):
	help_text = f"`{self.prefix}advice` - Get a random piece of advice.\n" + NO_ARGS_STR

	return help_text

def ping_help(self):
	help_text = f"`{self.prefix}ping` - Check the bot's latency.\n" + NO_ARGS_STR

	return help_text

def help_help(self):
	help_text = (
		f"`{self.prefix}help` - Show this help message.\n"
		"Usage: `{self.prefix}help` [Command]."
	)
	return help_text