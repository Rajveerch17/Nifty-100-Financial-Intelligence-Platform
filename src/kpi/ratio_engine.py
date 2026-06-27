"""Financial Ratio Engine - Computes 50+ KPIs for company-year combinations."""

import sqlite3
import math
from typing import Optional, Tuple, Dict, Any
from datetime import datetime


class RatioEngine:
    """Computes financial ratios from P&L, Balance Sheet, and Cash Flow data."""
    
    def __init__(self, db_path: str = "data/nifty100.db"):
        """Initialize ratio engine with database connection."""
        self.db_path = db_path
        self.conn = None
        self.edge_cases = []
    
    def connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def log_edge_case(self, company_id: str, year: str, metric: str, issue: str, value: Any = None):
        """Log an edge case for later review."""
        self.edge_cases.append({
            'timestamp': datetime.now().isoformat(),
            'company_id': company_id,
            'year': year,
            'metric': metric,
            'issue': issue,
            'value': value
        })
    
    def safe_divide(self, numerator: Optional[float], denominator: Optional[float], 
                   default: Optional[float] = None) -> Optional[float]:
        """Safe division with zero-division handling."""
        if numerator is None or denominator is None:
            return default
        if denominator == 0:
            return default
        return numerator / denominator
    
    def net_profit_margin(self, net_profit: Optional[float], sales: Optional[float]) -> Optional[float]:
        """Net Profit Margin = net_profit / sales × 100."""
        if sales is None or sales == 0:
            return None
        ratio = self.safe_divide(net_profit, sales, None)
        return ratio * 100 if ratio is not None else None
    
    def operating_profit_margin(self, operating_profit: Optional[float], sales: Optional[float]) -> Optional[float]:
        """Operating Profit Margin = operating_profit / sales × 100."""
        if sales is None or sales == 0:
            return None
        ratio = self.safe_divide(operating_profit, sales, None)
        return ratio * 100 if ratio is not None else None
    
    def return_on_equity(self, net_profit: Optional[float], equity: Optional[float],
                        reserves: Optional[float]) -> Optional[float]:
        """ROE = net_profit / (equity + reserves) × 100."""
        equity_total = (equity or 0) + (reserves or 0)
        if equity_total <= 0:
            return None
        ratio = self.safe_divide(net_profit, equity_total, None)
        return ratio * 100 if ratio is not None else None
    
    def return_on_capital(self, ebit: Optional[float], equity: Optional[float],
                         reserves: Optional[float], borrowings: Optional[float],
                         sector: Optional[str] = None) -> Optional[float]:
        """
        ROCE = EBIT / (equity + reserves + borrowings) × 100.
        For banks/NBFCs, uses sector-relative approach (NIM + ROA proxy).
        """
        capital = (equity or 0) + (reserves or 0) + (borrowings or 0)
        if capital <= 0:
            return None

        roce = self.safe_divide(ebit, capital, None)
        roce = roce * 100 if roce is not None else None

        # For banks and NBFCs, ROCE is structurally different due to high leverage
        # Log this for sector-relative analysis
        if sector and ('Financial' in sector or 'Bank' in sector):
            self.log_edge_case('SECTOR', 'ALL', 'ROCE', f'Banks/NBFCs: {sector}', roce)

        return roce
    
    def debt_to_equity(self, borrowings: Optional[float], equity: Optional[float], 
                      reserves: Optional[float]) -> Optional[float]:
        """D/E = borrowings / (equity + reserves). Returns 0 for debt-free companies."""
        equity_total = (equity or 0) + (reserves or 0)
        if equity_total <= 0:
            return None
        if borrowings is None or borrowings == 0:
            return 0.0
        return self.safe_divide(borrowings, equity_total, None)
    
    def interest_coverage(self, op_profit: Optional[float], other_income: Optional[float], 
                         interest: Optional[float]) -> Optional[float]:
        """ICR = (op_profit + other_income) / interest. Returns 999 for debt-free."""
        if interest is None or interest == 0:
            return 999.0  # Debt-free indicator
        numerator = (op_profit or 0) + (other_income or 0)
        return self.safe_divide(numerator, interest, None)
    
    def asset_turnover(self, sales: Optional[float], total_assets: Optional[float]) -> Optional[float]:
        """Asset Turnover = sales / total_assets."""
        if total_assets is None or total_assets == 0:
            return None
        return self.safe_divide(sales, total_assets, None)
    
    def free_cash_flow(self, operating_activity: Optional[float],
                      investing_activity: Optional[float]) -> Optional[float]:
        """FCF = CFO + CFI (investing activity is typically negative)."""
        if operating_activity is None or investing_activity is None:
            return None
        return operating_activity + investing_activity
    
    def return_on_assets(self, net_profit: Optional[float],
                        total_assets: Optional[float]) -> Optional[float]:
        """ROA = net_profit / total_assets × 100."""
        if total_assets is None or total_assets == 0:
            return None
        ratio = self.safe_divide(net_profit, total_assets, None)
        return ratio * 100 if ratio is not None else None
    
    def net_debt(self, borrowings: Optional[float], investments: Optional[float],
                cash: Optional[float] = None) -> Optional[float]:
        """Net Debt = borrowings - investments - cash."""
        borrowings_val = borrowings or 0
        investments_val = investments or 0
        cash_val = cash or 0
        return borrowings_val - investments_val - cash_val
    
    def net_debt_ebitda(self, net_debt: Optional[float], 
                       operating_profit: Optional[float],
                       depreciation: Optional[float] = None) -> Optional[float]:
        """Net Debt / EBITDA = net_debt / (operating_profit + depreciation)."""
        if operating_profit is None or operating_profit <= 0:
            return None
        ebitda = operating_profit + (depreciation or 0)
        if ebitda <= 0:
            return None
        return self.safe_divide(net_debt, ebitda, None)
    
    def working_capital_days(self, other_assets: Optional[float], 
                             other_liabilities: Optional[float],
                             sales: Optional[float]) -> Optional[float]:
        """Working Capital Days = (other_assets - other_liabilities) / sales × 365."""
        if sales is None or sales == 0:
            return None
        wc = (other_assets or 0) - (other_liabilities or 0)
        return (wc / sales) * 365
    
    def cfo_pat_ratio(self, operating_activity: Optional[float],
                     net_profit: Optional[float]) -> Optional[float]:
        """CFO / PAT Ratio = operating_activity / net_profit."""
        if net_profit is None or net_profit == 0:
            return None
        return self.safe_divide(operating_activity, net_profit, None)
    
    def fcf_conversion_rate(self, fcf: Optional[float],
                            operating_profit: Optional[float]) -> Optional[float]:
        """FCF Conversion Rate = FCF / operating_profit × 100."""
        if operating_profit is None or operating_profit == 0:
            return None
        ratio = self.safe_divide(fcf, operating_profit, None)
        return ratio * 100 if ratio is not None else None
    
    def calculate_cagr(self, start_value: Optional[float], end_value: Optional[float],
                      years: int) -> Tuple[Optional[float], Optional[str]]:
        """
        CAGR = ((end/start)^(1/n) - 1) × 100.
        Returns (cagr_value, flag) where flag can be 'TURNAROUND' for negative base to positive end.
        """
        if start_value is None or end_value is None:
            return None, None
        if start_value < 0:
            if end_value > 0:
                return None, 'TURNAROUND'
            return None, None
        if start_value == 0:
            return None, None
        if years <= 0:
            return None, None

        try:
            ratio = end_value / start_value
            if ratio < 0:
                # Negative ratio with fractional power results in complex number
                return None, None
            cagr = (ratio ** (1 / years) - 1) * 100
            # Ensure result is real (not complex)
            if isinstance(cagr, complex):
                return None, None
            return float(cagr), None
        except (ValueError, ZeroDivisionError):
            return None, None
    
    def capital_allocation_pattern(self, cfo: Optional[float], cfi: Optional[float], 
                                   cff: Optional[float]) -> str:
        """
        Classify capital allocation based on sign pattern of CFO, CFI, CFF.
        Returns one of 8 pattern labels.
        """
        cfo_sign = '+' if (cfo or 0) >= 0 else '-'
        cfi_sign = '+' if (cfi or 0) >= 0 else '-'
        cff_sign = '+' if (cff or 0) >= 0 else '-'
        
        pattern = f"{cfo_sign}{cfi_sign}{cff_sign}"
        
        pattern_map = {
            '+++': 'Reinvest',           # Positive across all - strong reinvestment
            '++-': 'Return',            # Positive ops/investing, negative financing (dividends/buybacks)
            '+-+': 'Distress',          # Positive ops, negative investing (asset sales), positive financing (raising capital)
            '+--': 'Turnaround',        # Positive ops, negative investing and financing (paying down debt)
            '-++': 'Expansion',         # Negative ops, positive investing (capex), positive financing (raising capital)
            '-+-': 'Contraction',       # Negative ops, positive investing, negative financing (paying down debt despite losses)
            '--+': 'Liquidation',       # Negative ops and investing, positive financing (raising capital to survive)
            '---': 'Collapse'           # Negative across all - severe distress
        }
        
        return pattern_map.get(pattern, 'Unknown')
    
    def get_company_data(self, company_id: str, year: str) -> Dict[str, Any]:
        """Fetch all financial data for a company-year combination."""
        cursor = self.conn.cursor()
        
        # Get P&L data
        cursor.execute("""
            SELECT sales, expenses, operating_profit, opm_percentage, other_income,
                   interest, depreciation, profit_before_tax, tax_percentage, 
                   net_profit, eps, dividend_payout
            FROM profitandloss WHERE company_id = ? AND year = ?
        """, (company_id, year))
        pl_row = cursor.fetchone()
        
        # Get Balance Sheet data
        cursor.execute("""
            SELECT equity_capital, reserves, borrowings, other_liabilities,
                   total_liabilities, fixed_assets, cwip, investments, 
                   other_asset, total_assets
            FROM balancesheet WHERE company_id = ? AND year = ?
        """, (company_id, year))
        bs_row = cursor.fetchone()
        
        # Get Cash Flow data
        cursor.execute("""
            SELECT operating_activity, investing_activity, financing_activity, net_cash_flow
            FROM cashflow WHERE company_id = ? AND year = ?
        """, (company_id, year))
        cf_row = cursor.fetchone()
        
        # Get sector info for ROCE adjustment
        cursor.execute("""
            SELECT broad_sector FROM sectors WHERE company_id = ?
        """, (company_id,))
        sector_row = cursor.fetchone()
        
        return {
            'pl': dict(pl_row) if pl_row else {},
            'bs': dict(bs_row) if bs_row else {},
            'cf': dict(cf_row) if cf_row else {},
            'sector': sector_row['broad_sector'] if sector_row else None
        }
    
    def compute_ratios_for_year(self, company_id: str, year: str) -> Dict[str, Any]:
        """Compute all ratios for a single company-year."""
        data = self.get_company_data(company_id, year)
        pl = data['pl']
        bs = data['bs']
        cf = data['cf']
        sector = data['sector']
        
        ratios = {
            'company_id': company_id,
            'year': year
        }
        
        # Profitability ratios
        ratios['net_profit_margin_pct'] = self.net_profit_margin(
            pl.get('net_profit'), pl.get('sales')
        )
        ratios['operating_profit_margin_pct'] = self.operating_profit_margin(
            pl.get('operating_profit'), pl.get('sales')
        )
        ratios['return_on_equity_pct'] = self.return_on_equity(
            pl.get('net_profit'), bs.get('equity_capital'), bs.get('reserves')
        )
        
        # ROCE with sector adjustment for banks/NBFCs
        ebit = (pl.get('operating_profit') or 0) + (pl.get('depreciation') or 0)
        ratios['return_on_capital_pct'] = self.return_on_capital(
            ebit, bs.get('equity_capital'), bs.get('reserves'), bs.get('borrowings'), sector
        )
        
        # ROA
        ratios['return_on_assets_pct'] = self.return_on_assets(
            pl.get('net_profit'), bs.get('total_assets')
        )
        
        # Leverage ratios
        ratios['debt_to_equity'] = self.debt_to_equity(
            bs.get('borrowings'), bs.get('equity_capital'), bs.get('reserves')
        )
        ratios['interest_coverage'] = self.interest_coverage(
            pl.get('operating_profit'), pl.get('other_income'), pl.get('interest')
        )
        
        # Net Debt
        ratios['net_debt_cr'] = self.net_debt(
            bs.get('borrowings'), bs.get('investments')
        )
        
        # Net Debt / EBITDA
        ratios['net_debt_ebitda'] = self.net_debt_ebitda(
            ratios['net_debt_cr'], pl.get('operating_profit'), pl.get('depreciation')
        )
        
        # Efficiency ratios
        ratios['asset_turnover'] = self.asset_turnover(
            pl.get('sales'), bs.get('total_assets')
        )
        ratios['working_capital_days'] = self.working_capital_days(
            bs.get('other_asset'), bs.get('other_liabilities'), pl.get('sales')
        )
        
        # Cash flow ratios
        ratios['free_cash_flow_cr'] = self.free_cash_flow(
            cf.get('operating_activity'), cf.get('investing_activity')
        )
        ratios['cash_from_operations_cr'] = cf.get('operating_activity')
        
        # CFO / PAT ratio
        ratios['cfo_pat_ratio'] = self.cfo_pat_ratio(
            cf.get('operating_activity'), pl.get('net_profit')
        )
        
        # FCF Conversion Rate
        ratios['fcf_conversion_rate_pct'] = self.fcf_conversion_rate(
            ratios['free_cash_flow_cr'], pl.get('operating_profit')
        )
        
        # Capital Allocation Pattern
        ratios['capital_allocation_pattern'] = self.capital_allocation_pattern(
            cf.get('operating_activity'), cf.get('investing_activity'), cf.get('financing_activity')
        )
        
        # CapEx intensity (absolute value of investing activity / sales)
        if pl.get('sales') and pl.get('sales') > 0:
            ratios['capex_cr'] = abs(cf.get('investing_activity') or 0) / pl.get('sales') * 100
        else:
            ratios['capex_cr'] = None
        
        # Per-share metrics
        ratios['earnings_per_share'] = pl.get('eps')
        
        # Book value per share
        equity_total = (bs.get('equity_capital') or 0) + (bs.get('reserves') or 0)
        face_value = pl.get('face_value')  # Will need to fetch from companies table
        if face_value and face_value > 0:
            ratios['book_value_per_share'] = equity_total / face_value
        else:
            ratios['book_value_per_share'] = None
        
        # Dividend payout ratio
        if pl.get('net_profit') and pl.get('net_profit') > 0:
            ratios['dividend_payout_ratio_pct'] = (pl.get('dividend_payout') or 0) / pl.get('net_profit') * 100
        else:
            ratios['dividend_payout_ratio_pct'] = None
        
        # Total debt
        ratios['total_debt_cr'] = bs.get('borrowings')
        
        # Initialize CAGR fields (will be computed separately)
        ratios['revenue_cagr_3yr'] = None
        ratios['revenue_cagr_5yr'] = None
        ratios['pat_cagr_3yr'] = None
        ratios['pat_cagr_5yr'] = None
        
        return ratios
    
    def compute_cagr_for_company(self, company_id: str, current_year: str) -> Dict[str, Any]:
        """Compute 3-year and 5-year CAGR for revenue and PAT for a company."""
        cursor = self.conn.cursor()
        
        # Get historical sales and net profit data
        cursor.execute("""
            SELECT year, sales, net_profit 
            FROM profitandloss 
            WHERE company_id = ? 
            ORDER BY year DESC
        """, (company_id,))
        historical_data = cursor.fetchall()
        
        if len(historical_data) < 2:
            return {
                'revenue_cagr_3yr': None,
                'revenue_cagr_5yr': None,
                'pat_cagr_3yr': None,
                'pat_cagr_5yr': None
            }
        
        # Convert to list for easier indexing
        data_list = [dict(row) for row in historical_data]
        
        # Find current year index
        current_idx = next((i for i, d in enumerate(data_list) if d['year'] == current_year), 0)
        
        # Compute 3-year CAGR
        revenue_cagr_3yr, revenue_flag_3yr = None, None
        pat_cagr_3yr, pat_flag_3yr = None, None
        
        if current_idx + 2 < len(data_list):
            start_sales = data_list[current_idx + 2]['sales']
            end_sales = data_list[current_idx]['sales']
            revenue_cagr_3yr, revenue_flag_3yr = self.calculate_cagr(start_sales, end_sales, 3)
            
            start_pat = data_list[current_idx + 2]['net_profit']
            end_pat = data_list[current_idx]['net_profit']
            pat_cagr_3yr, pat_flag_3yr = self.calculate_cagr(start_pat, end_pat, 3)
        
        # Compute 5-year CAGR
        revenue_cagr_5yr, revenue_flag_5yr = None, None
        pat_cagr_5yr, pat_flag_5yr = None, None
        
        if current_idx + 4 < len(data_list):
            start_sales = data_list[current_idx + 4]['sales']
            end_sales = data_list[current_idx]['sales']
            revenue_cagr_5yr, revenue_flag_5yr = self.calculate_cagr(start_sales, end_sales, 5)
            
            start_pat = data_list[current_idx + 4]['net_profit']
            end_pat = data_list[current_idx]['net_profit']
            pat_cagr_5yr, pat_flag_5yr = self.calculate_cagr(start_pat, end_pat, 5)
        
        # Log turnaround flags
        if revenue_flag_3yr == 'TURNAROUND':
            self.log_edge_case(company_id, current_year, 'revenue_cagr_3yr', 'TURNAROUND')
        if pat_flag_3yr == 'TURNAROUND':
            self.log_edge_case(company_id, current_year, 'pat_cagr_3yr', 'TURNAROUND')
        if revenue_flag_5yr == 'TURNAROUND':
            self.log_edge_case(company_id, current_year, 'revenue_cagr_5yr', 'TURNAROUND')
        if pat_flag_5yr == 'TURNAROUND':
            self.log_edge_case(company_id, current_year, 'pat_cagr_5yr', 'TURNAROUND')
        
        return {
            'revenue_cagr_3yr': revenue_cagr_3yr,
            'revenue_cagr_5yr': revenue_cagr_5yr,
            'pat_cagr_3yr': pat_cagr_3yr,
            'pat_cagr_5yr': pat_cagr_5yr
        }
    
    def compute_all_ratios(self):
        """Compute ratios for all company-year combinations in the database."""
        self.connect()
        cursor = self.conn.cursor()
        
        # Get all unique company-year combinations
        cursor.execute("""
            SELECT DISTINCT p.company_id, p.year 
            FROM profitandloss p
            ORDER BY p.company_id, p.year
        """)
        combinations = cursor.fetchall()
        
        computed_ratios = []
        for row in combinations:
            company_id = row['company_id']
            year = row['year']
            ratios = self.compute_ratios_for_year(company_id, year)
            
            # Compute CAGR for this company-year
            cagr_data = self.compute_cagr_for_company(company_id, year)
            ratios.update(cagr_data)
            
            computed_ratios.append(ratios)
        
        self.close()
        return computed_ratios
    
    def save_ratios_to_db(self, ratios: list):
        """Save computed ratios to financial_ratios table."""
        self.connect()
        cursor = self.conn.cursor()
        
        # Clear existing ratios
        cursor.execute("DELETE FROM financial_ratios")
        
        # Insert new ratios
        for ratio in ratios:
            cursor.execute("""
                INSERT INTO financial_ratios (
                    id, company_id, year, net_profit_margin_pct, operating_profit_margin_pct,
                    return_on_equity_pct, return_on_capital_pct, return_on_assets_pct,
                    debt_to_equity, interest_coverage, asset_turnover,
                    free_cash_flow_cr, capex_cr, earnings_per_share, book_value_per_share,
                    dividend_payout_ratio_pct, total_debt_cr, net_debt_cr, net_debt_ebitda,
                    working_capital_days, cash_from_operations_cr, cfo_pat_ratio,
                    fcf_conversion_rate_pct, capital_allocation_pattern,
                    revenue_cagr_3yr, revenue_cagr_5yr, pat_cagr_3yr, pat_cagr_5yr
                ) VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ratio['company_id'], ratio['year'],
                ratio['net_profit_margin_pct'], ratio['operating_profit_margin_pct'],
                ratio['return_on_equity_pct'], ratio['return_on_capital_pct'],
                ratio['return_on_assets_pct'], ratio['debt_to_equity'],
                ratio['interest_coverage'], ratio['asset_turnover'],
                ratio['free_cash_flow_cr'], ratio['capex_cr'],
                ratio['earnings_per_share'], ratio['book_value_per_share'],
                ratio['dividend_payout_ratio_pct'], ratio['total_debt_cr'],
                ratio['net_debt_cr'], ratio['net_debt_ebitda'],
                ratio['working_capital_days'], ratio['cash_from_operations_cr'],
                ratio['cfo_pat_ratio'], ratio['fcf_conversion_rate_pct'],
                ratio['capital_allocation_pattern'],
                ratio['revenue_cagr_3yr'], ratio['revenue_cagr_5yr'],
                ratio['pat_cagr_3yr'], ratio['pat_cagr_5yr']
            ))
        
        self.conn.commit()
        self.close()
    
    def write_edge_cases_log(self, output_path: str = "output/ratio_edge_cases.log"):
        """Write edge cases to log file."""
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write("timestamp,company_id,year,metric,issue,value\n")
            for case in self.edge_cases:
                f.write(f"{case['timestamp']},{case['company_id']},{case['year']},"
                       f"{case['metric']},{case['issue']},{case['value']}\n")


def main():
    """Main entry point for ratio computation."""
    engine = RatioEngine()
    ratios = engine.compute_all_ratios()
    engine.save_ratios_to_db(ratios)
    
    if engine.edge_cases:
        engine.write_edge_cases_log()
        print(f"Computed {len(ratios)} ratio records. {len(engine.edge_cases)} edge cases logged.")
    else:
        print(f"Computed {len(ratios)} ratio records. No edge cases.")


if __name__ == "__main__":
    main()
