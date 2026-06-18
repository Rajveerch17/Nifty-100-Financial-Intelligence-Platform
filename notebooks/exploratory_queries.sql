-- Nifty 100 Sprint 1 exploratory queries
-- Run with: sqlite3 data/nifty100.db < notebooks/exploratory_queries.sql

.headers on
.mode column

-- 1. Row counts for all core tables
SELECT 'companies' AS table_name, COUNT(*) AS row_count FROM companies
UNION ALL SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL SELECT 'financial_ratios', COUNT(*) FROM financial_ratios
UNION ALL SELECT 'documents', COUNT(*) FROM documents
UNION ALL SELECT 'sectors', COUNT(*) FROM sectors;

-- 2. Foreign key integrity check (expect 0 rows)
PRAGMA foreign_key_check;

-- 3. Companies with fewer than 5 years of P&L history
SELECT p.company_id, COUNT(*) AS pl_years
FROM profitandloss p
GROUP BY p.company_id
HAVING pl_years < 5
ORDER BY pl_years, p.company_id;

-- 4. Null coverage in key P&L metrics
SELECT
    SUM(CASE WHEN sales IS NULL THEN 1 ELSE 0 END) AS null_sales,
    SUM(CASE WHEN net_profit IS NULL THEN 1 ELSE 0 END) AS null_net_profit,
    SUM(CASE WHEN eps IS NULL THEN 1 ELSE 0 END) AS null_eps
FROM profitandloss;

-- 5. Year range coverage per statement type
SELECT 'profitandloss' AS dataset, MIN(year) AS min_year, MAX(year) AS max_year, COUNT(DISTINCT year) AS distinct_years FROM profitandloss
UNION ALL
SELECT 'balancesheet', MIN(year), MAX(year), COUNT(DISTINCT year) FROM balancesheet
UNION ALL
SELECT 'cashflow', MIN(year), MAX(year), COUNT(DISTINCT year) FROM cashflow;

-- 6. Sector distribution
SELECT broad_sector, COUNT(*) AS company_count
FROM sectors
GROUP BY broad_sector
ORDER BY company_count DESC;

-- 7. Top 10 companies by latest-year revenue
WITH latest AS (
    SELECT company_id, MAX(year) AS year
    FROM profitandloss
    GROUP BY company_id
)
SELECT p.company_id, p.year, p.sales, p.net_profit
FROM profitandloss p
JOIN latest l ON p.company_id = l.company_id AND p.year = l.year
ORDER BY p.sales DESC
LIMIT 10;

-- 8. Balance sheet rows failing strict asset = liability equality
SELECT company_id, year, total_assets, total_liabilities,
       ABS(total_assets - total_liabilities) AS diff
FROM balancesheet
WHERE total_assets != total_liabilities
ORDER BY diff DESC
LIMIT 20;

-- 9. Cash flow component reconciliation gaps (> 10 crore)
SELECT company_id, year, operating_activity, investing_activity, financing_activity, net_cash_flow,
       (operating_activity + investing_activity + financing_activity - net_cash_flow) AS gap
FROM cashflow
WHERE ABS(operating_activity + investing_activity + financing_activity - net_cash_flow) > 10
ORDER BY ABS(gap) DESC
LIMIT 20;

-- 10. Monthly price history completeness (expect 60 rows per company)
SELECT company_id, COUNT(*) AS months_loaded
FROM stock_prices
GROUP BY company_id
HAVING months_loaded != 60
ORDER BY months_loaded, company_id;
