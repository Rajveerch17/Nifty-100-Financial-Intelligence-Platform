"""
tests/api/test_api.py
======================
Unit tests for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app


client = TestClient(app)


def test_companies_count():
    """GET /api/v1/companies returns 100 records (92 master + 8 auto stubs)."""
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 100
    assert len(data["companies"]) == 100


def test_companies_with_limit():
    """GET /api/v1/companies with limit parameter."""
    response = client.get("/api/v1/companies?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 5
    assert len(data["companies"]) == 5


def test_invalid_ticker():
    """GET /api/v1/companies/INVALID returns 404."""
    response = client.get("/api/v1/companies/INVALID")
    assert response.status_code == 404


def test_screener_filter():
    """GET /api/v1/screener with min_roe filter returns results with ROE >= threshold."""
    response = client.get("/api/v1/screener?min_roe=15")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    # Verify all results have ROE >= 15
    for company in data["results"]:
        if company.get("return_on_equity_pct"):
            assert company["return_on_equity_pct"] >= 15


def test_screener_preset():
    """GET /api/v1/screener with preset parameter."""
    response = client.get("/api/v1/screener?preset=quality_compounder")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["preset"] == "quality_compounder"


def test_peer_groups():
    """GET /api/v1/peer-groups returns peer group definitions."""
    response = client.get("/api/v1/peer-groups")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 11
    assert len(data["peer_groups"]) == 11


def test_peer_comparison():
    """GET /api/v1/peer-comparison for a valid ticker."""
    response = client.get("/api/v1/peer-comparison/TCS")
    assert response.status_code == 200
    data = response.json()
    assert data["company"] == "TCS"
    assert "peer_group" in data
    assert "company_percentiles" in data
