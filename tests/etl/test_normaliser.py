"""Unit tests for year and ticker normalisation."""

import pytest

from src.etl.normaliser import (
    deduplicate_time_series,
    is_valid_ticker,
    normalize_company_name,
    normalize_ticker,
    normalize_year,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Mar-23", "2023-03"),
        ("Mar-14", "2014-03"),
        ("Mar-13", "2013-03"),
        ("Dec 2012", "2012-12"),
        ("Mar 2014", "2014-03"),
        ("Mar 2016 9m", "2016-03"),
        ("Mar 2023 15", "2023-03"),
        ("2023-03", "2023-03"),
        ("2019", "2019-03"),
        (2019, "2019-03"),
        ("Jan-20", "2020-01"),
        ("Sep-24", "2024-09"),
        ("Apr 2021", "2021-04"),
        ("Nov 2018", "2018-11"),
        ("Jun-99", "1999-06"),
        ("Jul-00", "2000-07"),
        ("Feb-05", "2005-02"),
        ("Aug 2022", "2022-08"),
        ("Oct-11", "2011-10"),
        ("Dec-19", "2019-12"),
    ],
    ids=[
        "mar23",
        "mar14",
        "mar13",
        "dec2012",
        "mar2014",
        "mar2016_9m",
        "mar2023_15",
        "already_norm",
        "year_int",
        "year_str",
        "jan20",
        "sep24",
        "apr2021",
        "nov2018",
        "jun99",
        "jul00",
        "feb05",
        "aug2022",
        "oct11",
        "dec19",
    ],
)
def test_normalize_year_valid(raw, expected):
    assert normalize_year(raw) == expected


@pytest.mark.parametrize(
    "raw",
    ["TTM", "", None, "invalid", "13-2020"],
    ids=["ttm", "empty", "none", "invalid", "bad_pattern"],
)
def test_normalize_year_invalid(raw):
    assert normalize_year(raw) is None


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("tcs", "TCS"),
        (" HDFCBANK ", "HDFCBANK"),
        ("bajaj-auto", "BAJAJ-AUTO"),
        ("  infy", "INFY"),
        ("reliance", "RELIANCE"),
        ("AgTl", "ATGL"),
        ("AGTL", "ATGL"),
        ("lt", "LT"),
        ("m&m", "M&M"),
        ("kotakbank", "KOTAKBANK"),
        ("axisbank", "AXISBANK"),
        ("  sbilife  ", "SBILIFE"),
        ("techm", "TECHM"),
        ("pidilitind", "PIDILITIND"),
        ("bajajhldng", "BAJAJHLDNG"),
    ],
    ids=[
        "lower",
        "spaces",
        "hyphen",
        "leading_space",
        "reliance",
        "agtl_mixed",
        "agtl_alias",
        "lt",
        "ampersand",
        "kotak",
        "axis",
        "sbilife",
        "techm",
        "pidilite",
        "bajaj_holdings",
    ],
)
def test_normalize_ticker(raw, expected):
    assert normalize_ticker(raw) == expected


@pytest.mark.parametrize(
    "ticker,valid",
    [
        ("TCS", True),
        ("BAJAJ-AUTO", True),
        ("A", False),
        ("THISISWAYTOOLONG", False),
        ("", False),
        (None, False),
    ],
)
def test_is_valid_ticker(ticker, valid):
    assert is_valid_ticker(ticker) is valid


def test_normalize_company_name_strips_newlines():
    assert (
        normalize_company_name("Tata\nConsultancy\nServices")
        == "Tata Consultancy Services"
    )


def test_deduplicate_time_series_keeps_last():
    import pandas as pd

    df = pd.DataFrame(
        {
            "company_id": ["TCS", "TCS", "INFY"],
            "year": ["2023-03", "2023-03", "2023-03"],
            "sales": [100, 200, 300],
        }
    )
    deduped, duplicates = deduplicate_time_series(df, ["company_id", "year"])
    assert len(deduped) == 2
    assert len(duplicates) == 2
    assert deduped.loc[deduped["company_id"] == "TCS", "sales"].iloc[0] == 200
