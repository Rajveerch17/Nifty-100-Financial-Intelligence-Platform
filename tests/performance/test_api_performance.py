"""
tests/performance/test_api_performance.py
==========================================
Performance tests for API endpoints.
"""

import pytest
import time
from fastapi.testclient import TestClient
from src.api.main import app


client = TestClient(app)


def test_health_response_time():
    """Health check should respond within 100ms."""
    start = time.time()
    response = client.get("/api/v1/health")
    elapsed = (time.time() - start) * 1000  # Convert to ms
    assert response.status_code == 200
    assert elapsed < 100, f"Health check took {elapsed:.2f}ms, expected < 100ms"


def test_companies_list_response_time():
    """Companies list should respond within 500ms."""
    start = time.time()
    response = client.get("/api/v1/companies")
    elapsed = (time.time() - start) * 1000
    assert response.status_code == 200
    assert elapsed < 500, f"Companies list took {elapsed:.2f}ms, expected < 500ms"


def test_company_detail_response_time():
    """Company detail should respond within 200ms."""
    start = time.time()
    response = client.get("/api/v1/companies/TCS")
    elapsed = (time.time() - start) * 1000
    assert response.status_code == 200
    assert elapsed < 200, f"Company detail took {elapsed:.2f}ms, expected < 200ms"


def test_screener_response_time():
    """Screener should respond within 1000ms."""
    start = time.time()
    response = client.get("/api/v1/screener?min_roe=15")
    elapsed = (time.time() - start) * 1000
    assert response.status_code == 200
    assert elapsed < 1000, f"Screener took {elapsed:.2f}ms, expected < 1000ms"


def test_sectors_response_time():
    """Sectors list should respond within 300ms."""
    start = time.time()
    response = client.get("/api/v1/sectors")
    elapsed = (time.time() - start) * 1000
    assert response.status_code == 200
    assert elapsed < 300, f"Sectors list took {elapsed:.2f}ms, expected < 300ms"


def test_portfolio_stats_response_time():
    """Portfolio stats should respond within 500ms."""
    start = time.time()
    response = client.get("/api/v1/portfolio/stats")
    elapsed = (time.time() - start) * 1000
    assert response.status_code == 200
    assert elapsed < 500, f"Portfolio stats took {elapsed:.2f}ms, expected < 500ms"
