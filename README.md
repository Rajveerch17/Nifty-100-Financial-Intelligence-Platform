# Nifty 100 Financial Intelligence Platform

Sprint 1 deliverable: Excel → SQLite ETL pipeline for 12 datasets and 12 database tables.

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

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Load data into database
python -m src.etl.loader      # or: .\load.ps1 (Windows script)

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
| `db/schema.sql` | 12-table schema with FK constraints |
| `src/etl/` | `loader.py`, `validator.py`, `normaliser.py` |
| `output/` | `load_audit.csv`, `validation_failures.csv` |
| `notebooks/exploratory_queries.sql` | 10 SQL sanity-check queries |
| `tests/etl/` | 35+ unit tests |

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

## Data note

Your `companies.xlsx` contains **92** tickers, while P&L/BS/CF files reference **8 additional** tickers (`WIPRO`, `VEDL`, `ZOMATO`, etc.). The loader adds minimal stub rows so FK constraints pass and financial history loads. To keep exactly 92 companies, add those 8 companies to `companies.xlsx` with full metadata and remove the stubs from the DB after reload.

TTM rows (100 in P&L) are excluded per DQ-07 (unparseable annual year label).
