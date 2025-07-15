import atexit
import json
import os
from pathlib import Path

import discord
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv

from custom_logging import voice_log
from utils import db_stuff, utils

load_dotenv()


@atexit.register
def on_exit():
	db_stuff.disconnect()


def load_config():
	"""Load configuration from config.json file or create default if not exists"""
	config_path = Path("config.json")
	
	# Default configuration
	default_config: dict[str, str | int | list[int] | dict[str, int | dict[str, list[int]] | discord.TextChannel]] = {
		"command_prefix":   "f!",
		"del_after":        3,
		"admin_ids":        [235644709714788352, 542798185857286144, 937278965557641227],
		"dev_ids":          [542798185857286144],
		"no_log":           {
			"user_ids":     [1329366814517628969, 1329366963805491251, 1329367238146396211,
							 1329367408330145805, 235148962103951360, 1299640624848306177],
			"channel_ids":  [],
			"category_ids": [1329366612821938207]
		},
		"send_blacklist":   {
			"channel_ids":  [],
			"category_ids": []
		},
		"logging_channels": {
			"voice": 1329366741909770261
		},
		"maintenance_mode": False,
	}
	
	# Create a config file with defaults if it doesn't exist
	if not config_path.exists():
		with open(config_path, "w", encoding="utf-8") as _f:
			json.dump(default_config, _f, indent=4)
		print("Created default config.json file")
		return default_config
	
	# Load existing config
	try:
		with open(config_path, "r", encoding="utf-8") as _f:
			_config = json.load(_f)
		print("Configuration loaded successfully")
		return _config
	except Exception as e:
		print(f"Error loading config: {e}")
		print("Writing default configuration")
		with open(config_path, "w", encoding="utf-8") as _f:
			json.dump(default_config, _f, indent=4)
		return default_config


# Load configuration
config = load_config()

# Create bot with intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config["command_prefix"], intents=intents)

# Initialize bot configuration from loaded config
bot.today = utils.formatted_time()
bot.del_after = config["del_after"]
bot.admin_ids = config["admin_ids"]
bot.dev_ids = config["dev_ids"]
bot.no_log = config["no_log"]
bot.logging_channels = config["logging_channels"]
bot.send_blacklist = config["send_blacklist"]
bot.maintenance_mode = config["maintenance_mode"]
bot.config = config

# Reaction roles
bot.role_message_id = 1380639010564603976
emoji_to_role: dict[discord.PartialEmoji, int] = {
	discord.PartialEmoji.from_str('<:jjs:1380607586231128155>'):         1314274909815439420,
	discord.PartialEmoji(name='❕'): 1321214081977421916,
	discord.PartialEmoji.from_str('<:grass_block:1380607192717328505>'): 1380623674918310079,
	discord.PartialEmoji.from_str('<:Vrchat:1380607441691214048>'):      1380623882574368939,
	discord.PartialEmoji.from_str('<:rust:1380606572127850639>'):        1130284770757197896,
	discord.PartialEmoji(name='❔'): 1352341336459841688,
	discord.PartialEmoji(name='🎬'): 1380624012090150913,
	discord.PartialEmoji(name='🎨'): 1295024229799952394,
}

bot.emoji_to_role = emoji_to_role

# Load blacklist
if not os.path.isfile('blacklist_users.json'):
	with open('blacklist_users.json', 'w') as blacklist_file:
		json.dump(bot.blacklist_ids, blacklist_file, indent=4)
else:
	with open('blacklist_users.json', 'r') as blacklist_file:
		bot.blacklist_ids = json.load(blacklist_file)


# Bot configuration
@bot.event
async def on_ready() -> None:
	await load_extensions()
	utils.check_env_variables()
	utils.clean_up_APOD()
	
	print(f"Loaded {len(bot.cogs)} cogs:")
	for cog in bot.cogs:
		print(f" - {cog}")
	
	print(f"Total commands: {len(bot.commands)}")
	if bot.maintenance_mode:
		print("Bot is in maintenance mode. Only admins can use commands.")
	
	print(f'Logged in as {bot.user} (ID: {bot.user.id})')
	print('------')
	
	# Apply blacklist to channel
	channel = bot.get_channel(1379193761791213618)
	for u_id in bot.blacklist_ids['ids']:
		await channel.set_permissions(get(bot.get_all_members(), id=u_id), send_messages=False)
	
	for key, value in bot.logging_channels.items():
		channel: discord.TextChannel = bot.get_channel(value)
		bot.logging_channels[key] = channel
	
	guild = bot.get_guild(1081760248433492140)
	for vc_channel in guild.voice_channels:
		members = [member for member in vc_channel.members]
		if members:
			for member in members:
				voice_log.handle_join(member, vc_channel)
	
	react_role_msg = await bot.get_channel(1337465612875595776).fetch_message(bot.role_message_id)
	if react_role_msg is None:
		print(f"Role message with ID {bot.role_message_id} not found. Reaction roles will not work.")
	else:
		# Add reaction roles to the message
		for emoji, role_id in bot.emoji_to_role.items():
			role = guild.get_role(role_id)
			if role is not None:
				try:
					await react_role_msg.add_reaction(emoji)
				except Exception as e:
					print(f"Failed to add reaction {emoji} for role {role.name}: {e}")
			
			else:
				print(f"Role with ID {role_id} not found. Skipping emoji {emoji}.")
	
	await bot.change_presence(activity=discord.CustomActivity(name='f!help'))


# Custom help command formatting
class CustomHelpCommand(commands.DefaultHelpCommand):
	def __init__(self):
		super().__init__(
				no_category="Miscellaneous",
				width=100,
				sort_commands=True,
				dm_help=False
		)
	
	async def send_bot_help(self, mapping):
		ctx = self.context
		if ctx.author.id in bot.blacklist_ids['ids']:
			await ctx.message.channel.send('You are not allowed to use this command.', delete_after=bot.del_after)
			return
		
		# Check if the user is an admin or developer
		is_admin = ctx.author.id in bot.admin_ids or ctx.author.id in bot.dev_ids
		
		# list of embeds for each cog
		embeds = []
		
		main_embed = discord.Embed(
				title="Bot Help",
				description=f"Use `{ctx.prefix}help [command/category]` for more info",
				color=discord.Color.blue()
		)
		main_embed.set_footer(text=f"Type {ctx.prefix}help <command/category> for detailed info")
		
		admin_embed = None
		if is_admin:
			admin_embed = discord.Embed(
					title="Admin Commands",
					description="These commands are only available to administrators",
					color=discord.Color.red()
			)
		
		# Process each cog
		for cog, cmds in mapping.items():
			cog_name = getattr(cog, "qualified_name", "Miscellaneous")
			
			# Get commands the user can use (with permission checks)
			regular_cmds = await self.filter_commands(cmds, sort=True)
			
			if regular_cmds:
				cmd_list = []
				for cmd in regular_cmds:
					# Add command with its brief description
					brief = cmd.brief or "No description"
					usage = cmd.usage or f"{ctx.prefix}{cmd.name}"
					cmd_list.append(f"`{usage}` - {brief}")
				
				main_embed.add_field(
						name=cog_name,
						value="\n".join(cmd_list) if cmd_list else "No commands available",
						inline=False
				)
			
			# For admins, also get admin-only commands
			if is_admin and admin_embed:
				# Get all commands without permission checks
				all_cmds = cmds  # Get all commands in this cog
				
				# Find admin-only commands by comparing names
				regular_cmd_names = {cmd.qualified_name for cmd in regular_cmds}
				admin_cmds = [cmd for cmd in all_cmds if cmd.qualified_name not in regular_cmd_names]
				
				if admin_cmds:
					admin_cmd_list = []
					for cmd in admin_cmds:
						# Add command with its brief description
						brief = cmd.brief or "No description"
						usage = cmd.usage or f"{ctx.prefix}{cmd.name}"
						admin_cmd_list.append(f"`{usage}` - {brief}")
					
					admin_embed.add_field(
							name=cog_name,
							value="\n".join(admin_cmd_list),
							inline=False
					)
		
		embeds.append(main_embed)
		
		# Add admin embed if it has content
		if admin_embed and len(admin_embed.fields) > 0:
			embeds.append(admin_embed)
		
		# If there's only one page, no need for pagination
		if len(embeds) == 1:
			await ctx.send(embed=embeds[0])
			return
		
		# Use buttons for pagination
		pagination_view = HelpPaginationView(embeds, ctx.author)
		await ctx.send(embed=embeds[0], view=pagination_view)


class HelpPaginationView(discord.ui.View):
	def __init__(self, embeds: list[discord.Embed], author: discord.User | discord.Member) -> None:
		super().__init__(timeout=60)
		self.embeds: list[discord.Embed] = embeds
		self.author: discord.User | discord.Member = author
		self.current_page: int = 0
		self.total_pages: int = len(embeds)
		
		# Update button states initially
		self.update_buttons()
	
	def update_buttons(self) -> None:
		# Disable previous button on first page
		self.prev_button.disabled = (self.current_page == 0)
		# Disable next button on last page
		self.next_button.disabled = (self.current_page == self.total_pages - 1)
		# Update the page counter
		self.page_button.label = f"Page {self.current_page + 1}/{self.total_pages}"
	
	async def interaction_check(self, interaction: discord.Interaction) -> bool:
		# Only allow the original command author to use the buttons
		if interaction.user != self.author:
			await interaction.response().send_message("You cannot use these buttons.", ephemeral=True)
			return False
		return True
	
	@discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, emoji="⬅️",
	                   custom_id="prev")  # type: ignore
	async def prev_button(self, interaction: discord.Interaction, button) -> None:
		if self.current_page > 0:
			self.current_page -= 1
			self.update_buttons()
			await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)  # type: ignore
	
	@discord.ui.button(label="Page 1/2", style=discord.ButtonStyle.secondary, disabled=True,
	                   custom_id="page")  # type: ignore
	async def page_button(self, interaction: discord.Interaction, button) -> None:
		# This button is just a label and doesn't do anything when clicked
		pass
	
	@discord.ui.button(label="Next", style=discord.ButtonStyle.primary, emoji="➡️", custom_id="next")  # type: ignore
	async def next_button(self, interaction: discord.Interaction, button) -> None:
		if self.current_page < self.total_pages - 1:
			self.current_page += 1
			self.update_buttons()
			await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)  # type: ignore


# Apply custom help command
bot.help_command = CustomHelpCommand()


@bot.event
async def on_command_error(ctx: discord.ext.commands.Context, error: discord.ext.commands.CommandError):
	if isinstance(error, commands.CommandOnCooldown):
		await ctx.message.channel.send(
				f'This command is on cooldown. Please try again in {error.retry_after:.0f} seconds.',
				delete_after=bot.del_after
		)
		await ctx.message.delete()
	elif isinstance(error, commands.CheckFailure):
		await ctx.message.channel.send('You do not have permission to use this command.', delete_after=bot.del_after)
		await ctx.message.delete()
	
	else:
		print(f"Unhandled error: {error}")


# Message event for logging and processing
@bot.event
async def on_message(message: discord.Message):
	bot.today = utils.formatted_today()
	if message.author.bot:
		return
	
	if message.content.startswith('​'):  # Zero-width space
		print(f'[NOT LOGGED] Message from {message.author.global_name} [#{message.channel}]: {message.content}')
		return
	
	# Process commands first
	if (not bot.maintenance_mode) or (message.author.id in bot.admin_ids) or (message.author.id in bot.dev_ids):
		await bot.process_commands(message)
		
		# Don't log command messages
		if message.content.startswith(bot.command_prefix):
			return
	elif bot.maintenance_mode:
		await message.channel.send('The bot is currently in maintenance mode. Please try again later.')
	
	if ((message.channel.id == 1346720879651848202) and (message.author.id == 542798185857286144) and
			(message.content.startswith('FUN FACT'))):
		await message.channel.send('<@&1352341336459841688>', delete_after=1)
		print('Fun fact ping sent')
	
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
			'channel':            message.channel.name,
			'channel_id':         str(message.channel.id)
		}
		
		if os.getenv('LOCAL_SAVE') == 'True':
			with utils.make_file() as file:
				file.write(json.dumps(json_data, ensure_ascii=False) + '\n')
		
		print(f'Message from {message.author.display_name} [#{message.channel}]: {message.content}')
		if has_attachment:
			if os.environ.get('LOCAL_IMG_SAVE') == 'True':
				await utils.save_attachments(message)
			else:
				for attachment in message.attachments:
					await db_stuff.send_attachment(message, attachment)
		
		db_stuff.send_message(json_data)


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
		embed = discord.Embed(title=f'{member.display_name} joined #{after.channel.name}',
		                      color=discord.Color.green())
		embed.set_author(name=member.name, icon_url=member.avatar.url)
		embed.timestamp = discord.utils.utcnow()
		if logging_channel:
			await logging_channel.send(embed=embed)
	
	
	# Member left channel
	elif before.channel is not None and after.channel is None:
		voice_log.handle_leave(member)
		if logging_channel:
			embed = discord.Embed(title=f'{member.display_name} left #{before.channel.name}',
			                      color=discord.Color.red())
			embed.set_author(name=member.name, icon_url=member.avatar.url)
			embed.timestamp = discord.utils.utcnow()
			await logging_channel.send(embed=embed)
		
		if before.channel.name.startswith('private_'):
			if before.channel and len(before.channel.members) == 0:
				await before.channel.delete(reason='Private VC empty after member left')
	
	# Member moved to another channel
	elif before.channel != after.channel:
		if after.channel is None:
			return
		voice_log.handle_move(member, before, after)
		embed = discord.Embed(title=f'{member.display_name} moved from #{before.channel.name} to'
		                            f' #{after.channel.name}', color=discord.Color.blue())
		embed.set_author(name=member.name, icon_url=member.avatar.url)
		embed.timestamp = discord.utils.utcnow()
		if logging_channel:
			await logging_channel.send(embed=embed)


@bot.event
async def on_guild_update(before: discord.Guild, after: discord.Guild):
	if after.vanity_url_code != 'foxeshaven':
		await bot.get_channel(1329366175796432898).send("<@235644709714788352> <@542798185857286144> Guild invite " +
														"has been updated!")


async def load_extensions() -> None:
	for filename in os.listdir('./cogs'):
		if filename.endswith('.py') and not filename.startswith('_'):
			await bot.load_extension(f'cogs.{filename[:-3]}')
			print(f'Loaded {filename[:-3]}')


@bot.check
async def not_blacklisted(ctx: discord.ext.commands.Context):
	"""
	Check if the user is blacklisted from using commands.
	"""
	if ctx.author.id in bot.blacklist_ids['ids']:
		await ctx.send('You are not allowed to use this command.', delete_after=bot.del_after)
		return False
	return True


# Run the bot
bot.run(token=os.getenv('TOKEN'), reconnect=True)

# TODO: Take over the url deleting in counting from yag
"""
# Regular Expression to extract URL from the string
import re

regex = r'\b((?:https?|ftp|file):\/\/[-a-zA-Z0-9+&@#\/%?=~_|!:,.;]*[-a-zA-Z0-9+&@#\/%=~_|])'

# Compile the Regular Expression
p = re.compile(regex, re.IGNORECASE)

# Find the match between string and the regular expression
while True:
	s = input("Enter a string to find URLs: ")
	m = p.finditer(s)
	found = False
	if m:
		for match in m:
			found = True
			break
	
	if found:
		print("URLs found in the string.")
	else:
		print("No URLs found in the string.")
"""