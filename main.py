import time
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Query, Request

from src.config.logger import logger
from src.middlewares.exception_handlers import (
    cache_error_handler,
    storage_connection_error_handler,
    storage_data_error_handler,
    storage_error_handler,
    storage_permission_error_handler,
    weather_fetch_error_handler,
)
from src.services.storage_service import StorageService
from src.services.weather_service import WeatherService
from src.utils.exceptions import (
    CacheError,
    StorageConnectionError,
    StorageDataError,
    StorageError,
    StoragePermissionError,
    WeatherFetchError,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""

    logger.info("FastAPI application starting up")
    yield
    logger.info("FastAPI application shutting down")


app = FastAPI(
    title="Weather API",
    description="API service for retrieving weather information for cities",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_exception_handler(WeatherFetchError, weather_fetch_error_handler)
app.add_exception_handler(StorageError, storage_error_handler)
app.add_exception_handler(StorageConnectionError, storage_connection_error_handler)
app.add_exception_handler(StorageDataError, storage_data_error_handler)
app.add_exception_handler(StoragePermissionError, storage_permission_error_handler)
app.add_exception_handler(CacheError, cache_error_handler)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all incoming requests and their processing time"""

    start_time = time.time()

    response = await call_next(request)

    # Calculate request processing time
    process_time = (time.time() - start_time) * 1000
    logger.info(
        f"Method: {request.method} Path: {request.url.path} "
        f"Status: {response.status_code} Duration: {process_time:.2f}ms"
    )

    return response


@app.get("/")
def read_root():
    logger.info("Processing root endpoint request")
    return {"message": "Hello, World!"}


@app.get("/weather")
async def get_weather(
    city: Annotated[
        str,
        Query(
            min_length=2,
            max_length=50,
            pattern=r"^[A-Za-zÀ-ÿ\s\-]+$",
            description="Name of the city to fetch weather data for (supports accented characters)",
            examples=["London", "New York", "São Paulo", "Tbilisi"],
        ),
    ],
) -> dict:
    """
    Fetch current weather data for a specified city.

    Args:
        city: Name of the city (letters, spaces, and accented characters only)

    Returns:
        dict: Weather data including temperature, humidity, wind speed, and description

    Raises:
        StoragePermissionError: If there are permission issues with the storage service
        WeatherFetchError: If weather data cannot be retrieved
    """

    logger.info(f"Processing weather request for city: {city}")

    try:
        try:
            cached_data = await StorageService.get_recent_weather_data(city)
            if cached_data:
                logger.info(f"Returning cached weather data for {city}")
                return cached_data
        except CacheError as e:
            logger.warning(f"Cache retrieval failed for {city}: {str(e)}")

        weather_data = await WeatherService.fetch_weather_data(city)

        try:
            await StorageService.upload_json_to_storage(city, weather_data)
        except StorageError as e:
            # Log storage error but still return the weather data
            logger.error(f"Failed to store weather data for {city}: {str(e)}")

        return weather_data

    except StoragePermissionError as e:
        logger.error(f"Storage permission error for {city}: {str(e)}")
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error processing weather request for {city}: {str(e)}"
        )
        raise
