from pydantic import BaseModel
from pydantic.generics import GenericModel
from typing import Optional, TypeVar, Generic

from app.shared.enums import ResponseCode

# Definimos un tipo genérico T
T = TypeVar("T")

class StandardResponse(GenericModel, Generic[T]):
    """Standard schema for all API responses"""
    code: str
    message: str
    data: Optional[T] = None  # ahora data puede ser de cualquier tipo

    @classmethod
    def success(cls, data: T = None, message: str = "Success", code: str = ResponseCode.SUCCESS):
        return cls(code=code, message=message, data=data)
    
    @classmethod
    def validation_error(cls, message: str = "Validation error"):
        return cls(code=ResponseCode.BAD_REQUEST, message=message, data=None)

    @classmethod
    def not_found(cls, message: str = "Resource not found"):
        return cls(code=ResponseCode.NOT_FOUND, message=message, data=None)

    @classmethod
    def unauthorized(cls, message: str = "Unauthorized"):
        return cls(code=ResponseCode.UNAUTHORIZED, message=message, data=None)

    @classmethod
    def internal_error(cls, message: str = "Internal server error"):
        return cls(code=ResponseCode.INTERNAL_SERVER_ERROR, message=message, data=None)
