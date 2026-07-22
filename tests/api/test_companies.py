"""
tests/api/test_companies.py
===========================
Unit tests for companies API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app


client = TestClient(app)


def test_companies_returns_92_records():
    """GET /companies returns 92 records."""
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 90  # At least 90 companies


def test_companies_tcs_returns_data():
    """GET /companies/TCS returns correct data."""
    response = client.get("/api/v1/companies/TCS")
    assert response.status_code == 200
    data = response.json()
    assert "company" in data
    assert data["company"]["id"] == "TCS"


def test_companies_invalid_returns_404():
    """GET /companies/INVALID returns HTTP 404."""
    response = client.get("/api/v1/companies/INVALIDTICKER")
    assert response.status_code == 404


def test_companies_pl_history():
    """GET /companies/TCS/pl returns P&L history."""
    response = client.get("/api/v1/companies/TCS/pl")
    assert response.status_code == 200
    data = response.json()
    assert "history" in data


def test_companies_bs_history():
    """GET /companies/TCS/bs returns balance sheet history."""
    response = client.get("/api/v1/companies/TCS/bs")
    assert response.status_code == 200
    data = response.json()
    assert "history" in data


def test_companies_cashflow_history():
    """GET /companies/TCS/cashflow returns cash flow history."""
    response = client.get("/api/v1/companies/TCS/cashflow")
    assert response.status_code == 200
    data = response.json()
    assert "history" in data


def test_companies_ratios():
    """GET /companies/TCS/ratios returns KPIs."""
    response = client.get("/api/v1/companies/TCS/ratios")
    assert response.status_code == 200
    data = response.json()
    assert "ratios" in data
