import sys
from collections.abc import Iterable, Callable
from pathlib import Path
import json
from typing import overload, Any
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
    SerialisedGuild,
)

import discord


def get_file_creation_time(path: Path) -> int:
    on_linux: bool = sys.platform == "linux" or sys.platform == "linux2"
    creation_time: int
    if on_linux:
        creation_time = round(statx.statx(path).btime)
    else:
        creation_time = round(path.stat().st_birthtime) # type: ignore
    return creation_time


def _serialise_perm_overwrite(overwrite: discord.PermissionOverwrite) -> PermissionOverwriteDict:
    return {k: v for k, v in overwrite}  # type: ignore[return-value]


def _serialise_perm_overwrite_channel(channel: discord.abc.GuildChannel) -> dict[int, PermissionOverwriteDict]:
    roles: dict[int, discord.PermissionOverwrite] = {}
    for k, v in channel.overwrites.items():
        if isinstance(k, discord.Role) or (isinstance(k, discord.Object) and k.type == discord.Role):
            roles[k.id] = v
    return {k: _serialise_perm_overwrite(v) for k, v in roles.items()}  # type: ignore[has-type]


async def save_guild(guild: discord.Guild) -> None | str:
    try:
        guild_data: SerialisedGuild = await serialise_guild(guild)
    except Exception as e:
        return f'Failed serialising guild: {e}'
    
    backups_path = Path('backups').resolve()
    if not backups_path.exists():
        backups_path.mkdir(exist_ok=True, parents=True)
    guild_path = backups_path / f'{guild.id}.json'
    
    if guild_path.exists():
        guild_folder = backups_path / f'{guild.id}'
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
        with open(guild_path, 'wt+') as f:
            json.dump(guild_data, f, indent=4)
    except OSError as e:
        return f'Failed writing json to {guild_path}: {e}'
    
    return None


async def serialise_guild(guild: discord.Guild) -> SerialisedGuild:
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
    
    return SerialisedGuild(
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
            premium_progress_bar_enabled=guild.premium_progress_bar_enabled,
            widget_enabled=guild.widget_enabled,
            roles=roles,
            categories=categories_list,
            no_category_channels=no_category_channels,
    )


async def save_icon(icon: discord.Asset) -> str:
    timestamp: int = round(discord.utils.utcnow().timestamp())
    
    icon_path: Path = Path('icons').resolve() / str(timestamp)
    icon_path.mkdir(exist_ok=True, parents=True)
    file_name = icon.key + '.png'
    file_path = icon_path / file_name
    with open(file_path, 'wb') as f:
        f.write(await icon.with_format('webp').read())
    
    return str(file_path)


async def serialise_role(role: discord.Role) -> SerialisedRole:
    icon: tuple[bool, str | Path] | None
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


def to_guild_data(data: dict[str, Any]) -> SerialisedGuild:
    for key, _ in SerialisedGuild.__annotations__.items():
        if key not in data:
            raise ValueError(f"{key}")
    return data  # type: ignore


def _most_recent_file(folder: Path) -> Path | None:
    if not folder.is_dir():
        raise NotADirectoryError
    
    most_recent_time: int = 0
    most_recent: Path = Path()
    creation_time: int
    
    for file in folder.iterdir():
        creation_time = get_file_creation_time(file)
        if creation_time > most_recent_time:
            most_recent_time = creation_time
            most_recent = file
    
    if most_recent == Path():
        return None
    
    return most_recent


def _get_most_recent_backup(g_id: str) -> Path | str:
    backups_path = Path('backups').resolve()
    
    if not backups_path.exists():
        return 'No backups path'
    
    guild_folder_path: Path = backups_path / f'{g_id}'
    guild_path: Path = backups_path / f'{g_id}.json'
    
    if guild_path.exists():
        pass
    
    elif guild_folder_path.exists() and guild_folder_path.is_dir():
        t_guild_path = _most_recent_file(guild_folder_path)
        if t_guild_path is None:
            return 'Guild backup folder exists, but is empty'
        guild_path = t_guild_path
    
    else:
        return 'No guild backup for this ID'
    
    return guild_path.resolve()


def get_most_recent_backup(g_id: str | int) -> str | dict[Any, Any]:
    if isinstance(g_id, int):
        g_id = str(g_id)
    
    most_recent_backup: Path | str = _get_most_recent_backup(g_id)
    if isinstance(most_recent_backup, str):
        # There was an error in _get_most_recent_backup
        return most_recent_backup
    
    try:
        with open(most_recent_backup, 'rt') as f:
            backup: dict[Any, Any] = json.load(f)
        
        return backup
    
    except json.JSONDecodeError as e:
        return f'Failed to decode JSON document. Path: {most_recent_backup} \n Error: {e}'
    except OSError as e:
        return f'Failed to read file. Path: {most_recent_backup} \n Error: {e}'


async def load_roles(roles: Iterable[SerialisedRole], server: discord.Guild) -> dict[int, discord.Role]:
    """
    Returns a dict of [old_id: role]
    """
    id_map: dict[int, discord.Role] = {}
    for role in roles:
        permissions: discord.Permissions = discord.Permissions(role['permissions'])
        if role['name'] == '@everyone':
            await server.default_role.edit(permissions=permissions)
            id_map[role['id']] = server.default_role
            continue
        
        colour: discord.Colour = discord.Colour.from_rgb(*role['colour'])
        kwargs: dict[str, Any] = {
            'name':        role['name'],
            'permissions': permissions,
            'colour':      colour,
            'hoist':       role['hoist'],
            'mentionable': role['mentionable']
        }
        if role['icon'] is None:
            pass
        elif role['icon'][0]:
            kwargs['icon'] = role['icon'][1]
        else:
            with open(role['icon'][1], "rb") as f:
                kwargs['icon'] = f.read()
        
        if role['secondary_colour'] is not None:
            kwargs['secondary_colour'] = discord.Colour.from_rgb(*role['secondary_colour'])
        
        if role['tertiary_colour'] is not None:
            kwargs['tertiary_colour'] = discord.Colour.from_rgb(*role['tertiary_colour'])
        
        created_role: discord.Role = await server.create_role(**kwargs)
        id_map[role['id']] = created_role
    
    return id_map


def _perm_overwrite(perms: PermissionOverwriteDict) -> discord.PermissionOverwrite:
    ow = discord.PermissionOverwrite()
    ow.update(**perms)
    return ow


def _overwrites_for_discord(ows: dict[int, PermissionOverwriteDict], role_map: dict[int, discord.Role]) -> dict[discord.Role, discord.PermissionOverwrite]:
    disc_ows: dict[discord.Role, discord.PermissionOverwrite] = {}
    for role_id, ow in ows.items():
        disc_ows[role_map[role_id]] = _perm_overwrite(ow)
    return disc_ows


async def load_channel(channel: SerialisedChannel, role_map: dict[int, discord.Role], server: discord.Guild, add_to_map: Callable[[int, discord.abc.GuildChannel], None], category: discord.CategoryChannel | None = None) -> discord.CategoryChannel | None:
    match channel['channel_type']:
        case 'text':
            await load_text_channel(channel, role_map, server, category)  # type: ignore[arg-type]
        case 'voice':
            await load_voice_channel(channel, role_map, server, category)  # type: ignore[arg-type]
        case 'category':
            return await load_category(channel, role_map, server, add_to_map)  # type: ignore[arg-type]
    
    return None


async def load_text_channel(channel: TextChannel, role_map: dict[int, discord.Role], server: discord.Guild, add_to_map: Callable[[int, discord.abc.GuildChannel], None], category: discord.CategoryChannel | None = None):
    kwargs: dict[str, Any] = {}
    kwargs['name'] = channel['name']
    if not channel['permissions_synced']:
        kwargs['overwrites'] = _overwrites_for_discord(channel['overwrites'], role_map)
    
    kwargs['nsfw'] = channel['nsfw']
    if channel['topic'] is not None:
        kwargs['topic'] = channel['topic']
    
    kwargs['default_auto_archive_duration'] = channel['default_auto_archive_duration']
    kwargs['default_thread_slowmode_delay'] = channel['default_thread_slowmode_delay']
    if category is not None:
        kwargs['category'] = category
    
    add_to_map(channel['id'], await server.create_text_channel(**kwargs))


async def load_voice_channel(channel: VoiceChannel, role_map: dict[int, discord.Role], server: discord.Guild, add_to_map: Callable[[int, discord.abc.GuildChannel], None], category: discord.CategoryChannel | None = None):
    kwargs: dict[str, Any] = {}
    kwargs['name'] = channel['name']
    if not channel['permissions_synced']:
        kwargs['overwrites'] = _overwrites_for_discord(channel['overwrites'], role_map)
    
    kwargs['nsfw'] = channel['nsfw']
    if channel['rtc_region'] is not None:
        kwargs['rtc_region'] = channel['rtc_region']
    
    kwargs['bitrate'] = channel['bitrate']
    kwargs['user_limit'] = channel['user_limit']
    if category is not None:
        kwargs['category'] = category
    
    add_to_map(channel['id'], await server.create_voice_channel(**kwargs))


async def load_category(category: CategoryChannel, role_map: dict[int, discord.Role], server: discord.Guild, add_to_map: Callable[[int, discord.abc.GuildChannel], None]) -> discord.CategoryChannel:
    ows: dict[discord.Role, discord.PermissionOverwrite] = _overwrites_for_discord(category['overwrites'], role_map)
    cat: discord.CategoryChannel = await server.create_category(
            name=category['name'],
            overwrites=ows,  # type: ignore[arg-type]
    )
    add_to_map(category['id'], cat)
    return cat


async def load_categories(categories: list[CategoryChannel], role_map: dict[int, discord.Role], server: discord.Guild, add_to_map: Callable[[int, discord.abc.GuildChannel], None]):
    for category in reversed(categories):
        category_obj = await load_channel(category, role_map, server, add_to_map)
        for channel in reversed(category['channels']):
            await load_channel(channel, role_map, server, add_to_map, category_obj)


async def load_backup(dict_backup: dict[Any, Any], server: discord.Guild) -> str | None:
    backup: SerialisedGuild
    try:
        backup = to_guild_data(dict_backup)
    except ValueError as e:
        return f'Backup data missing field: {e}'
    
    role_map: dict[int, discord.Role] = await load_roles(backup['roles'].values(), server)
    
    channel_map: dict[int, discord.abc.GuildChannel] = {}
    
    def add_to_map(o_id: int, c: discord.abc.GuildChannel):
        channel_map[o_id] = c
    
    for channel in backup['no_category_channels']:
        await load_channel(channel, role_map, server, add_to_map)
    
    await load_categories(backup['categories'], role_map, server, add_to_map)
    
    icon: bytes | None = None
    if isinstance(backup['icon'], Path):
        with open(backup['icon'], 'rb') as f:
            icon = f.read()
    # channel_map[backup['afk_channel_id']]
    kwargs: dict[str, Any] = {}
    kwargs['name'] = backup['name']
    kwargs['icon'] = icon
    kwargs['verification_level'] = discord.VerificationLevel(backup['verification_level'])
    kwargs['default_notifications'] = discord.NotificationLevel(backup['default_notifications'])
    kwargs['explicit_content_filter'] = discord.ContentFilter(backup['explicit_content_filter'])
    kwargs['premium_progress_bar_enabled'] = backup['premium_progress_bar_enabled']
    kwargs['widget_enabled'] = backup['widget_enabled']
    kwargs['afk_timeout'] = backup['afk_timeout']
    if backup['afk_channel_id'] is not None:
        kwargs['afk_channel'] = channel_map[backup['afk_channel_id']]
    if backup['system_channel_id'] is not None:
        kwargs['system_channel'] = channel_map[backup['system_channel_id']]
        # noinspection PyProtectedMember
        kwargs['system_channel_flags'] = discord.SystemChannelFlags()._from_value(backup['system_channel_flags'])
    
    await server.edit(**kwargs)
    return None