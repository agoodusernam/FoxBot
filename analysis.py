import discord

import db_stuff


def check_valid_syntax(message: dict) -> bool:
	required_keys = {
		'author', 'author_id', 'author_global_name',
		'content', 'reply_to', 'HasAttachments',
		'timestamp', 'channel'
	}
	return all(key in message for key in required_keys)


def analyse() -> dict | Exception | str | None:
	try:
		messages = db_stuff.download_all()

		if messages is None:
			print("No messages found or failed to connect to the database.")
			return None

		valid_messages = []
		content = []

		for message in messages:
			if not check_valid_syntax(message):
				db_stuff.delete_message(message['_id'])
				continue

			valid_messages.append(message)
			content.append(message['content'])

		print(f"Total valid messages: {len(valid_messages)}")

		if content:
			word_count = {}
			for msg in content:
				for word in msg.split():
					word = word.lower()
					if word not in word_count:
						word_count[word] = 0
					word_count[word] += 1

			most_common_word = max(word_count, key=word_count.get)
			print(f"Most common word: '{most_common_word}' with {word_count[most_common_word]} occurrences")

			unique_words = set(word_count.keys())
			print(f"Total unique words: {len(unique_words)}")
			average_length = sum(len(word) for word in unique_words) / len(unique_words)
			print(f"Average length of unique words: {average_length:.2f} characters")

			user_message_count = {}
			for message in valid_messages:
				user_id = message['author_global_name']
				if user_id not in user_message_count:
					user_message_count[user_id] = 0
				user_message_count[user_id] += 1

			most_active_users = [{"user": user, "num_messages": count} for user, count in user_message_count.items()]

			most_active_channels = {}
			for message in valid_messages:
				channel = message['channel']
				if channel not in most_active_channels:
					most_active_channels[channel] = 0
				most_active_channels[channel] += 1

			most_active_channels = [{"channel": channel, "num_messages": count} for channel, count in
			                        most_active_channels.items()]

			return {
				"total_messages":         len(valid_messages),
				"most_common_word":       most_common_word,
				"most_common_word_count": word_count[most_common_word],
				"total_unique_words":     len(unique_words),
				"average_length":         average_length,
				"active_users_lb":        most_active_users,
				"active_channels_lb":     most_active_channels,
				"total_users":            len(user_message_count),
			}

		else:
			return "No valid messages found to analyse."

	except Exception as e:
		print(f"An error occurred: {e}")
		return e


async def format_analysis(admin_ids: list[int], cooldown: bool | int, del_after: int,
                          message: discord.Message):
	await message.delete()
	if message.author.id not in admin_ids:
		await message.channel.send('You are not allowed to use this command.', delete_after=del_after)
		return

	if type(cooldown) == int:
		await message.channel.send(
				f'Please wait {cooldown} seconds before using this command again.',
				delete_after=del_after)
		return

	new_msg = await message.channel.send('Analysing...')
	try:
		result = analyse()
		await new_msg.delete()
		if isinstance(result, dict):
			top_5_active_users = sorted(result["active_users_lb"], key=lambda x: x["num_messages"],
			                            reverse=True)[:5]

			top_5_active_channels = sorted(result["active_channels_lb"], key=lambda x: x["num_messages"],
			                               reverse=True)[:5]

			msg = (f'{result["total_messages"]} total messages analysed\n'
			       f'Most common word: {result["most_common_word"]} said {result["most_common_word_count"]} times \n'
			       f'({result["total_unique_words"]} unique words, average length: {result["average_length"]:.2f} characters)\n'
			       f'Total users: {result["total_users"]}\n'
			       f'Top 5 most active users:\n')
			for i, user in enumerate(top_5_active_users, start=1):
				realUser = user["user"]

				if realUser is None:
					realUser = f"Unknown User {user['user']}"

				msg += f'**{i}. {realUser}** {user["num_messages"]} messages\n'

			msg += '\n'

			msg += f'Top 5 most active channels:\n'
			for i, channel in enumerate(top_5_active_channels, 1):
				msg += f'**{i}. {channel["channel"]}** {channel["num_messages"]} messages\n'

			await message.channel.send(msg)
		elif isinstance(result, Exception):
			await message.channel.send(f'Error during analysis: {result}')
		elif isinstance(result, str):
			await message.channel.send(result)

		else:
			print("No valid messages found for analysis.")
	except Exception as e:
		print(f"Error during analysis: {e}")
