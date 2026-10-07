"""
Sprint 2 - Populate financial_ratios table
Step 1: Profitability ratios (NPM, OPM, ROE, ROCE, ROA)
"""

import sqlite3
import pandas as pd

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
)


def main():
    conn = sqlite3.connect("db/nifty100.db")

    # Join profitandloss + balancesheet on company_id and year
    query = """
        SELECT
            p.company_id,
            p.year,
            p.sales,
            p.operating_profit,
            p.other_income,
            p.net_profit,
            b.equity_capital,
            b.reserves,
            b.borrowings,
            b.total_assets
        FROM profitandloss p
        JOIN balancesheet b
            ON p.company_id = b.company_id
            AND p.year = b.year
    """

    df = pd.read_sql(query, conn)

    print(f"Company-year rows to process: {len(df)}")

    rows_written = 0

    for _, row in df.iterrows():

        npm = net_profit_margin(row["net_profit"], row["sales"])
        opm = operating_profit_margin(row["operating_profit"], row["sales"])
        roe = return_on_equity(
            row["net_profit"], row["equity_capital"], row["reserves"]
        )

        # Using operating_profit as an EBIT approximation
        roce = return_on_capital_employed(
            row["operating_profit"],
            row["equity_capital"],
            row["reserves"],
            row["borrowings"],
        )

        roa = return_on_assets(row["net_profit"], row["total_assets"])

        conn.execute(
            """
            INSERT INTO financial_ratios (
                company_id, year,
                net_profit_margin_pct,
                operating_profit_margin_pct,
                return_on_equity_pct,
                return_on_capital_employed_pct,
                return_on_assets_pct
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(company_id, year) DO UPDATE SET
                net_profit_margin_pct = excluded.net_profit_margin_pct,
                operating_profit_margin_pct = excluded.operating_profit_margin_pct,
                return_on_equity_pct = excluded.return_on_equity_pct,
                return_on_capital_employed_pct = excluded.return_on_capital_employed_pct,
                return_on_assets_pct = excluded.return_on_assets_pct
            """,
            (
                row["company_id"], row["year"],
                npm, opm, roe, roce, roa,
            ),
        )

        rows_written += 1

    conn.commit()
    conn.close()

    print(f"Rows written to financial_ratios: {rows_written}")


if __name__ == "__main__":
    main()