import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    with patch('main.r') as mock_redis:
        mock_redis.ping.return_value = True
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

def test_health_check_redis_failure():
    """Test health check when Redis is down"""
    with patch('main.r') as mock_redis:
        mock_redis.ping.side_effect = Exception("Connection failed")
        response = client.get("/health")
        assert response.status_code == 503

def test_create_job():
    """Test job creation endpoint"""
    with patch('main.r') as mock_redis:
        mock_redis.lpush.return_value = 1
        mock_redis.hset.return_value = 1
        response = client.post("/jobs")
        assert response.status_code == 200
        assert "job_id" in response.json()

def test_get_job_not_found():
    """Test getting non-existent job"""
    with patch('main.r') as mock_redis:
        mock_redis.hget.return_value = None
        response = client.get("/jobs/nonexistent-id")
        assert response.status_code == 404

def test_get_job_found():
    """Test getting existing job"""
    with patch('main.r') as mock_redis:
        mock_redis.hget.return_value = "queued"
        response = client.get("/jobs/123")
        assert response.status_code == 200
        assert response.json()["status"] == "queued"
