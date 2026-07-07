"""
src/screener/engine.py
======================
Filter engine for multi-criteria financial screener.
Supports 15 metrics, 6 presets, and custom threshold combinations.

Author: Data Analytics Team
Date: Sprint 3 (Day 15-17)
"""

import logging
import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml

logger = logging.getLogger(__name__)


class ScreenerEngine:
    """
    Multi-criteria financial screener with composite scoring.
    
    Attributes:
        config (dict): Loaded YAML configuration
        df_ratios (pd.DataFrame): Financial ratios table
        df_sectors (pd.DataFrame): Sector mapping table
        db_path (str): SQLite database path
    """
    
    def __init__(self, config_path: str = "config/screener_config.yaml", 
                 db_path: str = "data/nifty100.db"):
        """
        Initialize screener engine.
        
        Args:
            config_path: Path to screener_config.yaml
            db_path: Path to SQLite database
        """
        self.config_path = config_path
        self.db_path = db_path
        self.config = self._load_config()
        self.df_ratios = None
        self.df_sectors = None
        self._load_data()
        logger.info(f"ScreenerEngine initialized with {len(self.df_ratios)} companies")
    
    def _load_config(self) -> dict:
        """Load and validate YAML configuration."""
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded screener config with {len(config['presets'])} presets")
        return config
    
    def _load_data(self) -> None:
        """Load financial_ratios and sectors tables from SQLite."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                self.df_ratios = pd.read_sql_query(
                    "SELECT * FROM financial_ratios ORDER BY company_id, year",
                    conn
                )
                self.df_sectors = pd.read_sql_query(
                    "SELECT * FROM sectors",
                    conn
                )
            logger.info(f"Loaded {len(self.df_ratios)} ratio records, {len(self.df_sectors)} companies")
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise
    
    def apply_filters(self, df: pd.DataFrame, filter_dict: Dict[str, float]) -> pd.DataFrame:
        """
        Apply one or more filters to a DataFrame.
        
        Args:
            df: Input DataFrame with financial metrics
            filter_dict: {filter_name: threshold_value, ...}
                       e.g., {"roe_min": 15, "de_max": 1.0}
        
        Returns:
            Filtered DataFrame
        """
        result = df.copy()
        
        for filter_name, threshold in filter_dict.items():
            if filter_name not in self.config['filters']:
                logger.warning(f"Unknown filter: {filter_name}")
                continue
            
            filter_def = self.config['filters'][filter_name]
            column = filter_def['column']
            operator = filter_def['operator']
            
            # Handle sector carve-outs (e.g., skip D/E for Financials)
            if 'sector_carve_out' in filter_def and filter_name in ['de_max']:
                # Add sector info
                result = result.merge(
                    self.df_sectors[['company_id', 'broad_sector']],
                    on='company_id',
                    how='left'
                )
                # Apply filter only to non-Financial companies
                if 'broad_sector' in result.columns:
                    mask = (result['broad_sector'] == 'Financials') | \
                           self._apply_operator(result[column], operator, threshold)
                    result = result[mask].drop(columns=['broad_sector'])
                else:
                    result = self._apply_filter_operator(result, column, operator, threshold)
            
            # Handle special metric handling (e.g., debt-free ICR)
            elif filter_def.get('special_handling') == 'debt_free_infinity':
                # ICR: debt-free companies (None) always pass
                if column in result.columns:
                    # Mark debt-free as 999 (always passes any minimum threshold)
                    result[column] = result[column].fillna(999)
                    result = self._apply_filter_operator(result, column, operator, threshold)
            else:
                result = self._apply_filter_operator(result, column, operator, threshold)
            
            logger.debug(f"Filter {filter_name}: {len(result)} companies remain")
        
        return result.dropna(subset=[col for col in result.columns if col in 
                                      [self.config['filters'][f]['column'] 
                                       for f in filter_dict.keys()]])
    
    def _apply_operator(self, series: pd.Series, operator: str, threshold: float) -> pd.Series:
        """Apply comparison operator and return boolean series."""
        if operator == ">=":
            return series >= threshold
        elif operator == "<=":
            return series <= threshold
        elif operator == ">":
            return series > threshold
        elif operator == "<":
            return series < threshold
        elif operator == "==":
            return series == threshold
        else:
            raise ValueError(f"Unknown operator: {operator}")
    
    def _apply_filter_operator(self, df: pd.DataFrame, column: str, 
                               operator: str, threshold: float) -> pd.DataFrame:
        """Apply filter to DataFrame and return filtered result."""
        if column not in df.columns:
            logger.warning(f"Column {column} not found in DataFrame")
            return df
        
        mask = self._apply_operator(df[column], operator, threshold)
        return df[mask]
    
    def compute_composite_score(self, df: pd.DataFrame) -> pd.Series:
        """
        Compute composite quality score (0-100 scale).
        
        Weights:
        - Profitability (35%): ROE 15% + ROCE 10% + NPM 10%
        - Cash Quality (30%): FCF CAGR 15% + CFO/PAT 10% + FCF flag 5%
        - Growth (20%): Rev CAGR 10% + PAT CAGR 10%
        - Leverage (15%): D/E score 10% + ICR score 5%
        
        Args:
            df: DataFrame with computed metrics
        
        Returns:
            Series with composite scores (0-100)
        """
        score_df = df.copy()
        
        # Normalize each metric to 0-100 using P10/P90 winsorisation
        score_df['roe_score'] = self._winsorise_and_scale(df['return_on_equity_pct'], 0, 100)
        score_df['roce_score'] = self._winsorise_and_scale(df['return_on_capital_employed_pct'], 0, 100)
        score_df['npm_score'] = self._winsorise_and_scale(df['net_profit_margin_pct'], 0, 100)
        
        score_df['fcf_cagr_score'] = self._winsorise_and_scale(df['fcf_cagr_5yr'], 0, 100)
        score_df['cfo_pat_score'] = self._winsorise_and_scale(df['cfo_pat_ratio'].fillna(0.5), 0, 100)
        score_df['fcf_flag_score'] = (df['free_cash_flow_cr'] > 0).astype(int) * 100
        
        score_df['rev_cagr_score'] = self._winsorise_and_scale(df['revenue_cagr_5yr'], 0, 100)
        score_df['pat_cagr_score'] = self._winsorise_and_scale(df['pat_cagr_5yr'], 0, 100)
        
        # D/E: lower is better (invert)
        score_df['de_score'] = 100 - self._winsorise_and_scale(df['debt_to_equity'], 0, 100)
        score_df['icr_score'] = self._winsorise_and_scale(df['interest_coverage'].fillna(10), 0, 100)
        
        # Compute weighted composite score
        profitability = (score_df['roe_score'] * 0.15 + 
                         score_df['roce_score'] * 0.10 + 
                         score_df['npm_score'] * 0.10)
        
        cash_quality = (score_df['fcf_cagr_score'] * 0.15 + 
                       score_df['cfo_pat_score'] * 0.10 + 
                       score_df['fcf_flag_score'] * 0.05)
        
        growth = (score_df['rev_cagr_score'] * 0.10 + 
                 score_df['pat_cagr_score'] * 0.10)
        
        leverage = (score_df['de_score'] * 0.10 + 
                   score_df['icr_score'] * 0.05)
        
        composite = (profitability * 0.35 + 
                    cash_quality * 0.30 + 
                    growth * 0.20 + 
                    leverage * 0.15)
        
        return composite.fillna(0).clip(0, 100)
    
    def _winsorise_and_scale(self, series: pd.Series, min_val: float = 0, 
                            max_val: float = 100) -> pd.Series:
        """
        Winsorise at P10/P90 and scale to [min_val, max_val].
        
        Args:
            series: Input series to winsorise
            min_val: Minimum scale value
            max_val: Maximum scale value
        
        Returns:
            Winsorised and scaled series
        """
        p10 = series.quantile(0.10)
        p90 = series.quantile(0.90)
        
        # Cap values at P10/P90
        winsorised = series.clip(p10, p90)
        
        # Scale to [min_val, max_val]
        scaled = min_val + (winsorised - p10) / (p90 - p10) * (max_val - min_val)
        
        return scaled.fillna((min_val + max_val) / 2)
    
    def apply_preset(self, preset_name: str, year: str = None) -> pd.DataFrame:
        """
        Apply a preset screener template.
        
        Args:
            preset_name: Name of preset (e.g., 'quality_compounder')
            year: Specific year to screen (default: latest available)
        
        Returns:
            Filtered and ranked DataFrame
        """
        if preset_name not in self.config['presets']:
            raise ValueError(f"Unknown preset: {preset_name}")
        
        preset = self.config['presets'][preset_name]
        logger.info(f"Applying preset: {preset_name}")
        
        # Get latest year if not specified
        if year is None:
            year = self.df_ratios['year'].max()
        
        df = self.df_ratios[self.df_ratios['year'] == year].copy()
        logger.info(f"Screening {len(df)} companies for year {year}")
        
        # Apply preset filters
        df = self.apply_filters(df, preset['filters'])
        logger.info(f"After filters: {len(df)} companies remain")
        
        # Compute composite score
        df['composite_quality_score'] = self.compute_composite_score(df)
        
        # Rank by specified metric
        ranking_metric = preset['ranking_metric']
        ranking_order = preset['ranking_order']
        
        ascending = ranking_order == 'ascending'
        df = df.sort_values(ranking_metric, ascending=ascending).reset_index(drop=True)
        df['rank'] = range(1, len(df) + 1)
        
        logger.info(f"Preset {preset_name}: {len(df)} companies returned")
        
        return df
    
    def generate_all_presets(self, year: str = None) -> Dict[str, pd.DataFrame]:
        """
        Generate results for all 6 preset screeners.
        
        Args:
            year: Specific year to screen
        
        Returns:
            Dict of {preset_name: results_dataframe}
        """
        results = {}
        for preset_name in self.config['presets'].keys():
            try:
                results[preset_name] = self.apply_preset(preset_name, year)
            except Exception as e:
                logger.error(f"Error applying preset {preset_name}: {e}")
        
        return results
    
    def export_to_excel(self, results: Dict[str, pd.DataFrame], 
                       output_path: str = "output/screener_output.xlsx") -> None:
        """
        Export preset results to Excel with formatting.
        
        Args:
            results: Dict of {preset_name: results_dataframe}
            output_path: Output Excel file path
        """
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for preset_name, df in results.items():
                    if df.empty:
                        logger.warning(f"Skipping empty preset: {preset_name}")
                        continue
                    
                    # Select columns for export
                    columns_to_export = [
                        'rank', 'company_id', 'company_name', 'sector',
                        'return_on_equity_pct', 'return_on_capital_employed_pct',
                        'net_profit_margin_pct', 'debt_to_equity',
                        'free_cash_flow_cr', 'fcf_cagr_5yr', 'revenue_cagr_5yr',
                        'pat_cagr_5yr', 'pe_ratio', 'pb_ratio', 'dividend_yield_pct',
                        'interest_coverage', 'market_cap_crore', 'composite_quality_score'
                    ]
                    
                    export_df = df[[col for col in columns_to_export if col in df.columns]]
                    
                    # Write to Excel sheet
                    export_df.to_excel(writer, sheet_name=preset_name[:31], index=False)
                    
                    # Format header row
                    worksheet = writer.sheets[preset_name[:31]]
                    for col_num, value in enumerate(export_df.columns, 1):
                        cell = worksheet.cell(row=1, column=col_num)
                        cell.fill = "D9E8F5"  # Light blue
                        cell.font = cell.font.copy(bold=True)
            
            logger.info(f"Exported screener results to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export Excel: {e}")
            raise


if __name__ == "__main__":
    # Test the screener engine
    logging.basicConfig(level=logging.INFO)
    
    engine = ScreenerEngine()
    results = engine.generate_all_presets()
    engine.export_to_excel(results)
    
    print(f"\n✓ Generated {len(results)} preset screeners")
    for name, df in results.items():
        print(f"  - {name}: {len(df)} companies")
