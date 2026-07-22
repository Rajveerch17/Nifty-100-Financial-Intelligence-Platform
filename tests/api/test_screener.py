"""
tests/api/test_screener.py
===========================
Unit tests for screener API endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app


client = TestClient(app)


def test_screener_min_roe_15():
    """Screener with min_roe=15 returns only companies with ROE >= 15."""
    response = client.get("/api/v1/screener?min_roe=15")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    # Verify all results have ROE >= 15
    for company in data["results"]:
        if company.get("return_on_equity_pct") is not None:
            assert company["return_on_equity_pct"] >= 15


def test_screener_invalid_param_returns_400():
    """Screener with invalid parameter returns HTTP 400."""
    response = client.get("/api/v1/screener?min_roe=-10")
    assert response.status_code == 400


def test_screener_no_filters():
    """Screener with no filters returns companies."""
    response = client.get("/api/v1/screener")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["count"] >= 0


def test_screener_max_de():
    """Screener with max_de filter works."""
    response = client.get("/api/v1/screener?max_de=2")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
