import sqlite3

conn = sqlite3.connect("db/nifty100.db")

print("=" * 70)
print("SECTOR TABLE STRUCTURE")
print("=" * 70)

columns = conn.execute("PRAGMA table_info(sectors)").fetchall()

for column in columns:
    print(column)

print("\n" + "=" * 70)
print("SECTOR SAMPLE")
print("=" * 70)

rows = conn.execute("SELECT * FROM sectors LIMIT 20").fetchall()

for row in rows:
    print(row)

print("\n" + "=" * 70)
print("FINANCIALS COMPANIES")
print("=" * 70)

# Try the most likely column names.
column_names = [column[1] for column in columns]

print("Columns:", column_names)

conn.close()