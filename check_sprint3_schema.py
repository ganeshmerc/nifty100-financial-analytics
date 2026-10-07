import sqlite3

conn = sqlite3.connect("db/nifty100.db")

tables = [
    "financial_ratios",
    "companies",
    "sectors",
    "peer_groups",
    "profitandloss",
    "analysis",
]

for table in tables:
    print("\n" + "=" * 70)
    print(table.upper())
    print("=" * 70)

    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()

    for row in rows:
        print(f"{row[1]:35} {row[2]}")

conn.close()