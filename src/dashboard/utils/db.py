from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"
PEER_GROUPS_PATH = PROJECT_ROOT / "data" / "source" / "peer_groups.xlsx"
MARKET_CAP_PATH = PROJECT_ROOT / "data" / "source" / "market_cap.xlsx"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    return sqlite3.connect(str(DB_PATH))


# ============================================================
# GENERIC QUERY HELPER
# ============================================================

@st.cache_data(ttl=600)
def _query(sql, params=()):
    conn = get_connection()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


# ============================================================
# COMPANIES
# ============================================================

@st.cache_data(ttl=600)
def get_companies():
    sql = """
        SELECT
            company_id,
            company_name,
            ticker,
            broad_sector
        FROM companies
        ORDER BY company_name
    """

    df = _query(sql)

    # The project uses company_id as the NSE ticker/symbol
    # because the ticker column is NULL in the current database.
    df["symbol"] = df["company_id"]

    return df


# ============================================================
# COMPANY ID RESOLUTION
# ============================================================

@st.cache_data(ttl=600)
def resolve_company_id(ticker_or_company_id):
    """
    Resolve a user-entered ticker/company_id.

    Priority:
    1. company_id
    2. ticker
    3. company name
    """

    if ticker_or_company_id is None:
        return None

    value = str(ticker_or_company_id).strip()

    if not value:
        return None

    sql = """
        SELECT company_id
        FROM companies
        WHERE UPPER(company_id) = UPPER(?)
           OR UPPER(COALESCE(ticker, '')) = UPPER(?)
           OR UPPER(company_name) = UPPER(?)
        LIMIT 1
    """

    df = _query(sql, (value, value, value))

    if df.empty:
        return None

    return df.iloc[0]["company_id"]


# ============================================================
# FINANCIAL RATIOS
# ============================================================

@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    company_id = resolve_company_id(ticker)

    if company_id is None:
        return pd.DataFrame()

    if year is None:
        sql = """
            SELECT *
            FROM financial_ratios
            WHERE company_id = ?
            ORDER BY year
        """
        return _query(sql, (company_id,))

    sql = """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
          AND year = ?
        ORDER BY year
    """

    return _query(sql, (company_id, year))


# ============================================================
# PROFIT & LOSS
# ============================================================

@st.cache_data(ttl=600)
def get_pl(ticker):
    company_id = resolve_company_id(ticker)

    if company_id is None:
        return pd.DataFrame()

    sql = """
        SELECT *
        FROM profitandloss
        WHERE company_id = ?
        ORDER BY year
    """

    return _query(sql, (company_id,))


# ============================================================
# BALANCE SHEET
# ============================================================

@st.cache_data(ttl=600)
def get_bs(ticker):
    company_id = resolve_company_id(ticker)

    if company_id is None:
        return pd.DataFrame()

    sql = """
        SELECT *
        FROM balancesheet
        WHERE company_id = ?
        ORDER BY year
    """

    return _query(sql, (company_id,))


# ============================================================
# CASH FLOW
# ============================================================

@st.cache_data(ttl=600)
def get_cf(ticker):
    company_id = resolve_company_id(ticker)

    if company_id is None:
        return pd.DataFrame()

    sql = """
        SELECT *
        FROM cashflow
        WHERE company_id = ?
        ORDER BY year
    """

    return _query(sql, (company_id,))



# SECTORS
# ============================================================

@st.cache_data(ttl=600)
def get_sectors():
    """
    Return company-sector mapping from the sectors table.

    Actual database structure:
        company_id
        broad_sector
        sector

    The populated sector information is stored in broad_sector.
    """

    sql = """
        SELECT
            company_id,
            broad_sector AS sector
        FROM sectors
        WHERE broad_sector IS NOT NULL
        ORDER BY broad_sector, company_id
    """

    return _query(sql)# ============================================================
# PEER GROUP DEFINITIONS
# ============================================================

@st.cache_data(ttl=600)
def get_peer_groups():
    """
    Read the authoritative peer-group definitions from
    data/source/peer_groups.xlsx.
    """

    if not PEER_GROUPS_PATH.exists():
        return pd.DataFrame(
            columns=[
                "id",
                "peer_group_name",
                "company_id",
                "is_benchmark",
            ]
        )

    df = pd.read_excel(PEER_GROUPS_PATH)

    expected = [
        "id",
        "peer_group_name",
        "company_id",
        "is_benchmark",
    ]

    for column in expected:
        if column not in df.columns:
            df[column] = None

    return df[expected].copy()


@st.cache_data(ttl=600)
def get_peer_group_names():
    df = get_peer_groups()

    if df.empty:
        return []

    return sorted(
        df["peer_group_name"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


# ============================================================
# PEERS
# ============================================================

@st.cache_data(ttl=600)
def get_peers(group_name):
    """
    Return all companies belonging to a peer group.
    """

    groups = get_peer_groups()

    if groups.empty or group_name is None:
        return pd.DataFrame()

    selected = groups[
        groups["peer_group_name"].astype(str).str.strip()
        == str(group_name).strip()
    ].copy()

    if selected.empty:
        return pd.DataFrame()

    companies = get_companies()

    result = selected.merge(
        companies,
        on="company_id",
        how="left",
    )

    return result.sort_values(
        ["is_benchmark", "company_name"],
        ascending=[False, True],
    ).reset_index(drop=True)


# ============================================================
# PEER PERCENTILES
# ============================================================

@st.cache_data(ttl=600)
def get_peer_percentiles(group_name):
    """
    Return pre-calculated peer percentile data from SQLite
    when available.

    Falls back to an empty DataFrame if the table is unavailable.
    """

    groups = get_peer_groups()

    if groups.empty:
        return pd.DataFrame()

    selected = groups[
        groups["peer_group_name"].astype(str).str.strip()
        == str(group_name).strip()
    ].copy()

    if selected.empty:
        return pd.DataFrame()

    company_ids = selected["company_id"].tolist()

    if not company_ids:
        return pd.DataFrame()

    placeholders = ",".join(["?"] * len(company_ids))

    sql = f"""
        SELECT *
        FROM peer_percentiles
        WHERE company_id IN ({placeholders})
    """

    try:
        return _query(sql, tuple(company_ids))
    except Exception:
        return pd.DataFrame()


# ============================================================
# LATEST RATIOS
# ============================================================

@st.cache_data(ttl=600)
def get_latest_ratios():
    """
    Latest financial ratio row for every company.
    """

    sql = """
        SELECT fr.*
        FROM financial_ratios fr
        INNER JOIN (
            SELECT
                company_id,
                MAX(year) AS max_year
            FROM financial_ratios
            GROUP BY company_id
        ) latest
            ON fr.company_id = latest.company_id
           AND fr.year = latest.max_year
        ORDER BY fr.company_id
    """

    return _query(sql)


# ============================================================
# PROS & CONS
# ============================================================

@st.cache_data(ttl=600)
def get_pros_cons(ticker):
    company_id = resolve_company_id(ticker)

    if company_id is None:
        return pd.DataFrame()

    sql = """
        SELECT
            company_id,
            item_type,
            description
        FROM prosandcons
        WHERE company_id = ?
        ORDER BY item_type
    """

    return _query(sql, (company_id,))


# ============================================================
# ANNUAL REPORTS
# ============================================================

@st.cache_data(ttl=600)
def get_reports(ticker):
    company_id = resolve_company_id(ticker)

    if company_id is None:
        return pd.DataFrame()

    sql = """
        SELECT
            company_id,
            document_type,
            report_year,
            document_url
        FROM documents
        WHERE company_id = ?
        ORDER BY report_year DESC, document_type
    """

    return _query(sql, (company_id,))
# ============================================================
# VALUATION / MARKET CAP
# ============================================================

@st.cache_data(ttl=600)
def get_valuation(ticker):
    """
    Return market-cap / valuation information for a company
    from market_cap.xlsx.
    """

    company_id = resolve_company_id(ticker)

    if company_id is None:
        return pd.DataFrame()

    if not MARKET_CAP_PATH.exists():
        return pd.DataFrame()

    df = pd.read_excel(MARKET_CAP_PATH)

    if "company_id" not in df.columns:
        return pd.DataFrame()

    result = df[
        df["company_id"].astype(str).str.upper()
        == str(company_id).upper()
    ].copy()

    return result.reset_index(drop=True)


# ============================================================
# TICKERS / SYMBOLS
# ============================================================

@st.cache_data(ttl=600)
def get_tickers():
    companies = get_companies()

    if companies.empty:
        return []

    return (
        companies["company_id"]
        .dropna()
        .astype(str)
        .sort_values()
        .tolist()
    )