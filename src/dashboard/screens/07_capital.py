"""Capital Allocation Map — treemap by allocation pattern."""

import sys
from pathlib import Path

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import plotly.express as px
from src.dashboard.utils.db import get_all_ratios

st.markdown('<div class="main-title">💰 Capital Allocation Map</div>', unsafe_allow_html=True)
st.markdown("---")

selected_year = st.session_state.get("selected_year", "2024-03")
ratios = get_all_ratios(year=selected_year)

CAPITAL_PATTERNS = {
    "High CapEx Growth": lambda row: (
        str(row.get("capex_intensity_classification", "")).lower() == "high"
        and pd.notna(row.get("revenue_cagr_5yr"))
        and row["revenue_cagr_5yr"] > 10
    ),
    "Dividend Aristocrat": lambda row: (
        pd.notna(row.get("dividend_yield_pct"))
        and row["dividend_yield_pct"] > 2
        and pd.notna(row.get("free_cash_flow_cr"))
        and row["free_cash_flow_cr"] > 0
    ),
    "Debt-Funded Growth": lambda row: (
        pd.notna(row.get("debt_to_equity"))
        and row["debt_to_equity"] > 1.5
        and pd.notna(row.get("revenue_cagr_5yr"))
        and row["revenue_cagr_5yr"] > 10
    ),
    "Cash Rich": lambda row: (
        pd.notna(row.get("debt_to_equity"))
        and row["debt_to_equity"] < 0.5
        and pd.notna(row.get("free_cash_flow_cr"))
        and row["free_cash_flow_cr"] > 500
    ),
    "Turnaround": lambda row: (
        pd.notna(row.get("revenue_cagr_5yr"))
        and row["revenue_cagr_5yr"] > 10
        and pd.notna(row.get("pat_cagr_5yr"))
        and row["pat_cagr_5yr"] > 20
    ),
    "Mature Cash Cow": lambda row: (
        pd.notna(row.get("revenue_cagr_5yr"))
        and row["revenue_cagr_5yr"] < 5
        and pd.notna(row.get("dividend_yield_pct"))
        and row["dividend_yield_pct"] > 2
    ),
    "High Leverage": lambda row: pd.notna(row.get("debt_to_equity")) and row["debt_to_equity"] > 2.0,
    "Balanced": lambda row: (
        pd.notna(row.get("debt_to_equity"))
        and 0.5 <= row["debt_to_equity"] <= 1.5
        and pd.notna(row.get("revenue_cagr_5yr"))
        and row["revenue_cagr_5yr"] >= 5
    ),
}

if ratios.empty:
    st.warning(f"No ratio data available for year {selected_year}")
    st.stop()

pattern_data = []
for _, row in ratios.iterrows():
    assigned_pattern = row.get("capital_allocation_pattern") or "Unclassified"

    if assigned_pattern == "Unclassified" or pd.isna(assigned_pattern):
        for pattern_name, pattern_func in CAPITAL_PATTERNS.items():
            try:
                if pattern_func(row):
                    assigned_pattern = pattern_name
                    break
            except (TypeError, KeyError):
                continue

    pattern_data.append(
        {
            "company_id": row["company_id"],
            "company_name": row.get("company_name", row["company_id"]),
            "pattern": assigned_pattern,
            "market_cap": row.get("market_cap_crore") or 100,
            "composite_score": row.get("composite_quality_score") or 50,
        }
    )

pattern_df = pd.DataFrame(pattern_data)
pattern_df["market_cap"] = pattern_df["market_cap"].fillna(100).clip(lower=1)

st.markdown("### Capital Allocation Treemap")

fig = px.treemap(
    pattern_df,
    path=["pattern", "company_name"],
    values="market_cap",
    color="composite_score",
    color_continuous_scale="RdYlGn",
    title="Companies by Capital Allocation Pattern (Size = Market Cap, Color = Quality Score)",
    hover_data=["company_id", "composite_score"],
)
fig.update_layout(height=600)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

selected_pattern = st.selectbox("Select Pattern to View Companies", sorted(pattern_df["pattern"].unique()), index=0)

if selected_pattern:
    pattern_companies = pattern_df[pattern_df["pattern"] == selected_pattern]
    st.markdown(f"### Companies in {selected_pattern}")
    st.dataframe(
        pattern_companies[["company_id", "company_name", "market_cap", "composite_score"]].round(2),
        use_container_width=True,
    )
    st.metric("Total Companies", len(pattern_companies))
    st.metric("Total Market Cap (Cr)", f"{pattern_companies['market_cap'].sum():.2f}")

st.markdown("---")
st.markdown("### Pattern Summary")
pattern_summary = (
    pattern_df.groupby("pattern")
    .agg(company_count=("company_id", "count"), total_market_cap=("market_cap", "sum"), avg_quality=("composite_score", "mean"))
    .round(2)
)
st.dataframe(pattern_summary, use_container_width=True)

st.markdown("---")
st.markdown(f"*Data as of fiscal year: {selected_year}*")
