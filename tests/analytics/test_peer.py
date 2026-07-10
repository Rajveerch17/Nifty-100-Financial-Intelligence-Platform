import sqlite3
from pathlib import Path

from src.analytics.peer import PeerComparisonEngine


def test_generate_peer_comparison_excel_falls_back_to_latest_available_year(tmp_path, monkeypatch):
    db_path = tmp_path / "peer_test.db"
    conn = sqlite3.connect(db_path)

    conn.execute(
        "CREATE TABLE financial_ratios ("
        "company_id TEXT, year TEXT, company_name TEXT, "
        "return_on_equity_pct REAL, return_on_capital_employed_pct REAL, "
        "net_profit_margin_pct REAL, debt_to_equity REAL, free_cash_flow_cr REAL, "
        "pat_cagr_5yr REAL, revenue_cagr_5yr REAL, eps_cagr_5yr REAL, "
        "interest_coverage REAL, asset_turnover REAL)"
    )
    conn.execute(
        "CREATE TABLE companies (id TEXT, company_name TEXT)"
    )

    conn.execute("INSERT INTO companies VALUES (?, ?)", ("AAA", "Alpha"))
    conn.execute("INSERT INTO companies VALUES (?, ?)", ("BBB", "Beta"))
    conn.execute("INSERT INTO companies VALUES (?, ?)", ("CCC", "Gamma"))

    conn.execute(
        "INSERT INTO financial_ratios VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("AAA", "2023-03", "Alpha", 12.0, 11.0, 10.0, 0.8, 1.0, 8.0, 7.0, 6.0, 5.0, 4.0),
    )
    conn.execute(
        "INSERT INTO financial_ratios VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("BBB", "2023-03", "Beta", 13.0, 12.0, 11.0, 0.7, 1.2, 9.0, 8.0, 7.0, 6.0, 5.0),
    )
    conn.execute(
        "INSERT INTO financial_ratios VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("CCC", "2024-03", "Gamma", 20.0, 18.0, 16.0, 0.5, 2.0, 15.0, 14.0, 13.0, 12.0, 11.0),
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(PeerComparisonEngine, "PEER_GROUPS", {"Test Group": ["AAA", "BBB"]})
    monkeypatch.setattr(PeerComparisonEngine, "BENCHMARK_COMPANIES", {"Test Group": "AAA"})

    engine = PeerComparisonEngine(str(db_path))
    output_path = tmp_path / "peer_comparison.xlsx"

    engine.generate_peer_comparison_excel(output_path=str(output_path))

    assert output_path.exists()
