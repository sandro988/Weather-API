from datetime import datetime

from fastapi import Request
from fastapi.responses import JSONResponse

from src.config.logger import logger
from src.utils.exceptions import (
    CacheError,
    StorageConnectionError,
    StorageDataError,
    StorageError,
    StoragePermissionError,
    WeatherFetchError,
)


def create_error_response(exc: Exception, include_details: bool = False) -> dict:
    """
    Create a standardized error response dictionary.

    Args:
        exc: The exception that was raised
        include_details: Whether to include additional error details

    Returns:
        Dictionary containing error response data
    """

    response = {
        "error": exc.message,
        "status": "error",
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat(),
    }

    if include_details and hasattr(exc, "original_error"):
        response["details"] = str(exc.original_error)

    return response


async def weather_fetch_error_handler(request: Request, exc: WeatherFetchError):
    """Handle WeatherFetchError exception and return standardized error responses."""

    error_response = create_error_response(exc)

    if exc.original_error:
        logger.error(f"Original error details: {str(exc.original_error)}")

    return JSONResponse(status_code=exc.status_code, content=error_response)


async def storage_error_handler(request: Request, exc: StorageError):
    """
    Handle general storage errors with appropriate logging and response formatting.

    Args:
        request: The incoming request object
        exc: The StorageError exception

    Returns:
        JSONResponse containing error details
    """

    error_response = create_error_response(exc)

    if exc.original_error:
        logger.error(f"Storage error details: {str(exc.original_error)}")

    return JSONResponse(status_code=exc.status_code, content=error_response)


async def storage_connection_error_handler(
    request: Request, exc: StorageConnectionError
):
    """Handle storage connection errors"""

    error_response = create_error_response(exc)
    logger.error(f"Storage connection error: {str(exc.original_error)}")
    return JSONResponse(status_code=exc.status_code, content=error_response)


async def storage_data_error_handler(request: Request, exc: StorageDataError):
    """Handle data validation and format errors for storage operations."""

    error_response = create_error_response(exc)
    logger.warning(f"Storage data error: {str(exc.message)}")
    return JSONResponse(status_code=exc.status_code, content=error_response)


async def storage_permission_error_handler(
    request: Request, exc: StoragePermissionError
):
    """Handle permission-related storage errors."""

    error_response = create_error_response(exc)
    logger.error(f"Storage permission error: {str(exc.message)}")
    return JSONResponse(status_code=exc.status_code, content=error_response)


async def cache_error_handler(request: Request, exc: CacheError):
    """Handle cache-specific errors while maintaining service availability."""

    error_response = create_error_response(exc)
    logger.error(f"Cache error: {str(exc.message)}")
    return JSONResponse(status_code=exc.status_code, content=error_response)
