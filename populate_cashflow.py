"""
Sprint 2 - Cash Flow KPIs

Computes:
- Free Cash Flow
- CFO Quality Score
- CapEx
- CapEx Intensity
- FCF Conversion Rate
"""

import sqlite3
import pandas as pd

from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality_score,
    capex_intensity,
    fcf_conversion_rate,
)


def main():
    conn = sqlite3.connect("db/nifty100.db")

    query = """
        SELECT
            c.company_id,
            c.year,
            c.operating_activity,
            c.investing_activity,
            p.sales,
            p.operating_profit,
            p.net_profit
        FROM cashflow c
        JOIN profitandloss p
            ON c.company_id = p.company_id
            AND c.year = p.year
    """

    df = pd.read_sql(query, conn)

    print(f"Company-year rows to process: {len(df)}")

    rows_updated = 0
    rows_skipped_no_target = 0

    for _, row in df.iterrows():

        # Free Cash Flow
        fcf = free_cash_flow(
            row["operating_activity"],
            row["investing_activity"],
        )

        # CFO Quality Score
        cfo_score, cfo_label = cfo_quality_score(
            row["operating_activity"],
            row["net_profit"],
        )

        # CapEx Intensity
        capex_pct, capex_label = capex_intensity(
            row["investing_activity"],
            row["sales"],
        )

        # FCF Conversion Rate
        fcf_conv = fcf_conversion_rate(
            fcf,
            row["operating_profit"],
        )

        cursor = conn.execute(
            """
            UPDATE financial_ratios
            SET
                free_cash_flow_cr = ?,
                capex_cr = ?,
                cfo_quality_score = ?,
                capex_intensity_pct = ?,
                fcf_conversion_rate_pct = ?
            WHERE company_id = ? AND year = ?
            """,
            (
                fcf,
                row["investing_activity"],
                cfo_score,
                capex_pct,
                fcf_conv,
                row["company_id"],
                row["year"],
            ),
        )

        if cursor.rowcount == 0:
            rows_skipped_no_target += 1
        else:
            rows_updated += 1

    conn.commit()
    conn.close()

    print(f"Rows updated: {rows_updated}")
    print(
        f"Rows skipped (no matching financial_ratios row): "
        f"{rows_skipped_no_target}"
    )


if __name__ == "__main__":
    main()