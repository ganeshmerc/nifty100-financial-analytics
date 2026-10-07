"""
Sprint 2 - Populate Composite Quality Score
"""

import sqlite3
import pandas as pd

from src.analytics.quality_score import composite_quality_score


def main():
    conn = sqlite3.connect("db/nifty100.db")

    query = """
        SELECT
            company_id,
            year,
            net_profit_margin_pct,
            return_on_equity_pct,
            return_on_capital_employed_pct,
            debt_to_equity,
            interest_coverage,
            cfo_quality_score,
            fcf_conversion_rate_pct,
            revenue_cagr_3yr,
            pat_cagr_3yr
        FROM financial_ratios
    """

    df = pd.read_sql(query, conn)

    print(f"Rows to process: {len(df)}")

    rows_updated = 0

    for _, row in df.iterrows():

        score = composite_quality_score(
            row["net_profit_margin_pct"],
            row["return_on_equity_pct"],
            row["return_on_capital_employed_pct"],
            row["debt_to_equity"],
            row["interest_coverage"],
            row["cfo_quality_score"],
            row["fcf_conversion_rate_pct"],
            row["revenue_cagr_3yr"],
            row["pat_cagr_3yr"],
        )

        conn.execute(
            """
            UPDATE financial_ratios
            SET composite_quality_score = ?
            WHERE company_id = ?
              AND year = ?
            """,
            (
                score,
                row["company_id"],
                row["year"],
            ),
        )

        rows_updated += 1

    conn.commit()
    conn.close()

    print(f"Rows updated: {rows_updated}")


if __name__ == "__main__":
    main()