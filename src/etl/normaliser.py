"""Field normalisation utilities for Nifty 100 ETL pipeline."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

MONTH_MAP = {
    "jan": "01",
    "feb": "02",
    "mar": "03",
    "apr": "04",
    "may": "05",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "sep": "09",
    "oct": "10",
    "nov": "11",
    "dec": "12",
}

YEAR_PATTERN = re.compile(r"^\d{4}-\d{2}$")
TICKER_PATTERN = re.compile(r"^[A-Z0-9&-]{2,12}$")

TICKER_ALIASES = {
    "AGTL": "ATGL",
}


def _two_digit_year(year_suffix: str) -> str:
    value = int(year_suffix)
    return str(2000 + value if value <= 50 else 1900 + value)


def normalize_year(value: Any) -> str | None:
    """Convert assorted year labels to canonical YYYY-MM format."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    if isinstance(value, int):
        return f"{value:04d}-03"

    text = str(value).strip()
    if not text:
        return None

    if text.upper() == "TTM":
        return None

    if YEAR_PATTERN.match(text):
        return text

    match = re.match(r"^([A-Za-z]{3})\s+(\d{4})\b", text)
    if match:
        month = MONTH_MAP[match.group(1).lower()]
        return f"{match.group(2)}-{month}"

    match = re.match(r"^([A-Za-z]{3})-(\d{2})$", text)
    if match:
        month = MONTH_MAP[match.group(1).lower()]
        year = _two_digit_year(match.group(2))
        return f"{year}-{month}"

    match = re.match(r"^([A-Za-z]{3})\s+(\d{4})$", text)
    if match:
        month = MONTH_MAP[match.group(1).lower()]
        return f"{match.group(2)}-{month}"

    match = re.match(r"^(\d{4})$", text)
    if match:
        return f"{match.group(1)}-03"

    return None


def normalize_ticker(value: Any) -> str | None:
    """Normalise NSE ticker symbols to uppercase stripped form."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    ticker = str(value).strip().upper()
    if not ticker:
        return None
    return TICKER_ALIASES.get(ticker, ticker)


def is_valid_ticker(ticker: str | None) -> bool:
    if ticker is None:
        return False
    return bool(TICKER_PATTERN.match(ticker))


def normalize_company_name(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    return re.sub(r"\s+", " ", str(value).replace("\n", " ")).strip()


def normalize_dataframe_tickers(
    df: pd.DataFrame, column: str = "company_id"
) -> pd.DataFrame:
    """Apply ticker normalisation to a DataFrame column in place."""
    if column not in df.columns:
        return df
    df[column] = df[column].map(normalize_ticker)
    return df


def normalize_dataframe_years(df: pd.DataFrame, column: str = "year") -> pd.DataFrame:
    """Apply year normalisation to a DataFrame column in place."""
    if column not in df.columns:
        return df
    df[column] = df[column].map(normalize_year)
    return df


def deduplicate_time_series(
    df: pd.DataFrame, keys: list[str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Remove duplicate composite keys, keeping the last occurrence."""
    duplicated_mask = df.duplicated(subset=keys, keep=False)
    duplicates = df[duplicated_mask].copy()
    deduped = df.drop_duplicates(subset=keys, keep="last").copy()
    return deduped, duplicates
