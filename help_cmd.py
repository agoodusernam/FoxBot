import discord
from discord.ext import commands

_FIELD_LIMIT = 1024
_DESC_LIMIT = 4096


def _chunk_lines(lines: list[str], limit: int) -> list[str]:
    """Split lines into chunks that each fit within `limit` chars when joined by newlines."""
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in lines:
        needed = len(line) + (1 if current else 0)
        if current and current_len + needed > limit:
            chunks.append("\n".join(current))
            current = [line]
            current_len = len(line)
        else:
            current.append(line)
            current_len += needed

    if current:
        chunks.append("\n".join(current))

    return chunks


def _cmd_line(cmd: commands.Command, prefix: str) -> str:
    brief = cmd.brief or "No description"
    aliases = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
    return f"`{prefix}{cmd.name}`{aliases} — {brief}"


class CustomHelpCommand(commands.MinimalHelpCommand):
    def __init__(self) -> None:
        super().__init__(no_category="Miscellaneous", sort_commands=True, dm_help=False)

    async def send_bot_help(self, mapping: dict[commands.Cog, list[commands.Command]]) -> None:  # type: ignore
        ctx: commands.Context = self.context
        if ctx.bot.blacklist.is_blacklisted(ctx.author.id):
            await ctx.message.channel.send(
                "You are not allowed to use this command.",
                delete_after=ctx.bot.config.del_after,
            )
            return

        is_admin: bool = (
            ctx.author.id in ctx.bot.config.admin_ids
            or ctx.author.id in ctx.bot.config.dev_ids
        )
        prefix = ctx.clean_prefix
        embeds: list[discord.Embed] = []

        for cog, cmds in mapping.items():
            cog_name = getattr(cog, "qualified_name", "Miscellaneous")
            regular_cmds: list[commands.Command] = await self.filter_commands(cmds, sort=True)

            admin_cmds: list[commands.Command] = []
            if is_admin:
                regular_names: set[str] = {c.qualified_name for c in regular_cmds}
                admin_cmds = [c for c in cmds if c.qualified_name not in regular_names]

            if not regular_cmds and not admin_cmds:
                continue

            regular_lines = [_cmd_line(c, prefix) for c in regular_cmds]
            admin_lines = [_cmd_line(c, prefix) for c in admin_cmds]

            # Commands go in description; admin commands go in a field.
            # Both are chunked so neither limit is exceeded.
            desc_chunks = _chunk_lines(regular_lines, _DESC_LIMIT) if regular_lines else [""]
            admin_chunks = _chunk_lines(admin_lines, _FIELD_LIMIT) if admin_lines else []

            for i, desc_chunk in enumerate(desc_chunks):
                title = cog_name if i == 0 else f"{cog_name} (cont.)"
                embed = discord.Embed(
                    title=f"{title} Commands",
                    description=desc_chunk or "No commands.",
                    color=discord.Color.blurple(),
                )
                embed.set_footer(text=f"Use {prefix}help [command] for details.")

                # Only attach admin fields on the last desc chunk to avoid duplication
                if i == len(desc_chunks) - 1:
                    for j, admin_chunk in enumerate(admin_chunks):
                        field_name = "Admin Commands" if j == 0 else "Admin Commands (cont.)"
                        embed.add_field(name=field_name, value=admin_chunk, inline=False)

                embeds.append(embed)

        if not embeds:
            await ctx.send("No commands available.")
            return

        total = len(embeds)
        for i, embed in enumerate(embeds):
            current_footer = embed.footer.text or ""
            embed.set_footer(text=f"Page {i + 1}/{total} • {current_footer}")

        if total == 1:
            await ctx.send(embed=embeds[0])
            return

        view = HelpPaginationView(embeds, ctx.author)
        await ctx.send(embed=embeds[0], view=view)


class HelpPaginationView(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed], author: discord.User | discord.Member) -> None:
        super().__init__(timeout=120)
        self.embeds = embeds
        self.author = author
        self.current_page = 0
        self.total_pages = len(embeds)
        self._update_buttons()

    def _update_buttons(self) -> None:
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == self.total_pages - 1
        self.page_button.label = f"{self.current_page + 1}/{self.total_pages}"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("You cannot use these buttons.", ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True  # type: ignore

    @discord.ui.button(label="◀", style=discord.ButtonStyle.primary, custom_id="prev")  # type: ignore
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.current_page -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @discord.ui.button(label="1/1", style=discord.ButtonStyle.secondary, disabled=True, custom_id="page")  # type: ignore
    async def page_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        pass

    @discord.ui.button(label="▶", style=discord.ButtonStyle.primary, custom_id="next")  # type: ignore
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.current_page += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
