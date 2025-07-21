"""
Enhanced Bot Configuration System
Provides type-safe, validated configuration with easy bot.config.* access
"""
from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field
from pathlib import Path
import json
import discord


@dataclass
class NoLogConfig:
    """Configuration for channels/users to exclude from logging"""
    user_ids: list[int] = field(default_factory=list)
    channel_ids: list[int] = field(default_factory=list)
    category_ids: list[int] = field(default_factory=list)


@dataclass
class BlacklistConfig:
    """Configuration for send blacklist"""
    channel_ids: list[int] = field(default_factory=list)
    category_ids: list[int] = field(default_factory=list)


@dataclass
class LoggingChannelsConfig:
    """Configuration for logging channels"""
    voice: int | None = None
    moderation: int | None = None
    public_logs: int | None = None


@dataclass
class ReactionRolesConfig:
    """Configuration for reaction roles"""
    message_id: int | None = None
    emoji_to_role: dict[str, int] = field(default_factory=dict)


@dataclass
class BotConfig:
    """Main bot configuration class"""
    # Basic settings
    command_prefix: str = "f!"
    del_after: int = 3
    maintenance_mode: bool = False
    
    # User permissions
    admin_ids: list[int] = field(default_factory=list)
    dev_ids: list[int] = field(default_factory=list)
    blacklist_ids: list[int] = field(default_factory=list)
    
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
            "command_prefix": "f!",
            "del_after": 3,
            "admin_ids": [235644709714788352, 542798185857286144, 937278965557641227],
            "dev_ids": [542798185857286144],
            "blacklist_ids": [],
            "maintenance_mode": False,
            "no_log": {
                "user_ids": [1329366814517628969, 1329366963805491251, 1329367238146396211,
                            1329367408330145805, 235148962103951360, 1299640624848306177],
                "channel_ids": [],
                "category_ids": [1329366612821938207]
            },
            "send_blacklist": {
                "channel_ids": [],
                "category_ids": []
            },
            "logging_channels": {
                "voice": 1329366741909770261,
                "moderation": 1329367677940006952,
                "public_logs": 1345300442376310885
            },
            "reaction_roles": {
                "message_id": 1380639010564603976,
                "emoji_to_role": {
                    "<:jjs:1380607586231128155>": 1314274909815439420,
                    "❕": 1321214081977421916,
                    "<:grass_block:1380607192717328505>": 1380623674918310079,
                    "<:Vrchat:1380607441691214048>": 1380623882574368939,
                    "<:rust:1380606572127850639>": 1130284770757197896,
                    "❔": 1352341336459841688,
                    "🎬": 1380624012090150913,
                    "🎨": 1295024229799952394,
                    "<:Forsaken:1396046411610718279>": 1396045343958892605
                }
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BotConfig:
        """Create BotConfig instance from dictionary"""
        config = cls()
        
        # Basic settings
        config.command_prefix = data.get("command_prefix", config.command_prefix)
        config.del_after = data.get("del_after", config.del_after)
        config.maintenance_mode = data.get("maintenance_mode", config.maintenance_mode)
        
        # User permissions
        config.admin_ids = data.get("admin_ids", config.admin_ids)
        config.dev_ids = data.get("dev_ids", config.dev_ids)
        config.blacklist_ids = data.get("blacklist_ids", config.blacklist_ids)
        
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
            "command_prefix": self.command_prefix,
            "del_after": self.del_after,
            "maintenance_mode": self.maintenance_mode,
            "admin_ids": self.admin_ids,
            "dev_ids": self.dev_ids,
            "blacklist_ids": self.blacklist_ids,
            "no_log": {
                "user_ids": self.no_log.user_ids,
                "channel_ids": self.no_log.channel_ids,
                "category_ids": self.no_log.category_ids
            },
            "send_blacklist": {
                "channel_ids": self.send_blacklist.channel_ids,
                "category_ids": self.send_blacklist.category_ids
            },
            "logging_channels": {
                "voice": self.logging_channels.voice,
                "moderation": self.logging_channels.moderation,
                "public_logs": self.logging_channels.public_logs
            },
            "reaction_roles": {
                "message_id": self.reaction_roles.message_id,
                "emoji_to_role": self.reaction_roles.emoji_to_role
            }
        }
    
    def save(self, config_path: Path = Path("config.json")) -> None:
        """Save configuration to file"""
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4)
    
    def reload(self, config_path: Path = Path("config.json")) -> None:
        """Reload configuration from file"""
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


def load_config(config_path: Path = Path("config.json")) -> BotConfig:
    """Load configuration from file or create default"""
    if not config_path.exists():
        print("Config file not found, creating default config.json")
        config = BotConfig.from_dict(BotConfig.get_default_config())
        config.save(config_path)
        return config
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print("Configuration loaded successfully")
        return BotConfig.from_dict(data)
    except Exception as e:
        print(f"Error loading config: {e}")
        print("Creating default configuration")
        config = BotConfig.from_dict(BotConfig.get_default_config())
        config.save(config_path)
        return config
