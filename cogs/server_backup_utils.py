from pathlib import Path
import random
import string
from typing import Self, overload

from type_stuff.permission_types import (
    PermissionOverwriteDict,
    SerialisedRole,
    TextChannel,
    VoiceChannel,
    CategoryChannel,
    SerialisedChannel
)

import discord


def _serialise_perm_overwrite(overwrite: discord.PermissionOverwrite) -> PermissionOverwriteDict:
    return {k: v for k, v in overwrite} # type: ignore

def _serialise_perm_overwrite_channel(channel: discord.abc.GuildChannel) -> dict[int, PermissionOverwriteDict]:
    roles: dict[int, discord.PermissionOverwrite] = {}
    for k, v in channel.overwrites.items():
        if isinstance(k, discord.Role) or (isinstance(k, discord.Object) and k.type == discord.Role):
            roles[k.id] = v
    return {k: _serialise_perm_overwrite(v) for k, v in roles} # type: ignore

class DiscordSerializer:
    instance = None
    def __new__(cls) -> Self:
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance
    
    def __init__(self) -> None:
        self.roles: dict[int, SerialisedRole] = {}
        self.channels: dict[int, SerialisedChannel] = {}
    
    
    @staticmethod
    async def save_role_icon(icon: discord.Asset, timestamp: int) -> str:
        path_addition: str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        icon_path: Path = Path('icons').absolute() / str(timestamp) / path_addition
        file_name = icon.url.split('/')[-1]
        file_path = icon_path / file_name
        await icon.save(file_path)
        return str(file_path)
    
    async def serialise_role(self, role: discord.Role, timestamp: int) -> None:
        icon: tuple[bool, str] | None
        if role.display_icon is None:
            icon = None
        elif isinstance(role.display_icon, str):
            icon = (True, role.display_icon)
        else:
            icon = False, await self.save_role_icon(role.display_icon, timestamp)
        
        serialised_role: SerialisedRole = {
            'name':             role.name,
            'hoist':            role.hoist,
            'mentionable':      role.mentionable,
            'colour':           role.colour.to_rgb(),
            'secondary_colour': role.secondary_colour.to_rgb() if role.secondary_colour is not None else None,
            'tertiary_colour':  role.tertiary_colour.to_rgb() if role.tertiary_colour is not None else None,
            'permissions':      role.permissions.value,
            'icon':             icon
        }
        self.roles[role.id] = serialised_role
        return None
    
    @overload
    async def serialise_channel(self, channel: discord.TextChannel) -> TextChannel: ...
    
    @overload
    async def serialise_channel(self, channel: discord.VoiceChannel) -> VoiceChannel: ...
    
    @overload
    async def serialise_channel(self, channel: discord.CategoryChannel) -> CategoryChannel: ...
    
    async def serialise_channel(self, channel: discord.TextChannel | discord.VoiceChannel | discord.CategoryChannel):
        if isinstance(channel, discord.TextChannel):
            return await self._serialise_text_channel(channel)
        elif isinstance(channel, discord.VoiceChannel):
            return await self._serialise_voice_channel(channel)
        elif isinstance(channel, discord.CategoryChannel):
            return await self._serialise_category_channel(channel)
        else:
            raise ValueError(f"Channel type {type(channel)} not recognised.")
    
    @staticmethod
    async def _serialise_text_channel(channel: discord.TextChannel) -> TextChannel:
        return TextChannel(
                channel_type="text",
                name=channel.name,
                category=channel.category.id if channel.category is not None else None,
                overwrites=_serialise_perm_overwrite_channel(channel),
                permissions_synced=channel.permissions_synced,
                nsfw=channel.is_nsfw(),
                topic=channel.topic,
                default_auto_archive_duration=channel.default_auto_archive_duration,
                default_thread_slowmode_delay=channel.default_thread_slowmode_delay
        )
    
    @staticmethod
    async def _serialise_voice_channel(channel: discord.VoiceChannel) -> VoiceChannel:
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
                slowmode_delay=channel.slowmode_delay # type: ignore
        )
    
    @staticmethod
    async def _serialise_category_channel(channel: discord.CategoryChannel) -> CategoryChannel:
        return CategoryChannel(
                channel_type="category",
                name=channel.name,
                category=None,
                overwrites=_serialise_perm_overwrite_channel(channel),
                permissions_synced=channel.permissions_synced,
                nsfw=False,
                channels=[c.id for c in channel.channels]
        )
