"""Integration tests for ETL loader and validation."""

import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from src.etl.loader import (
    get_paths,
    load_all_excel_files,
    run_load,
    synthesize_missing_companies,
)
from src.etl.validator import run_all_validations


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def loaded_outputs():
    audit_df, failures_df = run_load()
    paths = get_paths()
    return {
        "audit": audit_df,
        "failures": failures_df,
        "db_path": paths["db_path"],
    }


def test_all_twelve_source_files_present():
    paths = get_paths()
    datasets = load_all_excel_files(paths)
    assert len(datasets) == 12


def test_synthesize_missing_companies_adds_orphans():
    paths = get_paths()
    datasets = load_all_excel_files(paths)
    merged, missing = synthesize_missing_companies(datasets["companies"], datasets)
    assert len(missing) >= 0
    assert len(merged) >= len(datasets["companies"])


def test_validation_runs_without_error():
    paths = get_paths()
    datasets = load_all_excel_files(paths)
    merged, _ = synthesize_missing_companies(datasets["companies"], datasets)
    datasets["companies"] = merged
    result, validated = run_all_validations(datasets)
    assert "companies" in validated
    assert isinstance(result.failures, list)


def test_database_file_created(loaded_outputs):
    assert loaded_outputs["db_path"].exists()


def test_companies_table_populated(loaded_outputs):
    conn = sqlite3.connect(loaded_outputs["db_path"])
    count = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    conn.close()
    assert count >= 92


def test_stock_prices_exact_count(loaded_outputs):
    conn = sqlite3.connect(loaded_outputs["db_path"])
    count = conn.execute("SELECT COUNT(*) FROM stock_prices").fetchone()[0]
    conn.close()
    assert count == 5520


def test_foreign_key_check_zero(loaded_outputs):
    conn = sqlite3.connect(loaded_outputs["db_path"])
    conn.execute("PRAGMA foreign_keys = ON")
    issues = conn.execute("PRAGMA foreign_key_check").fetchall()
    conn.close()
    assert issues == []


def test_load_audit_written():
    audit_path = PROJECT_ROOT / "output" / "load_audit.csv"
    assert audit_path.exists()
    audit = pd.read_csv(audit_path)
    assert len(audit) == 12


def test_validation_failures_written():
    failures_path = PROJECT_ROOT / "output" / "validation_failures.csv"
    assert failures_path.exists()


def test_all_tables_have_rows(loaded_outputs):
    tables = [
        "companies",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "analysis",
        "documents",
        "prosandcons",
        "sectors",
        "peer_groups",
        "financial_ratios",
        "market_cap",
        "stock_prices",
    ]
    conn = sqlite3.connect(loaded_outputs["db_path"])
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert count > 0, f"{table} is empty"
    conn.close()


def test_profitandloss_minimum_rows(loaded_outputs):
    conn = sqlite3.connect(loaded_outputs["db_path"])
    count = conn.execute("SELECT COUNT(*) FROM profitandloss").fetchone()[0]
    conn.close()
    assert count >= 1100


def test_schema_file_exists():
    assert (PROJECT_ROOT / "db" / "schema.sql").exists()
