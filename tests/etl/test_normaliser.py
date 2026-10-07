import pandas as pd
from datetime import datetime

from src.etl.normaliser import (
    normalize_year,
    normalize_ticker,
    normalize_company_name,
    normalize_numeric,
)


# ============================================================
# normalize_year — 20 tests
# ============================================================

def test_year_integer():
    assert normalize_year(2024) == 2024


def test_year_string():
    assert normalize_year("2024") == 2024


def test_year_fy():
    assert normalize_year("FY2024") == 2024


def test_year_fy_with_space():
    assert normalize_year("FY 2024") == 2024


def test_year_financial_range():
    assert normalize_year("2024-25") == 2024


def test_year_full_financial_range():
    assert normalize_year("2024-2025") == 2024


def test_year_month_year():
    assert normalize_year("Mar 2024") == 2024


def test_year_timestamp():
    assert normalize_year(pd.Timestamp("2023-06-30")) == 2023


def test_year_datetime():
    assert normalize_year(datetime(2022, 5, 1)) == 2022


def test_year_float():
    assert normalize_year(2021.0) == 2021


def test_year_lowercase_fy():
    assert normalize_year("fy2020") == 2020


def test_year_with_text():
    assert normalize_year("Financial Year 2019") == 2019


def test_year_whitespace():
    assert normalize_year(" 2024 ") == 2024


def test_year_none():
    assert normalize_year(None) is None


def test_year_nan():
    assert normalize_year(float("nan")) is None


def test_year_empty_string():
    assert normalize_year("") is None


def test_year_invalid():
    assert normalize_year("ABC") is None


def test_year_out_of_range():
    assert normalize_year(1800) is None


def test_year_future_out_of_range():
    assert normalize_year(2200) is None


def test_year_non_numeric():
    assert normalize_year("FY-ABC") is None


# ============================================================
# normalize_ticker — 15 tests
# ============================================================

def test_ticker_uppercase():
    assert normalize_ticker("tcs") == "TCS"


def test_ticker_already_uppercase():
    assert normalize_ticker("TCS") == "TCS"


def test_ticker_whitespace():
    assert normalize_ticker(" TCS ") == "TCS"


def test_ticker_nse_prefix():
    assert normalize_ticker("NSE:TCS") == "TCS"


def test_ticker_bse_prefix():
    assert normalize_ticker("BSE:TCS") == "TCS"


def test_ticker_ns_suffix():
    assert normalize_ticker("TCS.NS") == "TCS"


def test_ticker_bo_suffix():
    assert normalize_ticker("TCS.BO") == "TCS"


def test_ticker_lowercase_nse():
    assert normalize_ticker("nse:tcs") == "TCS"


def test_ticker_special_characters():
    assert normalize_ticker("TCS@") == "TCS"


def test_ticker_hyphen():
    assert normalize_ticker("M&M") == "M&M"


def test_ticker_none():
    assert normalize_ticker(None) is None


def test_ticker_empty():
    assert normalize_ticker("") is None


def test_ticker_whitespace_only():
    assert normalize_ticker("   ") is None


def test_ticker_nan():
    assert normalize_ticker(float("nan")) is None


def test_ticker_numeric():
    assert normalize_ticker(123) == "123"


# ============================================================
# normalize_company_name — 5 tests
# ============================================================

def test_company_name_basic():
    assert normalize_company_name("TCS") == "Tcs"


def test_company_name_whitespace():
    assert normalize_company_name("  Tata   Consultancy   Services  ") == (
        "Tata Consultancy Services"
    )


def test_company_name_empty():
    assert normalize_company_name("") is None


def test_company_name_none():
    assert normalize_company_name(None) is None


def test_company_name_nan():
    assert normalize_company_name(float("nan")) is None


# ============================================================
# normalize_numeric — 10 tests
# ============================================================

def test_numeric_integer():
    assert normalize_numeric(100) == 100.0


def test_numeric_float():
    assert normalize_numeric(100.50) == 100.50


def test_numeric_string():
    assert normalize_numeric("100") == 100.0


def test_numeric_comma():
    assert normalize_numeric("1,250") == 1250.0


def test_numeric_percentage():
    assert normalize_numeric("15.5%") == 15.5


def test_numeric_rupee():
    assert normalize_numeric("₹1,000") == 1000.0


def test_numeric_negative_parentheses():
    assert normalize_numeric("(1,250)") == -1250.0


def test_numeric_dash():
    assert normalize_numeric("--") is None


def test_numeric_none():
    assert normalize_numeric(None) is None


def test_numeric_invalid():
    assert normalize_numeric("ABC") is None