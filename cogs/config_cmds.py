"""
Configuration management commands for bot admins
"""
import dataclasses
from typing import get_type_hints

import discord
from discord.ext import commands

from cogs import config_cmds_utils
from command_utils.CContext import CContext, CoolBot
from command_utils.checks import is_admin, is_dev
from config.bot_config import ConfigBase


class ConfigCog(commands.Cog, name="Configuration"):
    """Commands for managing bot configuration"""
    
    def __init__(self, bot: CoolBot) -> None:
        self.bot: CoolBot = bot
    
    @commands.command(name="config", brief="View or modify bot configuration")
    @commands.check(is_dev)
    async def config_command(self, ctx: CContext, section: str | None = None, key: str | None = None, *, value: str | None = None):
        """
        View or modify bot configuration
        Usage:
        - f!config - Show all config sections
        - f!config <section> - Show section details
        - f!config <section> <key> - Show specific value
        - f!config <section> <key> <value> - Set specific value
        """
        if section is None:
            # Show all config sections
            embed = discord.Embed(title="Bot Configuration", color=discord.Color.blue())
            embed.add_field(name="Available Sections",
                          value="• basic - Basic bot settings\n"
                                "• users - User permission lists\n"
                                "• logging - Logging configuration\n"
                                "• reaction_roles - Reaction role settings",
                          inline=False)
            embed.add_field(name="Usage",
                          value=f"`{ctx.prefix}config <section>` to view section details",
                          inline=False)
            await ctx.send(embed=embed)
            return
        
        section = section.lower()
        
        if section == "basic":
            await self._handle_generic_config(ctx, self.bot.config, key, value, 
                                            exclude_keys={'no_log', 'send_blacklist', 'logging_channels', 'reaction_roles', 'admin_ids', 'dev_ids', 'blacklist_ids'})
        elif section == "users":
            await self._handle_users_config(ctx)
        elif section == "logging":
             await self._handle_generic_config(ctx, self.bot.config.logging_channels, key, value)
        elif section == "reaction_roles":
             await self._handle_generic_config(ctx, self.bot.config.reaction_roles, key, value)
             
        else:
            await ctx.send(f"Unknown section: {section}", delete_after=self.bot.config.del_after)
    
    async def _handle_generic_config(self, ctx: CContext, config_obj: ConfigBase, key: str | None, value: str | None, exclude_keys: set[str] | None = None):
        if exclude_keys is None:
            exclude_keys = set()

        if key is None:
            embed = discord.Embed(title=f"{type(config_obj).__name__} Configuration", color=discord.Color.blue())
            
            field_list = []
            
            for f in dataclasses.fields(config_obj):
                if f.name in exclude_keys:
                    continue
                    
                val = getattr(config_obj, f.name)
                # Format value for display
                if isinstance(val, list):
                    val_str = f"[{len(val)} items]"
                elif isinstance(val, dict):
                    val_str = f"{{...}} ({len(val)} items)"
                else:
                    val_str = f"`{val}`"
                    
                field_list.append(f"• **{f.name}**: {val_str}")
            
            if not field_list:
                embed.description = "No configurable fields in this section."
            else:
                embed.description = "\n".join(field_list)
                
            await ctx.send(embed=embed)
            return
        
        key = key.lower()
        if not hasattr(config_obj, key) or key in exclude_keys:
             await ctx.send(f"Unknown key: {key}", delete_after=self.bot.config.del_after)
             return
        
        target_field = next((f for f in dataclasses.fields(config_obj) if f.name == key), None)
        if not target_field:
             await ctx.send(f"Unknown key (not in fields): {key}", delete_after=self.bot.config.del_after)
             return
        
        if value is None:
            val = getattr(config_obj, key)
            await ctx.send(f"`{key}`: `{val}`")
            return
            
        type_hints = get_type_hints(type(config_obj))
        type_hint = type_hints.get(key, target_field.type)
        
        try:
            new_value = config_cmds_utils.convert_value(value, type_hint)
            setattr(config_obj, key, new_value)
            await ctx.send(f"Set `{key}` to `{new_value}`")
            success = ctx.bot.config.save()
            if success is not None:
                await ctx.bot.log_error(success)
        except ValueError as e:
            await ctx.send(f"Error setting value: {e}", delete_after=self.bot.config.del_after)
    
    async def _handle_users_config(self, ctx: CContext):
        embed = discord.Embed(title="User Configuration", color=discord.Color.orange())
        admin_ids = ", ".join(f"<@{uid}>" for uid in self.bot.config.admin_ids)
        dev_ids = ", ".join(f"<@{uid}>" for uid in self.bot.config.dev_ids)
        embed.add_field(name="admin_ids", value=f"{admin_ids}", inline=True)
        embed.add_field(name="dev_ids", value=f"{dev_ids}", inline=True)
        await ctx.send(embed=embed)
        return
        
    @commands.command(name="reload_config", brief="Reload configuration from file")
    @commands.check(is_admin)
    async def reload_config(self, ctx: CContext):
        """Reload bot configuration from config.json"""
        try:
            self.bot.config.reload()
            await ctx.send("Configuration reloaded successfully!")
        except Exception as e:
            await ctx.send(f"Failed to reload config: {e}", delete_after=self.bot.config.del_after)
    
    @commands.command(name="save_config", brief="Save current configuration to file")
    @commands.check(is_admin)
    async def save_config(self, ctx: CContext):
        """Save current bot configuration to config.json"""
        success = self.bot.config.save()
        if success is not None:
            await self.bot.log_error(success, ctx.channel)
        else:
            await ctx.send("Configuration saved successfully!")


async def setup(bot):
    await bot.add_cog(ConfigCog(bot))
