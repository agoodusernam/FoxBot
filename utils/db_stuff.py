import logging
import os
from typing import Any, Mapping, Literal

import cachetools.func  # type: ignore[import-untyped]
import discord
import pymongo
from gridfs import GridFS
from pymongo.mongo_client import MongoClient
from pymongo.results import DeleteResult
from pymongo.server_api import ServerApi
# Purely for type hinting
from pymongo.synchronous.collection import Collection
from pymongo.synchronous.database import Database

logger = logging.getLogger('discord')

# Global client instance
_mongo_client: MongoClient | None = None
_DB_connect_enabled: bool = False

def disable_connection() -> None:
    global _DB_connect_enabled
    _DB_connect_enabled = False

def enable_connection() -> None:
    global _DB_connect_enabled
    _DB_connect_enabled = True


def _connect() -> MongoClient | None:
    """
    Establishes a connection to the MongoDB database using the URI from environment variables.
    :return: MongoClient instance if successful, None otherwise.
    """
    if _DB_connect_enabled:
        logger.warning("Attempted to connect to MongoDB, but connection has been disabled.")
        return None
    
    global _mongo_client
    
    if _mongo_client is not None:
        return _mongo_client
    
    uri = os.getenv('MONGO_URI')
    
    client: MongoClient = MongoClient(uri, server_api=ServerApi('1'), serverSelectionTimeoutMS=5000, tls=True,
                         tlsCertificateKeyFile="mongo_cert.pem")
    try:
        client.admin.command('ping')
        _mongo_client = client  # Store the connection
        logger.info('MongoDB connection established successfully')
        return client
    except ConnectionError:
        logger.error('Connection error while connecting to MongoDB')
        return None
    except Exception as e:
        logger.error(f"An error occurred while connecting to MongoDB: {e}")
        return None


def disconnect():
    """
    Closes the MongoDB connection if it exists.
    :return: None
    """
    global _mongo_client
    if _mongo_client is not None:
        try:
            _mongo_client.close()
            logger.info('MongoDB connection closed')
        except Exception as e:
            logger.error(f'Error closing MongoDB connection: {e}')
        finally:
            _mongo_client = None


def send_message(message: Mapping[str, Any]) -> bool:
    """
    Saves a single message to MongoDB.
    :param message: A dictionary representing the message to be saved.
    :return: None
    """
    client = _connect()
    if not client:
        return False
    
    db = client['discord']
    collection: Collection[Mapping[str, Any]] = db['messages']
    
    try:
        collection.insert_one(message)
        logger.info('Message saved successfully')
        return True
    except Exception as e:
        logger.error(f'Error saving message: {e}')
        return False


def bulk_send_messages(messages: list[dict[str, Any]]) -> None:
    """
    Saves multiple messages to MongoDB in bulk.
    :param messages: A list of dictionaries, each representing a message.
    :return: None
    """
    client = _connect()
    if not client:
        return
    
    db: Database[Mapping[str, Any]] = client['discord']
    collection: Collection[Mapping[str, Any]] = db['messages']
    
    try:
        collection.insert_many(messages)
        logger.info(f'{len(messages)} messages saved successfully')
    except Exception as e:
        logger.error(f'Error saving messages: {e}')


async def send_attachment(message: discord.Message, attachment: discord.Attachment) -> None:
    """
    Saves an attachment to MongoDB using GridFS.
    :param message: discord.Message object containing the message metadata.
    :param attachment: discord.Attachment object containing the attachment data.
    :return: None
    """
    client = _connect()
    if not client:
        return None
    
    db = client['discord']
    fs = GridFS(db, 'attachments')
    
    try:
        # Download the attachment data
        attachment_bytes = await attachment.read()
        
        # Store metadata
        metadata = {
            'message_id':         str(message.id),
            'author_id':          str(message.author.id),
            'content_type':       attachment.content_type,
            'timestamp':          message.created_at.timestamp()
        }
        
        # Store file in GridFS
        fs.put(
                attachment_bytes,
                filename=attachment.filename,
                metadata=metadata
        )
        logger.info(f'Attachment saved successfully: {attachment.filename}')
        return None
    except Exception as e:
        logger.error(f'Error saving attachment: {e}')
        return None


@cachetools.func.ttl_cache(maxsize=2, ttl=300)
def cached_download_all() -> list[dict[str, Any]] | None:
    """
    Retrieves all messages from the MongoDB database.
    :return: A list of dictionaries containing message data, or None if an error occurs.
    """
    return _download_all()


def _download_all() -> list[dict[str, Any]] | None:
    client = _connect()
    if not client:
        return None
    
    logger.info('Downloading all messages from MongoDB...')
    
    db = client['discord']
    collection = db['messages']
    
    try:
        messages = collection.find({})
        return list(messages)
    
    except Exception as e:
        logger.error(f'Error retrieving messages: {e}')
        return None


def delete_message(ObjId: str) -> None:
    """
    Deletes a message from the MongoDB database by its ObjectId.
    :param ObjId: The ObjectId of the message to delete.
    :return: None
    """
    client = _connect()
    if not client:
        return
    
    db = client['discord']
    collection = db['messages']
    try:
        result = collection.delete_one({'_id': ObjId})
        if result.deleted_count > 0:
            logger.info('Message deleted successfully')
        else:
            logger.warning('No message found with the given ID')
    except Exception as e:
        logger.error(f'Error deleting message: {e}')


def del_channel_from_db(channel: discord.TextChannel) -> None:
    """
    Deletes all messages from a specific channel in the MongoDB database.
    :param channel: A discord.TextChannel object representing the channel to delete messages from.
    :return: None
    """
    client = _connect()
    if not client:
        return
    
    db = client['discord']
    collection = db['messages']
    
    try:
        result: DeleteResult = collection.delete_many({'channel_id': channel.id})
        logger.info(f'Deleted {result.deleted_count} messages from channel {channel.id}')
    except Exception as e:
        logger.error(f'Error deleting messages from channel {channel.id}: {e}')


def send_voice_session(session_data: Mapping[str, Any]) -> None:
    """
    Saves a voice session to the MongoDB database.
    :param session_data: A dictionary containing the voice session data.
    :return: None
    """
    client = _connect()
    if not client:
        return
    
    db = client['discord']
    collection: Collection[Mapping[str, Any]] = db['voice_sessions']
    
    try:
        collection.insert_one(session_data)
        logger.info(f'Voice session for {session_data["user_name"]} saved successfully')
    except Exception as e:
        logger.error(f'Error saving voice session: {e}')


@cachetools.func.ttl_cache(maxsize=1, ttl=300)
def cached_download_voice_sessions() -> list[Mapping[str, str]] | None:
    return _download_voice_sessions()


def _download_voice_sessions() -> list[Mapping[str, str]] | None:
    client = _connect()
    if not client:
        return None
    
    db = client['discord']
    collection: Collection[Mapping[str, Any]] = db['voice_sessions']
    
    try:
        sessions = collection.find({})
        return list(sessions)
    except Exception as e:
        logger.error(f'Error retrieving voice sessions: {e}')
        return None


def send_to_db(collection_name: str, data: Mapping[str, Any]) -> None:
    """
    Generic function to send data to a specified MongoDB collection.
    """
    client = _connect()
    if not client:
        return
    
    db = client['discord']
    collection: Collection[Mapping[str, Any]] = db[collection_name]
    
    try:
        collection.insert_one(data)
        logger.info(f'Data sent successfully to {collection_name} collection')
    except Exception as e:
        logger.error(f'Error sending data to {collection_name} collection: {e}')


def edit_db_entry(collection_name: str, query: Mapping[str, Any], update_data: Mapping[str, Any]) -> bool:
    """
    Generic function to edit an entry in a specified MongoDB collection.
    """
    client = _connect()
    if not client:
        return False
    
    db = client['discord']
    collection: Collection[Mapping[str, Any]] = db[collection_name]
    
    try:
        result = collection.update_one(query, {'$set': update_data})
        if result.modified_count > 0:
            return True
        else:
            logger.warning(f'No entry matched the query in {collection_name} collection')
            return False
    except Exception as e:
        logger.error(f'Error updating entry in {collection_name} collection: {e}')
        return False


def del_db_entry(collection_name: str, query: Mapping[str, Any]) -> bool:
    """
    Generic function to delete an entry from a specified MongoDB collection.
    """
    client = _connect()
    if not client:
        return False
    
    db = client['discord']
    collection: Collection[Mapping[str, Any]] = db[collection_name]
    
    try:
        result: DeleteResult = collection.delete_one(query)
        if result.deleted_count > 0:
            logger.info(f'Entry deleted successfully from {collection_name} collection')
            return True
        else:
            logger.warning(f'No entry matched the query in {collection_name} collection')
            return False
    except Exception as e:
        logger.error(f'Error deleting entry from {collection_name} collection: {e}')
        return False


def del_many_db_entries(collection_name: str, query: Mapping[str, Any]) -> int | None:
    """
    Generic function to delete multiple entries from a specified MongoDB collection.
    """
    client = _connect()
    if not client:
        return None
    
    db = client['discord']
    collection: Collection[Mapping[str, Any]] = db[collection_name]
    
    try:
        result: DeleteResult = collection.delete_many(query)
        logger.info(f'Deleted {result.deleted_count} entries from {collection_name} collection')
        return result.deleted_count
    except Exception as e:
        logger.error(f'Error deleting entries from {collection_name} collection: {e}')
        return None


def get_from_db(collection_name: str, query: Mapping[str, Any]) -> None | dict[str, Any]:
    """
    Generic function to retrieve data from a specified MongoDB collection.
    """
    client = _connect()
    if not client:
        return None
    
    db = client['discord']
    collection: Collection[Mapping[str, Any]] = db[collection_name]
    
    try:
        results = collection.find_one(query)
        if results is None:
            return None
        return dict(results)
    except Exception as e:
        logger.error(f'Error retrieving data from {collection_name} collection: {e}')
        return None


def get_many_from_db(collection_name: str, query: Mapping[str, Any], sort_by=None, direction: Literal["a", "b"] = "a", limit: int = 0) -> list[dict[str, Any]] | None:
    """
    Generic function to retrieve multiple documents from a specified MongoDB collection.

    Direction should be either "a" for ascending or "d" for descending.
    """
    if direction not in ['a', 'd']:
        raise ValueError("Direction must be either 'a' for ascending or 'd' for descending.")
    
    client = _connect()
    if not client:
        return None
    
    db = client['discord']
    collection: Collection[Mapping[str, Any]] = db[collection_name]
    if direction.lower() == 'a':
        mongo_direction = pymongo.ASCENDING
    else:
        mongo_direction = pymongo.DESCENDING
        
    if sort_by is None:
        results = collection.find(query)
        return [dict(result) for result in results]
    try:
        if limit > 0:
            results = collection.find(query).sort(sort_by, mongo_direction).limit(limit)
        else:
            results = collection.find(query).sort(sort_by, mongo_direction)
        
        return [dict(result) for result in results]
    except Exception as e:
        logger.error(f'Error retrieving data from {collection_name} collection: {e}')
        return None
