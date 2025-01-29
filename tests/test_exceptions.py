from http import HTTPStatus

import pytest

from src.utils.exceptions import (
    CacheError,
    StorageConnectionError,
    StorageDataError,
    StorageError,
    StoragePermissionError,
    WeatherFetchError,
)


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


class TestStorageError:
    """
    Test suite for base StorageError exception class.
    Verifies exception instantiation and attribute handling.
    """

    def test_init_with_default_values(self):
        """Test exception initialization with default values."""

        error = StorageError(message="Test error")

        assert error.message == "Test error"
        assert error.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert error.original_error is None
        assert str(error) == "Test error"

    def test_init_with_custom_status_code(self):
        """Test exception initialization with custom status code."""

        error = StorageError(message="Bad request", status_code=HTTPStatus.BAD_REQUEST)

        assert error.message == "Bad request"
        assert error.status_code == HTTPStatus.BAD_REQUEST
        assert error.original_error is None

    def test_init_with_original_error(self):
        """Test exception initialization with original error."""

        original_error = ValueError("Original error")
        error = StorageError(message="Storage error", original_error=original_error)

        assert error.message == "Storage error"
        assert error.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert error.original_error == original_error

    @pytest.mark.parametrize(
        "message,status_code,original_error",
        [
            (
                "Connection failed",
                HTTPStatus.SERVICE_UNAVAILABLE,
                ConnectionError("No connection"),
            ),
            ("Invalid format", HTTPStatus.BAD_REQUEST, ValueError("Bad format")),
            ("Permission denied", HTTPStatus.FORBIDDEN, None),
        ],
    )
    def test_init_parametrized(self, message, status_code, original_error):
        """Test exception initialization with various parameter combinations."""

        error = StorageError(
            message=message, status_code=status_code, original_error=original_error
        )

        assert error.message == message
        assert error.status_code == status_code
        assert error.original_error == original_error


class TestStorageConnectionError:
    """
    Test suite for StorageConnectionError exception class.
    Verifies exception instantiation and attribute handling.
    """

    def test_init_with_default_values(self):
        """Test exception initialization with default values."""

        error = StorageConnectionError()

        assert error.message == "Unable to connect to storage service"
        assert error.status_code == HTTPStatus.SERVICE_UNAVAILABLE
        assert error.original_error is None

    def test_init_with_custom_message(self):
        """Test exception initialization with custom message."""

        error = StorageConnectionError(message="Custom connection error")

        assert error.message == "Custom connection error"
        assert error.status_code == HTTPStatus.SERVICE_UNAVAILABLE

    def test_init_with_original_error(self):
        """Test exception initialization with original error."""

        original_error = ConnectionError("Network timeout")
        error = StorageConnectionError(
            message="Connection failed", original_error=original_error
        )

        assert error.message == "Connection failed"
        assert error.original_error == original_error


class TestStorageDataError:
    """
    Test suite for StorageDataError exception class.
    Verifies exception instantiation and attribute handling.
    """

    def test_init_with_default_values(self):
        """Test exception initialization with default values."""

        error = StorageDataError()

        assert error.message == "Invalid data format for storage"
        assert error.status_code == HTTPStatus.BAD_REQUEST
        assert error.original_error is None

    def test_init_with_custom_message(self):
        """Test exception initialization with custom message."""

        error = StorageDataError(message="Invalid JSON format")

        assert error.message == "Invalid JSON format"
        assert error.status_code == HTTPStatus.BAD_REQUEST


class TestStoragePermissionError:
    """
    Test suite for StoragePermissionError exception class.
    Verifies exception instantiation and attribute handling.
    """

    def test_init_with_default_values(self):
        """Test exception initialization with default values."""

        error = StoragePermissionError()

        assert error.message == "Permission denied for storage operation"
        assert error.status_code == HTTPStatus.FORBIDDEN
        assert error.original_error is None

    def test_init_with_custom_message(self):
        """Test exception initialization with custom message."""

        error = StoragePermissionError(message="No write access")

        assert error.message == "No write access"
        assert error.status_code == HTTPStatus.FORBIDDEN


class TestCacheError:
    """
    Test suite for CacheError exception class.
    Verifies exception instantiation and attribute handling.
    """

    def test_init_with_default_values(self):
        """Test exception initialization with default values."""

        error = CacheError()

        assert error.message == "Cache operation failed"
        assert error.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert error.original_error is None

    def test_init_with_custom_message(self):
        """Test exception initialization with custom message."""

        error = CacheError(message="Cache miss")

        assert error.message == "Cache miss"
        assert error.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
