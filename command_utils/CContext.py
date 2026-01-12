import asyncio
import datetime
import logging
import threading
from typing import Any, Optional

from discord import Message
from discord.ext import commands
import discord

from config.blacklist_manager import BlacklistManager
from config.bot_config import BotConfig, load_config

logger = logging.getLogger('discord')


class CContext(commands.Context):
    bot: "CoolBot"
    async def delete(self) -> bool:
        """Delete the command message if possible.
        Returns:
            bool: True if the message was deleted, False if it could not be deleted.
        """
        try:
            await self.message.delete()
        
        except Exception as e:
            # We don't care if we can't delete the message
            logger.info(f"Failed to delete message: {e}")
            return False
        return True
    
    async def safe_reply(self, content: Optional[str] = None, **kwargs: Any) -> Message | None:
        try:
            return await super().reply(content, **kwargs)
        except discord.Forbidden as e:
            logger.error(f"Failed to send reply, Forbidden: {e}")
            return None
        
        except discord.HTTPException as e:
            logger.error(f"Failed to send reply, HTTPException: {e}")
            return None
        
        except Exception as e:
            logger.error(f"Failed to send reply, Unknown error: {e}")
            return None

class CoolBot(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        self.config: BotConfig = load_config()
        kwargs['command_prefix'] = self.config.command_prefix
        super().__init__(*args, **kwargs)
        self.blacklist: BlacklistManager = BlacklistManager()
        self.admin_ids: list[int] = self.config.admin_ids
        self.dev_ids: list[int] = self.config.dev_ids
        self.del_after: int = self.config.del_after
        self.config.today = datetime.datetime.now(datetime.UTC).strftime('%d-%m-%Y_%H-%M-%S')
        self.landmine_channels: dict[int, int] = {}
        self.forced_landmines: set[int] = set()
        self.dev_func_thread: threading.Thread | None = None
        self.vc_client: discord.VoiceClient | None = None
        self.tts_lock: asyncio.Lock = asyncio.Lock()
        self.logger: logging.Logger = logging.getLogger('discord')
    
    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)
        
    async def get_context(self, message, *, cls=CContext) -> Any:
        return await super().get_context(message, cls=cls)
