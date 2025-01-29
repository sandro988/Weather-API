# Weather API Service

FastAPI-based weather service with AWS integration for data caching and storage.

## Prerequisites

- Docker and Docker Compose (for Docker setup)
- Python 3.11+ (for local setup)
- AWS Account with S3 and DynamoDB access

## Quick Start with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd weather-api-service
```

2. Configure environment variables in `.env`:
```env
# OpenWeatherMap Configuration
OPENWEATHER_API_KEY="api-key"
OPENWEATHER_BASE_URL="https://api.openweathermap.org/data/3.0/weather"

# AWS Configuration
AWS_ACCESS_KEY_ID="aws-access-key"
AWS_SECRET_ACCESS_KEY="aws-secret-access-key"
S3_BUCKET="aws-s3-bucket-name"
DYNAMODB_TABLE="aws-dynamodb-table-name"
AWS_REGION="aws-region"
```

3. Run with Docker:
```bash
docker-compose up --build
```

## Run Without Docker

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure `.env` file as shown above

4. Run the application:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoint

```http
GET /weather?city={city_name}
```

## Project Structure
```
├── main.py                 # FastAPI application
├── src/
│   ├── config/            # Configuration and logger
│   ├── middlewares/       # Exception handlers
│   ├── services/          # Core services
│   └── utils/             # Utilities and exceptions
├── requirements.txt
├── Dockerfile
└── docker-compose.yaml
```

## Features

- Async weather data fetching
- AWS S3 for data storage
- AWS DynamoDB for event logging
- 5-minute data caching
- Docker deployment support
