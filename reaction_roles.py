import discord

to_send_msg = """JJS role: :jjs: 
JJS PING: ❕ 
Minecraft: :grass_block:
VRChat: :Vrchat:
Rust: :rust:
fun fact ping:❔ 
movie night ping: 🎬"""


async def send_reaction_role_msg(channel: discord.TextChannel) -> None:

	msg = await channel.send(to_send_msg)

	reactions = [':jjs:', '❕', ':grass_block:', ':Vrchat:', ':rust:', '❔', '🎬']
	for reaction in reactions:
		await msg.add_reaction(reaction)
