import os
from copy import deepcopy

import discord
from discord.ext import commands
from discord.ext.commands import BucketType

from utils import api_stuff, utils


def not_blacklisted(ctx):
	return ctx.author.id not in ctx.bot.blacklist_ids['ids']

class ApiCommands(commands.Cog):
	"""Commands related to various APIs like NASA, dog/cat pictures, jokes, etc."""
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name = "nasa", aliases = ["nasa_pic", "nasa_apod", "nasapic"],
				 brief = "NASA's picture of the day",
				 help = "Get NASA's Astronomy Picture of the Day with explanation")
	@commands.cooldown(1, 5, BucketType.user)
	@commands.check(not_blacklisted)
	async def nasa_pic(self, ctx: discord.ext.commands.Context):
		if os.path.exists(f'nasa/nasa_pic_{ctx.bot.today}.jpg'):
			await ctx.message.channel.send(f'**{ctx.bot.nasa_data["title"]}**\n')
			await ctx.message.channel.send(file = discord.File(f'nasa/nasa_pic_{ctx.bot.today}.jpg', filename = f'nasa_pic_{ctx.bot.today}.jpg'))
			await ctx.message.channel.send(f'**Explanation:** {ctx.botnasa_data["explanation"]}')
			return
	
		try:
			fetch_msg = await ctx.message.channel.send('Fetching NASA picture of the day...')
			nasa_data = api_stuff.get_nasa_apod()
			ctx.bot.nasa_data = deepcopy(nasa_data)
			url = nasa_data['url']
	
			utils.download_from_url(f'nasa/nasa_pic_{ctx.bot.today}.jpg', url)
	
			await ctx.message.channel.send(f'**{nasa_data["title"]}**\n')
			await ctx.message.channel.send(file = discord.File(f'nasa/nasa_pic_{ctx.bot.today}.jpg', filename = f'nasa_pic_{ctx.bot.today}.jpg'))
			await ctx.message.channel.send(f'**Explanation:** {nasa_data["explanation"]}')
			await fetch_msg.delete()
	
		except Exception as e:
			await ctx.message.channel.send(f'Error fetching NASA picture: {e}')
	
	
	@commands.command(name = "dog", aliases = ["dogpic", "dog_pic"],
				 brief = "Get a random dog picture",
				 help = "Fetches and displays a random dog picture from an API")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.check(not_blacklisted)
	async def dogpic(self, ctx: discord.ext.commands.Context):
		await api_stuff.get_dog_pic(ctx.message)
	
	
	@commands.command(name = "cat", aliases = ["catpic", "cat_pic"],
				 brief = "Get a random cat picture",
				 help = "Fetches and displays a random cat picture from an API")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.check(not_blacklisted)
	async def catpic(self, ctx: discord.ext.commands.Context):
		await api_stuff.get_cat_pic(ctx.message)
	
	
	@commands.command(name = "fox", aliases = ["foxpic", "fox_pic"],
				 brief = "Get a random fox picture",
				 help = "Fetches and displays a random fox picture from an API")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.check(not_blacklisted)
	async def foxpic(self, ctx: discord.ext.commands.Context):
		await api_stuff.get_fox_pic(ctx.message)
	
	
	@commands.command(name = "insult", aliases = ["insults"],
				 brief = "Get a random insult",
				 help = "Fetches and displays a random insult from an API")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.check(not_blacklisted)
	async def insult(self, ctx: discord.ext.commands.Context):
		await api_stuff.get_insult(ctx.message)
	
	
	@commands.command(name = "advice", aliases = ["advise", "give_advice"],
				 brief = "Get random advice",
				 help = "Fetches and displays a random piece of advice from an API")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.check(not_blacklisted)
	async def advice(self, ctx: discord.ext.commands.Context):
		await api_stuff.get_advice(ctx.message)
	
	
	@commands.command(name = "joke", aliases = ["jokes"],
				 brief = "Get a random joke",
				 help = "Fetches and displays a random joke from an API")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.check(not_blacklisted)
	async def joke(self, ctx: discord.ext.commands.Context):
		await api_stuff.get_joke(ctx.message)
	
	
	@commands.command(name = "wyr", aliases = ["would_you_rather", "wouldyourather"],
				 brief = "Get a random 'Would You Rather' question",
				 help = "Fetches and displays a random 'Would You Rather' question from an API")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.check(not_blacklisted)
	async def wyr(self, ctx: discord.ext.commands.Context):
		await api_stuff.get_wyr(ctx.message)

	@commands.command(name = "karma", aliases = ["karmapic", "karma_pic"],
				 brief = "Get a random karma picture",
				 help = "Shows a random karma picture from the local collection")
	@commands.cooldown(1, 5, commands.BucketType.user)
	@commands.check(not_blacklisted)
	async def karma(self, ctx: discord.ext.commands.Context):
		karma_pic = api_stuff.get_karma_pic()
		if karma_pic is None:
			await ctx.message.channel.send('No karma pictures found.')
			return
		file_path, file_name = karma_pic
		await ctx.message.channel.send(file = discord.File(file_path, filename = file_name))

async def setup(bot):
	await bot.add_cog(ApiCommands(bot))
	print('Api Commands Cog Loaded')
