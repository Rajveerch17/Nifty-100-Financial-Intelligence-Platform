"""Sector Analysis screen — bubble chart and sector median KPIs."""

import sys
from pathlib import Path

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.dashboard.utils.db import get_sectors, get_all_ratios

st.markdown('<div class="main-title">🏭 Sector Analysis</div>', unsafe_allow_html=True)
st.markdown("---")

selected_year = st.session_state.get("selected_year", "2024-03")

sectors_df = get_sectors()
ratios = get_all_ratios(year=selected_year)

if ratios.empty:
    st.warning(f"No data available for year {selected_year}")
    st.stop()

sector_list = sorted(sectors_df["broad_sector"].dropna().unique().tolist())
selected_sector = st.selectbox("Select Sector", sector_list, index=0)

if selected_sector:
    sector_company_ids = sectors_df[sectors_df["broad_sector"] == selected_sector]["company_id"].tolist()
    sector_ratios = ratios[ratios["company_id"].isin(sector_company_ids)].copy()

    if sector_ratios.empty:
        st.warning(f"No ratio data available for sector {selected_sector} in year {selected_year}")
        st.stop()

    st.markdown("### Sector Bubble Chart (Revenue vs ROE)")

    bubble_data = sector_ratios.copy()
    if "revenue_from_operations" not in bubble_data.columns:
        bubble_data["revenue_from_operations"] = 0
    if "market_cap_crore" not in bubble_data.columns:
        bubble_data["market_cap_crore"] = 100

    bubble_data["revenue_from_operations"] = bubble_data["revenue_from_operations"].fillna(0)
    bubble_data["market_cap_crore"] = bubble_data["market_cap_crore"].fillna(100).clip(lower=1)

    fig = px.scatter(
        bubble_data,
        x="revenue_from_operations",
        y="return_on_equity_pct",
        size="market_cap_crore",
        color="sub_sector" if "sub_sector" in bubble_data.columns else "company_name",
        hover_name="company_id",
        hover_data=["company_name", "debt_to_equity", "net_profit_margin_pct"],
        title=f"Revenue vs ROE — {selected_sector}",
        labels={
            "revenue_from_operations": "Revenue (Cr)",
            "return_on_equity_pct": "ROE (%)",
            "market_cap_crore": "Market Cap (Cr)",
            "sub_sector": "Sub-sector",
        },
        size_max=50,
    )
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### Sector Median KPIs")

    kpi_metrics = [
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "composite_quality_score",
    ]
    available_kpis = [m for m in kpi_metrics if m in sector_ratios.columns]

    if available_kpis:
        sector_medians = sector_ratios[available_kpis].median(numeric_only=True)

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=[m.replace("_", " ").title() for m in available_kpis],
                y=sector_medians.values,
                marker_color="#1f77b4",
            )
        )
        fig.update_layout(xaxis_title="Metric", yaxis_title="Median Value", height=400)
        st.plotly_chart(fig, use_container_width=True)

        median_df = pd.DataFrame(
            {"Metric": [m.replace("_", " ").title() for m in available_kpis], "Median": sector_medians.values}
        )
        st.dataframe(median_df.round(2), use_container_width=True)

    st.markdown("---")
    st.markdown("### Companies in Sector")
    sector_companies = sector_ratios[["company_id", "company_name"]].drop_duplicates()
    st.dataframe(sector_companies, use_container_width=True)

    st.markdown("---")
    st.markdown(f"*Data as of fiscal year: {selected_year}*")
