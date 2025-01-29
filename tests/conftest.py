import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def test_client():
    """Fixture providing a test client for the FastAPI application."""

    return TestClient(app)
