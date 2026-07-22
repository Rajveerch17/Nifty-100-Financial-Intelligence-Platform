"""Sectors router"""
from fastapi import APIRouter, HTTPException
import sqlite3
import pandas as pd
from pathlib import Path

router = APIRouter()
DB_PATH = Path("data/nifty100.db")


@router.get("/sectors")
async def get_sectors():
    """Get all sectors with stats"""
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT s.broad_sector, COUNT(*) as company_count,
           AVG(fr.return_on_equity_pct) as median_roe,
           AVG(mc.pe_ratio) as median_pe,
           AVG(fr.debt_to_equity) as median_de
    FROM sectors s
    LEFT JOIN financial_ratios fr ON s.company_id = fr.company_id 
        AND fr.year = (SELECT MAX(year) FROM financial_ratios)
    LEFT JOIN market_cap mc ON s.company_id = mc.company_id 
        AND mc.year = (SELECT MAX(year) FROM market_cap)
    GROUP BY s.broad_sector
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    df = df.replace({float('nan'): None})
    return {"count": len(df), "sectors": df.to_dict(orient="records")}


@router.get("/sectors/{sector}/companies")
async def get_sector_companies(sector: str):
    """Get companies in a sector"""
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT c.id, c.company_name, s.broad_sector,
           fr.return_on_equity_pct, fr.debt_to_equity, fr.revenue_cagr_5yr,
           fr.operating_profit_margin_pct, fr.free_cash_flow_cr
    FROM companies c
    LEFT JOIN sectors s ON c.id = s.company_id
    LEFT JOIN financial_ratios fr ON c.id = fr.company_id 
        AND fr.year = (SELECT MAX(year) FROM financial_ratios)
    WHERE s.broad_sector = ?
    """
    
    df = pd.read_sql_query(query, conn, params=[sector])
    conn.close()
    
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Sector {sector} not found")
    
    df = df.replace({float('nan'): None})
    return {"sector": sector, "count": len(df), "companies": df.to_dict(orient="records")}
