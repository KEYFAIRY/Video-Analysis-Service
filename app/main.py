from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio

from app.core.config import settings
from app.core.logging import configure_logging
from app.infrastructure.kafka.kafka_consumer import start_kafka_consumer
from app.infrastructure.kafka.kafka_producer import KafkaProducer
from app.presentation.middleware.exception_handler import (
    database_connection_exception_handler,
    validation_exception_handler,
    request_validation_exception_handler,
    general_exception_handler,
)
from app.core.exceptions import (
    DatabaseConnectionException,
    ValidationException,
)
from fastapi.exceptions import RequestValidationError
from app.presentation.api.v1.postural_error import router as postural_error


# CConfigure logging
configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.APP_ENV}")

    # Inicializar Kafka Producer
    producer = KafkaProducer(bootstrap_servers=settings.KAFKA_BROKER)
    await producer.start()

    # Inicializar Kafka Consumer
    loop = asyncio.get_event_loop()
    consumer_task = loop.create_task(start_kafka_consumer())

    yield

    # Shutdown ordenado
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        logger.info("Kafka consumer stopped")

    await producer.stop()
    logger.info("Kafka producer stopped")



def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers
    app.add_exception_handler(DatabaseConnectionException, database_connection_exception_handler)
    app.add_exception_handler(ValidationException, validation_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
        }
    
    app.include_router(postural_error)

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {settings.HOST}:{settings.VIDEO_ANALYSIS_SERVICE_PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.VIDEO_ANALYSIS_SERVICE_PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
