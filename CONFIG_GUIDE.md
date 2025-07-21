# Bot Configuration System - Usage Guide

## Overview
Your bot config system has been completely overhauled with a modern, type-safe approach while keeping the convenient `bot.config.*` and `bot.blacklist.*` access patterns you requested.

## Key Improvements

### 1. **Type Safety & Validation**
- All configuration is now type-checked with dataclasses
- Automatic validation prevents invalid configurations
- IDE support with autocomplete for all config options

### 2. **Organized Structure**
```python
bot.config.command_prefix           # Basic settings
bot.config.del_after
bot.config.maintenance_mode

bot.config.admin_ids               # User permissions
bot.config.dev_ids

bot.config.no_log.user_ids         # Nested configurations
bot.config.no_log.channel_ids
bot.config.logging_channels.voice
bot.config.reaction_roles.message_id

bot.blacklist.is_blacklisted(user_id)  # Separate blacklist manager
bot.blacklist.add_user(user_id)
```

### 3. **Easy Configuration Management**
```python
# Save changes
bot.config.save()

# Reload from file
bot.config.reload()

# Convert emoji strings to Discord objects
emoji_dict = bot.config.get_emoji_to_role_discord_objects()
```

## Usage Examples

### In Your Cogs
```python
class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def example(self, ctx):
        # Access config values easily
        if ctx.author.id in self.bot.config.admin_ids:
            await ctx.send("You're an admin!", 
                         delete_after=self.bot.config.del_after)
        
        # Check blacklist
        if self.bot.blacklist.is_blacklisted(ctx.author.id):
            return
        
        # Use logging channels
        log_channel = self.bot.get_channel(self.bot.config.logging_channels.voice)
        if log_channel:
            await log_channel.send("Something happened!")
```

### Runtime Configuration Changes
Use the new config commands:
- `f!config` - View all config sections
- `f!config basic` - View basic settings
- `f!config basic maintenance_mode true` - Enable maintenance mode
- `f!save_config` - Save changes to file
- `f!reload_config` - Reload from file

## File Structure
- `config/bot_config.py` - Main configuration system
- `config/blacklist_manager.py` - Blacklist management
- `cogs/config_cmds.py` - Configuration commands
- `config.json` - Configuration file (auto-created)
- `blacklist_users.json` - Blacklist file (auto-managed)

## Migration Benefits
- **No more manual attribute assignment** - Everything is automatic
- **No more hardcoded values mixed with config** - Everything is in the config system
- **Type safety** - Catch configuration errors at startup
- **Organized structure** - Related settings are grouped together
- **Easy maintenance** - Add new config options by just adding to the dataclass
- **Backward compatibility** - Your existing `bot.config.*` usage still works

## Adding New Configuration Options
To add a new config option:

1. Add it to the appropriate dataclass in `bot_config.py`:
```python
@dataclass
class BotConfig:
    # ...existing fields...
    new_feature_enabled: bool = False
```

2. Add it to the default config:
```python
"new_feature_enabled": False
```

3. Use it in your code:
```python
if bot.config.new_feature_enabled:
    # Do something
```

The system automatically handles loading, saving, and validation!
