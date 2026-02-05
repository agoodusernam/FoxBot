import sys
from pathlib import Path
import random
import string
import json
from typing import overload
import shutil
# noinspection PyPackageRequirements
import statx  # type: ignore[import-untyped]

from type_stuff.permission_types import (
    PermissionOverwriteDict,
    SerialisedRole,
    TextChannel,
    VoiceChannel,
    CategoryChannel,
    SerialisedChannel,
    Guild
    )

import discord


def get_file_creation_time(path: Path) -> int:
    on_linux: bool = sys.platform == "linux" or sys.platform == "linux2"
    creation_time: int
    if on_linux:
        creation_time = round(statx.statx(path).btime)
    else:
        creation_time = round(path.stat().st_birthtime)
    return creation_time


def _serialise_perm_overwrite(overwrite: discord.PermissionOverwrite) -> PermissionOverwriteDict:
    return {k: v for k, v in overwrite}  # type: ignore


def _serialise_perm_overwrite_channel(channel: discord.abc.GuildChannel) -> dict[int, PermissionOverwriteDict]:
    roles: dict[int, discord.PermissionOverwrite] = {}
    for k, v in channel.overwrites.items():
        if isinstance(k, discord.Role) or (isinstance(k, discord.Object) and k.type == discord.Role):
            roles[k.id] = v
    return {k: _serialise_perm_overwrite(v) for k, v in roles.items()}  # type: ignore[has-type]


async def save_guild(guild: discord.Guild) -> None | str:
    try:
        guild_data: Guild = await serialise_guild(guild)
    except Exception as e:
        # return f'Failed serialising guild: {e}'
        raise
    
    backups_path = Path('backups').absolute()
    guild_path = backups_path / f'{guild.id}.json'
    
    if guild_path.exists():
        guild_folder = guild_path / f'{guild.id}'
        try:
            guild_folder.mkdir(exist_ok=True, parents=True)
        except OSError as e:
            return f'Failed creating guild folder: {e}'
        
        creation_time = get_file_creation_time(guild_path)
        
        old_backup_path = guild_folder / f'{guild.id}_{creation_time}.json'
        try:
            shutil.move(guild_path, old_backup_path)
        except OSError as e:
            return f'Failed moving old backup to {old_backup_path}: {e}'
        
        guild_path = guild_folder / f'{guild.id}_{round(discord.utils.utcnow().timestamp())}.json'
    
    try:
        with open(guild_path, 'wt') as f:
            json.dump(guild_data, f, indent=4)
    except OSError as e:
        return f'Failed writing json to {guild_path}: {e}'
    
    return None


async def serialise_guild(guild: discord.Guild) -> Guild:
    roles: dict[int, SerialisedRole] = {}
    for role in guild.roles:
        roles[role.id] = await serialise_role(role)
    
    categories_list: list[CategoryChannel] = []
    no_category_channels: list[SerialisedChannel] = []
    
    for category, channels in guild.by_category():
        if isinstance(channels, (discord.StageChannel, discord.ForumChannel, discord.CategoryChannel)):
            continue
        
        if category is not None:
            categories_list.append(await serialise_channel(category))
            continue
        else:
            for channel in channels:
                no_category_channels.append(await serialise_channel(channel))  # type: ignore[arg-type]
    
    return Guild(
            name=guild.name,
            description=guild.description,
            icon=await save_icon(guild.icon) if guild.icon is not None else None,
            afk_channel_id=guild.afk_channel.id if guild.afk_channel is not None else None,
            afk_timeout=guild.afk_timeout,
            verification_level=guild.verification_level.value,
            default_notifications=guild.default_notifications.value,
            explicit_content_filter=guild.explicit_content_filter.value,
            system_channel_id=guild.system_channel.id if guild.system_channel is not None else None,
            system_channel_flags=guild.system_channel_flags.value,
            nsfw_level=guild.nsfw_level.value,
            premium_progress_bar_enabled=guild.premium_progress_bar_enabled,
            widget_enabled=guild.widget_enabled,
            roles=roles,
            categories=categories_list,
            no_category_channels=no_category_channels,
            )


async def save_icon(icon: discord.Asset) -> str:
    timestamp: int = round(discord.utils.utcnow().timestamp())
    
    icon_path: Path = Path('icons').absolute() / str(timestamp)
    icon_path.mkdir(exist_ok=True, parents=True)
    file_name = icon.key + '.png'
    file_path = icon_path / file_name
    with open(file_path, 'wb') as f:
        f.write(await icon.with_format('webp').read())
    
    return str(file_path)


async def serialise_role(role: discord.Role) -> SerialisedRole:
    icon: tuple[bool, str] | None
    if role.display_icon is None:
        icon = None
    elif isinstance(role.display_icon, str):
        icon = (True, role.display_icon)
    else:
        icon = False, await save_icon(role.display_icon)
    
    serialised_role: SerialisedRole = {
        'name':             role.name,
        'hoist':            role.hoist,
        'mentionable':      role.mentionable,
        'colour':           role.colour.to_rgb(),
        'secondary_colour': role.secondary_colour.to_rgb() if role.secondary_colour is not None else None,
        'tertiary_colour':  role.tertiary_colour.to_rgb() if role.tertiary_colour is not None else None,
        'permissions':      role.permissions.value,
        'icon':             icon,
        'id':               role.id
        }
    return serialised_role


@overload
async def serialise_channel(channel: discord.TextChannel) -> TextChannel:
    ...


@overload
async def serialise_channel(channel: discord.VoiceChannel) -> VoiceChannel:
    ...


@overload
async def serialise_channel(channel: discord.CategoryChannel) -> CategoryChannel:
    ...


async def serialise_channel(channel: discord.abc.GuildChannel):
    if isinstance(channel, discord.TextChannel):
        return _serialise_text_channel(channel)
    elif isinstance(channel, discord.VoiceChannel):
        return _serialise_voice_channel(channel)
    elif isinstance(channel, discord.CategoryChannel):
        return await _serialise_category_channel(channel)
    else:
        raise ValueError(f"Channel type {type(channel)} not recognised.")


def _serialise_text_channel(channel: discord.TextChannel) -> TextChannel:
    return TextChannel(
            channel_type="text",
            name=channel.name,
            category=channel.category.id if channel.category is not None else None,
            overwrites=_serialise_perm_overwrite_channel(channel),
            permissions_synced=channel.permissions_synced,
            nsfw=channel.is_nsfw(),
            topic=channel.topic,
            default_auto_archive_duration=channel.default_auto_archive_duration,
            default_thread_slowmode_delay=channel.default_thread_slowmode_delay,
            id=channel.id,
            )


def _serialise_voice_channel(channel: discord.VoiceChannel) -> VoiceChannel:
    return VoiceChannel(
            channel_type="voice",
            name=channel.name,
            category=channel.category.id if channel.category is not None else None,
            overwrites=_serialise_perm_overwrite_channel(channel),
            permissions_synced=channel.permissions_synced,
            bitrate=channel.bitrate,
            user_limit=channel.user_limit,
            rtc_region=channel.rtc_region,
            nsfw=channel.is_nsfw(),
            slowmode_delay=channel.slowmode_delay,  # type: ignore
            id=channel.id,
            )


async def _serialise_category_channel(channel: discord.CategoryChannel) -> CategoryChannel:
    return CategoryChannel(
            channel_type="category",
            name=channel.name,
            category=None,
            overwrites=_serialise_perm_overwrite_channel(channel),
            permissions_synced=channel.permissions_synced,
            nsfw=False,
            channels=[await serialise_channel(c) for c in channel.channels],  # type: ignore[arg-type]
            id=channel.id,
            )
