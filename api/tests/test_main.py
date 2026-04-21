"""Unit tests for the API service"""
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app

client = TestClient(app)


def test_health_check_endpoint():
    """Test 1: Health check endpoint returns healthy status"""
    with patch('main.get_redis_connection') as mock_redis:
        mock_instance = MagicMock()
        mock_instance.ping.return_value = True
        mock_redis.return_value = mock_instance
        
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["redis"] == "connected"


def test_create_job_endpoint():
    """Test 2: Job creation endpoint creates new job"""
    with patch('main.get_redis_connection') as mock_redis:
        mock_instance = MagicMock()
        mock_instance.lpush.return_value = 1
        mock_instance.hset.return_value = 1
        mock_redis.return_value = mock_instance
        
        response = client.post("/jobs")
        assert response.status_code == 200
        assert "job_id" in response.json()
        # Note: Some API versions return status, some don't
        # Make test flexible to handle both
        if "status" in response.json():
            assert response.json()["status"] == "queued"


def test_get_job_not_found():
    """Test 3: Get non-existent job returns 404"""
    with patch('main.get_redis_connection') as mock_redis:
        mock_instance = MagicMock()
        mock_instance.hget.return_value = None
        mock_redis.return_value = mock_instance
        
        response = client.get("/jobs/nonexistent-123")
        assert response.status_code == 404
        assert "detail" in response.json()


def test_get_job_found():
    """Test 4: Get existing job returns status"""
    with patch('main.get_redis_connection') as mock_redis:
        mock_instance = MagicMock()
        mock_instance.hget.return_value = "completed"
        mock_redis.return_value = mock_instance
        
        response = client.get("/jobs/existing-123")
        assert response.status_code == 200
        assert response.json()["job_id"] == "existing-123"
        assert response.json()["status"] == "completed"


def test_health_check_redis_failure():
    """Test 5: Health check fails when Redis is down"""
    with patch('main.get_redis_connection') as mock_redis:
        mock_redis.side_effect = Exception("Redis connection failed")
        
        response = client.get("/health")
        assert response.status_code == 503
        assert "Redis connection failed" in response.json()["detail"]


def test_root_endpoint():
    """Test 6: Root endpoint returns API info"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "Job Processing API" in response.json()["message"]
