"""Companies router"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sqlite3
import pandas as pd
from pathlib import Path

router = APIRouter()
DB_PATH = Path("data/nifty100.db")


@router.get("/companies")
async def get_companies(
    sector: Optional[str] = None,
    market_cap_category: Optional[str] = None,
    search: Optional[str] = None
):
    """Get all companies with optional filters"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT c.id, c.company_name, s.broad_sector, s.sub_sector,
           fr.return_on_equity_pct as roe_pct, fr.return_on_capital_pct as roce_pct
    FROM companies c
    LEFT JOIN sectors s ON c.id = s.company_id
    LEFT JOIN financial_ratios fr ON c.id = fr.company_id 
        AND fr.year = (SELECT MAX(year) FROM financial_ratios)
    WHERE 1=1
    """
    params = []
    
    if sector:
        query += " AND s.broad_sector = ?"
        params.append(sector)
    if search:
        query += " AND (c.id LIKE ? OR c.company_name LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    df = df.replace({float('nan'): None})
    return {"count": len(df), "companies": df.to_dict(orient="records")}


@router.get("/companies/{ticker}")
async def get_company(ticker: str):
    """Get full company profile"""
    conn = sqlite3.connect(DB_PATH)
    ticker = ticker.upper()
    
    company_df = pd.read_sql_query("SELECT * FROM companies WHERE id = ?", conn, params=[ticker])
    if company_df.empty:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company {ticker} not found")
    
    ratios_df = pd.read_sql_query(
        "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year DESC LIMIT 1",
        conn, params=[ticker]
    )
    
    sector_df = pd.read_sql_query(
        "SELECT * FROM sectors WHERE company_id = ?",
        conn, params=[ticker]
    )
    
    conn.close()
    
    return {
        "company": company_df.iloc[0].to_dict(),
        "latest_kpis": ratios_df.iloc[0].to_dict() if not ratios_df.empty else None,
        "sector": sector_df.iloc[0].to_dict() if not sector_df.empty else None
    }


@router.get("/companies/{ticker}/pl")
async def get_pl_history(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    """Get P&L history"""
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM profitandloss WHERE company_id = ?"
    params = [ticker.upper()]
    
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    df = df.replace({float('nan'): None})
    return {"company": ticker.upper(), "history": df.to_dict(orient="records")}


@router.get("/companies/{ticker}/bs")
async def get_bs_history(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    """Get balance sheet history"""
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM balancesheet WHERE company_id = ?"
    params = [ticker.upper()]
    
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    df = df.replace({float('nan'): None})
    return {"company": ticker.upper(), "history": df.to_dict(orient="records")}


@router.get("/companies/{ticker}/cashflow")
async def get_cashflow_history(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    """Get cash flow history"""
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM cashflow WHERE company_id = ?"
    params = [ticker.upper()]
    
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    df = df.replace({float('nan'): None})
    return {"company": ticker.upper(), "history": df.to_dict(orient="records")}


@router.get("/companies/{ticker}/ratios")
async def get_ratios(ticker: str, year: Optional[str] = None):
    """Get computed KPIs per year"""
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM financial_ratios WHERE company_id = ?"
    params = [ticker.upper()]
    
    if year:
        query += " AND year = ?"
        params.append(year)
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    df = df.replace({float('nan'): None})
    return {"company": ticker.upper(), "ratios": df.to_dict(orient="records")}


@router.get("/companies/{ticker}/tearsheet")
async def get_tearsheet(ticker: str):
    """Get tearsheet PDF"""
    from fastapi.responses import FileResponse
    from pathlib import Path
    
    pdf_path = Path("reports/tearsheets") / f"{ticker.upper()}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Tearsheet not found")
    return FileResponse(pdf_path, media_type="application/pdf")
