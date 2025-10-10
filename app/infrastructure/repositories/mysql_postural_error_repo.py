import logging
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.domain.entities.postural_error import PosturalError
from app.domain.repositories.i_postural_error_repo import IPosturalErrorRepo
from app.infrastructure.database.models.postural_error_model import PosturalErrorModel
from app.infrastructure.database.mysql_connection import mysql_connection
from app.core.exceptions import DatabaseConnectionException

logger = logging.getLogger(__name__)

class MySQLPosturalErrorRepository(IPosturalErrorRepo):
    """Concrete implementation of IPosturalErrorRepo using MySQL."""

    async def create(self, postural_error: PosturalError) -> PosturalError:
        session = None
        try:
            session = mysql_connection.get_async_session()
            model = PosturalErrorModel(
                min_sec_init=postural_error.min_sec_init,
                min_sec_end=postural_error.min_sec_end,
                frame=postural_error.frame,
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
            frame=model.frame,
            explication=model.explication,
            id_practice=model.id_practice
        )
