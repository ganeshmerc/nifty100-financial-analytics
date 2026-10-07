"""
Sprint 2 - Populate financial_ratios table
Step 3: Asset Turnover
"""

import sqlite3
import pandas as pd

from src.analytics.ratios import asset_turnover


def main():
    conn = sqlite3.connect("db/nifty100.db")

    query = """
        SELECT
            p.company_id,
            p.year,
            p.sales,
            b.total_assets
        FROM profitandloss p
        JOIN balancesheet b
            ON p.company_id = b.company_id
            AND p.year = b.year
    """

    df = pd.read_sql(query, conn)

    print(f"Company-year rows to process: {len(df)}")

    rows_updated = 0

    for _, row in df.iterrows():

        at = asset_turnover(row["sales"], row["total_assets"])

        conn.execute(
            """
            UPDATE financial_ratios
            SET asset_turnover = ?
            WHERE company_id = ? AND year = ?
            """,
            (at, row["company_id"], row["year"]),
        )

        rows_updated += 1

    conn.commit()
    conn.close()

    print(f"Rows updated: {rows_updated}")


if __name__ == "__main__":
    main()