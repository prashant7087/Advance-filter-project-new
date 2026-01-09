"""
MongoDB Database Connection Module
Handles connection to MongoDB and provides collection accessors.
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB connection
_client = None
_db = None


def get_client():
    """Get or create MongoDB client."""
    global _client
    if _client is None:
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            raise ValueError("MONGODB_URI environment variable is not set")
        _client = MongoClient(mongodb_uri)
    return _client


def get_db():
    """Get database instance."""
    global _db
    if _db is None:
        client = get_client()
        # Use 'advance_filter' as the database name
        _db = client.advance_filter
    return _db


def get_users_collection():
    """Get users collection."""
    db = get_db()
    return db.users


def get_measurements_collection():
    """Get measurements collection."""
    db = get_db()
    return db.measurements


def test_connection():
    """Test the MongoDB connection."""
    try:
        client = get_client()
        # The ping command is cheap and does not require auth
        client.admin.command('ping')
        return True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return False
