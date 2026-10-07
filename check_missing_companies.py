import sqlite3

conn = sqlite3.connect("db/nifty100.db")

tables = ["profitandloss", "balancesheet", "cashflow"]

company_sets = {}

for table in tables:
    rows = conn.execute(
        f"SELECT DISTINCT company_id FROM {table} ORDER BY company_id"
    ).fetchall()

    company_sets[table] = {row[0] for row in rows}

all_companies = set.union(*company_sets.values())

print("=" * 70)
print("MISSING COMPANY CHECK")
print("=" * 70)

print(f"\nTotal companies across all financial tables: {len(all_companies)}")

for table in tables:
    missing = sorted(all_companies - company_sets[table])

    print(f"\n{table.upper()}")
    print(f"Companies present: {len(company_sets[table])}")
    print(f"Missing companies: {len(missing)}")

    if missing:
        for company in missing:
            print(f"  - {company}")

print("\n" + "=" * 70)
print("COMPANY UNIVERSE FROM MASTER")
print("=" * 70)

master = {
    row[0]
    for row in conn.execute(
        "SELECT DISTINCT company_id FROM companies"
    ).fetchall()
}

print(f"Companies table: {len(master)}")

for table in tables:
    missing_from_table = sorted(master - company_sets[table])

    print(f"\nMissing from {table.upper()}: {len(missing_from_table)}")
    for company in missing_from_table:
        print(f"  - {company}")

conn.close()