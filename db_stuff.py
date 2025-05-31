import os

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

# Global client instance
_mongo_client = None

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