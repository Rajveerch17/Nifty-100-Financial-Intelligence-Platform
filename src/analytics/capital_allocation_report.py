"""
Capital Allocation Report - Day 32
Analyzes capital allocation patterns and tracks year-over-year changes
"""

import pandas as pd
import sqlite3
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CapitalAllocationReport:
    """Generate capital allocation distribution and pattern change reports"""
    
    def __init__(self, db_path: str = 'data/nifty100.db'):
        """Initialize with database connection"""
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        logger.info(f"Connected to database: {self.db_path}")
        
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def load_capital_allocation_data(self) -> pd.DataFrame:
        """Load capital allocation data from CSV"""
        csv_path = Path('output/capital_allocation.csv')
        
        if not csv_path.exists():
            logger.error(f"Capital allocation CSV not found at: {csv_path}")
            logger.info("Generating capital allocation data from database...")
            return self.generate_capital_allocation_from_db()
        
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} rows from capital_allocation.csv")
        return df
    
    def generate_capital_allocation_from_db(self) -> pd.DataFrame:
        """Generate capital allocation patterns from database if CSV doesn't exist"""
        query = """
        SELECT 
            cf.company_id,
            cf.year,
            cf.operating_activity as cfo,
            cf.investing_activity as cfi,
            cf.financing_activity as cff
        FROM cashflow cf
        ORDER BY cf.company_id, cf.year
        """
        
        df = pd.read_sql_query(query, self.conn)
        
        # Determine pattern for each row
        patterns = []
        for _, row in df.iterrows():
            cfo = row['cfo']
            cfi = row['cfi']
            cff = row['cff']
            
            # Classify based on signs
            if pd.isna(cfo) or pd.isna(cfi) or pd.isna(cff):
                pattern = 'Insufficient Data'
            elif cfo > 0 and cfi < 0 and cff < 0:
                pattern = 'Self-Sufficient Growth'
            elif cfo > 0 and cfi < 0 and cff > 0:
                pattern = 'Debt-Funded Growth'
            elif cfo > 0 and cfi > 0 and cff < 0:
                pattern = 'Asset Liquidation'
            elif cfo > 0 and cfi > 0 and cff > 0:
                pattern = 'Asset Sale + Financing'
            elif cfo < 0 and cfi < 0 and cff > 0:
                pattern = 'Distress Signal'
            elif cfo < 0 and cfi > 0 and cff > 0:
                pattern = 'Severe Distress'
            elif cfo < 0 and cfi < 0 and cff < 0:
                pattern = 'Turnaround Risk'
            elif cfo < 0 and cfi > 0 and cff < 0:
                pattern = 'Restructuring'
            else:
                pattern = 'Neutral'
            
            patterns.append(pattern)
        
        df['capital_allocation_pattern'] = patterns
        
        # Save to CSV for future use
        output_path = Path('output/capital_allocation.csv')
        df.to_csv(output_path, index=False)
        logger.info(f"Generated and saved capital allocation data to: {output_path}")
        
        return df
    
    def generate_latest_year_distribution(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate distribution summary for latest year"""
        # Get latest year for each company
        latest_year_data = df.sort_values('year', ascending=False).groupby('company_id').first().reset_index()
        
        # Count by pattern
        pattern_col = 'pattern_label' if 'pattern_label' in df.columns else 'capital_allocation_pattern'
        distribution = latest_year_data[pattern_col].value_counts().reset_index()
        distribution.columns = ['pattern', 'count']
        
        logger.info("\n=== Latest Year Capital Allocation Distribution ===")
        for _, row in distribution.iterrows():
            logger.info(f"{row['pattern']}: {row['count']} companies")
        
        return distribution
    
    def detect_pattern_changes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect companies that changed capital allocation pattern year-over-year"""
        changes = []
        
        pattern_col = 'pattern_label' if 'pattern_label' in df.columns else 'capital_allocation_pattern'
        companies = df['company_id'].unique()
        
        for company_id in companies:
            company_data = df[df['company_id'] == company_id].sort_values('year', ascending=False)
            
            if len(company_data) < 2:
                continue
            
            # Get latest two years
            latest = company_data.iloc[0]
            previous = company_data.iloc[1]
            
            latest_pattern = latest[pattern_col]
            previous_pattern = previous[pattern_col]
            
            # Check if pattern changed
            if latest_pattern != previous_pattern:
                changes.append({
                    'company_id': company_id,
                    'previous_year': previous['year'],
                    'previous_pattern': previous_pattern,
                    'latest_year': latest['year'],
                    'latest_pattern': latest_pattern,
                    'change_description': f"{previous_pattern} → {latest_pattern}"
                })
        
        changes_df = pd.DataFrame(changes)
        
        logger.info(f"\nFound {len(changes_df)} companies with pattern changes year-over-year")
        
        return changes_df
    
    def merge_with_cashflow_intelligence(self) -> None:
        """Add capital allocation to cashflow_intelligence.xlsx"""
        cf_intel_path = Path('output/cashflow_intelligence.xlsx')
        
        if not cf_intel_path.exists():
            logger.warning("cashflow_intelligence.xlsx not found, skipping merge")
            return
        
        # Load cashflow intelligence
        cf_intel_df = pd.read_excel(cf_intel_path, header=1)
        
        # Already has capital_allocation_label from Day 31
        logger.info("Capital allocation already included in cashflow_intelligence.xlsx from Day 31")
        logger.info(f"Total companies in cashflow intelligence: {len(cf_intel_df)}")
    
    def save_outputs(self, distribution: pd.DataFrame, changes: pd.DataFrame) -> None:
        """Save distribution and pattern changes to files"""
        output_path = Path('output')
        output_path.mkdir(exist_ok=True)
        
        # Save pattern changes
        changes_output = output_path / 'pattern_changes.csv'
        changes.to_csv(changes_output, index=False)
        logger.info(f"Saved pattern changes to: {changes_output}")
        
        # Save distribution summary
        distribution_output = output_path / 'capital_allocation_distribution.csv'
        distribution.to_csv(distribution_output, index=False)
        logger.info(f"Saved distribution summary to: {distribution_output}")
    
    def run(self) -> None:
        """Main execution method"""
        try:
            self.connect()
            
            # Load capital allocation data
            df = self.load_capital_allocation_data()
            
            # Generate latest year distribution
            distribution = self.generate_latest_year_distribution(df)
            
            # Detect pattern changes
            changes = self.detect_pattern_changes(df)
            
            # Merge with cashflow intelligence
            self.merge_with_cashflow_intelligence()
            
            # Save outputs
            self.save_outputs(distribution, changes)
            
            logger.info("✓ Capital Allocation Report completed successfully")
            
        except Exception as e:
            logger.error(f"Error during capital allocation report: {str(e)}", exc_info=True)
            raise
        finally:
            self.disconnect()


def main():
    """Main entry point"""
    reporter = CapitalAllocationReport()
    reporter.run()


if __name__ == '__main__':
    main()
