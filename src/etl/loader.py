"""
Sprint 1 - Excel Loader
Loads Nifty 100 source Excel files into SQLite.
"""

from pathlib import Path
import sqlite3
import pandas as pd

from src.etl.normaliser import normalize_year, normalize_company_name


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data" / "source"
DB = ROOT / "db" / "nifty100.db"
OUTPUT = ROOT / "output"


FILES = {
    "companies.xlsx": "companies",
    "profitandloss.xlsx": "profitandloss",
    "balancesheet.xlsx": "balancesheet",
    "cashflow.xlsx": "cashflow",
    "analysis.xlsx": "analysis",
    "documents.xlsx": "documents",
    "prosandcons.xlsx": "prosandcons",
    "sectors.xlsx": "sectors",
    "stock_prices.xlsx": "stock_prices",
    "peer_groups.xlsx": "peer_groups",
}


def clean_columns(df):
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
        .str.replace("/", "_", regex=False)
        .str.replace("(", "", regex=False)
        .str.replace(")", "", regex=False)
    )
    return df


def find_header_row(file_path):
    """
    Find the row containing company_id or another known schema column.
    """

    preview = pd.read_excel(
        file_path,
        header=None,
        nrows=20
    )

    known_columns = {
        "company_id",
        "year",
        "ticker",
        "company_name",
        "sales",
        "operating_profit",
        "equity_capital",
        "reserves",
        "borrowings",
        "operating_activity",
        "date",
        "document_type",
        "item_type",
    }

    for row_number, row in preview.iterrows():

        values = {
            str(value).strip().lower().replace(" ", "_")
            for value in row.tolist()
            if pd.notna(value)
        }

        if values.intersection(known_columns):
            return row_number

    return 0


def read_source(file_path):

    header_row = find_header_row(file_path)

    df = pd.read_excel(
        file_path,
        header=header_row
    )

    df = clean_columns(df)

    # companies.xlsx uses "id" for the ticker symbol — rename to company_id
    # so it matches the primary key used by every other source file.
    if "id" in df.columns and "company_id" not in df.columns:
        df = df.rename(columns={"id": "company_id"})

    # Clean the year column: "Mar 2014" -> 2014, "TTM" -> dropped
    if "year" in df.columns:
        df["year"] = df["year"].apply(normalize_year)
        df = df[df["year"].notna()]

    # Clean up company names (strips stray whitespace/newlines)
    if "company_name" in df.columns:
        df["company_name"] = df["company_name"].apply(normalize_company_name)

    # Remove completely empty rows
    df = df.dropna(how="all")

    # Remove completely empty columns
    df = df.dropna(axis=1, how="all")

    return df, header_row


def load_table(conn, filename, table):

    file_path = SOURCE / filename

    print(f"\nLoading: {filename}")

    if not file_path.exists():
        print("  [SKIP] File not found")
        return {
            "file": filename,
            "table": table,
            "source_rows": 0,
            "loaded_rows": 0,
            "status": "FILE_NOT_FOUND",
        }

    df, header_row = read_source(file_path)

    print(f"  Header row: {header_row}")
    print(f"  Source rows: {len(df)}")
    print(f"  Source columns: {len(df.columns)}")

    # Get database columns
    db_columns = [
        row[1]
        for row in conn.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    ]

    # Keep only columns existing in SQLite
    matching_columns = [
        column for column in df.columns
        if column in db_columns
    ]

    print(f"  Matching columns: {matching_columns}")

    if not matching_columns:
        print("  [ERROR] No matching columns")
        return {
            "file": filename,
            "table": table,
            "source_rows": len(df),
            "loaded_rows": 0,
            "status": "NO_MATCHING_COLUMNS",
        }

    df = df[matching_columns]

    # Convert NaN to None for SQLite
    df = df.where(pd.notna(df), None)

    # Remove duplicate rows
    before = len(df)
    df = df.drop_duplicates()
    duplicates_removed = before - len(df)

    print(f"  Duplicates removed: {duplicates_removed}")

    # Skip rows referencing a company_id not present in the companies table
    orphans_removed = 0
    if table != "companies" and "company_id" in df.columns:
        valid_ids = {
            row[0] for row in conn.execute(
                "SELECT company_id FROM companies"
            ).fetchall()
        }
        before_orphan_check = len(df)
        df = df[df["company_id"].isin(valid_ids)]
        orphans_removed = before_orphan_check - len(df)

        if orphans_removed:
            print(f"  Orphan rows skipped (unknown company_id): {orphans_removed}")

    # For tables keyed on (company_id, year), keep only the first
    # occurrence if duplicates exist with different values
    key_duplicates_removed = 0
    if {"company_id", "year"}.issubset(df.columns):
        before_key_dedup = len(df)
        df = df.drop_duplicates(subset=["company_id", "year"], keep="first")
        key_duplicates_removed = before_key_dedup - len(df)

        if key_duplicates_removed:
            print(f"  Duplicate (company_id, year) rows skipped: {key_duplicates_removed}")

    try:

        df.to_sql(
            table,
            conn,
            if_exists="append",
            index=False
        )

        print(f"  Loaded rows: {len(df)}")

        return {
            "file": filename,
            "table": table,
            "source_rows": before,
            "loaded_rows": len(df),
            "orphans_removed": orphans_removed,
            "key_duplicates_removed": key_duplicates_removed,
            "status": "LOADED",
        }

    except Exception as exc:

        print(f"  [ERROR] {type(exc).__name__}: {exc}")

        return {
            "file": filename,
            "table": table,
            "source_rows": before,
            "loaded_rows": 0,
            "orphans_removed": orphans_removed,
            "key_duplicates_removed": key_duplicates_removed,
            "status": f"ERROR: {type(exc).__name__}: {exc}",
        }


def load_data():

    print("=" * 60)
    print("NIFTY 100 - DATA LOADER")
    print("=" * 60)

    OUTPUT.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB)

    conn.execute("PRAGMA foreign_keys = ON")

    audit = []

    # IMPORTANT:
    # companies must be loaded before all FK-dependent tables.
    load_order = [
        "companies.xlsx",
        "profitandloss.xlsx",
        "balancesheet.xlsx",
        "cashflow.xlsx",
        "analysis.xlsx",
        "documents.xlsx",
        "prosandcons.xlsx",
        "sectors.xlsx",
        "stock_prices.xlsx",
        "peer_groups.xlsx",
    ]

    try:

        for filename in load_order:

            table = FILES[filename]

            result = load_table(
                conn,
                filename,
                table
            )

            audit.append(result)

            # Commit after every table so a successful
            # table is preserved even if a later table fails.
            conn.commit()

    finally:

        conn.close()

    audit_df = pd.DataFrame(audit)

    audit_file = OUTPUT / "load_audit.csv"

    audit_df.to_csv(
        audit_file,
        index=False
    )

    print("\n" + "=" * 60)
    print("LOAD COMPLETE")
    print("=" * 60)

    print(f"Audit: {audit_file}")

    print("\nLoad summary:")
    print(
        audit_df[
            ["table", "source_rows", "loaded_rows", "status"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    load_data()
