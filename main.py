import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from src.config.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""

    logger.info("FastAPI application starting up")
    yield
    logger.info("FastAPI application shutting down")


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all incoming requests and their processing time"""

    start_time = time.time()

    response = await call_next(request)

    # Calculate request processing time
    process_time = (time.time() - start_time) * 1000
    logger.info(
        f"Method: {request.method} Path: {request.url.path} "
        f"Status: {response.status_code} Duration: {process_time:.2f}ms"
    )

    return response


@app.get("/")
def read_root():
    logger.info("Processing root endpoint request")
    return {"message": "Hello, World!"}
