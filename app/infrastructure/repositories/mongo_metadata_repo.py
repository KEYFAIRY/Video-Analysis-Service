import logging
from app.domain.repositories.i_metadata_repo import IMetadataRepo
from app.infrastructure.database.mongo_connection import mongo_connection

logger = logging.getLogger(__name__)

class MongoMetadataRepo(IMetadataRepo):
    """Concrete implementation of IMetadataRepo using MongoDB."""

    def __init__(self):
        try:
            self.db = mongo_connection.connect()
            self.users_collection = self.db["users"]
            logger.info("MongoRepo initialized successfully")
        except Exception as e:
            logger.exception("Error initializing MongoRepo")
            raise

    async def mark_practice_video_done(self, uid: str, id_practice: int) -> bool:
        try:
            result = await self.users_collection.update_one(
                {"uid": uid, "practices.id_practice": id_practice},
                {"$set": {"practices.$.video_done": True}}
            )
            if result.modified_count == 1:
                logger.info(
                    "Updated video_done for uid=%s, practice=%s", uid, id_practice
                )
                return True

            logger.warning(
                "No document updated for uid=%s, practice=%s", uid, id_practice
            )
            return False

        except Exception as e:
            logger.exception(
                "Error updating video_done for uid=%s, practice=%s",
                uid,
                id_practice,
            )
            raise
