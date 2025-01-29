from typing import Optional


class WeatherFetchError(Exception):
    """Exception raised for errors in the weather fetching process."""

    def __init__(
        self,
        message: str,
        status_code: int = 503,
        original_error: Optional[Exception] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.original_error = original_error
        super().__init__(self.message)


class StorageError(Exception):
    """Base exception for storage-related errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        original_error: Optional[Exception] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.original_error = original_error
        super().__init__(self.message)


class StorageConnectionError(StorageError):
    """Exception raised when unable to connect to storage service."""

    def __init__(
        self,
        message: str = "Unable to connect to storage service",
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=message, status_code=503, original_error=original_error
        )


class StorageDataError(StorageError):
    """Exception raised for issues with data format or validation."""

    def __init__(
        self,
        message: str = "Invalid data format for storage",
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=message, status_code=400, original_error=original_error
        )


class StoragePermissionError(StorageError):
    """Exception raised for permission-related issues with storage service."""

    def __init__(
        self,
        message: str = "Permission denied for storage operation",
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=message, status_code=403, original_error=original_error
        )


class CacheError(StorageError):
    """Exception raised for cache-related issues."""

    def __init__(
        self,
        message: str = "Cache operation failed",
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=message, status_code=500, original_error=original_error
        )


class DynamoDBError(Exception):
    """Base exception for DynamoDB-related errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        original_error: Optional[Exception] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.original_error = original_error
        super().__init__(self.message)


class DynamoDBConnectionError(DynamoDBError):
    """Exception raised when unable to connect to DynamoDB."""

    def __init__(
        self,
        message: str = "Unable to connect to DynamoDB",
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=message, status_code=503, original_error=original_error
        )


class DynamoDBDataError(DynamoDBError):
    """Exception raised for issues with data format or validation."""

    def __init__(
        self,
        message: str = "Invalid data format for DynamoDB",
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=message, status_code=400, original_error=original_error
        )


class DynamoDBPermissionError(DynamoDBError):
    """Exception raised for permission-related issues with DynamoDB."""

    def __init__(
        self,
        message: str = "Permission denied for DynamoDB operation",
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=message, status_code=403, original_error=original_error
        )
