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
