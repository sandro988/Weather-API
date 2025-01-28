import time
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Query, Request

from src.config.logger import logger
from src.middlewares.exception_handlers import weather_fetch_error_handler
from src.services.weather_service import WeatherService
from src.utils.exceptions import WeatherFetchError


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
):
    """
    Fetch current weather data for a specified city.

    param:
        city: Name of the city (letters and spaces only (supports accented characters))

    Returns:
        Dict containing weather data including temperature, humidity,
        wind speed, and description
    """

    logger.info(f"Processing weather request for city: {city}")
    weather_data = await WeatherService.fetch_weather_data(city)

    return weather_data
