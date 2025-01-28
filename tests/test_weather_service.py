from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
import pytest_asyncio

from src.config.settings import settings
from src.services.weather_service import WeatherService
from src.utils.exceptions import WeatherFetchError

# Constants for test data
TEST_CITY = "London"
INVALID_CITY = "NonExistentCity"


@pytest.fixture
def sample_weather_data() -> Dict[str, Any]:
    """
    Provides a realistic sample of weather data matching OpenWeather API format.
    Used as a standardized response across tests.
    """

    return {
        "coord": {"lon": -0.1257, "lat": 51.5085},
        "weather": [
            {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}
        ],
        "main": {
            "temp": 15.6,
            "feels_like": 14.8,
            "temp_min": 14.4,
            "temp_max": 16.7,
            "pressure": 1024,
            "humidity": 67,
        },
        "wind": {"speed": 3.09, "deg": 360},
        "sys": {"country": "GB", "sunrise": 1619413821, "sunset": 1619464150},
        "name": TEST_CITY,
        "cod": 200,
    }


@pytest_asyncio.fixture
async def mock_httpx_client():
    """
    Creates a mocked httpx.AsyncClient that properly handles the async context manager pattern.

    This fixture uses AsyncMock to handle async operations and properly mocks the context manager
    behavior of httpx.AsyncClient.
    """

    mock_client = AsyncMock()
    mock_client.get = AsyncMock()

    async def async_enter():
        return mock_client

    async def async_exit(*args):
        pass

    mock_async_client = AsyncMock()
    mock_async_client.__aenter__.return_value = mock_client
    mock_async_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_async_client):
        yield mock_client


class TestWeatherService:
    """
    Test suite for WeatherService class.
    Groups related tests and provides shared setup/teardown if needed.
    """

    @pytest.mark.asyncio
    async def test_successful_weather_fetch(
        self, mock_httpx_client: AsyncMock, sample_weather_data: Dict[str, Any]
    ):
        """
        Verifies successful weather data retrieval and response structure.

        Tests:
        1. Correct API endpoint and parameters
        2. Response processing
        3. Timestamp addition
        4. Data structure integrity
        """

        # Create a mock response that will be returned by mock client
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_weather_data

        mock_httpx_client.get.return_value = mock_response

        result = await WeatherService.fetch_weather_data(TEST_CITY)

        assert mock_httpx_client.get.called
        called_url = mock_httpx_client.get.call_args[0][0]
        called_params = mock_httpx_client.get.call_args[1]["params"]

        assert called_url == settings.OPENWEATHER_BASE_URL
        assert called_params == {
            "q": TEST_CITY,
            "appid": settings.OPENWEATHER_API_KEY,
            "units": "metric",
        }

        assert isinstance(result, dict)
        assert result["name"] == TEST_CITY
        assert "fetch_timestamp" in result
        assert all(key in result for key in ["weather", "main", "wind"])

        # Verify timestamp is of valid ISO format
        try:
            datetime.fromisoformat(result["fetch_timestamp"])
        except ValueError:
            pytest.fail("Timestamp is not in valid ISO format")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "error_scenario",
        [
            (
                "404_status",
                404,
                {"cod": "404", "message": "City not found"},
                404,
                "City not found",
            ),
            (
                "cod_404",
                200,
                {"cod": "404", "message": "City not found"},
                404,
                "City not found",
            ),
            (
                "service_error",
                503,
                {"message": "Service Unavailable"},
                503,
                "Weather service temporarily unavailable",
            ),
        ],
    )
    async def test_error_scenarios(
        self, mock_httpx_client: Mock, error_scenario: tuple
    ):
        """
        Tests various error scenarios using parameterized tests.

        Parameters:
        - scenario_name: Name of the test scenario
        - status_code: HTTP status code to simulate
        - response_data: Mock response data
        - expected_code: Expected error code
        - expected_message: Expected error message
        """

        # Unpack scenario data
        scenario_name, status_code, response_data, expected_code, expected_message = (
            error_scenario
        )

        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = status_code
        mock_response.json.return_value = response_data
        mock_response.text = str(response_data)
        mock_httpx_client.get.return_value = mock_response

        with pytest.raises(WeatherFetchError) as exc_info:
            await WeatherService.fetch_weather_data(INVALID_CITY)

        assert exc_info.value.status_code == expected_code
        assert expected_message in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_network_error(self, mock_httpx_client: Mock):
        """
        Tests handling of network-level errors (timeouts, connection issues).
        Verifies proper error transformation and logging.
        """

        mock_httpx_client.get.side_effect = httpx.RequestError("Connection failed")

        with pytest.raises(WeatherFetchError) as exc_info:
            await WeatherService.fetch_weather_data(TEST_CITY)

        assert exc_info.value.status_code == 503
        assert "Unable to connect to weather service" in str(exc_info.value)
        assert isinstance(exc_info.value.original_error, httpx.RequestError)

    @pytest.mark.asyncio
    async def test_unexpected_error(self, mock_httpx_client: Mock):
        """
        Tests handling of unexpected exceptions.
        Verifies proper error transformation and status code assignment.
        """

        mock_httpx_client.get.side_effect = ValueError("Unexpected internal error")

        with pytest.raises(WeatherFetchError) as exc_info:
            await WeatherService.fetch_weather_data(TEST_CITY)

        assert exc_info.value.status_code == 500
        assert "Internal weather service error" in str(exc_info.value)
        assert isinstance(exc_info.value.original_error, ValueError)
