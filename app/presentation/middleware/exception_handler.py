from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import (
    DatabaseConnectionException,
    PosturalErrorServiceException,
    ValidationException
)
from app.presentation.schemas.common_schema import StandardResponse
import logging

logger = logging.getLogger(__name__)

async def posture_service_exception_handler(request: Request, exc: PosturalErrorServiceException):
    """Handler for generic posture service exceptions"""
    logger.error("%s: %s - Code: %s", exc.__class__.__name__, exc.message, exc.code)
    response = StandardResponse.error(message=exc.message, code=exc.code)
    return JSONResponse(status_code=int(exc.code), content=response.dict())


async def database_connection_exception_handler(request: Request, exc: DatabaseConnectionException):
    """Handler for database connection errors"""
    logger.error("DatabaseConnectionException: %s", exc.message)
    response = StandardResponse.internal_error(exc.message)
    return JSONResponse(status_code=500, content=response.dict())


async def validation_exception_handler(request: Request, exc: ValidationException):
    """Handler for validation errors"""
    logger.warning("ValidationException: %s", exc.message)
    response = StandardResponse.validation_error(exc.message)
    return JSONResponse(status_code=400, content=response.dict())


async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler for FastAPI/Pydantic validation errors"""
    logger.warning("Request validation error: %s", exc.errors())
    error_messages = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_messages.append(f"{field}: {message}")
    formatted_message = "Validation errors: " + "; ".join(error_messages)
    response = StandardResponse.validation_error(formatted_message)
    return JSONResponse(status_code=422, content=response.dict())


async def general_exception_handler(request: Request, exc: Exception):
    """Handler for uncaught exceptions"""
    logger.error("Unhandled exception: %s: %s", type(exc).__name__, str(exc), exc_info=True)
    response = StandardResponse.internal_error("An unexpected error occurred")
    return JSONResponse(status_code=500, content=response.dict())
