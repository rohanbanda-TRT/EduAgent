from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "eduagent")

# MongoDB collections
ORGANIZATIONS_COLLECTION = "organizations"
STUDENTS_COLLECTION = "students"
FILES_COLLECTION = "files"
SUGGESTED_QUESTIONS_COLLECTION = "suggested_questions"

class MongoDB:
    client = None
    db = None

    @classmethod
    async def connect_to_mongodb(cls):
        """Connect to MongoDB."""
        try:
            cls.client = AsyncIOMotorClient(MONGO_URI)
            # Verify connection
            await cls.client.admin.command('ping')
            cls.db = cls.client[DB_NAME]
            print(f"Connected to MongoDB: {DB_NAME}")
            return cls.db
        except ConnectionFailure:
            print("Failed to connect to MongoDB")
            return None

    @classmethod
    async def close_mongodb_connection(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            print("MongoDB connection closed")

    @classmethod
    def get_collection(cls, collection_name):
        """Get a specific collection."""
        if cls.db is None:
            raise ConnectionError("Database not connected")
        return cls.db[collection_name]

# Database dependency
async def get_database():
    """Database dependency to be used in FastAPI endpoints."""
    db = MongoDB.db
    if db is None:
        await MongoDB.connect_to_mongodb()
        db = MongoDB.db
    return db
