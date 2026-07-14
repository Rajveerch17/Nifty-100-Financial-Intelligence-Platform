"""Home screen — summary KPIs, sector donut, top-5 quality score table."""

import sys
from pathlib import Path

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import plotly.express as px
from src.dashboard.utils.db import get_companies, get_all_ratios

st.markdown('<div class="main-title">📊 Dashboard Home</div>', unsafe_allow_html=True)
st.markdown("---")

selected_year = st.session_state.get("selected_year", "2024-03")

companies = get_companies()
ratios = get_all_ratios(year=selected_year)

st.markdown("### Summary Metrics")
col1, col2, col3, col4, col5, col6 = st.columns(6)

if not ratios.empty:
    avg_roe = ratios["return_on_equity_pct"].mean()
    median_pe = ratios["pe_ratio"].median() if "pe_ratio" in ratios.columns else None
    median_de = ratios["debt_to_equity"].median()
    total_companies = ratios["company_id"].nunique()
    median_revenue_cagr = ratios["revenue_cagr_5yr"].median()
    debt_free_count = len(ratios[ratios["debt_to_equity"].fillna(999) == 0])

    col1.metric("Average ROE", f"{avg_roe:.2f}%" if pd.notna(avg_roe) else "N/A")
    col2.metric("Median P/E", f"{median_pe:.2f}x" if pd.notna(median_pe) else "N/A")
    col3.metric("Median D/E", f"{median_de:.2f}" if pd.notna(median_de) else "N/A")
    col4.metric("Total Companies", total_companies)
    col5.metric("Median Revenue CAGR 5yr", f"{median_revenue_cagr:.2f}%" if pd.notna(median_revenue_cagr) else "N/A")
    col6.metric("Debt-Free Companies", debt_free_count)
else:
    st.warning(f"No ratio data available for {selected_year}")

st.markdown("---")

st.markdown("### Sector Breakdown")
col1, col2 = st.columns([1, 2])

with col1:
    if "broad_sector" in companies.columns and companies["broad_sector"].notna().any():
        sector_counts = (
            companies.dropna(subset=["broad_sector"])
            .groupby("broad_sector")
            .size()
            .reset_index(name="Count")
        )
        fig = px.pie(
            sector_counts,
            values="Count",
            names="broad_sector",
            title="Company Count by Sector",
            hole=0.4,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sector data not available")

with col2:
    st.markdown("#### Sector Statistics")
    if not ratios.empty and "broad_sector" in ratios.columns:
        sector_stats = (
            ratios.groupby("broad_sector")
            .agg(
                avg_roe=("return_on_equity_pct", "mean"),
                median_de=("debt_to_equity", "median"),
                median_rev_cagr=("revenue_cagr_5yr", "median"),
                company_count=("company_id", "count"),
            )
            .round(2)
        )
        st.dataframe(sector_stats, use_container_width=True)

st.markdown("---")

st.markdown("### Top 5 Companies by Composite Quality Score")
if not ratios.empty and "composite_quality_score" in ratios.columns:
    top_companies = ratios.nlargest(5, "composite_quality_score")[
        [
            "company_id",
            "company_name",
            "composite_quality_score",
            "return_on_equity_pct",
            "debt_to_equity",
            "revenue_cagr_5yr",
        ]
    ].round(2)

    st.dataframe(
        top_companies,
        column_config={
            "company_id": st.column_config.TextColumn("Ticker"),
            "company_name": st.column_config.TextColumn("Company Name"),
            "composite_quality_score": st.column_config.ProgressColumn(
                "Quality Score", format="%.2f", min_value=0, max_value=100
            ),
            "return_on_equity_pct": st.column_config.NumberColumn("ROE (%)", format="%.2f"),
            "debt_to_equity": st.column_config.NumberColumn("D/E", format="%.2f"),
            "revenue_cagr_5yr": st.column_config.NumberColumn("Revenue CAGR 5yr (%)", format="%.2f"),
        },
        use_container_width=True,
    )
else:
    st.warning("Composite quality score not available in data")

st.markdown("---")
st.markdown(f"*Data as of fiscal year: {selected_year}*")
