import discord


def handle_join(member: discord.Member, after: discord.VoiceState):
	print(f'{member.name} joined {after.channel.name}')
	raise NotImplementedError

def handle_leave(member: discord.Member, before: discord.VoiceState):
	print(f'{member.name} left {before.channel.name}')
	raise NotImplementedError

def handle_move(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
	print(f'{member.name} moved from {before.channel.name} to {after.channel.name}')
	raise NotImplementedError
