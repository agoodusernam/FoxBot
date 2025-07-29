"""
Configuration management commands for bot admins
"""
import discord
from discord.ext import commands
from discord.ext.commands import Context
from command_utils.checks import is_admin


class ConfigCog(commands.Cog, name="Configuration"):
    """Commands for managing bot configuration"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="config", brief="View or modify bot configuration")
    @commands.check(is_admin)
    async def config_command(self, ctx: Context, section: str = None, key: str = None, *, value: str = None):
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
                                "• reaction_roles - Reaction role settings\n"
                                "• blacklist - Blacklist management",
                          inline=False)
            embed.add_field(name="Usage",
                          value=f"`{ctx.prefix}config <section>` to view section details",
                          inline=False)
            await ctx.send(embed=embed)
            return
        
        section = section.lower()
        
        if section == "basic":
            await self._handle_basic_config(ctx, key, value)
        elif section == "users":
            await self._handle_users_config(ctx, key, value)
        elif section == "logging":
            await self._handle_logging_config(ctx, key, value)
        elif section == "reaction_roles":
            await self._handle_reaction_roles_config(ctx, key, value)
        elif section == "blacklist":
            await self._handle_blacklist_config(ctx, key, value)
        else:
            await ctx.send(f"Unknown section: {section}", delete_after=self.bot.config.del_after)
    
    async def _handle_basic_config(self, ctx: Context, key, value):
        if key is None:
            embed = discord.Embed(title="Basic Configuration", color=discord.Color.green())
            embed.add_field(name="command_prefix", value=f"`{self.bot.config.command_prefix}`", inline=True)
            embed.add_field(name="del_after", value=f"`{self.bot.config.del_after}`", inline=True)
            embed.add_field(name="maintenance_mode", value=f"`{self.bot.config.maintenance_mode}`", inline=True)
            await ctx.send(embed=embed)
            return
        
        key = key.lower()
        if value is None:
            # Show specific value
            if hasattr(self.bot.config, key):
                current_value = getattr(self.bot.config, key)
                await ctx.send(f"`{key}`: `{current_value}`")
            else:
                await ctx.send(f"Unknown key: {key}", delete_after=self.bot.config.del_after)
            return
        
        # Set value
        if key == "command_prefix":
            self.bot.config.command_prefix = value
            await ctx.send(f"✅ Command prefix set to `{value}`")
        elif key == "del_after":
            try:
                self.bot.config.del_after = int(value)
                await ctx.send(f"✅ Delete after time set to `{value}` seconds")
            except ValueError:
                await ctx.send("❌ Delete after time must be a number", delete_after=self.bot.config.del_after)
                return
        elif key == "maintenance_mode":
            self.bot.config.maintenance_mode = value.lower() in ('true', '1', 'yes', 'on')
            await ctx.send(f"✅ Maintenance mode set to `{self.bot.config.maintenance_mode}`")
        else:
            await ctx.send(f"Unknown or read-only key: {key}", delete_after=self.bot.config.del_after)
            return
        
        # Save config
        self.bot.config.save()
    
    async def _handle_users_config(self, ctx: Context, key, value):
        if key is None:
            embed = discord.Embed(title="User Configuration", color=discord.Color.orange())
            admin_ids = ", ".join(f"<@{uid}>" for uid in self.bot.config.admin_ids)
            dev_ids = ", ".join(f"<@{uid}>" for uid in self.bot.config.dev_ids)
            embed.add_field(name="admin_ids", value=f"{admin_ids}", inline=True)
            embed.add_field(name="dev_ids", value=f"{dev_ids}", inline=True)
            await ctx.send(embed=embed)
            return
        
        # User management would require more complex handling
        await ctx.send("User management commands coming soon!", delete_after=self.bot.config.del_after)
    
    async def _handle_logging_config(self, ctx: Context, key: str, value: str):
        if key is None:
            embed = discord.Embed(title="Logging Configuration", color=discord.Color.purple())
            embed.add_field(name="voice", value=f"<#{self.bot.config.logging_channels.voice}>" if self.bot.config.logging_channels.voice else "Not set", inline=True)
            embed.add_field(name="moderation", value=f"<#{self.bot.config.logging_channels.moderation}>" if self.bot.config.logging_channels.moderation else "Not set", inline=True)
            embed.add_field(name="public_logs", value=f"<#{self.bot.config.logging_channels.public_logs}>" if self.bot.config.logging_channels.public_logs else "Not set", inline=True)
            await ctx.send(embed=embed)
            return
        
        # Channel management would require parsing channel mentions/IDs
        await ctx.send("Logging channel management commands coming soon!", delete_after=self.bot.config.del_after)
    
    async def _handle_reaction_roles_config(self, ctx: Context, key: str, value: str):
        if key is None:
            embed = discord.Embed(title="Reaction Roles Configuration", color=discord.Color.gold())
            embed.add_field(name="message_id", value=f"`{self.bot.config.reaction_roles.message_id}`" if self.bot.config.reaction_roles.message_id else "Not set", inline=True)
            embed.add_field(name="emoji_count", value=f"{len(self.bot.config.reaction_roles.emoji_to_role)} emojis", inline=True)
            await ctx.send(embed=embed)
            return
        
        await ctx.send("Reaction role management commands coming soon!", delete_after=self.bot.config.del_after)
    
    async def _handle_blacklist_config(self, ctx: Context, key: str, value: str):
        if key is None:
            blacklist_ids = ", ".join(f"<@{uid}>" for uid in self.bot.blacklist) if self.bot.blacklist else "No users blacklisted"
            embed = discord.Embed(title="Blacklist Configuration", color=discord.Color.red())
            embed.add_field(name="blacklisted_users", value=f"{blacklist_ids}", inline=True)
            await ctx.send(embed=embed)
            return
        
        await ctx.send("Blacklist management commands coming soon!", delete_after=self.bot.config.del_after)
    
    @commands.command(name="reload_config", brief="Reload configuration from file")
    @commands.check(is_admin)
    async def reload_config(self, ctx: Context):
        """Reload bot configuration from config.json"""
        try:
            self.bot.config.reload()
            await ctx.send("✅ Configuration reloaded successfully!")
        except Exception as e:
            await ctx.send(f"❌ Failed to reload config: {e}", delete_after=self.bot.config.del_after)
    
    @commands.command(name="save_config", brief="Save current configuration to file")
    @commands.check(is_admin)
    async def save_config(self, ctx: Context):
        """Save current bot configuration to config.json"""
        try:
            self.bot.config.save()
            await ctx.send("✅ Configuration saved successfully!")
        except Exception as e:
            await ctx.send(f"❌ Failed to save config: {e}", delete_after=self.bot.config.del_after)


async def setup(bot):
    await bot.add_cog(ConfigCog(bot))
