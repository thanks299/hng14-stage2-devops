"""Repository-level smoke tests for API endpoints with mocked Redis."""
from unittest.mock import MagicMock, patch
import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))
from main import app  # noqa: E402


client = TestClient(app)


def test_root_endpoint_returns_metadata():
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "Job Processing API"


def test_health_endpoint_with_mocked_redis():
    with patch("main.get_redis_connection") as mock_get_redis:
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_get_redis.return_value = mock_client

        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


def test_get_job_uses_mocked_redis_and_returns_status():
    with patch("main.get_redis_connection") as mock_get_redis:
        mock_client = MagicMock()
        mock_client.hget.return_value = "completed"
        mock_get_redis.return_value = mock_client

        response = client.get("/jobs/job-123")
        assert response.status_code == 200
        body = response.json()
        assert body["job_id"] == "job-123"
        assert body["status"] == "completed"
