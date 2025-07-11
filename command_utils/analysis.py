import collections
import copy
import datetime
from typing import Any

import discord
import matplotlib.pyplot as plt
from discord.ext.commands import Context

import utils.utils
from utils import db_stuff


def check_valid_syntax(message: dict) -> bool:
	"""Validate message contains all required keys."""
	required_keys = {
		'author', 'author_id', 'author_global_name',
		'content', 'reply_to', 'HasAttachments',
		'timestamp', 'channel', 'channel_id',
	}
	return all(key in message for key in required_keys)


def get_valid_messages(flag: str = None) -> tuple[list[dict], int]:
	"""Download and validate messages from the database."""
	# flag can be 'w' for last week, 'd' for last day, 'h' for last hour, or None for all messages
	excluded_ids: list[str] = ["1107579143140413580"]
	messages = db_stuff.download_all()
	total_messages = len(messages)
	if not messages:
		print('No messages found or failed to connect to the database.')
		return [], 0
	
	# Filter out excluded users
	all_messages = [msg for msg in messages if msg['author_id'] not in excluded_ids]
	
	# First get all valid messages and delete invalid ones
	valid_messages = []
	for message in all_messages:
		if check_valid_syntax(message):
			valid_messages.append(message)
		else:
			db_stuff.delete_message(message['_id'])
	
	# Then apply time filter if specified
	if flag:
		time_ago = None
		if flag == 'w':
			# Filter to last week
			time_ago = discord.utils.utcnow() - datetime.timedelta(days=7)
		elif flag == 'd':
			# Filter to last day
			time_ago = discord.utils.utcnow() - datetime.timedelta(days=1)
		elif flag == 'h':
			# Filter to last hour
			time_ago = discord.utils.utcnow() - datetime.timedelta(hours=1)
		
		if time_ago:
			valid_messages = [msg for msg in valid_messages
			                  if utils.utils.parse_utciso8601(msg['timestamp']) >= time_ago]
	
	print(f'Total valid messages: {len(valid_messages)}')
	print(f'Total messages in database: {total_messages}')
	return valid_messages, total_messages


def analyse_word_stats(content_list: list[str]) -> dict[str, Any]:
	"""Analyse word statistics from a list of message content."""
	if not content_list:
		return {}
	
	all_words = [word.lower() for msg in content_list for word in msg.split()]
	if not all_words:
		return {}
	
	word_count = collections.Counter(all_words)
	most_common_word, most_common_word_count = word_count.most_common(1)[0]
	unique_words = set(all_words)
	average_length = sum(len(word) for word in unique_words) / len(unique_words) if unique_words else 0
	
	return {
		'most_common_word':       most_common_word,
		'most_common_word_count': most_common_word_count,
		'total_unique_words':     len(unique_words),
		'average_length':         average_length
	}


def get_channel_stats(messages: list[dict]) -> list[dict]:
	"""Get statistics about channel activity."""
	if not messages:
		return []
	channel_counts = collections.Counter(msg['channel'] for msg in messages)
	return [{'channel': channel, 'num_messages': count}
	        for channel, count in channel_counts.items() if count > 0]


def analyse(flag: str = None) -> dict[str, Any] | str | Exception:
	"""Analyse all messages in the database."""
	try:
		valid_messages, total_messages = get_valid_messages(flag)
		if not valid_messages:
			return 'No valid messages found to analyse.'
		
		# Get message content list
		
		content_list = [message['content'] for message in valid_messages]
		
		# Analyse word statistics
		word_stats = analyse_word_stats(content_list)
		if not word_stats:
			return 'No valid content to analyze.'
		
		# Get user message counts
		user_message_count = collections.Counter(
				msg['author_id'] for msg in valid_messages
		)
		
		active_users = [{'user': user, 'num_messages': count}
		                for user, count in user_message_count.items()]
		
		# Get channel stats
		active_channels = get_channel_stats(valid_messages)
		
		return {
			'total_messages':         total_messages,
			'most_common_word':       word_stats['most_common_word'],
			'most_common_word_count': word_stats['most_common_word_count'],
			'total_unique_words':     word_stats['total_unique_words'],
			'average_length':         word_stats['average_length'],
			'active_users_lb':        active_users,
			'active_channels_lb':     active_channels,
			'total_users':            len(user_message_count),
		}
	
	except Exception as e:
		print(f'An error occurred: {e}')
		return e


def analyse_single_user(member: discord.User, flag: str = None) -> dict[str, Any] | str | None:
	"""Analyse messages from a specific user."""
	try:
		valid_messages, _ = get_valid_messages(flag)
		if not valid_messages:
			return None
		
		# Filter messages by this user
		messages_by_user = [msg for msg in valid_messages
		                    if msg['author_id'] == str(member.id)]
		
		if not messages_by_user:
			return f'No messages found for user {member.display_name}.'
		
		content_list = [msg['content'] for msg in messages_by_user]
		
		# Analyse word statistics
		word_stats = analyse_word_stats(content_list)
		if not word_stats:
			return f'No analyzable content found for user {member.display_name}.'
		
		# Get channel stats for this user
		active_channels = get_channel_stats(messages_by_user)
		most_recent_message = max(
				utils.utils.parse_utciso8601(msg['timestamp']) for msg in messages_by_user
		) if messages_by_user else None
		
		# Get user message counts
		user_message_count = collections.Counter(
				msg['author_id'] for msg in valid_messages
		)
		
		active_users = [{'user': user, 'num_messages': count}
		                for user, count in user_message_count.items()]
		
		active_user_lb = sorted(active_users, key=lambda x: x['num_messages'],
		                        reverse=True)
		active_user_lb_position = 0
		for i, user in enumerate(active_user_lb, 1):
			if user['user'] == str(member.id):
				active_user_lb_position = i
				break
		
		return {
			'total_messages':           len(messages_by_user),
			'most_common_word':         word_stats['most_common_word'],
			'most_common_word_count':   word_stats['most_common_word_count'],
			'total_unique_words':       word_stats['total_unique_words'],
			'average_length':           word_stats['average_length'],
			'active_channels_lb':       active_channels,
			'active_users_lb_position': active_user_lb_position,
			'most_recent_message':      f"{most_recent_message:%H:%M:%S} on the {most_recent_message:%d.%m.%Y}" if most_recent_message else 'N/A',
		}
	
	except Exception as e:
		print(f'An error occurred: {e}')
		return None


async def format_analysis(ctx: Context, graph=False) -> None:
	"""Format and send analysis results."""
	message = ctx.message
	try:
		await message.delete()
	except discord.Forbidden:
		pass
	flag = message.content.split()[-1].replace('-', '')
	if flag not in ['w', 'd', 'h', 'all']:
		flag = None
	else:
		message.content = message.content.replace(f'-{flag}', '')
	
	new_msg = await message.channel.send('Analysing...')
	if len(message.content.split()) > 1:
		try:
			member_id = utils.utils.get_id_from_str(message.content.split()[1])
			member = await ctx.bot.fetch_user(member_id)
			if member is None:
				await new_msg.edit(content=f'User with ID {member_id} not found.')
				return
			await analyse_single_user_cmd(message, member, flag)
			await new_msg.delete()
			return
		except ValueError:
			await new_msg.edit(content='Invalid user ID format. Please provide a valid integer ID.')
			return
	
	try:
		result = analyse(flag)
		
		if isinstance(result, dict):
			guild = ctx.bot.get_guild(1081760248433492140)
			active_users_lb = copy.deepcopy(result['active_users_lb'])
			top_5_active_users = sorted(active_users_lb, key=lambda x: x['num_messages'],
			                            reverse=True)[:5]
			top_5_active_channels = sorted(result['active_channels_lb'], key=lambda x: x['num_messages'], reverse=True)[
			                        :5]
			for user in top_5_active_users:
				
				member = guild.get_member(int(user['user'].strip()))
				to_set = user['user']
				if isinstance(member, discord.Member):
					to_set = member.display_name
				if member is None:
					to_set = (await ctx.bot.fetch_user(int(user['user'].strip()))).display_name
				
				user['user'] = to_set
			
			msg = (f"{result['total_messages']} total messages analysed\n" +
			       f"Most common word: {result['most_common_word']} said {result['most_common_word_count']} times\n" +
			       f"({result['total_unique_words']} unique words, average length: {result['average_length']:.2f} " +
			       f"characters)\nTotal users: {result['total_users']}\n" +
			       f"Top 5 most active users:\n")
			
			for i, user in enumerate(top_5_active_users, start=1):
				msg += f"**{i}. {user['user']}** {user['num_messages']} messages\n"
			
			msg += '\nTop 5 most active channels:\n'
			for i, channel in enumerate(top_5_active_channels, start=1):
				msg += f"**{i}. {channel['channel']}** {channel['num_messages']} messages\n"
			
			await new_msg.edit(content=msg)
			if not graph:
				return
			
			top_15_active_users = sorted(result['active_users_lb'], key=lambda x: x['num_messages'], reverse=True)[:15]
			usernames = []
			message_counts = []
			for user in top_15_active_users:
				display = user['user']
				user_id = int(user['user'].strip())
				discord_member = guild.get_member(user_id)
				if discord_member is None:
					discord_member = await ctx.bot.fetch_user(user_id)
				
				if discord_member is not None:
					display = discord_member.display_name
				
				usernames.append(''.join(e for e in display if e.isalnum()))
				
				message_counts.append(user['num_messages'])
			
			# Reverse so members with most messages are at the top
			usernames = usernames[::-1]
			message_counts = message_counts[::-1]
			
			plt.figure(figsize=(10, 6), facecolor='#1f1f1f')  # Dark background
			ax = plt.gca()
			ax.set_facecolor('#2d2d2d')  # Slightly lighter background for plot area
			plt.barh(usernames, message_counts, color='#8a2be2')  # Purple bars
			plt.xlabel('Number of Messages', color='white')
			plt.title('Top 15 Active Users', color='white')
			plt.tick_params(axis='both', colors='white')  # White text for tick labels
			for spine in ax.spines.values():
				spine.set_color('#555555')  # Lighter border
			plt.tight_layout()
			
			graph_file = 'top_active_users.png'
			plt.savefig(graph_file)
			plt.close()
			
			await message.channel.send(file=discord.File(graph_file))
		elif isinstance(result, Exception):
			await message.channel.send(f'Error during analysis: {result}')
		elif isinstance(result, str):
			await message.channel.send(result)
		else:
			await message.channel.send('No valid messages found for analysis.')
	except Exception as e:
		await ctx.send(f'Error during analysis: {e}')


async def analyse_single_user_cmd(message: discord.Message, member: discord.User, flag: str) -> None:
	"""Format and send analysis results for a single user."""
	result = analyse_single_user(member, flag)
	
	if isinstance(result, dict):
		active_channels = sorted(result['active_channels_lb'], key=lambda x: x['num_messages'],
		                         reverse=True)[:5]
		num_channels = 5
		if flag == 'all':
			num_channels = len(result['active_channels_lb'])
			active_channels = sorted(result['active_channels_lb'], key=lambda x: x['num_messages'],
			                         reverse=True)
		
		msg = (f"{result['total_messages']} messages found for **{member.name}**\n"
		       f"Most common word: {result['most_common_word']} said {result['most_common_word_count']} times\n" +
		       f"({result['total_unique_words']} unique words, average length: {result['average_length']:.2f} " +
		       f"characters)\n" +
		       f"Leaderboard position: {result['active_users_lb_position']}\n" +
		       f"Most recent message sent at: {result['most_recent_message']}\n" +
		       f"Top {num_channels} most active channels:\n")
		
		for i, channel in enumerate(active_channels, 1):
			msg += f"**{i}. {channel['channel']}** {channel['num_messages']} messages\n"
		
		print(msg)
		await message.channel.send(msg)
	elif isinstance(result, str):
		await message.channel.send(result)
	else:
		await message.channel.send('An error occurred during analysis.')


def get_voice_statistics() -> dict[str, list[dict[str, Any]]] | None:
	"""Retrieve voice statistics from MongoDB and calculate user and channel totals"""
	sessions = db_stuff.download_voice_sessions()
	
	if not sessions:
		return None
	
	# Calculate user statistics
	user_stats = {}
	for session in sessions:
		user_id = session.get('user_id')
		user_name = session.get('user_global_name') or session.get('user_name')
		duration = session.get('duration_seconds', 0)
		
		if user_id not in user_stats:
			user_stats[user_id] = {
				'name':          user_name,
				'total_seconds': 0
			}
		
		user_stats[user_id]['total_seconds'] += duration
	
	# Calculate channel statistics
	channel_stats = {}
	for session in sessions:
		channel_id = session.get('channel_id')
		channel_name = session.get('channel_name')
		duration = session.get('duration_seconds', 0)
		
		if channel_id not in channel_stats:
			channel_stats[channel_id] = {
				'name':          channel_name,
				'total_seconds': 0
			}
		
		channel_stats[channel_id]['total_seconds'] += duration
	
	# Sort statistics
	top_users = sorted(
			[{'id': user_id, 'name': data['name'], 'total_seconds': data['total_seconds']}
			 for user_id, data in user_stats.items()],
			key=lambda x: x['total_seconds'],
			reverse=True
	)
	
	top_channels = sorted(
			[{'id': channel_id, 'name': data['name'], 'total_seconds': data['total_seconds']}
			 for channel_id, data in channel_stats.items()],
			key=lambda x: x['total_seconds'],
			reverse=True
	)
	
	return {
		'users':    top_users[:5],  # Top 5 users
		'channels': top_channels[:5]  # Top 5 channels
	}


def format_duration(seconds: int) -> str:
	"""Format seconds into a readable duration string"""
	hours, remainder = divmod(seconds, 3600)
	minutes, seconds = divmod(remainder, 60)
	
	if hours > 0:
		return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
	elif minutes > 0:
		return f"{int(minutes)}m {int(seconds)}s"
	else:
		return f"{int(seconds)}s"


async def voice_analysis(message: discord.Message) -> None:
	"""Generate voice activity statistics and send as a message"""
	stats = get_voice_statistics()
	
	if not stats:
		await message.channel.send("No voice activity data available.")
		return
	
	result = "**Voice Activity Statistics**\n\n"
	
	# Top users
	result += "**Top 5 Users by Voice Activity**\n"
	for i, user in enumerate(stats['users'], 1):
		formatted_time = format_duration(user['total_seconds'])
		result += f"{i}. {user['name']}: {formatted_time}\n"
	
	result += "\n"
	
	# Top channels
	result += "**Top 5 Voice Channels by [Man Hours](https://en.wikipedia.org/wiki/Man-hour)**\n"
	for i, channel in enumerate(stats['channels'], 1):
		formatted_time = format_duration(channel['total_seconds'])
		result += f"{i}. {channel['name']}: {formatted_time}\n"
	
	await message.channel.send(result)


async def format_voice_analysis(ctx: Context) -> None:
	"""Format and send voice analysis results."""
	message = ctx.message
	try:
		await message.delete()
	except discord.Forbidden:
		pass
	
	new_msg = await message.channel.send('Analysing voice statistics...')
	
	if len(message.content.split()) > 1:
		try:
			member_id = utils.utils.get_id_from_str(message.content.split()[1])
			member = await ctx.bot.fetch_user(member_id)
			if member is None:
				await new_msg.edit(content=f'User with ID {member_id} not found.')
				return
			
			await add_voice_analysis_for_user(message, member)
			await new_msg.delete()
			return
		except ValueError:
			await new_msg.edit(
					content=f'Invalid user ID format. Please provide a valid integer ID. Provided: {message.content.split()[1]}')
			return
	
	# No user specified, show general voice stats
	try:
		await voice_analysis(message)
		await new_msg.delete()
	except Exception as e:
		await message.channel.send(f'Error during voice analysis: {e}')


def get_user_voice_statistics(user_id: str) -> dict[str, Any] | None:
	"""Retrieve voice statistics for a specific user"""
	sessions = db_stuff.download_voice_sessions()
	
	if not sessions:
		return None
	
	# Filter sessions for this user
	user_sessions = [s for s in sessions if s.get('user_id') == user_id]
	
	if not user_sessions:
		return None
	
	user_name = user_sessions[0].get('user_global_name') or user_sessions[0].get('user_name')
	
	total_seconds = sum(s.get('duration_seconds', 0) for s in user_sessions)
	
	# Calculate per-channel stats
	channel_stats = {}
	for session in user_sessions:
		channel_id = session.get('channel_id')
		channel_name = session.get('channel_name')
		duration = session.get('duration_seconds', 0)
		
		if channel_id not in channel_stats:
			channel_stats[channel_id] = {
				'name':          channel_name,
				'total_seconds': 0
			}
		
		channel_stats[channel_id]['total_seconds'] += duration
	
	top_channels = sorted(
			[{'id': channel_id, 'name': data['name'], 'total_seconds': data['total_seconds']}
			 for channel_id, data in channel_stats.items()],
			key=lambda x: x['total_seconds'],
			reverse=True
	)
	
	return {
		'user_id':       user_id,
		'user_name':     user_name,
		'total_seconds': total_seconds,
		'channels':      top_channels[:5]  # Top 5 channels
	}


async def add_voice_analysis_for_user(message: discord.Message, member: discord.User) -> None:
	"""Generate voice activity statistics for a specific user"""
	stats = get_user_voice_statistics(str(member.id))
	
	if not stats:
		await message.channel.send(f"No voice activity data available for {member.display_name}.")
		return
	
	formatted_total_time = format_duration(stats['total_seconds'])
	
	result = f"**Voice Activity for {stats['user_name']}**\n\n"
	result += f"**Total time in voice channels:** {formatted_total_time}\n\n"
	
	result += "**Top 5 Most Used Voice Channels**\n"
	for i, channel in enumerate(stats['channels'], 1):
		formatted_time = format_duration(channel['total_seconds'])
		result += f"{i}. {channel['name']}: {formatted_time}\n"
	
	await message.channel.send(result)
