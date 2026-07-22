"""Portfolio router"""
from fastapi import APIRouter
import sqlite3
import pandas as pd
from pathlib import Path

router = APIRouter()
DB_PATH = Path("data/nifty100.db")


@router.get("/portfolio/stats")
async def get_portfolio_stats():
    """Get P10-P90 percentile table for 10 KPIs"""
    conn = sqlite3.connect(DB_PATH)
    
    kpi_cols = ['return_on_equity_pct', 'debt_to_equity', 'revenue_cagr_5yr',
                'operating_profit_margin_pct', 'free_cash_flow_cr',
                'return_on_capital_pct', 'net_profit_margin_pct',
                'asset_turnover', 'dividend_payout_ratio_pct', 'interest_coverage']
    
    query = f"""
    SELECT {','.join(kpi_cols)}
    FROM financial_ratios
    WHERE year = (SELECT MAX(year) FROM financial_ratios)
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    stats = df[kpi_cols].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9])
    stats = stats.replace({float('nan'): None})
    
    return {"kpis": kpi_cols, "statistics": stats.to_dict()}
