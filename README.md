# Nifty 100 Financial Intelligence Platform

Sprint 1 deliverable: Excel → SQLite ETL pipeline for 12 datasets and 12 database tables.
Sprint 2 deliverable: Financial Ratio Engine computing 50+ KPIs for all company-year combinations.
Sprint 3 deliverable: Multi-criteria financial screener, peer comparison engine, and REST API.
Sprint 4 deliverable: Streamlit dashboard with 8 screens and valuation module.
Sprint 5 deliverable: NLP module for auto-generating pros/cons, Cash Flow Intelligence, and PDF tearsheet reports for all companies.
Sprint 6 deliverable: KMeans clustering, cluster profiling, FastAPI server with routers, and comprehensive testing.

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

## Module 5 Sprint 5 Status: ✅ COMPLETED

All Sprint 5 tasks have been successfully completed and verified:
- ✅ NLP Analysis Text Parser with regex pattern extraction from analysis.xlsx
- ✅ Auto Pros/Cons Generator with 12 pro rules and 12 con rules
- ✅ Cash Flow Intelligence module with CFO Quality Score, CapEx Intensity, and Distress Signals
- ✅ Capital Allocation Report with pattern change detection
- ✅ PDF Tearsheet Generator (2-page professional layout)
- ✅ Batch generation: 99 company tearsheets (1 skipped due to insufficient data)
- ✅ Portfolio Summary PDF with 101 pages (1 title + 100 companies)
- ✅ output/analysis_parsed.csv - 63 parsed entries from text fields
- ✅ output/parse_failures.csv - 17 entries logged that didn't match pattern
- ✅ output/pros_cons_generated.csv - 568 entries (401 pros, 167 cons) with 78.5% avg confidence
- ✅ output/cashflow_intelligence.xlsx - 100 companies analyzed with CFO quality, CapEx intensity, FCF metrics
- ✅ output/distress_alerts.csv - 13 companies flagged with distress signals
- ✅ output/pattern_changes.csv - 42 companies with YoY capital allocation pattern changes
- ✅ reports/tearsheets/ - 99 PDF tearsheets (2 pages each)
- ✅ reports/portfolio/portfolio_summary.pdf - 101 pages with trend arrows
- ✅ 100% company coverage: Every company has at least 1 pro and 1 con
- ✅ All existing dashboard functionality intact (no breaking changes)

## Module 6 Sprint 6 Status: ✅ COMPLETED

All Sprint 6 tasks have been successfully completed and verified:
- ✅ KMeans Clustering Engine with 5 clusters (src/analytics/clustering.py)
- ✅ Features: ROE, D/E, Revenue CAGR 5yr, FCF CAGR 5yr, OPM
- ✅ Missing value imputation with sector median
- ✅ StandardScaler normalization
- ✅ Elbow plot generation (reports/elbow_plot.png)
- ✅ Cluster labels output (output/cluster_labels.csv)
- ✅ Cluster profiling with mean/median per cluster
- ✅ Descriptive cluster names assigned
- ✅ Correlation heatmap (reports/correlation_heatmap.png)
- ✅ Outlier detection with Z-score > 3 (output/outlier_report.csv)
- ✅ Portfolio statistics P10-P90 (output/portfolio_stats.csv)
- ✅ FastAPI server scaffold with routers (src/api/main.py)
- ✅ CORS middleware for all origins
- ✅ Request logging middleware
- ✅ 8 router modules: health, companies, screener, sectors, peers, valuation, portfolio, documents
- ✅ 16 API endpoints implemented
- ✅ 26 API unit tests passing
- ✅ 6 performance tests passing
- ✅ 121 ETL/KPI/DQ unit tests passing
- ✅ API server verified at http://localhost:8000
- ✅ OpenAPI documentation available at /docs

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

# Generate NLP analysis and pros/cons
python -m src.nlp.parser
python -m src.nlp.pros_cons_generator

# Generate cash flow intelligence
python -m src.analytics.cashflow_kpis
python -m src.analytics.capital_allocation_report

# Generate PDF tearsheets and portfolio summary
python -m src.reports.tearsheet
python -m src.reports.portfolio_summary

# Run clustering and cluster statistics
python -m src.analytics.clustering
python -m src.analytics.cluster_stats

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
| `src/analytics/` | `peer.py` - Peer comparison, `charting.py` - Radar charts, `valuation.py` - Valuation, `cashflow_kpis.py` - Cash flow intelligence, `capital_allocation_report.py` - Pattern analysis, `clustering.py` - KMeans clustering, `cluster_stats.py` - Cluster profiling |
| `src/nlp/` | `parser.py` - Text field parser, `pros_cons_generator.py` - Auto pros/cons with 12+12 rules |
| `src/reports/` | `tearsheet.py` - 2-page PDF generator, `portfolio_summary.py` - Portfolio PDF |
| `src/api/` | `main.py` - FastAPI REST server, `routers/` - 8 router modules (health, companies, screener, sectors, peers, valuation, portfolio, documents) |
| `src/dashboard/` | `app.py` - Streamlit dashboard, `pages/` - 8 screen files, `utils/db.py` - Cached data loader |
| `config/` | `screener_config.yaml` - Screener presets and filter definitions |
| `output/` | CSV/Excel analysis files: load_audit, validation_failures, ratio_edge_cases, capital_allocation, screener_output, peer_comparison, valuation_summary, valuation_flags, analysis_parsed, parse_failures, pros_cons_generated, cashflow_intelligence, distress_alerts, pattern_changes, cluster_labels, outlier_report, portfolio_stats |
| `reports/tearsheets/` | 99 company PDF tearsheets (2 pages each) |
| `reports/portfolio/` | Portfolio summary PDF (101 pages) |
| `reports/` | elbow_plot.png, correlation_heatmap.png |
| `notebooks/exploratory_queries.sql` | 10 SQL sanity-check queries |
| `tests/etl/` | 35+ unit tests for ETL pipeline |
| `tests/kpi/` | 42 unit tests for ratio engine |
| `tests/dq/` | 14 unit tests for data quality rules |
| `tests/api/` | 26 unit tests for API endpoints |
| `tests/performance/` | 6 performance tests for API |

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

## Sprint 5 exit checks

```bash
# Run NLP modules
python -m src.nlp.parser
python -m src.nlp.pros_cons_generator
# Should generate: output/analysis_parsed.csv (63 entries)
# Should generate: output/parse_failures.csv (17 entries)
# Should generate: output/pros_cons_generated.csv (568 entries)

# Run cash flow intelligence
python -m src.analytics.cashflow_kpis
python -m src.analytics.capital_allocation_report
# Should generate: output/cashflow_intelligence.xlsx (100 companies)
# Should generate: output/distress_alerts.csv (13 companies)
# Should generate: output/pattern_changes.csv (42 companies)

# Generate PDF reports
python -m src.reports.tearsheet
python -m src.reports.portfolio_summary
# Should generate: reports/tearsheets/*.pdf (99 tearsheets)
# Should generate: reports/portfolio/portfolio_summary.pdf (101 pages)
```

```bash
# Verify all outputs
ls output/ | wc -l        # Should show 15+ files
ls reports/tearsheets/ | wc -l  # Should show 99 PDF files
ls reports/portfolio/ | wc -l   # Should show 1 PDF file
```

## Sprint 6 exit checks

```bash
# Run clustering
python -m src.analytics.clustering
# Should generate: reports/elbow_plot.png, output/cluster_labels.csv

# Run cluster statistics
python -m src.analytics.cluster_stats
# Should generate: reports/correlation_heatmap.png, output/outlier_report.csv, output/portfolio_stats.csv

# Start API server
python -m src.api.main
# Server runs on http://0.0.0.0:8000
# Test health endpoint: curl http://localhost:8000/api/v1/health
# Test docs: http://localhost:8000/docs

# Run all tests
python -m pytest tests/ -v
# Should show: 153 tests passing (121 ETL/KPI/DQ + 26 API + 6 performance)
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

## NLP & PDF Reports (Sprint 5)

### NLP Analysis Text Parser
- Parses text fields from analysis.xlsx using regex pattern `(\d+)\s*Years?:?\s*([\d.]+)%`
- Extracts period and value from formats like "10 Years: 21%"
- Generates structured output: `output/analysis_parsed.csv`
- Logs failures: `output/parse_failures.csv`

### Auto Pros/Cons Generator
- Implements 12 pro rules and 12 con rules
- Assigns confidence scores (0-100), only includes entries > 60% confidence
- Ensures 100% company coverage (at least 1 pro and 1 con per company)
- Generates: `output/pros_cons_generated.csv` (568 entries, 78.5% avg confidence)

**Pro Rules:** ROE > 20% sustained, FCF positive 5+ years, debt-free, revenue CAGR > 15%, OPM > 25%, PAT CAGR > 20%, high ICR, dividend yield > 2%, EPS CAGR > 15%, improving ROE, operating leverage, self-sustaining growth

**Con Rules:** D/E > 2.0, FCF negative 3+ years, declining OPM, net loss, declining revenue, ICR < 1.5, dividend payout > 100%, rising D/E, declining EPS, ROCE < 10%, high net debt, low revenue growth

### Cash Flow Intelligence
- CFO Quality Score: CFO/PAT ratio averaged over 5 years
  - High Quality (>1.0), Moderate (0.5-1.0), Accrual Risk (<0.5)
- CapEx Intensity: abs(investing_activity) / sales × 100
  - Asset Light (<3%), Moderate (3-8%), Capital Intensive (>8%)
- Distress Signal: CFO < 0 AND CFF > 0 (13 companies flagged)
- Deleveraging Flag: CFF < 0 AND declining borrowings (28 companies)
- Capital Allocation: 8 patterns (Self-Sufficient Growth, Debt-Funded Growth, Distress Signal, etc.)
- Generates: `output/cashflow_intelligence.xlsx`, `output/distress_alerts.csv`

### PDF Tearsheets
- 2-page professional tearsheets for all companies
- **Page 1:** Header, 6 KPI tiles (ROE, ROCE, OPM, D/E, ICR, EPS), 5-year financial trend table
- **Page 2:** Cash flow intelligence, investment strengths (top 5 pros), investment concerns (top 5 cons)
- Automatic text wordwrap prevents overflow
- Generated: 99 tearsheets in `reports/tearsheets/`
- Skipped: 1 company (JIOFIN - insufficient data)

### Portfolio Summary
- Comprehensive 101-page PDF (1 title + 100 companies)
- One page per company in alphabetical order by ticker
- Company name, sector, top 6 KPIs with trend arrows
- Trend logic: ↑ up (>2% change), → flat (±2%), ↓ down (<-2%)
- Generated: `reports/portfolio/portfolio_summary.pdf`

## Data note

Your `companies.xlsx` contains **92** tickers, while P&L/BS/CF files reference **8 additional** tickers (`WIPRO`, `VEDL`, `ZOMATO`, etc.). The loader adds minimal stub rows so FK constraints pass and financial history loads. To keep exactly 92 companies, add those 8 companies to `companies.xlsx` with full metadata and remove the stubs from the DB after reload.

TTM rows (100 in P&L) are excluded per DQ-07 (unparseable annual year label).

## Complete Pipeline Execution

To run the complete pipeline from data loading to report generation:

```bash
# 1. Load data and compute ratios
python -m src.etl.loader
python -m src.kpi.ratio_engine

# 2. Run analytics engines
python -m src.screener.engine
python -m src.analytics.peer
python -m src.analytics.valuation

# 3. Generate NLP analysis and reports
python -m src.nlp.parser
python -m src.nlp.pros_cons_generator
python -m src.analytics.cashflow_kpis
python -m src.analytics.capital_allocation_report

# 4. Generate PDF reports
python -m src.reports.tearsheet
python -m src.reports.portfolio_summary

# 5. Launch dashboard
streamlit run src/dashboard/app.py
```

## Key Features Summary

### Data Pipeline (Sprint 1)
- 12-table SQLite database with FK integrity
- 100 companies, 1,164 financial ratio records
- 16 data quality rules with validation logging
- Auto-stub generation for missing companies

### Financial Analytics (Sprint 2)
- 50+ KPIs computed per company-year
- CAGR engine (3yr, 5yr, 10yr) with edge case handling
- Composite quality score (0-100 scale)
- 8-pattern capital allocation classification

### Screening & Comparison (Sprint 3)
- Multi-criteria screener with 6 presets
- 11 peer groups with percentile rankings
- Radar chart visualizations
- REST API with 5 endpoints

### Dashboard (Sprint 4)
- 8 interactive screens
- Real-time filtering and search
- 10-year trend analysis
- Sector bubble charts
- CSV export functionality

### Intelligence & Reports (Sprint 5)
- NLP text parsing with confidence scoring
- Auto pros/cons generation (568 entries)
- Cash flow intelligence with distress detection
- 99 PDF company tearsheets (2 pages each)
- 101-page portfolio summary PDF
- 100% company coverage guarantee

## Documentation

- `SPRINT5_COMPLETION_SUMMARY.md` - Detailed Sprint 5 deliverables and verification
- `DASHBOARD_FIXES_SUMMARY.md` - Dashboard testing results and bug fixes
- `Nifty100_Project_Document_FINAL.pdf` - Complete project specification

## Dependencies

Core packages:
- pandas, openpyxl - Data processing
- sqlite3 - Database
- pyyaml - Configuration
- fastapi, uvicorn - REST API
- streamlit, plotly - Dashboard
- pytest - Testing
- reportlab - PDF generation

See `requirements.txt` for complete list with versions.

