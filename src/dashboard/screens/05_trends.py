"""Trend Analysis screen — multi-metric overlay with YoY annotations."""

import sys
from pathlib import Path

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.dashboard.utils.db import get_companies, get_ratios, get_pl

st.markdown('<div class="main-title">📈 Trend Analysis</div>', unsafe_allow_html=True)
st.markdown("---")

companies = get_companies()
company_options = companies["id"].tolist()

selected_ticker = st.selectbox(
    "Select Company",
    company_options,
    format_func=lambda x: f"{x} - {companies.loc[companies['id'] == x, 'company_name'].iloc[0]}",
    index=0,
)

if selected_ticker:
    ratios = get_ratios(selected_ticker)
    pl_data = get_pl(selected_ticker)

    if ratios.empty and pl_data.empty:
        st.warning(f"No trend data available for {selected_ticker}")
        st.stop()

    st.markdown("### Select Metrics to Overlay")

    metric_options = [
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "composite_quality_score",
        "revenue_from_operations",
        "net_profit",
    ]

    available_metrics = []
    for metric in metric_options:
        if metric in ratios.columns or metric in pl_data.columns:
            available_metrics.append(metric)

    if not available_metrics:
        st.warning("No trend data available for this company")
        st.stop()

    default_metrics = available_metrics[: min(3, len(available_metrics))]
    selected_metrics = st.multiselect(
        "Choose up to 3 metrics to overlay",
        available_metrics,
        default=default_metrics,
        max_selections=3,
    )

    if selected_metrics:
        if len(ratios) < 10 and not pl_data.empty and len(pl_data) < 10:
            st.info(f"Note: Only {max(len(ratios), len(pl_data))} years of data available for this company.")

        st.markdown("### 10-Year Trend")
        fig = go.Figure()
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

        for i, metric in enumerate(selected_metrics):
            if metric in ratios.columns:
                data = ratios.sort_values("year").tail(10).copy()
            elif metric in pl_data.columns:
                data = pl_data.sort_values("year").tail(10).copy()
            else:
                continue

            if len(data) < 2:
                continue

            data["yoy_change"] = data[metric].pct_change() * 100

            fig.add_trace(
                go.Scatter(
                    x=data["year"],
                    y=data[metric],
                    mode="lines+markers",
                    name=metric.replace("_", " ").title(),
                    line=dict(color=colors[i % len(colors)], width=3),
                    hovertemplate="%{x}<br>%{y:.2f}<extra></extra>",
                )
            )

            for _, row in data.iterrows():
                if pd.notna(row["yoy_change"]):
                    fig.add_annotation(
                        x=row["year"],
                        y=row[metric],
                        text=f"{row['yoy_change']:.1f}%",
                        showarrow=False,
                        yshift=10,
                        font=dict(size=9, color=colors[i % len(colors)]),
                    )

        fig.update_layout(
            xaxis_title="Fiscal Year",
            yaxis_title="Value",
            hovermode="x unified",
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Historical Data")
        ratio_metrics = [m for m in selected_metrics if m in ratios.columns]
        pl_metrics = [m for m in selected_metrics if m in pl_data.columns]

        if ratio_metrics:
            display_data = ratios[["year"] + ratio_metrics].sort_values("year").tail(10)
        elif pl_metrics:
            display_data = pl_data[["year"] + pl_metrics].sort_values("year").tail(10)
        else:
            display_data = pd.DataFrame()

        if not display_data.empty:
            st.dataframe(display_data.round(2), use_container_width=True)
    else:
        st.warning("Please select at least one metric to display")

    st.markdown("---")
    st.markdown("*YoY % change shown as annotations on each data point*")
else:
    st.info("Please select a company to view trend analysis")
