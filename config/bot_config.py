"""
Enhanced Bot Configuration System
Provides type-safe, validated configuration with easy bot.config.* access
"""
import logging
from typing import Any, Self
from dataclasses import dataclass, field
from pathlib import Path
import json
import discord

logger = logging.getLogger('discord')

@dataclass
class ConfigBase:
    """Base configuration class with common methods"""
    pass

@dataclass
class NoLogConfig(ConfigBase):
    """Configuration for channels/users to exclude from logging"""
    user_ids: list[int] = field(default_factory=list)
    channel_ids: list[int] = field(default_factory=list)
    category_ids: list[int] = field(default_factory=list)


@dataclass
class BlacklistConfig(ConfigBase):
    """Configuration for send blacklist"""
    channel_ids: list[int] = field(default_factory=list)
    category_ids: list[int] = field(default_factory=list)


@dataclass
class LoggingChannelsConfig(ConfigBase):
    """Configuration for logging channels"""
    voice: int | None = None
    moderation: int | None = None
    public_logs: int | None = None


@dataclass
class ReactionRolesConfig(ConfigBase):
    """Configuration for reaction roles"""
    message_id: int | None = None
    emoji_to_role: dict[str, int] = field(default_factory=dict)


@dataclass
class BotConfig(ConfigBase):
    """Main bot configuration class"""
    # Basic settings
    command_prefix: str = "f!"
    del_after: int = 3
    maintenance_mode: bool = False
    guild_id: int = 0
    verified_roles: list[int] = field(default_factory=list)
    staging: bool = False
    counting_channel: int = 0
    highest_count: int = 0
    last_count: int = 0
    last_count_user: int = 0
    tts_requires_role: bool = False
    required_tts_role: int = 0
    counting_ban_role: int = 0
    counting_fail_role: int = 0
    counting_fails: dict[int, int] = field(default_factory=dict)
    counting_successes: dict[int, int] = field(default_factory=dict)
    highest_user_count: dict[int, int] = field(default_factory=dict)
    last_counted_message_id: int = 0
    
    # User permissions
    admin_ids: list[int] = field(default_factory=list)
    dev_ids: list[int] = field(default_factory=list)
    blacklist_ids: list[int] = field(default_factory=list)
    staff_role_id: int = 0
    
    # Nested configurations
    no_log: NoLogConfig = field(default_factory=NoLogConfig)
    send_blacklist: BlacklistConfig = field(default_factory=BlacklistConfig)
    logging_channels: LoggingChannelsConfig = field(default_factory=LoggingChannelsConfig)
    reaction_roles: ReactionRolesConfig = field(default_factory=ReactionRolesConfig)
    
    # Dynamic properties (not saved to config)
    today: str | None = field(default=None, init=False)
    
    @classmethod
    def get_default_config(cls) -> dict[str, Any]:
        """Returns default configuration dictionary"""
        return {
            "command_prefix":   "f!",
            "del_after":        3,
            "admin_ids":        [],
            "dev_ids":          [],
            "blacklist_ids":    [],
            "maintenance_mode": False,
            "guild_id":         0,
            "no_log":           {
                "user_ids":     [],
                "channel_ids":  [],
                "category_ids": []
            },
            "send_blacklist":   {
                "channel_ids":  [],
                "category_ids": []
            },
            "logging_channels": {
                "voice":       0,
                "moderation":  0,
                "public_logs": 0
            },
            "reaction_roles":   {
                "message_id":    0,
                "emoji_to_role": {}
            },
            
            "verified_roles":   [],
            "staff_role_id":    0,
            "staging":          False,
            "counting_channel": 0,
            "highest_count":    0,
            "last_count":       0,
            "last_count_user":   0,
            "tts_requires_role": False,
            "required_tts_role": 0,
            "counting_ban_role": 0,
            "counting_fail_role": 0,
            "counting_fails": {},
            "counting_successes": {},
            "highest_user_count": {},
            "last_counted_message_id": 0
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create BotConfig instance from dictionary"""
        config = cls()
        
        # Basic settings
        config.command_prefix = data.get("command_prefix", config.command_prefix)
        config.del_after = data.get("del_after", config.del_after)
        config.maintenance_mode = data.get("maintenance_mode", config.maintenance_mode)
        config.guild_id = data.get("guild_id", config.guild_id)
        config.verified_roles = data.get("verified_roles", config.verified_roles)
        config.staging = data.get("staging", config.staging)
        config.counting_channel = data.get("counting_channel", config.counting_channel)
        config.highest_count = data.get("highest_count", config.highest_count)
        config.last_count = data.get("last_count", config.last_count)
        config.last_count_user = data.get("last_count_user", config.last_count_user)
        config.tts_requires_role = data.get("tts_requires_role", config.tts_requires_role)
        config.required_tts_role = data.get("required_tts_role", config.required_tts_role)
        config.counting_ban_role = data.get("counting_ban_role", config.counting_ban_role)
        config.counting_fail_role = data.get("counting_fail_role", config.counting_fail_role)
        config.counting_fails = data.get("counting_fails", config.counting_fails)
        config.counting_successes = data.get("counting_successes", config.counting_successes)
        config.highest_user_count = data.get("highest_user_count", config.highest_user_count)
        config.last_counted_message_id = data.get("last_counted_id", config.last_counted_message_id)
        
        # User permissions
        config.admin_ids = data.get("admin_ids", config.admin_ids)
        config.dev_ids = data.get("dev_ids", config.dev_ids)
        config.blacklist_ids = data.get("blacklist_ids", config.blacklist_ids)
        config.staff_role_id = data.get("staff_role_id", config.staff_role_id)
        
        # Nested configurations
        if "no_log" in data:
            no_log_data = data["no_log"]
            config.no_log = NoLogConfig(
                    user_ids=no_log_data.get("user_ids", []),
                    channel_ids=no_log_data.get("channel_ids", []),
                    category_ids=no_log_data.get("category_ids", [])
            )
        
        if "send_blacklist" in data:
            blacklist_data = data["send_blacklist"]
            config.send_blacklist = BlacklistConfig(
                    channel_ids=blacklist_data.get("channel_ids", []),
                    category_ids=blacklist_data.get("category_ids", [])
            )
        
        if "logging_channels" in data:
            logging_data = data["logging_channels"]
            config.logging_channels = LoggingChannelsConfig(
                    voice=logging_data.get("voice"),
                    moderation=logging_data.get("moderation"),
                    public_logs=logging_data.get("public_logs")
            )
        
        if "reaction_roles" in data:
            reaction_data = data["reaction_roles"]
            config.reaction_roles = ReactionRolesConfig(
                    message_id=reaction_data.get("message_id"),
                    emoji_to_role=reaction_data.get("emoji_to_role", {})
            )
        
        return config
    
    def to_dict(self) -> dict[str, Any]:
        """Convert BotConfig to dictionary for saving"""
        return {
            "command_prefix":   self.command_prefix,
            "del_after":        self.del_after,
            "maintenance_mode": self.maintenance_mode,
            "guild_id":         self.guild_id,
            "admin_ids":        self.admin_ids,
            "dev_ids":          self.dev_ids,
            "blacklist_ids":    self.blacklist_ids,
            "staff_role_id":    self.staff_role_id,
            
            "no_log":           {
                "user_ids":     self.no_log.user_ids,
                "channel_ids":  self.no_log.channel_ids,
                "category_ids": self.no_log.category_ids
            },
            "send_blacklist":   {
                "channel_ids":  self.send_blacklist.channel_ids,
                "category_ids": self.send_blacklist.category_ids
            },
            "logging_channels": {
                "voice":       self.logging_channels.voice,
                "moderation":  self.logging_channels.moderation,
                "public_logs": self.logging_channels.public_logs
            },
            "reaction_roles":   {
                "message_id":    self.reaction_roles.message_id,
                "emoji_to_role": self.reaction_roles.emoji_to_role
            },
            
            "verified_roles":   self.verified_roles,
            "staging":          self.staging,
            "counting_channel": self.counting_channel,
            "highest_count":    self.highest_count,
            "last_count":       self.last_count,
            "last_count_user":  self.last_count_user,
            "tts_requires_role": self.tts_requires_role,
            "required_tts_role": self.required_tts_role,
            "counting_ban_role": self.counting_ban_role,
            "counting_fail_role": self.counting_fail_role,
            "counting_fails": self.counting_fails,
            "counting_successes": self.counting_successes,
            "highest_user_count": self.highest_user_count,
            "last_counted_message_id": self.last_counted_message_id
        }
    
    def save(self, config_path: Path = Path("config.json")) -> None:
        """Save configuration to file"""
        logger.debug(f"Saving config to {config_path}")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4)
    
    def reload(self, config_path: Path = Path("config.json")) -> None:
        """Reload configuration from file"""
        logger.debug("Reloading config")
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            new_config = self.from_dict(data)
            self.__dict__.update(new_config.__dict__)
    
    def get_emoji_to_role_discord_objects(self) -> dict[discord.PartialEmoji, int]:
        """Convert emoji strings to discord.PartialEmoji objects"""
        emoji_dict = {}
        for emoji_str, role_id in self.reaction_roles.emoji_to_role.items():
            if emoji_str.startswith('<') and emoji_str.endswith('>'):
                # Custom emoji
                emoji_dict[discord.PartialEmoji.from_str(emoji_str)] = role_id
            else:
                # Unicode emoji
                emoji_dict[discord.PartialEmoji(name=emoji_str)] = role_id
        return emoji_dict
    
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a specific configuration option"""
        return getattr(self, key, default)
    
    def __getitem__(self, key: str) -> Any:
        item = getattr(self, key, None)
        if item is None:
            raise KeyError(f"Key '{key}' not found in config")
        return item
    
    def add_counting_fail(self, user_id: int) -> None:
        """Add a counting fail to the config"""
        self.counting_fails[user_id] = self.counting_fails.get(user_id, 0) + 1
    
    def reset_counting_fails(self, user_id: int) -> bool:
        """Reset the number of counting fails for a user"""
        if user_id not in self.counting_fails:
            return False
        self.counting_fails[user_id] = 0
        return True
    
    def user_counted(self, user_id: str, number: int, message_id: str) -> None:
        """Record that a user has counted a number"""
        logger.debug(f"User {user_id}, in message {message_id} counted {number}")
        self.counting_successes[user_id] = self.counting_successes.get(user_id, 0) + 1
        if number > self.highest_user_count.get(user_id, 0):
            self.highest_user_count[user_id] = number
            
        self.last_counted_message_id = message_id
        return
    

def move_invalid_config(config_path: Path = Path("config.json")) -> None:
    """Move invalid config file to backup"""
    logger.debug("Moving invalid config to backup")
    backup_path = Path("invalid_config.json")
    if config_path.exists():
        config_path.rename(backup_path)

def load_config(config_path: Path = Path("config.json")) -> BotConfig:
    """Load configuration from file or create default"""
    logger.debug("Loading config")
    
    if not config_path.exists():
        logger.info("Config file not found, creating default config.json")
        config = BotConfig.from_dict(BotConfig.get_default_config())
        config.save(config_path)
        return config
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        logger.info("Configuration loaded successfully")
        return BotConfig.from_dict(data)
    
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        logger.error("Creating default configuration and moving old config to invalid_config.json")
        move_invalid_config(config_path)
        config = BotConfig.from_dict(BotConfig.get_default_config())
        return config


def get_config_option(option: str, default: Any = None) -> Any:
    """
    Retrieve a specific configuration option from the config file.
    :param option: str: The configuration option to retrieve.
    :param default: Any: The default value to return if the option is not found.
    :return: Any: The value of the configuration option or the default value.
    """
    config: BotConfig = load_config()
    return config.get(option, default)
