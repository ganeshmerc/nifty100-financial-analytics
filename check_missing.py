import sqlite3

DB = "db/nifty100.db"

conn = sqlite3.connect(DB)

print("=" * 70)
print("P&L rows missing from Balance Sheet")
print("=" * 70)

query1 = """
SELECT
    p.company_id,
    p.year
FROM profitandloss p
LEFT JOIN balancesheet b
    ON p.company_id = b.company_id
    AND p.year = b.year
WHERE b.company_id IS NULL
ORDER BY p.company_id, p.year
"""

rows = conn.execute(query1).fetchall()

print(f"Count: {len(rows)}")
for row in rows:
    print(row)


print("\n" + "=" * 70)
print("Balance Sheet rows missing from P&L")
print("=" * 70)

query2 = """
SELECT
    b.company_id,
    b.year
FROM balancesheet b
LEFT JOIN profitandloss p
    ON b.company_id = p.company_id
    AND b.year = p.year
WHERE p.company_id IS NULL
ORDER BY b.company_id, b.year
"""

rows = conn.execute(query2).fetchall()

print(f"Count: {len(rows)}")
for row in rows:
    print(row)


print("\n" + "=" * 70)
print("Balance Sheet rows missing from Cash Flow")
print("=" * 70)

query3 = """
SELECT
    b.company_id,
    b.year
FROM balancesheet b
LEFT JOIN cashflow f
    ON b.company_id = f.company_id
    AND b.year = f.year
WHERE f.company_id IS NULL
ORDER BY b.company_id, b.year
"""

rows = conn.execute(query3).fetchall()

print(f"Count: {len(rows)}")
for row in rows:
    print(row)


print("\n" + "=" * 70)
print("Cash Flow rows missing from P&L")
print("=" * 70)

query4 = """
SELECT
    f.company_id,
    f.year
FROM cashflow f
LEFT JOIN profitandloss p
    ON f.company_id = p.company_id
    AND f.year = p.year
WHERE p.company_id IS NULL
ORDER BY f.company_id, f.year
"""

rows = conn.execute(query4).fetchall()

print(f"Count: {len(rows)}")
for row in rows:
    print(row)


conn.close()