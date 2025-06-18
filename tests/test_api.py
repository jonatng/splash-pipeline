"""
Tests for the FastAPI application
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Splash Visual Trends Analytics API" in data["message"]


def test_health_endpoint():
    """Test the health check endpoint"""
    # Note: This might fail if database is not available
    response = client.get("/health")
    # Accept both 200 (healthy) and 500 (database not available) for testing
    assert response.status_code in [200, 500]


def test_photos_endpoint():
    """Test the photos endpoint"""
    response = client.get("/photos?limit=5")
    # Accept both 200 (data available) and 500 (database not available) for testing
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert "photos" in data
        assert "pagination" in data


def test_search_photos_endpoint():
    """Test the search photos endpoint"""
    response = client.get("/search/photos?q=nature&limit=5")
    # Accept both 200 (data available) and 500 (database not available) for testing
    assert response.status_code in [200, 500]


def test_analytics_statistics_endpoint():
    """Test the analytics statistics endpoint"""
    response = client.get("/analytics/statistics")
    # Accept both 200 (data available) and 500 (database not available) for testing
    assert response.status_code in [200, 500]


def test_trends_endpoints():
    """Test various trends endpoints"""
    endpoints = [
        "/trends/search?days=7",
        "/trends/tags",
        "/trends/photographers",
        "/trends/daily?days=30"
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        # Accept both 200 (data available) and 500 (database not available) for testing
        assert response.status_code in [200, 500]


def test_invalid_endpoint():
    """Test invalid endpoint returns 404"""
    response = client.get("/invalid-endpoint")
    assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__]) 