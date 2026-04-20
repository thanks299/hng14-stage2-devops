"""Unit tests for the API service"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import app after mocking to avoid real Redis connection
with patch('api.main.get_redis_connection'):
    from api.main import app


client = TestClient(app)


def test_health_check():
    """Test health check endpoint when Redis is healthy"""
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True
    
    with patch('api.main.get_redis_connection', return_value=mock_redis):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


def test_health_check_redis_failure():
    """Test health check when Redis is down"""
    with patch('api.main.get_redis_connection', side_effect=Exception("Connection failed")):
        response = client.get("/health")
        assert response.status_code == 503


def test_create_job():
    """Test job creation endpoint"""
    mock_redis = MagicMock()
    mock_redis.lpush.return_value = 1
    mock_redis.hset.return_value = 1
    
    with patch('api.main.get_redis_connection', return_value=mock_redis):
        response = client.post("/jobs")
        assert response.status_code == 200
        assert "job_id" in response.json()


def test_get_job_not_found():
    """Test getting non-existent job"""
    mock_redis = MagicMock()
    mock_redis.hget.return_value = None
    
    with patch('api.main.get_redis_connection', return_value=mock_redis):
        response = client.get("/jobs/nonexistent-id")
        assert response.status_code == 404


def test_get_job_found():
    """Test getting existing job"""
    mock_redis = MagicMock()
    mock_redis.hget.return_value = "queued"
    
    with patch('api.main.get_redis_connection', return_value=mock_redis):
        response = client.get("/jobs/123")
        assert response.status_code == 200
        assert response.json()["status"] == "queued"
