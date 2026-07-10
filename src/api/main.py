"""
src/api/main.py
===============
FastAPI server for Nifty 100 Financial Intelligence Platform.
Provides REST API endpoints for companies, screener, and health checks.

Author: Data Analytics Team
Date: Sprint 3 (Day 21-23)
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, Dict, List
import logging
import sqlite3
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Nifty 100 Financial Intelligence API",
    description="REST API for financial ratios, screener, and peer comparison",
    version="1.0.0"
)

# Database path
DB_PATH = Path("data/nifty100.db")


@app.get("/api/v1/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON response with status 'ok' if service is healthy
    """
    try:
        # Check database connection
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
        
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "error", "message": str(e)}
        )


@app.get("/api/v1/companies")
async def get_companies(
    limit: Optional[int] = Query(None, description="Limit number of results")
):
    """
    Get all companies.
    
    Args:
        limit: Optional limit on number of results
    
    Returns:
        List of companies with metadata
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        
        query = "SELECT id, company_name, roce_percentage, roe_percentage FROM companies"
        params = []
        
        if limit:
            query += f" LIMIT {limit}"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        # Replace NaN with None for JSON serialization
        df = df.replace({float('nan'): None})
        
        return {
            "count": len(df),
            "companies": df.to_dict(orient="records")
        }
    except Exception as e:
        logger.error(f"Failed to get companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/companies/{ticker}")
async def get_company_by_ticker(ticker: str):
    """
    Get company details by ticker symbol.
    
    Args:
        ticker: NSE ticker symbol (e.g., TCS, RELIANCE)
    
    Returns:
        Company details with latest financial ratios
    """
    try:
        ticker = ticker.upper()
        conn = sqlite3.connect(DB_PATH)
        
        # Get company info
        company_query = "SELECT * FROM companies WHERE id = ?"
        company_df = pd.read_sql_query(company_query, conn, params=[ticker])
        
        if company_df.empty:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Company {ticker} not found")
        
        # Get latest financial ratios
        ratios_query = """
            SELECT * FROM financial_ratios 
            WHERE company_id = ? 
            ORDER BY year DESC 
            LIMIT 1
        """
        ratios_df = pd.read_sql_query(ratios_query, conn, params=[ticker])
        
        conn.close()
        
        return {
            "company": company_df.iloc[0].to_dict(),
            "financial_ratios": ratios_df.iloc[0].to_dict() if not ratios_df.empty else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get company {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/screener")
async def run_screener(
    preset: Optional[str] = Query(None, description="Preset name (e.g., quality_compounder)"),
    min_roe: Optional[float] = Query(None, description="Minimum ROE (%)"),
    max_de: Optional[float] = Query(None, description="Maximum Debt-to-Equity"),
    min_fcf: Optional[float] = Query(None, description="Minimum Free Cash Flow (Cr)"),
    min_revenue_cagr: Optional[float] = Query(None, description="Minimum Revenue CAGR 5yr (%)"),
    year: Optional[str] = Query(None, description="Specific year (e.g., 2024-03)")
):
    """
    Run financial screener with custom filters or preset.
    
    Args:
        preset: Optional preset name from screener_config.yaml
        min_roe: Minimum ROE filter
        max_de: Maximum D/E filter
        min_fcf: Minimum FCF filter
        min_revenue_cagr: Minimum Revenue CAGR filter
        year: Specific year to screen
    
    Returns:
        Filtered companies with ranking
    """
    try:
        from src.screener.engine import ScreenerEngine
        
        engine = ScreenerEngine(db_path=str(DB_PATH))
        
        # Build filter dict from query params
        filters = {}
        if min_roe is not None:
            filters['roe_min'] = min_roe
        if max_de is not None:
            filters['de_max'] = max_de
        if min_fcf is not None:
            filters['fcf_min'] = min_fcf
        if min_revenue_cagr is not None:
            filters['revenue_cagr_5yr_min'] = min_revenue_cagr
        
        # Add fcf_cagr_5yr column if not present (use free_cash_flow_cr as proxy)
        if 'fcf_cagr_5yr' not in engine.df_ratios.columns:
            engine.df_ratios['fcf_cagr_5yr'] = engine.df_ratios['free_cash_flow_cr'].fillna(0)
        
        if preset:
            # Use preset
            df = engine.apply_preset(preset, year=year)
        else:
            # Use custom filters
            df = engine.df_ratios.copy()
            
            if year:
                df = df[df['year'] == year]
            else:
                df = df[df['year'] == df['year'].max()]
            
            if filters:
                df = engine.apply_filters(df, filters)
            
            # Add company names
            conn = sqlite3.connect(DB_PATH)
            company_lookup = pd.read_sql_query(
                "SELECT id AS company_id, company_name FROM companies",
                conn
            )
            df = df.merge(company_lookup, on='company_id', how='left')
            conn.close()
            
            # Compute composite score
            df['composite_quality_score'] = engine.compute_composite_score(df)
            df = df.sort_values('composite_quality_score', ascending=False)
            df['rank'] = range(1, len(df) + 1)
        
        # Replace NaN with None for JSON serialization
        df = df.replace({float('nan'): None})
        
        return {
            "count": len(df),
            "preset": preset,
            "filters": filters,
            "year": year,
            "results": df.to_dict(orient="records")
        }
    except Exception as e:
        logger.error(f"Screener failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/peer-groups")
async def get_peer_groups():
    """
    Get all peer group definitions.
    
    Returns:
        Dictionary of peer groups with member companies
    """
    try:
        from src.analytics.peer import PeerComparisonEngine
        
        peer_groups = PeerComparisonEngine.PEER_GROUPS
        benchmarks = PeerComparisonEngine.BENCHMARK_COMPANIES
        
        result = []
        for group_name, members in peer_groups.items():
            result.append({
                "group_name": group_name,
                "members": members,
                "benchmark": benchmarks.get(group_name)
            })
        
        return {
            "count": len(result),
            "peer_groups": result
        }
    except Exception as e:
        logger.error(f"Failed to get peer groups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/peer-comparison/{ticker}")
async def get_peer_comparison(ticker: str, year: Optional[str] = None):
    """
    Get peer comparison for a company.
    
    Args:
        ticker: NSE ticker symbol
        year: Specific year (optional)
    
    Returns:
        Peer group comparison with percentile ranks
    """
    try:
        ticker = ticker.upper()
        from src.analytics.peer import PeerComparisonEngine
        
        engine = PeerComparisonEngine(db_path=str(DB_PATH))
        
        # Find which peer group this company belongs to
        peer_group = None
        for group_name, members in engine.PEER_GROUPS.items():
            if ticker in members:
                peer_group = group_name
                break
        
        if not peer_group:
            raise HTTPException(
                status_code=404, 
                detail=f"Company {ticker} not found in any peer group"
            )
        
        # Get peer percentiles
        df_percentiles = engine.compute_peer_percentiles(year=year)
        
        # Filter to this company's peer group
        company_percentiles = df_percentiles[
            (df_percentiles['company_id'] == ticker) &
            (df_percentiles['peer_group'] == peer_group)
        ]
        
        # Get group members for comparison
        group_members = engine.PEER_GROUPS[peer_group]
        group_percentiles = df_percentiles[
            df_percentiles['peer_group'] == peer_group
        ]
        
        return {
            "company": ticker,
            "peer_group": peer_group,
            "group_members": group_members,
            "year": year,
            "company_percentiles": company_percentiles.to_dict(orient="records"),
            "group_comparison": group_percentiles.to_dict(orient="records")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Peer comparison failed for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
