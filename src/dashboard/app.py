"""
src/dashboard/app.py
====================
Main Streamlit entry point for Nifty 100 Analytics Dashboard.
Provides sidebar navigation to all 8 screens.
"""

import importlib.util
import sys
from pathlib import Path

import streamlit as st

# Add project root to Python path before any src.* imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Set the project root for all screen modules to use
import os
os.chdir(project_root)

SCREENS_DIR = Path(__file__).parent / "screens"

PAGES = {
    "🏠 Home": "01_home.py",
    "🏢 Company Profile": "02_profile.py",
    "🔍 Screener": "03_screener.py",
    "👥 Peer Comparison": "04_peers.py",
    "📈 Trend Analysis": "05_trends.py",
    "🏭 Sector Analysis": "06_sectors.py",
    "💰 Capital Allocation": "07_capital.py",
    "📄 Annual Reports": "08_reports.py",
}


def _load_screen(filename: str) -> None:
    screen_path = SCREENS_DIR / filename
    if not screen_path.exists():
        st.error(f"Screen file not found: {screen_path}")
        return

    spec = importlib.util.spec_from_file_location(f"dashboard_{filename}", screen_path)
    if spec is None or spec.loader is None:
        st.error(f"Could not load screen: {filename}")
        return

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .sidebar-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: #ff7f0e;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    '<div class="sidebar-title">📊 Nifty 100 Analytics</div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

st.sidebar.markdown("### Select Year")
year_options = ["2019-03", "2020-03", "2021-03", "2022-03", "2023-03", "2024-03"]
selected_year = st.sidebar.selectbox(
    "Fiscal Year",
    year_options,
    index=len(year_options) - 1,
    key="global_year_selector",
)
st.session_state["selected_year"] = selected_year

st.sidebar.markdown("---")

selected_page = st.sidebar.radio(
    "Navigate to:",
    list(PAGES.keys()),
    label_visibility="collapsed",
)

try:
    _load_screen(PAGES[selected_page])
except Exception as exc:
    st.error(f"Error loading page: {exc}")
    st.exception(exc)
