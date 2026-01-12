import discord
from discord.ext.commands import Context


async def create_private_vc(ctx: Context, member: discord.Member) -> bool:
    """
    Creates a private voice channel for the member.
    :param member: The member for whom to create the private VC.
    :param ctx: The context in which the command is invoked.
    """
    guild = member.guild
    vc_name = f"private_{member.display_name}"
    
    # Create the voice channel
    category = discord.utils.get(guild.categories, id=1081760248878071888)
    if category is None:
        raise discord.ext.commands.CommandError("Something terrible has happened")
    
    try:
        private_vc = await guild.create_voice_channel(vc_name, category=category, position=len(category.channels),
                                                      overwrites={guild.default_role: discord.PermissionOverwrite(
                                                              view_channel=False)})
        
        overwrite: discord.PermissionOverwrite = discord.PermissionOverwrite(
                connect=True,
                speak=True,
                view_channel=True,
                mute_members=True,
                deafen_members=True,
                move_members=True,
        )
        
        await private_vc.set_permissions(member, overwrite=overwrite)
        await member.move_to(private_vc)
    
    except discord.NotFound:
        raise discord.ext.commands.CommandError("The role or member being edited is not part of the guild.")
    
    except discord.Forbidden:
        raise discord.ext.commands.BotMissingPermissions(["manage_channels"])
    
    except discord.HTTPException as e:
        raise discord.ext.commands.CommandError(f"Failed to create voice channel: {e}")
    
    except Exception as e:
        raise discord.ext.commands.CommandError(f"An unexpected error occurred: {e}")
    
    return True


async def give_rich_role(ctx: Context, member: discord.Member) -> bool:
    """
    Gives the 'Rich' role to the member.
    :param member: The member to whom to give the 'Rich' role.
    :param ctx: The context in which the command is invoked.
    """
    rich_role = discord.utils.get(member.guild.roles, id=1394949504888999957)
    if rich_role is None:
        raise discord.ext.commands.RoleNotFound("Rich role not found in the server.")
    
    try:
        await member.add_roles(rich_role)
        
    except discord.Forbidden:
        raise discord.ext.commands.BotMissingPermissions(["manage_roles"])
    
    return True


async def send_announcement(ctx: Context, member: discord.Member) -> None:
    """
    Allows the bot to send an announcement message in the server.
    :param ctx: The context in which the command is invoked.
    :param member: The member who sends the announcement.
    """
    # TODO: Figure out how to get a message from the user to send as an announcement
    raise NotImplementedError
