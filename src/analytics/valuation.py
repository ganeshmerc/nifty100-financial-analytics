import sqlite3
from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"
MARKET_CAP_PATH = PROJECT_ROOT / "data" / "source" / "market_cap.xlsx"

OUTPUT_DIR = PROJECT_ROOT / "output"

VALUATION_OUTPUT = OUTPUT_DIR / "valuation_summary.xlsx"
FLAGS_OUTPUT = OUTPUT_DIR / "valuation_flags.csv"


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    """Create SQLite database connection."""
    return sqlite3.connect(DB_PATH)


# ============================================================
# LOAD MARKET DATA
# ============================================================

def load_market_data():
    """Load market-cap and valuation data from Excel."""

    df = pd.read_excel(MARKET_CAP_PATH)

    required_columns = [
        "company_id",
        "year",
        "market_cap_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "dividend_yield_pct",
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns in market_cap.xlsx: {missing}"
        )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    numeric_columns = [
        "market_cap_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "dividend_yield_pct",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        )

    return df


# ============================================================
# LOAD COMPANY / SECTOR DATA
# ============================================================

def load_company_data():
    """Load company names and sectors from SQLite."""

    conn = get_connection()

    try:
        companies = pd.read_sql_query(
            """
            SELECT
                company_id,
                company_name,
                broad_sector
            FROM companies
            """,
            conn,
        )

        sectors = pd.read_sql_query(
            """
            SELECT
                company_id,
                broad_sector
            FROM sectors
            WHERE broad_sector IS NOT NULL
            """,
            conn,
        )

    finally:
        conn.close()

    # Remove duplicate sector mappings
    sectors = sectors.drop_duplicates(
        subset=["company_id"]
    )

    # Prefer company table sector
    companies["sector"] = companies["broad_sector"]

    sector_lookup = sectors[
        ["company_id", "broad_sector"]
    ].rename(
        columns={
            "broad_sector": "sector_from_sectors"
        }
    )

    companies = companies.merge(
        sector_lookup,
        on="company_id",
        how="left",
    )

    companies["sector"] = companies[
        "sector"
    ].fillna(
        companies["sector_from_sectors"]
    )

    companies = companies.drop(
        columns=[
            "broad_sector",
            "sector_from_sectors",
        ],
        errors="ignore",
    )

    return companies


# ============================================================
# LOAD FINANCIAL RATIOS
# ============================================================

def load_ratios():
    """Load financial ratios from SQLite."""

    conn = get_connection()

    try:
        ratios = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                free_cash_flow_cr
            FROM financial_ratios
            """,
            conn,
        )

    finally:
        conn.close()

    ratios["year"] = pd.to_numeric(
        ratios["year"],
        errors="coerce",
    )

    ratios["free_cash_flow_cr"] = pd.to_numeric(
        ratios["free_cash_flow_cr"],
        errors="coerce",
    )

    return ratios


# ============================================================
# BUILD VALUATION DATA
# ============================================================

def build_valuation_data():
    """Build valuation dataset for all companies and years."""

    market = load_market_data()
    companies = load_company_data()
    ratios = load_ratios()

    # Merge company information
    df = market.merge(
        companies,
        on="company_id",
        how="left",
    )

    # Merge FCF
    df = df.merge(
        ratios,
        on=["company_id", "year"],
        how="left",
    )

    # --------------------------------------------------------
    # FCF Yield
    # --------------------------------------------------------

    df["FCF_yield_pct"] = (
        df["free_cash_flow_cr"]
        / df["market_cap_crore"]
        * 100
    )

    df.loc[
        df["market_cap_crore"] <= 0,
        "FCF_yield_pct",
    ] = pd.NA

    # --------------------------------------------------------
    # Sector median P/E
    # --------------------------------------------------------

    sector_medians = (
        df.groupby("sector")["pe_ratio"]
        .median()
        .rename("sector_median_pe")
        .reset_index()
    )

    df = df.merge(
        sector_medians,
        on="sector",
        how="left",
    )

    # --------------------------------------------------------
    # P/E vs sector median
    # --------------------------------------------------------

    df["PE_vs_sector_median_pct"] = (
        (
            df["pe_ratio"]
            - df["sector_median_pe"]
        )
        / df["sector_median_pe"]
        * 100
    )

    # --------------------------------------------------------
    # Valuation flag
    # --------------------------------------------------------

    df["flag"] = "Fair"

    df.loc[
        df["pe_ratio"]
        > df["sector_median_pe"] * 1.5,
        "flag",
    ] = "Caution"

    df.loc[
        df["pe_ratio"]
        < df["sector_median_pe"] * 0.7,
        "flag",
    ] = "Discount"

    # Invalid / missing P/E
    df.loc[
        df["pe_ratio"].isna()
        | df["sector_median_pe"].isna(),
        "flag",
    ] = "N/A"

    return df


# ============================================================
# CREATE VALUATION SUMMARY
# ============================================================

def create_valuation_summary():
    """Create latest-year valuation summary for all companies."""

    df = build_valuation_data()

    # Requirement is based on latest available year.
    latest_year = int(
        df["year"].dropna().max()
    )

    latest = df[
        df["year"] == latest_year
    ].copy()

    # One row per company
    latest = latest.drop_duplicates(
        subset=["company_id"]
    )

    # Required output columns
    summary = latest[
        [
            "company_id",
            "company_name",
            "sector",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "FCF_yield_pct",
            "sector_median_pe",
            "PE_vs_sector_median_pct",
            "flag",
        ]
    ].copy()

    # Rename columns to exact Sprint 4 specification
    summary = summary.rename(
        columns={
            "pe_ratio": "P/E",
            "pb_ratio": "P/B",
            "ev_ebitda": "EV/EBITDA",
            "sector_median_pe": "5yr_median_PE",
        }
    )

    # Keep exact required column order
    summary = summary[
        [
            "company_id",
            "company_name",
            "sector",
            "P/E",
            "P/B",
            "EV/EBITDA",
            "FCF_yield_pct",
            "5yr_median_PE",
            "PE_vs_sector_median_pct",
            "flag",
        ]
    ]

    # Round numerical values
    numeric_columns = [
        "P/E",
        "P/B",
        "EV/EBITDA",
        "FCF_yield_pct",
        "5yr_median_PE",
        "PE_vs_sector_median_pct",
    ]

    for col in numeric_columns:
        summary[col] = pd.to_numeric(
            summary[col],
            errors="coerce",
        ).round(2)

    return summary


# ============================================================
# CREATE FLAG FILE
# ============================================================

def create_valuation_flags(summary):
    """Create CSV containing only Caution and Discount companies."""

    flags = summary[
        summary["flag"].isin(
            ["Caution", "Discount"]
        )
    ].copy()

    return flags


# ============================================================
# SAVE OUTPUTS
# ============================================================

def save_outputs():
    """Generate and save valuation outputs."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary = create_valuation_summary()

    flags = create_valuation_flags(
        summary
    )

    summary.to_excel(
        VALUATION_OUTPUT,
        index=False,
    )

    flags.to_csv(
        FLAGS_OUTPUT,
        index=False,
    )

    return summary, flags


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("NIFTY 100 VALUATION ENGINE")
    print("=" * 60)

    try:

        summary, flags = save_outputs()

        print(
            f"Valuation rows: {len(summary)}"
        )

        print(
            f"Caution/Discount rows: {len(flags)}"
        )

        print(
            f"Excel output: {VALUATION_OUTPUT}"
        )

        print(
            f"CSV output: {FLAGS_OUTPUT}"
        )

        print("\nFlag distribution:")

        print(
            summary["flag"]
            .value_counts(dropna=False)
            .to_string()
        )

        print("\nVALUATION ENGINE COMPLETE")

    except Exception as e:

        print(
            f"\nERROR: {type(e).__name__}: {e}"
        )

        raise