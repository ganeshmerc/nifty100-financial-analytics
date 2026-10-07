import sqlite3

DB = "db/nifty100.db"

conn = sqlite3.connect(DB)

query = """
SELECT
    company_id,
    year,
    return_on_equity_pct,
    debt_to_equity
FROM financial_ratios
WHERE return_on_equity_pct > 15
  AND debt_to_equity < 1
ORDER BY return_on_equity_pct DESC;
"""

rows = conn.execute(query).fetchall()

print("=" * 70)
print("SPRINT 2 SCREENER PREVIEW")
print("=" * 70)

print("\nFilter:")
print("ROE > 15% AND D/E < 1")

print(f"\nMatching company-year rows: {len(rows)}")

companies = sorted(set(row[0] for row in rows))

print(f"Unique companies: {len(companies)}")

print("\nTop results:")
print("-" * 70)

for company_id, year, roe, de in rows[:50]:
    print(
        f"{company_id:<15} "
        f"{str(year):<8} "
        f"ROE: {roe:>8.2f}%   "
        f"D/E: {de:>8.2f}"
    )

print("\n" + "=" * 70)

if 15 <= len(companies) <= 50:
    print("SCREENING CHECK: PASS")
    print("Unique company count is between 15 and 50.")
else:
    print("SCREENING CHECK: REVIEW")
    print("Unique company count is outside the expected 15-50 range.")

conn.close()