import discord.ext

def not_blacklisted(ctx: discord.ext.commands.Context) -> bool:
	return ctx.author.id not in ctx.bot.blacklist_ids['ids']

def is_dev(ctx: discord.ext.commands.Context) -> bool:
	return ctx.author.id in ctx.bot.dev_ids

def is_admin(ctx: discord.ext.commands.Context) -> bool:
	return ctx.author.id in ctx.bot.admin_ids