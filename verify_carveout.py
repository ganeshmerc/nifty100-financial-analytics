import sqlite3

conn = sqlite3.connect("db/nifty100.db")

query = """
SELECT COUNT(*)
FROM financial_ratios r
JOIN sectors s
    ON r.company_id = s.company_id
WHERE s.broad_sector = 'Financials'
  AND r.high_leverage_flag = 1
"""

count = conn.execute(query).fetchone()[0]

print("Financials high-leverage flags:", count)

conn.close()