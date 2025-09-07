import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """MySQL async connection manager using SQLAlchemy"""

    def __init__(self):
        self.mysql_host = os.getenv("MYSQL_HOST", "localhost")
        self.mysql_port = os.getenv("MYSQL_PORT", "3306")
        self.mysql_user = os.getenv("MYSQL_USER", "root")
        self.mysql_password = os.getenv("MYSQL_PASSWORD", "")
        self.mysql_db = os.getenv("MYSQL_DB", "music_db")

        self.async_database_url = (
            f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}"
        )

        self.async_engine = None
        self.async_session_factory: async_sessionmaker[AsyncSession] | None = None

    def init_engine(self):
        """Initializes the async database engine and session factory if not already done."""
        if not self.async_engine:
            try:
                self.async_engine = create_async_engine(
                    self.async_database_url,
                    echo=False,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                )
                self.async_session_factory = async_sessionmaker(
                    self.async_engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                )
                logger.info("Async database engine created successfully")
            except Exception as e:
                logger.error("Error creating async database engine", exc_info=True)
                raise RuntimeError(f"Failed to create database connection: {e}")

    def get_async_session(self) -> AsyncSession:
        """Gets a new async session."""
        if not self.async_session_factory:
            self.init_engine()
        return self.async_session_factory()

    async def close_connections(self):
        """Closes the database engine connections."""
        if self.async_engine:
            await self.async_engine.dispose()
            logger.info("Database connections closed")


# Global instance
mysql_connection = DatabaseConnection()
