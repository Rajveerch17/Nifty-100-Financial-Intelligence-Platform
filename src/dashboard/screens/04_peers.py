"""Peer Comparison screen — radar chart and KPI table."""

import sys
from pathlib import Path

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.dashboard.utils.db import get_all_ratios
from src.analytics.peer import PeerComparisonEngine

st.markdown('<div class="main-title">👥 Peer Comparison</div>', unsafe_allow_html=True)
st.markdown("---")

selected_year = st.session_state.get("selected_year", "2024-03")

peer_groups = PeerComparisonEngine.PEER_GROUPS
benchmark_companies = PeerComparisonEngine.BENCHMARK_COMPANIES

selected_group = st.selectbox("Select Peer Group", list(peer_groups.keys()), index=0)

if selected_group:
    members = peer_groups[selected_group]
    benchmark = benchmark_companies.get(selected_group)

    all_ratios = get_all_ratios(year=selected_year)
    peer_ratios = all_ratios[all_ratios["company_id"].isin(members)].copy()
    company_options = [m for m in members if m in peer_ratios["company_id"].values]

    if company_options:
        selected_company = st.selectbox("Select Company to Compare", company_options, index=0)

        st.markdown("### Radar Chart Comparison")

        radar_metrics_raw = [
            "return_on_equity_pct",
            "return_on_capital_employed_pct",
            "net_profit_margin_pct",
            "debt_to_equity",
            "free_cash_flow_cr",
            "pat_cagr_5yr",
            "revenue_cagr_5yr",
            "composite_quality_score",
        ]
        
        # Filter to only include metrics that exist in the dataframe
        radar_metrics = []
        for m in radar_metrics_raw:
            if m in peer_ratios.columns:
                radar_metrics.append(m)
            elif m == "return_on_capital_employed_pct" and "return_on_capital_pct" in peer_ratios.columns:
                # Use return_on_capital_pct as fallback
                if "return_on_capital_pct" not in radar_metrics:
                    radar_metrics.append("return_on_capital_pct")
        
        if not radar_metrics:
            st.error("No radar metrics available for this peer group")
            st.stop()
        # Create dynamic axis labels based on actual metrics
        axis_label_map = {
            "return_on_equity_pct": "ROE",
            "return_on_capital_pct": "ROCE",
            "return_on_capital_employed_pct": "ROCE",
            "net_profit_margin_pct": "NPM",
            "debt_to_equity": "D/E",
            "free_cash_flow_cr": "FCF",
            "pat_cagr_5yr": "PAT CAGR",
            "revenue_cagr_5yr": "Rev CAGR",
            "composite_quality_score": "Quality Score"
        }
        axis_labels = [axis_label_map.get(m, m) for m in radar_metrics]

        selected_company_data = peer_ratios[peer_ratios["company_id"] == selected_company].iloc[0]
        peer_avg = peer_ratios[radar_metrics].mean(numeric_only=True)

        def normalize_value(val, min_val, max_val):
            if pd.isna(val) or max_val == min_val:
                return 50
            return (val - min_val) / (max_val - min_val) * 100

        selected_values = []
        peer_values = []
        for metric in radar_metrics:
            min_val = peer_ratios[metric].min()
            max_val = peer_ratios[metric].max()
            selected_values.append(normalize_value(selected_company_data.get(metric), min_val, max_val))
            peer_values.append(normalize_value(peer_avg[metric], min_val, max_val))

        fig = go.Figure()
        fig.add_trace(
            go.Scatterpolar(
                r=selected_values + [selected_values[0]],
                theta=axis_labels + [axis_labels[0]],
                fill="toself",
                name=selected_company,
                line_color="#1f77b4",
            )
        )
        fig.add_trace(
            go.Scatterpolar(
                r=peer_values + [peer_values[0]],
                theta=axis_labels + [axis_labels[0]],
                fill="toself",
                name=f"{selected_group} Average",
                line_color="#ff7f0e",
            )
        )
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True, height=500)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.markdown("### Peer Group KPI Comparison")

        comparison_cols_raw = [
            "company_id", "company_name", "return_on_equity_pct",
            "return_on_capital_employed_pct", "net_profit_margin_pct",
            "debt_to_equity", "free_cash_flow_cr", "pat_cagr_5yr",
            "revenue_cagr_5yr", "composite_quality_score",
        ]
        
        # Use available columns only, with fallback for ROCE
        comparison_cols = ["company_id"]
        if "company_name" in peer_ratios.columns:
            comparison_cols.append("company_name")
        
        for col in comparison_cols_raw[2:]:
            if col in peer_ratios.columns:
                comparison_cols.append(col)
            elif col == "return_on_capital_employed_pct" and "return_on_capital_pct" in peer_ratios.columns:
                if "return_on_capital_pct" not in comparison_cols:
                    comparison_cols.append("return_on_capital_pct")
        
        comparison_df = peer_ratios[comparison_cols].copy()

        def highlight_benchmark(row):
            if row["company_id"] == benchmark:
                return ["background-color: #FFD700"] * len(row)
            if row["company_id"] == selected_company:
                return ["background-color: #D9E8F5"] * len(row)
            return [""] * len(row)

        st.dataframe(comparison_df.style.apply(highlight_benchmark, axis=1), use_container_width=True)
        st.markdown(f"*🏆 Benchmark: {benchmark}*")
        st.markdown(f"*🔵 Selected: {selected_company}*")
    else:
        st.warning(f"No ratio data available for peer group {selected_group} in year {selected_year}")

    st.markdown("---")
    st.markdown(f"*Data as of fiscal year: {selected_year}*")
