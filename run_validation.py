"""
Sprint 1 - Run DQ validation against the real loaded database.
"""

import sqlite3
import pandas as pd

from src.etl.validator import DataQualityValidator


def load_table(conn, table):
    return pd.read_sql(f"SELECT * FROM {table}", conn)


def main():
    conn = sqlite3.connect("db/nifty100.db")

    companies = load_table(conn, "companies")
    pnl = load_table(conn, "profitandloss")
    balancesheet = load_table(conn, "balancesheet")

    validator = DataQualityValidator()

    # Company/year uniqueness + FK checks on P&L
    validator.check_company_year_uniqueness(pnl)
    validator.check_foreign_keys(pnl, companies)
    validator.check_positive_sales(pnl)

    # Company/year uniqueness + FK checks on balance sheet
    validator.check_company_year_uniqueness(balancesheet)
    validator.check_foreign_keys(balancesheet, companies)

    # Duplicate company records
    validator.check_duplicate_companies(companies)

    # Missing key financial fields in P&L
    validator.check_missing_financial_data(
        pnl,
        ["sales", "operating_profit", "net_profit"],
    )

    conn.close()

    output_path = validator.export_failures()

    print(f"Total issues found: {len(validator.failures)}")
    print(f"Saved to: {output_path}")

    if validator.failures:
        preview = pd.DataFrame(
            [vars(f) for f in validator.failures]
        )
        print("\nBreakdown by rule:")
        print(preview["rule_id"].value_counts())


if __name__ == "__main__":
    main()