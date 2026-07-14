"""Quick verification that all dashboard data loaders work."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Mock streamlit cache decorators for CLI testing
import streamlit as st
st.cache_data = lambda **kw: (lambda f: f)
st.cache_resource = lambda **kw: (lambda f: f)

from src.dashboard.utils.db import (
    get_companies, get_ratios, get_pl, get_bs, get_cf,
    get_sectors, get_all_ratios, get_documents, get_pros_cons,
)
from src.screener.engine import ScreenerEngine

TICKERS = ["HDFCBANK", "TCS", "ITC", "RELIANCE", "SUNPHARMA", "ABB", "MARUTI", "INFY", "NESTLEIND", "ONGC"]
YEAR = "2024-03"
errors = []

print("Testing db.py functions...")
companies = get_companies()
print(f"  companies: {len(companies)} rows, sectors: {companies['broad_sector'].notna().sum()}")

ratios = get_all_ratios(year=YEAR)
required_cols = ["return_on_capital_employed_pct", "fcf_cagr_5yr", "pe_ratio", "broad_sector", "revenue_from_operations"]
missing = [c for c in required_cols if c not in ratios.columns]
if missing:
    errors.append(f"get_all_ratios missing columns: {missing}")
else:
    print(f"  get_all_ratios: {len(ratios)} rows, all required columns present")

for ticker in TICKERS:
    try:
        pl = get_pl(ticker)
        if pl.empty:
            errors.append(f"get_pl({ticker}) returned empty")
        elif "revenue_from_operations" not in pl.columns:
            errors.append(f"get_pl({ticker}) missing revenue_from_operations")
        r = get_ratios(ticker, year=YEAR)
        docs = get_documents(ticker)
    except Exception as e:
        errors.append(f"{ticker}: {e}")

engine = ScreenerEngine()
df = get_all_ratios(year=YEAR)
if "fcf_cagr_5yr" not in df.columns:
    df["fcf_cagr_5yr"] = df["free_cash_flow_cr"].fillna(0)
scores = engine.compute_composite_score(df)
print(f"  composite score: {len(scores)} values, mean={scores.mean():.2f}")

sectors = get_sectors()
print(f"  sectors: {sectors['broad_sector'].nunique()} unique sectors")

if errors:
    print("\nERRORS:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("\nAll checks passed!")
