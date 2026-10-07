import re
from datetime import datetime

import pandas as pd


def normalize_year(value):
    """
    Convert different year formats into an integer year.

    Examples:
        2024          -> 2024
        "2024"        -> 2024
        "FY2024"      -> 2024
        "FY 2024"     -> 2024
        "2024-25"     -> 2024
        "2024-2025"   -> 2024
        "Mar 2024"    -> 2024
        "TTM"         -> None (not a real year)
        Timestamp     -> year
    """

    if value is None or pd.isna(value):
        return None

    if isinstance(value, (datetime, pd.Timestamp)):
        return int(value.year)

    if isinstance(value, (int, float)):
        year = int(value)

        if 1900 <= year <= 2100:
            return year

        return None

    value = str(value).strip().upper()

    if not value:
        return None

    if value == "TTM":
        return None

    match = re.search(r"(19|20)\d{2}", value)

    if match:
        return int(match.group())

    return None


def normalize_ticker(value):
    """
    Normalize company ticker symbols.

    Examples:
        "TCS"          -> "TCS"
        " tcs "        -> "TCS"
        "NSE:TCS"      -> "TCS"
        "BSE:TCS"      -> "TCS"
        "TCS.NS"       -> "TCS"
        "TCS.BO"       -> "TCS"
    """

    if value is None or pd.isna(value):
        return None

    ticker = str(value).strip().upper()

    if not ticker:
        return None

    ticker = ticker.replace("NSE:", "")
    ticker = ticker.replace("BSE:", "")

    ticker = ticker.replace(".NS", "")
    ticker = ticker.replace(".BO", "")

    ticker = re.sub(r"[^A-Z0-9&-]", "", ticker)

    return ticker or None


def normalize_company_name(value):
    """Normalize company names."""

    if value is None or pd.isna(value):
        return None

    name = str(value).strip()

    name = re.sub(r"\s+", " ", name)

    return name.title() if name else None


def normalize_numeric(value):
    """
    Convert financial values into numeric values.

    Handles:
        commas
        percentages
        currency symbols
        parentheses for negative values
        '--'
        blank values
    """

    if value is None or pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    value = str(value).strip()

    if value in {"", "-", "--", "NA", "N/A", "NULL", "NAN"}:
        return None

    negative = False

    if value.startswith("(") and value.endswith(")"):
        negative = True
        value = value[1:-1]

    value = value.replace(",", "")
    value = value.replace("₹", "")
    value = value.replace("$", "")
    value = value.replace("%", "")

    try:
        number = float(value)

        if negative:
            number = -number

        return number

    except ValueError:
        return None
