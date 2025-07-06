import os
from typing import Any, Mapping

import discord
import pymongo
from gridfs import GridFS
from pymongo.mongo_client import MongoClient
from pymongo.results import DeleteResult
from pymongo.server_api import ServerApi
# Purely for type hinting
from pymongo.synchronous.collection import Collection
from pymongo.synchronous.database import Database

# Global client instance
_mongo_client: MongoClient | None = None


def _connect():
	global _mongo_client
	# Return the existing connection if available
	if _mongo_client is not None:
		return _mongo_client

	uri = os.getenv('MONGO_URI')
	
	client = MongoClient(uri, server_api=ServerApi('1'), serverSelectionTimeoutMS=5000, tls=True,
	                     tlsCertificateKeyFile="mongo_cert.pem")
	try:
		client.admin.command('ping')
		_mongo_client = client  # Store the connection
		return client
	except ConnectionError:
		print('Failed to connect to MongoDB')
		return False
	except Exception as e:
		print(e)
		return False


def disconnect():
	global _mongo_client
	if _mongo_client is not None:
		try:
			_mongo_client.close()
			print('MongoDB connection closed')
		except Exception as e:
			print(f'Error closing MongoDB connection: {e}')
		finally:
			_mongo_client = None


def send_message(message: Mapping[str, Any]) -> None:
	client = _connect()
	if not client:
		print('Failed to connect to MongoDB')
		return

	db = client['discord']
	collection: Collection[Mapping[str, Any]] = db['messages']

	try:
		collection.insert_one(message)
		print('Message saved successfully')
	except Exception as e:
		print(f'Error saving message: {e}')


def bulk_send_messages(messages: list[Mapping[str, Any]]) -> None:
	client = _connect()
	if not client:
		print('Failed to connect to MongoDB')
		return

	db: Database[Mapping[str, Any]] = client['discord']
	collection: Collection[Mapping[str, Any]] = db['messages']

	try:
		collection.insert_many(messages)
		print(f'{len(messages)} messages saved successfully')
	except Exception as e:
		print(f'Error saving messages: {e}')


async def send_attachment(message: discord.Message, attachment: discord.Attachment) -> None:
	client = _connect()
	if not client:
		print('Failed to connect to MongoDB')
		return None

	db = client['discord']
	fs = GridFS(db, 'attachments')  # Create GridFS instance

	try:
		# Download the attachment data
		attachment_bytes = await attachment.read()

		# Store metadata
		metadata = {
			'message_id':         str(message.id),
			'author_global_name': message.author.global_name,
			'content_type':       attachment.content_type,
			'timestamp':          message.created_at.isoformat()
		}

		# Store file in GridFS
		file_id = fs.put(
				attachment_bytes,
				filename=attachment.filename,
				metadata=metadata
		)
		print(f'Attachment saved successfully: {attachment.filename}')
		return None
	except Exception as e:
		print(f'Error saving attachment: {e}')
		return None


def download_all() -> list[dict[str, str]] | None:
	client = _connect()
	if not client:
		raise ConnectionError('Failed to connect to MongoDB')

	db = client['discord']
	collection = db['messages']

	try:
		messages = collection.find({})
		return list(messages)

	except Exception as e:
		print(f'Error retrieving messages: {e}')
		return None


def delete_message(ObjId: str) -> None:
	client = _connect()
	if not client:
		print('Failed to connect to MongoDB')
		return

	db = client['discord']
	collection = db['messages']
	try:
		result = collection.delete_one({'_id': ObjId})
		if result.deleted_count > 0:
			print('Message deleted successfully')
		else:
			print('No message found with the given ID')
	except Exception as e:
		print(f'Error deleting message: {e}')


def del_channel_from_db(channel: discord.TextChannel) -> None:
	client = _connect()
	if not client:
		print('Failed to connect to MongoDB')
		return

	db = client['discord']
	collection = db['messages']

	try:
		result: DeleteResult = collection.delete_many({'channel_id': channel.id})
		print(f'Deleted {result.deleted_count} messages from channel {channel.id}')
	except Exception as e:
		print(f'Error deleting messages from channel {channel.id}: {e}')


def send_voice_session(session_data: Mapping[str, Any]) -> None:
	client = _connect()
	if not client:
		print('Failed to connect to MongoDB')
		return

	db = client['discord']
	collection: Collection[Mapping[str, Any]] = db['voice_sessions']

	try:
		collection.insert_one(session_data)
		print(f'Voice session for {session_data["user_name"]} saved successfully')
	except Exception as e:
		print(f'Error saving voice session: {e}')


def download_voice_sessions() -> list[Mapping[str, Any]] | None:
	client = _connect()
	if not client:
		print('Failed to connect to MongoDB')
		return None

	db = client['discord']
	collection: Collection[Mapping[str, Any]] = db['voice_sessions']

	try:
		sessions = collection.find({})
		return list(sessions)
	except Exception as e:
		print(f'Error retrieving voice sessions: {e}')
		return None


def send_to_db(collection_name: str, data: Mapping[str, Any]) -> None:
	"""
	Generic function to send data to a specified MongoDB collection.
	"""
	client = _connect()
	if not client:
		print('Failed to connect to MongoDB')
		return

	db = client['discord']
	collection: Collection[Mapping[str, Any]] = db[collection_name]

	try:
		collection.insert_one(data)
		print(f'Data sent successfully to {collection_name} collection')
	except Exception as e:
		print(f'Error sending data to {collection_name} collection: {e}')


def edit_db_entry(collection_name: str, query: Mapping[str, Any], update_data: Mapping[str, Any]) -> None:
	"""
	Generic function to edit an entry in a specified MongoDB collection.
	"""
	client = _connect()
	if not client:
		print('Failed to connect to MongoDB')
		return

	db = client['discord']
	collection: Collection[Mapping[str, Any]] = db[collection_name]

	try:
		result = collection.update_one(query, {'$set': update_data})
		if result.modified_count > 0:
			print(f'Entry updated successfully in {collection_name} collection')
		else:
			print(f'No entry matched the query in {collection_name} collection')
	except Exception as e:
		print(f'Error updating entry in {collection_name} collection: {e}')


def del_db_entry(collection_name: str, query: Mapping[str, Any]) -> None:
	"""
	Generic function to delete an entry from a specified MongoDB collection.
	"""
	client = _connect()
	if not client:
		print('Failed to connect to MongoDB')
		return
	
	db = client['discord']
	collection: Collection[Mapping[str, Any]] = db[collection_name]
	
	try:
		result: DeleteResult = collection.delete_one(query)
		if result.deleted_count > 0:
			print(f'Entry deleted successfully from {collection_name} collection')
		else:
			print(f'No entry matched the query in {collection_name} collection')
	except Exception as e:
		print(f'Error deleting entry from {collection_name} collection: {e}')


def del_many_db_entries(collection_name: str, query: Mapping[str, Any]) -> int | None:
	"""
	Generic function to delete multiple entries from a specified MongoDB collection.
	"""
	client = _connect()
	if not client:
		print('Failed to connect to MongoDB')
		return None
	
	db = client['discord']
	collection: Collection[Mapping[str, Any]] = db[collection_name]
	
	try:
		result: DeleteResult = collection.delete_many(query)
		print(f'Deleted {result.deleted_count} entries from {collection_name} collection')
		return result.deleted_count
	except Exception as e:
		print(f'Error deleting entries from {collection_name} collection: {e}')


def get_from_db(collection_name: str, query: Mapping[str, Any]) -> None | dict[str, Any]:
	"""
	Generic function to retrieve data from a specified MongoDB collection.
	"""
	client = _connect()
	if not client:
		print('Failed to connect to MongoDB')
		return None

	db = client['discord']
	collection: Collection[Mapping[str, Any]] = db[collection_name]

	try:
		results = collection.find_one(query)
		if results is None:
			return None
		return dict(results)
	except Exception as e:
		print(f'Error retrieving data from {collection_name} collection: {e}')
		return None


def get_many_from_db(collection_name: str, query: Mapping[str, Any], sort_by, direction: str, limit: int = 0) -> list[dict[str, Any]] | None:
	"""
	Generic function to retrieve multiple documents from a specified MongoDB collection.

	direction should be either "a" for ascending or "d" for descending.
	"""
	if direction not in ['a', 'd']:
		print('Invalid sort direction. Use "a" for ascending or "d" for descending.')
		return None
	client = _connect()
	if not client:
		print('Failed to connect to MongoDB')
		return None

	db = client['discord']
	collection: Collection[Mapping[str, Any]] = db[collection_name]
	if direction.lower() == 'a':
		direction = pymongo.ASCENDING
	else:
		direction = pymongo.DESCENDING

	try:
		if limit > 0:
			results = collection.find(query).sort(sort_by, direction).limit(limit)
		else:
			results = collection.find(query).sort(sort_by, direction)

		return [dict(result) for result in results]
	except Exception as e:
		print(f'Error retrieving data from {collection_name} collection: {e}')
		return None
