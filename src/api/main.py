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
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, List
import logging
import sqlite3
import pandas as pd
from pathlib import Path
import time
import sys
from src.api.routers import health, companies, screener, sectors, peers, valuation, portfolio, documents

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Nifty 100 Financial Intelligence API",
    description="REST API for financial ratios, screener, and peer comparison",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    return response

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(companies.router, prefix="/api/v1", tags=["companies"])
app.include_router(screener.router, prefix="/api/v1", tags=["screener"])
app.include_router(sectors.router, prefix="/api/v1", tags=["sectors"])
app.include_router(peers.router, prefix="/api/v1", tags=["peers"])
app.include_router(valuation.router, prefix="/api/v1", tags=["valuation"])
app.include_router(portfolio.router, prefix="/api/v1", tags=["portfolio"])
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])



if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
