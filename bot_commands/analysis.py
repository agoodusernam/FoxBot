import time
from typing import Dict, List, Optional, Union, Any

import discord

from utils import db_stuff


def check_valid_syntax(message: dict) -> bool:
	"""Validate message contains all required keys."""
	required_keys = {
		'author', 'author_id', 'author_global_name',
		'content', 'reply_to', 'HasAttachments',
		'timestamp', 'channel'
	}
	return all(key in message for key in required_keys)


def get_valid_messages() -> List[dict]:
	"""Download and validate messages from database."""
	messages = db_stuff.download_all()
	if not messages:
		print('No messages found or failed to connect to the database.')
		return []

	valid_messages = []
	for message in messages:
		if check_valid_syntax(message):
			valid_messages.append(message)
		else:
			db_stuff.delete_message(message['_id'])

	print(f'Total valid messages: {len(valid_messages)}')
	return valid_messages


def analyze_word_stats(content_list: List[str]) -> Dict[str, Any]:
	"""Analyze word statistics from a list of message content."""
	if not content_list:
		return {}

	word_count = {}
	for msg in content_list:
		for word in msg.split():
			word = word.lower()
			word_count[word] = word_count.get(word, 0) + 1

	if not word_count:
		return {}

	most_common_word = max(word_count, key = word_count.get)
	unique_words = set(word_count.keys())
	average_length = sum(len(word) for word in unique_words) / len(unique_words) if unique_words else 0

	return {
		'most_common_word':       most_common_word,
		'most_common_word_count': word_count[most_common_word],
		'total_unique_words':     len(unique_words),
		'average_length':         average_length
	}


def get_channel_stats(messages: List[dict]) -> List[dict]:
	"""Get statistics about channel activity."""
	channel_counts = {}
	for message in messages:
		channel = message['channel']
		channel_counts[channel] = channel_counts.get(channel, 0) + 1

	return [{'channel': channel, 'num_messages': count}
			for channel, count in channel_counts.items()]


def analyse() -> Optional[Union[Dict[str, Any], str, Exception]]:
	"""Analyze all messages in the database."""
	try:
		valid_messages = get_valid_messages()
		if not valid_messages:
			return 'No valid messages found to analyse.'

		# Get message content list
		content_list = [message['content'] for message in valid_messages]

		# Analyze word statistics
		word_stats = analyze_word_stats(content_list)
		if not word_stats:
			return 'No valid content to analyze.'

		# Get user message counts
		user_message_count = {}
		for message in valid_messages:
			user_id = message['author_global_name'] or message['author']
			user_message_count[user_id] = user_message_count.get(user_id, 0) + 1

		active_users = [{'user': user, 'num_messages': count}
						for user, count in user_message_count.items()]

		# Get channel stats
		active_channels = get_channel_stats(valid_messages)

		return {
			'total_messages':         len(valid_messages),
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


async def analyse_single_user(member: discord.Member) -> Optional[Union[Dict[str, Any], str]]:
	"""Analyze messages from a specific user."""
	try:
		valid_messages = get_valid_messages()
		if not valid_messages:
			return None

		# Filter messages by this user
		global_name = member.global_name
		author_name = member.name
		messages_by_user = [msg for msg in valid_messages
							if msg['author_global_name'] == global_name or msg['author'] == author_name]

		if not messages_by_user:
			return f'No messages found for user {member.mention}.'

		content_list = [msg['content'] for msg in messages_by_user]

		# Analyze word statistics
		word_stats = analyze_word_stats(content_list)
		if not word_stats:
			return f'No analyzable content found for user {member.mention}.'

		# Get channel stats for this user
		active_channels = get_channel_stats(messages_by_user)

		return {
			'total_messages':         len(messages_by_user),
			'most_common_word':       word_stats['most_common_word'],
			'most_common_word_count': word_stats['most_common_word_count'],
			'total_unique_words':     word_stats['total_unique_words'],
			'average_length':         word_stats['average_length'],
			'active_channels_lb':     active_channels,
		}

	except Exception as e:
		print(f'An error occurred: {e}')
		return None


async def format_analysis(admin_ids: List[int], cooldown: Union[bool, int], del_after: int,
						  message: discord.Message) -> None:
	"""Format and send analysis results."""
	await message.delete()
	if message.author.id not in admin_ids:
		await message.channel.send('You are not allowed to use this command.', delete_after = del_after)
		return

	if type(cooldown) == int:
		await message.channel.send(
				f'Please wait {cooldown} seconds before using this command again.',
				delete_after = del_after)
		return

	new_msg = await message.channel.send('Analysing...')
	if len(message.content.split()) > 1:
		try:
			member_id = int(message.content.split()[1].replace('@', '').replace('<', '').replace('>', '').strip())
			member = message.guild.get_member(member_id)
			if member is None:
				await new_msg.edit(content = f'User with ID {member_id} not found.')
				return
			await analyse_single_user_cmd(message, member)
			await new_msg.delete()
			return
		except ValueError:
			await new_msg.edit(content = 'Invalid user ID format. Please provide a valid integer ID.')
			return

	try:
		result = analyse()
		await new_msg.delete()

		if isinstance(result, dict):
			top_5_active_users = sorted(result['active_users_lb'], key = lambda x: x['num_messages'],
										reverse = True)[:5]
			top_5_active_channels = sorted(result['active_channels_lb'], key = lambda x: x['num_messages'],
										   reverse = True)[:5]

			msg = (f"{result['total_messages']} total messages analysed\n"
				   f"Most common word: {result['most_common_word']} said {result['most_common_word_count']} times\n"
				   f"({result['total_unique_words']} unique words, average length: {result['average_length']:.2f} characters)\n"
				   f"Total users: {result['total_users']}\n"
				   f"Top 5 most active users:\n")

			for i, user in enumerate(top_5_active_users, start = 1):
				username = user['user'] or 'Unknown User'
				msg += f"**{i}. {username}** {user['num_messages']} messages\n"

			msg += '\nTop 5 most active channels:\n'
			for i, channel in enumerate(top_5_active_channels, 1):
				msg += f"**{i}. {channel['channel']}** {channel['num_messages']} messages\n"

			await message.channel.send(msg)
		elif isinstance(result, Exception):
			await message.channel.send(f'Error during analysis: {result}')
		elif isinstance(result, str):
			await message.channel.send(result)
		else:
			await message.channel.send('No valid messages found for analysis.')
	except Exception as e:
		await message.channel.send(f'Error during analysis: {e}')


async def analyse_single_user_cmd(message: discord.Message, member: discord.Member) -> None:
	"""Format and send analysis results for a single user."""
	result = await analyse_single_user(member)

	if isinstance(result, dict):
		top_5_active_channels = sorted(result['active_channels_lb'], key = lambda x: x['num_messages'],
									   reverse = True)[:5]
		msg = (f"{result['total_messages']} messages found for **{member.name}**\n"
			   f"Most common word: {result['most_common_word']} said {result['most_common_word_count']} times\n"
			   f"({result['total_unique_words']} unique words, average length: {result['average_length']:.2f} characters)\n"
			   f"Top 5 most active channels:\n")

		for i, channel in enumerate(top_5_active_channels, 1):
			msg += f"**{i}. {channel['channel']}** {channel['num_messages']} messages\n"

		await message.channel.send(msg)
	elif isinstance(result, str):
		await message.channel.send(result)
	else:
		await message.channel.send('An error occurred during analysis.')


def check_analyse_cooldown(client) -> Union[bool, int]:
	"""Check if analysis cooldown has expired.
	Returns True if ready, or seconds remaining if on cooldown.
	"""
	current_time = int(time.time())
	time_elapsed = current_time - client.cooldowns['analyse']['last_time']
	cooldown_complete = time_elapsed >= client.cooldowns['analyse']['duration']

	if cooldown_complete:
		client.cooldowns['analyse']['last_time'] = current_time
		return True
	return client.cooldowns['analyse']['duration'] - time_elapsed