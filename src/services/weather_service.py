from datetime import datetime
from typing import Any, Dict

import httpx

from src.config.logger import logger
from src.config.settings import settings
from src.utils.exceptions import WeatherFetchError


class WeatherService:
    @classmethod
    async def fetch_weather_data(cls, city: str) -> Dict[str, Any]:
        """
        Fetches weather data for a given city using OpenWeather API.

        Args:
            city (str): Name of the city to fetch weather data for.

        Returns:
            Dict[str, Any]: Weather data dictionary containing:
                - Current temperature, humidity, wind speed and etc
                - Weather description
                - City information
                - Fetch timestamp

        Raises:
            WeatherFetchError: In cases of:
                - City not found (status_code=404)
                - API service issues (status_code=503)
                - Network errors (status_code=503)
                - Unexpected errors (status_code=500)
        """

        async with httpx.AsyncClient() as client:
            params = {
                "q": city,
                "appid": settings.OPENWEATHER_API_KEY,
                "units": "metric",
            }

            logger.info(f"Fetching weather for {city}")

            try:
                response = await client.get(
                    settings.OPENWEATHER_BASE_URL, params=params
                )

                response_data = response.json()

                # Handle city not found - OpenWeather can return either HTTP 404 or cod:404
                if response.status_code == 404 or (
                    "cod" in response_data and response_data["cod"] == "404"
                ):
                    logger.warning(f"City not found: {city}")
                    raise WeatherFetchError(
                        message=f"City not found: {city}", status_code=404
                    )
                elif response.status_code != 200:
                    logger.error(f"API Error: {response.status_code} - {response.text}")
                    raise WeatherFetchError(
                        message="Weather service temporarily unavailable",
                        status_code=503,
                        original_error=Exception(
                            f"API Error: {response.status_code} - {response.text}"
                        ),
                    )

                # Add timestamp to successful response
                weather_data = response_data
                weather_data["fetch_timestamp"] = datetime.now().isoformat()

                logger.info(f"Successfully fetched weather for {city}")
                return weather_data

            except httpx.RequestError as e:
                # Handle network-level errors (timeouts, connection issues)
                logger.error(f"Network error while fetching weather data: {str(e)}")
                raise WeatherFetchError(
                    message="Unable to connect to weather service",
                    status_code=503,
                    original_error=e,
                )
            except WeatherFetchError:
                raise
            except Exception as e:
                logger.critical(f"Unexpected error in weather service: {str(e)}")
                raise WeatherFetchError(
                    message="Internal weather service error",
                    status_code=500,
                    original_error=e,
                )
