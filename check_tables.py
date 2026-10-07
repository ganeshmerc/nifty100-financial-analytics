import sqlite3

conn = sqlite3.connect("db/nifty100.db")

query = """
SELECT name
FROM sqlite_master
WHERE type = 'table'
ORDER BY name
"""

tables = conn.execute(query).fetchall()

print("=" * 70)
print("SQLITE TABLES")
print("=" * 70)

for table in tables:
    print(table[0])

conn.close()