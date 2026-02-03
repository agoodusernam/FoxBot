import datetime
from typing import TypedDict

import discord
from dateutil.relativedelta import relativedelta  # type: ignore[import-untyped]

from command_utils.embed_util import create_log_embed


class MissingType:
    instance = None
    
    def __new__(cls):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance
    
    def __str__(self):
        return "MISSING"
    
    def __repr__(self):
        return str(self)


MISSING: MissingType = MissingType()


class MemberChange(TypedDict):
    nick: str | None | MissingType
    roles_added: list[discord.Role] | MissingType
    roles_removed: list[discord.Role] | MissingType
    timed_out_until: datetime.datetime | None | MissingType
    pending: bool | MissingType
    avatar: discord.Asset | MissingType
    flags: discord.MemberFlags | MissingType


def time_ago(dt: datetime.datetime | int | float):
    if isinstance(dt, (int, float)):
        dt = datetime.datetime.fromtimestamp(dt, tz=datetime.UTC)
    
    now: datetime.datetime = datetime.datetime.now(datetime.UTC)
    delta: relativedelta = relativedelta(now, dt)
    t_times: dict[str, int] = {
        'years':   delta.years,
        'months':  delta.months,
        'days':    delta.days,
        'hours':   delta.hours,
        'minutes': delta.minutes,
        'seconds': delta.seconds
        }
    slots: int = 0
    max_slots: int = 3
    times: list[tuple[str, int]] = []
    for k, v in t_times.items():
        if v == 1:
            k = k[:-1]
        
        times.append((k, v))
        if v != 0 and slots < max_slots:
            slots += 1
    
    if slots == 0:
        return "0 seconds ago"
    
    filled_slots: int = 0
    count: int = 0
    to_return: str = ""
    while filled_slots < slots:
        if count >= len(times):
            break
        
        if times[count][1] == 0:
            count += 1
            continue
        
        filled_slots += 1
        to_return += f"{times[count][1]} {times[count][0]}"
        count += 1
        
        if filled_slots == slots - 1:
            to_return += " and "
        
        elif filled_slots < slots:
            to_return += ", "
    
    return to_return + " ago"


def get_changed_roles(before: list[discord.Role], after: list[discord.Role]) -> tuple[list[discord.Role], list[discord.Role]]:
    """
    Returns a tuple of lists containing roles added and removed from a member.
    Added is first, removed second.
    """
    added: list[discord.Role] = []
    removed: list[discord.Role] = []
    
    for role in after:
        if role not in before:
            added.append(role)
    
    for role in before:
        if role not in after:
            removed.append(role)
    
    return added, removed


def get_changes(before: discord.Member, after: discord.Member) -> MemberChange:
    added, removed = get_changed_roles(before.roles[1:], after.roles[1:])
    changes: MemberChange = {
        'nick':            after.nick if after.nick != before.nick else MISSING,
        'roles_added':     added if added else MISSING,
        'roles_removed':   removed if removed else MISSING,
        'timed_out_until': after.timed_out_until if after.timed_out_until != before.timed_out_until else MISSING,
        'pending':         after.pending if after.pending != before.pending else MISSING,
        'avatar':          after.display_avatar if after.display_avatar.url != before.display_avatar.url else MISSING,
        'flags':           after.flags if after.flags != before.flags else MISSING
        }
    return changes

def nick_update_embed(before_nick: str | None, after: discord.Member) -> discord.Embed:
    title: str = 'Nickname changed'
    description: str
    if before_nick is None:
        title = 'Nickname added'
        name = after.global_name if after.global_name is not None else after.name
        description = f'{after.mention} ({name}) has been given the nickname `{after.nick}`'
    else:
        description = f"{after.mention}'s nickname was changed from `{before_nick}` to `{after.nick}`"
    
    return create_log_embed(after.name, after.display_avatar.url, description, discord.Color.blurple(), title)

def roles_changed_embed(changed: list[discord.Role], member: discord.Member, title: str, desc: str) -> discord.Embed:
    roles: str = ", ".join([r.mention for r in changed])
    return create_log_embed(member.name, member.display_avatar.url, f'Roles {desc} {member.mention}:\n{roles}', discord.Color.blurple(), title)

def timeout_embed(member: discord.Member, until: datetime.datetime | None) -> discord.Embed:
    if until is None:
        return create_log_embed(member.name, member.display_avatar.url, f'Timeout removed from {member.mention}', discord.Color.green(), 'Timeout removed')
    
    formatted_until: str = discord.utils.format_dt(until, style='F')
    
    return create_log_embed(member.name, member.display_avatar.url, f'Timeout set for {member.mention} until {formatted_until}', discord.Color.red(), 'Timeout added')
    
def avatar_update_embed(after: discord.Member) -> discord.Embed:
    embed = create_log_embed(
            after.name,
            after.display_avatar.url,
            f'{after.mention}',
            discord.Color.blurple(),
            'Avatar update',
            )
    embed.set_thumbnail(url=after.display_avatar.url)
    return embed
    