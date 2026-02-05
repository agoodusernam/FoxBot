from typing import TypedDict, Literal


class PermissionOverwriteDict(TypedDict):
    create_instant_invite: bool | None
    kick_members: bool | None
    ban_members: bool | None
    administrator: bool | None
    manage_channels: bool | None
    manage_guild: bool | None
    add_reactions: bool | None
    view_audit_log: bool | None
    priority_speaker: bool | None
    stream: bool | None
    read_messages: bool | None
    view_channel: bool | None
    send_messages: bool | None
    send_tts_messages: bool | None
    manage_messages: bool | None
    embed_links: bool | None
    attach_files: bool | None
    read_message_history: bool | None
    mention_everyone: bool | None
    external_emojis: bool | None
    use_external_emojis: bool | None
    view_guild_insights: bool | None
    connect: bool | None
    speak: bool | None
    mute_members: bool | None
    deafen_members: bool | None
    move_members: bool | None
    use_voice_activation: bool | None
    change_nickname: bool | None
    manage_nicknames: bool | None
    manage_roles: bool | None
    manage_permissions: bool | None
    manage_webhooks: bool | None
    manage_expressions: bool | None
    manage_emojis: bool | None
    manage_emojis_and_stickers: bool | None
    use_application_commands: bool | None
    request_to_speak: bool | None
    manage_events: bool | None
    manage_threads: bool | None
    create_public_threads: bool | None
    create_private_threads: bool | None
    send_messages_in_threads: bool | None
    external_stickers: bool | None
    use_external_stickers: bool | None
    use_embedded_activities: bool | None
    moderate_members: bool | None
    use_soundboard: bool | None
    use_external_sounds: bool | None
    send_voice_messages: bool | None
    create_expressions: bool | None
    create_events: bool | None
    send_polls: bool | None
    create_polls: bool | None
    use_external_apps: bool | None

class SerialisedRole(TypedDict):
    name: str
    hoist: bool
    mentionable: bool
    colour: tuple[int, int, int]
    secondary_colour: tuple[int, int, int] | None
    tertiary_colour: tuple[int, int, int] | None
    permissions: int
    icon: tuple[bool, str] | None
    # if icon[0] is True, icon[1] is the unicode emoji as a str.
    # else, icon[1] is the absolute file path to the role icon image as a str.
    id: int

class ChannelBase(TypedDict):
    id: int

class SerialisedChannel(ChannelBase):
    channel_type: Literal["text", "voice", "category", "stage", "forum"]
    name: str
    category: int | None
    # the internal ID of the category this channel belongs to, or None if it's not in a category
    overwrites: dict[int, PermissionOverwriteDict]
    # overwrites[internal_id] is the permission overwrites for that role
    permissions_synced: bool
    nsfw: bool

class TextChannel(SerialisedChannel):
    default_auto_archive_duration: int
    default_thread_slowmode_delay: int
    topic: str | None

class VoiceChannel(SerialisedChannel):
    bitrate: int
    user_limit: int
    rtc_region: str | None
    slowmode_delay: int

class CategoryChannel(SerialisedChannel):
    channels: list[SerialisedChannel]

class Guild(TypedDict):
    name: str
    description: str | None
    icon: str | None
    afk_channel_id: int | None
    afk_timeout: int
    verification_level: int
    default_notifications: int
    explicit_content_filter: int
    system_channel_id: int | None
    system_channel_flags: int
    nsfw_level: int
    premium_progress_bar_enabled: bool
    widget_enabled: bool
    roles: dict[int, SerialisedRole]
    categories: list[CategoryChannel]
    no_category_channels: list[SerialisedChannel]