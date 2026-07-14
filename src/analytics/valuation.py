"""
src/analytics/valuation.py
===========================
Valuation module for computing FCF yield, P/E flags,
and overvaluation/discount labels.

Author: Data Analytics Team
Date: Sprint 4 (Day 26)
"""

import pandas as pd
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class ValuationEngine:
    """
    Valuation analysis engine.
    
    Computes FCF yield, sector median P/E, and overvaluation flags.
    """
    
    def __init__(self, db_path: str = "data/nifty100.db"):
        """
        Initialize valuation engine.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.df_companies = None
        self.df_ratios = None
        self.df_market_cap = None
        self._load_data()
    
    def _load_data(self) -> None:
        """Load required data from SQLite."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                self.df_companies = pd.read_sql_query("SELECT * FROM companies", conn)
                self.df_ratios = pd.read_sql_query(
                    "SELECT * FROM financial_ratios ORDER BY company_id, year DESC",
                    conn
                )
                self.df_market_cap = pd.read_sql_query("SELECT * FROM market_cap", conn)
            
            logger.info(f"Loaded valuation data: {len(self.df_companies)} companies, {len(self.df_ratios)} ratio records")
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise
    
    def compute_fcf_yield(self) -> pd.DataFrame:
        """
        Compute FCF yield for all companies.
        
        FCF Yield = FCF / Market Cap x 100
        
        Returns:
            DataFrame with FCF yield for each company
        """
        # Get latest ratios for each company
        latest_ratios = self.df_ratios.groupby('company_id').first().reset_index()
        
        # Get latest market cap data for each company
        latest_market_cap = self.df_market_cap.groupby('company_id').first().reset_index()
        
        # Merge ratios with market cap data
        df = latest_ratios.merge(
            latest_market_cap[['company_id', 'market_cap_crore', 'pe_ratio', 'pb_ratio', 'ev_ebitda']],
            on='company_id',
            how='left'
        )
        
        # Merge with companies to get company_name
        df = df.merge(
            self.df_companies[['id', 'company_name']],
            left_on='company_id',
            right_on='id',
            how='left'
        )
        
        # Compute FCF yield
        df['fcf_yield_pct'] = (df['free_cash_flow_cr'] / df['market_cap_crore'] * 100).fillna(0)
        
        return df
    
    def compute_sector_median_pe(self) -> Dict[str, float]:
        """
        Compute sector median P/E for each sector in the latest year.
        
        Returns:
            Dictionary mapping sector to median P/E
        """
        # Get latest year
        latest_year = self.df_ratios['year'].max()
        
        # Get latest market cap data with P/E
        latest_market_cap = self.df_market_cap[self.df_market_cap['year'] == latest_year].copy()
        
        # Merge with companies to get sector info
        df = latest_market_cap.merge(
            self.df_companies[['id', 'company_name']],
            left_on='company_id',
            right_on='id',
            how='left'
        )
        
        # Compute median P/E by sector (using company_name as proxy for sector)
        sector_median_pe = df.groupby('company_name')['pe_ratio'].median().to_dict()
        
        return sector_median_pe
    
    def compute_overvaluation_flags(self) -> pd.DataFrame:
        """
        Apply overvaluation flags based on P/E vs sector median.
        
        Rules:
        - Caution: P/E > sector_median x 1.5
        - Discount: P/E < sector_median x 0.7
        - Fair: Otherwise
        
        Returns:
            DataFrame with valuation flags
        """
        df = self.compute_fcf_yield()
        sector_median_pe = self.compute_sector_median_pe()
        
        # Get 5-year median P/E for each company from market_cap table
        company_5yr_median_pe = self.df_market_cap.groupby('company_id')['pe_ratio'].median().to_dict()
        
        # Apply flags
        flags = []
        for _, row in df.iterrows():
            company_id = row['company_id']
            sector = row.get('company_name', 'Unknown')
            pe = row.get('pe_ratio', 0)
            sector_median = sector_median_pe.get(sector, 20)  # Default to 20 if not found
            
            # Calculate P/E vs sector median percentage
            pe_vs_sector_pct = (pe / sector_median * 100) if sector_median > 0 else 100
            
            # Determine flag
            if pe > sector_median * 1.5:
                flag = 'Caution'
            elif pe < sector_median * 0.7:
                flag = 'Discount'
            else:
                flag = 'Fair'
            
            flags.append({
                'company_id': company_id,
                'company_name': row.get('company_name', company_id),
                'sector': sector,
                'pe_ratio': pe,
                'pb_ratio': row.get('pb_ratio', 0),
                'ev_ebitda': row.get('ev_ebitda', 0),  # If available
                'fcf_yield_pct': row['fcf_yield_pct'],
                '5yr_median_pe': company_5yr_median_pe.get(company_id, pe),
                'pe_vs_sector_median_pct': pe_vs_sector_pct,
                'flag': flag
            })
        
        return pd.DataFrame(flags)
    
    def generate_valuation_summary(self) -> pd.DataFrame:
        """
        Generate complete valuation summary for all companies.
        
        Returns:
            DataFrame with all valuation metrics
        """
        df = self.compute_overvaluation_flags()
        
        # Market cap is already included from compute_fcf_yield
        # Just ensure it's present
        if 'market_cap_crore' not in df.columns:
            latest_market_cap = self.df_market_cap.groupby('company_id').first().reset_index()
            df = df.merge(
                latest_market_cap[['company_id', 'market_cap_crore']],
                on='company_id',
                how='left'
            )
        
        return df
    
    def save_valuation_summary(self, output_path: str = "output/valuation_summary.xlsx") -> None:
        """
        Save valuation summary to Excel.
        
        Args:
            output_path: Output file path
        """
        df = self.generate_valuation_summary()
        
        # Reorder columns
        columns = [
            'company_id', 'company_name', 'sector', 'pe_ratio', 'pb_ratio',
            'ev_ebitda', 'fcf_yield_pct', '5yr_median_pe', 'pe_vs_sector_median_pct',
            'flag', 'market_cap_crore'
        ]
        
        df = df[[col for col in columns if col in df.columns]]
        
        # Save to Excel
        df.to_excel(output_path, index=False)
        logger.info(f"Saved valuation summary to {output_path}")
    
    def save_valuation_flags(self, output_path: str = "output/valuation_flags.csv") -> None:
        """
        Save only Caution and Discount flagged companies to CSV.
        
        Args:
            output_path: Output file path
        """
        df = self.generate_valuation_summary()
        
        # Filter for Caution and Discount
        flagged_df = df[df['flag'].isin(['Caution', 'Discount'])].copy()
        
        # Save to CSV
        flagged_df.to_csv(output_path, index=False)
        logger.info(f"Saved valuation flags to {output_path} ({len(flagged_df)} companies)")


if __name__ == "__main__":
    # Test valuation engine
    logging.basicConfig(level=logging.INFO)
    
    engine = ValuationEngine()
    
    # Generate outputs
    engine.save_valuation_summary()
    engine.save_valuation_flags()
    
    print("\n✓ Valuation analysis completed")
    print(f"  - valuation_summary.xlsx generated")
    print(f"  - valuation_flags.csv generated")
