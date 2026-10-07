import sqlite3

conn = sqlite3.connect("db/nifty100.db")

query = """
SELECT
    f.company_id,
    f.year,
    f.return_on_equity_pct,
    p.net_profit,
    b.equity_capital,
    b.reserves,
    (b.equity_capital + b.reserves) AS total_equity
FROM financial_ratios f
JOIN profitandloss p
    ON f.company_id = p.company_id
   AND f.year = p.year
JOIN balancesheet b
    ON f.company_id = b.company_id
   AND f.year = b.year
WHERE f.return_on_equity_pct > 100
ORDER BY f.return_on_equity_pct DESC
LIMIT 30;
"""

rows = conn.execute(query).fetchall()

print("=" * 100)
print("EXTREME ROE INVESTIGATION")
print("=" * 100)

for row in rows:
    company, year, roe, profit, equity_capital, reserves, total_equity = row

    print(
        f"{company:<15} "
        f"{year:<6} "
        f"ROE={roe:>10.2f}% | "
        f"PAT={profit:>12.2f} | "
        f"Equity={equity_capital:>12.2f} | "
        f"Reserves={reserves:>12.2f} | "
        f"Total Equity={total_equity:>12.2f}"
    )

conn.close()