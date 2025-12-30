import os
from copy import deepcopy

import discord
from discord.ext import commands
from discord.ext.commands import BucketType

from utils import api_stuff, utils
from command_utils.CContext import CContext, CoolBot


class ApiCommands(commands.Cog, name='Images and APIs'):
    """These commands fetch images and data from various APIs."""
    
    def __init__(self, bot: CoolBot):
        self.bot: CoolBot = bot
    
    @commands.command(name='nasa', aliases=['nasa_pic', 'nasa_apod', 'nasapic'],
                      brief="NASA's picture of the day",
                      help="Get NASA's Astronomy Picture of the Day with explanation")
    @commands.cooldown(1, 5, BucketType.user)  # type: ignore
    async def nasa_pic(self, ctx: CContext):
        if os.path.exists(f'nasa/nasa_pic_{ctx.bot.config.today}.jpg'):
            await ctx.send(f'**{ctx.bot.nasa_data['title']}**\n')
            await ctx.send(
                    file=discord.File(f'nasa/nasa_pic_{ctx.bot.config.today}.jpg',
                                      filename=f'nasa_pic_{ctx.bot.config.today}.jpg'))
            await ctx.send(f'**Explanation:** {ctx.bot.nasa_data['explanation']}')
            return
        
        try:
            fetch_msg = await ctx.message.channel.send('Fetching NASA picture of the day...')
            nasa_data = api_stuff.get_nasa_apod()
            ctx.bot.nasa_data = deepcopy(nasa_data)
            
            utils.download_from_url(f'nasa/nasa_pic_{ctx.bot.config.today}.jpg', nasa_data['url'])
            
            await ctx.send(f'**{nasa_data['title']}**\n')
            await ctx.send(
                    file=discord.File(f'nasa/nasa_pic_{ctx.bot.config.today}.jpg',
                                      filename=f'nasa_pic_{ctx.bot.config.today}.jpg'))
            await ctx.send(f'**Explanation:** {nasa_data['explanation']}')
            await fetch_msg.delete()
        
        except Exception as e:
            raise discord.ext.commands.CommandError(f"{e}")
    
    @commands.command(name='dog', aliases=['dogpic', 'dog_pic'],
                      brief='Get a random dog picture',
                      help='Fetches and displays a random dog picture from an API')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def dogpic(self, ctx: CContext):
        await api_stuff.get_dog_pic(ctx)
    
    @commands.command(name='cat', aliases=['catpic', 'cat_pic'],
                      brief='Get a random cat picture',
                      help='Fetches and displays a random cat picture from an API')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def catpic(self, ctx: CContext):
        await api_stuff.get_cat_pic(ctx)
    
    @commands.command(name='fox', aliases=['foxpic', 'fox_pic'],
                      brief='Get a random fox picture',
                      help='Fetches and displays a random fox picture from an API')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def foxpic(self, ctx: CContext):
        await api_stuff.get_fox_pic(ctx)
    
    @commands.command(name='insult', aliases=['insults'],
                      brief='Get a random insult',
                      help='Fetches and displays a random insult from an API')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def insult(self, ctx: CContext):
        await api_stuff.get_insult(ctx)
    
    @commands.command(name='advice', aliases=['advise', 'give_advice'],
                      brief='Get random advice',
                      help='Fetches and displays a random piece of advice from an API')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def advice(self, ctx: CContext):
        await api_stuff.get_advice(ctx)
    
    @commands.command(name='joke', aliases=['jokes'],
                      brief='Get a random joke',
                      help='Fetches and displays a random joke from an API')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def joke(self, ctx: CContext):
        await api_stuff.get_joke(ctx)
    
    @commands.command(name='wyr', aliases=['would_you_rather', 'wouldyourather'],
                      brief="Get a random 'Would You Rather' question",
                      help="Fetches and displays a random 'Would You Rather' question from an API")
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def wyr(self, ctx: CContext):
        await api_stuff.get_wyr(ctx)
    
    @commands.command(name='karma', aliases=['karmapic', 'karma_pic'],
                      brief='Get a random karma picture',
                      help='Shows a random karma picture from the local collection')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def karma(self, ctx: CContext):
        karma_pic = api_stuff.get_karma_pic()
        if karma_pic is None:
            await ctx.send('No karma pictures found.')
            return
        file_path, file_name = karma_pic
        await ctx.send(file=discord.File(file_path, filename=file_name))
    
    @commands.command(name='no',
                      brief="Get a random 'no' response",
                      help="Fetches and displays a random 'no' response from an API")
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def no(self, ctx: CContext):
        await api_stuff.get_no(ctx)


async def setup(bot):
    await bot.add_cog(ApiCommands(bot))
