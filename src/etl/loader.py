"""Excel loader and SQLite database builder for Nifty 100 ETL pipeline."""

from __future__ import annotations

import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from src.etl.normaliser import normalize_company_name, normalize_ticker, normalize_year
from src.etl.validator import run_all_validations

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

CORE_FILES = {
    "companies": ("companies.xlsx", 1),
    "profitandloss": ("profitandloss.xlsx", 1),
    "balancesheet": ("balancesheet.xlsx", 1),
    "cashflow": ("cashflow.xlsx", 1),
    "analysis": ("analysis.xlsx", 1),
    "documents": ("documents.xlsx", 1),
    "prosandcons": ("prosandcons.xlsx", 1),
}

SUPPORTING_FILES = {
    "sectors": ("sectors.xlsx", 0),
    "stock_prices": ("stock_prices.xlsx", 0),
    "market_cap": ("market_cap.xlsx", 0),
    # financial_ratios table is populated by ratio_engine, not loaded from Excel
    "peer_groups": ("peer_groups.xlsx", 0),
}

LOAD_ORDER = [
    "companies",
    "sectors",
    "analysis",
    "prosandcons",
    "documents",
    "peer_groups",
    "profitandloss",
    "balancesheet",
    "cashflow",
    # financial_ratios is populated by ratio_engine after load
    "market_cap",
    "stock_prices",
]

TABLE_COLUMNS = {
    "companies": [
        "id",
        "company_logo",
        "company_name",
        "chart_link",
        "about_company",
        "website",
        "nse_profile",
        "bse_profile",
        "face_value",
        "book_value",
        "roce_percentage",
        "roe_percentage",
    ],
    "profitandloss": [
        "id",
        "company_id",
        "year",
        "sales",
        "expenses",
        "operating_profit",
        "opm_percentage",
        "other_income",
        "interest",
        "depreciation",
        "profit_before_tax",
        "tax_percentage",
        "net_profit",
        "eps",
        "dividend_payout",
    ],
    "balancesheet": [
        "id",
        "company_id",
        "year",
        "equity_capital",
        "reserves",
        "borrowings",
        "other_liabilities",
        "total_liabilities",
        "fixed_assets",
        "cwip",
        "investments",
        "other_asset",
        "total_assets",
    ],
    "cashflow": [
        "id",
        "company_id",
        "year",
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow",
    ],
    "analysis": [
        "id",
        "company_id",
        "compounded_sales_growth",
        "compounded_profit_growth",
        "stock_price_cagr",
        "roe",
    ],
    "documents": ["id", "company_id", "year", "annual_report"],
    "prosandcons": ["id", "company_id", "pros", "cons"],
    "sectors": [
        "id",
        "company_id",
        "broad_sector",
        "sub_sector",
        "index_weight_pct",
        "market_cap_category",
    ],
    "stock_prices": [
        "id",
        "company_id",
        "date",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
        "adjusted_close",
    ],
    "market_cap": [
        "id",
        "company_id",
        "year",
        "market_cap_crore",
        "enterprise_value_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "dividend_yield_pct",
    ],
    # financial_ratios table is populated by ratio_engine, not loaded from Excel
    "peer_groups": ["id", "peer_group_name", "company_id", "is_benchmark"],
}


def get_paths() -> dict[str, Path]:
    raw_dir = PROJECT_ROOT / Path(__import__("os").getenv("RAW_DATA_DIR", "data/raw"))
    supporting_dir = PROJECT_ROOT / Path(
        __import__("os").getenv("SUPPORTING_DATA_DIR", "data/supporting")
    )
    db_path = PROJECT_ROOT / Path(
        __import__("os").getenv("DB_PATH", "data/nifty100.db")
    )
    output_dir = PROJECT_ROOT / Path(__import__("os").getenv("OUTPUT_DIR", "output"))
    schema_path = PROJECT_ROOT / "db" / "schema.sql"
    return {
        "raw_dir": raw_dir,
        "supporting_dir": supporting_dir,
        "db_path": db_path,
        "output_dir": output_dir,
        "schema_path": schema_path,
    }


def read_excel_file(path: Path, header_row: int) -> pd.DataFrame:
    return pd.read_excel(path, header=header_row)


def synthesize_missing_companies(
    companies: pd.DataFrame, datasets: dict[str, pd.DataFrame]
) -> tuple[pd.DataFrame, list[str]]:
    """Create stub company rows for tickers referenced in child tables but absent from master."""
    known_ids = set(companies["id"].map(normalize_ticker).dropna())
    referenced: set[str] = set()

    child_tables = [
        "profitandloss",
        "balancesheet",
        "cashflow",
        "analysis",
        "documents",
        "prosandcons",
        "sectors",
        "stock_prices",
        "market_cap",
        # financial_ratios is populated by ratio_engine
        "peer_groups",
    ]
    for table_name in child_tables:
        frame = datasets[table_name]
        column = "id" if table_name == "companies" else "company_id"
        if column not in frame.columns:
            continue
        referenced.update(frame[column].map(normalize_ticker).dropna())

    missing = sorted(referenced - known_ids)
    if not missing:
        return companies, missing

    stubs = pd.DataFrame(
        {
            "id": missing,
            "company_logo": [None] * len(missing),
            "company_name": missing,
            "chart_link": [None] * len(missing),
            "about_company": [None] * len(missing),
            "website": [None] * len(missing),
            "nse_profile": [None] * len(missing),
            "bse_profile": [None] * len(missing),
            "face_value": [1.0] * len(missing),
            "book_value": [None] * len(missing),
            "roce_percentage": [None] * len(missing),
            "roe_percentage": [None] * len(missing),
        }
    )
    return pd.concat([companies, stubs], ignore_index=True), missing


def load_all_excel_files(paths: dict[str, Path]) -> dict[str, pd.DataFrame]:
    datasets: dict[str, pd.DataFrame] = {}
    for name, (filename, header) in CORE_FILES.items():
        datasets[name] = read_excel_file(paths["raw_dir"] / filename, header)
    for name, (filename, header) in SUPPORTING_FILES.items():
        datasets[name] = read_excel_file(paths["supporting_dir"] / filename, header)
    return datasets


def prepare_companies(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    prepared["id"] = prepared["id"].map(normalize_ticker)
    prepared["company_name"] = prepared["company_name"].map(normalize_company_name)
    prepared["face_value"] = prepared["face_value"].fillna(1.0)
    return prepared


def prepare_peer_groups(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    prepared["is_benchmark"] = prepared["is_benchmark"].astype(int)
    return prepared


def prepare_table_frame(name: str, df: pd.DataFrame) -> pd.DataFrame:
    if name == "companies":
        return prepare_companies(df)
    if name == "peer_groups":
        return prepare_peer_groups(df)
    return df


def init_database(conn: sqlite3.Connection, schema_path: Path) -> None:
    conn.execute("PRAGMA foreign_keys = ON")
    schema_sql = schema_path.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    conn.commit()


def write_table(conn: sqlite3.Connection, table_name: str, df: pd.DataFrame) -> int:
    columns = TABLE_COLUMNS[table_name]
    frame = df[columns].copy()
    # Use smaller chunksize for large tables to avoid SQLite variable limit
    chunksize = 100 if table_name == "stock_prices" else 1000
    frame.to_sql(table_name, conn, if_exists="append", index=False, method="multi", chunksize=chunksize)
    return len(frame)


def build_load_audit_row(
    table_name: str,
    source_file: str,
    rows_in: int,
    rows_out: int,
    rejected: int,
    runtime_s: float,
    critical_rejections: int,
) -> dict[str, object]:
    return {
        "table": table_name,
        "source_file": source_file,
        "rows_in": rows_in,
        "rows_out": rows_out,
        "rejected": rejected,
        "critical_rejections": critical_rejections,
        "runtime_s": round(runtime_s, 3),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


def run_load() -> tuple[pd.DataFrame, pd.DataFrame]:
    paths = get_paths()
    paths["output_dir"].mkdir(parents=True, exist_ok=True)
    paths["db_path"].parent.mkdir(parents=True, exist_ok=True)

    if paths["db_path"].exists():
        paths["db_path"].unlink()

    missing_tickers: list[str] = []
    datasets = load_all_excel_files(paths)
    companies_raw = datasets["companies"].copy()
    companies_raw, missing_tickers = synthesize_missing_companies(
        companies_raw, datasets
    )
    datasets["companies"] = companies_raw
    if missing_tickers:
        datasets["_missing_company_stubs"] = pd.DataFrame({"id": missing_tickers})

    validation_result, validated = run_all_validations(datasets)

    conn = sqlite3.connect(paths["db_path"])
    try:
        init_database(conn, paths["schema_path"])
        audit_rows: list[dict[str, object]] = []

        for table_name in LOAD_ORDER:
            start = time.perf_counter()
            source_name = CORE_FILES.get(table_name, SUPPORTING_FILES.get(table_name))[
                0
            ]
            rows_in = len(datasets[table_name])
            if table_name == "companies" and missing_tickers:
                rows_in = rows_in - len(missing_tickers)
            prepared = prepare_table_frame(table_name, validated[table_name])
            if table_name == "companies":
                rejected = 0
                rows_out = len(prepared)
            else:
                rows_out = len(prepared)
                rejected = max(rows_in - rows_out, 0)
            critical_rejections = rejected
            rows_out = write_table(conn, table_name, prepared)
            runtime_s = time.perf_counter() - start
            audit_rows.append(
                build_load_audit_row(
                    table_name,
                    source_name,
                    rows_in,
                    rows_out,
                    rejected,
                    runtime_s,
                    critical_rejections,
                )
            )

        conn.commit()
        fk_issues = conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk_issues:
            raise RuntimeError(f"Foreign key check failed: {fk_issues}")
    finally:
        conn.close()

    audit_df = pd.DataFrame(audit_rows)
    failures_df = validation_result.to_dataframe()

    audit_df.to_csv(paths["output_dir"] / "load_audit.csv", index=False)
    failures_df.to_csv(paths["output_dir"] / "validation_failures.csv", index=False)
    if missing_tickers:
        pd.DataFrame(
            {
                "company_id": missing_tickers,
                "note": "Auto-generated stub from child tables",
            }
        ).to_csv(
            paths["output_dir"] / "missing_company_stubs.csv",
            index=False,
        )

    return audit_df, failures_df


def main() -> None:
    audit_df, failures_df = run_load()
    paths = get_paths()
    print(f"Database created at: {paths['db_path']}")
    print("\nLoad audit summary:")
    print(audit_df.to_string(index=False))
    print(f"\nValidation failures logged: {len(failures_df)}")
    print(
        f"Critical failures: {failures_df[failures_df['severity'] == 'CRITICAL'].shape[0] if not failures_df.empty else 0}"
    )


if __name__ == "__main__":
    main()
