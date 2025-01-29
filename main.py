import time
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Query, Request

from src.config.logger import logger
from src.config.settings import settings
from src.middlewares.exception_handlers import (
    cache_error_handler,
    dynamodb_connection_error_handler,
    dynamodb_data_error_handler,
    dynamodb_error_handler,
    dynamodb_permission_error_handler,
    storage_connection_error_handler,
    storage_data_error_handler,
    storage_error_handler,
    storage_permission_error_handler,
    weather_fetch_error_handler,
)
from src.services.dynamodb_service import DynamoDBService
from src.services.storage_service import StorageService
from src.services.weather_service import WeatherService
from src.utils.exceptions import (
    CacheError,
    DynamoDBConnectionError,
    DynamoDBDataError,
    DynamoDBError,
    DynamoDBPermissionError,
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
app.add_exception_handler(DynamoDBError, dynamodb_error_handler)
app.add_exception_handler(DynamoDBConnectionError, dynamodb_connection_error_handler)
app.add_exception_handler(DynamoDBDataError, dynamodb_data_error_handler)
app.add_exception_handler(DynamoDBPermissionError, dynamodb_permission_error_handler)


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
    Features:
    • Retrieves cached weather data if available
    • Falls back to fresh weather data if cache misses
    • Stores successful responses in S3 for caching
    • Logs all operations to DynamoDB for tracking

    Args:
        city: Name of the city (letters, spaces, and accented characters only)

    Returns:
        dict: Weather data including temperature, humidity, wind speed, and description

    Raises:
        StoragePermissionError: If there are permission issues with the storage service
        WeatherFetchError: If weather data cannot be retrieved
        DynamoDBError: If there are issues logging to DynamoDB
    """

    logger.info(f"Processing weather request for city: {city}")

    try:
        try:
            cached_data = await StorageService.get_recent_weather_data(city)
            if cached_data:
                logger.info(f"Returning cached weather data for {city}")

                # Log cached data retrieval to DynamoDB
                try:
                    cached_storage_key = f"{city.lower().replace(' ', '_')}_cached"
                    cached_uri = f"s3://{settings.S3_BUCKET}/{cached_storage_key}"
                    await DynamoDBService.log_weather_event(
                        city=city, storage_path=cached_uri, weather_data=cached_data
                    )
                except DynamoDBError as db_err:
                    logger.error(
                        f"Failed to log cached data retrieval to DynamoDB for {city}: {str(db_err)}"
                    )

                return cached_data
        except CacheError as e:
            logger.warning(f"Cache retrieval failed for {city}: {str(e)}")

        # Fetch new weather data
        weather_data = await WeatherService.fetch_weather_data(city)

        # Store in S3
        try:
            storage_key, s3_uri = await StorageService.upload_json_to_storage(
                city=city, weather_data=weather_data
            )

            # Log successful weather data retrieval and storage to DynamoDB
            try:
                await DynamoDBService.log_weather_event(
                    city=city, storage_path=s3_uri, weather_data=weather_data
                )
            except DynamoDBError as db_err:
                logger.error(
                    f"Failed to log weather event to DynamoDB for {city}: {str(db_err)}"
                )

        except StorageError as e:
            logger.error(f"Failed to store weather data for {city}: {str(e)}")
            # Still attempt to log to DynamoDB even if storage fails
            try:
                await DynamoDBService.log_weather_event(
                    city=city, storage_path="storage_failed", weather_data=weather_data
                )
            except DynamoDBError as db_err:
                logger.error(
                    f"Failed to log storage failure to DynamoDB for {city}: {str(db_err)}"
                )

        return weather_data

    except StoragePermissionError as e:
        logger.error(f"Storage permission error for {city}: {str(e)}")
        raise
    except WeatherFetchError as e:
        logger.error(f"Weather fetch error for {city}: {str(e)}")
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error processing weather request for {city}: {str(e)}"
        )
        raise
