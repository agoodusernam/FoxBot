import os
from typing import Any, Mapping

import discord
from pymongo.mongo_client import MongoClient
from pymongo.results import DeleteResult
from pymongo.server_api import ServerApi
from gridfs import GridFS
from bson.objectid import ObjectId

# Purely for type hinting
from pymongo.synchronous.collection import Collection
from pymongo.synchronous.database import Database


from dotenv import load_dotenv


# Global client instance
_mongo_client: MongoClient | None = None

load_dotenv()


def _connect():
	global _mongo_client
	# Return the existing connection if available
	if _mongo_client is not None:
		return _mongo_client

	uri = os.getenv("MONGO_URI")

	client = MongoClient(uri, server_api=ServerApi('1'))
	try:
		client.admin.command('ping')
		_mongo_client = client  # Store the connection
		return client
	except ConnectionError:
		print("Failed to connect to MongoDB")
		return False
	except Exception as e:
		print(e)
		return False


def send_message(message: Mapping[str, Any]) -> None:
	client = _connect()
	if not client:
		print("Failed to connect to MongoDB")
		return

	db = client["discord"]
	collection: Collection[Mapping[str, Any]] = db["messages"]

	try:
		collection.insert_one(message)
		print("Message saved successfully")
	except Exception as e:
		print(f"Error saving message: {e}")


def bulk_send_messages(messages: list[Mapping[str, Any]]) -> None:
	client = _connect()
	if not client:
		print("Failed to connect to MongoDB")
		return

	db: Database[Mapping[str, Any]] = client["discord"]
	collection: Collection[Mapping[str, Any]] = db["messages"]

	try:
		collection.insert_many(messages)
		print(f"{len(messages)} messages saved successfully")
	except Exception as e:
		print(f"Error saving messages: {e}")


async def send_attachment(message: discord.Message, attachment: discord.Attachment) -> None:
	client = _connect()
	if not client:
		print("Failed to connect to MongoDB")
		return None

	db = client["discord"]
	fs = GridFS(db, "attachments")  # Create GridFS instance

	try:
		# Download the attachment data
		attachment_bytes = await attachment.read()

		# Store metadata
		metadata = {
			"message_id":         str(message.id),
			"author_global_name": message.author.global_name,
			"content_type":       attachment.content_type,
			"timestamp":          message.created_at.isoformat()
		}

		# Store file in GridFS
		file_id = fs.put(
				attachment_bytes,
				filename=attachment.filename,
				metadata=metadata
		)
		print(f"Attachment saved successfully: {attachment.filename}")
		return None
	except Exception as e:
		print(f"Error saving attachment: {e}")
		return None


def get_attachment(file_id: str | ObjectId) -> dict | None:
	client = _connect()
	if not client:
		print("Failed to connect to MongoDB")
		return None

	db = client["discord"]
	fs = GridFS(db)

	try:
		# Convert string ID to ObjectId if needed
		if isinstance(file_id, str):
			file_id = ObjectId(file_id)

		if not fs.exists(file_id):
			print(f"No file found with ID {file_id}")
			return None

		grid_out = fs.get(file_id)
		return {
			"filename":     grid_out.filename,
			"content_type": grid_out.metadata.get("content_type"),  # type: ignore
			"data":         grid_out.read(),
			"metadata":     grid_out.metadata
		}
	except Exception as e:
		print(f"Error retrieving attachment: {e}")
		return None


def list_message_attachments(message_id: str | int) -> list[dict[str, str | Any]] | None:
	client = _connect()
	if not client:
		print("Failed to connect to MongoDB")
		return []

	db = client["discord"]
	fs = GridFS(db)

	try:
		# Find all files with matching message_id in metadata
		files = fs.find({"metadata.message_id": str(message_id)})
		return [
			{
				"file_id":      str(file._id),
				"filename":     file.filename,
				"content_type": file.metadata.get("content_type"),
				"timestamp":    file.metadata.get("timestamp")
			}
			for file in files
		]
	except Exception as e:
		print(f"Error listing attachments: {e}")
		return None


def download_all() -> list[dict[str, str]] | None:
	client = _connect()
	if not client:
		raise ConnectionError("Failed to connect to MongoDB")

	db = client["discord"]
	collection = db["messages"]

	try:
		messages = collection.find({})
		return list(messages)

	except Exception as e:
		print(f"Error retrieving messages: {e}")
		return None


def delete_message(ObjId: str) -> None:
	client = _connect()
	if not client:
		print("Failed to connect to MongoDB")
		return

	db = client["discord"]
	collection = db["messages"]
	try:
		result = collection.delete_one({"_id": ObjId})
		if result.deleted_count > 0:
			print("Message deleted successfully")
		else:
			print("No message found with the given ID")
	except Exception as e:
		print(f"Error deleting message: {e}")


def del_channel_from_db(channel: discord.TextChannel) -> None:
	client = _connect()
	if not client:
		print("Failed to connect to MongoDB")
		return

	db = client["discord"]
	collection = db["messages"]

	try:
		result: DeleteResult = collection.delete_many({"channel": channel.name})
		print(f"Deleted {result.deleted_count} messages from channel {channel.name}")
	except Exception as e:
		print(f"Error deleting messages from channel {channel.name}: {e}")
