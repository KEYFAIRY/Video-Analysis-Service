import logging
from typing import List
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.domain.entities.postural_error import PosturalError
from app.domain.repositories.i_mysql_repo import IMySQLRepo
from app.infrastructure.database.models.postural_error_model import PosturalErrorModel
from app.infrastructure.database.mysql_connection import db_connection
from app.core.exceptions import DatabaseConnectionException

logger = logging.getLogger(__name__)

class MySQLPosturalErrorRepository(IMySQLRepo):
    """Concrete implementation of IMySQLRepo using MySQL."""

    async def list_by_practice_id(self, id_practice: int) -> List[PosturalError]:
        async with db_connection.get_async_session() as session:
            try:
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

    async def create(self, postural_error: PosturalError) -> PosturalError:
        async with db_connection.get_async_session() as session:
            try:
                model = PosturalErrorModel(
                    min_sec=postural_error.min_sec,
                    explication=postural_error.explication,
                    id_practice=postural_error.id_practice
                )
                session.add(model)
                await session.commit()
                await session.refresh(model)

                logger.info(f"Postural error created with id={model.id} for practice_id={postural_error.id_practice}")
                return self._model_to_entity(model)

            except IntegrityError as e:
                await session.rollback()
                logger.error(
                    f"Integrity error creating postural error for practice_id={postural_error.id_practice}: {e}",
                    exc_info=True
                )
                raise DatabaseConnectionException(f"Integrity error: {str(e)}")

            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(
                    f"MySQL error creating postural error for practice_id={postural_error.id_practice}: {e}",
                    exc_info=True
                )
                raise DatabaseConnectionException(f"Error creating postural error: {str(e)}")

    def _model_to_entity(self, model: PosturalErrorModel) -> PosturalError:
        return PosturalError(
            id=model.id,
            min_sec=model.min_sec,
            explication=model.explication,
            id_practice=model.id_practice
        )
