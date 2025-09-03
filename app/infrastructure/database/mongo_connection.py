import os
from motor.motor_asyncio import AsyncIOMotorClient
import logging

logger = logging.getLogger(__name__)


class MongoConnection:
    """MongoDB connection singleton"""

    def __init__(self):
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.mongo_db_name = os.getenv("MONGO_DB", "keyfairy")
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

    async def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed", extra={"db_name": self.mongo_db_name})


# Global instance
mongo_connection = MongoConnection()
