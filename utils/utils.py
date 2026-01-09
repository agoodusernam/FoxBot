import datetime
import json
import os
import urllib.request
from io import TextIOWrapper
from pathlib import Path
from typing import Union

import discord
from discord import HTTPException

from command_utils.CContext import CoolBot
from utils import db_stuff  # type: ignore # IDE hates this, and so do I, but it seems to work


def eval_count_msg(message: str) -> int | None:
    allowed: str = "0123456789*/-+.()%^&<>|~"
    for char in message:
        if char not in allowed:
            return None
    
    try:
        return round(float(eval(message)))
    except (SyntaxError, ValueError, TypeError):
        return None


def get_id_from_str(u_id: str) -> int | None:
    """
	Converts a string representation of a user or channel ID to an integer ID.
	:param u_id: str: The string representation of the user or channel ID, which may include special characters like <, >, @, or #.
	:return: int: The integer ID extracted from the string, or None if the conversion fails.
	"""
    u_id = u_id.replace("<", "", 1)
    u_id = u_id.replace(">", "", 1)
    u_id = u_id.replace("@", "", 1)
    u_id = u_id.replace("#", "", 1)
    u_id = u_id.replace("&", "", 1)
    try:
        return int(u_id)
    except ValueError:
        raise ValueError("Invalid user ID")


def formatted_time() -> str:
    """
	Generates a formatted string representing the current time in 'dd-mm-yyyy_HH-MM-SS' format.
	:return: str: The current time in 'dd-mm-yyyy_HH-MM-SS' format.
	"""
    return datetime.datetime.now(datetime.timezone.utc).strftime('%d-%m-%Y_%H-%M-%S')


def formatted_today() -> str:
    """
	Generates a formatted string representing the current date in 'dd-mm-yyyy' format.
	:return: str: The current date in 'dd-mm-yyyy' format.
	"""
    return datetime.datetime.now(datetime.timezone.utc).strftime('%d-%m-%Y')


def make_file() -> TextIOWrapper:
    """
	Creates a new file with the current date in the 'data' directory.
	:return: TextIOWrapper: A file object for the newly created file.
	"""
    if not os.path.exists('../data/attachments'):
        os.makedirs('../data/attachments')
    return open(f'data/{formatted_today()}.json', 'a+', encoding='utf-8')


def make_empty_file(path: Path) -> None:
    """
	Creates an empty file at the specified path if it does not already exist.
	:param path: str | Path: The path where the empty file will be created.
	:return:
	"""
    if not os.path.exists(path.parent):
        os.makedirs(path.parent, exist_ok=True)
    if not os.path.exists(path):
        with open(path, 'x'):
            pass


async def save_attachments(message: discord.Message) -> int:
    """
	Saves all attachments from a Discord message to a local directory.
	:param message: discord.Message: The message containing attachments to be saved.
	:return: None
	"""
    attach_count: int = len(message.attachments)
    if attach_count == 0:
        return 0
    
    saved: int = 0
    
    for i, attachment in enumerate(message.attachments):
        file_ext: str = "".join(Path(attachment.filename).suffixes)
        base_path: Path = Path(os.path.abspath('data/attachments')) / str(message.author.id)
        file_path: Path
        if attach_count == 1:
            file_path = base_path / (str(message.id) + file_ext)
        else:
            # message has > 1 attachment
            file_path = base_path / str(message.id) / (str(i) + file_ext)
        make_empty_file(file_path)
        
        try:
            await attachment.save(file_path)
            saved += 1
        except discord.NotFound:
            print(f'Attachment {i + 1} of {attach_count} for message {message.id} was deleted before it could be saved.')
        except HTTPException:
            print(f'HTTP Error while saving attachment {i + 1} of {attach_count} for message {message.id}')
        except OSError:
            print(f'Error while writing attachment {i + 1} of {attach_count} for message {message.id}')
        
    return saved


def download_from_url(path: str | Path, url: str) -> None:
    """
	Downloads a file from a given URL and saves it to the specified path.
	:param path: str | Path: The path where the file will be saved.
	:param url: str: The URL from which the file will be downloaded.
	:return: None
	"""
    with urllib.request.urlopen(url) as f:
        pic = f.read()
    
    with open(path, 'wb') as file:
        file.write(pic)
    
    print(f'Downloaded file from {url} to {path}')
    return None


def clean_up_APOD() -> None:
    """
	Cleans up the APOD directory by deleting old images.
	:return: None
	"""
    apod_dir = Path('nasa/')
    if not apod_dir.exists():
        print('APOD directory does not exist, creating it.')
        apod_dir.mkdir(parents=True, exist_ok=True)
    
    for file in apod_dir.iterdir():
        if file.is_file() and file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            try:
                file.unlink()
                print(f'Deleted old APOD image: {file.name}')
            except Exception as e:
                print(f'Failed to delete {file.name}: {e}')


def check_env_variables() -> bool:
    """
	Checks if all required environment variables are set.
	:return: True if all required variables are set, False otherwise.
	"""
    complete = True
    if not os.getenv('MONGO_URI'):
        print('No MONGO_URI found in environment variables. Please set it to connect to a database.')
        os.environ['LOCAL_SAVE'] = 'True'
        complete = False
    
    if not os.getenv('NASA_API_KEY'):
        print('No NASA_API_KEY found in environment variables. Please set it to fetch NASA pictures.')
        complete = False
    
    if not os.getenv('CAT_API_KEY'):
        print('No CAT_API_KEY found in environment variables. Please set it to fetch cat pictures.')
        complete = False
    
    if not os.getenv('LOCAL_SAVE'):
        print('No LOCAL_SAVE found in environment variables. Defaulting to False.')
        os.environ['LOCAL_SAVE'] = 'False'
        complete = False
    
    if os.getenv('LOCAL_SAVE') not in ['True', 'False']:
        print('Invalid LOCAL_SAVE value. Please set it to True or False. Defaulting to False.')
        os.environ['LOCAL_SAVE'] = 'False'
        complete = False
    
    if os.getenv('LOCAL_IMG_SAVE') is None:
        print('No LOCAL_IMG_SAVE found in environment variables. Defaulting to False.')
        os.environ['LOCAL_IMG_SAVE'] = 'False'
        complete = False
    
    if os.getenv('LOCAL_IMG_SAVE') not in ['True', 'False']:
        print('Invalid LOCAL_IMG_SAVE value. Please set it to True or False. Defaulting to False.')
        os.environ['LOCAL_IMG_SAVE'] = 'False'
        complete = False
    
    return complete


def parse_utciso8601(date_str: str) -> datetime.datetime | None:
    """
	Parses a UTC ISO 8601 date string into a datetime object.
	"""
    try:
        return datetime.datetime.fromisoformat(date_str)
    except TypeError:
        print(f'Error parsing date string "{date_str}"')
        return None


def check_valid_utciso8601(date_str: str) -> bool:
    """
    Checks if a string is a valid UTC ISO 8601 date string.
    """
    try:
        datetime.datetime.fromisoformat(date_str)
        return True
    except TypeError:
        print(f'Invalid date string "{date_str}"')
        return False


def format_perms_overwrite(overwrite: discord.PermissionOverwrite) -> dict[str, Union[bool, None]]:
    perms: dict[str, Union[bool, None]] = {}
    for permission in overwrite:
        name = permission[0]
        value = permission[1]
        perms[name] = value
    
    return perms


def format_permissions(permissions: dict[discord.Role | discord.Member | discord.Object,
discord.PermissionOverwrite]) -> dict[str, dict[str, Union[bool, None]]]:
    formatted = {}
    
    for key in permissions:
        if isinstance(key, discord.Role):
            formatted[f'R{key.id}'] = format_perms_overwrite(permissions[key])
        elif isinstance(key, discord.Member):
            formatted[f'M{key.id}'] = format_perms_overwrite(permissions[key])
        else:
            formatted[f'O{key.id}'] = format_perms_overwrite(permissions[key])
    
    return formatted


async def log_msg(message: discord.Message) -> bool:
    has_attachment: bool = bool(message.attachments)
    
    reply: str | None = None if message.reference is None else str(message.reference.message_id)
    
    json_data = {
        'author':             message.author.name,
        'author_id':          str(message.author.id),
        'author_global_name': message.author.global_name,
        'content':            message.content,
        'reply_to':           reply,
        'HasAttachments':     has_attachment,
        'timestamp':          message.created_at.timestamp(),
        'id':                 str(message.id),
        'channel':            message.channel.name if hasattr(message.channel, 'name') else 'Unknown',
        'channel_id':         str(message.channel.id)
    }
    
    if os.getenv('LOCAL_SAVE') == 'True':
        with make_file() as file:
            file.write(json.dumps(json_data, ensure_ascii=False) + '\n')
    
    print(f'Message from {message.author.display_name} [#{message.channel}]: {message.content}')
    if has_attachment:
        if os.environ.get('LOCAL_IMG_SAVE') == 'True':
            await save_attachments(message)
        else:
            for attachment in message.attachments:
                await db_stuff.send_attachment(message, attachment)
    
    return db_stuff.send_message(json_data)

async def fail_count_number(message: discord.Message, bot: CoolBot) -> None:
    await message.reply(f"<@{message.author.id}> RUINED IT AT **{bot.config.last_count}**!! Next number is **1**. **Wrong number**.")
    bot.config.last_count = 0
    await message.add_reaction("❌")
    return None

async def fail_count_user(message: discord.Message, bot: CoolBot) -> None:
    await message.reply(f"<@{message.author.id}> RUINED IT AT **{bot.config.last_count}**!! Next number is **1**. **You can't count two numbers in a row**.")
    bot.config.last_count = 0
    await message.add_reaction("❌")
    return None

async def counting_msg(message: discord.Message, bot: CoolBot) -> bool:
    result: int | None = eval_count_msg(message.content.replace(" ", ""))
    if result is None:
        return False
    
    if result != bot.config.last_count + 1:
        if bot.config.last_count != 0:
            await fail_count_number(message, bot)
            return False
        await message.reply("The next number is **1**.")
        return False
    
    reaction: str = "✅"
    
    bot.config.last_count = result
    if result > bot.config.highest_count:
        bot.config.highest_count = result
        reaction = "☑️"
    
    await message.add_reaction(reaction)
    return True
    
