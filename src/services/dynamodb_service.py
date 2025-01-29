import json
import uuid
from datetime import datetime
from typing import Optional

import aiobotocore.session
from botocore.exceptions import ClientError

from src.config.logger import logger
from src.config.settings import settings
from src.utils.exceptions import (
    DynamoDBConnectionError,
    DynamoDBDataError,
    DynamoDBError,
    DynamoDBPermissionError,
)


class DynamoDBService:
    """Service for logging weather data operations in DynamoDB."""

    @classmethod
    async def _create_dynamodb_client(cls) -> aiobotocore.client.AioBaseClient:
        """Create an authenticated DynamoDB client session."""

        try:
            session = aiobotocore.session.get_session()
            return await session.create_client(
                "dynamodb",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            ).__aenter__()

        except Exception as e:
            logger.error(f"Failed to create DynamoDB client: {str(e)}")
            raise DynamoDBConnectionError(original_error=e)

    @classmethod
    async def log_weather_event(
        cls, city: str, storage_path: str, weather_data: dict
    ) -> Optional[str]:
        """
        Log weather data retrieval event to DynamoDB.

        Args:
            city: Name of the city
            storage_path: S3 storage path where weather data is stored
            weather_data: Weather data dictionary

        Returns:
            str: Event ID of the logged entry

        Raises:
            DynamoDBConnectionError: If connection to DynamoDB fails
            DynamoDBDataError: If data validation fails
            DynamoDBPermissionError: If permissions are insufficient
            DynamoDBError: For other DynamoDB-related errors
        """

        try:
            event_id = str(uuid.uuid4())
            client = await cls._create_dynamodb_client()

            try:
                log_item = {
                    "EventId": {"S": event_id},
                    "Timestamp": {"S": datetime.now().isoformat()},
                    "CityName": {"S": city},
                    "StoragePath": {"S": storage_path},
                    "Temperature": {
                        "N": str(weather_data.get("main", {}).get("temp", 0))
                    },
                    "WeatherCondition": {
                        "S": weather_data.get("weather", [{}])[0].get(
                            "description", "Unknown"
                        )
                    },
                    "FullMetadata": {"S": json.dumps(weather_data)},
                }

                await client.put_item(TableName=settings.DYNAMODB_TABLE, Item=log_item)

                logger.info(f"Successfully logged weather event for {city}")
                return event_id

            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code in ("ResourceNotFoundException", "AccessDeniedException"):
                    raise DynamoDBPermissionError(original_error=e)
                raise DynamoDBError(
                    message=f"DynamoDB operation failed: {error_code}", original_error=e
                )

            finally:
                await client.close()

        except json.JSONEncodeError as e:
            raise DynamoDBDataError(
                message="Failed to encode weather data for logging", original_error=e
            )
        except Exception as e:
            if not isinstance(e, DynamoDBError):
                logger.error(f"Unexpected error in DynamoDB service: {str(e)}")
                raise DynamoDBError(
                    message="Failed to log weather event", original_error=e
                )
            raise
