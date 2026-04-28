import discord

from command_utils.CContext import CContext
from utils.utils import user_has_role


def is_dev(ctx: CContext) -> bool:
    return ctx.author.id in ctx.bot.dev_ids


def is_admin(ctx: CContext) -> bool:
    return ctx.author.id in ctx.bot.admin_ids


def is_staff(ctx: CContext) -> bool:
    if isinstance(ctx.author, discord.User):
        return False
    if ctx.bot.config.staff_role_id == 0:
        return False
    return user_has_role(ctx.author, ctx.bot.config.staff_role_id)
