from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """Configuración del Video Worker Service"""

    # App
    APP_NAME: str = "video-worker-service"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = Field(default="development")
    DEBUG: bool = False

    # Servidor FastAPI
    HOST: str = "0.0.0.0"
    RELOAD: bool = False
    VIDEO_ANALYSIS_SERVICE_PORT: int

    # Kafka
    KAFKA_BROKER: str
    KAFKA_INPUT_TOPIC: str
    KAFKA_OUTPUT_TOPIC: str
    KAFKA_AUTO_OFFSET_RESET: str = "earliest"
    KAFKA_GROUP_ID: str

    # MySQL
    MYSQL_HOST: str
    MYSQL_PORT: int
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DB: str

    @property
    def ASYNC_MYSQL_URL(self) -> str:
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        )

    @property
    def SYNC_MYSQL_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        )

    # MongoDB
    MONGO_HOST: str
    MONGO_PORT: int
    MONGO_USER: str
    MONGO_PASSWORD: str
    MONGO_DB: str

    @property
    def MONGO_URI(self) -> str:
        return (
            f"mongodb://{self.MONGO_USER}:{self.MONGO_PASSWORD}"
            f"@{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_DB}"
        )

    # Storage
    HOST_VIDEO_PATH: str
    CONTAINER_VIDEO_PATH: str

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

    def configure(self):
        self.DEBUG = self.APP_ENV == "development"
        self.RELOAD = self.DEBUG
        self.LOG_LEVEL = "DEBUG" if self.DEBUG else self.LOG_LEVEL


settings = Settings()
settings.configure()
