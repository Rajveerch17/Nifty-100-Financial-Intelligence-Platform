"""Documents router"""
from fastapi import APIRouter, HTTPException
import sqlite3
import pandas as pd
from pathlib import Path

router = APIRouter()
DB_PATH = Path("data/nifty100.db")


@router.get("/companies/{ticker}/documents")
async def get_documents(ticker: str):
    """Get annual report links"""
    conn = sqlite3.connect(DB_PATH)
    ticker = ticker.upper()
    
    query = """
    SELECT year, annual_report
    FROM documents
    WHERE company_id = ?
    ORDER BY year DESC
    """
    
    df = pd.read_sql_query(query, conn, params=[ticker])
    conn.close()
    df = df.replace({float('nan'): None})
    return {"company": ticker, "documents": df.to_dict(orient="records")}
