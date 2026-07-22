"""Health check router"""
from fastapi import APIRouter
import sqlite3
import time
from pathlib import Path

router = APIRouter()
DB_PATH = Path("data/nifty100.db")
START_TIME = time.time()


@router.get("/health")
async def health_check():
    """Health check with db row counts and uptime"""
    conn = sqlite3.connect(DB_PATH)
    tables = ['companies', 'profitandloss', 'balancesheet', 'cashflow', 
              'financial_ratios', 'peer_groups', 'peer_percentiles']
    db_row_counts = {}
    for table in tables:
        try:
            db_row_counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except:
            db_row_counts[table] = 0
    conn.close()
    return {"status": "ok", "db_row_counts": db_row_counts, "uptime_seconds": time.time() - START_TIME, "version": "1.0.0"}
