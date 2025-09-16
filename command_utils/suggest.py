"""
Handles the suggestion command.
"""
import discord
import discord.ext.commands

from command_utils.CContext import CContext

HELP_MSG = '''Please post your suggestions for the server or <@1377636535968600135> in here using `f!suggest <suggestion>`.
If you have any additional comments, please use the thread.
✅: Implemented
💻: Working on it
❌: Will not add

👍: Vote for suggestion
'''


async def send_suggestion(ctx: CContext, suggestion: str) -> None:
    """
    Sends a suggestion to the designated channel and creates a thread for discussion.
    """
    await ctx.delete()
    
    channel: discord.TextChannel = ctx.bot.get_channel(1379193761791213618)
    last_msgs = [message async for message in channel.history(limit=3)]
    for message in last_msgs:
        if message.content.startswith(HELP_MSG[:20]):
            await message.delete()
    
    try:
        embed = discord.Embed(title='Suggestion', description=suggestion, color=discord.Color.blue())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        msg = await channel.send(embed=embed)
        await msg.add_reaction('👍')
        
        await msg.create_thread(
                name=f'suggestion-{ctx.author.display_name}',
        )
        
        await channel.send(HELP_MSG)
        print(f'Suggestion sent: {suggestion}')

    except discord.Forbidden as exc:
        raise discord.ext.commands.BotMissingPermissions(["manage_channels", "manage_threads",
                                                          "create_public_threads"]) from exc
    
    except discord.NotFound:
        print('Channel not found for sending suggestion.')
        
    except discord.HTTPException as e:
        print(f'Failed to send suggestion: {e}')
