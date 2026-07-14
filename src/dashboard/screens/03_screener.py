"""Screener screen — metric sliders, presets, live results, CSV export."""

import sys
from pathlib import Path

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
from src.dashboard.utils.db import get_all_ratios
from src.screener.engine import ScreenerEngine

st.markdown('<div class="main-title">🔍 Financial Screener</div>', unsafe_allow_html=True)
st.markdown("---")

selected_year = st.session_state.get("selected_year", "2024-03")


@st.cache_resource(ttl=600)
def get_screener_engine():
    return ScreenerEngine()


engine = get_screener_engine()

with st.sidebar:
    st.markdown("### Filter Settings")
    st.markdown("#### Quick Presets")

    preset_col1, preset_col2 = st.columns(2)

    with preset_col1:
        if st.button("Quality"):
            st.session_state.update(
                {"roe_min": 15.0, "de_max": 1.0, "fcf_min": 100.0, "revenue_cagr_min": 10.0,
                 "pat_cagr_min": 0.0, "opm_min": 0.0, "pe_max": 100.0, "pb_max": 100.0,
                 "dividend_yield_min": 0.0, "icr_min": 0.0}
            )
        if st.button("Value"):
            st.session_state.update(
                {"roe_min": 0.0, "de_max": 2.0, "fcf_min": 0.0, "revenue_cagr_min": 0.0,
                 "pat_cagr_min": 0.0, "opm_min": 0.0, "pe_max": 20.0, "pb_max": 3.0,
                 "dividend_yield_min": 1.0, "icr_min": 0.0}
            )
        if st.button("Growth"):
            st.session_state.update(
                {"roe_min": 0.0, "de_max": 2.0, "fcf_min": 0.0, "revenue_cagr_min": 15.0,
                 "pat_cagr_min": 20.0, "opm_min": 0.0, "pe_max": 100.0, "pb_max": 100.0,
                 "dividend_yield_min": 0.0, "icr_min": 0.0}
            )

    with preset_col2:
        if st.button("Dividend"):
            st.session_state.update(
                {"roe_min": 0.0, "de_max": 100.0, "fcf_min": 100.0, "revenue_cagr_min": 0.0,
                 "pat_cagr_min": 0.0, "opm_min": 0.0, "pe_max": 100.0, "pb_max": 100.0,
                 "dividend_yield_min": 2.0, "icr_min": 0.0}
            )
        if st.button("Debt-Free"):
            st.session_state.update(
                {"roe_min": 12.0, "de_max": 0.0, "fcf_min": 0.0, "revenue_cagr_min": 0.0,
                 "pat_cagr_min": 0.0, "opm_min": 0.0, "pe_max": 100.0, "pb_max": 100.0,
                 "dividend_yield_min": 0.0, "icr_min": 0.0}
            )
        if st.button("Turnaround"):
            st.session_state.update(
                {"roe_min": 0.0, "de_max": 100.0, "fcf_min": 50.0, "revenue_cagr_min": 10.0,
                 "pat_cagr_min": 0.0, "opm_min": 0.0, "pe_max": 100.0, "pb_max": 100.0,
                 "dividend_yield_min": 0.0, "icr_min": 0.0}
            )

    st.markdown("---")
    st.markdown("#### Custom Filters")

    defaults = {
        "roe_min": 0.0, "de_max": 2.0, "fcf_min": 0.0, "revenue_cagr_min": 0.0,
        "pat_cagr_min": 0.0, "opm_min": 0.0, "pe_max": 100.0, "pb_max": 100.0,
        "dividend_yield_min": 0.0, "icr_min": 0.0,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    roe_min = st.slider("ROE Min (%)", 0.0, 50.0, st.session_state["roe_min"], 0.5)
    de_max = st.slider("D/E Max", 0.0, 5.0, st.session_state["de_max"], 0.1)
    fcf_min = st.slider("FCF Min (Cr)", 0.0, 1000.0, st.session_state["fcf_min"], 10.0)
    revenue_cagr_min = st.slider("Revenue CAGR 5yr Min (%)", 0.0, 50.0, st.session_state["revenue_cagr_min"], 1.0)
    pat_cagr_min = st.slider("PAT CAGR 5yr Min (%)", 0.0, 50.0, st.session_state["pat_cagr_min"], 1.0)
    opm_min = st.slider("OPM Min (%)", 0.0, 50.0, st.session_state["opm_min"], 0.5)
    pe_max = st.slider("P/E Max", 0.0, 100.0, st.session_state["pe_max"], 1.0)
    pb_max = st.slider("P/B Max", 0.0, 20.0, st.session_state["pb_max"], 0.5)
    dividend_yield_min = st.slider("Dividend Yield Min (%)", 0.0, 10.0, st.session_state["dividend_yield_min"], 0.1)
    icr_min = st.slider("ICR Min", 0.0, 20.0, st.session_state["icr_min"], 0.5)

    for key, val in [
        ("roe_min", roe_min), ("de_max", de_max), ("fcf_min", fcf_min),
        ("revenue_cagr_min", revenue_cagr_min), ("pat_cagr_min", pat_cagr_min),
        ("opm_min", opm_min), ("pe_max", pe_max), ("pb_max", pb_max),
        ("dividend_yield_min", dividend_yield_min), ("icr_min", icr_min),
    ]:
        st.session_state[key] = val

ratios = get_all_ratios(year=selected_year)

if ratios.empty:
    st.warning(f"No data available for year {selected_year}")
    st.stop()

df_filtered = ratios.copy()

if "return_on_equity_pct" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["return_on_equity_pct"].fillna(-999) >= roe_min]
if "debt_to_equity" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["debt_to_equity"].fillna(999) <= de_max]
if "free_cash_flow_cr" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["free_cash_flow_cr"].fillna(-999) >= fcf_min]
if "revenue_cagr_5yr" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["revenue_cagr_5yr"].fillna(-999) >= revenue_cagr_min]
if "pat_cagr_5yr" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["pat_cagr_5yr"].fillna(-999) >= pat_cagr_min]
if "operating_profit_margin_pct" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["operating_profit_margin_pct"].fillna(-999) >= opm_min]
if "pe_ratio" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["pe_ratio"].fillna(999) <= pe_max]
if "pb_ratio" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["pb_ratio"].fillna(999) <= pb_max]
if "dividend_yield_pct" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["dividend_yield_pct"].fillna(-999) >= dividend_yield_min]
if "interest_coverage" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["interest_coverage"].fillna(-999) >= icr_min]

if "fcf_cagr_5yr" not in df_filtered.columns:
    df_filtered["fcf_cagr_5yr"] = df_filtered.get("free_cash_flow_cr", pd.Series(0)).fillna(0)

df_filtered = df_filtered.copy()
df_filtered["composite_quality_score"] = engine.compute_composite_score(df_filtered)
df_filtered = df_filtered.sort_values("composite_quality_score", ascending=False)
df_filtered["rank"] = range(1, len(df_filtered) + 1)

st.markdown(f"### {len(df_filtered)} companies match your filters")

csv = df_filtered.to_csv(index=False)
st.download_button(
    label="Download Results as CSV",
    data=csv,
    file_name=f"screener_results_{selected_year}.csv",
    mime="text/csv",
)

display_columns = [
    "rank", "company_id", "company_name", "broad_sector", "composite_quality_score",
    "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr", "revenue_cagr_5yr",
    "pat_cagr_5yr", "operating_profit_margin_pct", "pe_ratio", "pb_ratio",
    "dividend_yield_pct", "interest_coverage",
]
display_columns = [col for col in display_columns if col in df_filtered.columns]

st.dataframe(
    df_filtered[display_columns].round(2),
    column_config={
        "rank": st.column_config.NumberColumn("Rank", width="small"),
        "company_id": st.column_config.TextColumn("Ticker"),
        "company_name": st.column_config.TextColumn("Company Name"),
        "broad_sector": st.column_config.TextColumn("Sector"),
        "composite_quality_score": st.column_config.ProgressColumn(
            "Quality Score", format="%.2f", min_value=0, max_value=100
        ),
    },
    use_container_width=True,
    height=500,
)

st.markdown("---")
st.markdown(f"*Data as of fiscal year: {selected_year}*")
