"""
src/analytics/peer.py
======================
Peer group comparison and percentile ranking engine.
Computes within-group percentile ranks for 10 metrics across 11 peer groups.

Author: Data Analytics Team
Date: Sprint 3 (Day 18-20)
"""

import importlib
import logging
import pandas as pd
import numpy as np
import sqlite3
from typing import Any, Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


def _get_openpyxl_styles() -> Any:
    """Import openpyxl styles lazily to avoid editor resolution issues."""
    try:
        return importlib.import_module("openpyxl.styles")
    except Exception:
        return None


class PeerComparisonEngine:
    """
    Peer group comparison with percentile ranking.
    
    Attributes:
        db_path (str): SQLite database path
        df_ratios (pd.DataFrame): Financial ratios table
        df_peer_groups (pd.DataFrame): Peer group definitions
        peer_groups (dict): {group_name: [members]}
    """
    
    # 10 metrics for peer comparison ranking
    RANKING_METRICS = [
        'return_on_equity_pct',
        'return_on_capital_pct',
        'net_profit_margin_pct',
        'debt_to_equity',
        'free_cash_flow_cr',
        'pat_cagr_5yr',
        'revenue_cagr_5yr',
        'eps_cagr_5yr',
        'interest_coverage',
        'asset_turnover'
    ]
    
    # 11 peer groups as defined in project spec
    PEER_GROUPS = {
        'Private Banks': ['HDFCBANK', 'ICICIBANK', 'AXISBANK', 'KOTAKBANK', 'INDUSINDBK'],
        'Public Banks': ['SBIN', 'BANKBARODA', 'CANBK', 'PNB'],
        'IT Services': ['TCS', 'INFY', 'HCLTECH', 'TECHM', 'LTIM'],
        'Pharmaceuticals': ['SUNPHARMA', 'CIPLA', 'DRREDDY', 'DIVISLAB', 'TORNTPHARM'],
        'Automobiles': ['MARUTI', 'TATAMOTORS', 'M&M', 'BAJAJ-AUTO', 'EICHERMOT', 'HEROMOTOCO', 'TVSMOTOR'],
        'Life Insurance': ['LICI', 'HDFCLIFE', 'SBILIFE', 'ICICIPRULI'],
        'Oil & Gas': ['RELIANCE', 'ONGC', 'BPCL', 'IOC', 'GAIL'],
        'Power & Utilities': ['NTPC', 'POWERGRID', 'TATAPOWER', 'ADANIPOWER', 'NHPC', 'JSWENERGY', 'ADANIGREEN'],
        'Steel & Metals': ['TATASTEEL', 'JSWSTEEL', 'JINDALSTEL', 'HINDALCO'],
        'FMCG': ['HINDUNILVR', 'ITC', 'BRITANNIA', 'DABUR', 'NESTLEIND', 'GODREJCP', 'TATACONSUMER'],
        'Consumer Finance': ['BAJFINANCE', 'CHOLAFIN', 'SHRIRAMFIN']
    }
    
    # Benchmark company for each group
    BENCHMARK_COMPANIES = {
        'Private Banks': 'HDFCBANK',
        'Public Banks': 'SBIN',
        'IT Services': 'TCS',
        'Pharmaceuticals': 'SUNPHARMA',
        'Automobiles': 'MARUTI',
        'Life Insurance': 'LICI',
        'Oil & Gas': 'RELIANCE',
        'Power & Utilities': 'NTPC',
        'Steel & Metals': 'TATASTEEL',
        'FMCG': 'HINDUNILVR',
        'Consumer Finance': 'BAJFINANCE'
    }
    
    def __init__(self, db_path: str = "data/nifty100.db"):
        """
        Initialize peer comparison engine.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.df_ratios = None
        self.df_peer_groups = None
        self._load_data()
        logger.info(f"PeerComparisonEngine initialized with {len(self.PEER_GROUPS)} peer groups")
    
    def _load_data(self) -> None:
        """Load financial_ratios table from SQLite."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                self.df_ratios = pd.read_sql_query(
                    "SELECT * FROM financial_ratios ORDER BY company_id, year",
                    conn
                )

                if 'company_name' not in self.df_ratios.columns:
                    company_lookup = pd.read_sql_query(
                        "SELECT id AS company_id, company_name FROM companies",
                        conn
                    )
                    self.df_ratios = self.df_ratios.merge(
                        company_lookup,
                        on='company_id',
                        how='left'
                    )
            logger.info(f"Loaded {len(self.df_ratios)} financial ratio records")
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise

    def _has_peer_group_data(self, year: str) -> bool:
        """Check whether the configured peer groups have data for the given year."""
        if self.df_ratios is None or self.df_ratios.empty:
            return False

        df_year = self.df_ratios[self.df_ratios['year'].astype(str) == str(year)].copy()
        if df_year.empty:
            return False

        for members in self.PEER_GROUPS.values():
            if not df_year[df_year['company_id'].isin(members)].empty:
                return True

        return False

    def _resolve_year(self, year: Optional[str]) -> Optional[str]:
        """Return the latest year with data for the configured peer groups."""
        if self.df_ratios is None or self.df_ratios.empty:
            return None

        available_years = sorted(pd.unique(self.df_ratios['year'].dropna().astype(str)))
        if not available_years:
            return None

        if year is not None:
            year_str = str(year)
            if year_str in available_years and self._has_peer_group_data(year_str):
                return year_str

        for candidate in reversed(available_years):
            if self._has_peer_group_data(candidate):
                return candidate

        return available_years[-1]
    
    def compute_peer_percentiles(self, year: Optional[str] = None) -> pd.DataFrame:
        """
        Compute percentile ranks within each peer group.
        
        For each company in each peer group:
        - Rank against peer group members
        - Compute PERCENT_RANK (0-1) for each of 10 metrics
        - Handle special metrics (D/E: invert because lower is better)
        
        Args:
            year: Specific year to rank (default: latest)
        
        Returns:
            DataFrame with columns:
            [company_id, peer_group, metric, value, percentile_rank, year]
        """
        if self.df_ratios is None:
            logger.error("Financial ratios data not loaded")
            return pd.DataFrame()
        
        year = self._resolve_year(year)
        if year is None:
            logger.error("No ratio data available for peer percentile computation")
            return pd.DataFrame()
        
        logger.info(f"Computing peer percentiles for year {year}")
        
        df_year = self.df_ratios[self.df_ratios['year'] == year].copy()
        results = []
        
        for peer_group_name, members in self.PEER_GROUPS.items():
            # Filter to group members
            df_group = df_year[df_year['company_id'].isin(members)].copy()
            
            if len(df_group) == 0:
                logger.warning(f"Peer group {peer_group_name} has no data for year {year}")
                continue
            
            logger.debug(f"Ranking {len(df_group)} companies in {peer_group_name}")
            
            for metric in self.RANKING_METRICS:
                if metric not in df_group.columns:
                    logger.warning(f"Metric {metric} not found in DataFrame")
                    continue
                
                # Handle special metrics
                if metric == 'debt_to_equity':
                    # D/E: lower is better, so invert percentile rank
                    # Remove NaN values
                    df_valid = df_group[['company_id', metric]].dropna()
                    if len(df_valid) < 2:
                        continue
                    
                    # Compute percentile (normal)
                    percentiles = df_valid[metric].rank(pct=True)
                    # Invert: 1 - percentile so lower D/E = higher rank
                    percentiles = 1 - percentiles
                else:
                    # For other metrics: higher is better
                    df_valid = df_group[['company_id', metric]].dropna()
                    if len(df_valid) < 2:
                        continue
                    
                    percentiles = df_valid[metric].rank(pct=True)
                
                for idx, (company_id, percentile_rank) in enumerate(zip(df_valid['company_id'].values, percentiles.values)):
                    value = df_valid.iloc[idx][metric]
                    
                    results.append({
                        'company_id': company_id,
                        'peer_group': peer_group_name,
                        'metric': metric,
                        'value': value,
                        'percentile_rank': percentile_rank,
                        'year': year
                    })
        
        df_results = pd.DataFrame(results)
        logger.info(f"Computed {len(df_results)} peer percentile ranks")
        
        return df_results
    
    def save_to_database(self, df_percentiles: pd.DataFrame) -> None:
        """
        Save peer percentile ranks to SQLite database.
        
        Args:
            df_percentiles: DataFrame with percentile ranks
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Drop existing table if present
                conn.execute("DROP TABLE IF EXISTS peer_percentiles")
                
                # Create and populate table
                df_percentiles.to_sql(
                    'peer_percentiles',
                    conn,
                    if_exists='replace',
                    index=False
                )
                
                # Create index
                conn.execute(
                    "CREATE INDEX idx_peer_percentiles ON peer_percentiles (company_id, peer_group, year)"
                )
            
            logger.info("Saved peer_percentiles table to SQLite")
        except Exception as e:
            logger.error(f"Failed to save to database: {e}")
            raise
    
    def generate_peer_comparison_excel(self, year: Optional[str] = None, 
                                       output_path: str = "output/peer_comparison.xlsx") -> None:
        """
        Generate peer comparison Excel file.
        
        Creates 11 sheets (one per peer group) with:
        - All companies in group
        - 10 ranking metrics with values
        - Percentile ranks (colour-coded)
        - Benchmark company highlighted
        - Summary statistics row
        
        Args:
            year: Specific year (default: latest)
            output_path: Output file path
        """
        if self.df_ratios is None:
            logger.error("Financial ratios data not loaded")
            return
        
        year = self._resolve_year(year)
        if year is None:
            logger.error("No ratio data available for Excel generation")
            return
        
        logger.info(f"Generating peer comparison Excel for year {year}")
        
        df_year = self.df_ratios[self.df_ratios['year'] == year].copy()
        
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                
                for peer_group_name, members in self.PEER_GROUPS.items():
                    # Filter to group members
                    df_group = df_year[df_year['company_id'].isin(members)].copy()
                    
                    if len(df_group) == 0:
                        logger.warning(f"Skipping empty peer group: {peer_group_name}")
                        continue
                    
                    # Build comparison table
                    df_comparison = df_group[['company_id', 'company_name'] + self.RANKING_METRICS].copy()
                    
                    # Reorder columns: company info + metrics
                    df_comparison = df_comparison[
                        ['company_id', 'company_name'] + self.RANKING_METRICS
                    ]
                    
                    # Add percentile rank columns
                    for metric in self.RANKING_METRICS:
                        if metric == 'debt_to_equity':
                            percentiles = 1 - df_group[metric].rank(pct=True)
                        else:
                            percentiles = df_group[metric].rank(pct=True)
                        
                        df_comparison[f'{metric}_pct_rank'] = percentiles
                    
                    # Add summary row (median of group)
                    summary_row: Dict = {'company_id': 'PEER_MEDIAN', 'company_name': 'Peer Median'}
                    for metric in self.RANKING_METRICS:
                        summary_row[metric] = float(df_group[metric].median())  # type: ignore
                        summary_row[f'{metric}_pct_rank'] = 0.5  # Median = 50th percentile
                    
                    df_comparison = pd.concat([
                        df_comparison,
                        pd.DataFrame([summary_row])
                    ], ignore_index=True)
                    
                    # Write to Excel
                    sheet_name = peer_group_name[:31]  # Excel sheet name limit
                    df_comparison.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Format header
                    openpyxl_styles = _get_openpyxl_styles()
                    if openpyxl_styles is None:
                        raise ImportError("openpyxl is required to style Excel output")

                    worksheet = writer.sheets[sheet_name]
                    PatternFill = getattr(openpyxl_styles, "PatternFill")
                    Font = getattr(openpyxl_styles, "Font")
                    header_fill = PatternFill(start_color="D9E8F5", end_color="D9E8F5", fill_type="solid")
                    header_font = Font(bold=True)
                    
                    for col_num in range(1, len(df_comparison.columns) + 1):
                        cell = worksheet.cell(row=1, column=col_num)
                        cell.fill = header_fill
                        cell.font = header_font
                    
                    # Highlight benchmark company with gold background
                    benchmark = self.BENCHMARK_COMPANIES[peer_group_name]
                    openpyxl_styles = _get_openpyxl_styles()
                    PatternFill = getattr(openpyxl_styles, "PatternFill")
                    benchmark_fill = PatternFill(start_color="FFD700", end_color="FFD700", fill_type="solid")
                    
                    for row_num, row in enumerate(df_comparison.values, start=2):
                        if row[0] == benchmark:
                            for col_num in range(1, len(df_comparison.columns) + 1):
                                cell = worksheet.cell(row=row_num, column=col_num)
                                cell.fill = benchmark_fill
                    
                    # Colour-code percentile columns
                    openpyxl_styles = _get_openpyxl_styles()
                    PatternFill = getattr(openpyxl_styles, "PatternFill")
                    green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                    yellow_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
                    red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                    
                    for col_num, col_name in enumerate(df_comparison.columns, start=1):
                        if '_pct_rank' in col_name:
                            for row_num, value in enumerate(df_comparison[col_name].values, start=2):
                                if pd.isna(value):
                                    continue
                                cell = worksheet.cell(row=row_num, column=col_num)
                                if value >= 0.75:
                                    cell.fill = green_fill
                                elif value >= 0.25:
                                    cell.fill = yellow_fill
                                else:
                                    cell.fill = red_fill
            
            logger.info(f"Generated peer comparison Excel: {output_path}")
        except Exception as e:
            logger.error(f"Failed to generate Excel: {e}")
            raise


if __name__ == "__main__":
    # Test the peer comparison engine
    logging.basicConfig(level=logging.INFO)
    
    engine = PeerComparisonEngine()
    
    # Compute and save percentiles
    df_percentiles = engine.compute_peer_percentiles()
    engine.save_to_database(df_percentiles)
    
    # Generate Excel report
    engine.generate_peer_comparison_excel()
    
    print(f"\n[OK] Peer comparison completed")
    print(f"  - {len(df_percentiles)} percentile ranks computed")
    print(f"  - 11 peer groups ranked across 10 metrics")
    print(f"  - Generated: output/peer_comparison.xlsx")
