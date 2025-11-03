"""
Tests for API health endpoints
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns service info"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert "status" in data
    assert data["status"] == "running"


def test_simple_health_check():
    """Test simple health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_detailed_health_check():
    """Test detailed health check with CLI status"""
    response = client.get("/api/v1/health")
    assert response.status_code in [200, 503]  # May fail if CLI not installed
    data = response.json()
    assert "status" in data
    assert "cline_available" in data
    assert "qwen_available" in data


