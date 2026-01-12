import datetime
import json
import os
import re
import decimal
import signal
import urllib.request
import string
import warnings
from enum import IntEnum
from io import TextIOWrapper
from pathlib import Path
from typing import Union, Any
from sys import platform
import logging

import discord
import discord.ext.commands
import discord.ext.tasks
from discord import HTTPException

from command_utils.CContext import CoolBot
from utils import db_stuff  # type: ignore # IDE hates this, and so do I, but it seems to work

logger = logging.getLogger('discord')

class BitwiseDecimal(decimal.Decimal):
    def __and__(self, other):
        return BitwiseDecimal(round(self) & round(other))
    
    def __or__(self, other):
        return BitwiseDecimal(round(self) | round(other))
    
    def __xor__(self, other):
        return BitwiseDecimal(round(self) ^ round(other))
    

D = BitwiseDecimal

class CountStatus(IntEnum):
    SUCCESS = 0
    TIMEOUT = 1
    INVALID = 2
    OVERFLOW = 3
    ZERO_DIV = 4
    DECIMAL_ERR = 5

def user_has_role(member: discord.Member, role_id: int) -> bool:
    for role in member.roles:
        if role.id == role_id:
            return True
    return False

def count_only_allowed_chars(s: str) -> bool:
    """
    Checks if the counting string only contains allowed characters.
    Assumes the string is lowercase and has no whitespace.
    """
    allowed: str = "0123456789*/-+.()%^&<>|~"
    base_definitions: str = "xob"
    s = s.replace(",", ".")
    s = s.replace("_", "")
    for i, char in enumerate(s):
        if char not in allowed:
            if char not in base_definitions:
                return False
            
            if s[i-1] != "0":
                return False
            
            if i == 0:
                return False
            
    return True

def convert_to_base10(match: re.Match[str]) -> str:
    num_str: str = match.group(0)
    if num_str.startswith('0b'):
        return str(int(num_str[2:], 2))
    
    elif num_str.startswith('0o'):
        return str(int(num_str[2:], 8))
    
    elif num_str.startswith('0x'):
        return str(int(num_str[2:], 16))
    
    else:
        # This shouldn't happen
        return num_str

def eval_count_msg(message: str) -> tuple[BitwiseDecimal, CountStatus]:
    """
    Returns the evaluated result of a counting message.
    :param message: str: The counting message to evaluate.
    :return: tuple[BitwiseDecimal, CountStatus]: The evaluated result and the status of the evaluation.
    """
    def timeout_handler(signum: int, frame: Any):
        raise TimeoutError
    on_linux: bool = platform == "linux" or platform == "linux2"
    
    if not on_linux:
        warnings.warn("Counting timeout is only supported on Linux. Counts may hang indefinitely on other platforms.", RuntimeWarning)
    
    if on_linux:
        old_handler = signal.signal(signal.SIGALRM, timeout_handler) # type: ignore
        signal.alarm(2) # type: ignore
    
    try:
        pattern = r"0b[01]+|0o[0-7]+|0x[0-9a-f]+"
        base_10_msg = re.sub(pattern, convert_to_base10, message)
        decimal.getcontext().prec = 320
        expr: str = re.sub(r"(\d+\.\d*|\.\d+|\d+)", r"BitwiseDecimal('\1')", base_10_msg)
        result: BitwiseDecimal = round(eval(expr), 20)
        
        return result, CountStatus.SUCCESS
    
    except (SyntaxError, ValueError, TypeError):
        return D(0), CountStatus.INVALID
    
    except TimeoutError:
        return D(0), CountStatus.TIMEOUT
    
    except (decimal.DivisionByZero, ZeroDivisionError):
        return D(0), CountStatus.ZERO_DIV
    
    except (OverflowError, decimal.Overflow, MemoryError, decimal.Underflow):
        return D(0), CountStatus.OVERFLOW
    
    except decimal.InvalidOperation:
        return D(0), CountStatus.DECIMAL_ERR
    
    finally:
        if on_linux:
            signal.alarm(0) # type: ignore
            signal.signal(signal.SIGALRM, old_handler) # type: ignore  # noqa


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
            logger.info(f'Attachment {i + 1} of {attach_count} for message {message.id} was deleted before it could be saved.')
        except HTTPException:
            logger.error(f'HTTP Error while saving attachment {i + 1} of {attach_count} for message {message.id}')
        except OSError:
            logger.error(f'Error while writing attachment {i + 1} of {attach_count} for message {message.id}')
        
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
    
    logger.info(f'Downloaded file from {url} to {path}')
    return None


def clean_up_APOD() -> None:
    """
	Cleans up the APOD directory by deleting old images.
	:return: None
	"""
    apod_dir = Path('nasa/')
    if not apod_dir.exists():
        logger.info('APOD directory does not exist, creating it.')
        apod_dir.mkdir(parents=True, exist_ok=True)
    
    for file in apod_dir.iterdir():
        if file.is_file() and file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            try:
                file.unlink()
                logger.info(f'Deleted old APOD image: {file.name}')
            except Exception as e:
                logger.info(f'Failed to delete {file.name}: {e}')


def check_env_variables() -> bool:
    """
	Checks if all required environment variables are set.
	:return: True if all required variables are set, False otherwise.
	"""
    complete = True
    if not os.getenv('NASA_API_KEY'):
        logger.warning('No NASA_API_KEY found in environment variables. Please set it to fetch NASA pictures.')
        complete = False
    
    if not os.getenv('CAT_API_KEY'):
        logger.warning('No CAT_API_KEY found in environment variables. Please set it to fetch cat pictures.')
        complete = False
    
    if not os.getenv('LOCAL_SAVE'):
        logger.warning('No LOCAL_SAVE found in environment variables. Defaulting to False.')
        os.environ['LOCAL_SAVE'] = 'False'
        complete = False
    
    if os.getenv('LOCAL_SAVE') not in ['True', 'False']:
        logger.warning('Invalid LOCAL_SAVE value. Please set it to True or False. Defaulting to False.')
        os.environ['LOCAL_SAVE'] = 'False'
        complete = False
    
    if not os.getenv('MONGO_URI'):
        logger.warning('No MONGO_URI found in environment variables. Please set it to connect to a database.')
        os.environ['LOCAL_SAVE'] = 'True'
        complete = False
    
    if os.getenv('LOCAL_IMG_SAVE') is None:
        logger.warning('No LOCAL_IMG_SAVE found in environment variables. Defaulting to False.')
        os.environ['LOCAL_IMG_SAVE'] = 'False'
        complete = False
    
    if os.getenv('LOCAL_IMG_SAVE') not in ['True', 'False']:
        logger.warning('Invalid LOCAL_IMG_SAVE value. Please set it to True or False. Defaulting to False.')
        os.environ['LOCAL_IMG_SAVE'] = 'False'
        complete = False
    
    return complete


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
    
    logger.info(f'Message from {message.author.display_name} [#{message.channel}]: {message.content}')
    if has_attachment:
        if os.environ.get('LOCAL_IMG_SAVE') == 'True':
            saved = await save_attachments(message)
            logger.debug(f'Saved {saved} attachments for message {message.id}')
        else:
            for attachment in message.attachments:
                await db_stuff.send_attachment(message, attachment)
    
    return db_stuff.send_message(json_data)

async def fail_count_number(message: discord.Message, bot: CoolBot, actual: int) -> None:
    await message.reply(f"<@{message.author.id}> RUINED IT AT **{bot.config.last_count}**!! Next number is **1**. Your message evaluated to **{actual}**.")
    await fail_count(message, bot)
    return None

async def fail_count_user(message: discord.Message, bot: CoolBot) -> None:
    await message.reply(f"<@{message.author.id}> RUINED IT AT **{bot.config.last_count}**!! Next number is **1**. **You can't count two numbers in a row**.")
    await fail_count(message, bot)
    return None

async def fail_count(message: discord.Message, bot: CoolBot) -> None:
    logger.debug(f'Counting fail by user {message.author.id} at message {message.id}')
    assert isinstance(message.author, discord.Member)
    
    bot.config.last_count = 0
    await message.add_reaction("❌")
    
    if not user_has_role(message.author, bot.config.counting_fail_role):
        await message.author.add_roles(discord.Object(id=bot.config.counting_fail_role))
    
    bot.config.add_counting_fail(message.author.id)
    return None

async def counting_msg(message: discord.Message, bot: CoolBot) -> bool:
    assert isinstance(message.author, discord.Member)
    s = message.content.lower()
    for char in string.whitespace:
        s = s.replace(char, "")
    
    if not count_only_allowed_chars(s):
        return False
    
    result, status = eval_count_msg(s)
    
    if status == CountStatus.INVALID:
        return False
    
    banrole: int = bot.config.counting_ban_role
    
    if banrole != 0 and user_has_role(message.author, banrole):
        await message.reply("You are banned from counting. Your message was not counted.")
        await message.delete()
        return False
    
    if bot.config.last_count_user == message.author.id and bot.config.last_count != 0:
        await fail_count_user(message, bot)
        return False
    
    if status == CountStatus.TIMEOUT:
        await message.reply("Expression took too long to evaluate.")
        return False
    
    if status == CountStatus.OVERFLOW:
        await message.reply("Expression resulted in an under or overflow, likely due to insufficient precision. Try using numbers closer to 0.")
        return False
    
    if status == CountStatus.ZERO_DIV:
        await message.reply("Expression resulted in a division by zero.")
        return False
    
    if status == CountStatus.DECIMAL_ERR:
        await message.reply("Expression resulted in a decimal error, likely due to insufficient precision. Try using numbers closer to 0.")
        return False
    
    int_result: int = round(result)
    del result
    
    if int_result != bot.config.last_count + 1:
        if bot.config.last_count != 0:
            await fail_count_number(message, bot, actual=int_result)
            return False
        
        await message.reply("The next number is **1**.")
        return False
    
    bot.config.user_counted(message.author.id, int_result, message.id)
    reaction: str = "✅"
    
    bot.config.last_count = int_result
    if int_result > bot.config.highest_count:
        bot.config.highest_count = int_result
        reaction = "☑️"
    
    bot.config.last_count_user = message.author.id
    await message.add_reaction(reaction)
    return True
    
