import discord

to_send_msg = """JJS role: <:jjs:1380607586231128155> 
JJS PING: ❕ 
Minecraft: <:grass_block:1380607192717328505> 
VRChat: <:Vrchat:1380607441691214048> 
Rust: <:rust:1380606572127850639> 
fun fact ping:❔ 
movie night ping: 🎬"""


async def send_reaction_role_msg(channel: discord.TextChannel) -> int:

	msg = await channel.send(to_send_msg)

	reactions = ['<:jjs:1380607586231128155>', '❕', '<:grass_block:1380607192717328505>',
				 '<:Vrchat:1380607441691214048>', '<:rust:1380606572127850639>', '❔', '🎬']
	for reaction in reactions:
		await msg.add_reaction(reaction)

	return msg.id
