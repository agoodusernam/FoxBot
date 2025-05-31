import os

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

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


async def send_message(message, attachment=False):
	client = _connect()
	if not client:
		print("Failed to connect to MongoDB")
		return

	db = client["discord"]
	if not attachment:
		collection = db["messages"]

		try:
			collection.insert_one(message)
			print("Message saved successfully")
		except Exception as e:
			print(f"Error saving message: {e}")


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