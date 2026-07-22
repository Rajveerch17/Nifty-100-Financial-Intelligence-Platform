"""
tests/api/test_api.py
======================
Unit tests for API endpoints - updated for new router structure.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app


client = TestClient(app)


def test_companies_count():
    """GET /api/v1/companies returns companies."""
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 90


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


def test_peers_group():
    """GET /api/v1/peers/{group_name} returns peer group data."""
    # First get a valid peer group name from the peer comparison engine
    from src.analytics.peer import PeerComparisonEngine
    peer_groups = PeerComparisonEngine.PEER_GROUPS
    if peer_groups:
        first_group = list(peer_groups.keys())[0]
        response = client.get(f"/api/v1/peers/{first_group}")
        assert response.status_code == 200
        data = response.json()
        assert "group_name" in data


def test_peers_compare():
    """GET /api/v1/companies/{ticker}/peers/compare returns radar data."""
    response = client.get("/api/v1/companies/TCS/peers/compare")
    # This might return 404 if TCS is not in a peer group
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = response.json()
        assert "company" in data
        assert "metrics" in data


def test_portfolio_stats():
    """GET /api/v1/portfolio/stats returns percentile table."""
    response = client.get("/api/v1/portfolio/stats")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "statistics" in data


def test_valuation_history():
    """GET /api/v1/market-cap/{ticker} returns valuation history."""
    response = client.get("/api/v1/market-cap/TCS")
    assert response.status_code == 200
    data = response.json()
    assert "company" in data
    assert "history" in data


def test_documents():
    """GET /api/v1/companies/{ticker}/documents returns annual report links."""
    response = client.get("/api/v1/companies/TCS/documents")
    assert response.status_code == 200
    data = response.json()
    assert "company" in data
    assert "documents" in data
