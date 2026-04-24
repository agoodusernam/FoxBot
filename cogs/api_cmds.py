import logging
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Final

import discord
from discord.ext import commands
from discord.ext.commands import BucketType

import cogs.api_cmds_utils as api_utils
from cogs.api_cmds_utils import VTInfo
from command_utils.CContext import CContext, CoolBot
from utils import utils

logger = logging.getLogger('discord')

MAX_VT_FILE_SIZE: Final[int] = 100*1024*1024

class ApiCommands(commands.Cog, name='Images and APIs'):
    """These commands fetch images and data from various APIs."""
    
    def __init__(self, bot: CoolBot):
        self.bot: CoolBot = bot
    
    @commands.command(name='nasa', aliases=['nasa_pic', 'nasa_apod', 'nasapic'],
                      brief="NASA's picture of the day",
                      help="Get NASA's Astronomy Picture of the Day with explanation")
    @commands.cooldown(1, 5, BucketType.guild)  
    async def nasa_pic(self, ctx: CContext) -> None:
        # TODO: This is kind of cursed, fix it later
        # You may be wondering why I can't post the URL directly,
        # Well, discord doesn't feel like embedding images from this source apparently.
        # So instead, we download and re-upload the image because fuck me I suppose.
        if os.path.exists(f'nasa/nasa_pic_{ctx.bot.config.today}.jpg'):
            await ctx.send(f'**{ctx.bot.nasa_data['title']}**\n')
            await ctx.send(
                    file=discord.File(f'nasa/nasa_pic_{ctx.bot.config.today}.jpg',
                                      filename=f'nasa_pic_{ctx.bot.config.today}.jpg'))
            await ctx.send(f'**Explanation:** {ctx.bot.nasa_data['explanation']}')
            return
        
        fetch_msg = await ctx.message.channel.send('Fetching NASA picture of the day...')
        nasa_data = await api_utils.get_nasa_apod()
        ctx.bot.nasa_data = deepcopy(nasa_data)
        
        await utils.download_from_url(f'nasa/nasa_pic_{ctx.bot.config.today}.jpg', nasa_data['url'])
        
        await ctx.send(f'**{nasa_data['title']}**\n')
        await ctx.send(
                file=discord.File(f'nasa/nasa_pic_{ctx.bot.config.today}.jpg',
                                  filename=f'nasa_pic_{ctx.bot.config.today}.jpg'))
        await ctx.send(f'**Explanation:** {nasa_data['explanation']}')
        await fetch_msg.delete()
    
    @commands.command(name='dog', aliases=['dogpic', 'dog_pic'],
                      brief='Get a random dog picture',
                      help='Fetches and displays a random dog picture from an API')
    @commands.cooldown(1, 5, commands.BucketType.guild)  
    async def dogpic(self, ctx: CContext) -> None:
        await api_utils.get_dog_pic(ctx)
    
    @commands.command(name='cat', aliases=['catpic', 'cat_pic'],
                      brief='Get a random cat picture',
                      help='Fetches and displays a random cat picture from an API')
    @commands.cooldown(1, 5, commands.BucketType.guild)  
    async def catpic(self, ctx: CContext) -> None:
        await api_utils.get_cat_pic(ctx)
    
    @commands.command(name='fox', aliases=['foxpic', 'fox_pic'],
                      brief='Get a random fox picture',
                      help='Fetches and displays a random fox picture from an API')
    @commands.cooldown(1, 5, commands.BucketType.guild)  
    async def foxpic(self, ctx: CContext) -> None:
        await api_utils.get_fox_pic(ctx)
    
    @commands.command(name='insult', aliases=['insults'],
                      brief='Get a random insult',
                      help='Fetches and displays a random insult from an API')
    @commands.cooldown(1, 5, commands.BucketType.guild)  
    async def insult(self, ctx: CContext) -> None:
        await api_utils.get_insult(ctx)
    
    @commands.command(name='advice', aliases=['advise', 'give_advice'],
                      brief='Get random advice',
                      help='Fetches and displays a random piece of advice from an API')
    @commands.cooldown(1, 5, commands.BucketType.guild)  
    async def advice(self, ctx: CContext) -> None:
        await api_utils.get_advice(ctx)
    
    @commands.command(name='joke', aliases=['jokes'],
                      brief='Get a random joke',
                      help='Fetches and displays a random joke from an API')
    @commands.cooldown(1, 5, commands.BucketType.guild)  
    async def joke(self, ctx: CContext) -> None:
        await api_utils.get_joke(ctx)
    
    @commands.command(name='wyr', aliases=['would_you_rather', 'wouldyourather'],
                      brief="Get a random 'Would You Rather' question",
                      help="Fetches and displays a random 'Would You Rather' question from an API")
    @commands.cooldown(1, 5, commands.BucketType.guild)  
    async def wyr(self, ctx: CContext) -> None:
        await api_utils.get_wyr(ctx)
    
    @commands.command(name='no',
                      brief="Get a random 'no' response",
                      help="Fetches and displays a random 'no' response from an API")
    @commands.cooldown(1, 5, commands.BucketType.guild)  
    async def no(self, ctx: CContext) -> None:
        await api_utils.get_no(ctx)
    
    @commands.command(name='virus_total_hash', aliases=['virustotalhash', 'vt_hash', 'vth'],
                      brief='Get file information from VirusTotal',
                      help='Get information about a file from VirusTotal using its hash',
                      usage='f!vt_hash <hash>'
                      )
    @commands.cooldown(3, 10, commands.BucketType.guild)
    async def virus_total_hash(self, ctx: CContext, given_hash: str) -> None:
        vt_info: VTInfo | str = await api_utils.get_vt_hash_info(given_hash)
        if isinstance(vt_info, str):
            await ctx.send(vt_info)
            return
        
        await ctx.send(embed=api_utils.create_vt_file_embed(vt_info))
    
    @commands.command(name='virus_total_file', aliases=['virustotalfile', 'vt_file', 'vtf'],
                      brief='Get file information from VirusTotal',
                      help='Scan and get information about a file from VirusTotal',
                      usage='f!vt_file [zip password, if applicable]')
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def virus_total_file(self, ctx: CContext, zip_password: str | None = None):
        if not ctx.message.attachments:
            await ctx.send('You must attach a file to scan.')
            return
        
        if len(ctx.message.attachments) > 1:
            await ctx.send('You can only scan one file at a time.')
            return
        
        if ctx.message.attachments[0].size > MAX_VT_FILE_SIZE:
            await ctx.send('Files above 100MiB are currently unsupported.')
            return
        
        await ctx.send('Scanning file, this may take a while. You will be pinged when it is done.')
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
            file_path: Path = Path(d) / ctx.message.attachments[0].filename
            with open(file_path, "w+b") as f:
                logger.debug(f'Writing file to {file_path}')
                # I would use Attachment.save() here, but it would try to open the file
                # twice as it's not of type io.BufferedIOBase
                written: int = f.write(await ctx.message.attachments[0].read())
                logger.debug(f'Wrote {written} bytes to file')
                if written > MAX_VT_FILE_SIZE:
                    # This should never happen, but just in case
                    logger.warning('File was somehow over 100MiB, this should never happen')
                    await ctx.send('Files above 100MiB are currently unsupported.')
                    return
                
                result: VTInfo | str = await api_utils.upload_file_vt(f, zip_password)
        
        if isinstance(result, str):
            await ctx.send(result)
        else:
            await ctx.send(embed=api_utils.create_vt_file_embed(result))
        
        await ctx.send(ctx.author.mention)

async def setup(bot):
    await bot.add_cog(ApiCommands(bot))
