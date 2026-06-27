"""Unit tests for financial ratio calculations."""

import pytest
from src.kpi.ratio_engine import RatioEngine


class TestProfitabilityRatios:
    """Test profitability ratio calculations."""
    
    def test_net_profit_margin_positive(self):
        """Net Profit Margin with positive values."""
        engine = RatioEngine()
        result = engine.net_profit_margin(100, 500)
        assert result == 20.0
    
    def test_net_profit_margin_zero_sales(self):
        """Net Profit Margin with zero sales returns None."""
        engine = RatioEngine()
        result = engine.net_profit_margin(100, 0)
        assert result is None
    
    def test_net_profit_margin_none_values(self):
        """Net Profit Margin with None values returns None."""
        engine = RatioEngine()
        result = engine.net_profit_margin(None, 500)
        assert result is None
    
    def test_operating_profit_margin(self):
        """Operating Profit Margin calculation."""
        engine = RatioEngine()
        result = engine.operating_profit_margin(150, 500)
        assert result == 30.0
    
    def test_roe_positive(self):
        """ROE with positive equity and profit."""
        engine = RatioEngine()
        result = engine.return_on_equity(100, 400, 100)
        assert result == 20.0
    
    def test_roe_zero_equity(self):
        """ROE with zero equity returns None."""
        engine = RatioEngine()
        result = engine.return_on_equity(100, 0, 0)
        assert result is None
    
    def test_roce_positive(self):
        """ROCE with positive capital."""
        engine = RatioEngine()
        result = engine.return_on_capital(120, 300, 100, 200)
        assert result == 20.0  # 120 / 600 * 100
    
    def test_roa_positive(self):
        """ROA with positive assets."""
        engine = RatioEngine()
        result = engine.return_on_assets(50, 1000)
        assert result == 5.0


class TestLeverageRatios:
    """Test leverage ratio calculations."""
    
    def test_debt_to_equity_positive(self):
        """D/E with positive debt and equity."""
        engine = RatioEngine()
        result = engine.debt_to_equity(200, 400, 100)
        assert result == 0.4  # 200 / 500
    
    def test_debt_to_equity_debt_free(self):
        """D/E returns 0 for debt-free companies."""
        engine = RatioEngine()
        result = engine.debt_to_equity(0, 400, 100)
        assert result == 0.0
    
    def test_debt_to_equity_zero_equity(self):
        """D/E with zero equity returns None."""
        engine = RatioEngine()
        result = engine.debt_to_equity(200, 0, 0)
        assert result is None
    
    def test_interest_coverage_positive(self):
        """Interest Coverage with positive values."""
        engine = RatioEngine()
        result = engine.interest_coverage(100, 20, 10)
        assert result == 12.0  # (100 + 20) / 10
    
    def test_interest_coverage_debt_free(self):
        """Interest Coverage returns 999 for debt-free (zero interest)."""
        engine = RatioEngine()
        result = engine.interest_coverage(100, 20, 0)
        assert result == 999.0
    
    def test_net_debt_positive(self):
        """Net Debt calculation."""
        engine = RatioEngine()
        result = engine.net_debt(300, 100, 50)
        assert result == 150  # 300 - 100 - 50
    
    def test_net_debt_negative(self):
        """Net Debt can be negative (net cash positive)."""
        engine = RatioEngine()
        result = engine.net_debt(100, 200, 50)
        assert result == -150  # 100 - 200 - 50
    
    def test_net_debt_ebitda(self):
        """Net Debt / EBITDA calculation."""
        engine = RatioEngine()
        result = engine.net_debt_ebitda(200, 100, 20)
        assert result == pytest.approx(1.67, rel=0.01)  # 200 / 120


class TestEfficiencyRatios:
    """Test efficiency ratio calculations."""
    
    def test_asset_turnover(self):
        """Asset Turnover calculation."""
        engine = RatioEngine()
        result = engine.asset_turnover(1000, 500)
        assert result == 2.0
    
    def test_asset_turnover_zero_assets(self):
        """Asset Turnover with zero assets returns None."""
        engine = RatioEngine()
        result = engine.asset_turnover(1000, 0)
        assert result is None
    
    def test_working_capital_days(self):
        """Working Capital Days calculation."""
        engine = RatioEngine()
        result = engine.working_capital_days(200, 100, 1000)
        assert result == 36.5  # (200 - 100) / 1000 * 365


class TestCashFlowRatios:
    """Test cash flow ratio calculations."""
    
    def test_free_cash_flow_positive(self):
        """FCF with positive CFO and negative CFI."""
        engine = RatioEngine()
        result = engine.free_cash_flow(500, -200)
        assert result == 300
    
    def test_cfo_pat_ratio(self):
        """CFO / PAT ratio calculation."""
        engine = RatioEngine()
        result = engine.cfo_pat_ratio(120, 100)
        assert result == 1.2
    
    def test_cfo_pat_ratio_zero_profit(self):
        """CFO / PAT with zero profit returns None."""
        engine = RatioEngine()
        result = engine.cfo_pat_ratio(120, 0)
        assert result is None
    
    def test_fcf_conversion_rate(self):
        """FCF Conversion Rate calculation."""
        engine = RatioEngine()
        result = engine.fcf_conversion_rate(80, 100)
        assert result == 80.0
    
    def test_capex_intensity(self):
        """CapEx Intensity (calculated in compute_ratios_for_year)."""
        # This is tested indirectly through compute_ratios_for_year
        pass


class TestCAGRCalculations:
    """Test CAGR calculations with edge cases."""
    
    def test_cagr_normal(self):
        """Normal CAGR calculation."""
        engine = RatioEngine()
        result, flag = engine.calculate_cagr(100, 200, 5)
        assert result == pytest.approx(14.87, rel=0.01)
        assert flag is None
    
    def test_cagr_turnaround(self):
        """CAGR with negative base to positive end returns TURNAROUND flag."""
        engine = RatioEngine()
        result, flag = engine.calculate_cagr(-100, 200, 5)
        assert result is None
        assert flag == 'TURNAROUND'
    
    def test_cagr_zero_base(self):
        """CAGR with zero base returns None."""
        engine = RatioEngine()
        result, flag = engine.calculate_cagr(0, 200, 5)
        assert result is None
        assert flag is None
    
    def test_cagr_negative_end(self):
        """CAGR with negative end (declining) - should calculate normally."""
        engine = RatioEngine()
        result, flag = engine.calculate_cagr(200, 100, 5)
        assert result == pytest.approx(-12.94, rel=0.01)
        assert flag is None
    
    def test_cagr_none_values(self):
        """CAGR with None values returns None."""
        engine = RatioEngine()
        result, flag = engine.calculate_cagr(None, 200, 5)
        assert result is None
        assert flag is None


class TestCapitalAllocationPatterns:
    """Test capital allocation pattern classification."""
    
    def test_pattern_reinvest(self):
        """+++ pattern: Reinvest."""
        engine = RatioEngine()
        result = engine.capital_allocation_pattern(100, 50, 20)
        assert result == 'Reinvest'
    
    def test_pattern_return(self):
        """++- pattern: Return (dividends/buybacks)."""
        engine = RatioEngine()
        result = engine.capital_allocation_pattern(100, 50, -20)
        assert result == 'Return'
    
    def test_pattern_distress(self):
        """+-+ pattern: Distress."""
        engine = RatioEngine()
        result = engine.capital_allocation_pattern(100, -50, 20)
        assert result == 'Distress'
    
    def test_pattern_turnaround(self):
        """+-- pattern: Turnaround."""
        engine = RatioEngine()
        result = engine.capital_allocation_pattern(100, -50, -20)
        assert result == 'Turnaround'
    
    def test_pattern_expansion(self):
        """-++ pattern: Expansion."""
        engine = RatioEngine()
        result = engine.capital_allocation_pattern(-100, 50, 20)
        assert result == 'Expansion'
    
    def test_pattern_contraction(self):
        """-+- pattern: Contraction."""
        engine = RatioEngine()
        result = engine.capital_allocation_pattern(-100, 50, -20)
        assert result == 'Contraction'
    
    def test_pattern_liquidation(self):
        """--+ pattern: Liquidation."""
        engine = RatioEngine()
        result = engine.capital_allocation_pattern(-100, -50, 20)
        assert result == 'Liquidation'
    
    def test_pattern_collapse(self):
        """--- pattern: Collapse."""
        engine = RatioEngine()
        result = engine.capital_allocation_pattern(-100, -50, -20)
        assert result == 'Collapse'


class TestSafeDivide:
    """Test safe division utility."""
    
    def test_safe_divide_normal(self):
        """Normal division."""
        engine = RatioEngine()
        result = engine.safe_divide(10, 2)
        assert result == 5.0
    
    def test_safe_divide_zero_denominator(self):
        """Division by zero returns default."""
        engine = RatioEngine()
        result = engine.safe_divide(10, 0)
        assert result is None
    
    def test_safe_divide_none_numerator(self):
        """None numerator returns default."""
        engine = RatioEngine()
        result = engine.safe_divide(None, 2)
        assert result is None
    
    def test_safe_divide_custom_default(self):
        """Custom default value."""
        engine = RatioEngine()
        result = engine.safe_divide(10, 0, default=999)
        assert result == 999


class TestEdgeCaseLogging:
    """Test edge case logging functionality."""
    
    def test_log_edge_case(self):
        """Edge case logging."""
        engine = RatioEngine()
        engine.log_edge_case('TEST', '2024-03', 'ROE', 'Zero equity', 0)
        assert len(engine.edge_cases) == 1
        assert engine.edge_cases[0]['company_id'] == 'TEST'
        assert engine.edge_cases[0]['metric'] == 'ROE'
