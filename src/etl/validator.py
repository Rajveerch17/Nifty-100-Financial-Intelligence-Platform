"""Data quality validation rules (DQ-01 through DQ-16) for Nifty 100 ETL."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any

import pandas as pd
import requests

from src.etl.normaliser import is_valid_ticker, normalize_ticker, normalize_year

YEAR_PATTERN = re.compile(r"^\d{4}-\d{2}$")
FINANCIAL_SECTOR_KEYWORDS = {
    "BANK",
    "FIN",
    "LIFE",
    "INSUR",
    "HDFC",
    "ICICI",
    "SBI",
    "AXIS",
    "KOTAK",
    "BAJFIN",
    "CHOLA",
    "SHRIRAM",
    "LICI",
}


@dataclass
class ValidationFailure:
    rule_id: str
    rule_name: str
    severity: str
    company_id: str | None
    year: str | None
    field: str | None
    issue: str
    raw_value: str | None = None


@dataclass
class ValidationResult:
    failures: list[ValidationFailure] = field(default_factory=list)
    rejected_rows: dict[str, pd.DataFrame] = field(default_factory=dict)
    deduped_rows: dict[str, pd.DataFrame] = field(default_factory=dict)
    coerced_rows: dict[str, pd.DataFrame] = field(default_factory=dict)

    def add(
        self,
        rule_id: str,
        rule_name: str,
        severity: str,
        issue: str,
        company_id: str | None = None,
        year: str | None = None,
        field: str | None = None,
        raw_value: str | None = None,
    ) -> None:
        self.failures.append(
            ValidationFailure(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=severity,
                company_id=company_id,
                year=year,
                field=field,
                issue=issue,
                raw_value=raw_value,
            )
        )

    @property
    def critical_count(self) -> int:
        return sum(1 for item in self.failures if item.severity == "CRITICAL")

    def to_dataframe(self) -> pd.DataFrame:
        if not self.failures:
            return pd.DataFrame(
                columns=[
                    "rule_id",
                    "rule_name",
                    "severity",
                    "company_id",
                    "year",
                    "field",
                    "issue",
                    "raw_value",
                ]
            )
        return pd.DataFrame([item.__dict__ for item in self.failures])


def _is_bank_company(company_id: str, sectors: pd.DataFrame | None) -> bool:
    if sectors is not None and not sectors.empty:
        match = sectors[sectors["company_id"] == company_id]
        if not match.empty:
            broad = str(match.iloc[0].get("broad_sector", ""))
            sub = str(match.iloc[0].get("sub_sector", ""))
            if broad == "Financials":
                return True
            if any(
                keyword in sub.upper() for keyword in ("BANK", "FINANCE", "INSURANCE")
            ):
                return True
    return any(keyword in company_id for keyword in FINANCIAL_SECTOR_KEYWORDS)


def validate_companies(df: pd.DataFrame, result: ValidationResult) -> pd.DataFrame:
    working = df.copy()
    working["id"] = working["id"].map(normalize_ticker)
    working = working[working["id"].notna()]

    invalid = working[~working["id"].map(is_valid_ticker)]
    for _, row in invalid.iterrows():
        result.add(
            "DQ-08",
            "Ticker Format",
            "CRITICAL",
            f"Ticker length out of range: {row['id']}",
            company_id=str(row["id"]),
            field="id",
            raw_value=str(row["id"]),
        )
    working = working[working["id"].map(is_valid_ticker)]

    if len(working) != working["id"].nunique():
        dupes = working[working.duplicated("id", keep=False)]
        for ticker in dupes["id"].unique():
            result.add(
                "DQ-01",
                "Company PK Uniqueness",
                "CRITICAL",
                f"Duplicate company ticker: {ticker}",
                company_id=ticker,
                field="id",
            )
        working = working.drop_duplicates("id", keep="last")

    return working


def validate_time_series_table(
    df: pd.DataFrame,
    table_name: str,
    valid_company_ids: set[str],
    result: ValidationResult,
    sectors: pd.DataFrame | None = None,
    apply_sales_rule: bool = False,
    apply_opm_rule: bool = False,
    apply_bs_balance_rule: bool = False,
    apply_cf_rule: bool = False,
    apply_tax_rule: bool = False,
    apply_dividend_rule: bool = False,
    apply_eps_rule: bool = False,
    apply_fixed_assets_rule: bool = False,
) -> pd.DataFrame:
    working = df.copy()
    raw_years = working["year"].copy()
    working["company_id"] = working["company_id"].map(normalize_ticker)
    working["year"] = working["year"].map(normalize_year)

    invalid_year_mask = working["year"].isna()
    for idx in working.index[invalid_year_mask]:
        result.add(
            "DQ-07",
            "Year Format",
            "CRITICAL",
            "Unparseable year label",
            company_id=str(working.at[idx, "company_id"]),
            field="year",
            raw_value=str(raw_years.at[idx]),
        )
    working = working[~invalid_year_mask]

    invalid_year_format = ~working["year"].astype(str).str.match(YEAR_PATTERN)
    for idx in working.index[invalid_year_format]:
        result.add(
            "DQ-07",
            "Year Format",
            "CRITICAL",
            "Year does not match YYYY-MM format after normalisation",
            company_id=str(working.at[idx, "company_id"]),
            year=str(working.at[idx, "year"]),
            field="year",
        )
    working = working[~invalid_year_format]

    invalid_ticker_mask = ~working["company_id"].map(is_valid_ticker)
    for idx in working.index[invalid_ticker_mask]:
        result.add(
            "DQ-08",
            "Ticker Format",
            "CRITICAL",
            "Invalid ticker format",
            company_id=str(working.at[idx, "company_id"]),
            field="company_id",
            raw_value=str(working.at[idx, "company_id"]),
        )
    working = working[~invalid_ticker_mask]

    orphan_mask = ~working["company_id"].isin(valid_company_ids)
    orphans = working[orphan_mask].copy()
    if not orphans.empty:
        result.rejected_rows[f"{table_name}_fk"] = orphans
        for _, row in orphans.iterrows():
            result.add(
                "DQ-03",
                "FK Integrity",
                "CRITICAL",
                "company_id not found in companies table",
                company_id=str(row["company_id"]),
                year=str(row["year"]),
                field="company_id",
            )
    working = working[~orphan_mask]

    dup_mask = working.duplicated(["company_id", "year"], keep=False)
    if dup_mask.any():
        dupes = working[dup_mask].copy()
        result.deduped_rows[table_name] = dupes
        for _, row in dupes.iterrows():
            result.add(
                "DQ-02",
                "Annual PK Uniqueness",
                "CRITICAL",
                "Duplicate (company_id, year) — keeping last occurrence",
                company_id=str(row["company_id"]),
                year=str(row["year"]),
                field="year",
            )
        working = working.drop_duplicates(["company_id", "year"], keep="last")

    if apply_sales_rule:
        for idx, row in working.iterrows():
            sales = row.get("sales")
            if pd.isna(sales):
                continue
            if sales <= 0 and not _is_bank_company(str(row["company_id"]), sectors):
                result.add(
                    "DQ-06",
                    "Positive Sales",
                    "WARNING",
                    "Non-bank company with sales <= 0",
                    company_id=str(row["company_id"]),
                    year=str(row["year"]),
                    field="sales",
                    raw_value=str(sales),
                )

    if apply_opm_rule:
        for idx, row in working.iterrows():
            sales = row.get("sales")
            op_profit = row.get("operating_profit")
            opm = row.get("opm_percentage")
            if pd.isna(sales) or pd.isna(op_profit) or pd.isna(opm) or sales == 0:
                continue
            computed = (op_profit / sales) * 100
            if abs(opm - computed) >= 1.0:
                result.add(
                    "DQ-05",
                    "OPM Cross-Check",
                    "WARNING",
                    f"OPM mismatch: source={opm:.2f}, computed={computed:.2f}",
                    company_id=str(row["company_id"]),
                    year=str(row["year"]),
                    field="opm_percentage",
                )

    if apply_bs_balance_rule:
        for idx, row in working.iterrows():
            assets = row.get("total_assets")
            liabilities = row.get("total_liabilities")
            if pd.isna(assets) or pd.isna(liabilities) or assets == 0:
                continue
            diff_ratio = abs(assets - liabilities) / abs(assets)
            if diff_ratio >= 0.01:
                result.add(
                    "DQ-04",
                    "Balance Sheet Balance",
                    "WARNING",
                    f"Assets/liabilities mismatch ratio={diff_ratio:.4f}",
                    company_id=str(row["company_id"]),
                    year=str(row["year"]),
                    field="total_assets",
                )
            if liabilities != assets:
                result.add(
                    "DQ-15",
                    "BSE/ASE Balance",
                    "INFO",
                    "Strict balance sheet equality check failed",
                    company_id=str(row["company_id"]),
                    year=str(row["year"]),
                    field="total_liabilities",
                )

    if apply_cf_rule:
        for idx, row in working.iterrows():
            cfo = row.get("operating_activity")
            cfi = row.get("investing_activity")
            cff = row.get("financing_activity")
            net = row.get("net_cash_flow")
            if any(pd.isna(value) for value in (cfo, cfi, cff, net)):
                continue
            if abs(net - (cfo + cfi + cff)) > 10:
                result.add(
                    "DQ-09",
                    "Net Cash Check",
                    "WARNING",
                    f"net_cash_flow={net}, components sum={cfo + cfi + cff}",
                    company_id=str(row["company_id"]),
                    year=str(row["year"]),
                    field="net_cash_flow",
                )

    if apply_tax_rule:
        for idx, row in working.iterrows():
            tax = row.get("tax_percentage")
            if pd.isna(tax):
                continue
            if tax < 0 or tax > 60:
                result.add(
                    "DQ-11",
                    "Tax Rate Range",
                    "WARNING",
                    f"Tax percentage out of range: {tax}",
                    company_id=str(row["company_id"]),
                    year=str(row["year"]),
                    field="tax_percentage",
                    raw_value=str(tax),
                )

    if apply_dividend_rule:
        for idx, row in working.iterrows():
            payout = row.get("dividend_payout")
            if pd.isna(payout):
                continue
            if payout > 200:
                result.add(
                    "DQ-12",
                    "Dividend Payout Cap",
                    "WARNING",
                    f"Dividend payout exceeds 200%: {payout}",
                    company_id=str(row["company_id"]),
                    year=str(row["year"]),
                    field="dividend_payout",
                    raw_value=str(payout),
                )

    if apply_eps_rule:
        for idx, row in working.iterrows():
            eps = row.get("eps")
            net_profit = row.get("net_profit")
            if pd.isna(eps) or pd.isna(net_profit):
                continue
            if net_profit > 0 and eps <= 0:
                result.add(
                    "DQ-14",
                    "EPS Sign Consistency",
                    "WARNING",
                    "Positive net_profit with non-positive EPS",
                    company_id=str(row["company_id"]),
                    year=str(row["year"]),
                    field="eps",
                )

    if apply_fixed_assets_rule:
        coerced = []
        for idx, row in working.iterrows():
            fixed_assets = row.get("fixed_assets")
            if pd.isna(fixed_assets):
                continue
            if fixed_assets < 0:
                result.add(
                    "DQ-10",
                    "Non-Negative Fixed Assets",
                    "WARNING",
                    f"Negative fixed_assets coerced to 0: {fixed_assets}",
                    company_id=str(row["company_id"]),
                    year=str(row["year"]),
                    field="fixed_assets",
                    raw_value=str(fixed_assets),
                )
                working.at[idx, "fixed_assets"] = 0
                coerced.append(idx)
        if coerced:
            result.coerced_rows[table_name] = working.loc[coerced]

    return working


def validate_child_table_fk(
    df: pd.DataFrame,
    table_name: str,
    valid_company_ids: set[str],
    result: ValidationResult,
    ticker_column: str = "company_id",
) -> pd.DataFrame:
    working = df.copy()
    working[ticker_column] = working[ticker_column].map(normalize_ticker)
    invalid = working[~working[ticker_column].map(is_valid_ticker)]
    for _, row in invalid.iterrows():
        result.add(
            "DQ-08",
            "Ticker Format",
            "CRITICAL",
            "Invalid ticker format",
            company_id=str(row[ticker_column]),
            field=ticker_column,
        )
    working = working[working[ticker_column].map(is_valid_ticker)]

    orphan_mask = ~working[ticker_column].isin(valid_company_ids)
    orphans = working[orphan_mask]
    if not orphans.empty:
        result.rejected_rows[f"{table_name}_fk"] = orphans.copy()
        for _, row in orphans.iterrows():
            result.add(
                "DQ-03",
                "FK Integrity",
                "CRITICAL",
                "company_id not found in companies table",
                company_id=str(row[ticker_column]),
                field=ticker_column,
            )
    return working[~orphan_mask]


def validate_documents(
    df: pd.DataFrame,
    valid_company_ids: set[str],
    result: ValidationResult,
    validate_urls: bool = False,
) -> pd.DataFrame:
    working = df.copy()
    working = working.rename(columns={"Year": "year"})
    working["company_id"] = working["company_id"].map(normalize_ticker)
    working["year"] = pd.to_numeric(working["year"], errors="coerce").astype("Int64")
    working = validate_child_table_fk(working, "documents", valid_company_ids, result)

    if validate_urls and "annual_report" in working.columns:
        working = working.rename(columns={"Annual_Report": "annual_report"})
        for _, row in working.iterrows():
            url = row.get("annual_report")
            if pd.isna(url) or not str(url).startswith("http"):
                continue
            try:
                response = requests.head(str(url), timeout=5, allow_redirects=True)
                if response.status_code != 200:
                    result.add(
                        "DQ-13",
                        "URL Validity",
                        "WARNING",
                        f"URL returned status {response.status_code}",
                        company_id=str(row["company_id"]),
                        year=str(row["year"]),
                        field="annual_report",
                        raw_value=str(url),
                    )
            except requests.RequestException as exc:
                result.add(
                    "DQ-13",
                    "URL Validity",
                    "WARNING",
                    f"URL request failed: {exc}",
                    company_id=str(row["company_id"]),
                    year=str(row["year"]),
                    field="annual_report",
                    raw_value=str(url),
                )
    else:
        if "Annual_Report" in working.columns:
            working = working.rename(columns={"Annual_Report": "annual_report"})

    return working


def validate_coverage(
    profitandloss: pd.DataFrame,
    balancesheet: pd.DataFrame,
    cashflow: pd.DataFrame,
    result: ValidationResult,
    min_years: int = 5,
) -> None:
    for company_id in sorted(profitandloss["company_id"].unique()):
        pl_years = profitandloss[profitandloss["company_id"] == company_id][
            "year"
        ].nunique()
        bs_years = balancesheet[balancesheet["company_id"] == company_id][
            "year"
        ].nunique()
        cf_years = cashflow[cashflow["company_id"] == company_id]["year"].nunique()
        if pl_years < min_years or bs_years < min_years or cf_years < min_years:
            result.add(
                "DQ-16",
                "Coverage Check",
                "WARNING",
                f"Coverage below {min_years} years (P&L={pl_years}, BS={bs_years}, CF={cf_years})",
                company_id=str(company_id),
                field="year",
            )


def run_all_validations(
    datasets: dict[str, pd.DataFrame], validate_urls: bool | None = None
) -> ValidationResult:
    if validate_urls is None:
        validate_urls = os.getenv("VALIDATE_URLS", "false").lower() == "true"

    result = ValidationResult()
    companies = validate_companies(datasets["companies"], result)
    valid_ids = set(companies["id"].tolist())

    validated = {"companies": companies}
    validated["profitandloss"] = validate_time_series_table(
        datasets["profitandloss"],
        "profitandloss",
        valid_ids,
        result,
        sectors=datasets.get("sectors"),
        apply_sales_rule=True,
        apply_opm_rule=True,
        apply_dividend_rule=True,
        apply_eps_rule=True,
        apply_tax_rule=True,
    )
    validated["balancesheet"] = validate_time_series_table(
        datasets["balancesheet"],
        "balancesheet",
        valid_ids,
        result,
        apply_bs_balance_rule=True,
        apply_fixed_assets_rule=True,
    )
    validated["cashflow"] = validate_time_series_table(
        datasets["cashflow"],
        "cashflow",
        valid_ids,
        result,
        apply_cf_rule=True,
    )
    # financial_ratios is populated by ratio_engine, skip validation here
    validated["financial_ratios"] = None

    for name in ("analysis", "prosandcons", "sectors", "peer_groups"):
        validated[name] = validate_child_table_fk(
            datasets[name], name, valid_ids, result
        )

    stock_prices = datasets["stock_prices"].copy()
    stock_prices["company_id"] = stock_prices["company_id"].map(normalize_ticker)
    stock_prices = validate_child_table_fk(
        stock_prices, "stock_prices", valid_ids, result
    )
    dupes = stock_prices[stock_prices.duplicated(["company_id", "date"], keep=False)]
    if not dupes.empty:
        for _, row in dupes.iterrows():
            result.add(
                "DQ-02",
                "Annual PK Uniqueness",
                "CRITICAL",
                "Duplicate (company_id, date) in stock_prices",
                company_id=str(row["company_id"]),
                field="date",
                raw_value=str(row["date"]),
            )
        stock_prices = stock_prices.drop_duplicates(["company_id", "date"], keep="last")
    validated["stock_prices"] = stock_prices

    market_cap = datasets["market_cap"].copy()
    market_cap["company_id"] = market_cap["company_id"].map(normalize_ticker)
    market_cap = validate_child_table_fk(market_cap, "market_cap", valid_ids, result)
    validated["market_cap"] = market_cap

    validated["documents"] = validate_documents(
        datasets["documents"],
        valid_ids,
        result,
        validate_urls=validate_urls,
    )

    validate_coverage(
        validated["profitandloss"],
        validated["balancesheet"],
        validated["cashflow"],
        result,
    )

    return result, validated
