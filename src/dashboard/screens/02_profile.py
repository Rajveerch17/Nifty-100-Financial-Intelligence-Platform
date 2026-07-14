"""Company Profile screen — search, KPIs, charts, pros/cons."""

import sys
from pathlib import Path

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.dashboard.utils.db import get_companies, get_ratios, get_pl, get_pros_cons

st.markdown('<div class="main-title">🏢 Company Profile</div>', unsafe_allow_html=True)
st.markdown("---")

selected_year = st.session_state.get("selected_year", "2024-03")

companies = get_companies()
company_options = companies["id"].tolist()

search_query = st.text_input("Search Company (Ticker or Name)", placeholder="Type ticker or company name...")

if search_query:
    mask = (
        companies["id"].str.contains(search_query, case=False, na=False)
        | companies["company_name"].str.contains(search_query, case=False, na=False)
    )
    filtered = companies[mask]
    if filtered.empty:
        st.error("Ticker not found — please try another")
        st.stop()
    company_options = filtered["id"].tolist()

selected_ticker = st.selectbox(
    "Select Company",
    options=company_options,
    format_func=lambda x: f"{x} - {companies.loc[companies['id'] == x, 'company_name'].iloc[0]}",
    index=0,
)

if selected_ticker:
    company_info = companies[companies["id"] == selected_ticker].iloc[0]
    ratios = get_ratios(selected_ticker, year=selected_year)
    pl_data = get_pl(selected_ticker)
    pros_cons = get_pros_cons(selected_ticker)

    st.markdown("### Company Information")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Company Name", company_info["company_name"])
        st.metric("NSE Ticker", selected_ticker)

    with col2:
        st.metric("Sector", company_info.get("broad_sector") or "N/A")
        st.metric("Sub-sector", company_info.get("sub_sector") or "N/A")

    with col3:
        about = company_info.get("about_company") or "No description available"
        st.info(about[:200] + "..." if len(str(about)) > 200 else about)

    st.markdown("---")
    st.markdown("### Key Performance Indicators")

    if not ratios.empty:
        latest = ratios.iloc[0]

        def fmt(val, suffix=""):
            return f"{val:.2f}{suffix}" if pd.notna(val) else "N/A"

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("ROE", fmt(latest.get("return_on_equity_pct"), "%"))
        c2.metric("ROCE", fmt(latest.get("return_on_capital_employed_pct"), "%"))
        c3.metric("Net Profit Margin", fmt(latest.get("net_profit_margin_pct"), "%"))
        c4.metric("D/E", fmt(latest.get("debt_to_equity")))
        c5.metric("Revenue CAGR 5yr", fmt(latest.get("revenue_cagr_5yr"), "%"))
        c6.metric("FCF (Cr)", fmt(latest.get("free_cash_flow_cr")))
    else:
        st.warning(f"No ratio data available for {selected_ticker} in {selected_year}")

    st.markdown("---")
    st.markdown("### 10-Year Revenue & Net Profit Trend")

    if not pl_data.empty and len(pl_data) >= 2:
        pl_sorted = pl_data.sort_values("year").tail(10)
        fig = go.Figure()
        fig.add_trace(
            go.Bar(x=pl_sorted["year"], y=pl_sorted["revenue_from_operations"], name="Revenue", marker_color="#1f77b4")
        )
        fig.add_trace(
            go.Bar(x=pl_sorted["year"], y=pl_sorted["net_profit"], name="Net Profit", marker_color="#ff7f0e")
        )
        fig.update_layout(barmode="group", xaxis_title="Fiscal Year", yaxis_title="Amount (Cr)", height=450)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient P&L data for 10-year trend")

    st.markdown("---")
    st.markdown("### ROE & ROCE Trend (10 Years)")

    all_ratios = get_ratios(selected_ticker)
    if not all_ratios.empty and len(all_ratios) >= 2:
        trend = all_ratios.sort_values("year").tail(10)
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=trend["year"], y=trend["return_on_equity_pct"], name="ROE", mode="lines+markers", line=dict(color="#1f77b4", width=3))
        )
        fig.add_trace(
            go.Scatter(
                x=trend["year"],
                y=trend["return_on_capital_employed_pct"],
                name="ROCE",
                mode="lines+markers",
                line=dict(color="#ff7f0e", width=3),
                yaxis="y2",
            )
        )
        fig.update_layout(
            xaxis_title="Fiscal Year",
            yaxis_title="ROE (%)",
            yaxis2=dict(title="ROCE (%)", overlaying="y", side="right"),
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient ratio data for ROE/ROCE trend")

    st.markdown("---")
    st.markdown("### Pros & Cons")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ✅ Pros")
        if pros_cons["pros"]:
            for item in pros_cons["pros"].split(","):
                item = item.strip()
                if item:
                    st.success(item)
        elif not ratios.empty:
            latest = ratios.iloc[0]
            auto_pros = []
            if pd.notna(latest.get("return_on_equity_pct")) and latest["return_on_equity_pct"] > 15:
                auto_pros.append("High ROE (>15%)")
            if pd.notna(latest.get("debt_to_equity")) and latest["debt_to_equity"] < 1:
                auto_pros.append("Low Debt (D/E < 1)")
            if pd.notna(latest.get("revenue_cagr_5yr")) and latest["revenue_cagr_5yr"] > 10:
                auto_pros.append("Strong Growth (Revenue CAGR > 10%)")
            if pd.notna(latest.get("free_cash_flow_cr")) and latest["free_cash_flow_cr"] > 0:
                auto_pros.append("Positive FCF")
            if auto_pros:
                for pro in auto_pros:
                    st.success(pro)
            else:
                st.info("No significant pros identified")
        else:
            st.info("No pros data available")

    with col2:
        st.markdown("#### ❌ Cons")
        if pros_cons["cons"]:
            for item in pros_cons["cons"].split(","):
                item = item.strip()
                if item:
                    st.error(item)
        elif not ratios.empty:
            latest = ratios.iloc[0]
            auto_cons = []
            if pd.notna(latest.get("return_on_equity_pct")) and latest["return_on_equity_pct"] < 10:
                auto_cons.append("Low ROE (<10%)")
            if pd.notna(latest.get("debt_to_equity")) and latest["debt_to_equity"] > 2:
                auto_cons.append("High Debt (D/E > 2)")
            if pd.notna(latest.get("revenue_cagr_5yr")) and latest["revenue_cagr_5yr"] < 5:
                auto_cons.append("Weak Growth (Revenue CAGR < 5%)")
            if pd.notna(latest.get("free_cash_flow_cr")) and latest["free_cash_flow_cr"] < 0:
                auto_cons.append("Negative FCF")
            if auto_cons:
                for con in auto_cons:
                    st.error(con)
            else:
                st.info("No significant cons identified")
        else:
            st.info("No cons data available")

    st.markdown("---")
    st.markdown(f"*Data as of fiscal year: {selected_year}*")
else:
    st.info("Please select a company to view its profile")
