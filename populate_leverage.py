"""
Sprint 2 - Leverage & Efficiency Ratios

Computes:
- Debt-to-Equity
- Interest Coverage Ratio
- Net Debt
- Asset Turnover
- ICR warning flag
- High leverage flag
- Financials sector carve-out
"""

import sqlite3
import pandas as pd

from src.analytics.ratios import (
    debt_to_equity,
    interest_coverage,
    net_debt,
    asset_turnover,
)


DB_PATH = "db/nifty100.db"


def main():

    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            p.company_id,
            p.year,
            p.sales,
            p.operating_profit,
            p.other_income,
            p.interest,

            b.equity_capital,
            b.reserves,
            b.borrowings,
            b.investments,
            b.total_assets,

            COALESCE(s.broad_sector, 'Unknown') AS broad_sector

        FROM profitandloss p

        JOIN balancesheet b
            ON p.company_id = b.company_id
            AND p.year = b.year

        LEFT JOIN sectors s
            ON p.company_id = s.company_id
    """

    df = pd.read_sql(query, conn)

    print(f"Company-year rows to process: {len(df)}")

    rows_updated = 0
    debt_free_count = 0
    high_leverage_flags = 0
    icr_warning_flags = 0
    financials_excluded = 0

    for _, row in df.iterrows():

        # --------------------------------------------------
        # Debt-to-Equity
        # --------------------------------------------------

        de = debt_to_equity(
            row["borrowings"],
            row["equity_capital"],
            row["reserves"],
        )

        # --------------------------------------------------
        # Interest Coverage Ratio
        # --------------------------------------------------

        icr = interest_coverage(
            row["operating_profit"],
            row["other_income"],
            row["interest"],
        )

        # --------------------------------------------------
        # Net Debt
        # --------------------------------------------------

        nd = net_debt(
            row["borrowings"],
            row["investments"],
        )

        # --------------------------------------------------
        # Asset Turnover
        # --------------------------------------------------

        at = asset_turnover(
            row["sales"],
            row["total_assets"],
        )

        # --------------------------------------------------
        # ICR Label
        # --------------------------------------------------

        icr_label = None

        if row["interest"] == 0:
            icr_label = "Debt Free"
            debt_free_count += 1

        # --------------------------------------------------
        # Financials Sector Carve-Out
        #
        # Financial companies are excluded from the
        # D/E > 5 high-leverage warning.
        # --------------------------------------------------

        high_leverage_flag = 0

        if row["broad_sector"] == "Financials":

            financials_excluded += 1

        else:

            if de is not None and de > 5:
                high_leverage_flag = 1
                high_leverage_flags += 1

        # --------------------------------------------------
        # ICR Warning
        # --------------------------------------------------

        icr_warning_flag = 0

        if icr is not None and icr < 1.5:
            icr_warning_flag = 1
            icr_warning_flags += 1

        # --------------------------------------------------
        # Update financial_ratios
        # --------------------------------------------------

        conn.execute(
            """
            UPDATE financial_ratios

            SET
                debt_to_equity = ?,
                interest_coverage = ?,
                net_debt_cr = ?,
                asset_turnover = ?,
                icr_label = ?,
                high_leverage_flag = ?,
                icr_warning_flag = ?

            WHERE company_id = ?
              AND year = ?
            """,
            (
                de,
                icr,
                nd,
                at,
                icr_label,
                high_leverage_flag,
                icr_warning_flag,
                row["company_id"],
                row["year"],
            ),
        )

        rows_updated += 1

    conn.commit()
    conn.close()

    print()
    print("=" * 60)
    print("LEVERAGE & EFFICIENCY COMPLETE")
    print("=" * 60)
    print(f"Rows updated: {rows_updated}")
    print(f"Debt-free companies: {debt_free_count}")
    print(f"High leverage flags: {high_leverage_flags}")
    print(f"ICR warning flags: {icr_warning_flags}")
    print(f"Financials carve-out rows: {financials_excluded}")


if __name__ == "__main__":
    main()