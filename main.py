# pylint: disable=trailing-whitespace, line-too-long
import atexit
import datetime
import logging.handlers
import os
import random
import re

import discord
import discord.utils
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv

from command_utils.CContext import CoolBot, CContext
from custom_logging import voice_log
from utils import db_stuff, utils

load_dotenv()


@atexit.register
def on_exit():
    db_stuff.disconnect()

if not os.path.exists('logs'):
    os.mkdir('logs')

dt_fmt = '%Y-%m-%d %H:%M:%S'
log_formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')

debug_handler = logging.handlers.RotatingFileHandler(
    filename='logs/debug.log',
    encoding='utf-8',
    maxBytes=8 * 1024 * 1024,
    backupCount=3
)
debug_handler.setFormatter(log_formatter)
debug_handler.setLevel(logging.DEBUG)

err_handler = logging.handlers.RotatingFileHandler(
    filename='logs/err.log',
    encoding='utf-8',
    maxBytes=8 * 1024 * 1024,
    backupCount=3
)
err_handler.setFormatter(log_formatter)
err_handler.setLevel(logging.WARNING)

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
logger.addHandler(debug_handler)
logger.addHandler(err_handler)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
discord.utils.setup_logging(handler=handler, level=logging.DEBUG, root=False)

bot = CoolBot(intents=discord.Intents.all(), case_insensitive=True, log_handler=None)

regex = r'\b((?:https?|ftp|file):\/\/[-a-zA-Z0-9+&@#\/%?=~_|!:,.;]*[-a-zA-Z0-9+&@#\/%=~_|])'
url_pattern = re.compile(regex, re.IGNORECASE)


def find_url_in_string(string: str) -> bool:
    """
    Find a URL in a string using a regular expression.
    :param string: The string to search for a URL.
    :return: If a URL is found, return True; otherwise, return False.
    """
    global url_pattern
    
    match = url_pattern.search(string)
    return match is not None


# Bot configuration
@bot.event
async def on_ready() -> None:
    await load_extensions()
    utils.check_env_variables()
    utils.clean_up_APOD()
    
    logger.info(f"Loaded {len(bot.cogs)} cogs:")
    for cog in bot.cogs:
        logger.info(f" - {cog}")
    
    logger.info(f"Total commands: {len(bot.commands)}")
    if bot.config.maintenance_mode:
        logger.info("Bot is in maintenance mode. Only admins can use commands.")
    
    if bot.config.staging:
        logger.info("Staging mode is enabled. Most features are disabled.")
    
    # Reconnect voice states
    if not bot.config.staging:
        for channel in bot.get_all_channels():
            if not isinstance(channel, discord.VoiceChannel):
                continue
            
            for member in channel.members:
                if member.bot:
                    continue
                
                voice_log.handle_join(member, channel)
                logger.info(f'Reconnected voice state for {member.name} in {channel.name}')
                
    assert not bot.user is None
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    logger.info('------')
    
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
    
    async def send_bot_help(self, mapping: dict[commands.Cog, list[commands.Command]]) -> None: # type: ignore
        ctx: Context = self.context
        if bot.blacklist.is_blacklisted(ctx.author.id):
            await ctx.message.channel.send('You are not allowed to use this command.',
                                           delete_after=bot.config.del_after)
            return
        
        is_admin: bool = ctx.author.id in bot.config.admin_ids or ctx.author.id in bot.config.dev_ids
        embeds = []
        
        # Create a page for each cog
        for cog, cmds in mapping.items():
            cog_name = getattr(cog, "qualified_name", "Miscellaneous")
            
            # Filter commands the user can run
            regular_cmds: list[commands.Command] = await self.filter_commands(cmds, sort=True)
            
            admin_cmds: list[commands.Command] = []
            if is_admin:
                all_cmds: list[commands.Command] = cmds
                regular_cmd_names: set[str] = {cmd.qualified_name for cmd in regular_cmds}
                admin_cmds = [cmd for cmd in all_cmds if cmd.qualified_name not in regular_cmd_names]
            
            # Only create a page if there are commands to show
            if not regular_cmds and not admin_cmds:
                continue
            
            embed: discord.Embed = discord.Embed(
                    title=f"{cog_name} Commands",
                    description=f"Use `{ctx.prefix}help [command]` for more info on a command.",
                    color=discord.Color.blue()
            )
            
            if regular_cmds:
                cmd_list: list[str] = []
                for cmd in regular_cmds:
                    brief = cmd.brief or "No description"
                    usage = cmd.usage or f"{ctx.prefix}{cmd.name}"
                    cmd_list.append(f"`{usage}` - {brief}")
                
                embed.add_field(
                        name="Commands",
                        value="\n".join(cmd_list),
                        inline=False
                )
            
            if admin_cmds:
                admin_cmd_list: list[str] = []
                for cmd in admin_cmds:
                    brief = cmd.brief or "No description"
                    usage = cmd.usage or f"{ctx.prefix}{cmd.name}"
                    admin_cmd_list.append(f"`{usage}` - {brief}")
                
                embed.add_field(
                        name="Admin Commands",
                        value="\n".join(admin_cmd_list),
                        inline=False
                )
            
            embeds.append(embed)
        
        if not embeds:
            await ctx.send("No commands to show.")
            return
        
        # Add a footer to each embed
        for i, embed in enumerate(embeds):
            embed.set_footer(text=f"Page {i + 1}/{len(embeds)}")
        
        # If there's only one page, no need for pagination
        if len(embeds) == 1:
            await ctx.send(embed=embeds[0])
            return
        
        # Use buttons for pagination
        pagination_view: HelpPaginationView = HelpPaginationView(embeds, ctx.author)
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
            await interaction.response().send_message("You cannot use these buttons.", ephemeral=True)  # type: ignore
            return False
        return True
    
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, emoji="⬅️",  # type: ignore
                       custom_id="prev")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response().edit_message(embed=self.embeds[self.current_page], view=self)  # type: ignore
    
    @discord.ui.button(label="Page 1/2", style=discord.ButtonStyle.secondary, disabled=True,  # type: ignore
                       custom_id="page")
    async def page_button(self, interaction: discord.Interaction, button) -> None:
        # This button is just a label and doesn't do anything when clicked
        pass
    
    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, emoji="➡️", custom_id="next")  # type: ignore
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)  # type: ignore


bot.help_command = CustomHelpCommand()


@bot.event
async def on_command_error(ctx: CContext, error: discord.ext.commands.CommandError):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send('This command is on cooldown. Please try again in ' +
                       f'{utils.seconds_to_human_readable(error.retry_after)}.')
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send('This command cannot be used in private messages.', delete_after=bot.config.del_after)
        await ctx.delete()
    
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'Missing required argument: {error.param.name}', delete_after=bot.config.del_after)
        await ctx.delete()
    
    elif isinstance(error, commands.BotMissingPermissions):
        missing = ', '.join(error.missing_permissions)
        await ctx.send(f'I am missing the following permissions to run this command: {missing}',
                       delete_after=bot.config.del_after)
        await ctx.delete()
    
    elif isinstance(error, commands.CheckFailure):
        await ctx.send('You do not have permission to use this command.', delete_after=bot.config.del_after)
        await ctx.delete()
    
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f'Bad argument: {error}')
    
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(f'Command not found: {error}', delete_after=bot.config.del_after)
        await ctx.delete()
    
    else:
        logger.error(f'Error in command {ctx.command}: {error}', exc_info=error)


async def landmine_explode(message: discord.Message, forced=False) -> None:
    assert not isinstance(message.author, discord.User)
    try:
        msgs: list[str] = ["Landmine exploded!", "You stepped in a claymore!", "A grenade exploded next to you!",
                "A rogue cluster bomblet went off!", "You tripped down some stairs. (How did you manage that one?)",
                "You went too close to a proximity mine.", "A tree fell on you. (What an idiot.)",
                "You were hit by a car.", "You got struck by lightning.", "You fell off a cliff.",
                "You tripped on a rock and drowned in a puddle.",
                "A subspace tripmine appeared under you and detonated.",
                "You fell beyond the event horizon of a black hole and disappeared forever.",
                "nuke"]
        msg: str = random.choice(msgs)
        if msg == "nuke":
            await message.author.timeout(datetime.timedelta(seconds=60), reason='Nuke exploded')
            await message.reply(f'A nuclear bomb went off below your feet! You cannot talk for 60 seconds.')
        else:
            await message.author.timeout(datetime.timedelta(seconds=10), reason='Landmine exploded')
            await message.reply(f'{msg} You cannot talk for 10 seconds.')
        
        if not forced:
            await message.channel.send(
                f'There are now {bot.landmine_channels[message.channel.id] - 1} traps left in this channel.')
            bot.landmine_channels[message.channel.id] -= 1
            if bot.landmine_channels[message.channel.id] == 0:
                del bot.landmine_channels[message.channel.id]
        else:
            left = bot.landmine_channels.get(message.channel.id, 0)
            await message.channel.send(f'There are now {left} traps left in this channel.')
            bot.forced_landmines.remove(message.author.id)
            
    except Exception:
        pass


async def check_landmine(message: discord.Message) -> None:
    if isinstance(message.author, discord.User):
        return
    if message.author.id in bot.forced_landmines:
        await landmine_explode(message, forced=True)
        return
        
    if message.channel.id not in bot.landmine_channels.keys():
        return
    
    if (message.author.id in bot.config.admin_ids or message.author.id in bot.config.dev_ids or
            message.author.guild_permissions.administrator):
        return
    
    if random.random() < 0.05:  # 5% chance for a landmine to explode
        await landmine_explode(message)


# Message event for logging and processing
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    
    commands_enabled: bool = True
    if bot.config.staging:
        commands_enabled = False
    if bot.config.maintenance_mode:
        commands_enabled = False
    if message.author.id in bot.config.admin_ids or message.author.id in bot.config.dev_ids:
        commands_enabled = True
    
    assert isinstance(bot.command_prefix, str)
    if bot.config.staging:
        if commands_enabled and message.content.startswith(bot.command_prefix):
            bot.config.today = utils.formatted_today()
            await bot.process_commands(message)
        return
    
    
    if message.content.startswith('\u200B'):  # Zero-width space
        logger.info(f'[NOT LOGGED] Message from {message.author.global_name} [#{message.channel}]: {message.content}')
        return
    
    await check_landmine(message)
    
    if (message.channel.id == bot.config.counting_channel
            and find_url_in_string(message.content)
            and not message.author.bot
            and not (message.author.id in bot.config.admin_ids
                    or message.author.id in bot.config.dev_ids)):
        # If the message contains a URL, delete it and send a warning
        await message.delete()
        await message.channel.send('Please do not send links in this channel.',
                delete_after=bot.config.del_after
        )
    
    if commands_enabled and message.content.startswith(bot.command_prefix):
        bot.config.today = utils.formatted_today()
        await bot.process_commands(message)
    
    
    elif not commands_enabled and message.content.startswith(bot.command_prefix):
        await message.channel.send('The bot is currently in maintenance mode. Please try again later.')
        return
    
    if ((message.channel.id == 1346720879651848202) and (message.author.id == 542798185857286144) and
            (message.content.startswith('FUN FACT'))):
        await message.channel.send('<@&1352341336459841688>', delete_after=2)
    
    # Log regular messages
    if ((message.author != bot.user) and
            hasattr(message.channel, 'category_id') and (
            message.author.id not in bot.config.no_log.user_ids) and (
            message.channel.id not in bot.config.no_log.channel_ids) and (
            message.channel.category_id not in bot.config.no_log.category_ids)):
        
        await utils.log_msg(message)
    
    if message.channel.id == bot.config.counting_channel and not bot.config.staging:
        await utils.counting_msg(message, bot)
        bot.config.save()
    
    if message.content.startswith('!f'):
        if not bot.config.tts_requires_role:
            ctx: CContext = await bot.get_context(message)
            await ctx.invoke(bot.get_command('tts'), message=message.content.replace("!f", "").strip())
            return
        
        if bot.config.required_tts_role == 0:
            logger.warning('TTS role requirement is enabled, but no role ID is set in the config.')
            await message.reply('TTS commands are currently unavailable. Please contact an administrator.')
            return
        
        has_role: bool = False
        if isinstance(message.author, discord.User):
            await message.reply('TTS commands are only available in guild channels.')
            return
        
        for role in message.author.roles:
            if role.id == bot.config.required_tts_role:
                has_role = True
                break
        
        if not has_role:
            await message.reply('You do not have the required role to use TTS commands.')
            return
        
        ctx: CContext = await bot.get_context(message)
        await ctx.invoke(bot.get_command('tts'), message=message.content.replace("!f", "").strip())
        
# Reaction role events
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.guild_id is None:
        return
    if payload.member is None:
        return
    if bot.config.staging:
        return
    
    if payload.message_id != bot.config.reaction_roles.message_id:
        return
    
    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return
    
    emoji_to_role = bot.config.get_emoji_to_role_discord_objects()
    try:
        role_id = emoji_to_role[payload.emoji]
    except KeyError:
        logger.info(f"Emoji {payload.emoji} not found in emoji_to_role mapping.")
        return
    
    role = guild.get_role(role_id)
    if role is None:
        logger.info(f"Role with ID {role_id} not found for emoji {payload.emoji}.")
        return
    
    try:
        await payload.member.add_roles(role)
    except discord.HTTPException:
        pass


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if payload.message_id != bot.config.reaction_roles.message_id:
        return
    if bot.config.staging:
        return
    
    if payload.guild_id is None:
        return
    if payload.member is None:
        return
    
    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return
    
    emoji_to_role = bot.config.get_emoji_to_role_discord_objects()
    try:
        role_id = emoji_to_role[payload.emoji]
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
    if bot.config.staging:
        return
    
    logging_channel = bot.get_channel(bot.config.logging_channels.voice) if bot.config.logging_channels.voice else None
    
    if not isinstance(logging_channel, discord.TextChannel):
        return
    
    url = member.avatar.url if member.avatar is not None else member.default_avatar.url
    
    # Member joined channel
    if before.channel is None and after.channel is not None:
        voice_log.handle_join(member, after)
        embed = discord.Embed(title=f'{member.display_name} joined #{after.channel.name}',
                              color=discord.Color.green())
        embed.set_author(name=member.name, icon_url=url)
        embed.timestamp = discord.utils.utcnow()
        if logging_channel:
            await logging_channel.send(embed=embed)
    
    
    # Member left channel
    elif before.channel is not None and after.channel is None:
        voice_log.handle_leave(member)
        if logging_channel:
            embed = discord.Embed(title=f'{member.display_name} left #{before.channel.name}',
                                  color=discord.Color.red())
            embed.set_author(name=member.name, icon_url=url)
            embed.timestamp = discord.utils.utcnow()
            await logging_channel.send(embed=embed)
        
        if before.channel.name.startswith('private_'):
            if before.channel and len(before.channel.members) == 0:
                await before.channel.delete(reason='Private VC empty after member left')
        
        if before.channel.name.startswith('temp_'):
            if before.channel and len(before.channel.members) == 0:
                await before.channel.delete(reason='Temp VC empty after member left')
        
        if bot.vc_client is None:
            return
        
        if len(before.channel.members) == 1 and bot.vc_client.channel.id == before.channel.id:
            await bot.vc_client.disconnect()
            bot.vc_client = None
    
    # Member moved to another channel
    elif before.channel != after.channel:
        if before.channel is None or after.channel is None:
            return
        voice_log.handle_move(member, before, after)
        embed = discord.Embed(title=f'{member.display_name} moved from #{before.channel.name} to'
                                    f' #{after.channel.name}', color=discord.Color.blue())
        embed.set_author(name=member.name, icon_url=url)
        embed.timestamp = discord.utils.utcnow()
        if logging_channel:
            await logging_channel.send(embed=embed)
        
        if before.channel.name.startswith('private_'):
            if before.channel and len(before.channel.members) == 0:
                await before.channel.delete(reason='Private VC empty after member left')
        
        if bot.vc_client is None:
            return
        
        if len(before.channel.members) == 1 and bot.vc_client.channel.id == before.channel.id:
            await bot.vc_client.disconnect()
            bot.vc_client = None


@bot.event
async def on_raw_message_delete(payload: discord.RawMessageDeleteEvent) -> None:
    if bot.config.staging:
        return
    
    if payload.channel_id != bot.config.counting_channel:
        return
    
    if payload.message_id != bot.config.last_counted_message_id:
        return
    
    unknown_author: bool = False
    author_id: int = 0
    
    if payload.cached_message is not None:
        author_id = payload.cached_message.author.id
    else:
        msg = db_stuff.get_from_db('messages', {'id': payload.message_id})
        if msg is not None:
            author_id = int(msg['author_id'])
        else:
            unknown_author = True
    
    channel = bot.get_channel(payload.channel_id)
    assert isinstance(channel, discord.TextChannel)
    
    if unknown_author or author_id == 0:
        await channel.send(f'Unknown user deleted their message. The next number is {bot.config.last_count+1}')
        return
    
    await channel.send(f'<@{author_id}> deleted their message. The next number is `{bot.config.last_count+1}`')


async def load_extensions() -> None:
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('_'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            logger.info(f'Loaded {filename[:-3]}')


@bot.check
async def not_blacklisted(ctx: CContext):
    """
    Check if the user is blacklisted from using commands.
    """
    if bot.blacklist.is_blacklisted(ctx.author.id):
        return False
    return True


# Run the bot
token = os.getenv('TOKEN')
if not isinstance(token, str):
    raise TypeError('TOKEN environment variable not set.')
bot.run(token=token, reconnect=True)
