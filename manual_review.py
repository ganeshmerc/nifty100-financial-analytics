import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")

sample_companies = pd.read_sql(
    "SELECT company_id, company_name FROM companies LIMIT 5", conn
)

print("Sample companies:")
print(sample_companies.to_string(index=False))

for company_id in sample_companies["company_id"]:
    print(f"\n--- {company_id} ---")
    pnl = pd.read_sql(
        f"SELECT year, sales, net_profit, eps FROM profitandloss WHERE company_id = '{company_id}' ORDER BY year",
        conn,
    )
    print(pnl.to_string(index=False))

conn.close()