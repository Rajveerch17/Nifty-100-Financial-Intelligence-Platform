"""
src/dashboard/utils/db.py
========================
Shared data loader with @st.cache_data for Streamlit dashboard.
Provides cached database query functions for all screens.
"""

import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

# Ensure project root is on sys.path (needed when Streamlit runs page scripts directly)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def _normalise_year(value: object) -> str:
    if pd.isna(value):
        return ""
    value_str = str(value).strip()
    if not value_str:
        return ""
    if "-" in value_str:
        return value_str.split("-")[0]
    return value_str[:4] if len(value_str) >= 4 else value_str


def _normalize_ratios_df(df: pd.DataFrame) -> pd.DataFrame:
    """Add aliases and derived columns expected by dashboard pages."""
    if df.empty:
        return df

    result = df.copy()

    if "return_on_capital_pct" in result.columns and "return_on_capital_employed_pct" not in result.columns:
        result["return_on_capital_employed_pct"] = result["return_on_capital_pct"]

    if "fcf_cagr_5yr" not in result.columns and "free_cash_flow_cr" in result.columns:
        result["fcf_cagr_5yr"] = result["free_cash_flow_cr"].fillna(0)

    if "free_cash_flow_cr" in result.columns:
        result["fcf_positive_flag"] = result["free_cash_flow_cr"] > 0

    return result


def _merge_market_cap(df: pd.DataFrame, conn: sqlite3.Connection) -> pd.DataFrame:
    if df.empty:
        return df

    market_cap = pd.read_sql_query(
        """
        SELECT company_id, year, market_cap_crore, pe_ratio, pb_ratio,
               ev_ebitda, dividend_yield_pct
        FROM market_cap
        """,
        conn,
    )
    if market_cap.empty:
        return df

    result = df.copy()
    result["year_key"] = result["year"].apply(_normalise_year)
    market_cap = market_cap.copy()
    market_cap["year_key"] = market_cap["year"].apply(_normalise_year)

    merged = result.merge(
        market_cap.drop(columns=["year"]),
        on=["company_id", "year_key"],
        how="left",
        suffixes=("", "_mc"),
    )
    return merged.drop(columns=["year_key"], errors="ignore")


def _merge_sectors(df: pd.DataFrame, conn: sqlite3.Connection) -> pd.DataFrame:
    if df.empty:
        return df

    sectors = pd.read_sql_query(
        "SELECT company_id, broad_sector, sub_sector FROM sectors",
        conn,
    )
    if sectors.empty:
        return df

    return df.merge(sectors, on="company_id", how="left")


def _merge_company_names(df: pd.DataFrame, conn: sqlite3.Connection) -> pd.DataFrame:
    if df.empty or "company_name" in df.columns:
        return df

    companies = pd.read_sql_query(
        "SELECT id AS company_id, company_name FROM companies",
        conn,
    )
    return df.merge(companies, on="company_id", how="left")


def _merge_pl_revenue(df: pd.DataFrame, conn: sqlite3.Connection, year: Optional[str] = None) -> pd.DataFrame:
    """Attach latest revenue (sales) from profitandloss for sector bubble charts."""
    if df.empty:
        return df

    pl_query = "SELECT company_id, year, sales FROM profitandloss"
    params: list = []
    if year:
        pl_query += " WHERE year = ?"
        params.append(year)

    pl = pd.read_sql_query(pl_query, conn, params=params or None)
    if pl.empty:
        return df

    pl = pl.rename(columns={"sales": "revenue_from_operations"})
    return df.merge(pl, on=["company_id", "year"], how="left")


@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql_query(
        """
        SELECT c.*, s.broad_sector, s.sub_sector
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
        """,
        conn,
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_ratios(ticker: str, year: Optional[str] = None) -> pd.DataFrame:
    conn = _connect()

    if year:
        query = "SELECT * FROM financial_ratios WHERE company_id = ? AND year = ? ORDER BY year"
        df = pd.read_sql_query(query, conn, params=[ticker, year])
    else:
        query = "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year"
        df = pd.read_sql_query(query, conn, params=[ticker])

    df = _merge_market_cap(df, conn)
    df = _normalize_ratios_df(df)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pl(ticker: str) -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql_query(
        "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year",
        conn,
        params=[ticker],
    )
    conn.close()

    if not df.empty and "sales" in df.columns:
        df = df.rename(columns={"sales": "revenue_from_operations"})
    return df


@st.cache_data(ttl=600)
def get_bs(ticker: str) -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql_query(
        "SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year",
        conn,
        params=[ticker],
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_cf(ticker: str) -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql_query(
        "SELECT * FROM cashflow WHERE company_id = ? ORDER BY year",
        conn,
        params=[ticker],
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql_query(
        """
        SELECT s.company_id, c.company_name, s.broad_sector, s.sub_sector,
               s.index_weight_pct, s.market_cap_category
        FROM sectors s
        JOIN companies c ON s.company_id = c.id
        """,
        conn,
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peers(group_name: str) -> Dict[str, List[str]]:
    from src.analytics.peer import PeerComparisonEngine

    return {
        "members": PeerComparisonEngine.PEER_GROUPS.get(group_name, []),
        "benchmark": PeerComparisonEngine.BENCHMARK_COMPANIES.get(group_name),
    }


@st.cache_data(ttl=600)
def get_valuation(ticker: str) -> pd.DataFrame:
    conn = _connect()

    df = pd.read_sql_query(
        """
        SELECT c.id AS company_id, c.company_name, s.broad_sector AS sector,
               m.pe_ratio, m.pb_ratio, m.ev_ebitda, m.dividend_yield_pct,
               m.market_cap_crore
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
        LEFT JOIN market_cap m ON c.id = m.company_id
        WHERE c.id = ?
        ORDER BY m.year DESC
        LIMIT 1
        """,
        conn,
        params=[ticker],
    )

    ratios_df = pd.read_sql_query(
        """
        SELECT * FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year DESC
        LIMIT 1
        """,
        conn,
        params=[ticker],
    )
    conn.close()

    if not ratios_df.empty and not df.empty:
        for col in ratios_df.columns:
            if col not in df.columns:
                df[col] = ratios_df.iloc[0][col]

    return _normalize_ratios_df(df)


@st.cache_data(ttl=600)
def get_all_ratios(year: Optional[str] = None) -> pd.DataFrame:
    conn = _connect()

    if year:
        query = """
            SELECT fr.*
            FROM financial_ratios fr
            WHERE fr.year = ?
        """
        df = pd.read_sql_query(query, conn, params=[year])
    else:
        df = pd.read_sql_query("SELECT * FROM financial_ratios", conn)

    df = _merge_company_names(df, conn)
    df = _merge_sectors(df, conn)
    df = _merge_market_cap(df, conn)
    df = _merge_pl_revenue(df, conn, year=year)
    df = _normalize_ratios_df(df)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peer_percentiles(year: Optional[str] = None) -> pd.DataFrame:
    conn = _connect()

    if year:
        df = pd.read_sql_query(
            "SELECT * FROM peer_percentiles WHERE year = ?",
            conn,
            params=[year],
        )
    else:
        df = pd.read_sql_query("SELECT * FROM peer_percentiles", conn)

    conn.close()
    return df


@st.cache_data(ttl=600)
def get_documents(ticker: str) -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql_query(
        """
        SELECT company_id, year, annual_report
        FROM documents
        WHERE company_id = ?
        ORDER BY year DESC
        """,
        conn,
        params=[ticker],
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pros_cons(ticker: str) -> Dict[str, str]:
    conn = _connect()
    df = pd.read_sql_query(
        "SELECT pros, cons FROM prosandcons WHERE company_id = ? LIMIT 1",
        conn,
        params=[ticker],
    )
    conn.close()

    if df.empty:
        return {"pros": "", "cons": ""}
    return {"pros": df.iloc[0]["pros"] or "", "cons": df.iloc[0]["cons"] or ""}
