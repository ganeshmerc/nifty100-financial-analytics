import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")

df = pd.read_sql(
    """
    SELECT company_id, year,
           revenue_cagr_5yr, pat_cagr_5yr, eps_cagr_5yr
    FROM financial_ratios
    WHERE company_id = 'ADANIPORTS'
    ORDER BY year
    """,
    conn,
)

print(df.to_string(index=False))

conn.close()