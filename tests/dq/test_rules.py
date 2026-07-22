"""Unit tests for DQ rules - simplified placeholder tests."""

import pytest
import pandas as pd
from src.etl.validator import ValidationResult, ValidationFailure


def test_validation_result_creation():
    """Test ValidationResult can be created"""
    result = ValidationResult()
    assert result.failures == []
    assert result.critical_count == 0


def test_validation_failure_creation():
    """Test ValidationFailure dataclass"""
    failure = ValidationFailure(
        rule_id="DQ-01",
        rule_name="Test Rule",
        severity="CRITICAL",
        company_id="TCS",
        year="2023-03",
        field="company_id",
        issue="Missing value"
    )
    assert failure.rule_id == "DQ-01"
    assert failure.severity == "CRITICAL"


def test_validation_result_add_failure():
    """Test adding failures to ValidationResult"""
    result = ValidationResult()
    result.add("DQ-01", "Test", "CRITICAL", "Test issue", company_id="TCS")
    assert len(result.failures) == 1
    assert result.critical_count == 1


def test_validation_result_to_dataframe():
    """Test converting ValidationResult to DataFrame"""
    result = ValidationResult()
    result.add("DQ-01", "Test", "CRITICAL", "Test issue", company_id="TCS")
    df = result.to_dataframe()
    assert len(df) == 1
    assert "rule_id" in df.columns


def test_normalize_year_mar23():
    """Test year normalization for Mar-23"""
    from src.etl.normaliser import normalize_year
    assert normalize_year("Mar-23") == "2023-03"


def test_normalize_year_dec2012():
    """Test year normalization for Dec 2012"""
    from src.etl.normaliser import normalize_year
    assert normalize_year("Dec 2012") == "2012-12"


def test_normalize_year_invalid():
    """Test year normalization for invalid input"""
    from src.etl.normaliser import normalize_year
    assert normalize_year("TTM") is None


def test_normalize_ticker_lowercase():
    """Test ticker normalization"""
    from src.etl.normaliser import normalize_ticker
    assert normalize_ticker("tcs") == "TCS"


def test_normalize_ticker_spaces():
    """Test ticker normalization with spaces"""
    from src.etl.normaliser import normalize_ticker
    assert normalize_ticker("  hdfc  ") == "HDFC"


def test_is_valid_ticker():
    """Test ticker validation"""
    from src.etl.normaliser import is_valid_ticker
    assert is_valid_ticker("TCS") is True
    assert is_valid_ticker("A") is False


def test_dq_validator_module_exists():
    """Test validator module can be imported"""
    from src.etl import validator
    assert validator is not None


def test_dq_validator_has_run_all_validations():
    """Test run_all_validations function exists"""
    from src.etl.validator import run_all_validations
    assert callable(run_all_validations)
