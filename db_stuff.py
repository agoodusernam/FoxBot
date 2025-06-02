import os
import discord
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from gridfs import GridFS
from bson.objectid import ObjectId

# Global client instance
_mongo_client: MongoClient | None = None

load_dotenv()

def _connect():
	global _mongo_client
	# Return existing connection if available
	if _mongo_client is not None:
		return _mongo_client

	uri = os.getenv("MONGO_URI")

	client = MongoClient(uri, server_api = ServerApi('1'))
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


async def send_message(message) -> None:
	client = _connect()
	if not client:
		print("Failed to connect to MongoDB")
		return

	db = client["discord"]
	collection = db["messages"]

	try:
		collection.insert_one(message)
		print("Message saved successfully")
	except Exception as e:
		print(f"Error saving message: {e}")


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

		# Store metadata for easy querying
		metadata = {
			"message_id": str(message.id),
			"author_global_name": message.author.global_name,
			"content_type": attachment.content_type,
			"timestamp": message.created_at.isoformat()
		}

		# Store file in GridFS
		file_id = fs.put(
			attachment_bytes,
			filename=attachment.filename,
			metadata=metadata
		)
		print(f"Attachment saved successfully with ID: {file_id}")
		return None
	except Exception as e:
		print(f"Error saving attachment: {e}")
		return None


def get_attachment(file_id):
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
			"content_type": grid_out.metadata.get("content_type"),
			"data":         grid_out.read(),
			"metadata":     grid_out.metadata
		}
	except Exception as e:
		print(f"Error retrieving attachment: {e}")
		return None

def list_message_attachments(message_id):
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
				"file_id": str(file._id),
				"filename": file.filename,
				"content_type": file.metadata.get("content_type"),
				"timestamp": file.metadata.get("timestamp")
			}
			for file in files
		]
	except Exception as e:
		print(f"Error listing attachments: {e}")
		return []


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


def download_all_attachments() -> list[dict] | None:
	"""
	Downloads all attachments from GridFS to data/attachments folder.
	Returns a list of dictionaries with information about the downloaded files.
	"""
	client = _connect()
	if not client:
		print("Failed to connect to MongoDB")
		return None

	db = client["discord"]
	fs = GridFS(db)

	# Create attachments directory if it doesn't exist
	attachments_dir = os.path.join("data", "attachments")
	os.makedirs(attachments_dir, exist_ok = True)

	downloaded_files = []
	try:
		# Get all file IDs from GridFS
		all_file_ids = [file._id for file in fs.find()]

		for file_id in all_file_ids:
			# Get the file with fresh cursor
			grid_out = fs.get(file_id)

			# Extract metadata
			message_id = grid_out.metadata.get("message_id", "unknown")
			original_filename = grid_out.filename

			# Ensure filename is safe for filesystem
			safe_filename = "".join(c for c in original_filename if c.isalnum() or c in "._- ")
			if not safe_filename:
				safe_filename = "unknown_file"

			# Create unique filename with message_id prefix
			unique_filename = f"{message_id}_{safe_filename}"
			file_path = os.path.join(attachments_dir, unique_filename)

			# Save file to disk
			with open(file_path, "wb") as f:
				f.write(grid_out.read())

			# Add to list of downloaded files
			downloaded_files.append({
				"file_id":           str(file_id),
				"original_filename": original_filename,
				"saved_path":        file_path,
				"content_type":      grid_out.metadata.get("content_type"),
				"message_id":        message_id,
				"author":            grid_out.metadata.get("author_global_name"),
				"timestamp":         grid_out.metadata.get("timestamp")
			})

			print(f"Downloaded {original_filename} to {file_path}")

		print(f"Downloaded {len(downloaded_files)} attachment(s)")
		return downloaded_files

	except Exception as e:
		print(f"Error downloading attachments: {e}")
		return None

def delete_message(ObjId: str):
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