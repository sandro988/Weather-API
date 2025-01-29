import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import aiobotocore.session
from botocore.exceptions import (
    ClientError,
    CredentialRetrievalError,
    NoCredentialsError,
)

from src.config.logger import logger
from src.config.settings import settings
from src.utils.exceptions import (
    CacheError,
    StorageConnectionError,
    StorageDataError,
    StorageError,
    StoragePermissionError,
)


class StorageService:
    """Service for handling weather data storage operations in S3."""

    @staticmethod
    def _generate_storage_key(city: str) -> str:
        """Generate a standardized storage key for weather data files."""

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            normalized_city = city.lower().replace(" ", "_")
            return f"{normalized_city}_{timestamp}.json"
        except Exception as e:
            logger.error(f"Error generating storage key: {str(e)}")
            raise StorageDataError(
                message="Failed to generate storage key", original_error=e
            )

    @classmethod
    async def _create_s3_client(cls) -> aiobotocore.client.AioBaseClient:
        """Create an authenticated S3 client session."""

        try:
            session = aiobotocore.session.get_session()
            return await session.create_client(
                "s3",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            ).__aenter__()

        except (NoCredentialsError, CredentialRetrievalError) as e:
            logger.error(f"AWS credentials error: {str(e)}")
            raise StoragePermissionError(
                message="Invalid AWS credentials", original_error=e
            )

        except Exception as e:
            logger.error(f"Failed to create S3 client: {str(e)}")
            raise StorageConnectionError(
                message="Failed to connect to storage service", original_error=e
            )

    @classmethod
    async def upload_json_to_storage(
        cls, city: str, weather_data: dict
    ) -> Tuple[str, str]:
        """Asynchronously upload weather data to S3."""

        storage_key = cls._generate_storage_key(city)

        try:
            logger.info(f"Uploading weather data for {city} to S3")
            client = await cls._create_s3_client()

            try:
                json_data = json.dumps(weather_data, indent=2)

                # Attempt to upload to S3
                await client.put_object(
                    Bucket=settings.S3_BUCKET,
                    Key=storage_key,
                    Body=json_data.encode("utf-8"),
                    ContentType="application/json",
                    Metadata={
                        "city": city.lower(),
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                s3_uri = f"s3://{settings.S3_BUCKET}/{storage_key}"
                logger.info(f"Successfully uploaded weather data to {s3_uri}")
                return storage_key, s3_uri

            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code in ("NoSuchBucket", "AccessDenied"):
                    raise StoragePermissionError(
                        message=f"S3 access error: {error_code}", original_error=e
                    )
                raise StorageError(
                    message=f"S3 operation failed: {error_code}", original_error=e
                )

            finally:
                await client.close()

        except json.JSONEncodeError as e:
            logger.error(f"JSON encoding error: {str(e)}")
            raise StorageDataError(
                message="Failed to encode weather data", original_error=e
            )

    @classmethod
    async def get_recent_weather_data(
        cls, city: str, max_age_minutes: int = settings.CACHE_EXPIRY_MINUTES
    ) -> Optional[dict]:
        """Retrieve recent weather data for a city from S3 if available."""

        if not city or not isinstance(city, str):
            raise StorageDataError(message="City name must be a non-empty string")

        try:
            logger.info(f"Checking S3 for recent weather data for {city}")
            client = await cls._create_s3_client()

            try:
                normalized_city = city.lower().replace(" ", "_")
                min_timestamp = datetime.now(timezone.utc) - timedelta(
                    minutes=max_age_minutes
                )

                try:
                    response = await client.list_objects_v2(
                        Bucket=settings.S3_BUCKET, Prefix=f"{normalized_city}_"
                    )
                except ClientError as e:
                    error_code = e.response["Error"]["Code"]
                    if error_code == "NoSuchBucket":
                        raise StoragePermissionError(
                            message="S3 bucket not found", original_error=e
                        )
                    raise

                if "Contents" not in response:
                    logger.debug(f"No cached data found for {city}")
                    return None

                # Sort files by most recent
                recent_files = sorted(
                    response["Contents"], key=lambda x: x["LastModified"], reverse=True
                )

                for file in recent_files:
                    if file["LastModified"] >= min_timestamp:
                        try:
                            obj = await client.get_object(
                                Bucket=settings.S3_BUCKET, Key=file["Key"]
                            )
                            body = await obj["Body"].read()
                            weather_data = json.loads(body.decode("utf-8"))

                            logger.info(
                                f"Successfully retrieved cached weather data for {city}"
                            )
                            return weather_data
                        except ClientError as e:
                            raise CacheError(
                                message="Failed to retrieve cached data",
                                original_error=e,
                            )
                        except json.JSONDecodeError as e:
                            raise CacheError(
                                message="Cached data is corrupted", original_error=e
                            )

                logger.debug(f"No recent cached data found for {city}")
                return None

            finally:
                await client.close()

        except Exception as e:
            if not isinstance(e, (StorageError, CacheError)):
                logger.error(f"Unexpected error retrieving cached data: {str(e)}")
                raise StorageError(
                    message="Failed to retrieve cached weather data", original_error=e
                )
            raise
