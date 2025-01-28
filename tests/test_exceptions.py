from datetime import datetime
from http import HTTPStatus
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from src.middlewares.exception_handlers import weather_fetch_error_handler
from src.utils.exceptions import WeatherFetchError

client = TestClient(app)


@pytest.fixture(scope="module")
def test_client():
    """Fixture providing a test client for the FastAPI application."""

    return TestClient(app)


class TestWeatherFetchError:
    """
    Test suite for WeatherFetchError exception class.
    Verifies exception instantiation and attribute handling.
    """

    def test_init_with_default_values(self):
        """Test exception initialization with default values."""

        error = WeatherFetchError(message="Test error")

        assert error.message == "Test error"
        assert error.status_code == HTTPStatus.SERVICE_UNAVAILABLE
        assert error.original_error is None
        assert str(error) == "Test error"

    def test_init_with_custom_status_code(self):
        """Test exception initialization with custom status code."""

        error = WeatherFetchError(message="Not found", status_code=HTTPStatus.NOT_FOUND)

        assert error.message == "Not found"
        assert error.status_code == HTTPStatus.NOT_FOUND
        assert error.original_error is None

    def test_init_with_original_error(self):
        """Test exception initialization with original error."""

        original_error = ValueError("Original error")
        error = WeatherFetchError(
            message="Service error", original_error=original_error
        )

        assert error.message == "Service error"
        assert error.status_code == HTTPStatus.SERVICE_UNAVAILABLE
        assert error.original_error == original_error

    @pytest.mark.parametrize(
        "message,status_code,original_error",
        [
            (
                "Network error",
                HTTPStatus.BAD_GATEWAY,
                ConnectionError("Failed to connect"),
            ),
            ("Invalid data", HTTPStatus.BAD_REQUEST, ValueError("Invalid input")),
            ("Not authorized", HTTPStatus.UNAUTHORIZED, None),
        ],
    )
    def test_init_parametrized(self, message, status_code, original_error):
        """Test exception initialization with various parameter combinations."""

        error = WeatherFetchError(
            message=message, status_code=status_code, original_error=original_error
        )

        assert error.message == message
        assert error.status_code == status_code
        assert error.original_error == original_error


@pytest.mark.asyncio
class TestWeatherFetchErrorHandler:
    """
    Test suite for WeatherFetchError exception handler.
    Verifies error response formatting and handling.
    """

    async def test_handler_basic_error(self):
        """Test basic error handling without original error."""

        request = Mock()
        exc = WeatherFetchError(message="Test error", status_code=HTTPStatus.NOT_FOUND)

        response = await weather_fetch_error_handler(request, exc)

        assert response.status_code == HTTPStatus.NOT_FOUND

        content = response.body.decode()
        assert "Test error" in content
        assert "error" in content
        assert str(HTTPStatus.NOT_FOUND.value) in content

    async def test_handler_with_original_error(self):
        """Test error handling with original error present."""

        request = Mock()
        original_error = ValueError("Original test error")
        exc = WeatherFetchError(
            message="Test error",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            original_error=original_error,
        )

        with patch("src.middlewares.exception_handlers.logger") as mock_logger:
            response = await weather_fetch_error_handler(request, exc)

            # Ensure logger was called for the original error
            mock_logger.error.assert_called_once()
            assert "Original test error" in str(mock_logger.error.call_args)

        assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE

    async def test_response_timestamp_format(self, test_client):
        """Verify timestamp format in error responses."""

        response = test_client.get("/weather?city=NonExistentCity")
        data = response.json()

        assert "error" in data
        assert "status" in data
        assert "status_code" in data
        assert "timestamp" in data
        assert data["status"] == "error"
        assert data["status_code"] == HTTPStatus.NOT_FOUND

        # Verify timestamp is ISO format
        timestamp = data["timestamp"]
        try:
            datetime.fromisoformat(timestamp)
        except ValueError:
            pytest.fail("Timestamp is not in ISO format")
