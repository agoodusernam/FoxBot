import asyncio
import datetime
import logging
import threading
from typing import Any

from discord.ext import commands
import discord

from config.blacklist_manager import BlacklistManager
from config.bot_config import BotConfig


class CContext(commands.Context):
    bot: "CoolBot"
    async def delete(self) -> bool:
        """Delete the command message if possible.
        Returns:
            bool: True if the message was deleted, False if it could not be deleted.
        """
        try:
            await self.message.delete()
        
        except Exception:
            # We don't care if we can't delete the message
            return False
        return True

class CoolBot(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        self.config: BotConfig = kwargs.pop('config')
        self.blacklist: BlacklistManager = BlacklistManager()
        self.admin_ids: list[int] = self.config.admin_ids
        self.dev_ids: list[int] = self.config.dev_ids
        self.del_after: int = self.config.del_after
        self.config.today = datetime.datetime.now(datetime.UTC).strftime('%d-%m-%Y_%H-%M-%S')
        kwargs['command_prefix'] = self.config.command_prefix
        self.landmine_channels: dict[int, int] = {}
        self.forced_landmines: set[int] = set()
        self.dev_func_thread: threading.Thread | None = None
        self.vc_client: discord.VoiceClient | None = None
        self.tts_lock: asyncio.Lock = asyncio.Lock()
        
        super().__init__(*args, **kwargs)
        self.logger: logging.Logger = logging.getLogger('discord')
    
    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)
        
    async def get_context(self, message, *, cls=CContext) -> Any:
        return await super().get_context(message, cls=cls)
