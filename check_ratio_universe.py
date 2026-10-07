import sqlite3

conn = sqlite3.connect("db/nifty100.db")

tables = [
    "profitandloss",
    "balancesheet",
    "cashflow",
    "financial_ratios",
]

print("=" * 70)
print("COMPANY-YEAR UNIVERSE CHECK")
print("=" * 70)

for table in tables:
    total = conn.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    unique_pairs = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT DISTINCT company_id, year
            FROM {table}
        )
        """
    ).fetchone()[0]

    companies = conn.execute(
        f"""
        SELECT COUNT(DISTINCT company_id)
        FROM {table}
        """
    ).fetchone()[0]

    print(f"\n{table.upper()}")
    print(f"Total rows          : {total}")
    print(f"Unique company-years: {unique_pairs}")
    print(f"Unique companies    : {companies}")

print("\n" + "=" * 70)
print("MISSING FROM FINANCIAL_RATIOS")
print("=" * 70)

queries = {
    "P&L rows missing from ratios": """
        SELECT p.company_id, p.year
        FROM profitandloss p
        LEFT JOIN financial_ratios r
            ON p.company_id = r.company_id
            AND p.year = r.year
        WHERE r.company_id IS NULL
        ORDER BY p.company_id, p.year
    """,

    "Balance Sheet rows missing from ratios": """
        SELECT b.company_id, b.year
        FROM balancesheet b
        LEFT JOIN financial_ratios r
            ON b.company_id = r.company_id
            AND b.year = r.year
        WHERE r.company_id IS NULL
        ORDER BY b.company_id, b.year
    """,

    "Cash Flow rows missing from ratios": """
        SELECT c.company_id, c.year
        FROM cashflow c
        LEFT JOIN financial_ratios r
            ON c.company_id = r.company_id
            AND c.year = r.year
        WHERE r.company_id IS NULL
        ORDER BY c.company_id, c.year
    """
}

for title, query in queries.items():
    rows = conn.execute(query).fetchall()

    print(f"\n{title}")
    print(f"Count: {len(rows)}")

    for row in rows:
        print(row)

conn.close()