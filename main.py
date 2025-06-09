import datetime
import os
from copy import deepcopy
from typing import Union

from dotenv import load_dotenv
import discord
import json
from discord.utils import get
from discord.ext import commands
from discord.ext.commands import BucketType

from custom_logging import voice_log
from utils import db_stuff, utils, api_stuff
from bot_commands import suggest, restart, admin_cmds, fun_cmds, analysis, echo
import reaction_roles

load_dotenv()

# Create bot with intents (note: removed help_command=None to use built-in help)
intents = discord.Intents.all()
intents.presences = False
bot = commands.Bot(command_prefix = 'f!', intents = intents)


# Initialize bot configuration
bot.today = utils.formatted_time()

# Access control
bot.no_log = {
	'user_ids':     [1329366814517628969, 1329366963805491251, 1329367238146396211,
					 1329367408330145805, 235148962103951360, 1299640624848306177],
	'channel_ids':  [],
	'category_ids': [1329366612821938207]
}

logging_channels: dict[str, Union[discord.VoiceChannel, discord.StageChannel, discord.ForumChannel,
					   discord.TextChannel, discord.CategoryChannel, discord.Thread, None | int]] = {
	'voice': 1329366741909770261
}
bot.logging_channels = logging_channels

bot.admin_ids = [235644709714788352, 542798185857286144, 937278965557641227]
bot.dev_ids = [542798185857286144]
bot.blacklist_ids = {'ids': []}

bot.send_blacklist = {
	'channel_ids':  [],
	'category_ids': []
}

# UI settings
bot.del_after = 3

# NASA data
bot.nasa_data = {}

# Reaction roles
bot.role_message_id = 0
bot.emoji_to_role = {
	discord.PartialEmoji.from_str('<:jjs:1380607586231128155>'):         1314274909815439420,
	discord.PartialEmoji(name = '❕'):                                    1321214081977421916,
	discord.PartialEmoji.from_str('<:grass_block:1380607192717328505>'): 1380623674918310079,
	discord.PartialEmoji.from_str('<:Vrchat:1380607441691214048>'):      1380623882574368939,
	discord.PartialEmoji.from_str('<:rust:1380606572127850639>'):        1130284770757197896,
	discord.PartialEmoji(name = '❔'):                                    1352341336459841688,
	discord.PartialEmoji(name = '🎬'):                                    1380624012090150913,
}

# Load blacklist
if not os.path.isfile('blacklist_users.json'):
	with open('blacklist_users.json', 'w') as f:
		json.dump(bot.blacklist_ids, f, indent = 4)
else:
	with open('blacklist_users.json', 'r') as f:
		bot.blacklist_ids = json.load(f)


# Bot configuration
@bot.event
async def on_ready():

	utils.check_env_variables()
	utils.clean_up_APOD()
	await bot.change_presence(activity = discord.CustomActivity(name = 'f!help'))
	print(f'Logged in as {bot.user} (ID: {bot.user.id})')
	print('------')

	# Apply blacklist to channel
	channel = bot.get_channel(1379193761791213618)
	for u_id in bot.blacklist_ids['ids']:
		await channel.set_permissions(get(bot.get_all_members(), id = u_id), send_messages = False)

	# Set up reaction roles
	channel = bot.get_channel(1337465612875595776)
	messages = [message async for message in channel.history(limit = 1)]
	if (messages == []) or (messages[0].content != reaction_roles.to_send_msg):
		if not messages == []:
			await messages[0].delete()
		bot.role_message_id = await reaction_roles.send_reaction_role_msg(channel)
	else:
		bot.role_message_id = messages[0].id

	for key, value in bot.logging_channels.items():
		channel = bot.get_channel(value)
		bot.logging_channels[key] = channel


# Custom help command formatting
class CustomHelpCommand(commands.DefaultHelpCommand):
	def __init__(self):
		super().__init__(
				no_category = "Commands",
				width = 100,
				sort_commands = True,
				dm_help = False
		)

	async def send_bot_help(self, mapping):
		ctx = self.context
		if ctx.author.id in bot.blacklist_ids['ids']:
			await ctx.send('You are not allowed to use this command.', delete_after = bot.del_after)
			return

		await super().send_bot_help(mapping)

		# Send admin commands separately to admin users
		if ctx.author.id in bot.admin_ids:
			admin_help_text = (
				"**Admin Commands:**\n"
				f"`{ctx.prefix}rek <user_id/mention>` - Absolutely rek a user\n"
				f"`{ctx.prefix}analyse [user_id/mention]` - Analyse the server's messages\n"
				f"`{ctx.prefix}blacklist <user_id/mention>` - Blacklist a user from using commands\n"
				f"`{ctx.prefix}unblacklist <user_id/mention>` - Remove a user from the blacklist\n"
				f"`{ctx.prefix}echo [channel id] <message>` - Make the bot say something\n"
				f"`{ctx.prefix}hardlockdown` - Lock down the entire server\n"
				f"`{ctx.prefix}unhardlockdown` - Unlock the server from hard lockdown\n"
				f"`{ctx.prefix}restart` - Restart the bot\n"
			)
			dm = await ctx.author.create_dm()
			await dm.send(admin_help_text)


# Apply custom help command
bot.help_command = CustomHelpCommand()

# Command checks
def not_blacklisted(ctx):
	return ctx.author.id not in bot.blacklist_ids['ids']



def is_admin(ctx):
	return ctx.author.id in bot.admin_ids


def is_dev(ctx):
	return ctx.author.id in bot.dev_ids


@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandOnCooldown):
		await ctx.send(
			f'This command is on cooldown. Please try again in {error.retry_after:.1f} seconds.',
			delete_after=bot.del_after
		)
		await ctx.message.delete()
	elif isinstance(error, commands.CheckFailure):
		await ctx.send('You do not have permission to use this command.', delete_after = bot.del_after)
		await ctx.message.delete()

	else:
		print(f"Unhandled error: {error}")

# Dev commands
@bot.command(name = "restart",
			 brief = "Restart the bot",
			 help = "Dev only: Git pull and restart the bot instance", hidden=True)
@commands.check(is_dev)
async def restart_cmd(ctx):
	await ctx.message.delete()
	await restart.restart(bot)


@bot.command(name = 'reset_cooldowns',
			 brief = 'Reset command cooldowns',
			 help = 'Dev only: Reset all command cooldowns for the bot', hidden=True)
@commands.check(is_dev)
async def reset_cooldowns(ctx):
	await ctx.message.delete()
	for command in bot.commands:
		if command.is_on_cooldown(ctx):
			command.reset_cooldown(ctx)
	await ctx.send('All command cooldowns have been reset.', delete_after = bot.del_after)

@bot.command(name = "shutdown",
			 brief = "Shutdown the bot",
			 help = "Dev only: Shutdown the bot instance", hidden=True)
@commands.check(is_dev)
async def shutdown_cmd(ctx):
	await ctx.message.delete()
	await ctx.send('Shutting down the bot...', delete_after = bot.del_after)
	print('Bot is shutting down...')
	db_stuff.disconnect()
	await bot.close()

# Admin commands
@bot.command(name = "hardlockdown",
			 brief = "Lock down the entire server",
			 help = "Admin only: Timeout all non-admin users for 28 days and add them to blacklist", hidden=True)
@commands.check(is_admin)
async def hard_lockdown(ctx):
	await ctx.message.delete()
	# await admin_cmds.hardlockdown(ctx.message)

	for member in ctx.guild.members:
		if member.id in bot.admin_ids:
			continue

		if member.id not in bot.blacklist_ids['ids']:
			bot.blacklist_ids['ids'].append(member.id)

	for member in ctx.guild.members:
		if member.id not in bot.admin_ids:
			try:
				await member.timeout(datetime.timedelta(days = 28), reason = 'Hard lockdown initiated by admin')
			except Exception as e:
				print(f'Error during hard lockdown for user {member.id}: {e}')
				continue

	await ctx.send('Hard lockdown initiated. All non-admin users have been timed out for 28 days and added to the blacklist.',
				   delete_after = bot.del_after)


@bot.command(name = "unhardlockdown",
			 brief = "Unlock the server from hard lockdown",
			 help = "Admin only: Remove timeouts and blacklist from all users", hidden=True)
@commands.check(is_admin)
async def unhard_lockdown(ctx):
	await ctx.message.delete()

	for member in ctx.guild.members:
		if member.id in bot.admin_ids:
			continue

		if member.id in bot.blacklist_ids['ids']:
			bot.blacklist_ids['ids'].remove(member.id)

		try:
			await member.timeout(None, reason = 'Hard lockdown lifted by admin')
		except Exception as e:
			print(f'Error during unhardlockdown for user {member.id}: {e}')
			continue

	if os.path.isfile('blacklist_users.json'):
		with open('blacklist_users.json', 'r') as f:
			bot.blacklist_ids = json.load(f)

	await ctx.send('Hard lockdown lifted. All users have been removed from timeout and blacklist.',
				   delete_after = bot.del_after)


@bot.command(name = "rek",
			 brief = "Absolutely rek a user",
			 help = "Admin only: Timeout a user for 28 days and add them to blacklist", hidden=True,
			 usage = "rek <user_id/mention>")
@commands.check(is_admin)
async def rek(ctx):
	await admin_cmds.rek(bot.admin_ids, bot.del_after, ctx.message, bot.get_guild(ctx.guild.id))


@bot.command(name = "analyse", aliases = ["analysis", "analyze", "stats", "statistics"],
			 brief = "Analyze server message data",
			 help = "Provides statistics about messages sent in the server", hidden=True,
			 usage = "analyse [user_id/mention]")
@commands.cooldown(1, 300, commands.BucketType.user)
@commands.check(is_admin)
async def analyse(ctx):
	await analysis.format_analysis(ctx.message)


@bot.command(name = "blacklist",
			 brief = "Blacklist a user",
			 help = "Admin only: Prevent a user from using bot commands", hidden=True,
			 usage = "blacklist <user_id/mention>")
@commands.check(is_admin)
async def blacklist_id(ctx):
	await ctx.message.delete()

	u_id = utils.get_id_from_msg(ctx.message)

	try:
		u_id = int(u_id)
	except ValueError:
		await ctx.send('Invalid user ID format. Please provide a valid integer ID.',
					   delete_after = bot.del_after)
		return

	if u_id in bot.blacklist_ids:
		await ctx.send(f'User with ID {u_id} is already blacklisted.', delete_after = bot.del_after)
		return

	if u_id in bot.admin_ids:
		await ctx.send('You cannot blacklist an admin.', delete_after = bot.del_after)
		return

	bot.blacklist_ids['ids'].append(u_id)
	if os.path.isfile(f'blacklist_users.json'):
		os.remove(f'blacklist_users.json')

	with open('blacklist_users.json', 'w') as f:
		json.dump(bot.blacklist_ids, f, indent = 4)

	channel = bot.get_channel(1379193761791213618)
	await channel.set_permissions(get(bot.get_all_members(), id = u_id), send_messages = False)

	await ctx.send(f'User <@{u_id}> has been blacklisted.', delete_after = bot.del_after)


@bot.command(name = "unblacklist",
			 brief = "Remove user from blacklist",
			 help = "Admin only: Allow a blacklisted user to use bot commands again", hidden=True,
			 usage = "unblacklist <user_id/mention>")
@commands.check(is_admin)
async def unblacklist_id(ctx):
	await ctx.message.delete()

	u_id = utils.get_id_from_msg(ctx.message)

	try:
		u_id = int(u_id)
	except ValueError:
		await ctx.send('Invalid user ID format. Please provide a valid integer ID.',
					   delete_after = bot.del_after)
		return

	if u_id not in bot.blacklist_ids['ids']:
		await ctx.send(f'User with ID {u_id} is not blacklisted.', delete_after = bot.del_after)
		return

	bot.blacklist_ids['ids'].remove(u_id)
	if os.path.isfile(f'blacklist_users.json'):
		os.remove(f'blacklist_users.json')

	with open('blacklist_users.json', 'w') as f:
		json.dump(bot.blacklist_ids, f, indent = 4)

	await ctx.send(f'User with ID {u_id} has been unblacklisted.', delete_after = bot.del_after)


# User commands
@bot.command(name = "ping", aliases = ["latency"],
			 brief = "Check the bot's latency",
			 help = "Shows the bot's current latency in milliseconds")
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.check(not_blacklisted)
async def ping(ctx):
	await ctx.send(f'{bot.latency * 1000:.2f}ms', delete_after = bot.del_after)
	await ctx.message.delete()


@bot.command(name = "nasa", aliases = ["nasa_pic", "nasa_apod", "nasapic"],
			 brief = "NASA's picture of the day",
			 help = "Get NASA's Astronomy Picture of the Day with explanation")
@commands.cooldown(1, 5, BucketType.user)
@commands.check(not_blacklisted)
async def nasa_pic(ctx):

	if os.path.exists(f'nasa/nasa_pic_{bot.today}.jpg'):
		await ctx.send(f'**{bot.nasa_data["title"]}**\n')
		await ctx.send(file = discord.File(f'nasa/nasa_pic_{bot.today}.jpg', filename = f'nasa_pic_{bot.today}.jpg'))
		await ctx.send(f'**Explanation:** {bot.nasa_data["explanation"]}')
		return

	try:
		fetch_msg = await ctx.send('Fetching NASA picture of the day...')
		nasa_data = api_stuff.get_nasa_apod()
		bot.nasa_data = deepcopy(nasa_data)
		if 'hdurl' in nasa_data:
			url = nasa_data['hdurl']
		else:
			url = nasa_data['url']

		utils.download_from_url(f'nasa/nasa_pic_{bot.today}.jpg', url)

		await ctx.send(f'**{nasa_data["title"]}**\n')
		await ctx.send(file = discord.File(f'nasa/nasa_pic_{bot.today}.jpg', filename = f'nasa_pic_{bot.today}.jpg'))
		await ctx.send(f'**Explanation:** {nasa_data["explanation"]}')
		await fetch_msg.delete()

	except Exception as e:
		await ctx.send(f'Error fetching NASA picture: {e}')


@bot.command(name = "dog", aliases = ["dogpic", "dog_pic"],
			 brief = "Get a random dog picture",
			 help = "Fetches and displays a random dog picture from an API")
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.check(not_blacklisted)
async def dogpic(ctx):
	await get_from_api(ctx.message, api_stuff.get_dog_pic)


@bot.command(name = "cat", aliases = ["catpic", "cat_pic"],
			 brief = "Get a random cat picture",
			 help = "Fetches and displays a random cat picture from an API")
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.check(not_blacklisted)
async def catpic(ctx):
	await get_from_api(ctx.message, api_stuff.get_cat_pic)


@bot.command(name = "fox", aliases = ["foxpic", "fox_pic"],
			 brief = "Get a random fox picture",
			 help = "Fetches and displays a random fox picture from an API")
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.check(not_blacklisted)
async def foxpic(ctx):
	await get_from_api(ctx.message, api_stuff.get_fox_pic)


@bot.command(name = "insult", aliases = ["insults"],
			 brief = "Get a random insult",
			 help = "Fetches and displays a random insult from an API")
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.check(not_blacklisted)
async def insult(ctx):
	await get_from_api(ctx.message, api_stuff.get_insult)


@bot.command(name = "advice", aliases = ["advise", "give_advice"],
			 brief = "Get random advice",
			 help = "Fetches and displays a random piece of advice from an API")
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.check(not_blacklisted)
async def advice(ctx):
	await get_from_api(ctx.message, api_stuff.get_advice)


@bot.command(name = "joke", aliases = ["jokes"],
			 brief = "Get a random joke",
			 help = "Fetches and displays a random joke from an API")
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.check(not_blacklisted)
async def joke(ctx):
	await get_from_api(ctx.message, api_stuff.get_joke)


@bot.command(name = "dice", aliases = ["roll", "dice_roll"],
			 brief = "Roll a dice",
			 help = "Roll a dice between two values",
			 usage = "dice <min> <max>")
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.check(not_blacklisted)
async def dice(ctx):
	await fun_cmds.dice_roll(bot.del_after, ctx.message)


@bot.command(name = "flip", aliases = ["coin_flip", "coinflip"],
			 brief = "Flip a coin",
			 help = "Flip a coin and get either Heads or Tails")
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.check(not_blacklisted)
async def flip(ctx):
	coin_flip = fun_cmds.flip_coin()
	await ctx.send(f'You flipped a coin and got: **{coin_flip}**')


@bot.command(name = "suggest", aliases = ["suggestion"],
			 brief = "Submit a suggestion",
			 help = "Submit a suggestion for the bot",
			 usage = "suggest <suggestion>")
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.check(not_blacklisted)
async def suggest_cmd(ctx):
	await suggest.send_suggestion(bot, ctx.message)


@bot.command(name = "karma", aliases = ["karmapic", "karma_pic"],
			 brief = "Get a random karma picture",
			 help = "Shows a random karma picture from the local collection")
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.check(not_blacklisted)
async def karma(ctx):
	karma_pic = fun_cmds.get_karma_pic()
	if karma_pic is None:
		await ctx.send('No karma pictures found.')
		return
	file_path, file_name = karma_pic
	await ctx.message.channel.send(file=discord.File(file_path, filename=file_name))


@bot.command(name = "echo",
			 brief = "Make the bot say something",
			 help = "Admin only: Makes the bot say the specified message", hidden=True,
			 usage = "echo [channel id] <message>")
@commands.check(is_admin)
async def echo_cmd(ctx):
	await echo.echo(ctx.message, bot.del_after, bot)


# Message event for logging and processing
@bot.event
async def on_message(message):
	if message.author.bot:
		return

	if message.content.startswith('​'):  # Zero-width space
		print(f'[NOT LOGGED] Message from {message.author.global_name} [#{message.channel}]: {message.content}')
		return

	# Process commands first
	await bot.process_commands(message)

	# Don't log command messages
	if message.content.startswith(bot.command_prefix):
		return

	if ((message.channel.id == 1346720879651848202) and (message.author.id == 542798185857286144) and
			(message.content.startswith('FUN FACT'))):
		await message.channel.send('<@&1352341336459841688>', delete_after = 0.5)

	# Log regular messages
	if (message.author != bot.user) and (
			message.author.id not in bot.no_log['user_ids']) and (
			message.channel.id not in bot.no_log['channel_ids']) and (
			message.channel.category_id not in bot.no_log['category_ids']):

		has_attachment = bool(message.attachments)

		reply = None if message.reference is None else str(message.reference.message_id)

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
			with utils.make_file(bot.today) as file:
				file.write(json.dumps(json_data, ensure_ascii = False) + '\n')

		print(f'Message from {message.author.global_name} [#{message.channel}]: {message.content}')
		if has_attachment:
			if os.environ.get('LOCAL_IMG_SAVE') == 'True':
				await utils.save_attachments(message)
			else:
				for attachment in message.attachments:
					await db_stuff.send_attachment(message, attachment)

		db_stuff.send_message(json_data)
		bot.today = utils.formatted_time()


# Reaction role events
@bot.event
async def on_raw_reaction_add(payload):
	if payload.message_id != bot.role_message_id:
		return

	guild = bot.get_guild(payload.guild_id)
	if guild is None:
		return

	try:
		role_id = bot.emoji_to_role[payload.emoji]
	except KeyError:
		return

	role = guild.get_role(role_id)
	if role is None:
		return

	try:
		await payload.member.add_roles(role)
	except discord.HTTPException:
		pass


@bot.event
async def on_raw_reaction_remove(payload):
	if payload.message_id != bot.role_message_id:
		return

	guild = bot.get_guild(payload.guild_id)
	if guild is None:
		return

	try:
		role_id = bot.emoji_to_role[payload.emoji]
	except KeyError:
		return

	role = guild.get_role(role_id)
	if role is None:
		return

	member = guild.get_member(payload.user_id)
	if member is None:
		return

	try:
		await member.remove_roles(role)
	except discord.HTTPException:
		pass

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
	if member.bot:
		return
	logging_channel = bot.logging_channels.get('voice')

	# Member joined channel
	if before.channel is None and after.channel is not None:
		voice_log.handle_join(member, after)
		embed = discord.Embed(title=f'{member.global_name} joined #{after.channel.name}', color=discord.Color.green())
		embed.set_author(name=member.display_name, icon_url=member.avatar.url)
		embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
		if logging_channel:
			await logging_channel.send(embed=embed)


	# Member left channel
	elif before.channel is not None and after.channel is None:
		voice_log.handle_leave(member, before)
		embed = discord.Embed(title=f'{member.global_name} left #{before.channel.name}', color=discord.Color.red())
		embed.set_author(name=member.display_name, icon_url=member.avatar.url)
		embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
		if logging_channel:
			await logging_channel.send(embed=embed)

	# Member moved to another channel
	elif before.channel != after.channel:
		assert after.channel is not None
		voice_log.handle_move(member, before, after)
		embed = discord.Embed(title=f'{member.global_name} moved from #{before.channel.name} to'
									f' #{after.channel.name}', color=discord.Color.blue())
		embed.set_author(name=member.display_name, icon_url=member.avatar.url)
		embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
		if logging_channel:
			await logging_channel.send(embed=embed)


# Helper for API commands
async def get_from_api(message, api_func):
	try:
		data = api_func()
		await message.channel.send(data)
	except Exception as e:
		await message.channel.send(f'Error fetching data: {e}')


# Run the bot
bot.run(os.getenv('TOKEN'))