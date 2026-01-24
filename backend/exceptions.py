"""
Centralized exception handling for FastAPI application.
Provides consistent error responses and logging.
"""
import logging
import traceback
from typing import Any, Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import httpx

from backend.schemas import ErrorResponse

logger = logging.getLogger(__name__)

class VishwaGuruException(Exception):
    """Base exception for VishwaGuru application"""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationException(VishwaGuruException):
    """Exception for validation errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )

class NotFoundException(VishwaGuruException):
    """Exception for resource not found"""

    def __init__(self, resource: str, resource_id: Any = None):
        message = f"{resource} not found"
        if resource_id:
            message += f" with ID: {resource_id}"
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "resource_id": resource_id}
        )

class ServiceUnavailableException(VishwaGuruException):
    """Exception for service unavailability"""

    def __init__(self, service: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"{service} service is temporarily unavailable",
            error_code="SERVICE_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details or {"service": service}
        )

class FileUploadException(VishwaGuruException):
    """Exception for file upload errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="FILE_UPLOAD_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )

async def vishwaguru_exception_handler(request: Request, exc: VishwaGuruException) -> JSONResponse:
    """Handle VishwaGuru custom exceptions"""
    logger.error(
        f"VishwaGuruException: {exc.message} (code: {exc.error_code})",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.message,
            error_code=exc.error_code,
            details=exc.details
        ).model_dump(mode='json')
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    logger.warning(
        f"HTTPException: {exc.detail} (status: {exc.status_code})",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            error_code=f"HTTP_{exc.status_code}",
            details={"status_code": exc.status_code}
        ).model_dump(mode='json')
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    logger.warning(
        f"ValidationError: {exc.errors()}",
        extra={
            "errors": exc.errors(),
            "path": request.url.path,
            "method": request.method
        }
    )

    # Extract field-specific errors
    field_errors = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        if field:
            field_errors[field] = error.get("msg", "Invalid value")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="Request validation failed",
            error_code="VALIDATION_ERROR",
            details={
                "field_errors": field_errors,
                "validation_errors": exc.errors()
            }
        ).model_dump(mode='json')
    )

async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic ValidationError (different from RequestValidationError)"""
    logger.warning(
        f"Pydantic ValidationError: {exc.errors()}",
        extra={
            "errors": exc.errors(),
            "path": request.url.path,
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="Data validation failed",
            error_code="VALIDATION_ERROR",
            details={"validation_errors": exc.errors()}
        ).model_dump(mode='json')
    )

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database errors"""
    logger.error(
        f"SQLAlchemyError: {str(exc)}",
        exc_info=True,
        extra={
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method
        }
    )

    # Handle specific SQLAlchemy errors
    if isinstance(exc, IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                error="Database constraint violation",
                error_code="DATABASE_CONSTRAINT_ERROR",
                details={"constraint_error": str(exc)}
            ).model_dump(mode='json')
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Database operation failed",
            error_code="DATABASE_ERROR",
            details={"db_error": str(exc)}
        ).model_dump(mode='json')
    )

async def httpx_exception_handler(request: Request, exc: httpx.HTTPError) -> JSONResponse:
    """Handle HTTP client errors (external API calls)"""
    logger.error(
        f"HTTPError: {str(exc)}",
        exc_info=True,
        extra={
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content=ErrorResponse(
            error="External service communication failed",
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"http_error": str(exc)}
        ).model_dump(mode='json')
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle any unhandled exceptions"""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="An unexpected error occurred",
            error_code="INTERNAL_SERVER_ERROR",
            details={"exception_type": type(exc).__name__}
        ).model_dump(mode='json')
    )

# Exception handlers mapping for easy registration
EXCEPTION_HANDLERS = {
    VishwaGuruException: vishwaguru_exception_handler,
    HTTPException: http_exception_handler,
    RequestValidationError: validation_exception_handler,
    ValidationError: pydantic_validation_exception_handler,
    SQLAlchemyError: sqlalchemy_exception_handler,
    httpx.HTTPError: httpx_exception_handler,
    Exception: generic_exception_handler,
}