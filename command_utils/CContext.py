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
            # We don't care if we can't delete the message
            return False
        return True

class CoolBot(commands.Bot):
    async def get_context(self, message, *, cls=CContext):
        return await super().get_context(message, cls=cls)
