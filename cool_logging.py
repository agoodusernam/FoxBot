import logging
import logging.handlers
from pathlib import Path

def setup_logging(path: Path | str) -> None:
    if isinstance(path, str):
        path = Path(path)
    
    logs_path = path.resolve()
    
    ensure_logs_path(logs_path)
    
    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    basic_formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    
    for name in logger.handlers[:]:
        logger.removeHandler(name)
    
    levels = (
        ('debug.log', logging.DEBUG),
        ('info.log', logging.INFO),
        ('warning.log', logging.WARNING),
    )
    for filename, level in levels:
        handler = logging.handlers.RotatingFileHandler(
                filename=logs_path / filename,
                encoding='utf-8',
                maxBytes=8 * 1024 * 1024,
                backupCount=3,
        )
        handler.setFormatter(basic_formatter)
        handler.setLevel(level)
        logger.addHandler(handler)
    
    logging.getLogger('discord.http').setLevel(logging.INFO)
    logging.getLogger('discord.gateway').setLevel(logging.INFO)
    logging.getLogger('discord.client').setLevel(logging.INFO)


def ensure_logs_path(path: Path) -> None:
    if path.is_file():
        path.unlink()
    
    if not path.exists():
        path.mkdir(parents=True)
