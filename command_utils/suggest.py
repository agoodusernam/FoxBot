import discord

from command_utils.CContext import CContext

HELP_MSG = '''Please post your suggestions for the <@1377636535968600135> in here using `f!suggest <suggestion>`.
If you have any additional comments, please use the thread.
✅: Implemented
💻: Working on it
❌: Will not add

👍: Vote for suggestion
'''


async def send_suggestion(ctx: CContext, suggestion: str) -> None:
    await ctx.delete()
    
    channel: discord.TextChannel = ctx.bot.get_channel(1379193761791213618)
    last_msgs = [a_message async for a_message in channel.history(limit=3)]
    for _message in last_msgs:
        if _message.content.startswith(HELP_MSG[:20]):
            await _message.delete()
    
    try:
        embed = discord.Embed(title='Suggestion', description=suggestion, color=discord.Color.blue())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        embed.timestamp = discord.utils.utcnow()
        msg = await channel.send(embed=embed)
        await msg.add_reaction('👍')
        
        await msg.create_thread(
                name=f'suggestion-{ctx.author.display_name}',
        )
        
        await channel.send(HELP_MSG)
        print(f'Suggestion sent: {suggestion}')
    except discord.HTTPException as e:
        print(f'Failed to send suggestion: {e}')
    except Exception as e:
        print(f'An error occurred while sending suggestion: {e}')
