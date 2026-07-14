# Nifty 100 Financial Intelligence Platform

Sprint 1 deliverable: Excel → SQLite ETL pipeline for 12 datasets and 12 database tables.
Sprint 2 deliverable: Financial Ratio Engine computing 50+ KPIs for all company-year combinations.
Sprint 3 deliverable: Multi-criteria financial screener, peer comparison engine, and REST API.
Sprint 4 deliverable: Streamlit dashboard with 8 screens and valuation module.

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

## Module 3 Sprint 3 Status: ✅ COMPLETED

All Sprint 3 tasks have been successfully completed and verified:
- ✅ Multi-criteria financial screener with 6 preset templates
- ✅ 15 filtering metrics with sector carve-outs (e.g., skip D/E for Financials)
- ✅ Composite quality score (0-100 scale) with P10/P90 winsorisation
- ✅ 6 preset screeners: quality_compounder, value_pick, growth_accelerator, dividend_champion, debt_free_blue_chip, turnaround_watch
- ✅ Peer comparison engine with 11 peer groups and 10 ranking metrics
- ✅ 528 peer percentile ranks computed and saved to database
- ✅ Radar chart generator for peer group visualizations
- ✅ FastAPI REST server with 5 endpoints
- ✅ API endpoints: /api/v1/health, /api/v1/companies, /api/v1/screener, /api/v1/peer-groups, /api/v1/peer-comparison/{ticker}
- ✅ 9 API unit tests passing
- ✅ output/screener_output.xlsx generated with 6 preset sheets
- ✅ output/peer_comparison.xlsx generated with 11 peer group sheets

## Module 4 Sprint 4 Status: ✅ COMPLETED

All Sprint 4 tasks have been successfully completed and verified:
- ✅ Streamlit dashboard with 8 screens (Home, Company Profile, Screener, Peer Comparison, Trend Analysis, Sector Analysis, Capital Allocation, Annual Reports)
- ✅ Home screen with 6 summary KPI tiles, sector breakdown donut chart, and top-5 companies by quality score
- ✅ Company Profile screen with search, KPI tiles, 10-year charts, and pros/cons badges
- ✅ Screener screen with 10 metric sliders, 6 preset buttons, live results table, and CSV download
- ✅ Peer Comparison screen with radar chart and side-by-side KPI table
- ✅ Trend Analysis screen with multi-metric selector and 10-year line chart with YoY annotations
- ✅ Sector Analysis screen with bubble chart (Revenue vs ROE) and sector median KPI bar chart
- ✅ Capital Allocation Map screen with treemap of 8 capital allocation patterns
- ✅ Annual Reports screen with BSE PDF links and availability status
- ✅ Valuation module with FCF yield computation and overvaluation flags
- ✅ output/valuation_summary.xlsx generated with 92 companies
- ✅ output/valuation_flags.csv generated with 72 flagged companies
- ✅ Cached data loader with @st.cache_data(ttl=600) for all database queries
- ✅ Year selector (2019-2024) in sidebar for all screens

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Load data into database
python -m src.etl.loader      # or: .\load.ps1 (Windows script)

# Compute financial ratios
python -m src.kpi.ratio_engine

# Run screener engine
python -m src.screener.engine

# Run peer comparison engine
python -m src.analytics.peer

# Run valuation module
python -m src.analytics.valuation

# Start Streamlit dashboard
streamlit run src/dashboard/app.py

# Start API server
python -m src.api.main

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
| `db/schema.sql` | 14-table schema with FK constraints (12 base + financial_ratios + peer_percentiles) |
| `src/etl/` | `loader.py`, `validator.py`, `normaliser.py` |
| `src/kpi/` | `ratio_engine.py` - Financial KPI computation engine |
| `src/screener/` | `engine.py` - Multi-criteria financial screener |
| `src/analytics/` | `peer.py` - Peer comparison engine, `charting.py` - Radar chart generator, `valuation.py` - Valuation module |
| `src/api/` | `main.py` - FastAPI REST server |
| `src/dashboard/` | `app.py` - Streamlit dashboard, `pages/` - 8 screen files, `utils/db.py` - Cached data loader |
| `config/` | `screener_config.yaml` - Screener presets and filter definitions |
| `output/` | `load_audit.csv`, `validation_failures.csv`, `ratio_edge_cases.log`, `capital_allocation.csv`, `screener_output.xlsx`, `peer_comparison.xlsx`, `valuation_summary.xlsx`, `valuation_flags.csv` |
| `notebooks/exploratory_queries.sql` | 10 SQL sanity-check queries |
| `tests/etl/` | 35+ unit tests for ETL pipeline |
| `tests/kpi/` | 42 unit tests for ratio engine |
| `tests/api/` | 9 unit tests for API endpoints |

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

## Sprint 3 exit checks

```sql
sqlite3 data/nifty100.db
SELECT COUNT(*) FROM peer_percentiles;   -- 528
PRAGMA table_info(peer_percentiles);     -- 6 columns (company_id, peer_group, metric, value, percentile_rank, year)
```

```bash
python -m pytest tests/api/ -v
```

```bash
# Run screener engine
python -m src.screener.engine
# Should generate: output/screener_output.xlsx with 6 preset sheets

# Run peer comparison engine
python -m src.analytics.peer
# Should generate: output/peer_comparison.xlsx with 11 peer group sheets
```

```bash
# Start API server
python -m src.api.main
# Server runs on http://0.0.0.0:8000
# Test health endpoint: curl http://localhost:8000/api/v1/health
```

## Sprint 4 exit checks

```bash
# Run valuation module
python -m src.analytics.valuation
# Should generate: output/valuation_summary.xlsx with 92 companies
# Should generate: output/valuation_flags.csv with flagged companies

# Start Streamlit dashboard
streamlit run src/dashboard/app.py
# Dashboard opens at http://localhost:8501
# Verify all 8 screens load without errors
```

```bash
# Verify output files
ls output/
# Should show: load_audit.csv, validation_failures.csv, ratio_edge_cases.log, capital_allocation.csv, screener_output.xlsx, peer_comparison.xlsx, valuation_summary.xlsx, valuation_flags.csv
```

## Dashboard Screens

The Streamlit dashboard includes 8 screens:

1. **Home** - Summary KPI tiles (Average ROE, Median P/E, Median D/E, Total Companies, Median Revenue CAGR 5yr, Debt-Free Companies), sector breakdown donut chart, and top-5 companies by composite quality score

2. **Company Profile** - Company search with autocomplete, company card with details, 6 KPI tiles (ROE, ROCE, NPM, D/E, Revenue CAGR 5yr, FCF), 10-year Revenue & Net Profit bar chart, ROE & ROCE dual-axis line chart, and pros/cons badges

3. **Screener** - 10 metric sliders (ROE, D/E, FCF, Revenue CAGR, PAT CAGR, OPM, P/E, P/B, Dividend Yield, ICR), 6 preset buttons (Quality, Value, Growth, Dividend, Debt-Free, Turnaround), live results table with CSV download

4. **Peer Comparison** - Peer group dropdown (11 groups), radar chart showing company vs peer group average, side-by-side KPI table with benchmark highlighting

5. **Trend Analysis** - Company search, multi-metric selector (up to 3 metrics), 10-year line chart with YoY % change annotations

6. **Sector Analysis** - Sector dropdown, bubble chart (Revenue vs ROE with Market Cap size), sector median KPI bar chart

7. **Capital Allocation** - Treemap of 92 companies grouped by 8 capital allocation patterns, pattern selector for detailed view

8. **Annual Reports** - Company search, list of available years with BSE PDF links, availability status indicators

## Data note

Your `companies.xlsx` contains **92** tickers, while P&L/BS/CF files reference **8 additional** tickers (`WIPRO`, `VEDL`, `ZOMATO`, etc.). The loader adds minimal stub rows so FK constraints pass and financial history loads. To keep exactly 92 companies, add those 8 companies to `companies.xlsx` with full metadata and remove the stubs from the DB after reload.

TTM rows (100 in P&L) are excluded per DQ-07 (unparseable annual year label).


## Module 4 Sprint 4 Status: ✅ COMPLETED

All Sprint 4 tasks have been successfully completed and verified:
- ✅ Streamlit dashboard with 8 fully functional screens
- ✅ Home screen with summary KPIs, sector breakdown, and top 5 companies
- ✅ Company Profile screen with search, KPIs, charts, and pros/cons
- ✅ Screener screen with 10 sliders, 6 presets, and CSV export
- ✅ Peer Comparison screen with radar charts and KPI tables
- ✅ Trend Analysis screen with 10-year multi-metric overlay
- ✅ Sector Analysis screen with bubble charts and median KPIs
- ✅ Capital Allocation Map with treemap visualization
- ✅ Annual Reports screen with BSE PDF links
- ✅ All screens load without errors for 92 companies
- ✅ Comprehensive testing: 20/20 tests passed (100%)
- ✅ Load times < 3 seconds for all screens
- ✅ Defensive programming for missing data
- ✅ Year selector (FY 2019-2024) across all screens

### Running the Dashboard

```bash
streamlit run src/dashboard/app.py
```

Dashboard accessible at:
- Local: http://localhost:8501
- Network: http://192.168.1.4:8501

### Dashboard Screens

1. **🏠 Home** - Summary KPIs, sector breakdown donut chart, top 5 companies by quality score
2. **🏢 Company Profile** - Company search, 6 KPI tiles, 10-year revenue/profit charts, ROE/ROCE trends, pros & cons
3. **🔍 Screener** - 10 metric sliders, 6 preset filters (Quality, Value, Growth, etc.), live results, CSV download
4. **👥 Peer Comparison** - 11 peer groups, radar chart comparison, side-by-side KPI table, benchmark highlighting
5. **📈 Trend Analysis** - Multi-metric overlay (up to 3 metrics), 10-year line chart, YoY % annotations
6. **🏭 Sector Analysis** - Sector dropdown, bubble chart (Revenue vs ROE), median KPI bar chart, company list
7. **💰 Capital Allocation** - Treemap by allocation pattern (8 patterns), market cap sizing, quality score coloring
8. **📄 Annual Reports** - Company search, annual reports by year, BSE PDF links, availability status

### Testing the Dashboard

Run comprehensive test suite:
```bash
python test_dashboard.py
```

Results: 20/20 tests passing (100%)
- Tested across 5 sectors: IT, Financials, Consumer Staples, Energy, Healthcare
- All 8 screens verified with multiple tickers
- See `DASHBOARD_FIXES_SUMMARY.md` for detailed test results

### Bug Fixes Completed

All critical errors resolved:
- ✅ Fixed KeyError 'fcf_cagr_5yr' in screener
- ✅ Fixed KeyError 'return_on_capital_employed_pct' in peers
- ✅ Fixed ModuleNotFoundError 'src' in all screens
- ✅ Added empty data handling in trends screen
- ✅ Verified annual reports screen functionality

See `DASHBOARD_FIXES_SUMMARY.md` for complete details.
