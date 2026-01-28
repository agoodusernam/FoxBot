import discord

C = discord.Colour | tuple[int, int, int] | str | int


def create_log_embed(user_name: str,
                     display_url: str,
                     description: str,
                     colour: C,
                     embed_title: str,
                     footer: str | None = None
                     ) -> discord.Embed:
    
    if isinstance(colour, str):
        colour = discord.Colour.from_str(colour)
    if isinstance(colour, tuple):
        colour = discord.Colour.from_rgb(*colour)
    
    embed = discord.Embed(title=embed_title, colour=colour)
    embed.set_author(name=user_name, icon_url=display_url)
    embed.description = description
    embed.timestamp = discord.utils.utcnow()
    if footer:
        embed.set_footer(text=footer)
    return embed
