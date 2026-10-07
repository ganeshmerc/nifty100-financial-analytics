"""
Sprint 2 - CAGR Engine
Computes Revenue, PAT (net profit), and EPS CAGR
for 3-year, 5-year, and 10-year windows.
"""

import sqlite3
import pandas as pd

from src.analytics.cagr import calculate_cagr


def compute_cagr_for_company(df, value_column, years_list):
    """
    df: rows for ONE company, sorted by year, with a 'year' and value_column
    years_list: e.g. [3, 5, 10]

    Returns a dict keyed by year -> {window: (cagr, flag)}
    """

    results = {}

    df = df.sort_values("year").reset_index(drop=True)

    for i, row in df.iterrows():
        end_year = row["year"]
        end_value = row[value_column]

        results[end_year] = {}

        for window in years_list:
            start_year = end_year - window

            start_row = df[df["year"] == start_year]

            if start_row.empty:
                results[end_year][window] = (None, "INSUFFICIENT")
                continue

            start_value = start_row.iloc[0][value_column]

            cagr, flag = calculate_cagr(start_value, end_value, window)
            results[end_year][window] = (cagr, flag)

    return results


def main():
    conn = sqlite3.connect("db/nifty100.db")

    pnl = pd.read_sql(
        "SELECT company_id, year, sales, net_profit, eps FROM profitandloss",
        conn,
    )

    company_ids = pnl["company_id"].unique()

    print(f"Companies to process: {len(company_ids)}")

    windows = [3, 5, 10]
    rows_updated = 0

    for company_id in company_ids:

        company_df = pnl[pnl["company_id"] == company_id]

        revenue_cagr = compute_cagr_for_company(company_df, "sales", windows)
        pat_cagr = compute_cagr_for_company(company_df, "net_profit", windows)
        eps_cagr = compute_cagr_for_company(company_df, "eps", windows)

        for _, row in company_df.iterrows():
            year = row["year"]

            rev_3, rev_3_flag = revenue_cagr[year][3]
            rev_5, rev_5_flag = revenue_cagr[year][5]
            rev_10, rev_10_flag = revenue_cagr[year][10]

            pat_3, pat_3_flag = pat_cagr[year][3]
            pat_5, pat_5_flag = pat_cagr[year][5]
            pat_10, pat_10_flag = pat_cagr[year][10]

            eps_3, eps_3_flag = eps_cagr[year][3]
            eps_5, eps_5_flag = eps_cagr[year][5]
            eps_10, eps_10_flag = eps_cagr[year][10]

            conn.execute(
                """
                UPDATE financial_ratios
                SET
                    revenue_cagr_3yr = ?, revenue_cagr_5yr = ?, revenue_cagr_10yr = ?,
                    pat_cagr_3yr = ?, pat_cagr_5yr = ?, pat_cagr_10yr = ?,
                    eps_cagr_3yr = ?, eps_cagr_5yr = ?, eps_cagr_10yr = ?
                WHERE company_id = ? AND year = ?
                """,
                (
                    rev_3, rev_5, rev_10,
                    pat_3, pat_5, pat_10,
                    eps_3, eps_5, eps_10,
                    company_id, year,
                ),
            )
            rows_updated += 1

    conn.commit()
    conn.close()

    print(f"Rows updated: {rows_updated}")


if __name__ == "__main__":
    main()
