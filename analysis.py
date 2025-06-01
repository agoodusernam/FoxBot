import db_stuff


def check_valid_syntax(message: dict) -> bool:
	if 'author' not in message or 'author_id' not in message or 'author_global_name' not in message:
		return False

	if 'content' not in message or 'reply_to' not in message or 'HasAttachments' not in message:
		return False

	if 'timestamp' not in message or 'channel' not in message:
		return False

	return True


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

			most_common_word = max(word_count, key = word_count.get)
			print(f"Most common word: '{most_common_word}' with {word_count[most_common_word]} occurrences")

			unique_words = set(word_count.keys())
			print(f"Total unique words: {len(unique_words)}")
			average_length = sum(len(word) for word in unique_words) / len(unique_words)
			print(f"Average length of unique words: {average_length:.2f} characters")

			most_active_users: list[dict[str, int]] = [{}]
			user_message_count = {}
			for message in valid_messages:
				user_id = message['author_global_name']
				if user_id not in user_message_count:
					user_message_count[user_id] = 0
				user_message_count[user_id] += 1

			most_active_users = [{"user": user, "num_messages": count} for user, count in user_message_count.items()]

			return {
				"total_messages":         len(valid_messages),
				"most_common_word":       most_common_word,
				"most_common_word_count": word_count[most_common_word],
				"total_unique_words":     len(unique_words),
				"average_length":         average_length,
				"active_users_lb":        most_active_users,
			}

		else:
			return "No valid messages found to analyse."

	except Exception as e:
		print(f"An error occurred: {e}")
		return e