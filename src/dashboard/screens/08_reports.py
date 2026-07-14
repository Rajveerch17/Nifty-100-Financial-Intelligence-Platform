"""Annual Reports screen — BSE PDF links from documents table."""

import sys
from pathlib import Path

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import requests
from src.dashboard.utils.db import get_companies, get_documents

st.markdown('<div class="main-title">📄 Annual Reports</div>', unsafe_allow_html=True)
st.markdown("---")

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
    company_options,
    format_func=lambda x: f"{x} - {companies.loc[companies['id'] == x, 'company_name'].iloc[0]}",
    index=0,
)

if selected_ticker:
    company_info = companies[companies["id"] == selected_ticker].iloc[0]
    st.markdown(f"### {company_info['company_name']} ({selected_ticker})")

    documents = get_documents(selected_ticker)

    if documents.empty:
        st.warning(f"No annual reports found in database for {selected_ticker}")
    else:
        st.markdown("### Available Annual Reports")

        available_count = 0
        for _, row in documents.iterrows():
            year = row["year"]
            url = row["annual_report"]

            col1, col2, col3 = st.columns([1, 3, 2])

            with col1:
                st.markdown(f"**{year}**")

            with col2:
                if pd.notna(url) and str(url).startswith("http"):
                    st.markdown(f"[📄 Download BSE Report]({url})")
                else:
                    st.markdown("📄 Report unavailable")

            with col3:
                if pd.notna(url) and str(url).startswith("http"):
                    try:
                        response = requests.head(url, timeout=5, allow_redirects=True)
                        if response.status_code < 400:
                            st.success("✓ Available")
                            available_count += 1
                        else:
                            st.error("✗ Unavailable")
                    except requests.RequestException:
                        st.error("✗ Unavailable")
                else:
                    st.error("✗ Unavailable")

            st.markdown("---")

        st.metric("Available Reports", available_count)
        st.metric("Total Years", len(documents))

    st.markdown("---")
    st.markdown(
        "*Reports are sourced from BSE India via the documents database. "
        "If a report shows as unavailable, the link may be broken or the file may have moved.*"
    )
else:
    st.info("Please select a company to view annual reports")
