"""Screener router"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sqlite3
import pandas as pd
from pathlib import Path

router = APIRouter()
DB_PATH = Path("data/nifty100.db")


@router.get("/screener")
async def run_screener(
    min_roe: Optional[float] = None,
    max_de: Optional[float] = None,
    min_fcf: Optional[float] = None,
    sector: Optional[str] = None,
    min_rev_cagr_5yr: Optional[float] = None,
    min_pat_cagr_5yr: Optional[float] = None,
    max_pe: Optional[float] = None
):
    """Run screener with filters"""
    try:
        from src.screener.engine import ScreenerEngine
        
        engine = ScreenerEngine(db_path=str(DB_PATH))
        filters = {}
        
        if min_roe is not None:
            if min_roe < 0 or min_roe > 100:
                raise HTTPException(status_code=400, detail="Invalid min_roe value")
            filters['roe_min'] = min_roe
        if max_de is not None:
            if max_de < 0:
                raise HTTPException(status_code=400, detail="Invalid max_de value")
            filters['de_max'] = max_de
        if min_fcf is not None:
            filters['fcf_min'] = min_fcf
        if min_rev_cagr_5yr is not None:
            filters['revenue_cagr_5yr_min'] = min_rev_cagr_5yr
        if min_pat_cagr_5yr is not None:
            filters['pat_cagr_5yr_min'] = min_pat_cagr_5yr
        if max_pe is not None:
            if max_pe < 0:
                raise HTTPException(status_code=400, detail="Invalid max_pe value")
            filters['pe_max'] = max_pe
        
        df = engine.df_ratios.copy()
        df = df[df['year'] == df['year'].max()]
        
        if sector:
            conn = sqlite3.connect(DB_PATH)
            sector_companies = pd.read_sql_query(
                "SELECT id FROM companies WHERE broad_sector = ?", conn, params=[sector]
            )
            conn.close()
            df = df[df['company_id'].isin(sector_companies['id'])]
        
        if filters:
            df = engine.apply_filters(df, filters)
        
        conn = sqlite3.connect(DB_PATH)
        company_lookup = pd.read_sql_query("SELECT id AS company_id, company_name FROM companies", conn)
        df = df.merge(company_lookup, on='company_id', how='left')
        conn.close()
        
        df['composite_quality_score'] = engine.compute_composite_score(df)
        df = df.sort_values('composite_quality_score', ascending=False)
        df = df.replace({float('nan'): None})
        
        return {"count": len(df), "filters": filters, "results": df.to_dict(orient="records")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
