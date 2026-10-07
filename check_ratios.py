import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")

df = pd.read_sql(
    """
    SELECT company_id, year, net_profit_margin_pct,
           operating_profit_margin_pct, return_on_equity_pct,
           return_on_capital_employed_pct, return_on_assets_pct
    FROM financial_ratios
    LIMIT 5
    """,
    conn,
)

print(df.to_string(index=False))

count = conn.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
print(f"\nTotal rows: {count}")

conn.close()