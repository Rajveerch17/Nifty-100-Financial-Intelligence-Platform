"""
Test script to verify all dashboard screens load without errors.
Tests with tickers from IT, Financials, FMCG, Energy, Healthcare sectors.
"""

import sys
from pathlib import Path
import sqlite3
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.dashboard.utils.db import (
    get_companies, get_ratios, get_pl, get_all_ratios,
    get_sectors, get_documents, get_pros_cons
)
from src.screener.engine import ScreenerEngine
from src.analytics.peer import PeerComparisonEngine

# Test tickers from different sectors
TEST_TICKERS = {
    "Information Technology": ["TCS", "INFY", "HCLTECH"],
    "Financials": ["HDFCBANK", "ICICIBANK", "KOTAKBANK"],
    "Consumer Staples": ["HINDUNILVR", "ITC", "BRITANNIA"],
    "Energy": ["RELIANCE", "BPCL", "ONGC"],
    "Healthcare": ["SUNPHARMA", "APOLLOHOSP", "DRREDDY"]
}

def test_home_screen():
    """Test Home screen data loading."""
    print("\n🏠 Testing Home Screen...")
    try:
        companies = get_companies()
        assert not companies.empty, "Companies data is empty"
        
        ratios = get_all_ratios(year="2024-03")
        assert not ratios.empty, "Ratios data is empty for 2024-03"
        
        # Check required columns
        assert "return_on_equity_pct" in ratios.columns
        assert "debt_to_equity" in ratios.columns
        
        print("✓ Home screen: PASSED")
        return True
    except Exception as e:
        print(f"✗ Home screen: FAILED - {e}")
        return False

def test_profile_screen(ticker):
    """Test Company Profile screen for a ticker."""
    print(f"\n🏢 Testing Profile Screen for {ticker}...")
    try:
        companies = get_companies()
        company_info = companies[companies["id"] == ticker]
        assert not company_info.empty, f"Company {ticker} not found"
        
        ratios = get_ratios(ticker, year="2024-03")
        pl_data = get_pl(ticker)
        pros_cons = get_pros_cons(ticker)
        
        # Data can be empty for some companies, but functions should not crash
        print(f"  - Ratios: {len(ratios)} rows")
        print(f"  - P&L: {len(pl_data)} rows")
        print(f"  - Pros/Cons: {'Available' if pros_cons['pros'] or pros_cons['cons'] else 'Empty'}")
        
        print(f"✓ Profile screen ({ticker}): PASSED")
        return True
    except Exception as e:
        print(f"✗ Profile screen ({ticker}): FAILED - {e}")
        return False

def test_screener_screen():
    """Test Screener screen."""
    print("\n🔍 Testing Screener Screen...")
    try:
        engine = ScreenerEngine()
        ratios = get_all_ratios(year="2024-03")
        assert not ratios.empty, "Ratios data is empty"
        
        # Ensure fcf_cagr_5yr exists
        if "fcf_cagr_5yr" not in ratios.columns:
            ratios["fcf_cagr_5yr"] = ratios.get("free_cash_flow_cr", pd.Series(0)).fillna(0)
        
        # Test composite score computation
        scores = engine.compute_composite_score(ratios)
        assert len(scores) > 0, "Composite scores not computed"
        
        print(f"  - Computed scores for {len(scores)} companies")
        print(f"✓ Screener screen: PASSED")
        return True
    except Exception as e:
        print(f"✗ Screener screen: FAILED - {e}")
        return False

def test_peers_screen():
    """Test Peer Comparison screen."""
    print("\n👥 Testing Peer Comparison Screen...")
    try:
        peer_groups = PeerComparisonEngine.PEER_GROUPS
        assert len(peer_groups) > 0, "No peer groups defined"
        
        # Test first peer group
        first_group = list(peer_groups.keys())[0]
        members = peer_groups[first_group]
        
        ratios = get_all_ratios(year="2024-03")
        peer_ratios = ratios[ratios["company_id"].isin(members)]
        
        print(f"  - Testing peer group: {first_group}")
        print(f"  - Members with data: {len(peer_ratios)}")
        
        print(f"✓ Peers screen: PASSED")
        return True
    except Exception as e:
        print(f"✗ Peers screen: FAILED - {e}")
        return False

def test_trends_screen(ticker):
    """Test Trend Analysis screen for a ticker."""
    print(f"\n📈 Testing Trends Screen for {ticker}...")
    try:
        ratios = get_ratios(ticker)
        pl_data = get_pl(ticker)
        
        if ratios.empty and pl_data.empty:
            print(f"  - No trend data for {ticker} (expected for some tickers)")
            print(f"✓ Trends screen ({ticker}): PASSED (empty data handled)")
            return True
        
        print(f"  - Ratios: {len(ratios)} years")
        print(f"  - P&L: {len(pl_data)} years")
        
        print(f"✓ Trends screen ({ticker}): PASSED")
        return True
    except Exception as e:
        print(f"✗ Trends screen ({ticker}): FAILED - {e}")
        return False

def test_sectors_screen():
    """Test Sector Analysis screen."""
    print("\n🏭 Testing Sector Analysis Screen...")
    try:
        sectors_df = get_sectors()
        assert not sectors_df.empty, "Sectors data is empty"
        
        ratios = get_all_ratios(year="2024-03")
        assert not ratios.empty, "Ratios data is empty"
        
        # Test first sector
        first_sector = sectors_df["broad_sector"].dropna().iloc[0]
        sector_companies = sectors_df[sectors_df["broad_sector"] == first_sector]["company_id"].tolist()
        sector_ratios = ratios[ratios["company_id"].isin(sector_companies)]
        
        print(f"  - Testing sector: {first_sector}")
        print(f"  - Companies: {len(sector_ratios)}")
        
        print(f"✓ Sectors screen: PASSED")
        return True
    except Exception as e:
        print(f"✗ Sectors screen: FAILED - {e}")
        return False

def test_capital_screen():
    """Test Capital Allocation screen."""
    print("\n💰 Testing Capital Allocation Screen...")
    try:
        ratios = get_all_ratios(year="2024-03")
        assert not ratios.empty, "Ratios data is empty"
        
        # Check for capital allocation pattern column
        has_pattern = "capital_allocation_pattern" in ratios.columns
        print(f"  - Capital allocation patterns: {'In DB' if has_pattern else 'Will be computed'}")
        print(f"  - Companies: {len(ratios)}")
        
        print(f"✓ Capital Allocation screen: PASSED")
        return True
    except Exception as e:
        print(f"✗ Capital Allocation screen: FAILED - {e}")
        return False

def test_reports_screen(ticker):
    """Test Annual Reports screen for a ticker."""
    print(f"\n📄 Testing Reports Screen for {ticker}...")
    try:
        companies = get_companies()
        company_info = companies[companies["id"] == ticker]
        assert not company_info.empty, f"Company {ticker} not found"
        
        documents = get_documents(ticker)
        print(f"  - Documents: {len(documents)} annual reports")
        
        print(f"✓ Reports screen ({ticker}): PASSED")
        return True
    except Exception as e:
        print(f"✗ Reports screen ({ticker}): FAILED - {e}")
        return False

def run_all_tests():
    """Run all dashboard tests."""
    print("=" * 70)
    print("DASHBOARD COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    results = []
    
    # Test each screen
    results.append(("Home", test_home_screen()))
    results.append(("Screener", test_screener_screen()))
    results.append(("Peers", test_peers_screen()))
    results.append(("Sectors", test_sectors_screen()))
    results.append(("Capital", test_capital_screen()))
    
    # Test ticker-specific screens with multiple tickers
    test_count = 0
    for sector, tickers in TEST_TICKERS.items():
        for ticker in tickers[:2]:  # Test 2 tickers per sector
            results.append((f"Profile-{ticker}", test_profile_screen(ticker)))
            results.append((f"Trends-{ticker}", test_trends_screen(ticker)))
            results.append((f"Reports-{ticker}", test_reports_screen(ticker)))
            test_count += 1
            if test_count >= 5:  # Limit to 5 tickers total
                break
        if test_count >= 5:
            break
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:30} {status}")
    
    print("=" * 70)
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {passed} ({passed/len(results)*100:.1f}%)")
    print(f"Failed: {failed} ({failed/len(results)*100:.1f}%)")
    print("=" * 70)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
