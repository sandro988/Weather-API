import json
from datetime import datetime
from http import HTTPStatus
from unittest.mock import Mock, patch

import pytest

from src.middlewares.exception_handlers import (
    cache_error_handler,
    storage_connection_error_handler,
    storage_data_error_handler,
    storage_error_handler,
    storage_permission_error_handler,
    weather_fetch_error_handler,
)
from src.utils.exceptions import (
    CacheError,
    StorageConnectionError,
    StorageDataError,
    StorageError,
    StoragePermissionError,
    WeatherFetchError,
)


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


@pytest.mark.asyncio
class TestStorageErrorHandlers:
    """
    Test suite for all storage-related exception handlers.
    Verifies error response formatting and handling.
    """

    async def test_storage_error_handler(self):
        """Test basic storage error handling."""

        request = Mock()
        exc = StorageError(message="Storage error")

        response = await storage_error_handler(request, exc)

        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        content = response.body.decode()
        assert "Storage error" in content
        assert "error" in content

    async def test_storage_connection_error_handler(self):
        """Test storage connection error handling."""

        request = Mock()
        original_error = ConnectionError("Connection failed")
        exc = StorageConnectionError(original_error=original_error)

        with patch("src.middlewares.exception_handlers.logger") as mock_logger:
            response = await storage_connection_error_handler(request, exc)
            mock_logger.error.assert_called_once()

        assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE

    async def test_storage_data_error_handler(self):
        """Test storage data error handling."""

        request = Mock()
        exc = StorageDataError(message="Invalid data")

        with patch("src.middlewares.exception_handlers.logger") as mock_logger:
            response = await storage_data_error_handler(request, exc)
            mock_logger.warning.assert_called_once()

        assert response.status_code == HTTPStatus.BAD_REQUEST

    async def test_storage_permission_error_handler(self):
        """Test storage permission error handling."""

        request = Mock()
        exc = StoragePermissionError(message="Access denied")

        with patch("src.middlewares.exception_handlers.logger") as mock_logger:
            response = await storage_permission_error_handler(request, exc)
            mock_logger.error.assert_called_once()

        assert response.status_code == HTTPStatus.FORBIDDEN

    async def test_cache_error_handler(self):
        """Test cache error handling."""

        request = Mock()
        exc = CacheError(message="Cache error")

        with patch("src.middlewares.exception_handlers.logger") as mock_logger:
            response = await cache_error_handler(request, exc)
            mock_logger.error.assert_called_once()

        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    async def test_response_format(self, test_client):
        """Test response format for all storage handlers."""

        handlers = [
            (storage_error_handler, StorageError("Test error")),
            (storage_connection_error_handler, StorageConnectionError()),
            (storage_data_error_handler, StorageDataError()),
            (storage_permission_error_handler, StoragePermissionError()),
            (cache_error_handler, CacheError()),
        ]

        for handler, exc in handlers:
            request = Mock()
            response = await handler(request, exc)
            data = json.loads(response.body.decode("utf-8"))

            assert "error" in data
            assert "status" in data
            assert "status_code" in data
            assert "timestamp" in data

            try:
                timestamp = data["timestamp"]
                datetime.fromisoformat(timestamp)
            except ValueError:
                pytest.fail(
                    f"Invalid timestamp format in response from {handler.__name__}"
                )
