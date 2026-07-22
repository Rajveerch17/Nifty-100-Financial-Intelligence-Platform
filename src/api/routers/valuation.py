"""Valuation router"""
from fastapi import APIRouter
import sqlite3
import pandas as pd
from pathlib import Path

router = APIRouter()
DB_PATH = Path("data/nifty100.db")


@router.get("/market-cap/{ticker}")
async def get_market_cap_history(ticker: str):
    """Get historical valuation multiples 2019-2024"""
    conn = sqlite3.connect(DB_PATH)
    ticker = ticker.upper()
    
    query = """
    SELECT year, pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct
    FROM market_cap
    WHERE company_id = ? AND year BETWEEN '2019-03' AND '2024-03'
    ORDER BY year
    """
    
    df = pd.read_sql_query(query, conn, params=[ticker])
    conn.close()
    df = df.replace({float('nan'): None})
    return {"company": ticker, "history": df.to_dict(orient="records")}
