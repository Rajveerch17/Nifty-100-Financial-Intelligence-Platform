"""Peers router"""
from fastapi import APIRouter, HTTPException
import sqlite3
import pandas as pd
from pathlib import Path

router = APIRouter()
DB_PATH = Path("data/nifty100.db")


@router.get("/peers/{group_name}")
async def get_peer_group(group_name: str):
    """Get companies in a peer group with percentiles"""
    from src.analytics.peer import PeerComparisonEngine
    
    engine = PeerComparisonEngine(db_path=str(DB_PATH))
    
    if group_name not in engine.PEER_GROUPS:
        raise HTTPException(status_code=404, detail=f"Peer group {group_name} not found")
    
    # Return peer group members without percentiles since table doesn't exist
    return {
        "group_name": group_name,
        "members": engine.PEER_GROUPS[group_name],
        "benchmark": engine.BENCHMARK_COMPANIES.get(group_name)
    }


@router.get("/companies/{ticker}/peers/compare")
async def get_peer_radar(ticker: str):
    """Get radar data for peer comparison"""
    from src.analytics.peer import PeerComparisonEngine
    
    ticker = ticker.upper()
    engine = PeerComparisonEngine(db_path=str(DB_PATH))
    
    peer_group = None
    for group_name, members in engine.PEER_GROUPS.items():
        if ticker in members:
            peer_group = group_name
            break
    
    if not peer_group:
        raise HTTPException(status_code=404, detail=f"Company {ticker} not in any peer group")
    
    conn = sqlite3.connect(DB_PATH)
    
    metrics = ['return_on_equity_pct', 'debt_to_equity', 'revenue_cagr_5yr',
               'operating_profit_margin_pct', 'free_cash_flow_cr',
               'return_on_capital_pct', 'net_profit_margin_pct',
               'asset_turnover', 'dividend_payout_ratio_pct', 'interest_coverage']
    
    company_data = pd.read_sql_query(
        f"SELECT {','.join(metrics)} FROM financial_ratios WHERE company_id = ? ORDER BY year DESC LIMIT 1",
        conn, params=[ticker]
    )
    
    group_members = engine.PEER_GROUPS[peer_group]
    group_data = pd.read_sql_query(
        f"SELECT company_id, {','.join(metrics)} FROM financial_ratios WHERE company_id IN ({','.join(['?']*len(group_members))}) AND year = (SELECT MAX(year) FROM financial_ratios)",
        conn, params=group_members
    )
    
    benchmark = engine.BENCHMARK_COMPANIES.get(peer_group)
    benchmark_data = None
    if benchmark:
        benchmark_data = pd.read_sql_query(
            f"SELECT {','.join(metrics)} FROM financial_ratios WHERE company_id = ? ORDER BY year DESC LIMIT 1",
            conn, params=[benchmark]
        )
    
    conn.close()
    
    company_values = company_data.iloc[0][metrics].tolist() if not company_data.empty else [0]*10
    group_avg = group_data[metrics].mean().tolist() if not group_data.empty else [0]*10
    benchmark_values = benchmark_data.iloc[0][metrics].tolist() if benchmark_data is not None and not benchmark_data.empty else [0]*10
    
    return {
        "company": ticker,
        "peer_group": peer_group,
        "metrics": metrics,
        "company_values": company_values,
        "group_average": group_avg,
        "benchmark_values": benchmark_values
    }
