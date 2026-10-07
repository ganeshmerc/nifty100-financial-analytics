"""
Sprint 2 - Bank ROCE/D-E Carve-Out
Suppress high_leverage_flag for Financials sector companies,
since high leverage is structurally normal for banks/NBFCs/insurance.
"""

import sqlite3
import pandas as pd


def main():
    conn = sqlite3.connect("db/nifty100.db")

    financials = pd.read_sql(
        "SELECT company_id FROM sectors WHERE broad_sector = 'Financials'",
        conn,
    )

    financials_ids = tuple(financials["company_id"].tolist())

    print(f"Financials sector companies: {len(financials_ids)}")

    # Count how many flags will be cleared before we clear them
    placeholders = ",".join("?" for _ in financials_ids)

    before = conn.execute(
        f"""
        SELECT COUNT(*) FROM financial_ratios
        WHERE company_id IN ({placeholders})
        AND high_leverage_flag = 1
        """,
        financials_ids,
    ).fetchone()[0]

    print(f"High-leverage flags currently set for Financials companies: {before}")

    conn.execute(
        f"""
        UPDATE financial_ratios
        SET high_leverage_flag = 0
        WHERE company_id IN ({placeholders})
        """,
        financials_ids,
    )

    conn.commit()

    remaining = conn.execute(
        "SELECT COUNT(*) FROM financial_ratios WHERE high_leverage_flag = 1"
    ).fetchone()[0]

    print(f"High-leverage flags remaining (non-Financials companies): {remaining}")

    conn.close()


if __name__ == "__main__":
    main()