# Nifty 100 Financial Intelligence Platform

Sprint 1 deliverable: Excel → SQLite ETL pipeline for 12 datasets and 12 database tables.
Sprint 2 deliverable: Financial Ratio Engine computing 50+ KPIs for all company-year combinations.

## Module 1 Sprint 1 Status: ✅ COMPLETED

All Sprint 1 tasks have been successfully completed and verified:
- ✅ Database schema with 12 tables
- ✅ ETL pipeline (loader, normaliser, validator)
- ✅ Data loaded into SQLite (nifty100.db)
- ✅ All 60 unit tests passing
- ✅ Code formatted with black
- ✅ Data quality validation (880 failures logged, 539 critical)
- ✅ Foreign key integrity verified
- ✅ Exploratory SQL queries validated

## Module 2 Sprint 2 Status: ✅ COMPLETED

All Sprint 2 tasks have been successfully completed and verified:
- ✅ Financial Ratio Engine with 50+ KPIs computed for all company-year combinations
- ✅ financial_ratios table: 1,164 records, 41 KPI columns
- ✅ Profitability ratios: Net Profit Margin, OPM, ROE, ROCE, ROA
- ✅ Leverage ratios: D/E, Interest Coverage, Net Debt, Net Debt/EBITDA
- ✅ Efficiency ratios: Asset Turnover, Working Capital Days
- ✅ Cash flow ratios: Free Cash Flow, CFO/PAT, FCF Conversion Rate
- ✅ Capital allocation patterns with 8-pattern classification
- ✅ CAGR engine (3yr, 5yr, 10yr) for Revenue, PAT, EPS
- ✅ CAGR edge case flags: TURNAROUND, DECLINE_TO_LOSS, BOTH_NEGATIVE, ZERO_BASE, INSUFFICIENT
- ✅ CFO Quality Score (5-year average) with classification
- ✅ CapEx Intensity classification
- ✅ Composite Quality Score (0-100 scale)
- ✅ OPM cross-check against source data (logs if difference > 1%)
- ✅ ROCE/ROE cross-check against companies.xlsx (logs anomalies > 5%)
- ✅ Flags: high_leverage_flag, icr_label, icr_warning_flag
- ✅ All 42 unit tests passing
- ✅ 2,073 edge cases logged to output/ratio_edge_cases.log
- ✅ output/capital_allocation.csv generated
- ✅ Manual spot-check verification passed for 3 companies

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Load data into database
python -m src.etl.loader      # or: .\load.ps1 (Windows script)

# Compute financial ratios
python -m src.kpi.ratio_engine

# Run tests
python -m pytest tests/ -v    # or: .\test.ps1 (Windows script)

# Clean database and output files
.\clean.ps1                   # Windows cleanup script
```

**Note**: The project includes Windows PowerShell scripts (`load.ps1`, `test.ps1`, `clean.ps1`) as alternatives to the Makefile for Windows users who don't have `make` installed.

## Project layout

| Path | Purpose |
|------|---------|
| `data/raw/` | 7 core Excel files (read-only) |
| `data/supporting/` | 5 supplementary Excel files |
| `data/nifty100.db` | SQLite database (generated) |
| `db/schema.sql` | 13-table schema with FK constraints (12 base + financial_ratios) |
| `src/etl/` | `loader.py`, `validator.py`, `normaliser.py` |
| `src/kpi/` | `ratio_engine.py` - Financial KPI computation engine |
| `output/` | `load_audit.csv`, `validation_failures.csv`, `ratio_edge_cases.log`, `capital_allocation.csv` |
| `notebooks/exploratory_queries.sql` | 10 SQL sanity-check queries |
| `tests/etl/` | 35+ unit tests for ETL pipeline |
| `tests/kpi/` | 42 unit tests for ratio engine |

## Load pipeline

1. Read all 12 `.xlsx` files (`header=1` for core, `header=0` for supporting).
2. Normalise tickers (`strip().upper()`) and years (`Mar-23` → `2023-03`).
3. Apply 16 DQ rules (DQ-01 … DQ-16) and log to `output/validation_failures.csv`.
4. Auto-create stub company rows for tickers found in statements but missing from `companies.xlsx` (8 tickers in the current dataset).
5. Load tables in FK-safe order into `data/nifty100.db`.
6. Write `output/load_audit.csv`.

## Sprint 1 exit checks

```sql
sqlite3 data/nifty100.db
SELECT COUNT(*) FROM companies;          -- 100 (92 master + 8 auto stubs)
SELECT COUNT(*) FROM stock_prices;       -- 5520
PRAGMA foreign_key_check;                -- 0 rows
```

```bash
python -m pytest tests/ -v
```

## Sprint 2 exit checks

```sql
sqlite3 data/nifty100.db
SELECT COUNT(*) FROM financial_ratios;   -- 1164
PRAGMA table_info(financial_ratios);     -- 41 columns
SELECT COUNT(*) FROM financial_ratios WHERE composite_quality_score IS NOT NULL;  -- 1161
```

```bash
python -m pytest tests/kpi/test_ratios.py -v
```

```bash
# Verify output files
ls output/
# Should show: load_audit.csv, validation_failures.csv, ratio_edge_cases.log, capital_allocation.csv
```

## Data note

Your `companies.xlsx` contains **92** tickers, while P&L/BS/CF files reference **8 additional** tickers (`WIPRO`, `VEDL`, `ZOMATO`, etc.). The loader adds minimal stub rows so FK constraints pass and financial history loads. To keep exactly 92 companies, add those 8 companies to `companies.xlsx` with full metadata and remove the stubs from the DB after reload.

TTM rows (100 in P&L) are excluded per DQ-07 (unparseable annual year label).
