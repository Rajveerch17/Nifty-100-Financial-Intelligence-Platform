"""
Cash Flow Intelligence Module - Day 31
Implements CFO Quality Score, CapEx Intensity, Distress Signal detection
Classifies companies by cash flow patterns and capital allocation
"""

import pandas as pd
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CashFlowIntelligence:
    """Analyze and classify companies based on cash flow metrics"""
    
    def __init__(self, db_path: str = 'data/nifty100.db'):
        """Initialize with database connection"""
        self.db_path = db_path
        self.conn = None
        self.results = []
        self.distress_alerts = []
        
    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        logger.info(f"Connected to database: {self.db_path}")
        
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def load_data(self) -> pd.DataFrame:
        """Load cash flow, P&L, and balance sheet data"""
        logger.info("Loading cash flow and financial data")
        
        query = """
        SELECT 
            cf.company_id,
            s.broad_sector as sector,
            cf.year,
            cf.operating_activity as cfo,
            cf.investing_activity as cfi,
            cf.financing_activity as cff,
            cf.net_cash_flow,
            pl.sales as revenue,
            pl.net_profit as pat,
            bs.borrowings,
            fr.free_cash_flow_cr as fcf
        FROM cashflow cf
        LEFT JOIN sectors s ON cf.company_id = s.company_id
        LEFT JOIN profitandloss pl ON cf.company_id = pl.company_id AND cf.year = pl.year
        LEFT JOIN balancesheet bs ON cf.company_id = bs.company_id AND cf.year = bs.year
        LEFT JOIN financial_ratios fr ON cf.company_id = fr.company_id AND cf.year = fr.year
        ORDER BY cf.company_id, cf.year
        """
        
        df = pd.read_sql_query(query, self.conn)
        logger.info(f"Loaded {len(df)} rows of cash flow data")
        
        return df
    
    def compute_cfo_quality_score(self, df: pd.DataFrame, company_id: str) -> Tuple[float, str]:
        """
        Compute CFO Quality Score: CFO/PAT ratio averaged over 5 years
        Label: High Quality (>1.0), Moderate (0.5-1.0), Accrual Risk (<0.5)
        """
        company_data = df[df['company_id'] == company_id].sort_values('year', ascending=False)
        
        # Get last 5 years
        recent_data = company_data.head(5)
        
        # Compute CFO/PAT ratio for each year
        ratios = []
        for _, row in recent_data.iterrows():
            if pd.notna(row['cfo']) and pd.notna(row['pat']) and row['pat'] != 0:
                ratio = row['cfo'] / row['pat']
                ratios.append(ratio)
        
        if not ratios:
            return None, 'Insufficient Data'
        
        # Average over available years
        avg_ratio = sum(ratios) / len(ratios)
        
        # Classify
        if avg_ratio > 1.0:
            label = 'High Quality'
        elif avg_ratio >= 0.5:
            label = 'Moderate'
        else:
            label = 'Accrual Risk'
        
        return avg_ratio, label
    
    def compute_capex_intensity(self, df: pd.DataFrame, company_id: str) -> Tuple[float, str]:
        """
        CapEx Intensity: abs(investing_activity) / sales x 100
        Label: Asset Light (<3%), Moderate (3-8%), Capital Intensive (>8%)
        """
        company_data = df[df['company_id'] == company_id].sort_values('year', ascending=False)
        
        # Get latest year
        latest = company_data.iloc[0]
        
        if pd.notna(latest['cfi']) and pd.notna(latest['revenue']) and latest['revenue'] != 0:
            # Investing activity is typically negative, so take absolute value
            capex_intensity = (abs(latest['cfi']) / latest['revenue']) * 100
            
            # Classify
            if capex_intensity < 3:
                label = 'Asset Light'
            elif capex_intensity <= 8:
                label = 'Moderate'
            else:
                label = 'Capital Intensive'
            
            return capex_intensity, label
        else:
            return None, 'Insufficient Data'
    
    def compute_fcf_cagr(self, df: pd.DataFrame, company_id: str) -> float:
        """Compute FCF CAGR over 5 years"""
        company_data = df[df['company_id'] == company_id].sort_values('year', ascending=False)
        
        fcf_values = company_data['fcf'].head(5).dropna().tolist()
        
        if len(fcf_values) < 2:
            return None
        
        # CAGR calculation
        start_val = fcf_values[-1]
        end_val = fcf_values[0]
        n_periods = len(fcf_values) - 1
        
        # Handle negative values
        if start_val <= 0 or end_val <= 0:
            return None
        
        cagr = ((end_val / start_val) ** (1 / n_periods) - 1) * 100
        return cagr
    
    def compute_fcf_conversion(self, df: pd.DataFrame, company_id: str) -> float:
        """Compute FCF/PAT conversion percentage (latest year)"""
        company_data = df[df['company_id'] == company_id].sort_values('year', ascending=False)
        
        latest = company_data.iloc[0]
        
        if pd.notna(latest['fcf']) and pd.notna(latest['pat']) and latest['pat'] != 0:
            conversion = (latest['fcf'] / latest['pat']) * 100
            return conversion
        else:
            return None
    
    def detect_distress_signal(self, df: pd.DataFrame, company_id: str) -> bool:
        """
        Distress Signal: CFO < 0 AND CFF > 0 in latest year
        (raising cash from financing while operations burn cash)
        """
        company_data = df[df['company_id'] == company_id].sort_values('year', ascending=False)
        
        if len(company_data) == 0:
            return False
        
        latest = company_data.iloc[0]
        
        if pd.notna(latest['cfo']) and pd.notna(latest['cff']):
            if latest['cfo'] < 0 and latest['cff'] > 0:
                # Log distress alert
                self.distress_alerts.append({
                    'company_id': company_id,
                    'year': latest['year'],
                    'cfo': latest['cfo'],
                    'cff': latest['cff'],
                    'net_profit': latest['pat']
                })
                return True
        
        return False
    
    def detect_deleveraging(self, df: pd.DataFrame, company_id: str) -> bool:
        """
        Deleveraging flag: CFF < 0 AND borrowings declining year-over-year
        (actively paying down debt)
        """
        company_data = df[df['company_id'] == company_id].sort_values('year', ascending=False)
        
        if len(company_data) < 2:
            return False
        
        latest = company_data.iloc[0]
        prev_year = company_data.iloc[1]
        
        if pd.notna(latest['cff']) and pd.notna(latest['borrowings']) and pd.notna(prev_year['borrowings']):
            if latest['cff'] < 0 and latest['borrowings'] < prev_year['borrowings']:
                return True
        
        return False
    
    def determine_capital_allocation(self, df: pd.DataFrame, company_id: str) -> str:
        """
        Determine capital allocation pattern based on cash flow signs
        8 patterns based on CFO, CFI, CFF combinations
        """
        company_data = df[df['company_id'] == company_id].sort_values('year', ascending=False)
        
        if len(company_data) == 0:
            return 'Unknown'
        
        latest = company_data.iloc[0]
        
        cfo = latest['cfo']
        cfi = latest['cfi']
        cff = latest['cff']
        
        # Handle missing values
        if pd.isna(cfo) or pd.isna(cfi) or pd.isna(cff):
            return 'Insufficient Data'
        
        # Classify based on signs
        if cfo > 0 and cfi < 0 and cff < 0:
            return 'Self-Sufficient Growth'
        elif cfo > 0 and cfi < 0 and cff > 0:
            return 'Debt-Funded Growth'
        elif cfo > 0 and cfi > 0 and cff < 0:
            return 'Asset Liquidation'
        elif cfo > 0 and cfi > 0 and cff > 0:
            return 'Asset Sale + Financing'
        elif cfo < 0 and cfi < 0 and cff > 0:
            return 'Distress Signal'
        elif cfo < 0 and cfi > 0 and cff > 0:
            return 'Severe Distress'
        elif cfo < 0 and cfi < 0 and cff < 0:
            return 'Turnaround Risk'
        elif cfo < 0 and cfi > 0 and cff < 0:
            return 'Restructuring'
        else:
            return 'Neutral'
    
    def analyze_all_companies(self, df: pd.DataFrame) -> None:
        """Analyze cash flow intelligence for all companies"""
        companies = df['company_id'].unique()
        logger.info(f"Analyzing cash flow intelligence for {len(companies)} companies")
        
        for company_id in companies:
            company_data = df[df['company_id'] == company_id]
            
            if len(company_data) == 0:
                continue
            
            # Get sector
            sector = company_data.iloc[0]['sector']
            
            # Compute all metrics
            cfo_score, cfo_label = self.compute_cfo_quality_score(df, company_id)
            capex_intensity, capex_label = self.compute_capex_intensity(df, company_id)
            fcf_cagr = self.compute_fcf_cagr(df, company_id)
            fcf_conversion = self.compute_fcf_conversion(df, company_id)
            distress_flag = self.detect_distress_signal(df, company_id)
            deleveraging_flag = self.detect_deleveraging(df, company_id)
            capital_allocation = self.determine_capital_allocation(df, company_id)
            
            # Store results
            self.results.append({
                'company_id': company_id,
                'sector': sector,
                'cfo_quality_score': cfo_score,
                'cfo_quality_label': cfo_label,
                'capex_intensity_pct': capex_intensity,
                'capex_label': capex_label,
                'fcf_cagr_5yr': fcf_cagr,
                'fcf_conversion_pct': fcf_conversion,
                'distress_flag': 1 if distress_flag else 0,
                'deleveraging_flag': 1 if deleveraging_flag else 0,
                'capital_allocation_label': capital_allocation
            })
        
        logger.info(f"Completed analysis for {len(self.results)} companies")
        logger.info(f"Found {len(self.distress_alerts)} companies with distress signals")
    
    def save_outputs(self, output_dir: str = 'output') -> None:
        """Save cash flow intelligence and distress alerts to files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save main intelligence report as Excel
        results_df = pd.DataFrame(self.results)
        excel_output = output_path / 'cashflow_intelligence.xlsx'
        
        with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
            results_df.to_excel(writer, sheet_name='Cash Flow Intelligence', index=False)
        
        logger.info(f"Saved cash flow intelligence to: {excel_output}")
        logger.info(f"Total companies analyzed: {len(results_df)}")
        
        # Save distress alerts as CSV
        if self.distress_alerts:
            distress_df = pd.DataFrame(self.distress_alerts)
            distress_output = output_path / 'distress_alerts.csv'
            distress_df.to_csv(distress_output, index=False)
            logger.info(f"Saved {len(distress_df)} distress alerts to: {distress_output}")
        else:
            logger.info("No distress alerts to save")
        
        # Print summary statistics
        logger.info("\n=== Cash Flow Intelligence Summary ===")
        logger.info(f"CFO Quality Distribution:")
        logger.info(results_df['cfo_quality_label'].value_counts().to_string())
        logger.info(f"\nCapEx Intensity Distribution:")
        logger.info(results_df['capex_label'].value_counts().to_string())
        logger.info(f"\nCapital Allocation Patterns:")
        logger.info(results_df['capital_allocation_label'].value_counts().to_string())
        logger.info(f"\nDistress Flags: {results_df['distress_flag'].sum()}")
        logger.info(f"Deleveraging Flags: {results_df['deleveraging_flag'].sum()}")
    
    def run(self) -> None:
        """Main execution method"""
        try:
            self.connect()
            
            # Load data
            df = self.load_data()
            
            # Analyze all companies
            self.analyze_all_companies(df)
            
            # Save outputs
            self.save_outputs()
            
            logger.info("✓ Cash Flow Intelligence analysis completed successfully")
            
        except Exception as e:
            logger.error(f"Error during cash flow intelligence analysis: {str(e)}", exc_info=True)
            raise
        finally:
            self.disconnect()


def main():
    """Main entry point"""
    analyzer = CashFlowIntelligence()
    analyzer.run()


if __name__ == '__main__':
    main()
