import discord

NO_ARGS_STR = "Usage: Just type the command without any arguments.\n"

async def help_cmds(client, message: discord.Message):
	if not message.content.replace("help", "").strip() == "":
		cmd = message.content.replace("help", "", 1).strip()

		if cmd in client.command_aliases["nasa"]:
			await message.channel.send(nasa_help(client))
			return

		elif cmd in client.command_aliases["dogpic"]:
			await message.channel.send(dogpic_help(client))
			return

		elif cmd in client.command_aliases["catpic"]:
			await message.channel.send(catpic_help(client))
			return

		elif cmd in client.command_aliases["foxpic"]:
			await message.channel.send(foxpic_help(client))
			return

		elif cmd in client.command_aliases["insult"]:
			await message.channel.send(insult_help(client))
			return

		elif cmd in client.command_aliases["advice"]:
			await message.channel.send(advice_help(client))
			return

		elif cmd in client.command_aliases["ping"]:
			await message.channel.send(ping_help(client))
			return

		elif cmd in client.command_aliases["dice"]:
			await message.channel.send(dice_help(client))
			return

		elif cmd in client.command_aliases["help"]:
			await message.channel.send(help_help(client))
			return

		elif cmd in client.command_aliases["karma"]:
			await message.channel.send(karma_help(client))
			return

		elif cmd in client.command_aliases["joke"]:
			await message.channel.send(joke_help(client))
			return

		else:
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
		f"`{client.prefix}dog` - Get a random dog picture\n"
		f"`{client.prefix}cat` - Get a random cat picture\n"
		f"`{client.prefix}fox` - Get a random fox picture\n"
		f"`{client.prefix}karma` - Get a random karma picture\n"
		f"`{client.prefix}nasa` - Get NASA's picture of the day\n"
		f"`{client.prefix}insult` - Get a random insult\n"
		f"`{client.prefix}advice` - Get a random piece of advice\n"
		f"`{client.prefix}joke` - Get a random joke\n"
		f"`{client.prefix}dice` - Roll a dice between 2 values\n"
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
	cmd_aliases = self.command_aliases["nasa"]
	for cmds in cmd_aliases:
		help_text += f"Alias: `{self.prefix}{cmds}`\n"

	return help_text

def dogpic_help(self):
	help_text = f"`{self.prefix}dog` - Get a random dog picture.\n" + NO_ARGS_STR
	cmd_aliases = self.command_aliases["dogpic"]
	for cmds in cmd_aliases:
		help_text += f"Alias: `{self.prefix}{cmds}`\n"

	return help_text

def catpic_help(self):
	help_text = f"`{self.prefix}cat` - Get a random cat picture.\n" + NO_ARGS_STR
	cmd_aliases = self.command_aliases["catpic"]
	for cmds in cmd_aliases:
		help_text += f"Alias: `{self.prefix}{cmds}`\n"

	return help_text

def foxpic_help(self):
	help_text = f"`{self.prefix}fox` - Get a random fox picture.\n" + NO_ARGS_STR
	cmd_aliases = self.command_aliases["foxpic"]
	for cmds in cmd_aliases:
		help_text += f"Alias: `{self.prefix}{cmds}`\n"

	return help_text

def insult_help(self):
	help_text = f"`{self.prefix}insult` - Get a random insult.\n" + NO_ARGS_STR
	cmd_aliases = self.command_aliases["insult"]
	for cmds in cmd_aliases:
		help_text += f"Alias: `{self.prefix}{cmds}`\n"

	return help_text

def advice_help(self):
	help_text = f"`{self.prefix}advice` - Get a random piece of advice.\n" + NO_ARGS_STR
	cmd_aliases = self.command_aliases["advice"]
	for cmds in cmd_aliases:
		help_text += f"Alias: `{self.prefix}{cmds}`\n"

	return help_text

def ping_help(self):
	help_text = f"`{self.prefix}ping` - Check the bot's latency.\n" + NO_ARGS_STR
	cmd_aliases = self.command_aliases["ping"]
	for cmds in cmd_aliases:
		help_text += f"Alias: `{self.prefix}{cmds}`\n"

	return help_text

def karma_help(self):
	help_text = f"`{self.prefix}karma` - Get a random karma picture.\n"	+ NO_ARGS_STR
	cmd_aliases = self.command_aliases["karma"]
	for cmds in cmd_aliases:
		help_text += f"Alias: `{self.prefix}{cmds}`\n"

	return help_text

def dice_help(self):
	help_text = (
		f"`{self.prefix}dice <min> <max>` - Roll a dice between two values.\n"
		f"Usage: `{self.prefix}dice 1 6` to roll a dice between 1 and 6.\n"
		f"Usage: `{self.prefix}dice -8 14` to roll a dice between -8 and 14.\n"
	)
	cmd_aliases = self.command_aliases["dice"]
	for cmds in cmd_aliases:
		help_text += f"Alias: `{self.prefix}{cmds}`\n"

	return help_text

def joke_help(self):
	help_text = f"`{self.prefix}joke` - Get a random joke.\n" + NO_ARGS_STR
	cmd_aliases = self.command_aliases["joke"]
	for cmds in cmd_aliases:
		help_text += f"Alias: `{self.prefix}{cmds}`\n"

	return help_text

def help_help(self):
	help_text = (
		f"`{self.prefix}help` - Show this help message.\n"
		f"Usage: `{self.prefix}help` <Command>."
	)
	cmd_aliases = self.command_aliases["help"]
	for cmds in cmd_aliases:
		help_text += f"Alias: `{self.prefix}{cmds}`\n"
	return help_text