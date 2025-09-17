import logging
from typing import List
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.domain.entities.postural_error import PosturalError
from app.domain.repositories.i_mysql_repo import IMySQLRepo
from app.infrastructure.database.models.postural_error_model import PosturalErrorModel
from app.infrastructure.database.mysql_connection import mysql_connection
from app.core.exceptions import DatabaseConnectionException

logger = logging.getLogger(__name__)

class MySQLPosturalErrorRepository(IMySQLRepo):
    """Concrete implementation of IMySQLRepo using MySQL."""

    async def list_by_practice_id(self, id_practice: int) -> List[PosturalError]:
        session = None
        try:
            session = mysql_connection.get_async_session()
            result = await session.execute(
                select(PosturalErrorModel).where(PosturalErrorModel.id_practice == id_practice)
            )
            rows = result.scalars().all()
            logger.debug(f"Fetched {len(rows)} postural errors for practice_id={id_practice}")
            return [self._model_to_entity(row) for row in rows]
        except SQLAlchemyError as e:
            logger.error(
                f"MySQL error listing postural errors for practice_id={id_practice}: {e}",
                exc_info=True
            )
            raise DatabaseConnectionException(f"Error fetching postural errors: {str(e)}")
        finally:
            if session:
                await session.close()
            

    async def create(self, postural_error: PosturalError) -> PosturalError:
        session = None
        try:
            session = mysql_connection.get_async_session()
            model = PosturalErrorModel(
                min_sec_init=postural_error.min_sec_init,
                min_sec_end=postural_error.min_sec_end,
                explication=postural_error.explication,
                id_practice=postural_error.id_practice
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)

            logger.info(f"Postural error created with id={model.id} for practice_id={postural_error.id_practice}")
            return self._model_to_entity(model)

        except IntegrityError as e:
            if session:
                await session.rollback()
            logger.error(
                f"Integrity error creating postural error for practice_id={postural_error.id_practice}: {e}",
                exc_info=True
            )
            raise DatabaseConnectionException(f"Integrity error: {str(e)}")

        except SQLAlchemyError as e:
            if session:
                await session.rollback()
            logger.error(
                f"MySQL error creating postural error for practice_id={postural_error.id_practice}: {e}",
                exc_info=True
            )
            raise DatabaseConnectionException(f"Error creating postural error: {str(e)}")
        
        except Exception as e:
            if session:
                await session.rollback()
            logger.error(
                f"Unexpected error creating postural error for practice_id={postural_error.id_practice}: {e}",
                exc_info=True
            )
            raise DatabaseConnectionException(f"Unexpected error: {str(e)}")
        
        finally:
            if session:
                await session.close()

    def _model_to_entity(self, model: PosturalErrorModel) -> PosturalError:
        return PosturalError(
            id=model.id,
            min_sec_init=model.min_sec_init,
            min_sec_end=model.min_sec_end,
            explication=model.explication,
            id_practice=model.id_practice
        )
