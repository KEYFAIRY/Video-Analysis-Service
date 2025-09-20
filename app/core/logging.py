import logging
import sys
from app.core.config import settings

def configure_logging():
    """Configures logging for the application."""

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format=settings.LOG_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logging.getLogger("kafka").setLevel(logging.INFO)
