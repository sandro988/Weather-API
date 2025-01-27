from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Loads and manages application settings from environment variables.

    This class is responsible for loading configuration related to the
    OpenWeatherMap API, AWS credentials, and caching behavior,
    allowing the application to easily interact with these services.

    The settings are read from a .env file by default.
    """

    # OpenWeatherMap Configuration
    OPENWEATHER_API_KEY: str
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/3.0/weather"

    # AWS Configuration
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = "weather-data-bucket"
    DYNAMODB_TABLE: str = "weather-logs"

    # Cache configuration
    CACHE_EXPIRY_MINUTES: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra fields in the environment file that are not defined here
    )


# Initialize the settings instance
settings = Settings()
