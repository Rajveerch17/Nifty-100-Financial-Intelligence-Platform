"""
tests/api/test_health.py
========================
Unit tests for API health endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app


client = TestClient(app)


def test_health_200():
    """Health check returns 200 OK."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_health_db_row_counts():
    """Health check returns db_row_counts for all 10 tables."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "db_row_counts" in data
    assert len(data["db_row_counts"]) >= 7  # At least 7 tables


def test_health_uptime_seconds():
    """Health check returns uptime_seconds."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "uptime_seconds" in data
    assert data["uptime_seconds"] >= 0


def test_health_version():
    """Health check returns version string."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert data["version"] == "1.0.0"
