import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)


class MongoConnection:
    """MongoDB connection singleton"""

    def __init__(self):
        mongo_user = os.getenv("MONGO_USER")
        mongo_password = os.getenv("MONGO_PASSWORD")
        mongo_host = os.getenv("MONGO_HOST", "localhost")
        mongo_port = os.getenv("MONGO_PORT", "27017")
        mongo_db = os.getenv("MONGO_DB", "keyfairy")

        # Build the MongoDB URI
        self.mongo_uri = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/{mongo_db}"
        self.mongo_db_name = mongo_db
        self.client: AsyncIOMotorClient | None = None
        self.db = None

    def connect(self):
        if self.client is None:
            try:
                self.client = AsyncIOMotorClient(self.mongo_uri)
                self.db = self.client[self.mongo_db_name]
                logger.info(
                    "MongoDB connection established",
                    extra={"db_name": self.mongo_db_name, "uri": self.mongo_uri},
                )
            except Exception as e:
                logger.exception("Error connecting to MongoDB")
                raise RuntimeError(f"Failed to connect to MongoDB: {str(e)}")
        return self.db
    
    async def verify_connection(self):
        if not self.client:
            raise RuntimeError("MongoDB client not initialized. Call connect() first.")
        
        try:
            await self.client.admin.command('ping')
            logger.info(f"✅ MongoDB connection verified: {self.mongo_db_name}")
        except Exception as e:
            logger.error(f"❌ MongoDB connection verification failed: {e}")
            raise

    async def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed", extra={"db_name": self.mongo_db_name})


# Global instance
mongo_connection = MongoConnection()
