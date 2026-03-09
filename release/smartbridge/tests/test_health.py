"""
Unit tests for health check endpoints.

Tests the backend health check functionality to ensure the API
is responsive and returns expected status codes.

Run with:
    pytest tests/test_health.py
    pytest tests/test_health.py -v
    pytest tests/test_health.py --cov=backend
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

# Create test client
client = TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check_returns_200(self):
        """
        Test basic health check returns HTTP 200.
        
        Verifies that GET /health endpoint is responsive and
        indicates the application is running.
        """
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_json(self):
        """
        Test health check returns valid JSON response.
        
        Verifies the response can be parsed as JSON and contains
        expected "status" field.
        """
        response = client.get("/health")
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data

    def test_health_check_status_value(self):
        """
        Test health check returns correct status value.
        
        Verifies that the status field contains "ok" indicating
        healthy state.
        """
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "ok"

    def test_health_check_response_structure(self):
        """
        Test health check response has expected structure.
        
        Validates the response format consistency.
        """
        response = client.get("/health")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_detailed_health_check_returns_200(self):
        """
        Test detailed health check endpoint returns HTTP 200.
        """
        response = client.get("/health/detailed")
        assert response.status_code == 200

    def test_detailed_health_check_has_database_status(self):
        """
        Test detailed health check includes database status.
        """
        response = client.get("/health/detailed")
        data = response.json()
        assert "database" in data

    def test_readiness_check_returns_200(self):
        """
        Test readiness probe returns HTTP 200 (Kubernetes).
        """
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_liveness_check_returns_200(self):
        """
        Test liveness probe returns HTTP 200 (Kubernetes).
        """
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    def test_root_endpoint(self):
        """
        Test root endpoint returns API information.
        """
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AI Financial Advisor API"
        assert "version" in data

    def test_version_endpoint(self):
        """
        Test version endpoint returns version information.
        """
        response = client.get("/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "environment" in data


class TestHealthPerformance:
    """Performance and reliability tests."""

    def test_health_check_response_time(self):
        """
        Test health check completes within acceptable time.
        
        Health checks should be fast for load balancers.
        """
        import time

        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0, f"Health check took {elapsed}s (should be < 1s)"

    def test_multiple_concurrent_health_checks(self):
        """
        Test multiple health checks work correctly.
        
        Simulates load balancer checking health multiple times.
        """
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"


class TestAPIMetadata:
    """Tests for API metadata endpoints."""

    def test_openapi_schema_available(self):
        """
        Test OpenAPI schema is available.
        
        Verifies Swagger/OpenAPI documentation is accessible.
        """
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert response.json()["info"]["title"] == "AI Financial Advisor API"

    def test_swagger_ui_available(self):
        """
        Test Swagger UI is accessible.
        """
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger-ui" in response.text

    def test_redoc_available(self):
        """
        Test ReDoc documentation is available.
        """
        response = client.get("/redoc")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
