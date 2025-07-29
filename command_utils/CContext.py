import discord
from discord.ext import commands


class CContext(commands.Context):
    async def delete(self) -> bool:
        """Delete the command message if possible.
        Returns:
            bool: True if the message was deleted, False if it could not be deleted.
        """
        try:
            await self.message.delete()
        
        except:
            # If the message cannot be deleted for any reason (e.g., permissions, message not found), just ignore the error.
            return False
        return True
