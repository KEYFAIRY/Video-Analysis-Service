from contextlib import asynccontextmanager
import logging
import asyncio

from app.core.config import settings
from app.core.logging import configure_logging
from app.infrastructure.database import mongo_connection, mysql_connection
from app.infrastructure.kafka.kafka_consumer import start_kafka_consumer
from app.infrastructure.kafka.kafka_producer import KafkaProducer
from app.infrastructure.monitoring import metrics

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)


async def initialize_databases(retry_delay: int = 5):
    mysql_connected = False
    mongo_connected = False
    attempt = 0
    
    while not (mysql_connected and mongo_connected):
        logger.info(f"Reintentando conexión a BDs (intento {attempt + 1})...")
        await asyncio.sleep(retry_delay)
        
        attempt += 1
        
        # MySQL
        if not mysql_connected:
            try:
                mysql_connection.mysql_connection.init_engine()
                await mysql_connection.mysql_connection.verify_connection()
                mysql_connected = True
            except Exception as e:
                logger.warning(f"⚠️  MySQL connection failed: {e}")
        
        # MongoDB
        if not mongo_connected:
            try:
                mongo_connection.mongo_connection.connect()
                await mongo_connection.mongo_connection.verify_connection()
                mongo_connected = True
            except Exception as e:
                logger.warning(f"⚠️  MongoDB connection failed: {e}")
    
    logger.info("✅ Todas las conexiones de BD establecidas y verificadas")


@asynccontextmanager
async def lifespan():
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.APP_ENV}")

    # ---- Prometheus ----
    logger.info("Starting Prometheus metrics server...")
    metrics.start_metrics_server()
    logger.info("Prometheus metrics server started")

    # ---------- DB Connections ----------
    await initialize_databases(retry_delay=5)

    # ---------- Kafka ----------
    producer = KafkaProducer(bootstrap_servers=settings.KAFKA_BROKER)
    await producer.start()

    loop = asyncio.get_event_loop()
    consumer_task = loop.create_task(start_kafka_consumer(producer))

    yield

    # ---------- Shutdown ----------
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        logger.info("Kafka consumer stopped")

    await producer.stop()
    logger.info("Kafka producer stopped")

    # Close DBs
    await mysql_connection.mysql_connection.close_connections()
    await mongo_connection.mongo_connection.close()
    logger.info("Database connections closed")

async def main():
    async with lifespan():
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service stopped manually (Ctrl+C)")