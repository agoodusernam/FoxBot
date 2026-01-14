# Custom help command formatting
import discord
from discord.ext import commands


class CustomHelpCommand(commands.DefaultHelpCommand):
    def __init__(self):
        super().__init__(
                no_category="Miscellaneous",
                width=100,
                sort_commands=True,
                dm_help=False
        )
    
    async def send_bot_help(self, mapping: dict[commands.Cog, list[commands.Command]]) -> None:  # type: ignore
        ctx: commands.Context = self.context
        if ctx.bot.blacklist.is_blacklisted(ctx.author.id):
            await ctx.message.channel.send('You are not allowed to use this command.',
                    delete_after=ctx.bot.config.del_after)
            return
        
        is_admin: bool = ctx.author.id in ctx.bot.config.admin_ids or ctx.author.id in ctx.bot.config.dev_ids
        embeds = []
        
        # Create a page for each cog
        for cog, cmds in mapping.items():
            cog_name = getattr(cog, "qualified_name", "Miscellaneous")
            
            # Filter commands the user can run
            regular_cmds: list[commands.Command] = await self.filter_commands(cmds, sort=True)
            
            admin_cmds: list[commands.Command] = []
            if is_admin:
                all_cmds: list[commands.Command] = cmds
                regular_cmd_names: set[str] = {cmd.qualified_name for cmd in regular_cmds}
                admin_cmds = [cmd for cmd in all_cmds if cmd.qualified_name not in regular_cmd_names]
            
            # Only create a page if there are commands to show
            if not regular_cmds and not admin_cmds:
                continue
            
            embed: discord.Embed = discord.Embed(
                    title=f"{cog_name} Commands",
                    description=f"Use `{ctx.prefix}help [command]` for more info on a command.",
                    color=discord.Color.blue()
            )
            
            if regular_cmds:
                cmd_list: list[str] = []
                for cmd in regular_cmds:
                    brief = cmd.brief or "No description"
                    usage = cmd.usage or f"{ctx.prefix}{cmd.name}"
                    cmd_list.append(f"`{usage}` - {brief}")
                
                embed.add_field(
                        name="Commands",
                        value="\n".join(cmd_list),
                        inline=False
                )
            
            if admin_cmds:
                admin_cmd_list: list[str] = []
                for cmd in admin_cmds:
                    brief = cmd.brief or "No description"
                    usage = cmd.usage or f"{ctx.prefix}{cmd.name}"
                    admin_cmd_list.append(f"`{usage}` - {brief}")
                
                embed.add_field(
                        name="Admin Commands",
                        value="\n".join(admin_cmd_list),
                        inline=False
                )
            
            embeds.append(embed)
        
        if not embeds:
            await ctx.send("No commands to show.")
            return
        
        # Add a footer to each embed
        for i, embed in enumerate(embeds):
            embed.set_footer(text=f"Page {i + 1}/{len(embeds)}")
        
        # If there's only one page, no need for pagination
        if len(embeds) == 1:
            await ctx.send(embed=embeds[0])
            return
        
        # Use buttons for pagination
        pagination_view: HelpPaginationView = HelpPaginationView(embeds, ctx.author)
        await ctx.send(embed=embeds[0], view=pagination_view)


class HelpPaginationView(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed], author: discord.User | discord.Member) -> None:
        super().__init__(timeout=60)
        self.embeds: list[discord.Embed] = embeds
        self.author: discord.User | discord.Member = author
        self.current_page: int = 0
        self.total_pages: int = len(embeds)
        
        # Update button states initially
        self.update_buttons()
    
    def update_buttons(self) -> None:
        # Disable previous button on first page
        self.prev_button.disabled = (self.current_page == 0)
        # Disable next button on last page
        self.next_button.disabled = (self.current_page == self.total_pages - 1)
        # Update the page counter
        self.page_button.label = f"Page {self.current_page + 1}/{self.total_pages}"
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Only allow the original command author to use the buttons
        if interaction.user != self.author:
            await interaction.response().send_message("You cannot use these buttons.", ephemeral=True)  # type: ignore
            return False
        return True
    
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, emoji="⬅️",  # type: ignore
            custom_id="prev")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response().edit_message(embed=self.embeds[self.current_page], view=self)  # type: ignore
    
    @discord.ui.button(label="Page 1/2", style=discord.ButtonStyle.secondary, disabled=True,  # type: ignore
            custom_id="page")
    async def page_button(self, interaction: discord.Interaction, button) -> None:
        # This button is just a label and doesn't do anything when clicked
        pass
    
    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, emoji="➡️", custom_id="next")  # type: ignore
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)  # type: ignore
