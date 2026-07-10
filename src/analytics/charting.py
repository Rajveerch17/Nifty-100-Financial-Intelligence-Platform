"""
src/analytics/charting.py
==========================
Chart generation utilities for peer comparison and analysis.
Generates radar charts, polar plots, and comparative visualizations.

Author: Data Analytics Team
Date: Sprint 3 (Day 19)
"""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RadarChartGenerator:
    """
    Generate radar/polar charts for peer group comparisons.
    
    Features:
    - 8-axis radar chart showing company vs peer average
    - Filled polygon for company, dashed overlay for peer group
    - Readable font sizes and automatic scaling
    - PNG export at 300 DPI
    """
    
    # 8 metrics for radar chart
    RADAR_METRICS = [
        'return_on_equity_pct',
        'return_on_capital_pct',
        'net_profit_margin_pct',
        'debt_to_equity',
        'free_cash_flow_cr',
        'pat_cagr_5yr',
        'revenue_cagr_5yr',
        'composite_quality_score'
    ]
    
    # Axis labels (shorter names for clarity)
    AXIS_LABELS = [
        'ROE',
        'ROCE',
        'NPM',
        'D/E',
        'FCF',
        'PAT CAGR',
        'Rev CAGR',
        'Quality Score'
    ]
    
    def __init__(self, db_path: str = "data/nifty100.db"):
        """
        Initialize radar chart generator.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.df_ratios = None
        self.df_peer_percentiles = None
        self._load_data()
    
    def _load_data(self) -> None:
        """Load required data from SQLite."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                self.df_ratios = pd.read_sql_query(
                    "SELECT * FROM financial_ratios",
                    conn
                )
                # Try to load peer percentiles if they exist
                try:
                    self.df_peer_percentiles = pd.read_sql_query(
                        "SELECT * FROM peer_percentiles",
                        conn
                    )
                except:
                    self.df_peer_percentiles = None
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise
    
    def normalise_metrics(self, df: pd.DataFrame, year: Optional[str] = None) -> pd.DataFrame:
        """
        Normalise metrics to 0-100 scale for radar chart visibility.
        
        Args:
            df: DataFrame with financial metrics
            year: Specific year (default: latest)
        
        Returns:
            DataFrame with normalised metrics
        """
        if year is None:
            available_years = sorted(pd.unique(df['year'].dropna().astype(str)))
            year = available_years[-1] if available_years else None
        if year is None:
            return pd.DataFrame(columns=['company_id'] + self.RADAR_METRICS)

        df_year = df[df['year'].astype(str) == str(year)].copy()
        df_norm = df_year[['company_id'] + self.RADAR_METRICS].copy()
        
        # Normalise each metric to 0-100 using P10/P90 winsorisation
        for metric in self.RADAR_METRICS:
            if metric not in df_norm.columns:
                logger.warning(f"Metric {metric} not found in DataFrame")
                continue
            
            values = df_year[metric].dropna()
            p10 = values.quantile(0.10)
            p90 = values.quantile(0.90)
            
            if p90 == p10:
                df_norm[metric] = 50  # Constant value
            else:
                # Winsorise and scale to 0-100
                winsorised = df_year[metric].clip(p10, p90)
                df_norm[metric] = ((winsorised - p10) / (p90 - p10) * 100).fillna(50)
        
        return df_norm
    
    def generate_radar_chart(self, company_id: str, peer_group: Optional[str] = None,
                            year: Optional[str] = None, output_dir: str = "reports/radar_charts") -> Optional[str]:
        """
        Generate radar chart for a single company.
        
        Args:
            company_id: NSE ticker symbol
            peer_group: Peer group name (if available)
            year: Specific year (default: latest)
            output_dir: Output directory for PNG
        
        Returns:
            Path to generated PNG file
        """
        if self.df_ratios is None:
            logger.error("Financial ratios data not loaded")
            return None
        
        if year is None:
            year = self.df_ratios['year'].max()
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Get company data
        company_data = self.df_ratios[
            (self.df_ratios['company_id'] == company_id) & 
            (self.df_ratios['year'] == year)
        ]
        
        if company_data.empty:
            logger.warning(f"No data found for {company_id} in {year}")
            return None
        
        # Normalise metrics
        df_norm = self.normalise_metrics(self.df_ratios, year)
        company_norm = df_norm[df_norm['company_id'] == company_id].iloc[0]
        
        # Get company values for radar
        values = [company_norm.get(metric, 50) for metric in self.RADAR_METRICS]
        
        # Calculate peer average if peer group provided
        peer_values = None
        if peer_group and self.df_peer_percentiles is not None:
            peer_data = self.df_peer_percentiles[
                (self.df_peer_percentiles['peer_group'] == peer_group) &
                (self.df_peer_percentiles['year'] == year)
            ]
            
            if not peer_data.empty:
                # Get peer group members and their values
                peer_members = peer_data['company_id'].unique()
                peer_norm = df_norm[df_norm['company_id'].isin(peer_members)]
                
                peer_values = []
                for metric in self.RADAR_METRICS:
                    peer_avg = peer_norm[metric].mean()
                    peer_values.append(peer_avg)
        
        # Generate radar chart
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        # Number of variables
        num_vars = len(self.RADAR_METRICS)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        values += values[:1]  # Complete the circle
        angles += angles[:1]
        
        # Plot company values
        ax.plot(angles, values, 'o-', linewidth=2.5, color='#1f77b4', label=company_id, markersize=8)
        ax.fill(angles, values, alpha=0.25, color='#1f77b4')
        
        # Plot peer average if available
        if peer_values:
            peer_values += peer_values[:1]
            ax.plot(angles, peer_values, 'o--', linewidth=2, color='#ff7f0e', 
                   label=f'{peer_group} Average', markersize=6)
            ax.fill(angles, peer_values, alpha=0.10, color='#ff7f0e')
        
        # Customise chart
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(self.AXIS_LABELS, size=11, weight='bold')
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'], size=9)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Title and legend
        title = f"{company_id} - Peer Comparison ({year})"
        if peer_group:
            title += f"\n{peer_group}"
        
        ax.set_title(title, size=14, weight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)
        
        # Save figure
        output_path = Path(output_dir) / f"{company_id}_radar.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.debug(f"Generated radar chart: {output_path}")
        return str(output_path)
    
    def generate_all_radar_charts(self, peer_groups: Optional[Dict[str, List[str]]] = None,
                                  year: Optional[str] = None, 
                                  output_dir: str = "reports/radar_charts") -> Dict[str, str]:
        """
        Generate radar charts for all companies in peer groups.
        
        Args:
            peer_groups: {group_name: [members]}. If None, uses all companies
            year: Specific year (default: latest)
            output_dir: Output directory
        
        Returns:
            Dict of {company_id: output_path}
        """
        if self.df_ratios is None:
            logger.error("Financial ratios data not loaded")
            return {}
        
        if year is None:
            year = self.df_ratios['year'].max()
        
        results = {}
        total_companies = 0
        
        if peer_groups is None:
            # Generate for all companies
            companies = self.df_ratios[self.df_ratios['year'] == year]['company_id'].unique()
            for company_id in companies:
                try:
                    path = self.generate_radar_chart(company_id, year=year, output_dir=output_dir)
                    if path:
                        results[company_id] = path
                        total_companies += 1
                except Exception as e:
                    logger.error(f"Failed to generate chart for {company_id}: {e}")
        else:
            # Generate for peer group members
            for peer_group, members in peer_groups.items():
                for company_id in members:
                    try:
                        path = self.generate_radar_chart(
                            company_id, 
                            peer_group=peer_group,
                            year=year,
                            output_dir=output_dir
                        )
                        if path:
                            results[company_id] = path
                            total_companies += 1
                    except Exception as e:
                        logger.error(f"Failed to generate chart for {company_id}: {e}")
        
        logger.info(f"Generated {total_companies} radar charts")
        return results


if __name__ == "__main__":
    # Test radar chart generation
    logging.basicConfig(level=logging.INFO)
    
    from src.analytics.peer import PeerComparisonEngine
    
    # Load peer groups from comparison engine
    peer_engine = PeerComparisonEngine()
    peer_groups = PeerComparisonEngine.PEER_GROUPS
    
    # Generate charts
    chart_gen = RadarChartGenerator()
    results = chart_gen.generate_all_radar_charts(peer_groups=peer_groups)
    
    print(f"\n✓ Generated {len(results)} radar charts")
