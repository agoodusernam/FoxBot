import datetime
import os
import shutil
import socket
import urllib.request
from io import TextIOWrapper
from pathlib import Path
from typing import Union
import logging

import cachetools.func
import discord
import discord.ext.commands
import discord.ext.tasks
from discord import HTTPException

logger = logging.getLogger('discord')


def user_has_role(member: discord.Member, role_id: int) -> bool:
    for role in member.roles:
        if role.id == role_id:
            return True
    return False

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

def seconds_to_human_readable(seconds: float) -> str:
    """
    Convert seconds to a human-readable format.
    :param seconds: The number of seconds to convert.
    :return: A string representing the time in a human-readable format.
    """
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    seconds: int = int(seconds) # type: ignore
    if seconds < 3600:
        return f"{seconds // 60} minutes and {seconds % 60} seconds"
    if seconds < 86400:
        return f"{seconds // 3600} hours, {(seconds % 3600) // 60} minutes and {seconds % 60} seconds"
    return f"{seconds // 86400} days, {(seconds % 86400) // 3600} hours, " \
           f"{(seconds % 3600) // 60} minutes and {seconds % 60} seconds"



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


def get_attachment(user_id: int | str, message_id: int | str) -> Path | list[Path] | None:
    """
    Returns the path of the attachment, or a list of paths if there are multiple attachments.
    If no attachments are found, returns None.
    """
    base_path: Path = Path(os.path.abspath('data/attachments')) / str(user_id)
    path: Path = base_path / str(message_id)
    
    if not path.exists():
        return None
    
    if path.is_file():
        return path
    
    if path.is_dir():
        return list(path.iterdir())
    
    return None


def copy_attach_to_temp(src: list[Path]) -> bool:
    """
    Copies an attachment from src to dest.
    Returns True if successful, False otherwise.
    """
    dest: Path = Path(os.path.abspath('temp'))
    if not dest.exists():
        dest.mkdir(parents=True)
    
    if dest.is_file():
        dest.unlink()
        dest.mkdir(parents=True)
    
    for root, dirs, files in os.walk(dest):
        for f in files:
            os.unlink(os.path.join(root, f))
    
    names: list[str] = []
    for i, file in enumerate(src):
        names.append(f"{i}{"".join(file.suffixes)}")
    
    all_success: bool = True
    
    for i, name in enumerate(names):
        try:
            shutil.copy(src[i], dest / name)
        except Exception as e:
            logger.error(f"Failed to copy attachment {i}: {e}")
            all_success = False
    
    return all_success


@cachetools.func.fifo_cache(maxsize=1)
def loc_total() -> tuple[int, int]:
    total_lines: int = 0
    total_files: int = 0
    
    for root, dirs, files in os.walk(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')):
        # Skip .venv directory
        if '.venv' in dirs:
            dirs.remove('.venv')
        
        # Count lines in .py files
        for file in files:
            if not file.endswith('.py'):
                continue
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
                total_lines += line_count
                total_files += 1
                logger.debug(f'{file_path}: {line_count} lines')
            except Exception as e:
                logger.error(f'Error reading {file_path}: {e}')
        
    return total_lines, total_files

def internet(host="1.1.1.1", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        print(ex)
        return False
