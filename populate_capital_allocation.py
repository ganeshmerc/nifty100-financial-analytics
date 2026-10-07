"""
Sprint 2 - Populate Capital Allocation

Creates:
output/capital_allocation.csv

Columns:
company_id
year
cfo_sign
cfi_sign
cff_sign
pattern_label
"""

import sqlite3
import os
import pandas as pd

from src.analytics.capital_allocation import (
    get_capital_allocation,
)


DB_PATH = "db/nifty100.db"
OUTPUT_PATH = "output/capital_allocation.csv"


def main():

    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            c.company_id,
            c.year,
            c.operating_activity AS cfo,
            c.investing_activity AS cfi,
            c.financing_activity AS cff,
            p.net_profit AS pat

        FROM cashflow c

        LEFT JOIN profitandloss p
            ON c.company_id = p.company_id
            AND c.year = p.year

        ORDER BY
            c.company_id,
            c.year
    """

    df = pd.read_sql(query, conn)

    conn.close()

    print(f"Rows to process: {len(df)}")

    results = []

    for _, row in df.iterrows():

        result = get_capital_allocation(
            cfo=row["cfo"],
            cfi=row["cfi"],
            cff=row["cff"],
            pat=row["pat"],
        )

        results.append(
            {
                "company_id": row["company_id"],
                "year": row["year"],
                "cfo_sign": result["cfo_sign"],
                "cfi_sign": result["cfi_sign"],
                "cff_sign": result["cff_sign"],
                "pattern_label": result["pattern_label"],
            }
        )

    output_df = pd.DataFrame(results)

    os.makedirs("output", exist_ok=True)

    output_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print()
    print("=" * 60)
    print("CAPITAL ALLOCATION COMPLETE")
    print("=" * 60)

    print(f"Rows written: {len(output_df)}")
    print(f"Output: {os.path.abspath(OUTPUT_PATH)}")

    print()
    print("Pattern breakdown:")
    print(output_df["pattern_label"].value_counts().to_string())


if __name__ == "__main__":
    main()