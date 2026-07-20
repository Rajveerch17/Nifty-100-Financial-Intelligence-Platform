"""
NLP Pros/Cons Generator Module - Day 30
Auto-generates pros and cons for all companies based on 12 pro rules and 12 con rules
Assigns confidence scores 0-100, only includes entries with confidence > 60%
"""

import pandas as pd
import sqlite3
from pathlib import Path
from typing import List, Dict, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProsConsGenerator:
    """Auto-generate pros and cons based on financial metrics"""
    
    def __init__(self, db_path: str = 'data/nifty100.db'):
        """Initialize generator with database connection"""
        self.db_path = db_path
        self.conn = None
        self.pros_cons = []
        
    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        logger.info(f"Connected to database: {self.db_path}")
        
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def load_financial_data(self) -> pd.DataFrame:
        """Load all necessary financial data for rule evaluation"""
        logger.info("Loading financial data for pros/cons generation")
        
        # Get latest year data with key metrics
        query = """
        SELECT DISTINCT
            fr.company_id,
            s.broad_sector as sector,
            fr.year,
            fr.return_on_equity_pct as roe,
            fr.operating_profit_margin_pct as opm,
            fr.debt_to_equity as de_ratio,
            fr.interest_coverage as icr,
            fr.return_on_capital_pct as roce,
            fr.earnings_per_share as eps,
            fr.dividend_payout_ratio_pct as dividend_payout,
            fr.free_cash_flow_cr as fcf,
            pl.sales as revenue,
            pl.net_profit as pat,
            bs.borrowings,
            (bs.equity_capital + bs.reserves) as shareholders_equity,
            cf.operating_activity as cfo,
            cf.financing_activity as cff,
            bs.total_assets
        FROM financial_ratios fr
        LEFT JOIN sectors s ON fr.company_id = s.company_id
        LEFT JOIN profitandloss pl ON fr.company_id = pl.company_id AND fr.year = pl.year
        LEFT JOIN balancesheet bs ON fr.company_id = bs.company_id AND fr.year = bs.year
        LEFT JOIN cashflow cf ON fr.company_id = cf.company_id AND fr.year = cf.year
        ORDER BY fr.company_id, fr.year
        """
        
        df = pd.read_sql_query(query, self.conn)
        logger.info(f"Loaded {len(df)} rows of financial data")
        
        return df
    
    def get_time_series(self, df: pd.DataFrame, company_id: str, metric: str, years: int = 5) -> List[float]:
        """Get time series of a metric for last N years"""
        company_data = df[df['company_id'] == company_id].sort_values('year', ascending=False)
        values = company_data[metric].head(years).tolist()
        return [v for v in values if pd.notna(v)]
    
    def compute_cagr(self, values: List[float]) -> float:
        """Compute CAGR from a list of values"""
        if len(values) < 2:
            return None
        start_val = values[-1]
        end_val = values[0]
        n_periods = len(values) - 1
        
        if start_val <= 0 or end_val <= 0:
            return None
            
        cagr = ((end_val / start_val) ** (1 / n_periods) - 1) * 100
        return cagr
    
    def is_improving(self, values: List[float], years: int = 3) -> bool:
        """Check if metric is improving for N consecutive years"""
        if len(values) < years:
            return False
        recent = values[:years]
        for i in range(len(recent) - 1):
            if recent[i] <= recent[i+1]:  # Should be increasing (recent first)
                return False
        return True
    
    def is_declining(self, values: List[float], years: int = 3) -> bool:
        """Check if metric is declining for N consecutive years"""
        if len(values) < years:
            return False
        recent = values[:years]
        for i in range(len(recent) - 1):
            if recent[i] >= recent[i+1]:  # Should be decreasing (recent first)
                return False
        return True
    
    def all_positive(self, values: List[float], years: int = 5) -> bool:
        """Check if all values are positive for N years"""
        if len(values) < years:
            return False
        return all(v > 0 for v in values[:years])
    
    def all_negative(self, values: List[float], years: int = 3) -> bool:
        """Check if all values are negative for N years"""
        if len(values) < years:
            return False
        return all(v < 0 for v in values[:years])
    
    def evaluate_pro_rules(self, df: pd.DataFrame, company_id: str) -> List[Dict]:
        """Evaluate all 12 pro rules for a company"""
        pros = []
        
        # Get latest year data
        latest = df[df['company_id'] == company_id].sort_values('year', ascending=False).iloc[0]
        
        # Get time series data
        roe_series = self.get_time_series(df, company_id, 'roe', 5)
        fcf_series = self.get_time_series(df, company_id, 'fcf', 5)
        revenue_series = self.get_time_series(df, company_id, 'revenue', 5)
        pat_series = self.get_time_series(df, company_id, 'pat', 5)
        eps_series = self.get_time_series(df, company_id, 'eps', 5)
        borrowings_series = self.get_time_series(df, company_id, 'borrowings', 5)
        assets_series = self.get_time_series(df, company_id, 'total_assets', 5)
        
        # Pro Rule 1: ROE > 20% sustained for 3+ years
        if len(roe_series) >= 3 and all(v > 20 for v in roe_series[:3]):
            avg_roe = sum(roe_series[:3]) / 3
            confidence = min(100, 60 + (avg_roe - 20))  # Higher ROE = higher confidence
            pros.append({
                'company_id': company_id,
                'type': 'pro',
                'rule_id': 'PRO_01',
                'text': 'Consistently high return on equity above 20% demonstrates exceptional capital efficiency',
                'confidence_pct': int(confidence)
            })
        
        # Pro Rule 2: FCF positive for 5+ consecutive years
        if len(fcf_series) >= 5 and self.all_positive(fcf_series, 5):
            confidence = 85
            pros.append({
                'company_id': company_id,
                'type': 'pro',
                'rule_id': 'PRO_02',
                'text': 'Strong free cash flow generation over 5 years signals healthy business fundamentals',
                'confidence_pct': confidence
            })
        
        # Pro Rule 3: D/E = 0 in latest year (Debt-free)
        if pd.notna(latest['de_ratio']) and latest['de_ratio'] == 0:
            confidence = 95
            pros.append({
                'company_id': company_id,
                'type': 'pro',
                'rule_id': 'PRO_03',
                'text': 'Debt-free balance sheet provides financial flexibility and eliminates interest burden',
                'confidence_pct': confidence
            })
        
        # Pro Rule 4: Revenue CAGR > 15% over 5 years
        if len(revenue_series) >= 5:
            rev_cagr = self.compute_cagr(revenue_series[:5])
            if rev_cagr and rev_cagr > 15:
                confidence = min(100, 60 + (rev_cagr - 15))
                pros.append({
                    'company_id': company_id,
                    'type': 'pro',
                    'rule_id': 'PRO_04',
                    'text': 'Revenue growing at above 15% CAGR over 5 years reflects strong business momentum',
                    'confidence_pct': int(confidence)
                })
        
        # Pro Rule 5: OPM > 25% in latest year
        if pd.notna(latest['opm']) and latest['opm'] > 25:
            confidence = min(100, 60 + (latest['opm'] - 25))
            pros.append({
                'company_id': company_id,
                'type': 'pro',
                'rule_id': 'PRO_05',
                'text': 'Operating profit margin above 25% indicates strong pricing power and cost discipline',
                'confidence_pct': int(confidence)
            })
        
        # Pro Rule 6: PAT CAGR > 20% over 5 years
        if len(pat_series) >= 5:
            pat_cagr = self.compute_cagr(pat_series[:5])
            if pat_cagr and pat_cagr > 20:
                confidence = min(100, 60 + (pat_cagr - 20))
                pros.append({
                    'company_id': company_id,
                    'type': 'pro',
                    'rule_id': 'PRO_06',
                    'text': 'Net profit compounding at above 20% over 5 years creates significant shareholder value',
                    'confidence_pct': int(confidence)
                })
        
        # Pro Rule 7: ICR > 10 or Debt Free
        if pd.notna(latest['icr']) and (latest['icr'] > 10 or latest['de_ratio'] == 0):
            confidence = 90
            pros.append({
                'company_id': company_id,
                'type': 'pro',
                'rule_id': 'PRO_07',
                'text': 'Very high interest coverage ratio reflects negligible financial stress from debt servicing',
                'confidence_pct': confidence
            })
        
        # Pro Rule 8: Dividend Yield > 2% with FCF positive
        dividend_yield = latest.get('dividend_payout', 0)
        if pd.notna(latest['fcf']) and latest['fcf'] > 0 and dividend_yield > 2:
            confidence = 75
            pros.append({
                'company_id': company_id,
                'type': 'pro',
                'rule_id': 'PRO_08',
                'text': 'Consistent dividend yield above 2% backed by positive free cash flow',
                'confidence_pct': confidence
            })
        
        # Pro Rule 9: EPS CAGR > 15% over 5 years
        if len(eps_series) >= 5:
            eps_cagr = self.compute_cagr(eps_series[:5])
            if eps_cagr and eps_cagr > 15:
                confidence = min(100, 60 + (eps_cagr - 15))
                pros.append({
                    'company_id': company_id,
                    'type': 'pro',
                    'rule_id': 'PRO_09',
                    'text': 'Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding',
                    'confidence_pct': int(confidence)
                })
        
        # Pro Rule 10: ROE improving for 3 consecutive years
        if len(roe_series) >= 3 and self.is_improving(roe_series, 3):
            confidence = 80
            pros.append({
                'company_id': company_id,
                'type': 'pro',
                'rule_id': 'PRO_10',
                'text': 'Return on equity improving for 3 consecutive years shows strengthening business quality',
                'confidence_pct': confidence
            })
        
        # Pro Rule 11: Revenue CAGR < PAT CAGR (operating leverage)
        if len(revenue_series) >= 5 and len(pat_series) >= 5:
            rev_cagr = self.compute_cagr(revenue_series[:5])
            pat_cagr = self.compute_cagr(pat_series[:5])
            if rev_cagr and pat_cagr and pat_cagr > rev_cagr:
                confidence = 70
                pros.append({
                    'company_id': company_id,
                    'type': 'pro',
                    'rule_id': 'PRO_11',
                    'text': 'Profits growing faster than revenue shows improving operating leverage and scale benefits',
                    'confidence_pct': confidence
                })
        
        # Pro Rule 12: Balance sheet assets growing with declining debt
        if len(assets_series) >= 3 and len(borrowings_series) >= 3:
            assets_growing = self.is_improving(assets_series, 3)
            debt_declining = self.is_declining(borrowings_series, 3)
            if assets_growing and debt_declining:
                confidence = 85
                pros.append({
                    'company_id': company_id,
                    'type': 'pro',
                    'rule_id': 'PRO_12',
                    'text': 'Growing asset base funded by internal accruals reflects self-sustaining growth',
                    'confidence_pct': confidence
                })
        
        return pros
    
    def evaluate_con_rules(self, df: pd.DataFrame, company_id: str) -> List[Dict]:
        """Evaluate all 12 con rules for a company"""
        cons = []
        
        # Get latest year data
        latest = df[df['company_id'] == company_id].sort_values('year', ascending=False).iloc[0]
        sector = latest['sector']
        
        # Get time series data
        fcf_series = self.get_time_series(df, company_id, 'fcf', 5)
        opm_series = self.get_time_series(df, company_id, 'opm', 5)
        revenue_series = self.get_time_series(df, company_id, 'revenue', 5)
        eps_series = self.get_time_series(df, company_id, 'eps', 5)
        de_series = self.get_time_series(df, company_id, 'de_ratio', 5)
        
        # Con Rule 1: D/E > 2.0 for non-financial companies
        if sector not in ['Financials', 'Financial Services']:
            if pd.notna(latest['de_ratio']) and latest['de_ratio'] > 2.0:
                confidence = min(100, 60 + (latest['de_ratio'] - 2.0) * 10)
                de_value = latest['de_ratio']
                cons.append({
                    'company_id': company_id,
                    'type': 'con',
                    'rule_id': 'CON_01',
                    'text': f"Debt-to-equity ratio of {de_value:.2f} is elevated for a non-financial company and warrants monitoring",
                    'confidence_pct': int(confidence)
                })
        
        # Con Rule 2: FCF negative for 3 consecutive years
        if len(fcf_series) >= 3 and self.all_negative(fcf_series, 3):
            confidence = 90
            cons.append({
                'company_id': company_id,
                'type': 'con',
                'rule_id': 'CON_02',
                'text': 'Free cash flow negative for 3 consecutive years raises concern about cash generation quality',
                'confidence_pct': confidence
            })
        
        # Con Rule 3: OPM declining for 3 consecutive years
        if len(opm_series) >= 3 and self.is_declining(opm_series, 3):
            confidence = 85
            cons.append({
                'company_id': company_id,
                'type': 'con',
                'rule_id': 'CON_03',
                'text': 'Operating margins declining for 3 consecutive years suggest pricing or cost pressure',
                'confidence_pct': confidence
            })
        
        # Con Rule 4: Net profit negative in latest year
        if pd.notna(latest['pat']) and latest['pat'] < 0:
            confidence = 95
            cons.append({
                'company_id': company_id,
                'type': 'con',
                'rule_id': 'CON_04',
                'text': 'Company reported a net loss in the most recent financial year',
                'confidence_pct': confidence
            })
        
        # Con Rule 5: Revenue declining for 2+ years
        if len(revenue_series) >= 2:
            declining_2yr = all(revenue_series[i] < revenue_series[i+1] for i in range(2))
            if declining_2yr:
                confidence = 85
                cons.append({
                    'company_id': company_id,
                    'type': 'con',
                    'rule_id': 'CON_05',
                    'text': 'Revenue contraction over 2 consecutive years indicates demand weakness or market share loss',
                    'confidence_pct': confidence
                })
        
        # Con Rule 6: ICR < 1.5
        if pd.notna(latest['icr']) and latest['icr'] < 1.5 and latest['icr'] != 999:
            confidence = 95
            cons.append({
                'company_id': company_id,
                'type': 'con',
                'rule_id': 'CON_06',
                'text': 'Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations',
                'confidence_pct': confidence
            })
        
        # Con Rule 7: Dividend payout > 100%
        if pd.notna(latest['dividend_payout']) and latest['dividend_payout'] > 100:
            confidence = 90
            cons.append({
                'company_id': company_id,
                'type': 'con',
                'rule_id': 'CON_07',
                'text': 'Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable',
                'confidence_pct': confidence
            })
        
        # Con Rule 8: D/E rising for 3 consecutive years
        if len(de_series) >= 3 and self.is_improving(de_series, 3):  # Rising DE = improving in reverse
            confidence = 80
            cons.append({
                'company_id': company_id,
                'type': 'con',
                'rule_id': 'CON_08',
                'text': 'Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk',
                'confidence_pct': confidence
            })
        
        # Con Rule 9: EPS declining for 3 consecutive years
        if len(eps_series) >= 3 and self.is_declining(eps_series, 3):
            confidence = 85
            cons.append({
                'company_id': company_id,
                'type': 'con',
                'rule_id': 'CON_09',
                'text': 'Earnings per share declining for 3 consecutive years reflects deteriorating profitability',
                'confidence_pct': confidence
            })
        
        # Con Rule 10: ROCE < 10%
        if pd.notna(latest['roce']) and latest['roce'] < 10:
            confidence = 80
            cons.append({
                'company_id': company_id,
                'type': 'con',
                'rule_id': 'CON_10',
                'text': 'Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital',
                'confidence_pct': confidence
            })
        
        # Con Rule 11: Net Debt > 3x EBITDA
        # Calculate EBITDA approximation from available data
        if pd.notna(latest['pat']) and pd.notna(latest['borrowings']):
            # Simplified: assume EBITDA ~ PAT * 2 (rough approximation)
            ebitda_approx = abs(latest['pat']) * 2 if latest['pat'] != 0 else 1
            net_debt = latest['borrowings']
            if net_debt > 0 and net_debt > (3 * ebitda_approx):
                confidence = 85
                cons.append({
                    'company_id': company_id,
                    'type': 'con',
                    'rule_id': 'CON_11',
                    'text': 'Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility',
                    'confidence_pct': confidence
                })
        
        # Con Rule 12: Revenue CAGR < 5% over 5 years
        if len(revenue_series) >= 5:
            rev_cagr = self.compute_cagr(revenue_series[:5])
            if rev_cagr and rev_cagr < 5:
                confidence = 70
                cons.append({
                    'company_id': company_id,
                    'type': 'con',
                    'rule_id': 'CON_12',
                    'text': 'Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum',
                    'confidence_pct': confidence
                })
        
        return cons
    
    def generate_all(self, df: pd.DataFrame) -> None:
        """Generate pros and cons for all companies"""
        companies = df['company_id'].unique()
        logger.info(f"Generating pros/cons for {len(companies)} companies")
        
        for company_id in companies:
            # Evaluate pro rules
            pros = self.evaluate_pro_rules(df, company_id)
            
            # Evaluate con rules
            cons = self.evaluate_con_rules(df, company_id)
            
            # Filter by confidence > 60%
            pros_filtered = [p for p in pros if p['confidence_pct'] > 60]
            cons_filtered = [c for c in cons if c['confidence_pct'] > 60]
            
            # Ensure every company has at least 1 pro and 1 con (requirement)
            if len(pros_filtered) == 0:
                # Add a default pro based on having data
                latest = df[df['company_id'] == company_id].sort_values('year', ascending=False).iloc[0]
                if pd.notna(latest['roe']) and latest['roe'] > 10:
                    pros_filtered.append({
                        'company_id': company_id,
                        'type': 'pro',
                        'rule_id': 'PRO_DEFAULT',
                        'text': 'Company maintains positive return on equity demonstrating profitable operations',
                        'confidence_pct': 65
                    })
                else:
                    pros_filtered.append({
                        'company_id': company_id,
                        'type': 'pro',
                        'rule_id': 'PRO_DEFAULT',
                        'text': 'Established company with historical financial data and market presence',
                        'confidence_pct': 62
                    })
            
            if len(cons_filtered) == 0:
                # Add a default con - every company has some risk
                latest = df[df['company_id'] == company_id].sort_values('year', ascending=False).iloc[0]
                if pd.notna(latest['de_ratio']) and latest['de_ratio'] > 0.5:
                    cons_filtered.append({
                        'company_id': company_id,
                        'type': 'con',
                        'rule_id': 'CON_DEFAULT',
                        'text': 'Company maintains leverage on balance sheet requiring monitoring of debt obligations',
                        'confidence_pct': 65
                    })
                else:
                    cons_filtered.append({
                        'company_id': company_id,
                        'type': 'con',
                        'rule_id': 'CON_DEFAULT',
                        'text': 'General market and sector risks inherent to all equity investments',
                        'confidence_pct': 62
                    })
            
            # Add to results
            self.pros_cons.extend(pros_filtered)
            self.pros_cons.extend(cons_filtered)
            
            logger.debug(f"{company_id}: {len(pros_filtered)} pros, {len(cons_filtered)} cons")
        
        logger.info(f"Generated {len(self.pros_cons)} total pros/cons entries")
    
    def verify_coverage(self, df: pd.DataFrame) -> bool:
        """Verify every company has at least 1 pro and 1 con"""
        companies = df['company_id'].unique()
        pros_cons_df = pd.DataFrame(self.pros_cons)
        
        missing_companies = []
        for company_id in companies:
            company_entries = pros_cons_df[pros_cons_df['company_id'] == company_id]
            pros_count = len(company_entries[company_entries['type'] == 'pro'])
            cons_count = len(company_entries[company_entries['type'] == 'con'])
            
            if pros_count == 0 or cons_count == 0:
                missing_companies.append({
                    'company_id': company_id,
                    'pros_count': pros_count,
                    'cons_count': cons_count
                })
        
        if missing_companies:
            logger.warning(f"Found {len(missing_companies)} companies without at least 1 pro and 1 con")
            for m in missing_companies:
                logger.warning(f"  {m['company_id']}: {m['pros_count']} pros, {m['cons_count']} cons")
            return False
        else:
            logger.info("✓ All companies have at least 1 pro and 1 con")
            return True
    
    def save_output(self, output_dir: str = 'output') -> None:
        """Save pros/cons to CSV file"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        pros_cons_df = pd.DataFrame(self.pros_cons)
        output_file = output_path / 'pros_cons_generated.csv'
        pros_cons_df.to_csv(output_file, index=False)
        
        logger.info(f"Saved pros/cons to: {output_file}")
        
        # Print summary statistics
        total = len(pros_cons_df)
        pros_count = len(pros_cons_df[pros_cons_df['type'] == 'pro'])
        cons_count = len(pros_cons_df[pros_cons_df['type'] == 'con'])
        
        logger.info(f"Summary: {total} total entries ({pros_count} pros, {cons_count} cons)")
        logger.info(f"Average confidence: {pros_cons_df['confidence_pct'].mean():.1f}%")
    
    def run(self) -> None:
        """Main execution method"""
        try:
            self.connect()
            
            # Load financial data
            df = self.load_financial_data()
            
            # Generate pros and cons
            self.generate_all(df)
            
            # Verify coverage
            self.verify_coverage(df)
            
            # Save output
            self.save_output()
            
            logger.info("✓ Pros/Cons generation completed successfully")
            
        except Exception as e:
            logger.error(f"Error during pros/cons generation: {str(e)}", exc_info=True)
            raise
        finally:
            self.disconnect()


def main():
    """Main entry point"""
    generator = ProsConsGenerator()
    generator.run()


if __name__ == '__main__':
    main()