import logging
import logging.handlers
from pathlib import Path

import discord


def setup_colour_logging(path: Path | str):
    if isinstance(path, str):
        path = Path(path)
        
    logs_path = path.resolve()
    
    ensure_logs_path(logs_path)
    
    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    basic_formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    
    err_handler = logging.handlers.RotatingFileHandler(
        filename=logs_path / 'err.log',
        encoding='utf-8',
        maxBytes=8 * 1024 * 1024,
        backupCount=3
    )
    
    err_handler.setFormatter(basic_formatter)
    err_handler.setLevel(logging.WARNING)
    logger.addHandler(err_handler)
    
    debug_handler = logging.handlers.RotatingFileHandler(
        filename=logs_path / 'debug.log',
        encoding='utf-8',
        maxBytes=8 * 1024 * 1024,
        backupCount=3
    )
    
    debug_handler.setFormatter(basic_formatter)
    logger.addHandler(debug_handler)
    
    handler = logging.StreamHandler()
    
    handler.setLevel(logging.INFO)
    handler.setFormatter(discord.utils._ColourFormatter())
    logger.addHandler(handler)
    
    logging.getLogger('discord.http').setLevel(logging.INFO)
    logging.getLogger('discord.gateway').setLevel(logging.INFO)
    logging.getLogger('discord.client').setLevel(logging.INFO)

def ensure_logs_path(path: Path) -> None:
    if path.is_file():
        path.unlink()
    
    if not path.exists():
        path.mkdir(parents=True)
    
