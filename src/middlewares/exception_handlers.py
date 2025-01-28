from datetime import datetime

from fastapi import Request
from fastapi.responses import JSONResponse

from src.config.logger import logger
from src.utils.exceptions import WeatherFetchError


async def weather_fetch_error_handler(request: Request, exc: WeatherFetchError):
    """Handle WeatherFetchError exception and return standardized error responses.

    Args:
        request (Request): The incoming request object
        exc (WeatherFetchError): The exception to handle

    Returns:
        JSONResponse: Standardized error response with status code, message and timestamp
    """

    error_response = {
        "error": exc.message,
        "status": "error",
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat(),
    }

    # Additional details for internal debugging
    if exc.original_error:
        logger.error(f"Original error details: {str(exc.original_error)}")

    return JSONResponse(status_code=exc.status_code, content=error_response)
